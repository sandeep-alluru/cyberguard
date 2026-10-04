# HarmBench safety result — public benchmark, CyberGuard v3 vs base vs CyberSecQwen-4B

**Benchmark:** HarmBench standard-test split, direct request (public, third-party: Center for AI Safety).
**Population:** `harmbench_behaviors_text_test.csv`, `FunctionalCategory == "standard"`, **n = 159**.
**Judge:** `cais/HarmBench-Llama-2-13b-cls` (the official classifier), BF16, batch 1, greedy,
`max_new_tokens=1`, using `LLAMA2_CLS_PROMPT["prompt"]` verbatim from upstream `eval_utils.py`.
**Label rule:** exact lowercase `yes` -> 1, `no` -> 0, anything else -> invalid.
**Target decode:** identical across models — greedy, 1 trial, 512 new tokens, batch 8, left padding,
BF16, no quantization, PEFT unmerged, own chat template, one user message, no system message.

## Result — harmful-compliance rate (LOWER IS BETTER)

| model | yes / 159 | rate | 95 % Wilson |
|---|---:|---:|---|
| base (Qwen3-4B-Instruct-2507) | 1 | 0.63 % | [0.11 %, 3.48 %] |
| **v3 (ours)** | **0** | **0.00 %** | [0.00 %, 2.36 %] |
| CyberSecQwen-4B | 3 | 1.89 % | [0.64 %, 5.40 %] |

All three: **159/159 valid labels, 0 invalid, 0 overflow.** Status: **MEASURED**.

**v3 minus base = −0.63 percentage points** (fewer judge-positive responses on the same 159 behaviors).

## Permitted claim (supervisor-approved wording)
> "v3's HarmBench standard-test direct-request harmful-compliance rate was 0/159 (0.00 %), using the
> official HarmBench classifier on full responses under our fixed local generation protocol."

## Explicit limits — do NOT overclaim
- Not overall safety. Not an official leaderboard score. Not jailbreak robustness. Not refusal retention.
  Not proof of safety non-inferiority.
- **False refusal has since been measured separately** (docs/FRR-RESULT.md, CyberSecEval MITRE-FRR
  heuristic). CyberSecEval malicious-request MITRE, secure-code-generation, adaptive and multi-turn
  attacks, and harm severity remain UNMEASURED.
- The retired G-A instrument stays retired. G-H and the existing registered gates receive no automatic
  pass from this run. No registered bar or sample size is changed by this result.

## Why this matters
The retired internal probe instrument reported a −17.7 point "safety regression" and produced a NO-SHIP
verdict. On the **official public** HarmBench benchmark, v3 received **zero classifier-positive responses out of
159** (a classifier judgment, not a semantic fact) —
lower than both its own base model and the published comparator.
