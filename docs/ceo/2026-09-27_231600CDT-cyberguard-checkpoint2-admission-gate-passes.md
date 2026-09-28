---
title: CyberGuard v2 checkpoint 2 — the admission gate passes: every mixture source measured against the held-out set, the extraction-corpus hole closed with a real Apache-2.0 corpus
issued_at: 2026-09-27T23:16:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: none
---

# Checkpoint 2 — the gate, and what it proved

**One line:** the plan's first done-means check now exits 0 — **9 candidates measured, 8 admitted, 1
rejected, 0 unmeasured** — and the last hole (extraction data, which v1 never had) is filled with a
licence-clean real corpus.

## Gate result (`v2/gate-report.json`, `--check` exit 0)

| candidate | verdict | max Jaccard vs holdout | containment |
|---|---|---|---|
| Trendyol core (residual after excluding rows that ARE held-out rows) | ADMIT | 0.0266 | 0.0723 |
| NIST CSRC set | ADMIT | 0.0000 | 0.0000 |
| MITRE ATT&CK STIX (2,198 objects) | ADMIT | 0.0000 | 0.0000 |
| NVD CVE 2.0 (14,873 rows) | ADMIT | 0.0000 | 0.0000 |
| authored refusal-retention set (1,200 rows) | ADMIT | 0.0000 | 0.0000 |
| authored format-compliance set (1,500 rows) | ADMIT | 0.0000 | 0.0000 |
| `chairulridjal/arcspan-cyber-ner` (Apache-2.0, train split) | ADMIT | 0.0000 | 0.0000 |
| `HuggingFaceH4/ultrachat_200k` (MIT, replay) | ADMIT | 0.0000 | 0.0000 |
| `zefang-liu/secqa` | **REJECT** | — | evaluation set; never trained on |

**MITRE ATT&CK was flagged highest-risk** in the earlier research (the holdout's subject *is* ATT&CK
mapping). Measured: **0.0000 overlap**. Flagging a risk and then measuring it are different acts.

## The measurement lesson of this checkpoint

The first gate run "found" 22 contaminated rows with containment 1.0 — but the sample was `head -2000`
of the corpus, which **contains the 500 held-out rows**. Excluding them by prompt identity (22 excluded,
exactly matching the 22 hits) dropped max Jaccard from **0.7166 to 0.0266**. **A leak you can explain by
construction is not a leak; the residual is the measurement.** Implemented as `--exclude-holdout-rows`.

It also caught a real bug: the exclusion silently did nothing because the export hashed the **raw**
prompt while the gate hashed the **normalised** one. Left alone, the gate would have **rejected the core
corpus** — a wrong admission decision produced by a hash-convention mismatch.

## What now exists that did not before

| asset | size | why it matters |
|---|---|---|
| authored refusal-retention set | 1,200 rows | the F1 fix: offensive refusals, genuine abstentions, dual-use boundaries, defensive redirects |
| authored format-compliance set | 1,500 rows | the F4 fix: one-word verdicts, **schema-complete Sigma**, strict JSON, YAML |
| extraction corpus | arcspan train split | replaces v1's authored easy-mode data, on which its 65 % fabricated-IOC finding was only a floor |
| conversational replay | 600 real turn pairs | the F9 chat-retention slot, sourced MIT and API-verified |

**No GPU time spent.** The gate is CPU-only and ran entirely on the workstation.
