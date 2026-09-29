---
title: CyberGuard v2 checkpoint 16 — mid-window look 2
issued_at: 2026-09-29T06:14:25-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-29_055128CDT-cyberguard-checkpoint15-clearances-and-instrument-defects.md
---

# Checkpoint 16 — M2: 1596 / 1513 steps, 0.315 / 0.2986 epoch

**One line:** at M2 the two arms stand at **0.315** and **0.2986** of an epoch, measured 0.4988 s/sample against the declared basis of 0.968288 s/sample.

## The M2 numbers (source: `research-tmp/checkpoints/M2-metrics.json`)

| | arm A (`spark-40ee`) | arm B (`spark-8cf2`) |
|---|---|---|
| steps | 1596 | 1513 |
| s/step | 7.98 | 7.57 |
| samples seen | 25536 | 24208 |
| epoch fraction | 0.315 | 0.2986 |
| refusal presentations | 3018 | 2861 |
| GPU utilisation | 93 % | 95 % |
| trainer alive | yes | yes |

Declared basis (all cited from `v2/data/mixture/FACTS.json`): 81074 rows/arm,
9584 refusal slots, 1198 unique refusal rows.
Projection to 24 h from the same file: **2.137** / **2.252** epochs.

**Instrument governance (D12).** The registered batteries are training rows and are reported
as **recall**, never as generalisation; the fresh training-disjoint instruments carry the
generalisation verdict. The leakage instrument now includes the batteries as its own reference
set and gives per-set verdicts: `c24_batteries` LEAK, `holdout` CLEAN, `probes` CLEAN.

## Verified at this checkpoint

* Live trainer state and the numbers above come from `checkpoint_metrics.sh M2` at the scheduled moment.
* Watchdog, last cycle: `[2026-09-29 06:11:32] cycle 159 | hashes: MATCH | scans: skipped (hashes unchanged since the last full pass)`
* Repository revision: `9c1ae33 retract a finding I had not tested: I read stage 7's 'harvest | tail -3 || { exit 8; }' as a masked failure (|| binding to tail), which would `

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
