---
title: CyberGuard v2 checkpoint 10 — the C8 look: both arms at 0.73 epoch on the audited revision, and the verdict chain hardened while the window runs
issued_at: 2026-09-28T18:25:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-28_132000CDT-cyberguard-checkpoint9-v14-switch-fired.md
---

# Checkpoint 10 — C8: 0.73 epoch per arm, 16 of 48 authorised GPU-hours spent, and the chain that will produce the verdict made materially safer

**One line:** at the C8 trajectory point both arms are alive and level — **0.726 / 0.727 of an epoch**, 8.03 and
7.94 s/step, GPU 93 % and 95 % — running on the revision that passed the audit, while the evaluation chain that
will turn C24 into a verdict was reviewed a third time, found to contain **two further blocking defects**, and
had them fixed along with seven earlier findings.

## The C8 numbers (source: `research-tmp/checkpoints/C8-metrics.json`, taken 18:25:00 CDT)

| | arm A (`spark-40ee`) | arm B (`spark-8cf2`) |
|---|---|---|
| steps | **3,678** | **3,683** |
| s/step | 8.03 | 7.94 |
| samples seen | 58,848 | 58,928 |
| epoch fraction | **0.7259** | **0.7268** |
| refusal presentations | 6,956 | 6,966 |
| passes per unique refusal row | 5.81 | 5.81 |
| GPU utilisation | 93 % | 95 % |
| trainer alive | yes | yes |

Measured cost per sample: **0.5019 s** (A) and **0.4963 s** (B), against the declared FACTS basis of
0.968288 s/sample — the window is running **1.93× faster** than the basis the budget was built on. Projection to
24 h (from the same file): **2.12 / 2.15 epochs** and 20,350 / 20,581 refusal presentations. Elapsed at this
checkpoint: **≈8.0 h of the authorised 24 h per arm = 16.0 of 48 GPU-hours**; the declared basis is
81,074 rows/arm and 9,584 refusal slots with 1,198 unique refusal rows (all cited from
`v2/data/mixture/FACTS.json`).

## What was verified, not assumed

* **The run is the audited one.** Both trainers print their own `ARM MODE` line naming the mixture file, row
  count and sha256; those hashes are the ones the audit, leak scan, mixture receipt and FACTS all bind
  (`bc785b430551…` for arm A, `61c94262e3c4…` for arm B). Verified from the trainers' logs, not from hashes on
  disk.
* **The watchdog has cycled 49 times** since it was restarted with the correct baseline at 13:16; every cycle
  reported `hashes: MATCH`, the full leak scan returned `CLEAN`, and the full audit returned `PASS` at each
  full pass (last at 18:16). No `ALERT-*` file is open.
* **The C8 data point was captured at exactly 18:25:00 CDT** by the pre-armed collector, so the checkpoint does
  not depend on anyone being awake at the moment it was due.

## What changed in this round

**A third independent review of the evaluation chain returned BLOCKED, and it was right twice more.** Seven
findings were confirmed FIXED (including the one that mattered most: the driver had been sending each G-B
triage probe's **gold label as the question** — the battery would have asked the model to classify the word
"benign" 300 times and scored it against that same word). Two **new blocking** defects were found and fixed:

* **G-F double-counted refusal and hedge** — one response can be both, and the two counters were added, so ten
  double-flagged unknowns supplied twenty "handled" outcomes and **ten fabricated answers disappeared**; the
  gate PASSed. The scorer now returns the union and the verdict layer requires it.
* **A never-scanned corpus read as a measured zero** — a missing scan entry defaulted to `0` literal escape
  sequences and **G-I PASSed**. An incomplete scan now yields no number, and the gate says UNMEASURED.

Alongside those: unchecked CVE identifiers no longer count as clean; the extraction gate uses its *observed*
point estimate rather than a confidence endpoint the spec never registered for it; an aggregate input no longer
emits two contradictory rows for one gate; null-valued and duplicated probe records no longer satisfy support;
a severity share over a single observation is no longer called supported; a replay receipt can no longer be
mistaken for an arm evaluation; and **a `--stub` chain can no longer decide a gate** (it produced 1 PASS and 10
FAILs before). A missing producer was written for G-I's corpus half (`v2/corpus_escape_scan.py`): **0 literal
escape sequences** in both arms, hashes matching the arms actually training, with 45,268 assistant rows
containing genuine newlines — the distinction the gate is about. The verdict vector also grew from 15 to 18
rows so the three things the spec declares UNMEASURED by construction are visible instead of absent.

**The C24 contract could not have run as written.** Stages 1–2 execute locally while the adapters exist only on
the training hosts, so the contract would have aborted at preflight with *"adapter missing"* at 10:25 tomorrow,
after the full 24 GPU-hours. It now pulls both adapters first (keeping HF symlink semantics, excluding
intermediate checkpoints) and then requires that the adapter the batteries ran **is** the adapter that is
shipped, by comparing hashes.

**Owner decisions D10 and D11 were given and implemented:** G-A is re-registered as non-compliance retention
(700 offensive + 400 abstention, n=1,100 preserved) and G-G at the reachable floor (GSM8K 1,200 + IFEval 40,
MMLU-lite declared UNMEASURED with per-task n). Both are recorded in the plan of record.

**The Flash-Next serving stack was evicted from both hosts on the owner's instruction** and verified to stay
down across a full guard period: services and guard timers inactive **and** disabled, serving port closed, GPU
memory free rising from 14.9 to 69.5 GB (`spark-40ee`) and 5.9 to 88.0 GB (`spark-8cf2`). The only GPU compute
process left on either host is the CyberGuard trainer. The trainers were never signalled, and the previously
planned "restore the pool at the end of the window" step is superseded by that instruction.

## What is still open

* **Independent review is held.** The confirmation pass on the fixes above was dispatched and then lost to
  codex transport failures (`websocket: Connection refused`, then repeated model-endpoint refresh failures);
  the owner then asked for a pause while the work is evaluated, so it has not been re-dispatched. **Nothing in
  this checkpoint should be read as chain-cleared.**
* **Two chain items remain open by declaration:** the tested model/decoding identity now travels with the
  assembled input and is compared against the shipped adapter, but per-arm interval coverage for the control
  arm is incomplete; and merge-equivalence is still *recorded* rather than *measured* until the adapters exist.
* **C16 (≈02:25) and C24 (≈10:25 tomorrow)**, then the evaluation contract, `gate-report-v2.json`, the
  checksum-verified harvest and `VERDICT-v2.md`. The goal is not complete until that verdict and harvest exist.

## Cost to date

**16.0 GPU-hours of the owner-authorised 48** (8.0 h per arm at this checkpoint), no spend beyond the
authorisation. The evaluation contract adds an estimated ≈8 h of generation, split across both machines, after
training ends. Wall-clock since the window restarted: 8.0 h. Cost in money: none beyond the authorised machine
time — no rented capacity, no external service.

## Note on this checkpoint's timing

This brief is written late by the cadence it belongs to: the C8 point fell at 18:25 and the session was paused
at the owner's request shortly before it. The metrics were captured at the scheduled moment, so the numbers
above are the C8 quantities rather than a reconstruction. I have not retried the independent review or changed
any code during the pause.
