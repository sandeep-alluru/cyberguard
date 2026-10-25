# OUTPUT-CONTRACT — what the service emits, how it is parsed, and what that buys

**Date:** 2026-10-23 · **Programme item:** G-3 (step 8b) · **Status:** the contract
is **shipped**; mechanism (a) is measured and mechanism (b)'s parse stage is measured.

> **The strict headline is reported alongside the served configuration, never instead of it.**
> Every table in this document prints the strict number and the served number in the same row.
> A served number that replaced the strict one would be a claim the release rule does not support
> (`docs/BAR-SHEET.md` §0, clause 2: a public benchmark decides only when a bar names it, and the
> bar's comparator baseline must be a figure measured on the same frozen surface).

---

## 1. What this document is

Two output contracts exist in this programme, and they are not the same thing.

| contract | what it governs | where it is specified |
|---|---|---|
| **the product's** | what CyberGuard emits for a vulnerability: six keys, exactly six, `TRIAGE-1` | `docs/PRODUCT-CONTRACT.md` §4 |
| **the evaluation surfaces'** | what the model emits on the four public benchmarks, and how the harness reads it | **this document** |

The product's contract is the one the release is judged on. The evaluation surfaces' contract
exists because **the programme's published numbers were produced under a parsing rule, and that
rule is now measured against the alternative a service could ship** — the scope set for step 8b:
*"a serving-template change and a measurement"* with *"no training, no new data"*.

---

## 2. The evaluation surfaces' contract, as it stands

The rules below are **the frozen runner's own** (`pubbench/run_pubbench.py`), not this project's
preference. They are imported, never re-implemented.

| surface | the rule | the parse |
|---|---|---|
| **CyberMetric-500**, **SecQA-v1-test** | the **entire trimmed response** must be exactly one of `A`/`B`/`C`/`D` | `parse_whole_mcq` |
| **CTI-MCQ** | the **last nonempty line** must be exactly one of `A`/`B`/`C`/`D` | `parse_last_line(gen, ^[ABCD]$)` |
| **CTI-RCM** | the **last nonempty line** must be `CWE-<digits>` | `parse_last_line(gen, ^CWE-[0-9]{1,5}$)` |

**The CTI-RCM surface's instruction does not describe CTI-RCM.** All four surfaces are rendered
with one template — *"Answer the following multiple choice question. Reply with only the letter
of the correct answer: A, B, C, or D."* — while CTI-RCM asks for a **CWE identifier**, not a
letter. **A model that obeyed the instruction perfectly would still fail the CTI-RCM parse.**
That is not a hypothesis: it is what the surface is, and mechanism (a) below measures what
happens when the instruction is made to match the surface.

---

## 3. The served configuration — the three-stage ladder

It is a **parse-and-retry wrapper**:

1. **Strict.** Parse with the frozen rule above. If it yields an answer, **use it**.
2. **Fallback.** If it does not, apply the project's own permissive extractor —
   `eval-2026-10-23/output_contract_recovery_ceiling.py::permissive`, which looks for the answer
   *anywhere* in the response. **The fallback's pick is a guess**, and §5 reports how often it is
   right.
3. **Retry.** If neither yields an answer, re-prompt under a constrained instruction. **The size
   of this set is measured in §4**; it is the only stage that needs new generation.

**Stage 2 covers the CTI surfaces only.** `permissive()` returns `None` for CyberMetric-500 and
SecQA-v1-test, because their contract is *whole-response* rather than *last-line*, and no
permissive whole-response extractor exists in this project. **So on the two knowledge surfaces
the fallback buys exactly nothing, and every unparsed row goes to the retry stage.** That
asymmetry is the single most important thing in this document and it is easy to miss.

---

## 4. The measured delta — mechanism (b), parse stage

**Measured on the whole frozen surface: all six arms, all four public benchmarks, from the
generations the project already has. No GPU, no new generation, no new data.**

Instrument: `eval-2026-10-23/g3_output_contract_measurement.py` →
`eval-2026-10-23/g3-output-contract-measurement.json` (**3/3 PASS**).

**The instrument is checked against the record**: all **24** arm × benchmark cells reproduce
the evaluation record §5.3.1's published unparseable counts **exactly**, and the strict accuracies
reproduce the published accuracies exactly. The measurement is of the same surface the published
numbers were produced on.

| arm | benchmark | strict parse | served parse | strict acc | **served acc** | Δ acc | retry set |
|---|---|---:|---:|---:|---:|---:|---:|
| base | CTI-MCQ | 99.76 % | 100.00 % | 0.4444 | 0.4444 | +0.00 pp | 0 |
| base | CTI-RCM | 81.50 % | 100.00 % | 0.4100 | **0.5200** | **+11.00 pp** | 0 |
| v1 | CTI-MCQ | 22.52 % | 99.60 % | 0.1676 | **0.5152** | **+34.76 pp** | 10 |
| v1 | CTI-RCM | 0.00 % | 99.80 % | 0.0000 | **0.4190** | **+41.90 pp** | 2 |
| v2 arm A | CTI-MCQ | 15.08 % | 98.36 % | 0.1124 | **0.6344** | **+52.20 pp** | 41 |
| v2 arm A | CTI-RCM | 53.40 % | 75.10 % | 0.0490 | 0.0760 | +2.70 pp | 249 |
| v2 arm B | CTI-MCQ | 59.56 % | 96.88 % | 0.4172 | **0.6128** | **+19.56 pp** | 78 |
| v2 arm B | CTI-RCM | 49.10 % | 83.80 % | 0.1270 | 0.1770 | +5.00 pp | 162 |
| v3 | CTI-MCQ | 58.72 % | 95.36 % | 0.4648 | 0.5312 | +6.64 pp | 116 |
| v3 | CTI-RCM | 80.30 % | 100.00 % | 0.6360 | **0.7150** | **+7.90 pp** | 0 |
| comparator | CTI-MCQ | 97.00 % | 99.72 % | 0.5764 | 0.5924 | +1.60 pp | 7 |
| comparator | CTI-RCM | 100.00 % | 100.00 % | 0.6780 | 0.6780 | +0.00 pp | 0 |

**On the two knowledge surfaces the delta is +0.00 pp in all twelve cells** — base, v1, v2 arm A,
v2 arm B, v3 and comparator, on CyberMetric-500 and SecQA-v1-test — **because the fallback does
not apply there.** The retry sets on those surfaces are large: **488** rows for v2 arm A on
CyberMetric-500, **395** for v2 arm B, **239** for the comparator.

### 4.1 The one number that touches a bar

**B1 is a decision instrument: CTI-RCM > 0.6780**, against this project's own re-measurement of
the comparator on the same frozen surface. The comparator scores **0.6780** on CTI-RCM with
**0 of 1,000** unparseable, so **its served score is also 0.6780** — the comparator parses
everything, so the two surfaces agree for it.

- **Strict surface: v3 = 0.6360 — below the bar.**
- **Served surface: v3 = 0.7150 — above the bar.**

**And the clearing is made of guesses.** Of v3's 197 rescued CTI-RCM rows, the fallback picks
the right CWE on **79** — an accuracy of **0.4010 on the rescued rows**. So **7.90 pp of v3's
served advantage over the strict surface is fallback guessing**, and the 0.7150 is 0.6360 of
real, contract-conforming answers plus 0.0790 of permissive picks.

**This is stated here rather than smoothed over because it is the decision's substance.** A bar
met by a fallback whose picks are right 40 % of the time is a different fact from a bar met by
the model's own answers. **The strict surface remains the headline**; the served surface is
reported beside it; and **whether a served configuration is what a bar is measured against is an
open product question, not this document's.**

---

## 5. What the fallback costs, stated

The fallback is not free. It converts a *format* failure into a *guess*, and the guesses are
right at very different rates depending on the arm:

| arm | benchmark | rows rescued | of those, correct | accuracy on rescued rows |
|---|---|---:|---:|---:|
| base | CTI-RCM | 185 | 110 | 0.5946 |
| v1 | CTI-MCQ | 1,927 | 869 | 0.4510 |
| v1 | CTI-RCM | 998 | 419 | 0.4198 |
| v2 arm A | CTI-MCQ | 2,082 | 1,305 | 0.6268 |
| v2 arm A | CTI-RCM | 217 | 27 | 0.1244 |
| v2 arm B | CTI-MCQ | 933 | 489 | 0.5241 |
| v2 arm B | CTI-RCM | 347 | 50 | 0.1441 |
| v3 | CTI-MCQ | 916 | 166 | 0.1812 |
| v3 | CTI-RCM | 197 | 79 | 0.4010 |
| comparator | CTI-MCQ | 68 | 40 | 0.5882 |

**The range is 0.12 to 0.63.** The permissive extractor takes the **first** match anywhere in the
response, so on a response that discusses several candidates it can pick the wrong one. **A
fallback that rescues 2,082 rows at 0.63 accuracy and another that rescues 217 at 0.12 are not
the same instrument, and the served score alone does not show that.**

**This is why mechanism (a) matters.** A constrained instruction puts the answer *where the
contract wants it*, so it is an answer rather than a guess. The fallback is the cheap mitigation
and the constrained instruction is the honest one — and the programme should be able to say which
one it is shipping.

---

## 6. Mechanism (a) — the constrained last-line instruction

**What it is.** A serving-template change: the instruction is made to describe the surface the
model is actually on, instead of one multiple-choice template for four surfaces — two of which
are not multiple choice.

**What it is measured against.** The same frozen surface, the same populations, the same
greedy decoder, the same batch size, the same parse rules. **Only the instruction changes.**

Its measurement is a separate run and its result is reported in
`eval-2026-10-23/g3-constrained-instruction.json`.

---

## 7. What this document does **not** settle

- **It does not decide the release.** The release is programme item **H-3**, and a bar met is one
  condition of one.
- **It does not say a served configuration is what a bar should be measured against.** That is an
  open product question. The strict surface is the headline and stays the headline.
- **It does not claim the fallback's rescued answers are knowledge.** They are picks, and §5
  reports how good the picks are.
- **It does not cover the knowledge surfaces' retry stage.** The retry set is measured
  (§4); the retry itself needs generation, and the constrained instruction is the candidate
  mechanism for it.
- **It says nothing about the product's `TRIAGE-1` contract's parse behaviour**, which is a
  separate surface with its own validator (`docs/PRODUCT-CONTRACT.md` §7) and its own measured
  compliance rate (F-6: 245,273 of 245,273).

---

## 8. Change log

| date | change |
|---|---|
| 2026-10-23 | Document created. Mechanism (b)'s parse stage measured on all six arms × four benchmarks (**3/3**), reproducing all 24 published unparseable counts exactly. Mechanism (a) built and measured separately. |
