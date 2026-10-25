# P2 Data Gate calibration protocol — **APPROVED**; the confirmation draw is the next measurement

**Status:** APPROVED 2026-10-23 · **Item:** D-1 · **Registered values:** §9 below
**Basis:** the protocol's boundary decisions, taken 20261015 and recorded as 20261015-2120 (ada461b).
**Accepted:** the 2026-10-23 authorisation of the CyberGuard build, which accepts the sample sizes, uncertainty allocation and agreement rules that this protocol had flagged as needing acceptance. The accepted values are listed in §9.

**This protocol authorizes no sample draw, no labels, no scorer tuning, no training, no removals, no source edits and no Data Gate pass.** Accepting a measurement design is not executing it. The registered Data Gate limits remain **unsafe <1%, off-topic <2%, shallow <5%**, plus zero known unexplained cross-row leakage and verified metadata/provenance/rights. §9 names the execution dependencies that stand between this protocol and its first draw, so that *approved* is never read as *ready to run*.

## 1. Separate the populations and decisions

**Development calibration population:** the immutable original 140,545-row mixture, SHA-256 `75b5099c568313f2ceada6f79746e51840b5240d943e952c2f2ebe3c3318fc90`, at `<programme-tree>/data/v3/mixture/mixture-v3-no-trail.jsonl`. Original zero-based row IDs are authoritative. Flag file: `<workspace>/<other-workspace>/cyberguard-v4/data/<quality-flags>/flagged-rows.jsonl`, SHA-256 `9044dabcb625f383e6f9ba3c1166aba611c984bad0427df0a8aa33329e3eaf03`. There are 37,927 flagged and 102,618 unflagged IDs. These are **detector strata**, not true defect classes. Development measures scorer behavior and the original pool; it cannot qualify R2 or a later curated corpus.

**Qualification population:** the approved, frozen retained candidate with its own exact row count N, SHA-256, source→retained ID map, source/type/provenance/rights records and approved curation receipts. **This population exists now** — see the amendments in §9 — and the candidate is pinned at execution, not here: the Phase-C rebuild is `data/v4/corpus-v4-r3.jsonl`, **108,978 rows, SHA-256 `7798c4f589b855caa32dc9d6335926e856f78fe649419dd9e516b7ba1a6413ff`**, and the removals in D-4 and D-5 produce the frozen candidate `data/v4/corpus-final.jsonl`, whose **N and SHA-256 are fixed at the freeze** and are the values this protocol's confirmation draw uses. R2's 135,503 rows are a working copy, not this population. Qualification uses a separate, post-freeze probability sample and a locked rubric/scorer procedure. No percentage measured on the original, workbook, pilot, or selected parseable subset transfers to the candidate.

The unit for the three registered rates is a **physical corpus row/presentation**, including retained multiplicity. The original builder intentionally weights refusal ×8 and format ×2; the 4,644 R2 duplicate extras are not automatically bad examples. Report distinct-content counts, multiplicities and descriptive unique-content results separately, without substituting their denominator for the registered row rate. Do not select a weighting/removal policy in this protocol.

Sampling fixed row labels without replacement permits finite-population inference even when literal duplicates share a label. That inference is conditional on the approved rubric/adjudicated labels; it does not account for semantic annotation error. Duplicate presentations are never counted as independent judgements or evidence of broad content coverage.

## 2. Development sample: 4,000 rows, including both detector outcomes

Construct the following **disjoint priority strata** from the full flag-ID inventory. Recount every stratum at execution and fail closed if any input pin/count changes. Counts below were re-derived from the flag file; no sample was drawn.

| Stratum | Exact rule, in this priority order | Population N_h | Draw n_h |
|---|---|---:|---:|
| U-flag | Any `unsafe_*` flag, regardless of other flags | 195 | 195, census |
| O-flag | No unsafe flag; `off_topic` present | 37,330 | 1,403 |
| S-only | Neither unsafe nor off-topic; `shallow_short` present | 402 | 402, census |
| Unflagged | No row ID in the flagged file | 102,618 | 2,000 |
| Total | Complete partition of original rows | 140,545 | 4,000 |

Thus exactly **2,000 of the 37,927 flagged rows** and **2,000 of the 102,618 unflagged rows** are labelled. The 56 off-topic rows that also carry unsafe flags belong to U-flag; overlapping flags are never double-counted. A newly encountered flag signature outside this partition blocks the build rather than being silently discarded. Census of all 195 unsafe-flagged and 402 shallow-only rows deliberately gives those sparse detector strata coverage. It does not establish true unsafe/shallow prevalence.

Within O-flag and Unflagged, use simple random sampling **without replacement**, over sorted original row IDs. Before any labels are exposed, commit: protocol/rubric version, input pins, full stratum-ID inventory hashes, PRNG algorithm/version and seed, selection code hash, selected-ID manifest/hash, and source-row hashes. Use separate committed seeds for development and later confirmation; no reroll, replacement of difficult rows, or post-label sample-size change. The seed is recorded before reading sampled content, not selected after inspecting outcomes. A bounded reference implementation must reject duplicates, out-of-range IDs, strata mismatch and missing selected rows.

Every selected row receives **all three** labels; do not judge only the dimension that caused its flag. Include source strata, language, code-heavy, dual-use, malformed/unreadable and abstention categories in reporting. No claim of per-source accuracy or edge-bucket coverage is permitted when a bucket has too few or no sampled rows. Do not silently add rows to satisfy a bucket; a future augmented diagnostic must be separately registered and excluded from the probability-sample estimator.

Exact duplicate selected rows may be presented once per annotator, with a committed exact-byte hash→all selected-row-IDs map. Emit label records for every sampled ID with multiplicity/inclusion probability preserved; report both sampled presentations and distinct annotated content. Do not deduplicate merely similar rows, infer equality from a template prefix, or count a reused judgment as another independent judgment.

## 3. Label rubric: context and target content, not marker matching

Annotators inspect the full user request and assistant training target, with relevant system text, locally. They are blinded to detector flag, source uploader, stratum, prior score, model/teacher identity and each other's verdict. A separate custodian retains the inclusion/provenance map. Never truncate content silently; unreadable or unsupported material receives an explicit unresolved disposition.

Each dimension is independently recorded as `DEFECT`, `NO_DEFECT`, or `UNRESOLVED`, with a short evidence-grounded reason and local row hash:

- **Unsafe:** target materially teaches or enables offensive execution, credential abuse, persistence/evasion, payload deployment, exploitation or harmful abuse, including refuse-then-comply. Offensive terminology, quoted attack evidence or detection rules alone are not sufficient. Evaluate the actual actionability and defensive context; do not turn every command into an unsafe label.
- **Off-topic:** task/target is substantively outside the registered cybersecurity scope, or the answer is unrelated to the requested cyber task. Report declared replay/format/refusal roles, but do not exempt a source or reinterpret the domain without an approved rubric amendment.
- **Shallow:** target is vacuous/generic policy or best-practice recitation where a substantive defensive task requires grounded reasoning, specificity or bounded uncertainty. Correct concise refusals, clarification requests and legitimately short requested forms are not shallow merely because short. Length-only tests and the broken 53.5% acceptability instrument are not reference truth.

Unknown technical meaning is not `NO_DEFECT`. Annotators may find “not a defect” or “the detector is wrong”; these are genuine adjudication outcomes. Preserve primary judgments and the original detector output. All unresolved labels count as defects for that dimension's conservative statistical upper bound and separately remain a manual-resolution barrier for admission. Malformed/unreadable/unsupported rows cannot be automatically admitted; no successful JSON parse implies semantic safety. Rights/provenance uncertainty is separately unresolved even if the three content labels are clean.

## 4. Independent scorer procedure and pre-registered tolerance

Reference scoring uses **two independently working cybersecurity-competent annotators A and B**, with documented identities/competence, independent initial judgments, identical locked instructions and mixed presentation order. A third competent adjudicator C resolves every disagreement using the actual row and checkable evidence; C may return unresolved. Initial A/B records are immutable and written before either annotator sees the other's or C's verdict. The semantic reference is adjudicated content annotation, not the existing regex detector or an uncalibrated model probability.

Required annotator identities, availability, local access and annotation budget are **not supplied by this protocol**. Existing Codex/Claude sessions may independently annotate this protocol or prepare clearly labelled triage, but are not silently substituted for required competent human annotation or for the outstanding response adjudication. No person is contacted this cycle. No external scorer/API or <previous-analyst> training/promotion is authorized. This sample does not satisfy <previous-analyst>'s separate human-labelled training/held-out/calibration contract merely by having 4,000 rows.

Before population labels, a separately frozen **300-row reference-control cohort** is specified: 100 primary controls for each dimension (50 positive / 50 negative), independently established with row-level reasons by a qualified reference author and verified by C before A/B see it. Controls are local/publicly permitted material, with rights and hash records, and their assembly is the next step in the protocol. Include context-sensitive clean defensive commands and refuse-then-comply controls in the unsafe cohort (at least ten of each within its 50/50 allocation). Controls are not drawn/adapted from observed development mistakes and never enter population-rate denominators. Creation/scoring awaits an accepted protocol and permitted local evidence; no data generation occurs now.

**Initial scorer acceptance bars, before adjudication:**

1. On reference controls, each A/B annotator correctly labels at least **48/50 positive and 48/50 negative primary controls per dimension**. No unsafe refuse-then-comply control may be labelled `NO_DEFECT`; unresolved is not a correct control answer. This is a bounded instrument check, not a demonstrated population error guarantee.
2. Development initial **case agreement ≥95% per dimension in each of the four strata**; disagreements and unresolved cases remain explicit. Also report positive/negative agreement and full confusion tables; a high overall agreement under rare positives is not proof of sensitivity. Undefined positive agreement or recall is `UNMEASURED`, never 1.0.
3. Absolute difference between A and B **population-weighted defect-rate estimates**, and between each scorer and the adjudicated estimate, must be no more than **0.25 percentage points unsafe, 0.50 points off-topic, 1.00 point shallow**. These are agreement tolerances, not replacements for the <1/<2/<5% Data Gate limits.
4. Resolve every A/B disagreement through C, preserve both initial decisions and C's rationale, and retain unresolved outcomes conservatively. If any instrument/control/agreement bar fails, report **SCORER NOT CALIBRATED**. Do not edit labels until agreement appears, drop cases, relax tolerance or proceed to final qualification. Remedy requires an explicitly amended, re-validated protocol and a fresh independent control/development-validation plan.

The unchanged frozen regex classifier is the detector under audit, not a third independent reference annotator. Against adjudicated labels report per-dimension weighted prevalence, precision/recall/FPR/FNR with denominators, disagreement/abstention counts and uncertainty. The unflagged 2,000-row draw measures missed defects; absence of observed positives does not prove zero false negatives. No automatic-negative admission is conferred by these results, and no classifier promotion claim follows without its separate accepted contract.

## 5. Development population estimates and uncertainty

For each dimension, compute `p_hat = sum_h (N_h/N) * (k_h/n_h)`, with all selected IDs retained. The raw 4,000-row fraction is deliberately biased by oversampling and **must not** be presented as the original population's defect rate. N_h/N and n_h/N_h come from the frozen inventory, not rounded percentages; keep overlaps between label dimensions separate.

U-flag and S-only are censuses, so their adjudicated finite-population defect fractions are exact conditional on labels. For O-flag and Unflagged, construct one-sided exact finite-population hypergeometric upper bounds. Allocate family error **0.05/(3 dimensions × 2 sampled strata) = 1/120** to each of those six upper bounds. The dimension's conservative population upper bound is `sum_h (N_h/N)*U_h`, using the exact census fractions for the two census strata. Bonferroni then provides simultaneous ≥95% sampling coverage for the three weighted upper bounds, conditional on labels; no independence between dimensions is assumed.

Preserve initial A/B estimates alongside adjudicated estimates. Unresolved cases contribute to the conservative numerator, not a reduced denominator. These measurements diagnose the original pool and instrument; **even a development upper bound below a Data Gate limit does not qualify any training candidate**. The original pool is neither the final retained corpus nor a held-out public model benchmark.

## 6. Final Data Gate confirmation: one fresh draw after candidate freeze

Entry: accepted protocol and scorer qualification, completed required P1 controls and the outstanding adjudication prerequisite, approved curation/adjudication and final candidate identity, full metadata/provenance/rights records, exhaustive cross-row resolution and benchmark-exclusion evidence. Two required annotators and an adjudicator are assigned and the annotation budget is approved. Freeze rubric and scorer procedure before candidate labels; do not tune to confirmation outcomes.

For **N ≥6,000**, draw **6,000 candidate row IDs uniformly without replacement**, one committed independent post-freeze seed. For **N <6,000**, label the full N-row census; a sample smaller than 6,000 is not a discretionary economy. Score every selected row on all three dimensions under the same independent procedure, preferably with a confirmation annotator pair that did not see development rows/labels. Any required role change must be accepted and pass the frozen reference-control procedure before confirmation labels. The 300 controls are shared instrument controls, not population records; requalification with new annotators adds separately recorded work.

The draw is from **all candidate rows**, including detector-negative rows. Do not stratify the qualification sample by detector output, preferentially remove previously labelled IDs, or replace inconvenient/overlapping rows. Record overlap with development by row ID and exact content hash; a uniform fresh design may include such rows. Never reuse old development labels as new independent judgments or call an overlapping content subset independent holdout. Prior annotated content is blinded and, where required, routed to the accepted fresh annotator pair. These are corpus-quality samples, not downstream public benchmark test sets; training/evaluation benchmark isolation remains a separate mandatory check.

For each dimension with threshold t, define `M0 = ceil(N*t)` using rational thresholds 1/100, 1/50 and 1/20. Null: candidate defect count M ≥M0 (rate at least t). Given k adjudicated defects including unresolved cases in n rows, compute the **exact hypergeometric lower-tail p-value** `Pr[X ≤ k | population N, defect count M0, sample n]`. Use **alpha = 0.05/3 = 1/60** per dimension, giving simultaneous familywise sampling error ≤5%. Equivalently invert this test to an integer upper defect count M_U and require **M_U/N < t**, strictly. Exact census uses the actual K/N with the same strict inequalities. Round neither rates nor limits for decisions.

At every bound, preserve N, n, k, alpha, M0, p-value, M_U, upper rate, numerical method/code hash and the pass/fail comparison. Handle infeasible or unreadable inputs as failure, not a zero count; numeric boundary ambiguity requires independent high-precision verification rather than a favourable roundoff. The provided lgamma-based arithmetic is a **calculation helper**, not a qualified production gate. Verifier must independently validate the finite-population inversion and boundary controls before execution.

Illustration **only**, using the old original population N=140,545 and n=6,000; this is neither an approved final N nor a score:

| Dimension | Gate t | Largest observed k passing the finite-population rule | Upper defect count at that k | Upper rate |
|---|---:|---:|---:|---:|
| Unsafe | <1% | 44 | 1,405 | 0.99968% |
| Off-topic | <2% | 97 | 2,799 | 1.99153% |
| Shallow | <5% | 264 | 7,006 | 4.98488% |

For the same illustration, zero observed unsafe defects gives an upper count of 93/140,545 ≈0.06617%, **not zero prevalence**. Recompute all critical counts for the actual frozen candidate N; do not copy the example as a constant. Sample size 6,000 is set to give useful rare-defect precision near the 1% gate; it does not assure a pass, cover every edge bucket, or validate the labels.

Final acceptance requires **all three** approved upper-rate comparisons below their unchanged thresholds, accepted scorer/reference-control procedure, **no unresolved sampled semantic case** and no unresolved mandatory admission dependency, plus exhaustive non-statistical Data Gate criteria. Statistical sampling does not waive approved row-exclusion/adjudication decisions or clear known unexplained leakage, missing rights or required metadata merely because the aggregate bound passes. Known unsafe findings must receive the approved row-level disposition; this protocol authorizes neither retaining nor deleting them.

This design allows **one** confirmatory draw for a frozen candidate. Failure remains failure. No optional stopping, repeated draws until pass, post-label sample expansion, denominator changes or selective rescoring. Any changed candidate or new attempt requires a new approved preregistration and multiplicity/error-budget decision before labels; the original failure/evidence remains preserved. Development estimates cannot be used as a second qualification attempt.

## 7. Deliverables, workload and resources before execution

A later authorized executor must write local, append-only evidence with: frozen population/stratum manifests and code pins; selected-ID/hash/inclusion-probability manifests; independent A/B initial labels and C adjudications; duplicate-content correspondence; instrument controls; per-dimension raw/weighted statistics and bounds; unresolved cases; rights/provenance/metadata and cross-row gate evidence; the final gate-outcome table, one row per gate with its outcome. Preserve every selected row ID and original detector result. Labels contain checkable local evidence references, not secret values or external uploads.

Planned **initial** annotation volume: 4,000 development rows ×2 =8,000 row annotations; 6,000 confirmation rows ×2 =12,000; 300 reference controls ×2 =600: **20,600 initial row annotations**, each with three labels, plus reference authoring, sampled-row spot checks, adjudication and any new confirmation-panel requalification. Deduplicating exact repeated content may reduce distinct viewing workload but not the selected-row denominator. Human hours and attainable agreement are **UNMEASURED**. Time the first 50 development row annotations per annotator after approval, while preserving the fixed full sample; use timing to check remaining program labor ceilings, never silently shrink the sample. If the approved aggregate annotation ceiling is insufficient, block and re-plan before further spend. The outstanding response-annotation populations and budgets are not reduced or satisfied by these corpus annotations.

Annotator/labor/rights constraints are explicit execution dependencies, not a reason to claim this protocol sampled or qualified data. No new GPU need: selection and statistics are CPU/streaming; no <previous-analyst> training, model generation, paid API, Qwen operation or data transmission. Do not create multi-GB source/fixture copies. Store IDs/hashes/reasons rather than full corpus copies; label rows by streamed lookup under their immutable source hash. Before and after each future command, check free disk against the conservative **30 GiB** stop threshold; below it stop and report without deleting prior evidence.

## 8. Pre-registered failure-corpus checks and verifier checklist

The entire 112-mode set remains registered. The following are the specific checks for this measurement; future model/trainer/serving controls remain deferred under decision 5.

| Corpus IDs | Concrete pass criterion before dependent execution |
|---|---|
| CG-03/04/10/24; COG-24/28/46/51 | Accepted exact protocol/scope, competent annotator identities, actual sampled-row spot checks, current pinned verdict; no training launch or invalid release provenance. |
| CG-05/07/13/14/22; COG-06/15/16/22/35/37/41 | Independent initial scoring and predeclared tolerance; actual sampler/statistic entry points reject wrong counts, missing/duplicate IDs, malformed labels, wrong stratum weights, scalar-input errors and missing predicates. Raw rates never substitute for weighted rates; a defect stops advancement. |
| CG-09; COG-02/03/12/13/14 | Actual refuse-then-comply and context-sensitive clean controls; unresolved/empty required content never silently negative; all selected rows and required edge/bucket limits documented; regenerate without losing corrections. |
| COG-05/07/19/29 | All dimensions and unresolved/missing quantities explicit; partial/aborted annotation cannot be COMPLETE; no pooled mean hides a failed gate or forced truncation. |
| CG-10/23/30/33/36/42/43/44/49/52/56 | Exact source/freeze/renderer/scorer/code identities; proper split/domain scope; zero benchmark leakage; complete blinding audit; source/retained/draw maps and durable provenance. Before a dependent frozen-artifact producer change, byte-identity or explicit approved version transition. |
| CG-11/12/16/17/18/19/20/25/26; COG-25/26/45/47/54/57/58 | Independent annotators with no shared verdicts; local visible named sessions, correct paths, no external transfer; failed/voided evidence retained; exact commit scope, literal delivered report, no bytecode or claims of uptake without evidence. |
| CG-21/23; COG-18/27/32/40/48/50/55/62/63 | Full census/scratch before formal; every check runnable and mechanically linked; incremental label receipts and demonstrated restart integrity for long annotation sessions; fixed sample, full record inventory, no zero-data governance loop narrated as curation progress; two-amendment escalation cap. Future model launch components remain deferred. |
| CG-27; COG-08/09/17/38/39/59/60/61/64/65 | No GPU/trainer work in this protocol. Applicable token/length/recipe/abstention/citation checks remain registered at their later stage; this protocol is not their PASS. Long-row annotation must remain complete or unresolved, never truncated to fit. |
| ORN-02/05/06/09/10/11/13/14/15/16/17/18; SFN-01/02 | Missing evidence not zero; named final corpus plus accepted receipts, verified backup before dependent alteration/launch; actual disk probes and durable storage; no premature duration/completion, checkpoint deletion, service/guard resurrection or Qwen action. Runtime-only items stay deferred. |

The verifier must check: disjoint stratum arithmetic and inclusion probabilities; all 37,927 flagged/102,618 unflagged rows represented by the design; exact sample sizes; blind independent scoring and tolerances; duplicate/multiplicity and overlapping-sample interpretation; confidence/error allocation and strict threshold inversion; unresolved-case handling; candidate-versus-original population separation; workload/budget feasibility; no execution or policy waiver inferred. Missing competent annotator resources, controls, an accepted protocol or full Data Gate evidence stops the draw; it is never an implicit approval.

## 9. Registered values, amendments and execution dependencies

### 9.1 The registered values

**Registered:** 2026-10-23, under the 2026-10-23 authorisation of the CyberGuard build
(item **D-1**).

These are the registered values — the sample sizes, the uncertainty allocation and the agreement
rules this protocol applies — listed here so that nothing is adopted silently:

| item | registered value | where |
|---|---|---|
| development sample | **4,000 rows** over the **140,545**-row original mixture, in the four disjoint strata of §2 | §2 |
| stratum draws | U-flag **195** (census) · O-flag **1,403** · S-only **402** (census) · Unflagged **2,000** | §2 |
| confirmation sample | **6,000 rows** uniformly without replacement for N ≥ 6,000; **full census** for N < 6,000 | §6 |
| per-dimension alpha | **1/60** (= 0.05/3), exact hypergeometric lower tail | §6 |
| development error allocation | **1/120** (= 0.05/(3 dimensions × 2 sampled strata)) per upper bound, Bonferroni across the three dimensions | §5 |
| scorer agreement bars | case agreement **≥95 %** per dimension in each stratum; population-rate difference **≤0.25 pp** unsafe, **≤0.50 pp** off-topic, **≤1.00 pp** shallow | §4 |
| reference controls | **300 rows**, 100 primary controls per dimension (50 positive / 50 negative), **including ≥10 refuse-then-comply and ≥10 context-sensitive clean defensive** controls in the unsafe cohort | §4 |
| Data Gate limits (unchanged) | **unsafe <1 %, off-topic <2 %, shallow <5 %**, plus zero known unexplained cross-row leakage and verified metadata/provenance/rights | §3, §6 |
| draw rules | one committed seed per phase, no reroll, no replacement of difficult rows, no post-label sample-size change | §2, §6 |

### 9.2 The amendments to the protocol, and why

The protocol's substantive text is unchanged, with these amendments only:

| # | amendment | reason |
|---|---|---|
| **A1** | the status line is APPROVED and the accepted values are listed in §9.1 | the accepted values are named, so that nothing is adopted silently |
| **A2** | §1's qualification population names the candidate that exists, with its row count and SHA-256 | the protocol's **substance** is unchanged — the candidate is still frozen before the confirmation draw, and no percentage from another population transfers to it |
| **A3** | §9.4 records the **re-verified pins** | a pin that does not match is a stop condition, so the pins are checked, not assumed |
| **A4** | §9.5 names the execution dependencies that are **not met** | so that *approved* is never read as *ready to execute* |

No threshold was moved, no sample size was altered, no tolerance was relaxed, no statistical method was substituted.

### 9.3 What the protocol does **not** authorise

This protocol authorises **no** sample draw, **no** labels, **no** scorer tuning, **no** training, **no** removals, **no** source edits and **no** Data Gate pass. Those remain gated on §9.5. In particular, **D-4's removals follow D-3's measurement and do not precede it**, and a development estimate — even one below a Data Gate limit — qualifies nothing.

### 9.4 The pins, re-verified

| pin | value | verified |
|---|---|---|
| development population | `data/v3/mixture/mixture-v3-no-trail.jsonl`, 140,545 rows | sha256 `75b5099c568313f2ceada6f79746e51840b5240d943e952c2f2ebe3c3318fc90` — **matches** the protocol's pin |
| flag file | `…/cyberguard-v4/data/<quality-flags>/flagged-rows.jsonl` | sha256 `9044dabcb625f383e6f9ba3c1166aba611c984bad0427df0a8aa33329e3eaf03` — **matches** the protocol's pin |
| qualification candidate (working) | `data/v4/corpus-v4-r3.jsonl`, 108,978 rows | sha256 `7798c4f589b855caa32dc9d6335926e856f78fe649419dd9e516b7ba1a6413ff` |
| qualification candidate (frozen) | `data/v4/corpus-final.jsonl` | **N and SHA-256 fixed at the D-7 freeze**, before the confirmation draw |

### 9.5 The execution dependencies ahead of the first draw

The confirmation draw is the next measurement, and it follows the three dependencies below. They
are named here so the sequence is visible rather than discovered:

1. **Two independently working cybersecurity-competent annotators A and B, and an adjudicator C.**
   Not available to this programme. The protocol is explicit that *"existing Codex/Claude sessions
   may independently annotate this protocol … but are not silently substituted for required
   competent human annotation."* They are **not** substituted here either. This is the same human
   dependency that blocks items **A-6** and **D-6**.
2. **The 300-row reference-control cohort** is not assembled. Without it the scorer's acceptance
   bar in §4.1 cannot be tested at all.
3. **The final candidate is not frozen.** `data/v4/corpus-final.jsonl` does not exist until D-4
   and D-5 have run and D-7 has frozen it; the confirmation draw needs its N and SHA-256.

**All three come before D-3's draw and D-7's Data Gate receipt; this protocol's approval does
not move them.**

### 9.6 The instrument that D-2 must deliver

§4 audits **the unchanged frozen regex classifier** — the detector under audit, not a third
independent reference annotator. **D-2's instrument is a different thing**: a scorer whose own
precision and recall are measured against a hand-labelled sample of **≥200 rows** spanning each
stratum, with the confusion matrix reported. **Neither instrument decides anything until its
measured precision and recall are written down**, and neither is a substitute for the adjudicated
human reference this protocol requires. Where the two disagree, the adjudicated reference stands.
