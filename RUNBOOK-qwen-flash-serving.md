# Runbook — Qwen3.8-Flash-Next serving on spark-8cf2

Operating guide + post-mortem for "the model went strange / stopped answering".
Last revised 2026-09-28 after an independent **Codex Astra** (`gpt-6-astra`) review, which
corrected several overstatements in the earlier version. Corrections are marked **[Astra]**.

---

## 0. THREE independent failure modes (they look similar, they are not)

| # | failure mode | how it presents | self-healing guard |
|---|---|---|---|
| 1 | **RPC backend down** (`spark-rpc.service` on spark-40ee) | **no response at all** — model server cannot load and crash-loops | `spark-rpc-guard.timer` (40ee, **2 min**) |
| 2 | **Degenerate `/` collapse** | `Think` + a wall of `/`, first token is `/` | `qwen-flash-guard.timer` (8cf2, **5 min**) |
| 3 | **Slow first turn** (cold prefill) | ~30 s–3 min before any token after a restart | not a fault; see §6 |

**Mode 1 is the one that actually caused the 2026-09-28 outage.** Journal:
```
Sep 28 06:36:16  Stopping spark-rpc.service ... Deactivated successfully. Stopped.
Sep 28 09:25:13  Started spark-rpc.service            (manual recovery)
```
`spark-flash-next` loads with `--rpc 10.10.20.2:50052` and **aborts inside
`ggml_backend_rpc_add_server` → `rpc_dispatcher::start()`** when that peer is gone; with
`Restart=always` it crash-looped **NRestarts = 621** over ~2 h 49 m. Restarting the model server
cannot fix this — the RPC peer must be started. Hence a **second, separate guard on spark-40ee.**

## 1. Failure signature for mode 2

A wall of one character (`/`) **starting at the first output token**, in the reasoning field.
It is **context-dependent**: a tiny `Reply with the single word OK` prompt still answers cleanly
(~2 s) while the same server collapses on 19k+ token contexts. Short probes therefore do not
detect it — the first guard version missed a real recurrence for exactly this reason.

## 2. Mode 2 — the `q8_0` KV cache: mitigation WORKS, cause NOT established

The unit ran `--cache-type-k q8_0 --cache-type-v q8_0`; switching to **`f16`** removed the
collapse in every test since. Live config is now `f16`.

**Treat this as a working mitigation, not a proven root cause.** [Astra] raised these, and they
stand:

- **The original comparison was confounded.** The q8_0 failures occurred on a long-lived process;
  the f16 runs followed a fresh restart. Reset state, preceding workload, slot assignment and
  context configuration all differed. "Same history in the request" ≠ identical internal state.
- **The proposed mechanism is unmeasured.** "Quantized KV error accumulates with context length
  until the attention distribution collapses" is a hypothesis — no logits, attention maps or
  numerical comparisons support it. Even a clean difference would implicate *the q8_0 execution
  path* generally (cache handling, quantized attention kernels, allocation), not specifically
  rounding error.
- **Flash attention is required with quantized V** in current llama.cpp, so flash-attn-off is not
  a valid isolation arm; keeping `--flash-attn on` with `f16` KV is the supported combination.
- **RSS unchanged does not prove KV memory is negligible** — allocations may sit on the other host.
  Compare backend allocation logs on both machines before repeating that claim.

**Decisive experiment still owed** (Astra's design; the first attempt was invalidated by the
mode-1 outage): a **balanced crossover `q8_0 → f16 → f16 → q8_0`**, each arm from the same reset
procedure and fixed context config, replaying the exact inducing workload *including preceding
generations and request order*, holding model/binary/template/tools/batching/RPC placement
constant. **Falsifier:** equally-reset `q8_0` stays clean, or `f16` collapses comparably.

External support (not confirmation): a `q8_0`-KV decode penalty study on a Qwen3.8 model
([1](https://raw.githubusercontent.com/steveseguin/b70-optimization-lab/main/experiments/qwen38-27b-b70/notes/2026-08-22-qwen38-q4km-tp1-context-kv-sweep-finding.md)),
KV-quantization benchmarking specifically on DGX Spark GB10
([2](https://huggingface.co/datasets/memoriant/dgx-spark-kv-cache-benchmark/blob/0b38ae6f882db2cd5f1ee8d4b9b7f5285cd0e382/README.md)),
unsloth resetting quantized KV to f16 in a fallback path
([3](https://github.com/unslothai/unsloth/pull/7390)), and llama.cpp infinite-generation bugs
around KV-cache-full and `shift_context()`
([4](https://github.com/ggml-org/llama.cpp/pull/20050), [5](https://github.com/ggml-org/llama.cpp/pull/18432)).

## 3. What was ruled out, and how far that goes

| theory | test | result |
|---|---|---|
| sampling / temperature | `temp=0.6`, `temp=0.0` greedy, `repeat-penalty 1.15`, `dry-multiplier 1.0` | all still collapsed. **[Astra]** this shows *those changes did not cure it* — it does **not** prove every sampler defect is excluded |
| tool schema | bisected the tool list | **confounded**: with few tools declared, llama-server drops history blocks referencing other tools, so "clean" arms sent near-empty prompts |
| poisoned history via `thinking` | "magic word = BANANA" probe | the model did not know BANANA. **[Astra]** failed recall ≠ proof the field was dropped; inspect the rendered prompt to be sure |
| oversized request | 280,059 tokens into a 262,144 slot | clean `HTTP 400 exceed_context_size_error`, no poisoning. **[Astra]** the 145,631-token case was likewise a **rejection, not truncation** — an earlier version of this runbook wrongly said "truncated". Failures occurred *below* the slot limit, so exceeding it is not necessary for the collapse |
| reasoning budget | `--reasoning-budget 4096` with long generations | **[Astra]** my figures mixed units: 10,043 / 22,392 were **characters**, 22,362 was **tokens**. Non-enforcement is *unverified* — check token IDs and sampler activation |

## 4. Resets — prefer the in-place one

**Fast (~2 s, no reload)** — requires `--slot-save-path` (now set); without it the server returns
`HTTP 501 "does not support slots action"`:
```bash
curl -s -X POST -H 'x-api-key: dummy' 'http://127.0.0.1:8093/slots/0?action=erase'
curl -s -X POST -H 'x-api-key: dummy' 'http://127.0.0.1:8093/slots/1?action=erase'
```
**Slow (~190–330 s):** `ssh clawerdigi1@spark-8cf2 'sudo systemctl restart spark-flash-next.service'`
— also clears the prompt cache, so the next message pays a cold prefill.

## 5. THE SERVING INVARIANT

```
per-slot context = -c / --parallel
```
Current: `-c 524288` ÷ `--parallel 2` = **262,144 per slot**; DSH declares `contextWindow 200000`.
1. Never raise `--parallel` without raising `-c` by the same factor.
2. Never set the client `contextWindow` equal to the per-slot context (zero headroom).

## 6. Guards and timers (both installed, both verified no-false-positive)

| guard | host | interval | what it fixes | log |
|---|---|---|---|---|
| `spark-rpc-guard.timer` | spark-40ee | **2 min** | mode 1 — restarts `spark-rpc.service` if inactive or port 50052 unbound | `/var/log/spark-rpc-guard.log` |
| `qwen-flash-guard.timer` | spark-8cf2 | **5 min** | mode 2 — long-context probe → slot erase → restart | `~/qwen-run/guard.log` |

Both guards stay silent when healthy. `spark-rpc.service` and `spark-flash-next.service` are both
`enabled`, so they survive reboot — but **note that `spark-rpc.service` was manually stopped at
06:36 on 2026-09-28**; if a GPU-hungry job (vLLM/Ray, training) stops it again, the 2-minute guard
will bring it back.

```bash
ssh clawerdigi2@spark-40ee 'systemctl list-timers spark-rpc-guard.timer; tail /var/log/spark-rpc-guard.log'
ssh clawerdigi1@spark-8cf2 'systemctl list-timers qwen-flash-guard.timer; tail ~/qwen-run/guard.log'
```

## 7. Diagnostics that discriminate

- **Check `input_tokens`.** `in=4` for a long conversation means the history was **dropped**
  (llama-server cannot render `tool_result` blocks with no tools declared). Two "clean" results in
  this investigation were artifacts of an empty prompt.
- **`ps`/`ss` inside the DSH sandbox cannot see host processes** — it runs under
  `bwrap --unshare-pid`. Use `systemctl` or ssh.
- **A readiness check that ignores HTTP status is useless**: require **200** *and* `/slots`
  returning two entries. `HTTP 503 "Loading model"` is normal for ~190–330 s after a restart.
- **`ssh` inside a here-doc script must use `ssh -n`**, or it swallows the rest of the script.
- llama-server **does not cancel** a generation when the client disconnects — kill the remote
  client, not just your local one.
- `--reasoning on`: clients must send `max_tokens` **above** the reasoning budget or `content`
  comes back empty.

## 8. Configuration history (backups on spark-8cf2, `~/qwen-run/`)

| backup | what it is |
|---|---|
| `spark-flash-next.service.bak-slotapi-20260928T011137Z` | adds `--slot-save-path` (in-place reset) |
| `spark-flash-next.service.bak-f16kv-20260928T010027Z` | the `f16` KV mitigation |
| `spark-flash-next.service.bak-2slot-fullctx-20260928T000928Z` | 2 slots × 262,144 |
| `spark-flash-next.service.bak-20260927T220430Z` | original (`--parallel 1`, `q8_0` KV) |

## 9. If it happens again — first question, not a diagnosis

1. **No response at all?** → check `spark-rpc.service` on spark-40ee first (§0 mode 1). That is the
   most likely cause and the cheapest to check.
2. **`Think` + `/` wall?** → mode 2; the 5-minute guard should already have cleared it; if not,
   run the slot erase (§4).
3. **[Astra]** "first token `/` + large context" **describes the symptom, it does not identify the
   cause** — do not treat it as a diagnostic conclusion.
