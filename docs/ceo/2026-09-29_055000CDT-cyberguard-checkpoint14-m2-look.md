---
title: CyberGuard v2 checkpoint 14 — mid-window look 2
issued_at: 2026-09-29T05:50:05-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-29_035128CDT-cyberguard-checkpoint13-three-late-failures-closed.md
---

# Checkpoint 14 — M2: 1409 / 1339 steps, 0.2781 / 0.2643 epoch

**One line:** at M2 the two arms stand at **0.2781** and **0.2643** of an epoch, measured 0.5038 s/sample against the declared basis of 0.968288 s/sample.

## The M2 numbers (source: `research-tmp/checkpoints/M2-metrics.json`)

| | arm A (`spark-40ee`) | arm B (`spark-8cf2`) |
|---|---|---|
| steps | 1409 | 1339 |
| s/step | 8.06 | 7.88 |
| samples seen | 22544 | 21424 |
| epoch fraction | 0.2781 | 0.2643 |
| refusal presentations | 2664 | 2532 |
| GPU utilisation | 95 % | 95 % |
| trainer alive | yes | yes |

Declared basis (all cited from `v2/data/mixture/FACTS.json`): 81074 rows/arm,
9584 refusal slots, 1198 unique refusal rows.
Projection to 24 h from the same file: **2.116** / **2.164** epochs.

**Instrument governance (D12).** The registered batteries are training rows and are reported
as **recall**, never as generalisation; the fresh training-disjoint instruments carry the
generalisation verdict. The leakage instrument now includes the batteries as its own reference
set and gives per-set verdicts: `c24_batteries` LEAK, `holdout` CLEAN, `probes` CLEAN.

## Verified at this checkpoint

* Live trainer state and the numbers above come from `checkpoint_metrics.sh M2` at the scheduled moment.
* Watchdog, last cycle: `[2026-09-29 05:46:22] cycle 156 | hashes: MATCH | scans: skipped (hashes unchanged since the last full pass)`
* Repository revision: `a47f0bd review #23: subnormal spacing was 2^-134 where bf16's uniform subnormal spacing is 2^-133, so BOTH controls divided by a denominator half the `

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
