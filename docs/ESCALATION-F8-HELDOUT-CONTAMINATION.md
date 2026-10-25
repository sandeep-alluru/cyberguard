# Escalation F-8 — the 500-row held-out set is inside the training corpus

**Raised:** 2026-10-23 · **Ledger item:** F-8 (decontamination) · **Status:** OPEN, awaiting a ruling
**Measurement:** `eval-2026-10-23/f8-decontamination-report.json` (**18/20**, exit 1) · `eval-2026-10-23/f8c-holdout-leak-trace.json` (**15/15**, exit 0)

> **This document asks a question and does not answer it.** Removing rows from the training
> corpus is a corpus decision, and the worker does not make corpus decisions. Everything below is
> a **count**, an **authority fact**, and **three candidate treatments with their consequences**.

## 1. The counted class

The v2 admission gate split the Trendyol corpus into **51,784 train rows** and a **500-row
held-out set** (`v2/holdout500.jsonl`), and the exporter's own docstring says the split is *"by
construction the SAME 500 rows the v1 benchmark used"*. That held-out set is the instrument behind
EVALUATION.md §5.2a (held-out loss for every arm) and §5.3.5 (reference token-F1 for every arm).

**499 of those 500 held-out questions are in the rebuilt training mixture**, as **604 rows**, all
of them in the `fenrir` stream:

| stage | file | rows | rows carrying a held-out identity | distinct held-out rows covered |
|---|---|---:|---:|---:|
| fenrir, as downloaded | `data/v3/fenrir-v2.1/220426-CyberSec-Dataset_escaped.jsonl` | 99,870 | **605** | **500 / 500** |
| fenrir, cleaned | `data/v3/fenrir-v2.1/clean/fenrir-v2.1.clean.jsonl` | 99,852 | **605** | **500 / 500** |
| **v3's own SFT file** | `data/v3/sft/fenrir.jsonl` | 99,730 | **604** | **499 / 500** |
| **v3's training mixture** | `data/v3/mixture/mixture-v3-no-trail.jsonl` | 140,545 | **604** | **499 / 500** |
| the rebuilt corpus | `data/v4/corpus-v4-r3.jsonl` | 108,978 | **604** | **499 / 500** |
| **the rebuilt mixture** | `data/v4/mixture-v4.jsonl` | 367,198 | **604** | **499 / 500** |

Every other source — `triage` (245,273), `refusal` (18,029), `format` (3,304), `replay` (594),
`triage_salvage` (268) — carries **0**.

**The prompts are byte-identical, not paraphrases.** All **604 of 604** leaked rows carry the
held-out row's prompt string exactly. The identity key is the project's own —
`v2/export_holdout.py` writes `prompt_sha256 = sha256(" ".join(user.lower().split()))[:16]` and
says in its own comment that it *"must match gate_v2.prompt_hash_of and the dedupe key"*; the
trace cross-checks that key against the gate's own `prompt_hash_of` on 100 rows (**100/100 agree**).

**The answers leak too — and this section was WRONG when it was first written, which is why it
carries its own correction.** The first version of this document said that **25** of the 604 rows
carried the held-out answer and **579** carried "the fenrir corpus's own answer in the fenrir
house style". **That was an artefact of the instrument, not a property of the corpus.** The
held-out file stores the Trendyol reference with the escaping it came with — which varies in
depth between rows — while the SFT file restores literal `\n` to real newlines, so a **raw**
string comparison reported a difference on rows whose answers are in fact the same text. The
trace now compares the answers' **content** (escape syntax and whitespace removed), and the
corrected figures are:

- **499 of 604** (**82.6 %**) carry **the held-out row's own answer content** — **25** of them
  byte-identical and **474** differing only in JSON escaping depth;
- **105** carry a genuinely different answer (of which 3 are a refusal on both sides worded
  differently, 3 are the corpus refusing where the reference answers, 1 the other way round, and
  **98 are neither**).

**So the held-out set's answers leak into the training corpus far more than this document first
claimed: not a small minority but the large majority.** The correction is in the *conservative*
direction against the programme's own interest, and it is recorded here rather than quietly
replaced. The instrument that produced the wrong number was
`eval-2026-10-23/f8c_trace_holdout_leak.py`, and the comparison it now performs is written down
in the file's own `skeleton()` docstring.

The residual overlap is high (fenrir `jaccard_max` **0.7566**, `containment_max` **0.9795**)
because the **prompt** text is identical, and in 499 of the 604 rows the **answer** is the
held-out answer as well — so what the model would be trained on is the held-out item in full.

**The residual overlap is above the gate's own reject threshold.** The bar F-8 names is the v2
gate's recorded maximum across its 8 admitted candidates — `overlap_max` **0.0266**,
`containment_max` **0.0723**. fenrir measures **0.7566 / 0.9795**, and the gate's own reject
thresholds are **0.6** (overlap) and **0.8** (containment). **The gate would have rejected this
source on both counts.**

## 2. The cause, measured

**The fenrir bundle contains a copy of the very corpus the held-out set was split from.**
`data/v3/fenrir-v2.1/` holds `220426-CyberSec-Dataset_escaped.jsonl` — the Trendyol dataset,
**99,869 rows** — alongside fenrir's own rows, and **605 of its rows carry a held-out identity
covering all 500 of them**. The contamination is therefore **present in the download itself**,
before any processing this project performed.

**The source that carries it was never gated.** `v2/gate-report.json` gated **9 candidates**:
Trendyol, `ethanolivertroy/nist-cybersecurity-training`, `mitre-attack/attack-stix-data`,
`nvd-cve-json-feeds`, the two authored sets, `chairulridjal/arcspan-cyber-ner`,
`zefang-liu/secqa` (rejected) and `HuggingFaceH4/ultrachat_200k`. **Fenrir is not among them.**
Every gated candidate was fetched on **2026-09-27**; fenrir was fetched on **2026-09-29**
(`data/v3/dl-fenrir.log`) and never passed through the gate. The held-out set's exclusion was
therefore never established for the one source that actually carries it.

**The one contamination report that does exist covers a different population.**
`data/v3/fenrir-v2.1/CONTAMINATION_REPORT.md` records *"rows scanned: 99870 / contaminated rows:
0"* — against **CyberMetric-500** and SecQA, and SecQA's fingerprint file was a failed-download
placeholder that the report itself excludes. **It names neither the 500-row held-out set nor the
Trendyol corpus it came from.** Its zero does not contradict this finding; it is a zero about
other things.

**And the check that did run on the built mixture was aimed at the public set.**
`docs/CHECKPOINT-v3-02-2026-09-30.md` records a *"CONTAMINATION-FREE"* verdict for v3's mixture
against **CyberMetric-500 + SecQA (610 items)** — v3's §8.6 held-out set, as that document
correctly says, *"is not v2's `holdout500.jsonl`"*. The verdict is sound **for what it tested**.
The 500-row Trendyol holdout was never checked against the built mixture.

## 3. What is **not** broken

Two things that could be mistaken for damage are not.

- **No admissible evidence is affected.** `eval-2026-10-23/f8b-public-benchmark-integrity.json`
  (**14/14 PASS**) measures the mixture against the two public benchmarks on disk: **0 exact
  normalised-prompt matches** against CyberMetric-500 (500) and SecQA-v1-test (110) across **all
  six sources**, and **residual overlap 0.0 on every source** for both. Every public-benchmark
  number in EVALUATION.md — CTI-MCQ, CTI-RCM, MITRE-FRR, HarmBench, CyberMetric, SecQA — rests on
  a population the mixture does not touch. **The contamination is confined to the internal,
  retired 500-row battery.**
- **v1 and v2 are not affected.** v1 was trained on the Trendyol corpus (52,284 rows,
  `docs/muse-1.3-cyberguard-v1-training-postmortem-2026-09-27_153135CDT.md:29`) with the same
  500-row split excluded by construction, and v2's corpus is exactly the gated candidate set,
  fetched before fenrir existed. Their held-out losses and token-F1 are sound.

## 4. What **is** affected

**v3's held-out loss and token-F1 were measured on a split v3 trained on.** This is the
consequence, and it reaches published claims:

| published claim | where | status |
|---|---|---|
| "v3 is the best-fitting model in the family on the held-out domain split — 0.7738 against v1's 0.8762, v2's 0.8128/0.8147 and base's 2.3602" | EVALUATION.md §5.2a, and repeated in the §1 finding 3, §4, §5.3.5, §9 and §8 | **REPAIRED — withdrawn for v3.** The three clean arms are unaffected; v3's figure was measured on 499 of the 500 questions it trained on. |
| "all four tuned arms PASS the project's own joint §8.6 rule — token-F1 ≥ base + 0.02 **and** held-out loss ≤ base" | EVALUATION.md §5.3.5, §8.6, §9 | **REPAIRED — v3's pass on the held-out-loss half is withdrawn.** The token-F1 half was measured by generating on the same 500 rows, so it is affected the same way. |
| "the failure is one of **transfer, not of fit** … more training on the same corpus cannot fix it" | EVALUATION.md §1 finding 3, §5.2a, §8 | **REPAIRED — withdrawn as a statement about v3.** The measurement cannot distinguish "fits the corpus" from "fits the held-out questions it was trained on". |
| "held out from training by construction" | NEXT-STEPS.md §data-inventory row `holdout-500` | **REPAIRED** — the row now names the scope (*held out from the Trendyol train split by construction — but not from the fenrir stream*), and the two fenrir rows name the count. |
| "held-out NLL on the verified v1 split — **0.7738** — best in the family" | PRODUCT-RESEARCH.md §R1.3 | **REPAIRED** — the row now gives the three clean arms and records v3 as withdrawn and UNMEASURED on this instrument. |
| the generated §5.3.5 table | `eval-2026-10-23/make_results_tables.py` → `SECTION-5.3.md` → EVALUATION.md | **REPAIRED AT SOURCE** — the generator now reads the F-8 trace artefact and withdraws the contaminated arm's row automatically, so a regeneration cannot silently restore the claim. |

**The repairs are guarded.** `eval-2026-10-23/check_document_consistency.py` now lists the
withdrawn forms as **forbidden assertions** and scans **EVALUATION.md, PRODUCT-RESEARCH.md,
PRODUCT-DEFINITION.md and NEXT-STEPS.md** for them, line-scoped so that a document may quote a
withdrawn claim in order to withdraw it and is not penalised for the retraction. The guard was
**proved to fire** by planting an assertion, not merely observed to be silent. The finding is
also entered in the failure register as **A9** — *"a split's construction read as a property of
the corpus"* — and in **Pattern 2** there.

**What is *not* claimed here.** The magnitude of the effect on v3's 0.7738 is **UNMEASURED**.
**The correction above makes the concern larger, not smaller**: in **499 of the 604** leaked rows
the corpus carries the held-out row's own answer content, so the model was trained on both the
held-out question and its answer in the large majority of cases. What still bounds the claim is
that 0.7738 is a moderate NLL, not the near-zero a fully memorised set would produce — a
memorised 500-row set would score far lower. **No correction factor is asserted, because none has
been measured.**

## 5. The three candidate treatments

All are defensible. None is chosen here.

### Treatment A — **remove the 604 rows and re-derive**

- *What it does*: drops 604 of 367,198 rows (**0.164 %**), all fenrir, and rebuilds the mixture.
- *What it costs*: a **corpus change without a ruling**. fenrir is the mixture's largest general
  stream by characters (**68.0 %**), so a 0.261 % row trim is small by count but the removal's
  effect on coverage is **UNMEASURED**. The mixture must be re-assembled and F-7's weight
  rationale re-checked against the new counts.
- *What it buys*: the held-out set's exclusion becomes **true by construction** for the rebuilt
  mixture, and F-8's acceptance check would then pass on the mixture it is run against.
- *What it risks*: **it does not repair the history.** v3's published held-out loss and token-F1
  stay contaminated, and the two internal instruments stay unusable for v3 unless the arm is
  retrained.

### Treatment B — **keep the rows, retire the 500-row holdout as an instrument, record the class**

- *What it does*: keeps all 367,198 rows and records the 604 as a **known, counted, named
  class**, retires `v2/holdout500.jsonl` as an evaluation instrument for any fenrir-derived arm,
  and withdraws the §5.2a / §5.3.5 / §8.6 claims that depend on it.
- *What it costs*: **two of the project's own diagnostic instruments are lost** for the arms built
  from fenrir, and the "v3 is the best-fitting arm" reading is withdrawn rather than repaired. The
  finding that v3's failure is one of transfer rather than fit is **no longer available from this
  instrument.**
- *What it buys*: **no corpus change without a ruling**, and a record that states what the
  measurement was and was not.
- *What it risks*: the contamination stays in the training corpus. Any future arm built on the
  mixture inherits it, and the exclusion is only enforced by **the removal or the discipline of
  whoever builds next** — not by the corpus's construction.

### Treatment C — **build a clean held-out split and re-measure**

- *What it does*: constructs a **new** held-out split from a population that is in **no** arm's
  training corpus, and re-measures held-out loss and token-F1 on it.
- *What it costs*: a new split is **a new instrument**, and it is not comparable to the v1
  verdict's 500-row split — the replication check that anchors §5.2a (base 2.3600 → 2.3602,
  v1 0.8763 → 0.8762) **does not transfer**. It also needs a source outside every training
  corpus, which the inventory must supply.
- *What it buys*: a **sound** held-out instrument that v3 has not seen, and therefore a number
  that can actually answer "is v3 under-trained?".
- *What it risks*: the cheapest available reading is that this is an **expensive** way to
  re-derive a question the public benchmarks already answer — and the public benchmarks are the
  project's admissible evidence class in any case.

### What would settle it (neither treatment's weakness)

A **measurement that separates the two things the 0.7738 conflates**: hold out a **subset** of
the 604 contaminated rows' questions from a *fresh* fenrir-derived corpus and measure v3's
held-out loss on the contaminated rows and the clean rows separately. If v3's loss on the
contaminated rows is materially lower, the contamination inflated the number; if the two are
similar, the number stands and the reading of §5.2a survives. **That needs no trained model and
no new data** — it is a re-scoring of the existing v3 checkpoint against a split of the existing
500 rows by contamination status. **It has not been performed here**, because what it decides is
the ruling's.

## 6. The question

> **Should the 604 contaminated fenrir rows be removed from the training corpus and the mixture
> re-derived (Treatment A), should they stay with the 500-row holdout retired as an instrument
> and the dependent claims withdrawn (Treatment B), or should a clean held-out split be built and
> the measurement re-run (Treatment C)?**

**The worker does not choose.** Choosing a corpus change is the decision-maker's, and the
candidate treatments differ in coverage and in measured-ness, not in taste. The ruling should also
say whether the 500-row holdout is **retired outright** or kept with a scope note naming the
arms it is valid for.

**Until the ruling arrives, the rows stay** — in `data/v4/corpus-v4-r3.jsonl` and in
`data/v4/mixture-v4.jsonl`, unchanged and counted here, so that no later reader mistakes this
mixture for a decontaminated one. **The mixture is provisional in any case**: Phase D's removals
(D-3, D-4) and D-7's Data Gate are outstanding and blocked on humans.

## 7. The evidence

| artefact | what it carries |
|---|---|
| `eval-2026-10-23/f8-decontamination-report.json` | F-8's decontamination report: per-source residual overlap against the v2 gate's own instrument (**18/20**, exit 1) |
| `eval-2026-10-23/f8c-holdout-leak-trace.json` | the leak path stage by stage, with the project's own identity key (**15/15**, exit 0) |
| `eval-2026-10-23/f8b-public-benchmark-integrity.json` | the public benchmarks' integrity on the mixture: **0 exact matches, 0.0 residual overlap** (**14/14**) |
| `eval-2026-10-23/f8c_trace_holdout_leak.py` | the trace instrument; imports `v2/gate_v2.py::prompt_hash_of`, downloads nothing |
| `eval-2026-10-23/check_document_consistency.py` | the guard: the withdrawn forms are forbidden assertions, scanned across the four deliverables, line-scoped for retractions |
| `eval-2026-10-23/make_results_tables.py` | the generator now reads the F-8 trace and withdraws the contaminated arm's §5.3.5 row itself, so a regeneration cannot restore the claim |
| `v2/gate-report.json` | the v2 admission gate's own record: 9 candidates, **none of them fenrir**, and the bar (0.0266 / 0.0723) |
| `v2/holdout500.jsonl` + `v2/holdout500.manifest.json` | the certified 500-row split and its manifest |
| `data/v3/fenrir-v2.1/CONTAMINATION_REPORT.md` | the v3 report whose zero covers CyberMetric-500 (and SecQA, excluded as a failed download) — **not** this holdout |
| `docs/CHECKPOINT-v3-02-2026-09-30.md` | the mixture's *"CONTAMINATION-FREE"* verdict against the **public** 610-item set |
| `docs/ESCALATION-C9-TRAIL-MARKER-RESIDUE.md` | the sibling escalation in the same stream — 378 marker rows, also awaiting a ruling |

---
