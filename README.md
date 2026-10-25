# CyberGuard VulnTriage

> **A CVE or advisory in → CWE + CVSS v3.1 vector and score + plain-English impact + a
> prioritisation call out — proven only on public benchmarks, with ship/no-ship bars fixed in
> advance.**

**This repository is the evaluation programme, not a model release.** The model does not ship today.
The arm of record — **v3** — is a **NO-SHIP** on its own criteria, the release table does not carry
it forward, and the corpus Data Gate is **BLOCKED**. The recorded path forward is a new arm trained
from the base checkpoint on a qualified corpus.

Everything below is the proof of work that got us there, with the receipts.

---

## The benchmark table

Four models, one scoreboard. Every bar was written down **before** the training run, and no bar
may be restated once a new arm's number is visible.

**Legend —** **P** = **PUBLISHED** (by that model's own authors; cited under *Sources*).
**F** = **FIRST-PARTY** (our own evaluation; the report and its receipt are in `results/`).
A bar that fails is shown failing. A number we have not measured is shown as not measured.

| model | CTI-RCM ↑<br>CVE→CWE | CTI-MCQ ↑<br>2,500 MCQs | CTI-VSP ↓<br>CVSS MAD | MITRE-FRR ↓<br>false refusal | HarmBench ↓<br>harmful / 159 | CyberMetric-500 ↑ | SecQA ↑ |
|---|---|---|---|---|---|---|---|
| **the bar** | **> 0.6780** | *report only* | **≤ 1.223** @ 2048 | **≤ 5.13 %** | **≤ 1/159** (Wilson ≤ 3.50 %) | *report only* | *report only* |
| Qwen3-4B-Instruct-2507<br>*(base, untrained)* | 0.4100 **F** | 0.4444 **F** | 1.32 **F** | 4.13 % **F** | 1/159 **F** | 0.4680 **F** | 0.6818 **F** |
| **CyberSecQwen-4B**<br>*(the direct twin)* | 0.6664 **P**<br>0.6780 **F** | 0.5868 **P**<br>0.5764 **F** | 1.223 **F** | 1.07 % **F** | 3/159 **F** | 0.4460 **F** | 0.4727 **F** |
| **Cisco Foundation-Sec-8B-Instruct**<br>*(the reference specialist)* | 0.692 **P** | 0.644 **P** | 0.802 **P** ⚠ | not measured | not comparable ⚠ | not measured | not measured |
| **CyberGuard VulnTriage v3**<br>*(arm of record — NO-SHIP)* | **0.6360 F** ✗ | 0.4648 **F** | not measured | **29.07 % F** ✗ | **0/159 F** ✓ | **0.8000 F** | **0.9364 F** |

**Read it like this.** v3 is the **best** of the four on CyberMetric-500 (0.8000) and on SecQA
(0.9364), and it **clears** the HarmBench bar outright — 0 harmful completions in 159, the only
model in the table besides the untrained base to do so. It **fails** two bars: CTI-RCM, where it
lands 4.2 pp under a comparator it was measured against on the same surface, and the false-refusal
rate, where 29.07 % is **5.67×** a 5.13 % ceiling. That is why it is a NO-SHIP and why the next
arm is trained from base rather than from v3.

**The bars are of record** in [`docs/BAR-SHEET.md`](docs/BAR-SHEET.md) §2 — each with its
population, its baseline and its status. The release rule is §0 of the same sheet.

**Notes on the table.**

- **B1's bar (0.6780) is our own re-measurement of CyberSecQwen-4B** on this programme's equal-terms
  surface, not its published 0.6664 — that comparator, re-measured here, *is* the bar any
  CyberGuard release is judged against. Both numbers are shown rather than one.
- **The 5.13 % false-refusal ceiling** is *base + 1.0 pp*, with the base re-measured at 4.13 %
  (31/750). An earlier record of this bar read 5.27 %, built on a pre-repair base figure; it was
  corrected, not re-decided. The operative form — *no worse than the untrained base* — is
  unchanged.
- ⚠ **CTI-VSP is not comparable across the column.** CTI-Bench's own metric for the task is mean
  absolute deviation in CVSS points, lower is better, and that is how we score it (our comparator
  MAD **1.223**, base **1.32** at 2,048). Cisco's card describes CTI-VSP the same way but tabulates
  it alongside accuracy-style numbers and never states the direction, so its 0.802 cannot be placed
  against a MAD. It is shown, and not used as a bar.
- ⚠ **Cisco's HarmBench figure is a different measure.** Cisco publishes a HarmBench *safety rate*
  (91.98 % for Foundation-Sec-8B-Instruct, 99.25 % with LlamaGuard) over the full suite. Our bar
  counts **harmful completions out of the 159 standard-test behaviours**, and the two cannot be
  converted into one another. Cisco's row is therefore unmeasured here rather than guessed.
- **v3 was never measured on CTI-VSP.** It is not a zero; it is a hole.
- The report-only rows (CTI-MCQ, CyberMetric-500, SecQA) are published **with their unparseable
  rates in the same row** and are never subtracted against a chance floor.

**Where each number lives.** The first-party numbers and their receipts are in
[`results/`](results/); the bar sheet says which artefact each printed figure comes from in §5.
The published numbers are cited under *Sources*.

---

## The differentiator

Most model cards tell you how good a model is. This programme tells you **how it knows**, and
publishes the parts that are unflattering. Four things, in plain language:

**1 · The bars are fixed before the run, and cannot be moved afterwards.**
Every instrument's population, baseline and threshold is written down in advance. The rule is not
a convention — it is binding: the harmful-compliance bar was fixed by supervisor ruling *before*
the new arm's number could be seen, and it may not be restated afterwards.

**2 · Public third-party benchmarks only. Our own instruments decide nothing.**
Every bar is a published external suite with a public dataset and a protocol anyone can run. The
programme's self-made gates are diagnostic: they tell you where to look, and they never decide a
release. This is the direct fix for how this project failed once before — it spent a great deal of
effort grading itself with instruments it wrote.

**3 · Contamination is caught before it ships, not after.**
The programme's held-out set is 500 rows. **604 rows carrying a held-out identity were found
inside a training file, covering 499 of those 500 rows**, with byte-identical prompts. It was
caught by the programme's own gate — and it is the reason the next arm trains from base instead of
warm-starting from v3. A model card cannot show you a contamination check that passed; this one
shows you the check that *failed*, and what was done about it.

**4 · We publish our own judge's agreement rate.**
Where a human reviewer would normally stand in, this is a one-person programme, so the model's own
judgement stands in — and **every such judgement is labelled *model-adjudicated* where it is cited,
never as a human reference**. We also publish how far our judge actually agrees with a benchmark's
own human labels: on the official HarmBench judge, our run agrees with the suite's published human
column on **227/300 = 75.67 %**, against the suite's own **78.33 %**. That number is unflattering
and it is in the record.

> **PROPOSED — name for the method: *Bar-First Evaluation*.**
> The claim it makes is narrow and checkable: *the ship/no-ship threshold for every public
> benchmark is published before the run, the benchmark is public and third-party, and the
> programme's own failures — contamination, judge disagreement — are published with the results.*
> A name is a proposal, not a finding; the finding is the record.

---

## The path, plainly

**1 · Fix the gate measurement.** The corpus **Data Gate is BLOCKED — NOT PASS**. All three
registered limits — unsafe < 1 %, off-topic < 2 %, shallow < 5 % — are **NOT MEASURED**, because
the §6 confirmation draw has not been run; and the non-statistical criterion **cross-row leakage
FAILED**. The gate is being repaired before it is re-measured, and the re-measurement is to be
preregistered with a named reviewer pair and a decision rule.

**2 · Certify the corpus.** Run the confirmation draw; re-issue the gate. It must read **PASS**
with all three limits measured and the leakage criterion satisfied. No training is valid before it.

**3 · Train the new arm from base.** LoRA r = 32 on `Qwen3-4B-Instruct-2507`, **from the base
checkpoint, no warm start**, with the refusal-stream weight as the single controlled variable and
the epoch **never truncated** — an earlier run in this programme died at two tenths of an epoch
under a time cap, and that failure mode is excluded on the record. A 30-step throughput pilot has
already measured the machine at **2.506 samples/s**; the pilot's receipt is published, its adapter
is not, and it is not a release candidate.

**4 · Evaluate it on every bar.** Same frozen surface, same session, same instruments. B1–B4 decide;
B5–B8 are reported with their parse rates.

**5 · Rule it.** Ship or do not ship — recorded either way, with the numbers.

Then, and only then, the six release artefacts: merged bf16 weights → GGUF bf16 → Q4_K_M →
`generation_config.json` → model card → hash-frozen bundle. Until a **serving party** is named, a
release can be shipped as an artefact bundle but cannot honestly claim to be served.

---

## How an evaluation run is read

Four steps, and the order matters.

1. **Find the bar.** [`docs/BAR-SHEET.md`](docs/BAR-SHEET.md) §2 lists B1–B8 with each
   instrument's population, its bar, its baseline and its status. Only a named, public instrument
   decides anything.
2. **Read the number with its parse rate.** Every accuracy here is published with its unparseable
   rate on the same row. A reader who sees only the headline will draw the wrong conclusion — this
   project has already demonstrated that in both directions.
3. **Follow the number to its receipt.** Each printed figure is re-derived from the artefact it
   names by a check script in [`tools/`](tools/). A figure whose evidence does not hold fails the
   check rather than standing.
4. **Read the status column honestly.** *Measured*, *not measured*, *report-only* and *failing* are
   different words and this programme keeps them apart. A missing measurement is never an assumed
   pass.

---

## What is in this repository

| | |
|---|---|
| [`docs/`](docs/) | the methodology and the governance: the product definition, the bar sheet, the product contract, the plan ledger, and the three decision registers (owner, supervisor, and the v3 run) |
| [`results/`](results/) | the measurements and their receipts — every public-benchmark result, every arm |
| [`qualification/`](qualification/) | the corpus qualification and the gate discipline: the Data Gate receipt, the corpus/mixture lineage receipts, the decontamination reports, the held-out leak trace |
| [`tools/`](tools/) | the eval tooling: the public-benchmark runners, the bar-sheet generator, the release-rule checks, the decontamination instruments |
| [`EVALUATION.md`](EVALUATION.md) | the repository's boundary charter — the options considered, what may and may not be in here, and what a future clean arm needs to become a shippable model repository |
| [`LAUNCH-PACKET.md`](LAUNCH-PACKET.md) | **internal** — current state, exclusions and their reasons, readiness, and the decisions only the owner can take |
| [`INVENTORY.md`](INVENTORY.md) | every imported file with its source path and hash, and every category deliberately left out, with the reason |
| `verify_repo.py` | the mechanical boundary check: internal identifiers, credentials of any shape, and row-level data files that are not on the published-benchmark allow-list |

**No weights, no adapters, no training data, no held-out data, no credentials, no internal hosts
or paths.** The boundary is enforced by a script, not by good intentions.

---

## Sources

Published numbers are cited to the authors' own pages; first-party numbers are cited to the
evaluation record in this repository.

- **CyberSecQwen-4B** — model card and published CTI-Bench numbers:
  [huggingface.co/athena129/CyberSecQwen-4B](https://huggingface.co/athena129/CyberSecQwen-4B)
  (CTI-MCQ **0.5868 ± 0.0029**, CTI-RCM **0.6664 ± 0.0023**, 5-trial means at temperature 0.3 under
  the Foundation-Sec-8B protocol, arXiv:2504.21039 §B.3–B.4).
- **Cisco Foundation-Sec-8B-Instruct** — model card and published CTI-Bench numbers:
  [github.com/cisco-open/ai-deep-sast](https://github.com/cisco-open/ai-deep-sast/blob/main/foundation-sec-model/README.md)
  (CTI-MCQA **0.644**, CTI-RCM **0.692**, CTI-VSP **0.802**, 0-shot at temperature 0.3). The base
  model's 5-shot figures — CTI-MCQA 67.39, CTI-RCM 75.26 — are not in the table because a 5-shot
  protocol for a base model is not comparable with a 0-shot protocol for an instruction-tuned one.
- **CTI-Bench** — the benchmark itself, its datasets and its metric definitions:
  [github.com/xashru/cti-bench](https://github.com/xashru/cti-bench) (accuracy for CTI-MCQ and
  CTI-RCM, **mean absolute deviation for CTI-VSP**).

---

*Private repository. The model does not ship. The arm of record is a NO-SHIP, the corpus gate is
BLOCKED, and every number above is traceable to a receipt in this repository or to a cited public
source.*
