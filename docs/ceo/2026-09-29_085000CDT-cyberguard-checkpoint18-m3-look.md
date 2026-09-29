---
title: CyberGuard v2 checkpoint 18 — mid-window look 3
issued_at: 2026-09-29T08:50:08-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-29_080900CDT-cyberguard-checkpoint17-m1-look.md
---

# Checkpoint 18 — M3: 2784 / 2695 steps, 0.5494 / 0.5319 epoch

**One line:** at M3 the two arms stand at **0.5494** and **0.5319** of an epoch, measured 0.505 s/sample against the declared basis of 0.968288 s/sample.

## The M3 numbers (source: `research-tmp/checkpoints/M3-metrics.json`)

| | arm A (`spark-40ee`) | arm B (`spark-8cf2`) |
|---|---|---|
| steps | 2784 | 2695 |
| s/step | 8.08 | 7.62 |
| samples seen | 44544 | 43120 |
| epoch fraction | 0.5494 | 0.5319 |
| refusal presentations | 5265 | 5097 |
| GPU utilisation | 95 % | 94 % |
| trainer alive | yes | yes |

Declared basis (all cited from `v2/data/mixture/FACTS.json`): 81074 rows/arm,
9584 refusal slots, 1198 unique refusal rows.
Projection to 24 h from the same file: **2.11** / **2.238** epochs.

**Instrument governance (D12).** The registered batteries are training rows and are reported
as **recall**, never as generalisation; the fresh training-disjoint instruments carry the
generalisation verdict. The leakage instrument now includes the batteries as its own reference
set and gives per-set verdicts: `c24_batteries` LEAK, `holdout` CLEAN, `probes` CLEAN.

## Verified at this checkpoint

* Live trainer state and the numbers above come from `checkpoint_metrics.sh M3`; the snapshot is taken 2026-09-29 08:50:04, 0 min before this brief (the timeline writes a fresh snapshot ~2 min before composing it)
* Watchdog, last cycle: `[2026-09-29 08:49:51] cycle 183 | hashes: MATCH | scans: skipped (hashes unchanged since the last full pass)`
* Repository revision: `6177d0a session close: what is delivered and verified from artifacts (elements 1-2), what is scheduled (3-5, unattended), the one defect that would ha …[truncated]`
* **Serving posture (plan requirement):** in force on both hosts — no `8093` listener and no active serving unit (`eviction` block of the metrics file)
* **Astra review at this checkpoint:** **DISPATCHED, OUTPUT NOT YET WRITTEN** — `checkpoint-M3-review.log` exists, so the Astra review is a background `codex exec` dispatched moments before this brief (the timeline runs review, then brief, in that order); its answer lands at `research-tmp/reviews/checkpoint-M3-review.md`. At composition time this brief cannot report the reviewer's findings.

## What is open

* C24 evaluation contract: the verdict, the checksum-verified harvest and `VERDICT-v2.md` do not exist yet, so
  the objective is not complete.
* Known measurement limitations carried into the verdict: G-D extraction is declared zero-shot; G-I's
  normalised-F1 producer does not exist; MMLU-lite is declared UNMEASURED; the two confirmatory claims are
  scoped to the composed fresh G-A instrument with no inherited power figure (review F27).
* Leakage instrument finding: the registered batteries are present in the training data (**14,162** findings against a reference set of **4,840** battery strings), which is why they are reported as recall and not as generalisation.

## Cost to date

No spend beyond the owner's recorded 24 h x 2 authorization; every number above is cited from
`v2/data/mixture/FACTS.json` or from the live metrics file. The evaluation contract adds roughly 8 h of
generation, split across both machines, after training ends.
