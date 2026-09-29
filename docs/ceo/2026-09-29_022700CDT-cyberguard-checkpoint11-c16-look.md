---
title: CyberGuard v2 checkpoint 11 — the C16 look
issued_at: 2026-09-29T02:27:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-28_182500CDT-cyberguard-checkpoint10-c8-look.md
---

# Checkpoint 11 — C16: 1354 / 1348 steps, 0.2672 / 0.266 epoch

**One line:** at C16 the two arms stand at **0.2672** and **0.266** of an epoch, measured 0.475 s/sample against the declared basis of 0.968288 s/sample.

## The C16 numbers (source: `research-tmp/checkpoints/C16-metrics.json`)

| | arm A (`spark-40ee`) | arm B (`spark-8cf2`) |
|---|---|---|
| steps | 1354 | 1348 |
| s/step | 7.6 | 7.23 |
| samples seen | 21664 | 21568 |
| epoch fraction | 0.2672 | 0.266 |
| refusal presentations | 2560 | 2549 |
| GPU utilisation | 95 % | 95 % |
| trainer alive | yes | yes |

Declared basis (all cited from `v2/data/mixture/FACTS.json`): 81074 rows/arm,
9584 refusal slots, 1198 unique refusal rows.
Projection to 24 h from the same file: **2.244** / **2.358** epochs.

**Instrument governance (D12).** The registered batteries are training rows and are reported
as **recall**, never as generalisation; the fresh training-disjoint instruments carry the
generalisation verdict. The leakage instrument now includes the batteries as its own reference
set and gives per-set verdicts: `c24_batteries` LEAK, `holdout` CLEAN, `probes` CLEAN.

## Verified at this checkpoint

* Live trainer state and the numbers above come from `checkpoint_metrics.sh C16` at the scheduled moment.
* Watchdog, last cycle: `[2026-09-29 02:25:02] cycle 126 | hashes: MATCH | scans: skipped (hashes unchanged since the last full pass)`
* Repository revision: `f3bdb60 pass-eleven findings fixed and falsified. (1) merge acceptance admitted NaN (every comparison is false for NaN), so the stated tolerances were`

## What is open

* C24 evaluation contract: the verdict, the checksum-verified harvest and `VERDICT-v2.md` do not exist yet, so
  the objective is not complete.
* Known measurement limitations carried into the verdict: G-D extraction is declared zero-shot; G-I's
  normalised-F1 producer does not exist; MMLU-lite is declared UNMEASURED; the two confirmatory claims are
  scoped to the composed fresh G-A instrument with no inherited power figure (review F27).
* Leakage instrument finding: the registered batteries are present in the training data (14,162 findings against
  the battery reference set), which is why they are reported as recall and not as generalisation.

## Cost to date

No spend beyond the owner's recorded 24 h x 2 authorization; every number above is cited from
`v2/data/mixture/FACTS.json` or from the live metrics file. The evaluation contract adds roughly 8 h of
generation, split across both machines, after training ends.
