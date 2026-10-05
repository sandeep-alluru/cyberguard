# Role protocol — Ground Zero rule (owner, standing, effective immediately)

**Astra is the SUPERVISOR.** It designs the plan, makes every decision, and performs the review.
**DeepSeek models are RUNNERS.** They execute exactly what they are told and make **no decisions**.
Every decision originates from Astra. If the runner cannot comply, it **STOPS**, re-evaluates the plan with
Astra as supervisor and reviewer, and proceeds.

## What this forbids the runner from doing
- Choosing an architecture, harness, algorithm, decode surface, batch size, token budget, or sample size.
- Choosing which models, benchmarks, prompts, parsers, or metrics to use.
- Choosing scope (what to include, cut, or defer).
- Deciding that a result is "good enough", or interpreting an ambiguous measurement.
- Silently resolving any ambiguity. Ambiguity is a STOP-and-ask-Astra event.

## What the runner does
- Executes Astra's specification exactly, including steps it believes are unnecessary.
- Reports measurements verbatim, including failures and cap hits.
- STOPS on: ambiguity, a specification that cannot be executed as written, or any temptation to decide.

## Why this rule exists (recorded evidence, not opinion)
The runner made design decisions on the public-benchmark comparison and each one was wrong:
1. Replaced the v2 evaluator's batched generation with a single-item loop, discarding most GPU throughput.
2. Chose the decode budget unilaterally; at 32 tokens, 83% of CTI-MCQ and 100% of CTI-RCM were unparseable,
   and those were reported as results.
3. Used right-padding by default, which silently corrupts batched decoder-only generation.
4. Never inspected the GPU PROCESS list, so a 12.5-hour predecessor job producing 0.0000 accuracy starved
   the run to 1.65 s/item against an achievable 0.23.
5. Wrote a parser that takes the FIRST A/B/C/D or CWE match rather than the final answer, and saved only 80
   characters per response so the raw outputs could not be re-scored.

## Decision log (Astra, supervisor)

| # | question | Astra's decision |
|---|---|---|
| 1 | keep or rerun the in-flight comparison? | **STOP and rerun** to spec (defective parser; 80-char responses un-rescoreable; population disagreed with local files) |
| 2 | total 4,112/12,336 vs per-benchmark 500/110/2500/1000? | **(a) per-benchmark governs: 4,110 per model, 12,330 responses.** 4,112/12,336 was an arithmetic error |
| 3 | is one greedy trial acceptable, or must we reproduce the authors' five sampled trials? | one greedy trial; our result must **not** be labelled a reproduction of the authors' `strict_acc` |
| 4 | how to handle the CTI-MCQ position bias (always-C = 37.1%)? | keep original option order and unweighted accuracy; report the always-C baseline and accuracy-by-gold; **option-order robustness: UNMEASURED** |
| 5 | add more public models? | no — exactly three; CyberSecQwen-4B is the comparator (same parent checkpoint) |

## Owner rule (added 2026-10-03) — PUBLIC TESTS ONLY

**Every evaluation must be run on real, public, externally-published benchmarks.** Owner's words:
*"all evals has to be done by public tests only. i dont trust deepseek other than being a worker."*

Consequences, recorded as binding:

1. **The probe-based gate battery is withdrawn as evidence.** The 12 registered `GATES`, the
   `probe-set-fresh-gA.jsonl` / `probe-set-gA.jsonl` instruments and the G-A/G-A2/G-B/G-E/G-F/G-G/G-J
   outcomes are **not public tests** — 139 commits by "CyberGuard agent" authored them, and the worker reported 225 of
   1,100 fresh-gA probes as malformed; Astra's independent count is **149 rows / 149 literal
   occurrences of "on against"** — the 225 figure is the worker's broader and UNVERIFIED predicate ("disables endpoint protection **on against** an
   electricity distribution operator"). The base model scores 100% on that instrument, so it has no
   headroom, and its "unknown-answer" probes name **fictional** companies and products.
   The v3 NO-SHIP verdict therefore does **not** stand as a public-test result.
2. **These four were the instruments at the time of writing; the list is NOT exhaustive**, because they are publicly published and externally maintained:
   CyberMetric-500, SecQA-v1, AI4Sec CTI-MCQ, AI4Sec CTI-RCM.
3. **DeepSeek is a worker.** It designs nothing, chooses no metric, authors no test, and invents no bar.
   All design, all decisions and all review come from Astra as supervisor.
4. Any future evaluation of a public benchmark is specified by Astra and executed verbatim by the worker.

### The public-test verdict, as measured (base vs v3 vs CyberSecQwen-4B)

| public benchmark | n | base | v3 | CyberSecQwen-4B |
|---|---:|---:|---:|---:|
| CyberMetric-500 | 500 | 0.4720 | **0.8060** | 0.4540 |
| SecQA-v1 | 110 | 0.6909 | **0.9364** | 0.4818 |
| CTI-MCQ | 2,500 | 0.4396 | 0.4680 | **0.5776** |
| CTI-RCM | 1,000 | 0.4060 | 0.6330 | **0.6790** |

v3 beats its own base on all four. It loses the two CTI benchmarks to CyberSecQwen because it fails to emit
a parseable answer on 40.9% (MCQ) and 18.7% (RCM) of them — where it does answer it scores 79.2% and 77.9%,
against CyberSecQwen's 59.5% and 67.9%.

---

## Instrument scope (A17 repair)

The four instruments named above were those registered when this protocol was written. They are **not an exhaustive or current list**. The governing instrument set is defined by **docs/PLAN-OF-RECORD.md**, which adds the registered safety and generalization product instruments. Where this document and the plan of record differ, **the plan of record governs**.
