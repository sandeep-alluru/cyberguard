# Over-engineering audit — CyberGuard v3 (2026-09-30)

**Directive (Sandeep, via Ronin, permanent):** every validation step, gate, check and piece of
machinery must earn its place. Nothing that slows, blocks or taxes the work. Verification stays
harness-level and reusable; per-job gates and watchdogs that burn budget without catching real defects
are out. Applies to the plan **and to my own fixes**.

This is me applying that lens to what I built. I found more over-engineering in my own work than in
the plan.

---

## A. Cut immediately (my machinery)

| item | cost | catches real defects? | verdict |
|---|---|---|---|
| `tools/monitor-v3.sh` — 15-minute ssh poll for 40 h, logging `alive/gpu/progress` | an ssh round-trip every 15 min for ~40 h, and a log that duplicates the trainer's own | **No.** It never caught anything the trainer's log did not already show, and its only failure mode (trainer gone) is visible in the same log. | **CUT** — job killed. Status comes from the trainer's log at checkpoints. |
| 3-hourly Codex-Astra review timer | a full review pass every 3 h against a document that **cannot change the running training** | It caught real defects early (cycles 1–4 were valuable) — but only while the plan was the live artifact being edited. Once training launched, subsequent cycles re-read a frozen document. | **CUT as a timer.** Reviews become **change-triggered**: post-training, pre-eval, and after any material plan edit. Same reviewer, same rigour, no idle burn. |
| `tools/safety_screen.py` | 170 lines | **No — measured 0/11 recall** on the verified unsafe rows. It was already withdrawn as unusable. | **PARK** (deprecated in place; not deleted, deletion of repo files is not permitted here). |
| `tools/safety_screen_model.py` | 160 lines, 350 scorer calls if run | Only relevant to **Option B**, which the owner has not chosen and which is currently excluded anyway. | **PARK** — do not run, do not maintain. Un-park only if Option B is approved. |

## B. Simplify (my fixes, which grew under review pressure)

| item | what it grew into | why that is over-engineered | action |
|---|---|---|---|
| **A7 calibration apparatus** (`a7_calibration.py` 202 lines + a 48-row worksheet + per-sub-metric ≥0.90 agreement + model-name screening) | a calibration *precondition* that blocks A7 until a human labels 48 rows | A7 already caught a real defect (11 hand-verified unsafe rows) and the block is excluded on that basis. The calibration machinery was added to make a *population rate* publishable — a claim nobody needs in order to exclude the block. | **SIMPLIFY**: drop calibration as a blocking requirement. Keep "scorers are uncalibrated, so no population rate is claimed"; keep the hand-verified examples as the operative evidence. |
| **G-D annotation protocol** (`gd_annotation_kit.py` 247 lines: 100 docs × 2 annotators, blind 20-row re-annotation, span-F1 ≥0.90 inter-rater agreement, third-reviewer adjudication, model-name screening) | a full inter-rater reliability study for one secondary capability gate | G-D is already **BLOCKED** (no labels *and* no span scorer). Building a two-annotator protocol before the scorer exists is machinery ahead of need. | **SIMPLIFY**: one annotator + owner spot-check; drop the blind-recheck and adjudication layers unless G-D turns out to be decision-relevant. |
| **Per-metric missing-response taxonomy** | binary imputation + numeric complete-observation + per-metric denominator reconciliation + 5 % cap + the G-C verified/hallucinated/unchecked/zero-ID/imputed taxonomy | The **principle** (a missing value must never improve a verdict) earns its place — cycle 4 proved a real false-PASS path. The enumerated taxonomy does not need to live in the plan; it belongs in the scorer. | **TRIM to the principle** plus one worked rule (missing ⇒ conservative or invalid), and let implementations carry the detail. |
| **§12 disposition log** | ~40 finding-by-finding dispositions, each several lines; the plan is now **1,699 lines** | The log is becoming the artifact. For a document that can no longer change the run, most of this is provenance theatre; the review outputs are already on disk. | **TRIM**: keep dispositions that changed *substance*, compress the rest to a summary table + pointer to `research-tmp/reviews/`. |

## C. Earns its place — explicitly kept

- **`tools/refusal_rule_v3.py`** (§8.4): fixture-verified (8/8) *and* 12/12 on the stored Arm A replies.
  This is the instrument whose absence caused the v2 Arm A NO-SHIP — load-bearing, not decoration.
- **`tools/safety_classifier_v3.py`** (§8.1): 9/9 acceptance, stable across 3 runs. Same reason.
- **Mixture identity gate in `run-v3-arm.sh`** (refuse unless sha256 + row count match) and
  **per-file hash verify in `stage-v3.sh`**: boundary checks, near-zero cost, and they guard a failure
  mode that actually occurred this session (a second writer corrupting the corpus).
- **`supervisor/dedupe.py` / `tools/repair_trails.py`**: removed 57 duplicate records and refilled 97
  format failures — measured value.
- **`tools/validation`-style harness checks** (`validate_trails.py`, `admission_gate.py`): reusable,
  run on demand, and they gate the *artifact* rather than shadowing the run.

## D. Flagged for the owner (plan-level, not mine to cut unilaterally)

1. **Gate count.** §8 now carries G-A, G-A2, G-B, G-C, G-D, G-E, G-F, G-G, G-J, plus §8.5
   merge-equivalence and §8.6 held-out quality — for a **single-arm** ship decision on a 4B LoRA. Some
   were inherited from SPEC-V2/v2 and are reviewed commitments, so I have not removed any. But this is
   the single largest over-engineering risk in the plan: **which of these actually changes the ship
   decision?** A gate that cannot fail usefully is a gate that only costs.
2. **Four evaluators that do not implement their written contracts** (G-A/G-A2 Newcombe, §8.6 610
   benchmarks, G-B ranking AUC, G-D span metric). Building all four to spec is substantial machinery.
   Worth confirming each is decision-relevant before funding it.
3. **The launch-gate clause.** The plan still says training requires a clean review; it was launched
   without one. Either the clause goes (honest) or it stays as a paper commitment (bureaucracy). I
   recorded the override rather than deleting the clause — the owner should decide which it is.

## E. Applied in this revision

- Monitor cut; review cadence changed from timer to change-triggered (see §F).
- Option-B screens parked.
- A7 calibration downgraded from blocker to disclosure.
- G-D protocol simplified to one annotator + owner spot-check.
- Missing-response taxonomy trimmed to its principle.
- §12 log compressed.
- `tools/review_cycle.sh` prompt now **requires the reviewer to flag over-engineered design** in the
  plan and in the fixes, so the same lens keeps applying without me having to remember it.

## F. New review trigger (replaces the timer)

Reviews run on **material change**, not the clock:
- after training completes (harvest + receipt),
- before any eval scoring run,
- after a substantive plan revision (new machinery, new gate, new claim).
A timer that re-reads a frozen document is exactly the "burns budget without catching real defects"
pattern the directive names.
