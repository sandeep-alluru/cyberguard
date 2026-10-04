# PUBLIC EVAL MACHINERY — handover to CyberGuard

**Written 2026-10-04 by the gpu-work/ornith worker, at the owner's instruction:** *"cybergaurd is not aware of the
opensource eval machinery that you downloaded can you give the information on where it can find it and then i need it
to use it give me the info"*.

**Read this whole page before running anything.** Section 6 lists the traps that already cost the ornith programme
days; they will cost CyberGuard the same if it repeats them.

---

## 0 · What this machinery is — and what it is NOT

| it IS | it is NOT |
|---|---|
| the **official public benchmark harnesses**, obtained from the upstream projects, **pinned by hash** — BFCL (Berkeley Function-Calling Leaderboard) and SWE-bench | a security benchmark. For harm/safety use CyberGuard's own `pubbench/` with **HarmBench** and **CyberSecEval MITRE-FRR** |
| a **reusable method**: obtain the official wheel → pin it by sha256 → drive it with a **thin adapter** → let the **official code** decide every pass/fail | a local test suite. Nothing here was authored in-house; that is the point — an in-house scorer "is like giving keys to the thief" (owner) |

**Why it may still matter to CyberGuard:** if the CyberGuard model is expected to **emit tool calls**, BFCL measures
exactly that against a public standard, and the *method* transfers to any other public benchmark you choose.

---

## 1 · Where everything lives

| item | path |
|---|---|
| **Pinned venv (use this one)** | `/mnt/purple4tb/o9b-bench-venv-pinned` — python **3.12.3**, `bfcl_eval` **2026.3.23** |
| Older venv (kept as the record of the first install) | `/mnt/purple4tb/o9b-bench-venv` |
| **The wheels + freezes (the pins)** | `/mnt/purple4tb/o9b-bench-pins/` |
| **Tokenizer used for BFCL** | `/mnt/purple4tb/o9b-bfcl-tokenizer` (7 files, hash-verified 7/7) |
| **The BFCL CLI** | `/mnt/purple4tb/o9b-bench-venv-pinned/bin/bfcl` (equivalently: `<venv>/bin/python -m bfcl_eval`) |
| The thin adapter (the pattern to copy) | `gpu-work/training/katana/eval/bfcl_public_model.py` |
| The map instrument (what is pinned, what is not) | `gpu-work/training/katana/eval/public_benchmark_map.py` |
| **The pin receipt (authoritative)** | `gpu-work/training/ornith9b-v1-continuation-20260926/receipts/PUBLIC-HARNESS-PIN-20261003-1649.json` |
| The metric map receipt | `.../receipts/PUBLIC-BENCHMARK-METRIC-MAP-20261003-1449.json` |

*(`gpu-work` = `/mnt/purple4tb/AgentHub-archive/gpu-work`.)*

### The pinned artifacts, by hash

| artifact | size | sha256 |
|---|---|---|
| `bfcl_eval-2026.3.23-py3-none-any.whl` | 1,925,664 B | `3bb6dfa5f0c68ad403c9ec50b00db2bb3b4cc9b38ab1ff33f48fe30d853d3a0a` |
| `swebench-5.0.2-py3-none-any.whl` | 142,715 B | recorded in the pin receipt |
| `bfcl-venv-freeze-20261003-1613.txt` | — | the **final** frozen dependency set (`-1529.txt` is the earlier one) |

**The pin receipt covers 21 metric claims — 9 from BFCL, 12 from SWE-bench — with zero overlap and no placeholders.**
Read it before claiming any metric.

---

## 2 · How to run it

### The invocation shape (proven — this is what the ornith programme ran)

BFCL runs in **two phases**: `generate` (ask the model) then `evaluate` (score). Both go through the official CLI.

```bash
V=/mnt/purple4tb/o9b-bench-venv-pinned
AD=/mnt/purple4tb/AgentHub-archive/gpu-work/training/katana/eval/bfcl_public_model.py

# run from the venv's site-packages so the harness's own imports resolve
cd $V/lib/python3.12/site-packages

ORNITH_GGUF=<the served .gguf file>            \
ORNITH_TOKENIZER=/mnt/purple4tb/o9b-bfcl-tokenizer \
REMOTE_OPENAI_BASE_URL=http://<host>:<port>/v1 \
REMOTE_OPENAI_API_KEY=EMPTY                    \
$V/bin/python "$AD" generate \
    --model ornith-9b-adapter-v1 \
    --test-category simple_python \
    --skip-server-setup --temperature 0.001 \
    --result-dir <results-dir>

# score the generated file (official scorer; add --partial-eval to score what exists)
$V/bin/python "$AD" evaluate \
    --model ornith-9b-adapter-v1 \
    --test-category simple_python \
    --result-dir <results-dir> --partial-eval
```

### The adapter contract (copy this pattern, do not reimplement the benchmark)

`bfcl_public_model.py` is **1,770 bytes** and does exactly three things:

1. **requires** `ORNITH_GGUF`, `ORNITH_TOKENIZER`, `REMOTE_OPENAI_BASE_URL` — and **refuses to run** without them
   (*"it registers a model, it does not invent an endpoint"*);
2. **registers our model name** into the harness's own `MODEL_CONFIG_MAPPING` with a handler that **already exists
   upstream** (`QwenHandler`) — and `ORNITH_FC_MODEL=1` flips `is_fc_model` for the native-function-calling row;
3. **delegates the entire run** to the official CLI via
   `runpy.run_module("bfcl_eval", run_name="__main__")`.

**It renders no prompt, parses no call, compares no call and decides no pass/fail — the public code decides all of
that.** That is the discipline that makes the number defensible. **Do not "improve" it by adding your own parsing.**

---

## 3 · The server it talks to

The adapter drives an **OpenAI-compatible endpoint** — in the ornith case a `llama-server` serving a GGUF:

```bash
CUDA_VISIBLE_DEVICES=1 llama-server \
  --model <path>.gguf --jinja --port 8198 --host 0.0.0.0
# health:  curl http://<host>:8198/health
```

**Start the server and wait for `/health` to be OK before generating.** The ornith programme lost a whole pilot
(2,065 rows, 651 of them `503 Loading model` errors) by firing the harness at a server that had not finished loading.
**That single mistake voided a measurement.**

---

## 4 · What is pinned, and what is still NOT pinned

The map instrument reports its own state — run it, do not trust prose:

```bash
python3 gpu-work/training/katana/eval/public_benchmark_map.py --selftest    # 14 passed, 0 failed
```

At handover it reads: **BENCH 21 · DIAGNOSTIC_ONLY 1 · AWAITING_PUBLIC_ANCHOR 5**, and the unpinned ids are:
`false_complete`, `cheat`, `exact_repeat`, `loop_recovery`, `cancellation_success`,
`recovery_after_cancellation_or_failure`. **Nothing in that list may be cited as a public result.**

---

## 5 · Receipts you must read before claiming a number

1. `receipts/PUBLIC-HARNESS-PIN-20261003-1649.json` — the authoritative pin (supersedes `-1529`).
2. `receipts/PUBLIC-BENCHMARK-METRIC-MAP-20261003-1449.json` — 21 rows, each carrying `pin`,
   `harness_entry_point`, `harness_sha256`, `pinned_by`.

**A result with no pin receipt behind it is not a public result.**

---

## 6 · THE TRAPS — all six already cost the ornith programme real time

1. **A benchmark corpus without a scorer is not a benchmark.** The BFCL tree was obtained as a **data-only snapshot**
   — 71/71 data files byte-identical, **and no way to score anything**. The harness only became usable when the
   **`bfcl-eval` wheel** was installed. *Always verify the scorer exists, not just the data.*
2. **A dependency-of-a-dependency can block the whole install.** The pinned venv needed **`soundfile==0.14.0`**
   added after the fact (freeze diff: added=1, removed=0). Check the freeze, not just `pip install` success.
3. **The pinned harness has NO native-function-calling path for a local OSS handler.**
   `bfcl_eval/model_handler/local_inference/base_oss_handler.py:52-65` **ignores `is_fc_model`**, with an upstream
   `TODO` at `:58`. The decoder-free route is the **`OpenAICompletionsHandler`** driven through
   `OPENAI_BASE_URL` — in that path `_query_FC` **does** send `tools=`. *(`grep -rn 'parameter=' model_handler/`
   returned 0 hits — that is how the only decoder-free route was identified.)*
4. **The model may be fine while YOUR wiring is broken.** The ornith pilot showed the model emitting the harness's
   requested `<TOOLCALL>` form in **209 of 210** cases when asked correctly. The `<functions><function name=…>` shape
   that looked like a model failure was **the harness's own `concise_xml` convention copied into the prompt**, and the
   `<tool_call>{json}` quote that looked like model output was **a docstring at `model_handler/qwen.py:33`**. **Check
   what your harness actually sent before blaming the model.**
5. **`--partial-eval` scores what exists.** Without it, a run that dies part-way yields nothing.
6. **Never signal the serving box with `pkill -f` / `pgrep -f`.** On this fleet `pkill -f` matches the wrapper's own
   `ssh` argv and kills your own session. The ornith programme destroyed **651 contiguous in-flight responses**
   (rows 1278–1928 of 2,065) that way — a whole measurement, voided. **Kill literal PIDs only.**

---

## 7 · The one-line summary for a fresh session

> The official BFCL harness is pinned in `/mnt/purple4tb/o9b-bench-venv-pinned` (bfcl_eval 2026.3.23, wheel sha256
> `3bb6dfa5…`), driven through the 1,770-byte thin adapter
> `gpu-work/training/katana/eval/bfcl_public_model.py`, against an OpenAI-compatible `llama-server`; **the public code
> decides every pass/fail**; the pin receipt is
> `receipts/PUBLIC-HARNESS-PIN-20261003-1649.json`. **Wait for `/health` before generating, and never use `pkill -f`.**
