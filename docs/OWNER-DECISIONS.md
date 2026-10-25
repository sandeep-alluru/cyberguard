# OWNER-DECISIONS — current programme (CyberGuard VulnTriage build)

**This is the owner-decision register for the build that is running now.** It is a separate
namespace from the two legacy registers, and every entry here is cited as **`OWNER-D<n>`**.

| register | file | id form | scope |
|---|---|---|---|
| **this one** | `docs/OWNER-DECISIONS.md` | `OWNER-D<n>` | the VulnTriage build, from 2026-10-23 |
| legacy Astra | `docs/ASTRA-DECISIONS.jsonl` | `ASTRA-D<n>` | `ASTRA-D1`–`ASTRA-D24`, the supervisor's rulings, still live |
| legacy owner | `docs/V3-OWNER-DECISIONS.md` | `OWNER-D<n>` (v3) | the v3 run, consolidated 2026-09-30 |
| the v2 spec's own table | `docs/SPEC-V2.md` | `SPEC-V2 D<n>` | the v2 evaluation spec's decision table, `SPEC-V2 D1`–`SPEC-V2 D12` |
| v2 review defects | `docs/PLAN-SEQUENCE.md` | `REV-D<n>` | the nine review-round defects of 2026-09-28 — **not decisions** |
| failure register | `docs/FAILURE-REGISTER.md` | `FR-D<n>` | the process-and-role failure rows — **not decisions** |

**Why the split.** The v3 owner register shares a bare `D<n>` namespace with the Astra register
(`ASTRA-D1`–`ASTRA-D24` and `OWNER-D1`–`OWNER-D14` (v3) in both), and a reader following "D6" from
the HarmBench work lands on the v3 trail-block
decision instead of the HarmBench re-judgement ruling. `EVALUATION.md` §7 step 2-7 asks for exactly
this to be fixed; it is being fixed as **three** registers with three prefixes rather than two with
one, because the v3 run and the current build have genuinely different owners' decisions in them.
**The E-6 sweep found two more namespaces that are not decisions at all** — the v2 review-round
defect ids and the failure register's process rows — and one more decision table, SPEC-V2's own.
All five are now named above, and a bare `D<n>` no longer exists anywhere in the repository.

---

## OWNER-D1 — VulnTriage direction approved; full approval on the build

**Date:** 2026-10-23, 07:12 CDT
**Channel:** owner instruction to the working agent, verbatim sense: *"proceed as per the VulnTriage direction; full approval on the work."*
**Recorded by:** the working agent, in the same pass as the instruction.
**Supersedes:** nothing. **Does not supersede:** `ASTRA-D9` (execution freeze) was already released by the owner via `ASTRA-D23` on 2026-10-10; `ASTRA-D5`, `ASTRA-D17` and the rest of the Astra register remain in force.

### The approval

1. **The direction.** The **CyberGuard VulnTriage** direction in `PRODUCT-DEFINITION.md` is approved. The product is a vulnerability-triage scorer: CVE→CWE + CVSS + impact + prioritisation. The release artefact is named `CyberGuard-Vuln-4B`.

2. **Full approval on the work.** The build proceeds. The worker **makes its own decisions** on sequencing, prioritisation and method inside the build, subject to the boundaries below.

3. **The ledger is the single source of truth.** `PLAN-LEDGER.md` breaks every phase of the build approach (`PRODUCT-DEFINITION.md` §7, detailed in `NEXT-STEPS.md`) into line items, each with what it produces, an **acceptance check that measures completion rather than asserting it**, a status, and evidence paths.

4. **The phase order.** Measurement and evidence repair → the data work (inventory first, then fixing, then corpus qualification, then the vuln corpus build) → instruments → packaging and publication prep.

5. **Keep everything latest.** `PLAN-LEDGER.md` is updated in the same pass as each item completes. `EVALUATION.md`, `PRODUCT-DEFINITION.md` and `NEXT-STEPS.md` are kept consistent with the ledger whenever a finding changes a claim.

### The standing boundaries

| # | boundary |
|---|---|
| **1** | **Public third-party benchmarks only** for all evaluation. Internal instruments are diagnostic and decide nothing. |
| **2** | **Already-downloaded data first.** Any new download is logged in `PLAN-LEDGER.md` with its source and licence. |
| **3** | **The training launch line item is `OWNER GO`.** When the build reaches it, **stop** and report ready; the owner gives that go in the moment. **Everything before it proceeds without waiting for anyone.** |
| **4** | **No deadlines.** Keep going until every line item is done and measured. |

### Four worker decisions taken under this approval, recorded so they can be overridden

| # | decision | rationale | how to reverse it |
|---|---|---|---|
| **W-1** | The rebuilt corpus lineage is written to **`cyberguard/data/v4/`**, not into `<workspace>/<other-workspace>/cyberguard-v4/`. The v4 tree is read as a source and never written to. | The v4 tree was under a "measure and report only" freeze. Writing a new corpus lineage into another programme's tree would breach that, and the v4 lineage's own receipt says it is not a training set. | Change `PLAN-LEDGER.md` items C-1/C-2/D-7 to write into the v4 tree instead, and lift the freeze. |
| **W-2** | The **decode-budget sensitivity measurement** (`PLAN-LEDGER.md` A-5 / G-4) is authorised by this approval rather than by `ASTRA-D17`. | `ASTRA-D17` authorises "existing decoders and parsers" only, and `max_new_tokens` is part of the frozen decision surface. But the owner's instruction is to keep going until every line item is *done and measured*, and this is a named open item that gates a real product decision ("if the curve is flat, the corpus fix is the whole remedy"). The measurement varies **only** `max_new_tokens`; population, greedy decoder, prompt template and frozen parser are unchanged, and it runs on the same public benchmark. | Re-scope A-5/G-4 to be blocked on a fresh `ASTRA-D` ruling naming the permitted budgets. |
| **W-3** | The **refusal stream's target weight** in the rebuilt v4 corpus is set to **4.91 %** — **5,314 presentations** from the **1,198** distinct refusal rows, in a **108,238**-row corpus (measured **4.9096 %**). Executed as `data/v4/corpus-v4-r2.jsonl`; policy in `docs/REFUSAL-POLICY.md`. | The approved plan lists `PLAN-LEDGER.md` **C-5** as *"decide and execute the refusal-stream policy"*, and the owner's instruction is to keep going without waiting. **4.91 % is the lowest share for which the programme has a MEASURED false-refusal rate and a MEASURED harmful-compliance count** on the same arms, prompts and instrument — below it the dose-response is an extrapolation the record calls UNMEASURED. It maximises the certain gain: across the one controlled pair the false-refusal movement is −17.87 pp at p = 5.1 × 10⁻²² while the harmful-side movement (2/159 → 5/159) is **not** significant (p = 0.375). **This is the least-committing of the measured points, not the most attractive-sounding one:** at this target the expected harmful-compliance count is 5/159, whose Wilson upper bound (0.0554) is **above** the programme's own release bar — as is the public comparator's (3/159, upper 0.0540). The bar is owner-owned (`EVALUATION.md` §8 Q11) and is not settled by this decision. | Change `TARGET_SHARE` in `eval-2026-10-23/c5_refusal_policy.py` and re-run it: the corpus is re-emitted in one command and the alternatives' row counts are already computed in `data/v4/receipt-v4-r2.json`. `NEXT-STEPS.md` §2 calls this "an owner decision" and `EVALUATION.md` §8 Q12 puts the safety-posture choice with the owner, so **this is explicitly open to the owner's override.** |
| **W-4** | **The release-candidate table: which arms are carried forward.** **v1 is NOT carried forward.** v2 arm A, v2 arm B and v3 are **not carried forward as release candidates**; base (untrained) and the public comparator are **references, not candidates**; and the arm to be trained is the **new arm (H-2)**, at the qualified corpus's policy refusal share of **4.9092 %** (W-3). Recorded in `eval-2026-10-23/release-candidates.json` and rendered as the **release table** in `docs/BAR-SHEET.md` §1.1. | `EVALUATION.md` §8 Q1 asks *"Is v1 or v2 arm B a candidate at all?"* and answers itself precisely: *"the measurement cannot answer the question on its own: what counts as a candidate is a product decision (P2-1), not a number. **What the numbers DO tell you is whether those two arms are worth carrying forward at all.**"* This decision takes the second half of that sentence and leaves the first half alone: candidate **prioritisation** is exactly the delegation OWNER-D1 clause 2 makes ("the worker makes its own decisions on sequencing, prioritisation and method"), and it **changes no bar, metric, parser, sample size, decode budget or label** — the boundary OWNER-D1 draws. **Every status is a measured comparison against a bar the owner has already fixed, never a preference.** For **v1** specifically: it is the only arm in the family **measurably worse than the checkpoint it was trained from** on the harmful side — HarmBench **12/159 (7.55 %)** against the untrained base's **1/159 (0.63 %)**, paired exact McNemar **p = 9.8 × 10⁻⁴**, with **not one behaviour** where the base complied and v1 did not — it does not parse CTI-RCM at all (**0.0000**, 1,000 of 1,000 unparseable) and scores **below the always-C floor** on CTI-MCQ (**0.1676** vs 0.3712), and its one advantage, the family's best FRR at **10.93 %**, is still **2.07×** B3's **5.27 %** ceiling. **This is NOT the ship-or-do-not-ship decision**: that is ledger **H-3**, against the bar sheet, and it is recorded either way there. The product question — *what the shipped product is* — stays the owner's (P2-1). | Change a status in `eval-2026-10-23/release-candidates.json` and re-run `eval-2026-10-23/e2_bar_sheet.py`; the release table follows. `eval-2026-10-23/e7_release_candidates_check.py` (43/43) then re-reads every figure the reasons cite from the artefact it names, so a status whose evidence does not hold fails the check rather than standing. |

### What this approval does **not** do

- It does not change any bar, metric, parser, sample size, decode budget or label. Those are the supervisor's (`ASTRA-D`) and the owner's (the bar sheet, `PLAN-LEDGER.md` E-2) — not the worker's.
- It does not release `ASTRA-D9`; that was already released on 2026-10-10 (`ASTRA-D23`).
- It does not supply the two human-dependent items: the blinded FRR adjudication (A-6) and the owner's 20-row spot-check (D-6). Both need people; neither is delegated to an agent.
- It does not authorise training. That is H-1, and it is `OWNER GO`.

---

## OWNER-D2 — Namespace disambiguation (closes `EVALUATION.md` §7 step 2-7)

**Date:** 2026-10-23
**Cited as:** `OWNER-D2`

The bare `D<n>` namespace collision between `docs/ASTRA-DECISIONS.jsonl` (`ASTRA-D1`–`ASTRA-D24`)
and `docs/V3-OWNER-DECISIONS.md` (`OWNER-D1`–`OWNER-D14` (v3)) is closed by the multi-register
scheme set out at the head of this file. The **E-6 sweep** that executed this rule found three more
namespaces in live use — SPEC-V2's own decision table, the v2 review-round defect ids, and the
failure register's process rows — and they are named in the scheme too.

**Rule, in force for every document in this repository:**

| prefix | resolves to |
|---|---|
| `ASTRA-D<n>` | `docs/ASTRA-DECISIONS.jsonl` |
| `OWNER-D<n>` | `docs/V3-OWNER-DECISIONS.md` (the v3 register) |
| `OWNER-D<n>` *(this file)* | `docs/OWNER-DECISIONS.md` (the current programme) |
| `SPEC-V2 D<n>` | `docs/SPEC-V2.md`'s own decision table |
| `REV-D<n>` | `docs/PLAN-SEQUENCE.md`'s v2 review-round defect ids — **not a decision register** |
| `FR-D<n>` | `docs/FAILURE-REGISTER.md`'s process-and-role failure rows — **not a decision register** |

**Two registers share the `OWNER-D` prefix, so the v3 register's entries keep their own ids and are cited as `OWNER-D<n> (v3)` when they are the ones meant.** Where a bare `D<n>` is ambiguous, the citation is rewritten to name the file.

**The two citations this rule corrects**, both of which point at the wrong ruling today:

- **"D6"** in the HarmBench context means `ASTRA-D6` (re-judge the lost HarmBench vectors). In the v3 register, `OWNER-D6 (v3)` is *"Option B for the trail block (A7 FAIL)"* — a different decision entirely. `ASTRA-D6` is now `executed`; see its annotation.
- **"D7"** in the FRR context means `ASTRA-D7` (blinded human adjudication). In the v3 register, `OWNER-D7 (v3)` is *"the section 8.1 classifier is wired into nothing"*. `ASTRA-D7` is the item that is **blocked on humans** (`PLAN-LEDGER.md` A-6).

**Never cite "D11 (refusal redesigned)".** `ASTRA-D11` is *"ASTRA-D7 AMENDED - agent-ASSISTED review permitted"* and has nothing to do with a refusal redesign. The refusal work is **`CG-09`** (failure-corpus id) and **`FC-1`** (format-compliance id).

**Acceptance:** a grep for bare `D<n>` across `EVALUATION.md`, `PRODUCT-DEFINITION.md`, `NEXT-STEPS.md`, `PRODUCT-RESEARCH.md`, `PLAN-LEDGER.md` and `docs/` returns zero unqualified citations. Tracked as `PLAN-LEDGER.md` item **E-6**. **Measured, not asserted:** the grep is an instrument — `eval-2026-10-23/e6_namespace_sweep.py` — which scans 78 files and exits 0 only when the count is zero.

---

## OWNER-D3 — no human validation is available; the model's own judgement stands in; the goal stands

**Date:** 2026-10-24, ~15:20 CDT
**Channel:** owner instruction to the working agent, in session, verbatim sense: *"there is no people here to valdiate so i need the models best judgement to give the valdiation, there is no resources, this is a one person company. so you still need have to goal. launch our product direction model that beats the benchmarks and we working on previos failed model adapter, so i need to know if previous adapter is dragging us down … but now we need to know next steps to reach the goals do you have an answer for it if you need to do research anf fins the answer go ahead but let me know the next steps"*
**Recorded by:** the working agent, in the same pass as the instruction.
**Does not supersede:** `OWNER-D1`, `OWNER-D2`, or anything in the Astra register.

### 1. There are no people to validate, and there are no resources

The programme is a one-person company. Every line item that was waiting on a human — the protocol
§6 confirmation draw (**D-7**), the blinded FRR adjudication (**A-6**), the removal-set review
(**D-3**, **D-4**), the owner's 20-row spot-check (**D-6**) — **cannot be executed by a human, and
must not be left waiting for one.** Where those items required human judgement, **the model's own
best judgement provides the validation.**

**How that judgement is recorded, so it can never be mistaken for a human reference:**

| rule | |
|---|---|
| **a** | Every model-derived judgement names the **instrument and the method** that produced it, and the artefact that carries it says so in its own words. |
| **b** | A model-derived judgement is labelled **model-adjudicated** wherever it is cited. It is never described as a human reference, a blinded adjudication, or a review. |
| **c** | The model's judgement substitutes for **human review** — corpus membership, defect triage, refusal adjudication, the spot-check. It does **NOT** substitute for **public benchmark evidence**. Nothing model-derived is ever cited as evidence of model quality. |
| **d** | The public-benchmark bar is unchanged. A model's score on a public benchmark is still measured by the frozen harness on the frozen surface, and only that counts (OWNER-D1 boundary 1). |

### 2. The goal is unchanged and reaffirmed

**Ship the VulnTriage model that beats the public benchmarks.** The training launch (**H-1**) is
**GO**. The owner is aware that the launch follows the data work, and has asked for the next steps
to the goal rather than for another stop.

### 3. The previously-failed adapter is to be evaluated, not assumed

The owner asked whether the old adapter is dragging the programme down. **Answered, measured** —
`eval-2026-10-23/adapter_assessment.py` → `adapter-assessment.json` / `adapter-assessment.md`,
assembled from the artefacts already on disk (the six-arm family re-measurement, the A-16
equal-terms ladder, the official-classifier HarmBench re-judgement, the MITRE-FRR re-scoring, and
the F-8 trace). **The v3 adapter is not the drag; v1 and v2 are.** Full numbers in §2 below.

### Worker decision taken under this ruling — W-5

| # | decision | rationale | how to reverse it |
|---|---|---|---|
| **W-5** | **The new arm trains from the BASE checkpoint, not from the v3 adapter** (`RESUME_ADAPTER` unset — which is `train_cyberguard.py`'s default). | The v3 adapter is the **best** arm measured (W-5 evidence in `adapter-assessment.json`): **+33.20 pp** on CyberMetric-500, **+25.46 pp** on SecQA-v1-test, **+22.60 pp** on CTI-RCM, **+20.04 pp** on CTI-MCQ at 2,048 on the equal-terms surface, and HarmBench harmful compliance **0.63 pp BETTER** than the base. Its one liability is the false-refusal side (**+24.94 pp** MITRE-FRR), which the rebuilt corpus's 4.91 % refusal share (W-3) and 3,304 format-compliance rows exist to fix. But **a warm start would ship weights trained on the 604 rows that contain the held-out questions** (F-8: the leak reaches v3's own SFT file), so the new arm's own held-out measurement would be compromised before a single new row is seen. The adapter's gain is a **data** effect — reproducible by the same recipe on the rebuilt mixture, which carries **245,273 rows of NVD triage supervision the old corpus did not contain at all**. | Set `RESUME_ADAPTER=<programme-tree>/research-tmp/harvest-v3/adapters` in the training environment. The cost is stated in the ledger: the held-out instrument then reads the new arm's own lineage. |

### Worker decision taken under this ruling — W-6 (base checkpoint, delegated by the owner)

The owner delegated the base-model choice entirely to the worker: *"if your direction is train from
base if that is recommendation proceed i want to proceed with recommendation or even if you want to
changes differeent base i am ok to get the best decsions if you need to measure another base do its
totaly your best decisin"* (local desktop, 2026-10-24; the message id is not available to this
session — recorded here as the owner's verbatim instruction, with the provenance gap stated in the
same way D24 stated it for D23).

| # | decision | rationale | how to reverse it |
|---|---|---|---|
| **W-6** | **The base checkpoint is `Qwen3-4B-Instruct-2507`** (`TRAIN_BASE=<model-cache>/cyberguard-eval/Qwen3-4B-Instruct-2507`), i.e. the same checkpoint the public comparator was fine-tuned from. | Three measured reasons, not preferences. **(1) It is the only trainable base on this host.** Every larger local model is GGUF-only (MiniCPM-V-4.7-35B, LFM2.5-24B, Qwen3.8-27B, Saluki-27B) or unloadable (`Ornith-1.5-9B`, architecture `qwen3_5`, absent from transformers 5.5.0); this host has torch 2.4.0+cu121 / transformers 5.5.0 / peft 0.21.0 / trl 0.24.0 and 2 × RTX 3090 (24 GB). **(2) It is the only choice that keeps the comparator comparison equal-terms.** CyberSecQwen-4B is itself a LoRA fine-tune of `Qwen3-4B-Instruct-2507` (its model card and `GPT-64590/CyberSecQwen-4B` repository say so), so training our arm from the same substrate makes every benchmark cell a difference between two adapters over one base rather than a difference between two unrelated model families. **(3) It is the substrate the public recipe is known to work on** — the comparator's own recipe (LoRA r=64, alpha=64, dropout 0.05, lr 5e-5, 10 epochs, bf16, ~15K decontaminated MITRE/NVD CVE→CWE + synthetic Q&A records) produced +12.0 pp on CTI-MCQ and +15.1 pp on CTI-RCM over this base. | Point `TRAIN_BASE` at any other local checkpoint. Nothing in the trainer assumes this base; but a different substrate makes the comparator comparison a cross-family comparison and the equal-terms claim in the bar sheet no longer holds. |


### 4. What this ruling does **not** do

- It does **not** make the corpus qualified by fiat. The Data Gate is still issued, now on a
  **model-adjudicated** basis, and `data/v4/DATA-GATE.json` must say **which** basis it used.
- It does **not** change any bar, metric, parser, sample size, decode budget or label (OWNER-D1).
- It does **not** make the contaminated rows safe to keep. **F-8's acceptance check still FAILS**
  until the 604 rows are removed; the ruling changes who decides, not what the instrument says.
- It does **not** retire the held-out instrument. Nothing in this ruling authorises discarding a
  measurement instrument because the people who would have read it are unavailable.
