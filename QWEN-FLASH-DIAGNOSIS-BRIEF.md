# Diagnosis brief — Qwen3.8-Flash-Next degenerate `/` collapse (spark-8cf2)

Independent review requested. Everything below is measured, not assumed; where something is
inference it is marked. Be adversarial: find the flaws.

## Environment

- Inference: `llama-server` (llama.cpp 0.4.1-dev, build 1, commit 9425611, aarch64)
- Model: `Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf` (4 shards; n_params reported
  176,943,899,520; n_embd 2560; n_ctx_train 262144)
- Host: 2-node "DGX Spark" RPC pool. `llama-server` runs on spark-8cf2 (GB10) with
  `--rpc 10.10.20.2:50052` pointing at `ggml-rpc-server` on spark-40ee, which holds ~45.8 GB
  of GPU memory. Serving therefore depends on BOTH boxes.
- Client: DSH harness, provider `spark-local`, API style `anthropic-messages`, endpoint
  `http://100.118.142.51:8093`, `apiKeyEnv` = `dummy`. Agentic sessions carrying **62 tools**.
- Current unit flags:
  `-m <4 shards> --rpc 10.10.20.2:50052 -c 524288 -n 32768 --cache-type-k f16 --cache-type-v f16
   --flash-attn on --host 0.0.0.0 --port 8093 --api-key dummy -a qwen3.8-flash-next -ngl 999
   --jinja --parallel 2 --slot-save-path /home/clawerdigi1/qwen-run/slots
   --reasoning on --reasoning-preserve --reasoning-budget 4096`
- Memory: 121 GB total; llama-server RSS ~29.3 GB; ~39-43 GB available.

## Symptom

The model emits a **wall of the character `/` starting at the very first output token**, in the
`thinking` / reasoning field. In the DSH UI the user sees `Think` followed by thousands of `/`
and then stops it. Observed occurrences at 18:00, 18:16, 18:35, 19:40 (local). One instance
generated 22,392 characters of `/`; another 11,479; another 10,043.

## Established properties (each from a controlled experiment)

1. **Deterministic.** On an affected server, `temperature 0.6`, `temperature 0.0` (greedy),
   `repeat-penalty 1.15` and `dry-multiplier 1.0` **all still collapsed identically**.
   => This cannot be a sampling problem.
2. **Context-size dependent.** On an affected server a tiny prompt (`Reply with the single word
   OK`, ~50 tokens) still answered **cleanly in ~2 s**, while the same server collapsed on
   19,033 / 24,989 / 30,690 / 73,494-token contexts. So a short-context health probe does not
   detect the fault.
3. **Stateful.** A `systemctl restart` of llama-server, or erasing the slots via
   `POST /slots/{id}?action=erase`, clears it completely and immediately.
4. **Sticky.** Once one degenerate generation has occurred, subsequent requests keep collapsing
   until the state is reset (consistent with the degenerate output entering the slot's cached
   prefix and being replayed).
5. **Not caused by an oversized request.** Sending 280,059 tokens into a 262,144 slot returned a
   clean `HTTP 400 exceed_context_size_error` and did **not** poison subsequent requests.
6. **llama-server drops client-supplied `thinking` blocks.** Proven with a "magic word" probe:
   an assistant message whose `thinking` was "The magic word is BANANA" followed by
   "What is the magic word?" produced no knowledge of BANANA. This invalidated several earlier
   "clean" tests that thought they were injecting a poisoned reasoning trace.

## The finding

The unit previously ran `--cache-type-k q8_0 --cache-type-v q8_0`. **Switching both to `f16`
eliminated the collapse.** Same requests, same server build, same history, only KV type changed:

| context size | q8_0 KV | f16 KV |
|---|---|---|
| 19,033 tokens | COLLAPSE (`//////`) | clean |
| 24,989 tokens | COLLAPSE | clean |
| 30,690 tokens | COLLAPSE | clean |
| 73,494 tokens + 62 tools + long generation | not re-tested | clean |

Memory cost of `f16`: llama-server RSS stayed ~29.3 GB (weights dominate); ~39 GB still free.

**Claim: the `q8_0` KV cache quantization is the cause.** The mechanism proposed is that
quantized KV error accumulates with context length until the attention distribution collapses
into a repeated token.

## The second, separate bug found

`-c 262144` was combined with `--parallel 2`, which **halves per-slot context to 131,072**.
Per-slot context = `-c / --parallel`. The user's session had grown to 145,631 tokens and the
server logged `request (145631 tokens) exceeds the available context size (131072 tokens)`.
Also, the client's declared `contextWindow` had been set to 131,072 — exactly the slot size,
zero headroom. Both were corrected: `-c 524288` with `--parallel 2` (262,144/slot) and client
`contextWindow 200000`.

## Mitigations installed

- `qwen-flash-guard.timer` (every 5 min) runs a probe with a **~16k-token context** (a short
  probe did not detect the fault — the first guard version missed a real recurrence).
  Recovery order: probe → `POST /slots/{id}?action=erase` on both slots (~2 s, no reload) →
  `systemctl restart` only if that fails.
- `--slot-save-path` is set, which is required for the slot API (without it the server returns
  HTTP 501 "does not support slots action").

## What I want from this review

1. Is the `q8_0` KV attribution sound, or could the observed contrast be explained by something
   that co-varied (e.g. restart timing, cache state, the fact that the f16 build was freshly
   started while the q8_0 tests ran on a longer-lived process)?
2. If `q8_0` KV is truly the cause, **why is `f16` apparently sufficient** given that the
   unrelated second bug (context halving/truncation) also coincided with the first collapse?
   Could both be contributing, with KV as the trigger and truncation as an amplifier?
3. `--flash-attn on` combined with quantized KV: is there a known interaction? Is `f16` KV with
   flash attention the actually-safe combination, or is there a better one (e.g. asymmetric
   `q8_0` K / `f16` V)?
4. `--reasoning-budget 4096` does not appear to be enforced — generations of 10,043 and 22,362
   tokens occurred with the budget set to 4096. Is that expected for this template, and does it
   contribute?
5. The RPC split across two hosts: could `--rpc` offload change numerics in a way that makes
   this model unusually fragile to KV quantization? Is there a way to test that?
6. What is the **decisive** experiment you would run to confirm or refute the KV attribution,
   and what would falsify it?
7. Anything materially wrong or missing in the above, or in
   `/home/clawer-samurai-1/AgentHub/cyberguard/RUNBOOK-qwen-flash-serving.md`.

Constraints on scope: this is a serving/configuration diagnosis. Do not propose licence,
attribution or release-process changes. Be concrete and cite evidence from this brief; if you
assert something from general knowledge, say so explicitly.
