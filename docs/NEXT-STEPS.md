# NEXT-STEPS — CyberGuard VulnTriage

**Prepared** 2026-10-23 · **Status** approved direction · this document is the roadmap
**Scope of this document** inventory and roadmap only. **No new downloads were performed. No training was performed. No corpus file, adapter or model artifact was modified.**

> **STATUS — 2026-10-23, later the same day. This document is the *plan*; the *work* is tracked in
> the programme's running plan, which is the single source of truth.** Since this document was written the
> following have been **executed and measured** (all of it is read-only with respect to the v4 tree,
> and **no model artefact, adapter or corpus file was modified** — the rebuilt lineage is written
> to `cyberguard/data/v4/` under programme decision **1**):
>
> - **The corpus exclusion decision is now written and executed.** The removal set is a counted artefact
>   (`data/v4/removal-set-d5.jsonl`, 28,037 row_ids) and the rebuilt corpus carries **0 leading
>   thinking-control tokens** and **0 stock-preamble targets**, where the source had 4,891 and
>   18,074. **A finding this document did not have:** the exclusion *raised* the refusal share from
>   6.82 % to **8.52 %**, so the reweight had to be solved against the **final** denominator. The
>   refusal share is now **4.91 %** — executed under programme decision **3**
>   (`docs/REFUSAL-POLICY.md`), open to override.
> - **The product contract exists and is machine-checkable**: `docs/PRODUCT-CONTRACT.md` defines
>   **`TRIAGE-1`** (six keys, both enums, three machine-checked consistency rules), the abstain
>   path and the **refuse-and-surface** posture. The checker *parses the schema out of the
>   contract*, so the contract and the corpus cannot drift apart.
> - **The corpus carries the new families**: **352** triage-format rows (C-7), **144**
>   triage-shaped harmful requests (C-8), and the working corpus `data/v4/corpus-v4-r3.jsonl`
>   (**108,978 rows**, refusal share back on **4.9092 %**).
> - **One authoritative licence table** now exists — `docs/DATA-LEDGER.md` — and **five** sources
>   are marked **UNKNOWN** (not silently assigned): CTI-Bench MCQ, CTI-Bench RCM,
>   CyberMetric-500, **MITRE-FRR** and **HarmBench behaviours**.
> - **Four record questions are closed** in `docs/DISPOSITIONS.md`: SecQA's row count, <previous-analyst>'s
>   never-materialised directory, v1's unrecoverable mixture, and <previous-analyst>'s unavailable workbook.
>
> **Still true of this document:** the inventory (§2–§3) and the missing-data list (§4). What is
> **new** since it was written is §2.4 (i)'s resolution, §3.4's licence ground truth, and §5
> question 1's execution.

---

## 0. What this document is, and what it is bound by

The **CyberGuard VulnTriage** direction in `PRODUCT-DEFINITION.md` is approved, and the roadmap from the §7 build path is set out here, in order, with particular detail on data.

Three things it contains, in this order:

1. **§1 — The ordered next steps.** The §7 path, each step with **what it produces** and **what it unblocks**, plus the dependencies that the data work in §2 and §3 turned up.
2. **§2 — DATA FIXING.** For every existing corpus and stream: **fixable in place** or **must be rebuilt**, with the **measured defect** behind each call.
3. **§3 — DATA INVENTORY BEFORE ANY NEW COLLECTION.** Everything already on this machine, and everything the project record shows was downloaded, with name, location, size, row count, licence status, and whether it serves the VulnTriage corpus. **Only after that inventory** does §4 list what is genuinely missing.

### 0.1 The evidence rules this document obeys

- **Public third-party benchmarks only** count as evaluation evidence. The programme's own instruments are diagnostic and decide nothing.
- **Reproduce before claiming.** Every figure below was recomputed from files on disk for this document; the reproducible scripts and their output are listed in the **Appendix**. Figures carried over from `EVALUATION.md` are cited to their section.
- **VERIFIED / UNVERIFIED / UNKNOWN** are used as three different words. Where a licence is not on disk it is marked **UNKNOWN**, not assumed.
- **A missing measurement is never a pass.** The <previous-analyst> directory is empty and is recorded as empty.
- **Decision namespaces.** Every decision id names the file it lives in, so a citation is never a bare id. `docs/SPEC-V2.md` carries its own decision table; the plan-sequence defect ids (`REV-D<n>`) and the failure rows (`FR-D<n>`) are not decisions and are never cited as ones; `CG-…` and `FC-…` are failure-corpus and format-compliance identifiers. The sweep that enforces the rule is `eval-2026-10-23/e6_namespace_sweep.py` — **zero unqualified citations across 78 files**.
- **Standing rules apply.** Nothing here chooses a model, dataset, mixture, metric, bar, sample size, parser, decode budget, batch size, threshold or label on its own authority. Where a choice is needed, it is written as a **decision to be recorded**, with the options laid out.

### 0.2 Authority in force for this phase

| authority | what it authorises | used here? |
|---|---|---|
| **the benchmark-run authorisation** | running existing artifacts against public benchmarks already on disk | yes — the CTI sweep for the older arms |
| **the release of the benchmark-run authorisation** | the run authorisation released, 2026-10-10 | yes |
| **the corpus exclusion decision** | Primus and the merged reasoning corpus stay excluded | yes — §2, step 6b |
| **the existing-decoder decision** | existing decoders and parsers only | yes — no decode-budget change happens without a recorded decision |
| **the evaluation programme's standing terms** | evaluation of existing artifacts is permitted; training is not | yes — this document plans, and schedules no training |

`python3 tools/astra_gate.py D9 -- run-public-benchmark` → **AUTHORISED**.

---

## 1. The ordered next steps

### 1.1 The path

Each row names the artefact it produces and the work it unblocks. "Authority" is what has to be true before the step can start — not what it produces.

| # | step | **produces** | **unblocks** | authority needed | where it stands on 2026-10-23 |
|---:|---|---|---|---|---|
| **0** | **Freeze the data record** — re-issue the v2 mixture ledger against `FACTS.json`, record the licence receipts in one table, write the row-level provenance map (already built) into the corpus directory | a single authoritative `docs/DATA-LEDGER.md` **+ `data/v3/provenance-map.jsonl`** *(both to be written)* | step 6, step 7, and any future rebuild template | **none** — operator-side, no GPU, no network | **new in this document.** Two defects found (§2.4); next is the ledger re-issue — a few hours |
| **1** | **Finish the running public re-measurement** — FRR for all six arms, the HarmBench re-judgement, the 610-item knowledge sweep for the older arms, and the CTI free-form sweep for v1 / v2 arm A / v2 arm B | the release table | step 2's bars; every "good enough" judgement | the benchmark-run authorisation (released) | **MEASURED in full** — the CTI sweep finished on both GPUs (v1 and v2 arm A on GPU1, v2 arm B on GPU0), all three arms are merged into `results-merged-2026-10-23.json` (24 comparison rows), §5.3 is regenerated from the merged artefact, and the release table is regenerated from `release-candidates.json` |
| **2** | **Fix the bar sheet (§5 of `PRODUCT-DEFINITION.md`) and sign it** | a signed bar sheet: B1–B8 with their baselines | every public claim, including the VulnTriage headline | **a recorded decision** | next: sign the bar sheet once the 4 questions from the measurements (Q11–Q14) are answered |
| **3** | **Write the product contract** — user, job, operational meaning of "defensive", what the model must refuse, **and the triage output schema** (CWE, CVSS vector, severity, priority, rationale, abstain) | `docs/PRODUCT-CONTRACT.md` *(to be written)* | step 2's refusal bar; step 8b's output contract; the schema every dataset in §7 must target | a recorded decision | next: write the contract |
| **4** | **Commission the blinded human adjudication** — 750 FRR responses per model, 2 human assessors + adjudicator | a human-semantic judgment per response | B3's semantic meaning; the "was a refusal warranted?" half of CG-09 | **humans** | next: the human panel adjudicates — inputs are ready for all six arms, and this step is not a mechanical one |
| **5** | **Build the refusal-integrity check** — CG-09's prevention check: sampled refusals audited for post-refusal leakage | `eval-2026-10-23/refusal-integrity-audit.json` refreshed on the frozen surface | B3b | it can be built mechanically; **a human must sign it off** | next: re-run against the released surface — the tool exists |
| **6** | **Qualify the corpus** — approve the P2 calibration protocol, execute the held removal sets, freeze the corpus, issue the Data Gate | a frozen, qualified corpus + Data Gate | any future training | operator-side; the protocol is a **DRAFT** and must be approved first | next: approve the protocol, then execute the removal sets, freeze the corpus and issue the Data Gate |
| **6b** | **Execute the corpus exclusion, already decided** — drop Primus and the merged reasoning corpus (**28,037 rows, 19.95 % of the v3 mixture, 20.69 % of the v4 working corpus**) and add a stock-preamble gate (leading token = 0, preamble-opening targets = 0) | a written removal set, executed, with the resulting corpus hashed | step 7 | **nothing outstanding — this is the one removal with no missing authority** | **next: write the removal set, then execute it — the resulting corpus is hashed** |
| **7** | **Rebuild the vuln-analysis corpus from public structured sources** (NVD + MITRE CWE + CVSS), licence-clean, qualifying it from scratch rather than repairing the contaminated streams | the VulnTriage corpus | the retrain | data collection + the step-6 calibration gate | **§2 and §3 below are this step's specification** |
| **8** | **Add the missing instruments** — CTI-VSP and CTI-ATE to the harness | two public instruments, parsers, scorers | B2 (the CVSS-prediction bar) | a download; no gate issue (public benchmarks) | **next: download both, then write the parser and the scorer** |
| **8b** | **Ship an output contract and measure it** — a constrained last-line instruction and/or a parse-and-retry wrapper, evaluated on the frozen surface | `docs/OUTPUT-CONTRACT.md` *(to be written)* + a measured delta on the frozen surface | B1, B5, and the product's headline claim | **no training, no new data** — a serving-template change and a measurement | **next: write the shipped contract** — the measurement already exists (`output-contract-recovery-ceiling*.json`) |
| **9** | **THE TRAINING STEP — after 3–8b** | a trained adapter | the release | **a recorded decision**; the benchmark run's freeze state; a written hypothesis | **next: on a recorded decision and a written hypothesis** |
| **10** | **Package** — merge → quantise → GGUF → `generation_config.json` → model card → hash freeze | the release artefact | steps 11+ | the trained artefact | **starts after step 9** |
| **11** | **Publish the stack** in the §6.3 order | the public evidence stack | — | steps 1–10 | **follows the steps above** |

### 1.2 What changed in the ordering because of the data work

**Step 0 is new and it is first.** It was not in `PRODUCT-DEFINITION.md` §7 because the data record looked settled. It is not: `docs/MIXTURE-V2.md` — the ledger that calls itself the "frozen v2 mixture ledger" — **does not satisfy its own definition of done**, and it is the template any rebuild would naturally copy. §2.4 gives the numbers. This is days of operator work that has to happen before step 6, because the corpus gate in step 6 is written against a ledger that currently mis-states the composition of the artefact it governs.

**Step 6b and step 7 are now in tension, and the tension is sharp for VulnTriage specifically.** `PRODUCT-DEFINITION.md` §8 question 8 raised this for the general case: excluding the `merged` stream removes the CVE/CWE reasoning that CTI-RCM depends on. The data inventory sharpens it into a specific, decidable fact:

> **The corpus's *only* CVE→CWE supervision is the Primus stream — the 4,891 rows the exclusion removes — and the stream it also excludes (`merged`) is not CVE→CWE at all; its schema is `cwe_id`/`cwe_name`/`affected_line`/`partial_code`, i.e. code→CWE.**
>
> So for the VulnTriage direction specifically, executing step 6b removes **100 % of the CVE→CWE task from the training corpus** and leaves the code→CWE reasoning. Executing step 6b *without* step 7 leaves the corpus with **no CVE→CWE supervision at all**.

This is not an argument against the exclusion — it is correct and remains the one removal with no outstanding authority. It is an argument for **ordering**: 6b and 7 are the same project, and 7 is where the CVE→CWE supervision comes back, clean.

**Step 3 gains a schema.** The product contract must specify the triage output schema before step 7 collects anything, because step 7's collection spec, step 6's calibration gate and step 8b's output contract are three views of the same contract. A corpus collected against an unnamed schema cannot be qualified against one.

### 1.3 The steps that come later, and why

- **Step 9 (training)** — the two headline bars are missed for corpus-side reasons, and the measurements say a corpus-side and serving-side fix may clear them without a retrain. GPU time before steps 2–8b would go on re-measuring a known defect.
- **Step 8's CTI-VSP** — it is the only bar (B2) that measures the CVSS-prediction claim the product is named for, and it is not on disk. But adopting it means choosing a parser and scorer that do not exist in this project. That is a separate decision, and it is taken **together with** step 3's schema rather than ahead of it.
- **Anything that treats the `merged` stream's removal as a loss of CVE/CWE competence.** It is code→CWE. The competence CTI-RCM measures is *reasoning about a CVE description to a CWE*, and that competence lives in Primus's prompts and in the 268 clean trails in `data/v3/trails-30/` (§2.3).

---

## 2. DATA FIXING — in place, or rebuild

### 2.1 The rule applied

For each stream, one of four calls, made on a measured defect:

| call | meaning |
|---|---|
| **FIXABLE IN PLACE** | the defect is confined to a removable subset, or to a field-level edit; the rest of the stream is sound and its licence is compatible with redistribution in the release stack |
| **MUST BE REBUILT** | the defect is in the stream's *targets* at a rate that makes the stream unusable as supervision, or the stream lacks the field the product needs |
| **NOT APPLICABLE** | the stream is sound but does not serve the VulnTriage corpus; it is kept, and it is not repaired |
| **ABSENT** | the record says it exists; it does not exist on disk. Nothing to fix, nothing to use |

**"Fixable in place" is a claim about cost, not about virtue.** A stream that is fixable in place is still worth checking against the licence column in §3.

### 2.2 The table

| stream | rows | call | the measured defect behind the call |
|---|---:|---|---|
| **Fenrir v2.1** (CyberSec-Dataset-Fenrir-v2.1) | 99,730 admitted | **NOT APPLICABLE** | No defect found; the redaction pass changed 6 rows (`data/v3/REDACTION-RECEIPT.json`). But its schema is system/user/assistant cyber Q&A — **no CVE id, no CWE, no CVSS**. It teaches security reasoning and general helpfulness; it cannot teach triage. **Kept, not repaired.** |
| **Primus** (trendmicro-ailab/Primus-Reasoning, CTI-Bench subset) | 4,891 | **MUST BE REBUILT (targets) — prompts reusable** | The **only** CVE→CWE supervision in the entire corpus, and the single most defective stream. The thinking-control token appears in **100 %** of its rows; v3 emits `<\|reserved_special_token_0\|>` at the start of **100 %** of its CTI-MCQ responses (2,500/2,500) and **100 %** of its CTI-RCM responses (1,000/1,000), against base and comparator **0 %**; the population-level decode-cap truncation rate is **UNMEASURED** (the stored field is the batch maximum and the frozen runner records it as INVALID for interpretation; the label supports only the bound **v3/CTI-MCQ ∈ [12.12 %, 96.80 %]**), and **every one** of its 1,022 parse failures sits in a batch that contained a cap hit. The project's own preamble detector finds **0 %** in Primus — the stock-preamble defect belongs entirely to `merged` — so Primus carries exactly **one** contamination class, and it is the severe one. **The defect is in the targets, not the prompts** — and §2.3 shows a clean replacement for 268 of them is already on disk. |
| **merged** (Mohannadcse/cybersec-reasoning-merged) | 23,146 | **MUST BE REBUILT** | **78.087 %** of its targets (18,074 rows = **12.86 %** of the whole corpus) open by narrating the request instead of answering it. The release contract requires *"Zero stock preambles or thinking-control tokens across the release battery"* and the pilot spec gates them at ≤ 1 % of knowledge responses — **a model trained on 12.86 % preamble-opening targets is trained into a gate it will be measured against**. The corpus exclusion already removes it. **Its task is code→CWE, not CVE→CWE**, so its loss does not cost the triage axis. |
| **NVD candidate sample** (`nvd-sample.jsonl`) | 16,000 | **MUST BE REBUILT** | Recomputed for this document: **0 of 16,000 rows carry a CWE id and 0 carry a CVSS**. Its schema is `text`/`cve_id`/`source` — it teaches only *"what does CVE-X describe"*. And every CVE is from **1999–2006**: 1999:1,572 · 2000:1,233 · 2001:1,536 · 2002:2,357 · 2003:1,484 · 2004:2,658 · 2005:4,672 · 2006:488. A triage corpus built on this teaches a 1999–2006 vulnerability landscape and no labels at all. |
| **NVD raw page** (`nvd-raw.json`) | 2,000 (of **398,563** in the feed) | **MUST BE REBUILT** (as part of the modern fetch) | The one place on disk where the triage fields exist, and it shows why the slice is unusable: **1,865 of 2,000** weaknesses are `NVD-CWE-Other`, and the metric coverage is `cvssMetricV2` **1,966**, `cvssMetricV31` **36**, `cvssMetricV30` **1**, `ssvcV203` **26** — i.e. the legacy v2 vector, not the v3.1 vector that CTI-VSP-style prediction needs. It proves the fetch pipeline works; the data itself is 1999–2006 and mostly unlabelled. |
| **format-compliance** (authored) | 1,300 (×2 = 2,600 presentations) | **FIXABLE IN PLACE** | Sound and licensed (ours; SigmaHQ schema verified at U1). **This is the output-contract supervision** and the nearest thing on disk to the triage schema: *"Return JSON with exactly the keys…"*. It must be **extended**, not repaired — the triage schema (CWE, CVSS vector, severity, priority, rationale, abstain) is a superset. **This is the single highest-value in-place fix available.** |
| **refusal-retention** (authored) | 1,200 (×8 = 9,584) | **FIXABLE IN PLACE — but the target weight is a recorded decision** | Sound. The lever is proven: arm A (full stream) refuses **35.33 %** against arm B's **17.47 %** on the same prompts, exact McNemar **p = 5.1 × 10⁻²²**; the dose-response is monotonic (**4.91 % → 17.47 %**, **6.82 % → 29.07 %**, **11.82 % → 35.33 %**). **But it is a two-sided dial**: across the four trained arms Pearson(FRR, HarmBench) = **−0.87**, so turning it down turns up harmful compliance. **v1 buys the family's best FRR (10.93 %) at 12/159 harmful compliance — worse than the untrained base's 1/159.** The weight must be chosen against both instruments at once. Its prompts are also **not triage-specific**: nothing in the set is a "just give me the exploit for CVE-X" request, which is the refusal triage must actually make. |
| **ATT&CK STIX** (mitre-attack/attack-stix-data) | 2,198 sampled (2,144 / 2,136 admitted — §2.4 (i)) | **FIXABLE IN PLACE — but the CVE mapping is NOT in the source either** | The stream keeps `stix_id` and `type` but **drops `external_references`**, and the item assumed the dropped field was where ATT&CK's CVE↔technique mapping lives. **F-4 measured that it is not** (`eval-2026-10-23/f4-attack-cve-map.json`). The raw `enterprise-attack.json` master **is now on disk** — `data/vuln/attack/enterprise-attack.json`, 55,271,014 B, **byte-identical to upstream** — and it carries **0** structured technique↔CVE pairs across **3,498** `external_references`; the **v11.0 control** (2021) also carries **0**, so the mapping was never in the STIX. A **head-to-head test over all 2,198 rows** shows the flattened sample dropped **no** CVE the raw object carries: **0** rows' text CVEs differ from the raw object's `name`+`description`, **0** rows carry a CVE the raw object lacks. What exists in either is prose — **9** pairs over **7** distinct CVE ids, of which **8** sit in a technique's own text and **1** is citation-only. The master is therefore on disk and still not a mapping: MITRE publishes the usable signal **only on the website** (the **T1190** page names **63** CVE ids; the STIX object for the same technique carries **0**). **The technique axis needs a decision of its own** — see F-4. |
| **NIST CSRC** | 1,000 sampled (835/718 admitted) | **NOT APPLICABLE** | CC0-1.0, sound, administrative guidance. No CVE/CWE/CVSS fields. Kept; contributes general-defensive text. |
| **Trendyol** | 53,201 raw (50,672/50,606 admitted) | **NOT APPLICABLE** | Apache-2.0, sound, general cyber instruction tuning. The v1 core and the source of the 500-row holdout. No triage fields. Kept; not repaired. |
| **UltraChat** | 400 sampled / 600 pairs admitted | **NOT APPLICABLE** | MIT, sound, and deliberately near-zero weight (the replay slot carries real assistant turns). Not triage. |
| **arcspan-cyber-ner** | 500 sampled | **REJECTED at the v2 gate (0 admitted)** | Extraction supervision absent — arcspan's labels are not retrievable through the viewer API. Retained as the **G-D evaluation corpus** (making G-D zero-shot). Call: **NOT APPLICABLE** to training; the admission was correct and stands. |
| **v3 mixture** (`mixture-v3-no-trail.jsonl`) | 140,545 | **MUST BE REBUILT for VulnTriage** | Composition measured: fenrir 99,730 · merged 23,146 · primus 4,891 · refusal 9,584 · format 2,600 · replay 594. It **carries both contaminations at full strength** (the 4,891 thinking-token rows and the 18,074 preamble-opening rows). More importantly for VulnTriage: it contains **no CVSS supervision, no CVE-anchored impact supervision, and no prioritisation supervision of any kind**, because no such data exists on this machine. The corpus exclusion makes it clean; it does not make it a triage corpus. |
| **v4 working corpus** (`corpus-r2.jsonl`) | 135,503 | **SUPERSEDED — do not repair, do not train on** | sha256 `c29907c1…f228`, derived from the v3 mixture (source sha `75b5099c…fc90`, read-only). Its **only** removal pass was **5,042 exact-duplicate rows**; it still carries all 4,891 thinking-control-token rows and all 23,146 `merged` rows byte-for-byte. Its own receipt says *"This working copy is not a training set."* The dedup work, the leakage report and the row-level metadata tagging are all **reusable inputs to step 7** — the corpus file itself is not. |
| **`trails-30`** | 7,000 traces (1,976 combined; 855 muse) | **FIXABLE IN PLACE — and it is the most useful thing on disk** | Never trained on: the v3 build is `mixture-v3-**no-trail**` and its receipt records *"no trail stream in the no-trail build"*. Measured for this document: **0 thinking-control tokens** and **0 stock preambles** in the 268 Primus-sourced targets, **0** and **7/1,268** in the merged-sourced targets, **0** and **87/5,464** in the Fenrir-sourced targets. These are teacher-generated reasoning traces over the same CVE→CWE prompts. **See §2.3.** |
| **v1 mixture** | — | **ABSENT — unrecoverable** | `research-tmp/harvest-v1/` contains **only the adapter** (263 MB). v1's training composition is not on this machine and cannot be derived. Recorded as unrecoverable, **not** as data to collect. |
| **<previous-analyst> datasets** | — | **ABSENT — empty directory** | `~/<other-workspace>/cyberguard-v4/data/<previous-analyst>-datasets/` exists and contains **0 files, 0 bytes**. The stream-4 log claims *"Loaded 140545 rows across 6 strata"* and the dispatch specifies five planned outputs (`offensive-1200`, `offtopic-1200`, `shallow-1200`, `heldout-1000`, `dataset-card`) — **none were materialised**. Nothing to fix, nothing to use. |
| **supplemental pairs** | 55 + 53 rows + rubrics | **NOT APPLICABLE** (reusable as a small rationale set) | Attack→defense defence-writing pairs with rubrics. No CVE/CWE/CVSS fields. |
| **row metadata tagging** | 140,545 rows × 2 copies (675.54 MB each) | **FIXABLE IN PLACE — reuse as-is** | The row-level provenance map for the v3 mixture. **This is the highest-value reusable artefact in the inventory**: it is the row_id → source map a rebuild needs so that a source can be re-weighted or a stream surgically removed without re-deriving provenance. |
| **dedup / leakage census** | reports + certified census | **FIXABLE IN PLACE — reuse as-is** | M0-2 certified census: 140,545 lines, 130,859 unique hashes, 2,498 duplicate groups, 9,686 extra rows, reproduced. Cross-verified under both SHA-1 and SHA-256. **Reusable verbatim as step 7's decontamination baseline.** |

### 2.3 The three calls that carry the product

#### (a) Primus — rebuild the targets, keep the prompts, and 268 replacement targets already exist

The measured defect is in Primus's **targets**, and the evidence for that is unusually direct: the stream's **prompts** are a clean specification of the CVE→CWE task —

> *"Analyze the following CVE description and map it to the appropriate CWE. Provide a short justification for your choice. **Ensure the last line of your response contains only the CWE ID.**"*

— and that last-line instruction **is the CTI-RCM output contract**. So the task definition is right, and it is exactly VulnTriage's task.

What is wrong is the target: the thinking-control token in **100 %** of rows, and nothing else — the project's own preamble detector finds **0 %** in Primus.

**The replacement template is already on disk.** `data/v3/trails-30/` contains 7,000 teacher-generated reasoning traces over the same prompts, and they were never trained on. Measured for this document on the 268 Primus-sourced trails:

| metric | value |
|---|---|
| thinking-control token in the target | **0 / 268 (0.00 %)** |
| stock-preamble-opening target | **0 / 268 (0.00 %)** |
| contains a CWE id | 158 / 268 (58.96 %) |
| **ends with a CWE id** (the CTI-RCM contract) | **133 / 268 (49.63 %)** |

A sample target, verbatim:

> `Step 1: Parse the key facts. The vulnerability root cause is stated as "a tapjacking/overlay attack" in KeyChainActivity.onCreate…`  →  `…which is precisely CWE-1021 (Improper Restriction of Rendered UI Layers or Frames). The privilege escalation is the impact rather than the underlying weakness…`  →  **`CWE-1021`**

**What this means in practice:** 268 replacement targets for CVE→CWE reasoning exist today, produced by a generator that has already run, and they were never trained on. That is 5.5 % of Primus's size — **not enough to train on**, but it is enough to (i) prove the repair template works before any collection spend, (ii) give step 7 a format reference, and (iii) supply the exact output-contract examples the step-8b wrapper needs. The remaining **4,623** Primus rows need targets that do not exist on this machine — and because only **133** of the 268 present ones satisfy the last-line contract, **4,758 rows in total need a contract-conformant target written**.

#### (b) `merged` — the removal is correct, and it costs the triage axis nothing

The exclusion of `merged` is correct and stands. The cost the record worries about — *"a corpus without `merged` may lose the CTI-RCM gain that §5.3.7 shows is real"* — needs one correction: `merged`'s schema is **`cwe_id:CWE-798 / cwe_name:… / affected_line:… / partial_code:…`**, which is **code→CWE**. It is not CVE→CWE supervision. Its removal therefore does not remove the CVE→CWE task; it removes a *different* weakness-reasoning style that is 78 % contaminated.

The measured cost of removing `merged` is narrower than the record states: it removes the code-level weakness-localisation habit, and it removes 12.86 % of the corpus's stock-preamble teaching. Both are things step 6b wants gone.

#### (c) NVD — this is the gap, and it is the whole gap

Recomputed for this document, the NVD material on disk is:

| artefact | rows | CWE label | CVSS | usable for triage? |
|---|---:|---|---|---|
| `v2/candidates/nvd-sample.jsonl` | 16,000 | **0 rows** | **0 rows** | no — it is CVE *description* text with no label and no score |
| `v2/candidates/nvd-raw.json` | 2,000 (of 398,563) | 1,865/2,000 = `NVD-CWE-Other` | cvssMetricV2 1,966 / v31 36 / v30 1 | no — wrong era, wrong vector version, unlabelled weaknesses |
| `v2/candidates/nvd-authority-gC.json` | 288 CVEs | — | — | no — an authority-cross-check artefact, not supervision |

**So the machine has 16,000 CVE descriptions with no labels and no scores, plus a 2,000-row slice that is 1999–2006 and mostly `NVD-CWE-Other`.** The VulnTriage corpus needs a modern, labelled fetch. §4 specifies it.

### 2.4 Two defects in the record itself, found while fixing

**(i) `docs/MIXTURE-V2.md` does not satisfy its own definition of done.** The mixture record calls itself *"the frozen v2 mixture ledger"* and its definition-of-done item 4 requires that *"every number in this ledger equals the corresponding value in `v2/data/mixture/FACTS.json`"*. Recomputed:

| source | `MIXTURE-V2.md` | `FACTS.json` | delta |
|---|---:|---:|---:|
| trendyol | 50,672 | 50,606 | −66 |
| nvd | 14,847 | 14,836 | −11 |
| attack | 2,144 | 2,136 | −8 |
| nist | 835 | 718 | −117 |
| replay | 600 | 594 | −6 |
| refusal | 9,584 | 9,584 | **0 ✓** |
| format | 2,600 | 2,600 | **0 ✓** |
| **epoch total** | **81,282** (and the record's header says 81,282) | **81,074** | **−208** |

`armA.jsonl` and `armB.jsonl` **on disk both contain 81,074 rows**, and `FACTS.json`'s `source_breakdown` sums to exactly 81,074. So `FACTS.json` matches the artefact and **`MIXTURE-V2.md` describes a build that does not exist**.

**Impact on published figures: none.** The two streams that disagree about everything else — `refusal` (9,584) and `format` (2,600) — agree exactly, so the FRR dose-response's refusal share of **11.821 %** stands against the on-disk 81,074-row epoch. The five mismatching sources are the non-refusal bulk.

**Why it matters anyway:** `MIXTURE-V2.md` is the natural template for a rebuild record, and it is the document a careful reader would trust. **Step 0 re-issues it.** The correction is arithmetic, not judgement — and it is the kind of discrepancy that is much cheaper to fix now than to discover in a release.

**RESOLVED 2026-10-23 (programme item B-1).** `docs/MIXTURE-V2.md` has been re-issued: every number in it now equals `FACTS.json` (**7 of 7**), the header epoch reads **81,074**, and the ledger's own definition-of-done items 2 and 3 were re-run and pass (`gate_v2.py --check` → exit 0, `GATE-REPORT-OK: 9 candidates, admitted=8 rejected=1 unmeasured=0`; `audit_mixture.py --verify-receipt` → exit 0, `RECEIPT-BOUND`). The check is re-runnable: `eval-2026-10-23/b1_mixture_v2_check.py` → **16/16 PASS**.

**The re-issue caught a second and larger defect in the same file, which the FACTS reconciliation exposed.** The ledger asserted a *matched* control arm — *"(1,198 distinct prompts, 1,021 distinct answers, 3.9 % length gap)"* — a pool-level figure from the 2026-09-28 checkpoint that the arms do not realise. Measured from the arms, the 5,600 substituted rows carry **228 distinct prompts / 72 distinct answers** against the treatment side's **700 / 397**, with a **15.5 % length gap** (59.63 against 70.54 mean answer words); the programme's own `v2/data/mixture/d2-diversity.receipt.json` records that comparison as **NOT MET** on both of its gates (≥1,000 distinct control prompts; ≤10 % length gap) and carries the consequence in its own words: *"any claim of a MATCHED control must state this asymmetry"*. The superseded figure is now retained inside an explicit supersession note and never as a live claim, and the confound it implies is carried into `EVALUATION.md` §5.3.6/§5.3.9, `PRODUCT-DEFINITION.md` §5 and `PRODUCT-RESEARCH.md` (programme item **A-13**).

**(ii) SecQA's local row count disagrees with its own manifest.** `v2/candidates.json` records `zefang-liu/secqa` at *"CC BY-NC-SA 4.0, ~242 rows"*, and the record's second table repeats it. The local file `pubbench/secqa_test.csv` has **110 data rows** — the B7 benchmark's n. `pubbench/secqa.json` is a **15-byte `Entry not found` stub** from a failed download and resolves nothing. Every SecQA number in `EVALUATION.md` is correctly computed over the 110 rows actually on disk, so **no published figure changes**; but the licence-and-count column in §3 of this document carries 110 (local, measured), and the discrepancy is recorded rather than silently harmonised.

---

## 3. DATA INVENTORY BEFORE ANY NEW COLLECTION

### 3.1 Method and roots

Mechanical enumeration, extension-filtered, over five roots: `~/cyberguard`, `~/cyberguard-program`, `~/<other-workspace>`, `~/failure-corpus`, `~/tokenomics-bench`. Excluded from the count: `.git`, `.codex` (plugin/skill assets), `SESSION-ARCHIVE` (session transcripts), `node_modules`, `site-packages`, virtualenvs. `~/.cache/huggingface` → `/data/huggingface` and `<model-cache>` are inventoried separately in §3.7.

**7,146 data-extension files, 8,266,778,544 B = 8.27 GB.** `.json` 6,375 · `.txt` 442 · `.jsonl` 192 · `.tar` 117 · `.csv` 11 · `.parquet` 6 · `.tsv` 3.

**Filtering note, stated so the totals are not misread:** **6,360 of those files** live under `cyberguard-program/tools/evidence/p1/` and are **test-harness control fixtures** — that subtree holds 29,306 files in total, 83.6 MB, of which **297** are `.tar`/`.tar.gz` **fixture git repos, not datasets**. Removing them leaves **786 files, 8.21 GB** of real payload. The rest of the 8.27 GB is the corpus inventory in §3.3–§3.6, plus model-adapter weights and evaluation results, which are listed but not counted as corpus.

**Sizes are exact bytes.** Row counts are full parses, not `wc -l` guesses — and this matters in **three** places, not two: `fenrir-v2.1/220426-…_escaped.jsonl` (99,870, not 99,869), `v2/data/corpus/trendyol-escaped.jsonl` (53,201, not 53,200) and **both CTI-Bench TSVs** (`cti-mcq.tsv` **2,500**, `cti-rcm.tsv` **1,000**, not 2,499 and 999) have **no trailing newline**, so `wc -l` under-reports each by exactly 1. The CTI counts here are taken from the **frozen runner's own `csv.DictReader`**, which is the population every published CTI number uses.

### 3.2 The VulnTriage fit test

The product is a **vulnerability triage scorer**: given a vulnerability, produce the CWE, the CVSS vector and severity, the impact, and a prioritisation, in a schema the caller can rely on. The inventory therefore scores every source against **four axes**:

| axis | what it must supply |
|---|---|
| **A — CVE→CWE** | a CVE identifier or description paired with a weakness id, as supervision |
| **B — CVSS** | a base score and a vector, in the **v3.1** form, paired with the CVE |
| **C — impact** | the consequence of the weakness, stated in terms the triage output uses |
| **D — prioritisation** | a severity ranking that goes beyond the raw score (exploitability, exposure, asset context) |

**Fit codes used in the tables:** **✓** serves the axis · **~** partial or adjacent · **✗** does not serve it · **—** not applicable.

### 3.3 Table A — training and supervision streams

| name | location | size | rows | licence | A | B | C | D | VulnTriage |
|---|---|---|---:|---|:-:|:-:|:-:|:-:|---|
| **Fenrir v2.1** (raw) | `cyberguard/data/v3/fenrir-v2.1/220426-CyberSec-Dataset_escaped.jsonl` | 431,213,578 B | 99,870 | Apache-2.0 (`LICENSE_RECEIPT.md`) | ✗ | ✗ | ~ | ✗ | general cyber reasoning; no triage fields; **bundles a copy of the Trendyol corpus, and 605 of its rows carry a held-out-500 identity (F-8)** |
| **Fenrir v2.1** (clean) | `cyberguard/data/v3/fenrir-v2.1/clean/fenrir-v2.1.clean.jsonl` | 431,175,244 B | 99,852 | Apache-2.0 | ✗ | ✗ | ~ | ✗ | as above |
| **Fenrir** (SFT split) | `cyberguard/data/v3/sft/fenrir.jsonl` | 435,924,422 B | 99,730 | Apache-2.0 | ✗ | ✗ | ~ | ✗ | the stream as trained; **604 rows carry a held-out-500 identity — 499 of the 500 (F-8)** |
| **Primus** (raw, r1) | `cyberguard/data/v3/primus-reasoning/data/ctibench_deepseek-r1.parquet` | 3,824,196 B | 2,489 | **ODC-By — attribution required; gated repo, access approved 2026-09-29** | **✓** | ✗ | ~ | ✗ | **the only CVE→CWE supervision on this machine** |
| **Primus** (raw, o1) | `cyberguard/data/v3/primus-reasoning/data/ctibench_o1.parquet` | 5,236,710 B | 2,402 | ODC-By | **✓** | ✗ | ~ | ✗ | as above |
| **Primus** (clean, r1) | `cyberguard/data/v3/primus-reasoning/clean/ctibench_deepseek-r1.clean.parquet` | 3,790,919 B | 2,489 | ODC-By | **✓** | ✗ | ~ | ✗ | clean copy |
| **Primus** (clean, o1) | `cyberguard/data/v3/primus-reasoning/clean/ctibench_o1.clean.parquet` | 5,187,544 B | 2,402 | ODC-By | **✓** | ✗ | ~ | ✗ | clean copy |
| **Primus** (SFT split) | `cyberguard/data/v3/sft/primus.jsonl` | 20,626,170 B | 4,891 | ODC-By | **✓** | ✗ | ~ | ✗ | **the contaminated stream as trained** |
| **merged** (raw) | `cyberguard/data/v3/cybersec-reasoning-merged/data/train-00000-of-00001.parquet` | 27,086,716 B | 23,146 | Apache-2.0 | ~ (code→CWE) | ✗ | ~ | ✗ | weakness reasoning; **not** CVE→CWE |
| **merged** (clean) | `cyberguard/data/v3/cybersec-reasoning-merged/clean/train-00000-of-00001.clean.parquet` | 27,050,118 B | 23,146 | Apache-2.0 | ~ | ✗ | ~ | ✗ | clean copy |
| **merged** (SFT split) | `cyberguard/data/v3/sft/merged.jsonl` | 93,666,093 B | 23,146 | Apache-2.0 | ~ | ✗ | ~ | ✗ | **78.087 % preamble-opening** |
| **v3 SFT split (all three)** | `cyberguard/data/v3/sft/{fenrir,merged,primus}.jsonl` | 550,216,685 B | 127,767 | as above | ✓ | ✗ | ~ | ✗ | what v3 trained on, pre-mixture |
| **trails-30** (deepseek 7k) | `cyberguard/data/v3/trails-30/trails_deepseek_7k.jsonl` | 31,357,268 B | 7,000 | derived from the above (ODC-By + Apache-2.0) | **✓ (268 rows)** | ✗ | ~ | ✗ | **clean CVE→CWE reasoning targets — never trained on** |
| **trails-30** (combined) | `cyberguard/data/v3/trails-30/trails_combined.jsonl` | 9,198,503 B | 1,976 | as above | ✓ | ✗ | ~ | ✗ | as above |
| **trails-30** (muse 7k) | `cyberguard/data/v3/trails-30/trails_muse_7k.jsonl` | 2,535,958 B | 855 (+79 errors logged) | as above | ✓ | ✗ | ~ | ✗ | **generation incomplete — 855 of a planned 7,000** |
| **trails-30** (prompts) | `cyberguard/data/v3/trails-30/prompts-7k.jsonl` | 2,463,680 B | 7,000 | as above | ✓ | ✗ | ✗ | ✗ | **the prompt half of the repair template**; src = merged 1,268 / fenrir 5,464 / primus 268 |
| **trails-30** (prompts, small) | `cyberguard/data/v3/trails-30/prompts.jsonl` | 18,587 B | 30 | ours | ✓ | ✗ | ~ | ✗ | trial prompts |
| **trail-generation audit sample** | `cyberguard/data/v3/trails-30/supervisor/audit-sample.jsonl` | 435,851 B | 200 | ours | ✗ | ✗ | ✗ | ✗ | offensive-prompt audit sample |
| **a7 calibration** | `cyberguard/data/v3/trails-30/supervisor/a7-calibration-{labels,scorer}.jsonl` | 8,228 B | 48 + 48 | ours | ✗ | ✗ | ✗ | ✗ | **the draft calibration protocol's evidence; labels file is all-null** |
| **refusal-retention** | `cyberguard/v2/data/refusal-retention.jsonl` | 939,612 B | 1,200 (1,198 unique → 9,584) | ours + curated public (per-source gate) | ✗ | ✗ | ✗ | ✗ | the FRR dial; **two-sided** |
| **format-compliance** | `cyberguard/v2/data/format-compliance.jsonl` | 757,287 B | 1,300 (×2 = 2,600) | ours, from public rule schemas; SigmaHQ verified | ✗ | ✗ | ✗ | ✗ | **the output-contract supervision — the triage schema's ancestor** |
| **replay (ultrachat pairs)** | `cyberguard/v2/candidates/ultrachat-pairs.jsonl` | 922,698 B | 600 | MIT | ✗ | ✗ | ✗ | ✗ | real assistant turns |
| **Trendyol corpus** | `cyberguard/v2/data/corpus/trendyol-escaped.jsonl` | 195,018,595 B | 53,201 (50,672 admitted) | Apache-2.0 | ✗ | ✗ | ~ | ✗ | general cyber instruction data |
| **holdout-500** | `cyberguard/v2/holdout500.jsonl` | 1,853,103 B | 500 | from Trendyol | ✗ | ✗ | ✗ | ✗ | **held out from the Trendyol train split by construction — but NOT from the fenrir stream: 499 of these 500 questions are inside the training corpus as 604 rows (F-8; `docs/ESCALATION-F8-HELDOUT-CONTAMINATION.md`)** |

### 3.4 Table B — candidate sources and the licence ledger

The licence ground truth is now **`docs/DATA-LEDGER.md`** (programme item B-2) — one authoritative table covering every source in the corpus, candidate and evaluation trees, with each licence's provenance, its notice obligation and whether it may ship. It is built from `v2/candidates.json` (9 sources, each with id / revision / license / role / rows), `v2/candidates/SAMPLES.json` (2 sources), `docs/MIXTURE-V2.md` (the frozen v2 mixture record — see §2.4 (i)) and the three `data/v3/*/LICENSE_RECEIPT.md` files, and it is checked by `eval-2026-10-23/b2_data_ledger_check.py` (**9 of 9 PASS**). The per-source licence column below is a convenience restatement; **where it and the DATA-LEDGER differ, the DATA-LEDGER is the source of truth.**

| name | location | size | rows | licence | A | B | C | D | VulnTriage |
|---|---|---|---:|---|:-:|:-:|:-:|:-:|---|
| **NVD sample** | `cyberguard/v2/candidates/nvd-sample.jsonl` | 4,682,180 B | 16,000 | public domain (17 USC 105); **CVE(R) notice required** | ✗ | ✗ | ~ | ✗ | **0/16,000 carry a CWE id; 0/16,000 carry CVSS; all 1999–2006** |
| **NVD raw page** | `cyberguard/v2/candidates/nvd-raw.json` | 4,258,928 B | 2,000 of **398,563** | public domain; CVE(R) notice | ~ | ~ | ~ | ✗ | 1,865/2,000 `NVD-CWE-Other`; cvssMetricV2 1,966 / v31 36 |
| **NVD authority gC** | `cyberguard/v2/candidates/nvd-authority-gC.json` | 22,952 B | 288 CVEs | public domain; CVE(R) notice | ~ | ✗ | ✗ | ✗ | cross-check artefact |
| **ATT&CK STIX sample** | `cyberguard/v2/candidates/attack-sample.jsonl` | 2,205,754 B | 2,198 (2,144 per `MIXTURE-V2.md`, 2,136 per `FACTS.json` — §2.4 (i)) | **MITRE Terms of Use (copy-notice required)** | ~ (11 rows, strict CVE-id pattern; 12 under the looser `CVE-\S+`) | ✗ | ~ | ✗ | **the raw master is on disk now (F-4) and it carries no CVE↔technique mapping either — 0 structured pairs, 9 prose pairs, and the sample dropped none** |
| **ATT&CK master (raw STIX)** | `data/vuln/attack/enterprise-attack.json` | 55,271,014 B | 26,690 objects — 867 attack-patterns (706 live), 3,498 external references | **MITRE Terms of Use (copy-notice required)** | ~ | ✗ | ~ | ✗ | **carries no CVE↔technique mapping** (F-4): 0 structured pairs, 9 prose pairs; byte-identical to upstream |
| **NIST CSRC** | `cyberguard/v2/candidates/nist-sample.jsonl` / `nist-raw.json` | 1,863,793 / 2,106,880 B | 1,000 sampled (530,912 claimed; 835/718 admitted) | **CC0-1.0** | ✗ | ✗ | ~ | ✗ | administrative guidance |
| **Trendyol sample** | `cyberguard/v2/candidates/trendyol-sample.jsonl` | 6,702,746 B | 1,978 | Apache-2.0 | ✗ | ✗ | ~ | ✗ | general |
| **UltraChat** | `cyberguard/v2/candidates/ultrachat-{sample,raw}.jsonl` | 1,909,402 / 690,913 B | 400 sampled (600 pairs admitted) | **MIT** (verified via HF API cardData.license) | ✗ | ✗ | ✗ | ✗ | replay slot |
| **arcspan-cyber-ner** | `cyberguard/v2/candidates/arcspan-train-sample.jsonl` | 259,827 B | 500 | Apache-2.0 | ✗ | ✗ | ~ | ✗ | **0 admitted — rejected; retained as the G-D eval corpus** |

### 3.5 Table C — mixtures, working corpora and the v4 programme artefacts

| name | location | size | rows | licence | A | B | C | D | VulnTriage |
|---|---|---|---:|---|:-:|:-:|:-:|:-:|---|
| **v3 mixture** | `cyberguard/data/v3/mixture/mixture-v3-no-trail.jsonl` | 554,059,776 B | 140,545 | mixed (per stream) | ✓ | ✗ | ~ | ✗ | fenrir 99,730 · merged 23,146 · primus 4,891 · refusal 9,584 · format 2,600 · replay 594 — **carries both contaminations** |
| **v3 mixture copy** | `cyberguard/research-tmp/harvest-v3/evals/mixture-v3-no-trail.jsonl` | 554,059,776 B | 140,545 | as above | ✓ | ✗ | ~ | ✗ | byte-identical duplicate |
| **v2 arm A** | `cyberguard/v2/data/mixture/armA.jsonl` | 202,841,462 B | 81,074 | mixed | ✗ | ✗ | ~ | ✗ | sha256 `bc785b43…edd8a7` |
| **v2 arm B** | `cyberguard/v2/data/mixture/armB.jsonl` | 202,396,764 B | 81,074 | mixed | ✗ | ✗ | ~ | ✗ | sha256 `61c94262…8091c`; **the refusal-stream control arm** |
| **v2 arm copies** | `research-tmp/harvest-v2/mixture/` + the round-rebuild directories (5,6,7,8,10) under `research-tmp/` | ~193 MB each, ~2.2 GB total | 81,074 each | as above | ✗ | ✗ | ~ | ✗ | 10 rebuild copies + the round-six change file (221 MB, 49,776 entries) |
| **v4 working corpus** | `<other-workspace>/cyberguard-v4/data/corpus/corpus-r2.jsonl` | 550,192,547 B | 135,503 | derived | ✓ | ✗ | ~ | ✗ | sha256 `c29907c1…f228`; **inherits both contaminations; not a training set** |
| **v4 row metadata** | `<other-workspace>/cyberguard-v4/data/row-metadata/{tagged-rows,metadata-tagged}.jsonl` | 708,354,046 B each | 140,545 each | derived | ✓ | ✗ | ~ | ✗ | **the reusable row_id → source provenance map** |
| **v4 dedup / leakage** | `<other-workspace>/cyberguard-v4/data/dedup-leakage/*.json` | 551,354 B total | 140,545 rows censused; 13,326 leakage rows (9.48 %); 2,498 duplicate groups | derived | — | — | — | — | **the reusable decontamination baseline** |
| **v4 quality flags** | `<other-workspace>/cyberguard-v4/data/quality/flagged-rows.jsonl` | 4,336,968 B | 37,927 | derived | — | — | — | — | held; not executed |
| **v4 supplemental** | `<other-workspace>/cyberguard-v4/data/supplemental/` | ~200 KB | 55 + 53 + 17 rubrics | ours | ✗ | ✗ | ~ | ✗ | attack→defense pairs |
| **<previous-analyst> datasets** | `<other-workspace>/cyberguard-v4/data/<previous-analyst>-datasets/` | **0 B — 0 files** | **0** | — | — | — | — | — | **EMPTY DIRECTORY — nothing materialised** |
| **v1 harvest** | `cyberguard/research-tmp/harvest-v1/` | 263 MB | **0 data rows** | — | — | — | — | — | **adapter only; the mixture is absent and unrecoverable** |
| **exclusion set** | `cyberguard/research-tmp/s2-exclusion.jsonl` | 782,811 B | 42,969 | ours | — | — | — | — | row ids; 5,042 of them were removed to make corpus-r2 |

### 3.6 Table D — public benchmark corpora (evaluation only, never trained on)

| name | location | size | rows | licence | A | B | C | D | VulnTriage |
|---|---|---|---:|---|:-:|:-:|:-:|:-:|---|
| **CTI-Bench MCQ** | `cyberguard/research-tmp/ctibench/cti-mcq.tsv` | 2,394,094 B | **2,500** | **UNKNOWN — no licence file in the directory** | ✗ | ✗ | ~ | ✗ | B5; the free-form knowledge instrument |
| **CTI-Bench RCM** | `cyberguard/research-tmp/ctibench/cti-rcm.tsv` | 990,921 B | **1,000** | **UNKNOWN — no licence file** | **✓** | ✗ | ~ | ✗ | **B1 — the CVE→CWE headline benchmark** |
| **CTI-Bench VSP** | — | — | — | — | ✗ | ✓ | ✗ | ✗ | **ABSENT — the CVSS-prediction benchmark** |
| **CTI-Bench ATE** | — | — | — | — | ✗ | ✗ | ~ | ✗ | **ABSENT** |
| **CyberMetric-500** | `cyberguard/pubbench/cybermetric-500.json` | 219,557 B | 500 | **UNKNOWN — no licence file; not listed in `v2/candidates.json`** | ✗ | ✗ | ✗ | ✗ | B6; a format-compliance instrument |
| **SecQA-v1-test** | `cyberguard/pubbench/secqa_test.csv` | 51,635 B | **110** | **CC BY-NC-SA 4.0** (`v2/candidates.json`; manifest says ~242 upstream — discrepancy, §2.4 (ii)) | ✗ | ✗ | ~ | ✗ | B7; eval-only, correctly rejected for training |
| **MITRE-FRR** | `cyberguard/pubbench/frr/mitre_frr.json` | 420,424 B | 750 | **UNKNOWN — no licence file** | ✗ | ✗ | ✗ | ✗ | B3; the false-refusal benchmark |
| **HarmBench behaviours** | `cyberguard/pubbench/harmbench/harmbench_behaviors_text_test.csv` | 160,828 B | 1,214 (159 standard-test used) | **UNKNOWN — no licence file** | ✗ | ✗ | ✗ | ✗ | B4 |
| **SecQA stub** | `cyberguard/pubbench/secqa.json` | **15 B** | — | — | — | — | — | — | a failed-download placeholder; unparseable |

### 3.7 Table E — not corpora (recorded so the inventory is complete and nothing is double-counted)

| what | location | size | what it is |
|---|---|---:|---|
| programme governance | `~/cyberguard-program/` | 278 MB | board goal, written instructions, coordination, evidence. **29,306 files under `tools/evidence/p1/` are test fixtures** (297 of them `.tar`/`.tar.gz` fixture git repos), **not datasets** |
| session transcripts | `cyberguard/SESSION-ARCHIVE/` + `.codex/sessions` | 1.5 GB | 37 codex rollout `.jsonl` (largest 576.84 MB) — transcripts, not corpora |
| rebuild scratch | `cyberguard/research-tmp/` (the round-rebuild directories) | 2.2 GB | 10 rebuilt arm mixtures + the round-six change file |
| adapters | `research-tmp/harvest-{v1,v2,v3}/adapters/`, `cyberguard/adapters/` | 526 MB + 758 MB | LoRA weights — model artifacts, excluded from the corpus inventory |
| models | `<model-cache>/cyberguard-eval/` | 93 GB | Qwen3-4B-Instruct-2507 (base), CyberSecQwen-4B (comparator), HarmBench-Llama-2-13b-cls (judge), GGUF set |
| HF cache | `~/.cache/huggingface` → `/data/huggingface` | 25.3 GB (24 GiB) | **`datasets--nebius--SWE-rebench` only** — 27,878 rows across 3 Arrow files (14,668 + 6,668 + 6,542), plus a 200-row SWE-prompt set. **Not CyberGuard data.** |
| papers | `research_tmp/` (53 MB), `resbench/` (42 MB) | 95 MB | arXiv PDFs: cysslmm, nyuctf, cyberllm, ctf, 2404.13161, 2408.08926, socceval, 2306.14898, 2406.05598, 2503.17332 — reference, not corpus |
| misc | `~/data/` (19 MB), `failure-corpus/` (280 KB), `tokenomics-bench/` (52 KB) | — | a tokenizer config, 4 markdown files, 8 task definitions |

### 3.8 Table F — what the project record says was downloaded, that is **not** on disk

| record entry | where the record says | reality on disk | consequence |
|---|---|---|---|
| **<previous-analyst> datasets** | v4 stream-4 dispatch: 5 planned files; log claims *"Loaded 140545 rows across 6 strata"* | **directory exists, 0 files, 0 bytes** | the strata were never materialised. **Nothing to fix; nothing to use.** If a held-out-1,000 set is wanted later it must be built. |
| **v1 training mixture** | v1 adapter receipt, `research-tmp/harvest-v1/` | **adapter only (263 MB)** | v1's composition is **unrecoverable**. v1 remains a *measured arm*, never a rebuild candidate. |
| **Full NVD / CVE / CWE / CVSS feed** | `v2/candidates.json` pins `nvd-cve-json-feeds` at "2000 of 398,563 CVEs sampled" | a 2,000-row API page + a 16,000-row derived sample. **No `nvd*.json.2.0.gz`, no `cwe*.csv`, no `cvss*.csv` anywhere.** | **the whole triage labelling axis is absent.** This is the primary collection need (§4). |
| **ATT&CK `enterprise-attack.json` master** | `v2/candidates.json`: *"enterprise-attack.json master as fetched 2026-09-27"* | **now on disk** — `data/vuln/attack/enterprise-attack.json` (**byte-identical to upstream**) and `data/vuln/attack/LICENSE.txt`, with the licence note; the size, the hash and the object count are in Table B and in `eval-2026-10-23/f4-attack-cve-map.json` | **and it carries no CVE↔technique mapping either** (F-4): **0** structured pairs across 3,498 external references, the v11.0 control also **0**, and the head-to-head test over all 2,198 rows shows the flattened sample dropped **no** CVE the raw object carries. The prioritisation axis still has **no upstream source**; a decision is needed on where it comes from. |
| **CTI-VSP / CTI-ATE** | `PRODUCT-DEFINITION.md` §7 step 8 | **absent** | B2 has no instrument; adopting it needs a download **and** a parser/scorer decision. |
| **EPSS / CISA KEV / OSV** | **nowhere in the record** — grep over `docs/` returns no match | **absent** | the prioritisation axis has **no upstream dependency at all** in the current plan. |

### 3.9 What the inventory says, in one paragraph

The machine holds **7,146 data-extension files, 8.27 GB**, of which **~2.7 GB is training and candidate payload** (2.09 GB in `data/v3`, 0.61 GB in `v2/data`, 0.03 GB in `v2/candidates`; ~2.2 GB of that is unique once the derived SFT copies are excluded). That payload is dominated by two large general-cyber instruction corpora (Fenrir 99,730 rows and Trendyol 50,606 rows) that contain **no CVE, CWE or CVSS field at all**. The entire CVE→CWE axis rests on **4,891 Primus rows whose targets are the corpus's most defective**, plus **268 clean trail targets** that were never trained on and are sitting in `data/v3/trails-30/`. The CVSS axis rests on **36 `cvssMetricV31` records inside a 2,000-row 1999–2006 page** — effectively nothing, and there is **no CVSS feed, no CWE list, no EPSS, no KEV and no CVE→technique mapping** anywhere on the machine. So the record is right that a great deal was downloaded: **Fenrir, Primus, the merged reasoning set, the NVD feed, ATT&CK, NIST, Trendyol, UltraChat, arcspan and every benchmark corpus are all here.** What is *not* here is the part that VulnTriage is made of. **Update, 2026-10-23 (after the Phase F downloads, ledger D-1, D-2, D-4, D-4b, D-5, D-6):** the CWE catalogue, the CVSS v3.1 specification, the ATT&CK master, the ATT&CK v11.0 control and the CTI-VSP/ATE files are **now on disk** — and the gap they were collected to fill is **still open at the mapping**: F-4 measured **0** structured technique↔CVE pairs in the ATT&CK master (the v11.0 control also **0**), and MITRE publishes no CVE-mapping artefact at all. The CWE catalogue and the CVSS specification do fill their own gaps; the ATT&CK master does not.

---

## 4. What is genuinely missing for the VulnTriage rebuild

Only now, after the inventory.

### 4.1 The axes: what is on disk, and what the corpus needs

| axis | on disk today | gap | needed for the product? |
|---|---|---|---|
| **A — CVE→CWE** | 4,891 Primus prompts (targets contaminated) + 268 clean trail targets + 12 ATT&CK rows | **4,623** Promus rows have no replacement target, and **4,758** need a contract-conformant one written; the 4,891 are ODC-By, **attribution-required**, from a **gated** repo | **yes** — and the licence carries a redistribution condition to discharge |
| **B — CVSS** | 36 `cvssMetricV31` metric entries and 1,966 legacy `cvssMetricV2` entries, inside the 2,000-row 1999–2006 page; no feed, no vector list, no CTI-VSP instrument | **the entire axis** | **yes** — this is the product's second headline claim |
| **C — impact** | implicit in Fenrir/Trendyol general text; ATT&CK technique prose | CVE-anchored impact statements in the triage schema | **yes** |
| **D — prioritisation** | **nothing** — no EPSS, no KEV, no asset context, no exploitation signal | **the entire axis** | **yes** — and this is the axis the market's #1 pain (alert triage / false-positive suppression) actually lives on [R3, R6] |

### 4.2 The minimum collection spec

**This is a specification, not a download plan.** No fetch was performed and none is authorised by this document. Each item names the source, why, the licence it must arrive under, and what it unblocks.

| # | source | scope | why | licence to verify | unblocks |
|---:|---|---|---|---|---|
| **C1** | **NVD 2.0 CVE feed, modern window** (≈ 2020 → present) | the CVEs that carry a usable `CWE-*` assignment and a **v3.1** vector | supplies **A** and **B** together, joined and labelled | public domain (17 USC 105) + **CVE(R) notice** | the triage corpus's spine; B1's training analogue |
| **C2** | **MITRE CWE list** (the CWE catalogue, not the CVE mappings) | the CWE hierarchy and its views | C1's `CWE-*` strings are meaningless without the catalogue's semantics and hierarchy | MITRE Terms of Use (copy-notice) | CWE plausibility — the deterministic validator [R4] |
| **C3** | **CVSS v3.1 specification + vector corpus** | the scoring definition and its worked vectors | B needs a *definition* to learn against, and the validator needs the vector grammar | public specification (FSF-documented) | B2's instrument; the validator |
| **C4** | **ATT&CK `enterprise-attack.json` with `external_references`** | the raw STIX master — **collected (D-4) and measured (F-4)** | **restores nothing.** The raw master carries **0** structured technique↔CVE pairs (3,498 external references scanned; the v11.0 control also **0**), and the flattened sample dropped **no** CVE the raw object carries (head-to-head over all 2,198 rows: **0** differ). What exists is prose — **9** pairs over **7** distinct CVEs, **8** of them in a technique's own text. MITRE's usable signal is website-only (the T1190 page names **63** CVEs; its STIX object carries **0**) | MITRE Terms of Use (copy-notice) — **licence note written and the obligation quoted from the artefact**; the *mapping* remains **unsourced**, so axis **C** needs a decision |
| **C5** | **EPSS / CISA KEV** *(optional)* | daily EPSS scores; the KEV catalogue | axis **D** — prioritisation beyond the raw CVSS score | EPSS: public (CISA); KEV: public domain | the prioritisation claim, and the market's actual pain |
| **C6** | **CTI-VSP and CTI-ATE** | the two missing public benchmarks | B2 has **no instrument at all** today, and adopting one requires a parser/scorer that does not exist in this project | public, third-party | B2; the "is the CVSS claim measurable" question |

**C1–C3 are the irreducible minimum** to make VulnTriage a triage product. C4 and C5 are what turn it from "CWE + score" into "triage". C6 is what makes the claim falsifiable.

### 4.3 What must **not** be collected, and why

- **No new general instruction corpus.** Fenrir (99,730) and Trendyol (50,606) already cover general cyber instruction, and the v3 mixture is **70.97 % Fenrir** on its own. A fourth general corpus makes the corpus bigger without making it a triage corpus.
- **No new refusal or format corpus from scratch.** Both exist on disk and are licensed to this project. The work is **reweighting** the refusal stream against a two-sided bar (Pearson −0.87) and **extending** the format set to the triage schema — not collecting.
- **No re-collection of arcspan, UltraChat, NIST or Trendyol.** They are present, licensed, and either rejected or non-triage.
- **No attempt to reconstruct v1's mixture.** Unrecoverable, and not needed.

### 4.4 The order, once collection is authorised

1. **Step 0** — re-issue the ledger; publish the provenance map; write the licence table. *(no network)*
2. **Step 3** — the product contract, including **the triage schema and the abstain option** [R4]. *(no network)*
3. **Step 6b** — write and execute the corpus exclusion set; add the stock-preamble gate. *(no network)*
4. **C2 + C3** first — the CWE catalogue and the CVSS specification. They are small, they define the labels and the validator, and **C1's fetch depends on them** (you cannot label what you cannot describe).
5. **C1** — the modern NVD fetch, labelled and joined.
6. **C4** — the ATT&CK master. **Done, and it restored nothing** (F-4): the raw STIX carries **0** structured technique↔CVE pairs, the v11.0 control also **0**, and the flattened sample dropped **no** CVE the raw object carries. The mapping is **unsourced** and axis **C** needs a decision.
7. **Extend `format-compliance` in place** to the triage schema — the output-contract supervision.
8. **Step 6** — qualify the corpus against the (now-approved) calibration protocol; issue the Data Gate.
9. **C6** — CTI-VSP/ATE, if B2 is to be a bar rather than a gap.
10. **Step 8b** — ship and measure the output contract on the frozen surface.
11. **Step 9** — training, only after 3–8b, only on a recorded decision.

---

## 5. Open questions

These are **data decisions**. They are not measurement questions, and the measurement work does not need them answered to continue.

1. **The refusal stream's target weight, chosen against both ends.** The dial is two-sided (Pearson −0.87). The corpus-only floor is the untrained base model's own 4.13 % FRR; the public comparator is at 1.07 %. **What FRR does the release target, knowing that every point of it is paid for on the HarmBench side?** v1 (10.93 % / 12-of-159) and v3 (29.07 % / 0-of-159) bracket the current family. **→ EXECUTED 2026-10-23 under programme decision 3** (recorded with the full policy in `docs/REFUSAL-POLICY.md`), open to confirmation or override: the target is **4.91 %** — the lowest share with a *measured* FRR and a *measured* harmful-compliance count on the same instrument — giving **5,314 presentations** from the 1,198 distinct rows in a **108,238**-row corpus (measured **4.9096 %**). The full policy, the two-sided cost and the alternatives' row counts are in `docs/REFUSAL-POLICY.md`; changing the target is one parameter and one command. **The answer is still wanted**, because the target's harmful side (5/159, Wilson upper 0.0554) sits above the programme's release bar, as does the public comparator's (3/159, upper 0.0540).
2. **Rebuild vs. repair — for `merged` specifically.** The corpus exclusion stands. The question is narrower than the record's framing: is the code→CWE weakness-localisation habit worth a **regenerated, preamble-clean** version of the 23,146 rows, or is a fresh CVE→CWE corpus from C1 enough? **This is not the implementation's to decide.**
3. **CVSS v3.1 versus v2 in the corpus.** The 2,000-row NVD slice on disk is 98 % `cvssMetricV2`. If the corpus is built from the modern feed it will be v3.1 throughout. **Confirm v3.1 as the single target**, because the validator [R4] and the B2 instrument both have to speak the same vector grammar.
4. **Does prioritisation get EPSS/KEV, or is severity the whole claim?** The market's #1 pain is false-positive suppression, which needs a ranking signal beyond CVSS. If the answer is "severity only", the product's claim narrows and the collection list shortens to C1–C4 + C6.
5. **CTI-VSP: adopt as a bar, or record as a gap?** It needs a download **and** a parser/scorer that do not exist in this project. Adopting it means a new instrument and a new decision; leaving it means B2 has no baseline on either side, which is the current state.
6. **Primus's redistribution condition.** ODC-By requires attribution, and the repo is gated. A release that ships a model trained on Primus-derived supervision needs the attribution and the gate access recorded — and the 268 clean trail targets are **derived** from Primus prompts, so they inherit the condition. **Does the release stack carry Primus attribution, or does step 7's corpus avoid Primus entirely and rebuild the CVE→CWE task from C1?**
7. **The `trails-30` generation is incomplete.** `trails_muse_7k.jsonl` holds **855 of a planned 7,000** rows, with 79 errors logged. The deepseek 7k run completed. **Is the muse trail set worth regenerating** as additional clean reasoning supervision, or is 7,000 enough?

---

## Appendix — evidence index for this document

| artefact | path | what it establishes |
|---|---|---|
| **verification script** | `cyberguard/eval-2026-10-23/data_inventory_verification.py` | recomputes every figure in §2.4, §3.4 and §4 from files on disk; read-only |
| **verification output** | `cyberguard/eval-2026-10-23/data-inventory-verification.json` | the machine-readable form of the same figures |
| **path + size lint** | `cyberguard/eval-2026-10-23/lint_next_steps.py` | every path cited in this document exists; every `NNN B` figure matches the file. **77 paths, 0 missing; 38 byte figures, 0 wrong** |
| **row-count lint** | `cyberguard/eval-2026-10-23/lint_next_steps_rows.py` | every row count quoted in this document matches the file, counted by the same method the frozen runner uses. **39 counts, 0 wrong** |
| **trails probe** | `cyberguard/eval-2026-10-23/trails_primus_probe.py` | the 268-row clean CVE→CWE subset (§2.3 (a)) |
| **v2 mixture facts** | `cyberguard/v2/data/mixture/FACTS.json` | the composition that matches the arms on disk |
| **v2 ledger** | `cyberguard/docs/MIXTURE-V2.md` | the frozen ledger that does not match it (§2.4 (i)) |
| **candidate licence manifest** | `cyberguard/v2/candidates.json`, `cyberguard/v2/candidates/SAMPLES.json` | the 9-source licence ledger |
| **v3 mixture receipt** | `cyberguard/data/v3/mixture/MIXTURE-V3-RECEIPT.json` | the v3 composition, weights and S5 trail verdict |
| **licence receipts** | `cyberguard/data/v3/{fenrir-v2.1,cybersec-reasoning-merged,primus-reasoning}/LICENSE_RECEIPT.md` | Apache-2.0 / Apache-2.0 / ODC-By (attribution required, gated) |
| **v4 corpus receipt** | `<other-workspace>/cyberguard-v4/data/corpus/receipt-r2.json` | the only removal pass was 5,042 exact duplicates |
| **redaction receipt** | `cyberguard/data/v3/REDACTION-RECEIPT.json` | the Fenrir redaction pass (6 rows changed) |
| **corpus exclusion decision** | the programme's decision record | "Primus and the merged reasoning corpus stay excluded" |
| **bar sheet** | `cyberguard/PRODUCT-DEFINITION.md` §5 | B1–B8 with their baselines |
| **build path** | `cyberguard/PRODUCT-DEFINITION.md` §7 | the path this document orders |
| **evaluation** | `cyberguard/EVALUATION.md` | every measurement cited here, by section |
| **decisions** | the programme's decision record and the v3 decision record | two namespaces; cite the file, never a bare "D11" |

**Standing note (updated 2026-10-23, after the sweep landed).** The CTI free-form sweep for v1, v2 arm A and v2 arm B (3,500 items × 3 arms) has **finished and been merged**: the merged artefact went from 18 to 24 comparison rows, §5.3 was regenerated and spliced, and the consistency and lint passes were re-run. It closed the last gap in `EVALUATION.md` §7 step 0-5 — the older arms had never been run on the **free-form** benchmarks, the ones that do not confound format with knowledge. **What it found:** all three score **below the public comparator** on both CTI benchmarks (v1 0.1676 / 0.0000, v2 arm A 0.1124 / 0.0490, v2 arm B 0.4172 / 0.1270, against the comparator's 0.5764 / 0.6780), and two of them are below the always-C floor of 0.3712 on CTI-MCQ. The decomposition in §5.3.7b adds the qualifier the record needed: for v1 and v2 arm A the gap is substantially an **output contract** rather than a capability gap. **No arm's status changes on the strength of a ceiling** — the frozen numbers are the measurement.
