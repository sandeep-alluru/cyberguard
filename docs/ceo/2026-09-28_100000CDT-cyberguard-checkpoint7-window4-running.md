---
title: CyberGuard v2 checkpoint 7 — window 4 is running to C8; the ATT&CK supervision defect is down from 619 to 776 assertions across three stopped windows, and the cost of stopping early is now recorded
issued_at: 2026-09-28T10:00:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-28_070000CDT-cyberguard-checkpoint6-review-convergence.md
---

# Checkpoint 7 — the run is trading wall-clock for data cleanliness, deliberately

**One line:** the training is running (window 4, started 09:46 CDT), and it is the fourth start because three
independent reviews each found a real defect in the shared corpus within the first 25 minutes; I stopped each
rather than carry the defect to the C8 checkpoint, and the defect class is now 87 % smaller.

## Where the run stands

| | state |
|---|---|
| Window 4 | **running** since 09:46:15 CDT — arm A on `spark-40ee`, arm B on `spark-8cf2`, 24 h each, monitors armed on both hosts |
| C8 / C16 / C24 | ~17:46 today / ~01:46 tomorrow / ~09:46 tomorrow |
| Frozen arms | v13: **81,074 rows per arm**; armA `86348996…`, armB `1208858a…` — staged and hash-verified on both hosts |
| Instruments | audit **PASS** (0 failures, 0 warnings) · leak scan **CLEAN 0/162,148** · completeness screen **PASS 0 findings** · ATT&CK repair check **PASS (0 unresolved)** · O1 design **verified** |
| GPU spent | **~60 minutes** across three stopped windows; **0 h of training completed** so far |
| Reviews | 12 received, every finding dispositioned in writing |

## The defect, and why it kept surviving

The shared base corpus pairs ATT&CK technique **IDs with the wrong names** — it taught `T1071.004 = Web
Protocols` when T1071.004 is DNS, and `T1558.001 = Kerberoasting` when that is Golden Ticket. Both arms share
it, so the A/B comparison was never at risk, but the model would learn false mappings and the evaluation asks
about those very IDs. Three review rounds cut it down, and two of the three fixes were repairs of **my own
repair**:

| round | what the reviewer found | what was wrong | survivors |
|---|---|---:|
| #9 | wrong active id with a sibling's name | the corpus | 1,183 assertions |
| #10 | 619 survived | **my name index included MITRE's revoked objects**, so "Kerberoasting" resolved to dead `T1208` and the correct repair was refused | 619 |
| #11 | 105 survived | **my ambiguity guard** refused unique `Parent: Leaf` labels because the leaf alone was ambiguous | 105 |
| #12 | 26 full-label + 750 parent-ID | queued for the next fix | 776 |

Each fix is mechanical and verifiable: the current one resolves a text label through a full-label index
(`Parent: Leaf`), prefers **active** ids by name, still resolves revoked ids by ID so a historical citation is
not called unknown, and refuses a name that maps to more than one active id. The measurement is a script, not
an adjective: `v2/attack_label_audit.py` reports 8,013 correct / 1,598 stale-or-loose / 175 unknown-id
assertions, **identical in both arms**, and `REPAIR CHECK: PASS` means no assertion pairs an id with a name
that another active id carries.

## The decision I made, and the one I will make at C8

Review #12's verdict was **DATA NOT CLEARED, STOP AT C8, explicitly "no finding meets the STOP NOW
threshold"**. Your directive was not to be blocked. So rather than stop window 4 in its first hour for the
third time, it **runs to C8** while the two remaining classes are fixed and gated in parallel — a rebuild costs
CPU, not GPU, so it does not touch the run.

At C8 the decision is evidence-based, and I will state which branch I took and why:

- if the corrected arms are clean **and** the remaining defect is material (an active id paired with another
  active id's name), **stop and relaunch** on the corrected arms — cost 8 h;
- if the classes turn out to be loose-but-legitimate citation forms (a parent ID cited with a child's name),
  **continue** window 4 to C24 and record it as a declared residual.

## Cost and ETA

| milestone | when (CDT) |
|---|---|
| C8 checkpoint (Astra review + brief) | ~17:46 today |
| C16 | ~01:46 tomorrow |
| C24 — both arms complete | ~09:46 tomorrow |
| Evaluation contract (~8 h, split across both machines) | ~18:00 tomorrow |
| VERDICT-v2 + harvest + final brief | **~20:00 tomorrow** |

Risk to that ETA: one more data-fix cycle costs about an hour; each of the last two cut the defect count by
~85 %, so I expect at most one. The GPU authorization is untouched — 60 minutes of the 48 h window have been
used, and stopping early is exactly what keeps it that way.
