# CHECKPOINT 04 — CyberGuard v3 (after Codex-Astra cycle 3 and its fixes)

**Date:** 2026-09-30 04:15 CDT
**Trigger:** standing cadence — Codex-Astra review every 3 hours, checkpoint after each review and its fixes.
**Review:** cycle 3, ran 04:06:39 CDT against plan md5 `2b2136d861428f0791a909fc302e3b81` (1,396 lines).
**Verdict: REJECT — 8 Major + 4 Minor.** All twelve addressed (eleven fixed, one accepted-not-fixable).
**Training is live throughout:** launched 02:09 CDT, no interruption from this review.

---

## 1. Training status — unaffected by the review

| | |
|---|---|
| state | **RUNNING** on spark-40ee, main pid 1189450 |
| progress | **step 430 / 8783**, GPU **95 %**, ≈15–17 s/step |
| measured ETA | ≈**41 h** (≈19:00 CDT 2026-09-30), inside the 3300-min ceiling with ≈14 h margin |
| log | `spark-40ee:~/cyberguard/logs/train-cyberguard-lora-v3.log` |
| monitor | `logs/monitor-v3.log` — 15-min polls, `alive=yes` every time |

Cycle 3 reviewed *claims*, not the recipe; the recipe and the running run are unchanged.

## 2. What cycle 3 confirmed

Mixture arithmetic (127,767 SFT / 140,545 no-trail / 147,545 conditional / 4.744315 % / 6.495645 %),
**all nine cited SHA-256 values**, the refusal regression checks (8 fixtures + 12 historical replies),
and that excluding the failed trail block is correct.

## 3. What it refuted — including claims I made myself

**Four findings were reproduced independently here before being accepted.** The important pattern:
rev 8's "eval-chain readiness audit" claimed no gate was specified-but-unimplemented. **That was
wrong**, and it is retracted:

| gate | plan specifies | cited code actually does |
|---|---|---|
| G-A / G-A2 | Newcombe paired intervals, answer indicators | percentile bootstrap; G-A2 inputs are **refusals** — cycle 3 executed it and got FAIL for 60 *improved* answers / PASS for 60 *lost* |
| §8.6 held-out | 610 references (CyberMetric-500 + SecQA) | `eval_cyberguard.load_held_out()` builds the old **500-row Trendyol** split |
| G-B | ROC-AUC ranking score | `(TPR+TNR)/2` from one hard-label confusion matrix |
| G-D | character-offset, typed span F1 | `ioc_score` is set-based normalized-IOC F1 — no offsets, no types |

I had also written that G-D's "scorer is present, only the reference is missing". **Also wrong** — the
span scorer is absent too. My round-16/17 conclusions are corrected in §12 and §8.9 rather than
quietly edited.

## 4. The twelve dispositions (rev 9)

| # | sev | finding | disposition |
|---|---|---|---|
| 1 | Major | G-A/G-A2 don't implement the v3 contract (bootstrap ≠ Newcombe; refusals ≠ answers) | **retracted** readiness claim; listed as specified-path-not-implemented |
| 2 | Major | §8.6 evaluator measures the wrong population (500 Trendyol ≠ 610 benchmarks) | **retracted** |
| 3 | Major | G-D's "scorer present" claim false (set-based, no offsets/types) | **corrected** — bundle *and* scorer outstanding |
| 4 | Major | G-B hard-label AUC ≠ specified ranking ROC-AUC | **retracted** |
| 5 | Major | G-C missing-response rule left the emitted-ID verdict undefined | **fixed** — 600 generations = 2 samples × 300 rows; unit = emitted ID; zero-ID contributions; missing-response imputation; ≥300 support floor; receipt fields |
| 6 | Major | A7 calibration claim contradicted its evidence (0 of 48 labels filled) | **fixed** — both sub-metrics marked UNCALIBRATED/INVALID; *verified examples* distinguished from a *calibrated 5.5 % population estimate*; block stays excluded |
| 7 | Major | §5.3 receipt measures the pre-augmentation mixture, not the configured consumer | **fixed** — applicability limit stated; "S1–S4 pass" withdrawn as a claim about trained sequences; required evidence named |
| 8 | Major | launcher reuse unestablished (`run-v2-arm.sh` hardcodes v2 paths) | **resolved with evidence** — the run uses `run-v3-arm.sh` with a mixture-identity gate; live log line `ARM MODE: … sha256=75b5099c568313f2 rows=140545` is direct proof |
| 9 | Minor | "7,000 admitted" asserted despite failed A7 | **fixed** — "7,000 generated, block NOT admitted (A7 FAIL)" |
| 10 | Minor | host evidence over-claimed (00:37 loads; base "identity") | **fixed** — timestamps aligned; base identity asserted by path/filename set only; pre-flight superseded by the live run |
| 11 | Minor | projection presented as a lower bound | **fixed** — labelled conditional with its transfer assumption; "lower bound"/"48 %" withdrawn; **measured** rate now reported (≈41 h) |
| 12 | Minor | prior-revision comparison unverifiable (no backup with rev-7's md5) | **accepted, not fixable** — narrowed claim; **process fix:** every revision now writes a `.revN-bak` snapshot (rev 9 → `docs/PLAN-V3.md.rev9-bak`) so the next cycle can diff exact text |

## 5. Consequences for the ship path

The review changes **nothing about the running training** — the recipe is Arm B verbatim and the
launch evidence is on record. What it changes is that **the eval chain is not ready to produce §8
verdicts**: for four gates the cited evaluators measure different intervals, indicators, populations
or metrics, and G-D additionally lacks both its reference and its span scorer. Post-training, before
any ship verdict, those evaluators must be implemented or replaced and verified.

Also unchanged and still open: **the two-host instruction** (impossible without a recipe change —
`train_cyberguard.py` has no distributed support; details in CHECKPOINT-03), and **Option B** for the
trail block.

## 6. Next

Monitor to completion (≈41 h). Then: harvest the training receipt, implement/verify the four eval
evaluators above, close G-D's two gaps, and run the §8 chain. No ship verdict without those.
