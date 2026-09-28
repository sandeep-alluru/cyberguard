---
title: CyberGuard v2 checkpoint 4 — all four data items closed; the unified leak instrument found a real embedded-holdout row that three earlier instruments missed; Astra and Muse re-reviewing the frozen arms
issued_at: 2026-09-28T01:00:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-27_231700CDT-cyberguard-checkpoint3-data-audit-and-independent-review.md
---

# Checkpoint 4 — the four open data items, closed

**One line:** every item from the independent data review is closed, the audit and the leak scan both pass
on frozen arms, and the re-review is running — with one finding worth your attention: **the unified leak
instrument found a training row that was an evaluation prompt, which three earlier instruments had passed.**

## What was closed

| item | what it was | what was done | evidence |
|---|---|---|---|
| **D1** leakage instruments disagreed — one used 5-gram, another 13-gram, and the auditor ignored **142 of 160 safety probes** because they are shorter than 13 tokens | could train on an evaluation prompt unnoticed | **one instrument** (`leak_scan.py`): exact + n-gram Jaccard + **containment**, across all three text fields, **both arms**, short references handled by exact match | **it found a real leak**: `armA:55390` was a held-out prompt with words appended — containment **0.812**, below the old Jaccard bar. Builder exclusion extended to containment → **617 held-out rows removed** (was 496) → re-scan **CLEAN, 0 findings in 162,564 rows** |
| **D2** control arm was "a substantially more repetitive, shorter treatment" — 144 distinct prompts / 24 answers vs the treatment's 1,198 / 388 | weakens the causal contrast the whole second arm exists for | rebuilt from two defensive pools (family grid + ATT&CK objects already admitted) | control now **1,198 distinct prompts / 1,021 distinct answers**, same 9,584 slots, mean answer **68.3 vs 71.1 tokens = 3.9 % gap** (bar ≤10 %) |
| **D3** Sigma rules were structurally valid but taught arbitrary detections; 41 triage rows carried a random label | teaches wrong detection semantics | detection **selection derived from the handprint the prompt names**; triage labels for network events derived from the line | Sigma selection matches the named handprint **400/400 (100 %)**; triage now deterministic (11 malicious / 45 benign by rule, was random) |
| **D4** the audit could not invalidate its own PASS — one arm checked, no arm-equivalence assertion, no real tokenizer check | a vacuous PASS | real-tokenizer truncation check; arm-equivalence **assertion**; both-arms coverage | truncation **0.0 %**, empty supervision **0**, arm differences **9,584 with 0 illegal** |

## State of the frozen arms

Epoch **81,282 rows per arm** · refusal **9,584 slots from 1,198 unique rows** (700 offensive refusals +
498 genuine abstentions) = **11.8 %** of the epoch · 24 h covers **109.8 % of an epoch** with **8.78 passes
per refusal row** · leak scan **CLEAN** · audit **PASS (0 failures, 0 warnings)** · `--verify-receipt` →
**RECEIPT-BOUND**. Every figure derives from `v2/data/mixture/FACTS.json`; the watchdog (5-minute cycle) is
running and reported **hashes MATCH, leak CLEAN, audit PASS** on its first cycle.

## In flight

**Astra and Muse are re-reviewing the frozen arms** against the D1–D4 claims. The review is explicitly
asked to hunt for what the new instruments could be blind to *by construction*, and to check whether any
`FACTS.json` metric still disagrees with the delivered files.

## Cost

**Zero GPU-hours.** All four items were CPU and data work. The 24 h × 2 window has not started, the Flash
endpoint is untouched, and no training launches until the re-review clears the data.

## Honest note

D1's finding is the strongest argument for this cadence: the leak was reachable by three separate
instruments, all of which passed it, and it took replacing them with one better instrument to surface it.
Two of my own checks have also been caught lying this session — counting weighted slots instead of unique
rows, twice, once inside the file created to prevent exactly that.
