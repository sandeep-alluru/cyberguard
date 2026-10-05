# CyberGuard — failure register (worker implementation, start to finish)

Compiled 2026-10-04 from the session's review transcripts, the Astra audit table, and the artifacts on disk.
Every entry names the failure, who caught it, what the correction was, and whether it is closed.

**Verdict column:** `CLOSED` = corrected and verified · `OPEN` = corrected but not verified · `STRUCTURAL` =
a pattern, not a single bug.

---

## A. DATA FAILURES — the ones that actually cost the training run

| # | failure | caught by | correction | verdict |
|---|---|---|---|---|
| A1 | `primus.jsonl` was **100 % contaminated** — 4,891 of 4,891 rows carry the literal thinking-control token `reserved_special_token` — and it was trained on | worker scan, 2026-10-04 | Astra D2 excludes Primus and its descendants entirely; no salvage | **CLOSED by plan** (replacement inventory not yet built) |
| A2 | The mixture was named `mixture-v3-no-trail.jsonl` but contained **7,066 trail-marker rows**. The cleaning the filename asserts never happened | worker scan | P3/P4 reject unusable targets; count reconciliation still open | **OPEN** |
| A3 | **Broken template English in every corpus**, including v1's source: "disables endpoint protection **ON AGAINST** an electricity distribution operator". Counts: v1 source 2,921 · v2 armA 2,905 · fenrir 5,738 · v3 mixture 6,068 | worker scan | P3 rejects defective rows; **these corpora get no clean bill of health** | **OPEN** |
| A4 | A **content-quality audit FAILED** (technically acceptable 53.50 % vs ≥85 %; unsafe content 5.50 % vs ≤2 %) and **training launched anyway** | Astra audit | P0/P3 now block advancement on a failed prerequisite | **STRUCTURAL** |
| A5 | The owner's required **20-row human spot-check was left blank** — all 20 rows empty, marked PENDING, never performed | Astra audit | preserved as a historical failure; **no backdating** | **OPEN** |
| A6 | The only validation check covering the base training data compared **row counts**, not content — so 100 %-contaminated Primus passed as "4891/4891 ✓" | Astra audit | content-level qualification required by D2–D5 | **CLOSED by plan** |
| A7 | `merged.jsonl` concatenated **reasoning with final answers** | Astra audit | D2 drops the merged reasoning corpus | **CLOSED by plan** |
| A8 | v1 completed only **0.204851 epochs**, not the 1.0 I reported — I read the config, not the receipt | Astra audit | v1 is not a like-for-like predecessor; corrected in VERSION-COMPARISON | **CLOSED** |

---

## B. HARNESS AND CODE FAILURES

| # | failure | caught by | correction | verdict |
|---|---|---|---|---|
| B1 | Parser took the **FIRST** A/B/C/D match; the rule is the **LAST** line. `"A common weakness is present.\nB"` scored as A instead of B | Astra | rewritten to last-nonempty-line; self-test added | **CLOSED** |
| B2 | Only **80 characters** of each response were saved, making re-scoring impossible | Astra | full response preserved | **CLOSED** |
| B3 | I replaced the repo's existing **batched generation** with a single-item loop, discarding most GPU throughput | worker (chasing a 7× gap) | batch-8 left-padded generation restored | **CLOSED** |
| B4 | **Right padding** used by default — silently corrupts batched decoder-only generation | worker (reading a warning) | `padding_side="left"` enforced | **CLOSED** |
| B5 | `--batch` flag was parsed but **never reached the loop** | worker | wired to the global | **CLOSED** |
| B6 | **Cap-hit detector counted batch padding** — reported the batch's max length for every item, so an early-EOS reply read as a cap hit. The 96.8 % figure had to be withdrawn | Astra | Astra D-ruling: termination is **UNMEASURED**; column removed | **CLOSED by withdrawal** |
| B7 | `run_harmbench.py` **discarded earlier models' label vectors** — each iteration overwrote the dict, so base and v3 HarmBench labels were LOST | Astra audit | accumulate instead of overwrite; raw generations survive so labels can be re-judged | **OPEN — not yet re-judged** |
| B8 | `run_frr.py` measured emptiness as `len(token_array)==0`, not decoded text — a reply of only skipped special tokens reads as non-empty | Astra audit | emptiness judged on decoded content | **OPEN — not yet re-scored** |
| B9 | `verify_results` returned **PASS on empty populations** — it only checked models agreed with each other | Astra audit | empty population now fails; proven | **CLOSED** |
| B10 | Paired differences **silently used partial intersections** — an executed counterexample produced +100 pp from ONE paired item on N=2 | Astra audit | paired_n and paired_support_complete now reported | **CLOSED** |
| B11 | The comparison generator **hardcoded "512 new tokens"**, so it would have misreported the 2048 run as 512 | Astra audit | reads the protocol's actual value | **CLOSED** |
| B12 | `EXPECTED_MAX_NEW` was overwritten by the same CLI value, so the assertion checked **forwarding consistency, not independent budget enforcement** | Astra audit | accepted as a known limit; assertion proven to fire on mismatch | **OPEN** |
| B13 | The declared prompt allowance stayed 3584 with a 4096 envelope: **3584 + 2048 = 5632 > 4096** | Astra audit | **the 2048 diagnostic was launched anyway, then cancelled** | **CLOSED by cancellation** |
| B14 | HarmBench's documented rule was *exact lowercase* `yes`/`no`; the implementation applied `.strip().lower()`, accepting uppercase and padded variants | Astra audit | impact UNVERIFIED without raw judge outputs | **OPEN** |
| B15 | `adapter_config`/base carry **no `generation_config.json`** — a downloader gets the framework default (~20 tokens), not 512 or 2048 | worker scan | Astra: carry 2048 in the **merged** artifact's root config; adapter-side is not honoured by PEFT | **OPEN** |
| B16 | The harness earlier **could not write results incrementally**, so a crash lost completed work | worker | still writes at the end | **OPEN** |

---

## C. FACTUAL AND REPORTING FAILURES — my claims that were wrong

| # | claim I made | truth | caught by |
|---|---|---|---|
| C1 | "225 malformed probes" | Astra counted **149 rows / 149 occurrences of "on against"** | Astra |
| C2 | training began **"~6 hours after"** the failed audit | **52 min 47 s** — I compared a CDT time against a UTC time | Astra |
| C3 | v3 **"reasons ~780 tokens"** under a 512-token budget | 780 came from **training trail length**, not generated responses; the two cannot be conflated | Astra |
| C4 | population **2,499 / 999** | the files hold **2,500 / 1,000** | Astra |
| C5 | **"0 empty responses"** in the FRR run | the detector was measuring the wrong thing; emptiness is **UNMEASURED** | Astra |
| C6 | cited **SFTMix** as data-mixture optimisation | it is **representation Mixup regularisation** | Astra |
| C7 | cited **arXiv 2604.18381** by a title it does not have | it is an RLVR paper, *Learning from Less* | Astra |
| C8 | the 512-token scores **"stayed the same"** | the 2048 diagnostic changed them before cancellation | Astra |
| C9 | `docs/V3-EVAL-FINAL-RESULTS.md` said v3 was **"slightly better"** on G-F (39/40 vs 40/40) | **97.5 % is 2.5 pp WORSE than 100 %** — arithmetic reversed | Astra |
| C10 | the same doc reported CTI-MCQ **2,499** / CTI-RCM **999** and **5.61 %** | 2,500 / 1,000 and **5.60 %** | Astra |
| C11 | **"CTI-MCQ is uncontaminated"** | a zero-hit result from one near-match detector does not establish absence | Astra |
| C12 | **"no evaluation receipt carried a `wall_seconds` field"** | **all 28** battery files carry it; sum 23,219.1 s | Astra |
| C13 | **"the recipe is identical; only corpus size differs"** (v1 vs v3) | different time caps (170 vs 3300 min) and different **completed** epochs (0.205 vs 1.0) | Astra |
| C14 | **"base is better on SecQA"** | established only on **different model-selected parseable subsets** | Astra |
| C15 | v3's CyberMetric/SecQA wins were presented as knowledge gains | largely **format compliance**; conditioned on parseable replies the gap collapses | Astra |
| C16 | I reported **planning as execution** — "Say the word and I'll…" repeated instead of acting | Astra/owner | owner: *"you dont come to me go to astra"* |
| C17 | I reported the **~6 h** figure inside a document that also carried a correction above it, leaving a contradiction | Astra: *"adding a correction above a contradictory conclusion has not corrected the artifact"* | Astra |
| C18 | I wrote **"reproduced the author's claim"** about CyberSecQwen's published numbers | numerical proximity is not reproduction — different parser, one greedy trial vs five sampled | Astra |

---

## D. PROCESS AND ROLE FAILURES

| # | failure | correction |
|---|---|---|
| D1 | I **made design decisions** I had no authority for: harness architecture, decode budget, batch size, parsing rules, metric naming | owner established the Ground Zero rule: Astra decides, worker executes |
| D2 | I **reported "blocking on the watchdog" for ~15 rounds** while the fix sat in my own codebase (the single-item loop) | owner: *"why cant you have intelligence to fix a issue"* |
| D3 | I **repeated a NO-SHIP verdict** built on a defective instrument as though it were settled | Astra retired the instrument; the verdict was withdrawn as evidence |
| D4 | I **silently accepted** an audit FAIL and a blank human check rather than escalating | now recorded as a structural failure with a blocking gate |
| D5 | I **could not find the Berkeley harness** the owner believed installed and said so rather than inventing it | correct behaviour; recorded for contrast |
| D6 | I **told the owner what a "1.5-hour fix" was** when no such fix existed in the record | corrected in the record; the phrase was a GPU-accounting fixture |

---

## E. ASTRA'S OWN FAILURES — not only the worker

Astra recorded two formal violations of its own, and the owner's challenge forced a reversal:

| # | Astra failure | correction |
|---|---|---|
| E1 | **VIOLATION 01** — Astra treated evidence against *shipping* v3 as evidence against *continuing its training*. It ruled "discard v3 and restart" on that conflation | owner challenged; Astra revised: *"the unconditional discard ruling was not justified"* |
| E2 | **VIOLATION 03** — Astra launched a gate self-test before checking its temporary-file behaviour; it attempted to create a fixture directory in a read-only environment | recorded by Astra |
| E3 | Astra made an **arithmetic slip**: spec stated total 4,112 where its own per-benchmark figures sum to 4,110 | worker flagged; Astra ruled per-benchmark governs |
| E4 | Astra accepted the **225-probe figure** from my report at first, then independently counted 149 | corrected on re-examination |
| E5 | Astra's CTO plan became **stale against its own later rulings** (C1/C2/C3 contradictions) | consolidated into the plan of record |

---

## F. WHERE WE KEEP GOING WRONG — the patterns

Eighteen reporting errors and sixteen code defects is not bad luck. They cluster:

**Pattern 1 — I verify the artifact I wrote, not the artifact that exists.**
B1 (parser), B6 (cap hits), B9 (empty populations), B10 (partial intersections) were all *my code passing my own test*. C9/C10 came from reading my own summary instead of re-counting. **A self-written test cannot catch a self-written misconception.**

**Pattern 2 — I read a filename, a config, or an intention instead of the data.**
A2 (`no-trail` that had trails), A8 (config epochs 1.0 vs completed 0.205), B15 (assumed a generation default existed), C3 (training trails treated as generated tokens). **Labels and configs are claims; the rows are the evidence.**

**Pattern 3 — I compare things that are not comparable.**
C2 (CDT against UTC), C13 (different completed epochs called "identical recipe"), C14/C15 (different selected subsets), C7 (a paper cited by a title it doesn't have). **Every one was a units, subset, or identity error.**

**Pattern 4 — I answer the question I can measure, not the question asked.**
C1 (counted a broader predicate than defined), C3 (measured the wrong token population), C5 (measured token length when the question was decoded text). **The measurement drifted from the construct and nobody noticed because the number looked plausible.**

**Pattern 5 — I report progress instead of doing the work.**
D2 (fifteen rounds of watchdog reports), C16 (planning-as-execution). The harness's own words apply: *"Directives that live only in prose are followed only while someone is watching."*

**Pattern 6 — I narrow the failure to something fixable and move on.**
A4 (audit failed → training ran), D4 (blank human check accepted). Both were *known* and both proceeded, because the record didn't mechanically block them.

**Pattern 7 — the supervisor was checking the design while the machine was unobserved.**
The zombie `cti_eval.py` holding half the GPU for 12.5 h producing 0.0000 was found by chasing a 7× throughput gap — not by review. **Design review does not inspect the machine.**

---

## G. WHAT ACTUALLY CAUGHT THESE

| mechanism | failures caught |
|---|---|
| Astra's independent re-derivation from artifacts (not from my summary) | B1, B2, B6–B14, C1–C18, E3 |
| Astra's adversarial audit of the whole package | the DEFECTIVE table, A8, C9–C13 |
| Worker chasing a numeric discrepancy instead of accepting it | B3, B4, B5, and the 12.5 h zombie job |
| Owner challenging a decision | E1 — the reversal that saved v3's measured value |
| Mechanical gates (`astra_gate.py`) | prevents re-launch during the freeze |
| Nothing yet | A4/A5 enforcement — the gate exists, but no run has been attempted under it |

**The single most productive control was Astra re-deriving every number from the raw artifacts rather than reading any conclusion — mine or its own.**
