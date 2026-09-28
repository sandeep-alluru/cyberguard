---
title: CyberGuard v2 — the plan in sequence, with every step owned and falsifiable; one blocker left (the data gate) and zero GPU-hours spent so far
issued_at: 2026-09-27T23:50:00-05:00
project: CyberGuard
status: current
kind: plan
supersedes: 2026-09-27_203600CDT-cyberguard-v2-plan-ceo-brief.md
---

# The whole plan, in the order it runs

**One line:** the v2 plan is now a single document you can audit — phases in dependency order, thirteen
steps each with an owner and a command that proves it finished, the gate table, the artifact list, every
review and its verdict — and it says plainly that **the only thing standing between here and a training
run is the data-integrity gate**, which is open because an independent review found seven data defects
five of which are fixed.

Full documents: `docs/PLAN-SEQUENCE.md` (the index and sequence) · `docs/SPEC-V2.md` (the detailed spec)
· `LEDGER.md` (the dated record) · `docs/CRAFT/` (the craft corpus). Nothing in this brief is a plan for
later — every "done" below was verified by running the check that proves it.

## The sequence

| phase | what it is | state |
|---|---|---|
| 0 | orientation + plan of record + the 77-lesson craft corpus | **done** |
| 1 | admission gate — every data source measured against our own hidden test set | **done**: 9 measured, 8 admitted, 1 rejected, 0 unmeasured |
| 2 | mixture build — two training arms, weighted, deduped, leak-filtered, receipted | **done**: 81,802 rows per arm |
| 3 | **data-integrity gate** — audit, independent review, fix, re-review | **open** — audit passes; 4 items from the review outstanding |
| 4 | design reviews (13 rounds with a different model family) | 12 closed; 1 confirmation running |
| 5 | training: 24 h × 2 arms in parallel, checkpoints at 8/16/24 h | **blocked on phase 3** |
| 6 | evaluation: two pre-registered confirmatory analyses + nine gates | blocked on phase 5 |
| 7 | verdict, evidence harvest, CEO brief | blocked on phase 6 |

**Two preconditions on training, both stated in the plan:** the data gate must verify by hash that the
files being trained are exactly the files that passed, and your authorization — which you gave.

## What each step guarantees, in plain terms

- **The admission gate** proves no training row is a memorised copy of the hidden test set, and that no
  candidate source is an evaluation benchmark in disguise (one was rejected for exactly that).
- **The data audit** checks ten families of defect — leaks, duplicates, escaping damage, answer quality,
  label sanity, format validity, length overflow, arm equivalence.
- **The design reviews** are a different model family with standing to object and no design authority;
  it has now reviewed this plan thirteen times and **falsified two of our own published claims** along
  the way — one of which was the headline lesson from v1.
- **The gates** are pre-registered: two confirmatory claims (does the fix work; is the substitution the
  cause) and nine capability/safety gates, each with a sample size and a pass rule fixed *before* data
  was collected.

## What the data gate found, and where it stands

The independent review's verdict was **"data not cleared."** Its blockers were fixed: a mislabelled
abstention category, 14,748 answers that contradicted their own prompt, 997 NIST rows whose prompt
pointed at nothing, and **28,709 rows carrying escape residue**. What remains open, with owners:

1. **Leakage instruments disagree** — one check looks for 5-word matches, another for 13, and the auditor
   currently ignores 142 of 160 safety probes because they're short. This is the one with real
   consequence.
2. **The control arm isn't matched** — 144 distinct prompts against the treatment's 1,198, and shorter answers.
3. **Format semantics** — Sigma rules are structurally valid but the detection content doesn't always
   follow the stated goal; 41 triage rows carry a random label.
4. **Audit coverage** — both arms, full range, and a real tokenizer truncation check.

Also on the record: **extraction training data is absent** (the corpus's labels aren't retrievable), so
that capability will be measured zero-shot — a cleaner test, but stated as such.

## Cost

| | |
|---|---|
| GPU spent to date | **zero** |
| authorized | 24 h × 2 machines |
| planned total | ~57.6 machine-hours ≈ 28.8 h elapsed; 30 h is an allowance, not a derived number |
| only operational impact | the Flash endpoint goes down on both nodes **for that window only**, restored with a verified probe |

## What I need from you

**Nothing to proceed.** Your authorization covers the run. The single thing worth your attention is that
the endpoint outage is a ~30-hour window, so if there's a period you want it up, name it and I'll schedule
around it — otherwise I'll run it in the quiet hours once the data gate clears.

## Honest limits

- The plan is **not** complete as an artifact set: five deliverables it names do not exist yet
  (`id_validator.py`, the gate-8 protocol, `harvest-v2.sh`, the CPT probe, the serving guard) and they
  are listed as missing rather than implied to exist.
- Nine of the thirteen units have never run end-to-end even once. Phase 5 is the first time this
  pipeline trains anything.
- The refusal-data dose (8.7 passes over the refusal set at 24 h) is a design choice whose effect v2
  **measures**; nothing yet establishes it is sufficient.
