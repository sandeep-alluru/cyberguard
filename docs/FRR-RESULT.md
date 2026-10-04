# CyberSecEval MITRE-FRR result — public benchmark, CyberGuard v3 vs base vs CyberSecQwen-4B

**Instrument:** CyberSecEval MITRE-FRR, `meta-llama/PurpleLlama` at pinned commit
`172c1074069eb88ec834124272c1b1c4f8893445`.
**Population:** all **750** entries, file order, `mutated_prompt` verbatim, no filtering or sampling.
**Scorer:** upstream `is_response_llm_refusal()` **unchanged**, default `max_chars=220`, whole response.
**Verify:** git blob SHA-1 `15e58a34ea160aa5e1a75fd4437e60eab0a2f7f6` — MATCHED before execution.
**Decode:** identical across models — greedy, 1 trial, 512 tokens, batch 8, left padding, BF16,
no quantization, PEFT unmerged, own chat template, no system message, no input truncation.
**Integrity:** all three MEASURED. The "0 empty responses" figure produced by the original runner is
**WITHDRAWN** — its detector tested `len(token_array)==0` rather than decoded content, so it could not
detect a response that decodes to empty text. Emptiness is **UNMEASURED** pending re-scoring.

## Result — refusal rate on BENIGN cybersecurity requests (upstream heuristic)

| model | refusals / 750 | FRR | 95 % Wilson |
|---|---:|---:|---|
| base (Qwen3-4B-Instruct-2507) | 32 | 4.27 % | [3.04 %, 5.96 %] |
| **v3 (ours)** | **230** | **30.67 %** | [27.47 %, 34.06 %] |
| CyberSecQwen-4B | 8 | 1.07 % | [0.54 %, 2.09 %] |

**v3 minus base = +26.40 percentage points** (more refusals of benign requests).

Paired counts (base refusal, v3 refusal): **00 = 493 · 01 = 225 · 10 = 27 · 11 = 5**.
- **01 = 225**: base received a non-refusal label and v3 a refusal label — **225 requests where the
  upstream heuristic flipped from non-refusal to refusal**. A heuristic non-refusal label does not prove a
  useful answer was supplied.
- 10 = 27: base refused, v3 answered

## Permitted claim (supervisor wording)
> "Under our fixed local generation protocol, v3 had an upstream-heuristic refusal rate of 230/750
> (30.67 %; 95 % Wilson interval [27.47 %, 34.06 %]) on the pinned English CyberSecEval MITRE-FRR
> population."

## Explicit limits
- **Not** validated semantic false-refusal accuracy — the public implementation supports a reproducible
  **heuristic** measurement; its semantic accuracy on these models is **UNMEASURED**.
- Not a useful-answer rate, secure-code rate, overall safety, or an official leaderboard score.
- **Keep separate from HarmBench.** Two one-sided measurements. Do not average, subtract, or combine into
  a safety score, and do not infer "safe and useful". No significance, equivalence or non-inferiority
  claim is authorised. No registered gate or sample size is changed.

## The two safety measurements side by side

| measurement | base | v3 | CyberSecQwen-4B | better |
|---|---:|---:|---:|---|
| HarmBench harmful compliance (lower better) | 0.63 % | **0.00 %** | 1.89 % | v3 |
| MITRE-FRR benign refusal (lower better) | 4.27 % | **30.67 %** | **1.07 %** | CyberSecQwen |
