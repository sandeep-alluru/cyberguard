# Runbook — Qwen3.8-Flash-Next serving on spark-8cf2

Post-mortem and operating guide for the "the model went strange / stopped answering" class
of failure. Root cause found 2026-09-28.

---

## 1. The failure signature

**The model emits a wall of one character — observed `/` — starting at the FIRST token.**
In the DSH UI: `Think` followed by a huge run of `/`, then you stop it. Every later message
does the same.

**It is context-dependent.** A tiny prompt (`Reply with the single word OK`) still answers
perfectly while the server is broken. It appears as the context grows.

## 2. ROOT CAUSE: the `q8_0` KV cache quantization

The unit ran `--cache-type-k q8_0 --cache-type-v q8_0`. Quantized KV accumulates error with
context length; past a threshold the attention distribution collapses into a repeated token.

Decisive experiment — identical requests, only the KV type changed:

| context | `q8_0` KV | **`f16` KV** |
|---|---|---|
| 19,033 tok | **COLLAPSE** | clean |
| 24,989 tok | **COLLAPSE** | clean |
| 30,690 tok | **COLLAPSE** | clean |
| 73,494 tok (62 tools, long generation) | — | **clean** |

**Fix: `--cache-type-k f16 --cache-type-v f16`.** Cost: llama-server RSS unchanged at
29.3 GB, ~39 GB still free (the 177B-parameter weights dominate; KV is small next to them).

## 3. What it is NOT (each tested and ruled out — do not re-chase these)

| theory | test | result |
|---|---|---|
| sampling / temperature | `temp=0.6`, `temp=0.0` greedy, `repeat-penalty 1.15`, `dry-multiplier 1.0` | **all still collapsed** — it is deterministic |
| the 62-tool schema | bisected the tool list | confounded; irrelevant once KV degrades |
| poisoned history / reasoning traces | sent the exact `/`-wall as a `thinking` block | server **drops** client `thinking` blocks (proved with a "magic word" probe) |
| oversized request | 280,059 tokens into a 262,144 slot | clean HTTP 400, **no** poisoning |
| `--reasoning-budget` 4096 | set/unset | not enforced by this template; irrelevant to the collapse |
| `--parallel 2` context halving | — | a **second**, independent bug (see §5); not the collapse |

**Note:** the `/` wall is sticky once present — a degenerate generation enters the slot's
cached prefix and is replayed. So *both* the KV fix **and** a reset matter.

## 4. Two ways to reset — in-place is usually enough

**Fast (~2 s, no model reload):**
```bash
curl -s -X POST -H 'x-api-key: dummy' 'http://127.0.0.1:8093/slots/0?action=erase'
curl -s -X POST -H 'x-api-key: dummy' 'http://127.0.0.1:8093/slots/1?action=erase'
```
This is the "back to just-loaded state" reset. It requires `--slot-save-path` in the unit —
without that flag the server answers **HTTP 501** `"does not support slots action"`. It is now
set to `/home/clawerdigi1/qwen-run/slots`.

**Slow (~270–330 s): a service restart.**
```bash
ssh clawerdigi1@spark-8cf2 'sudo systemctl restart spark-flash-next.service'
```
Clears everything, but pays a full four-shard reload — and the next message then costs a cold
prefill. **Prefer the slot erase.**

## 5. THE SERVING INVARIANT — do not break this

```
per-slot context = -c / --parallel
```

Current: `-c 524288` ÷ `--parallel 2` = **262,144 per slot**; DSH declares
`contextWindow: 200000` (headroom).

1. **Never raise `--parallel` without raising `-c` by the same factor.** Going 1 → 2 at
   `-c 262144` silently halved per-slot context to 131,072 while the session was at 145,631.
2. **Never set the client `contextWindow` equal to the per-slot context** (zero headroom).

## 6. The guard (installed, self-healing)

| item | path / name |
|---|---|
| script | `/home/clawerdigi1/qwen-run/qwen-flash-guard.sh` |
| units | `qwen-flash-guard.service` + `qwen-flash-guard.timer` — **every 5 minutes** |
| log | `/home/clawerdigi1/qwen-run/guard.log` |

Recovery order: **probe → erase both slots → re-probe → restart only if still broken.**
The probe uses a **~16k-token context**, because a short probe stays clean while the server is
broken — the first version of this guard missed a real recurrence for exactly that reason.
Verified: healthy server → probe `OK`, 2 s, **no false restart**.

```bash
ssh clawerdigi1@spark-8cf2 'systemctl list-timers qwen-flash-guard.timer; tail -20 ~/qwen-run/guard.log'
```

## 7. Diagnostics that discriminate (these cost hours when ignored)

- **Check `input_tokens` in the response.** `in=4` for a long conversation means llama-server
  **dropped the whole history** (it cannot render `tool_result` blocks with no tools declared).
  Two "clean" results in this investigation were artifacts of an empty prompt.
- **`ps`/`ss` inside the DSH sandbox cannot see host processes** — it runs under
  `bwrap --unshare-pid`. Use `systemctl --user` or ssh.
- **A readiness check that ignores HTTP status is useless**: `curl -s -o /dev/null -w '%{http_code}'`
  without `-f` returns 0 for 4xx/5xx. Require **200** *and* `/slots` returning 2 entries.
- llama-server **does not cancel** a generation when the client disconnects. Killing a local
  `curl`/ssh leaves the server generating and holding a slot; kill the remote client too.
- `--reasoning on` + `--reasoning-budget 4096`: clients must send `max_tokens` **above** the
  budget or the reply comes back with empty `content`.

## 8. Configuration history (backups on spark-8cf2, `~/qwen-run/`)

| backup | what it is |
|---|---|
| `spark-flash-next.service.bak-slotapi-20260928T011137Z` | current (adds the slot API) |
| `spark-flash-next.service.bak-f16kv-20260928T010027Z` | the KV fix |
| `spark-flash-next.service.bak-2slot-fullctx-20260928T000928Z` | 2 slots × 262,144 |
| `spark-flash-next.service.bak-20260927T220430Z` | original (`--parallel 1`, `q8_0` KV) |

## 9. If it happens again

1. Check `guard.log` — the guard should already have cleared it.
2. Try the in-place reset (§4) before restarting; it preserves the loaded model.
3. **The one-line diagnosis to hand any agent: "the first token was `/` and the context was
   large."** That means KV degradation, not a prompt, tool, or reasoning problem.
