---
title: CyberGuard v2 checkpoint 8 — end of session: the 48-hour window is running unattended on both Sparks, the data has passed every instrument, and the exact continuation is written down
issued_at: 2026-09-28T11:00:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-28_100000CDT-cyberguard-checkpoint7-window4-running.md
---

# Checkpoint 8 — what is running, what is proven, and what remains

**One line:** the training window is live on both machines and will keep running without me, the data has
passed every instrument this project has, twelve independent reviews produced ninety fixed defects, and what is
left is wall-clock time plus procedures that are now written down rather than remembered.

## Running unattended right now

| | |
|---|---|
| **Window 4** | 24 h per arm, detached, `spark-40ee` arm A + `spark-8cf2` arm B — at handover step **210 / 209** of 5,068, ~8 s/step, both trainers alive |
| **Monitors** | host-side `monitor-v2.sh A\|B` — alert on death-without-receipt and on log stalls |
| **Watchdog** | local `watchdog.py`, now skips its hash/scan checks while a build writes the arms (two false DRIFT alerts were raised that way) |
| **Auto-relaunch** | armed: waits for the v14 gate, then runs the six-condition guarded switch; if the gate never lands, it does nothing and the window continues on v13 |
| **Pool** | your `spark-flash-next` pool is **active and enabled** — I re-enabled both units after an earlier fix had left them disabled, which would have kept your model down after a reboot |

## What is proven (evidence, not assertion)

| check | result |
|---|---|
| arms | **81,074 rows each** · armA `86348996…` · armB `1208858a…` — identical on disk, in `FACTS.json`, in all four receipts, and on both hosts |
| audit | **PASS (0 failures, 0 warnings)**, **RECEIPT-BOUND** |
| leakage | **CLEAN — 0 findings in 162,148 rows**, one instrument (exact + 13-gram Jaccard + containment), all three fields, both arms |
| completeness | **D9 acceptance screen PASS — 0 findings**, 12 decidable classes, exclusions printed with counts |
| ATT&CK supervision | **repair check PASS — 0 unresolved** active-id/name contradictions; residual 1,598 stale pre-rename names + 175 ids absent from the bundled export, byte-identical in both arms |
| design (your O1) | **5,600** substitutions, all refusal→replacement, **0 elsewhere**; **3,984** abstention rows identical in both arms |
| model mask | **MASK PROOF PASS on both hosts**, supervised 417/782 tokens, decoded span shown — assistant-only supervision observed, not inferred |
| throughput | measured **8.36 s/step = 0.523 s/sample** on both arms (identical), ≈2 epochs in 24 h |
| Phase 6 | evaluator + merge-equivalence + capability proxies + **gate-verdict layer** (`gates_v2.py`, self-test PASS) + **input bridge** (`eval_inputs_v2.py`, exits 1 on a partial battery) |

## Cost

| resource | spent |
|---|---|
| GPU | **~85 minutes** of the authorized 48 h (three windows stopped early for data reasons, window 4 running) |
| training completed | ~30 minutes of the current window |
| reviews | 12, each dispositioned in writing; 90 defects fixed, several of them defects **I** introduced |

## What remains, and the exact way to do it

`research-tmp/rebuild/HANDOVER.md` carries the procedures; the short form:

1. **C8 (~17:46), C16 (~01:46), C24 (~09:46 tomorrow)** — `bash v2/checkpoint_metrics.sh C8` writes measured
   exposure (samples, epochs, refusal presentations, 24 h projection) beside the FACTS basis; take an
   independent review; publish the dated brief under `docs/ceo/` and verify it renders (HTTP 200, content hits,
   0 raw IPv4). At C8, record which branch the v14 decision took.
2. **Evaluation** — `RUN_NAME=cyberguard-lora-v2-armA run-eval-chain.sh`, then armB; split across both machines.
3. **Verdict** — `python3 v2/eval_inputs_v2.py --check` (which of the 12 gate inputs exist), then
   `python3 v2/gates_v2.py --evals evals/ --out v2/gate-report-v2.json`.
4. **Close** — `harvest-v2.sh` (per-file sha256), then `docs/VERDICT-v2.md`.

## The one thing I could not do

The goal's round budget ends long before C8, so this session cannot execute the checkpoints, the evaluation or
the verdict. That is a limit of session length, not of the work: the window is running, every instrument has
passed, the Phase-6 machinery exists and is self-tested, and the continuation is written down. Nothing is left
resting on my memory.
