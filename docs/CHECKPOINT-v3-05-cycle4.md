# CHECKPOINT 05 — CyberGuard v3 (after Codex-Astra cycle 4 and its fixes)

**Date:** 2026-09-30 07:25 CDT
**Trigger:** standing cadence — review every 3 hours, checkpoint after each review and its fixes.
**Review:** cycle 4, ran 07:14 CDT against plan md5 `06f956aa203da2f672352a24ce8053b6` (rev 9, 1,554 lines).
**Verdict: REJECT — 7 Major + 3 Minor.** All ten addressed in **rev 10**.
**Training ran throughout, unaffected:** step ~1202/8783, GPU 96 %.

---

## 1. Training status

| | |
|---|---|
| state | **RUNNING**, main pid 1189450 on spark-40ee |
| progress | **step 1202 / 8783 (14 %)**, GPU 96 %, ≈13.5–16.4 s/step |
| projected finish | ≈33–41 h after 02:09 launch → **late 2026-09-30 to ~19:20 2026-10-01** |
| ceiling | `max_minutes 3300` (55 h) — comfortable margin |
| monitor | `logs/monitor-v3.log`, `alive=yes` on every 15-minute poll |

Cycle 4 reviewed claims and specifications; the recipe and the live run are untouched.

## 2. Cycle 4 found real defects — three of them in *my own* rev-9 fixes

This is the pattern worth naming: rev 9's corrections were themselves partially wrong, and cycle 4
proved it with counterexamples rather than assertions.

1. **G-C imputation could turn FAIL into PASS (Major, confirmed).** I had written "one hallucinated ID
   per missing tuned response" and called it worst case. It is not — a response may emit *many* IDs.
   Cycle 4's counterexample: 1/1,001 → Wilson upper 0.56 % **PASS**, versus a true 100/1,100 → 10.94 %
   **FAIL**, with missingness only 1/600 (under the 5 % cap). Since ID multiplicity is unbounded, no
   finite imputation is conservative → the hallucination component now **requires complete responses**;
   any missing response makes the measurement **INVALID → NO-SHIP**.
2. **G-C's "end-to-end" definition contradicted the inherited measurement (Major, confirmed).** My
   "two independent samples at registered temperature" was invented: `v2/run_battery.py` decodes
   **greedy**, so repeats would be byte-identical, and the inherited scorer consumes `{id, valid}`
   under **dual authority** with a ≥300 emitted-ID floor — whereas I had defined the denominator as
   "all emitted IDs". Fixed: greedy contract, denominator = **authority-checked** emitted IDs,
   unchecked IDs excluded and reported. The **SPEC-V2 600-generations-per-arm vs inherited 300**
   discrepancy is now left **flagged open** rather than invented away.
3. **§2 still claimed §5.3 "Built and passing" with S1–S4 PASS (Major, confirmed).** My retraction in
   §5.3 had not propagated. Fixed: §2 now states the applicability limit, drops the PASS labels, and
   no longer says staging is the only open pre-flight item.
4. **"FIXED by retraction" overstated the cycle-3 dispositions (Major).** Fixed: the G-A/G-A2, §8.6,
   G-D and G-B entries now read **"retracted; blocker OPEN"** and are listed as **open evaluation
   blockers**. Detector acceptance is explicitly not evidence of evaluator correctness.
5. **§8.3's 24-probe instrument is unidentified (Major).** Confirmed: the reused contract defines
   **12 offensive + 8 defensive = 20**, not the specified 12/12, and no 24-probe set exists. §8.3 is
   now **UNMEASURED**, with the requirement to write and freeze the 24 prompts.
6. **A7 reported content verdicts its own calibration invalidates (Minor).** Fixed: §4 now separates
   **raw scorer output** / **hand-verified facts** / **valid gate decisions**, states A7 yields **no
   valid verdict**, and rests exclusion on two independent grounds (11 hand-verified offensive rows;
   no sub-metric calibrated).
7. **The launch happened without a clean review, and the plan did not say so (Major).** Fixed: §10 now
   carries an explicit **Launch-gate disposition** — the run proceeded on owner approval alone, a
   deliberate override of the clean-review condition; it records what that purchases (a
   recipe-faithful, hash-verified training artifact) and what it does not (any evaluation claim). The
   header states the same and forbids citing the document as evidence the condition was met.
8. **Parent-model identity asserted, not established (Minor).** Fixed: §2 no longer says "same pinned
   base revision as v2"; identity is asserted by path and filename set only, and the limitation is
   stated where the base is introduced.
9. **§5.1 kept withdrawn claims and a wrong date (Minor).** Fixed: the withdrawn "lower bound"/"48 %"
   phrasing is reconciled, and completion is corrected to **≈19:20 CDT on 2026-10-01** for the measured
   rate (later readings improved it).
10. **The backup did not enable the cycle-3 comparison (Minor).** Cycle 3's reviewed text was never
    snapshotted and is unrecoverable — **accepted as unclosable**. But the going-forward fix is
    **verified**: `docs/PLAN-V3.md.rev9-bak` hashes to `06f956aa…`, exactly what cycle 4 reviewed, and
    `docs/PLAN-V3.md.rev10-bak` now equals the current rev 10, so cycle 5 can diff the exact text.

## 3. Net effect on the ship path

Unchanged: the run trains the approved recipe on the hash-verified mixture. Changed and now stated
plainly in both the plan and the go/no-go: **the adapter may be trained but cannot be scored** — four
gate evaluators do not implement the written contracts (G-A/G-A2, G-B, §8.6, G-D), G-D lacks both its
reference and its span scorer, G-C has two open contract inconsistencies, and §8.3 has no instrument.
No ship verdict is computable until those are built and demonstrated. Missing measurements remain
NO-SHIP, not passes.

## 4. Next

Monitor to completion; then harvest the training receipt and **build/verify the evaluators** before any
§8 scoring. Cycle 5 is scheduled on the 3-hour cadence against rev 10
(`docs/PLAN-V3.md.rev10-bak`, md5 `8b172d1f05c9af586c8892b8dad6b049`).

Still open from the owner: the **two-host instruction** (impossible without a recipe change — the
trainer has no distributed support) and **Option B** for the trail block.
