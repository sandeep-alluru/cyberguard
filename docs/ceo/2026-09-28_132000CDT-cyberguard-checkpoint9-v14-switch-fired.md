---
title: CyberGuard v2 checkpoint 9 — the guarded v14 switch fired by itself, the running window is verified on the corrected arms, and the checkpoint cadence resumes
issued_at: 2026-09-28T13:20:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-28_110000CDT-cyberguard-checkpoint8-end-of-session.md
---

# Checkpoint 9 — the corrected arms are the ones training, proven from the trainers' own logs

**One line:** the auto-relaunch I armed at handover fired unattended at 10:25:38, both arms restarted on the
**v14** revision (the one with the ATT&CK repair), and I verified that from each trainer's own `ARM MODE` line
rather than from hashes on disk — then found and fixed a watchdog defect that had been generating false
`DATA-DRIFT` alarms.

## Verified this checkpoint (checked, not remembered)

| item | evidence |
|---|---|
| which arms the trainers **actually loaded** | arm A `ARM MODE … rows=81074 sha256=bc785b430551d831`; arm B `sha256=61c94262e3c48321` — read from each trainer's own log, and each host's arm file hashes to the same value |
| are those the **audited** arms | **all four receipts bind them**: `FACTS.json`, `audit.receipt.json`, `mixture.receipt.json`, `leak-scan.receipt.json` → `bc785b4305…` / `61c94262e3…` |
| the switch itself | auto-relaunch log: gate complete → guarded relaunch → **exit 0**, both trainers alive, monitors re-armed, window relaunched 10:25:38 |
| v14 gate (all six conditions) | audit PASS (0 failures, 0 warnings) · RECEIPT-BOUND · leak CLEAN · completeness screen PASS · **ATT&CK repair PASS** · O1 verified (5,600 substituted, 3,984 abstentions identical) |
| the false alarm, explained | the `DATA-DRIFT` alerts from 10:21 were the window switch: the watchdog's baseline was the v13 audit while the arms had become v14. Its baseline now matches the running arms |

## Progress and projection (from the measured rate, not the plan's basis)

| | arm A | arm B |
|---|---:|---:|
| step | **1,309 / 5,068** | **1,310 / 5,068** |
| rate | 8.07 s/step | 7.96 s/step |
| exposure so far | 0.258 epoch · 2,475 refusal presentations | 0.259 epoch · 2,477 |
| 24 h projection | **2.11 epochs · ≈20,250 refusal presentations** | **2.14 epochs · ≈20,529** |
| GPU | 95 % | 95 % |

The declared FACTS basis (0.968 s/sample → 21.8 h/epoch) is printed beside the measured 8.0 s/step for
comparison: the run is ~1.85× faster than the basis the plan was written on, so the arms will see roughly
twice the planned refusal exposure (~17 passes per unique refusal row rather than 8.78). That is recorded, not
silently enjoyed — the verdict must quote realized exposure.

**Window timing, measured from the actual training start (10:24:28):** C8 ≈ **18:24 today**, C16 ≈ **02:24
tomorrow**, C24 ≈ **10:24 tomorrow**, self-stop at 24 h via `TimeBox`, receipt written by the trainer.

## Defect found and fixed this checkpoint

The watchdog's alert retirement was **not idempotent**: `ALERT-*` re-matched files that had already been
retired, so every resolution appended another `.resolved`. Names had accumulated **18 suffixes** and a shell
glob over them was failing with *File name too long* — which is also what made an earlier `bash`-launched
watchdog instance die loudly. Retirement now skips anything ending in `.resolved`; three runaway names were
collapsed and the watchdog restarted (pid 3074517) with the correct v14 baseline.

## Cost to date

| resource | spent |
|---|---|
| GPU (this window) | 2 h 51 m |
| GPU (three earlier windows, stopped for data reasons) | ~1 h 25 m |
| **total of the authorized 48 h** | **≈ 4 h 15 m** |
| reviews | 13 received, all dispositioned; 91 defects fixed, several of them mine |

## Open

| # | item | owner | exit condition |
|---|---|---|---|
| 1 | C8 / C16 / C24 checkpoints | me | metrics + independent review + dated brief per checkpoint |
| 2 | evaluation contract (~8 h, split across both machines) | me | `eval_cyberguard.py` per arm + the batteries behind the 12 gate inputs |
| 3 | `gate-report-v2.json` | me | `python3 v2/gates_v2.py --evals evals/ --out …` exits 0 with one outcome per gate |
| 4 | harvest + `docs/VERDICT-v2.md` | me | `harvest-v2.sh` per-file sha256 + verdict quoting realized exposure from the receipts |
