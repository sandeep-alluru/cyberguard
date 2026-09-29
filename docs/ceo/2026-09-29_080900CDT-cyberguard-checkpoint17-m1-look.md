---
title: CyberGuard v2 checkpoint 17 — mid-window look 1
issued_at: 2026-09-29T08:09:43-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-29_061400CDT-cyberguard-checkpoint16-m2-look.md
---

# Checkpoint 17 — M1: 137 / 137 steps, 0.027 / 0.027 epoch

**One line:** at M1 the two arms stand at **0.027** and **0.027** of an epoch, measured 0.5038 s/sample against the declared basis of 0.968288 s/sample.

## The M1 numbers (source: `research-tmp/checkpoints/M1-metrics.json`)

| | arm A (`spark-40ee`) | arm B (`spark-8cf2`) |
|---|---|---|
| steps | 137 | 137 |
| s/step | 8.06 | 8.09 |
| samples seen | 2192 | 2192 |
| epoch fraction | 0.027 | 0.027 |
| refusal presentations | 259 | 259 |
| GPU utilisation | 95 % | 85 % |
| trainer alive | yes | yes |

Declared basis (all cited from `v2/data/mixture/FACTS.json`): 81074 rows/arm,
9584 refusal slots, 1198 unique refusal rows.
Projection to 24 h from the same file: **2.116** / **2.108** epochs.

**Instrument governance (D12).** The registered batteries are training rows and are reported
as **recall**, never as generalisation; the fresh training-disjoint instruments carry the
generalisation verdict. The leakage instrument now includes the batteries as its own reference
set and gives per-set verdicts: `c24_batteries` LEAK, `holdout` CLEAN, `probes` CLEAN.

## Verified at this checkpoint

* Live trainer state and the numbers above come from `checkpoint_metrics.sh M1`; the snapshot is **STALE SNAPSHOT: taken 2026-09-29 02:50:43, 5.3 h before this brief.** `checkpoint_metrics.sh M1` did not refresh it for this checkpoint, so the numbers above describe the snapshot time shown here and NOT this checkpoint's moment.
* Watchdog, last cycle: `[2026-09-29 08:09:35] cycle 177 | hashes: MATCH | scans: skipped (hashes unchanged since the last full pass)`
* Repository revision: `5fb73bd ledger: consolidated pre-flight record — registration rules, probe sets, rehearsal, contract dry-run and the objective verifier all green in o …[truncated]`
* **Serving posture (plan requirement):** **not recorded for this checkpoint** (this metrics file predates the eviction check; the contract preflight verifies it again before the evaluation)
* **Astra review at this checkpoint:** **NO REVIEW for this checkpoint** — `checkpoint-M1-review-prompt.md` exists but there is NO dispatch log, and a real dispatch always creates one, so this prompt came from a `--dry-run` and no reviewer has seen it. The cadence requires an Astra review at every checkpoint, and this one has none.
**Composed retrospectively at 08:09 CDT.** The 02:50 M1 snapshot exists at `research-tmp/checkpoints/M1-metrics.json`, but no brief was written for it when the checkpoint fired, so this document fills that cadence gap — and it carries the **STALE** marker above rather than the freshness a brief composed at the checkpoint would have had. No review was dispatched for M1 either (the timeline gained its review step later); that gap is disclosed in this brief record and in `LEDGER.md`.
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
