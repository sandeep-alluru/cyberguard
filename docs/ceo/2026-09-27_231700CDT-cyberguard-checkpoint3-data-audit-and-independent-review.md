---
title: CyberGuard v2 checkpoint 3 — the pre-training data audit found three real defects (including 492 training rows that were held-out prompts), fixed them, and the independent review still says NOT CLEARED with four open items
issued_at: 2026-09-27T23:17:00-05:00
project: CyberGuard
status: current
kind: review
supersedes: none
---

# Checkpoint 3 — the data, audited and independently reviewed

**One line:** you asked that bad data be found now rather than mid-run. The audit found three real
defects — the worst being **492 training rows that were literally held-out evaluation prompts** — all
three are fixed; then an independent Astra review found **seven more**, two of them blockers, which are
fixed or openly listed below. **The data is not cleared yet, and I am not calling it cleared.**

## Part 1 — my audit, and what it caught

| # | defect | severity | fix | verified |
|---|---|---|---|---|
| 1 | **492 training rows whose prompt IS one of the 500 held-out prompts** — the builder never applied the train/eval split, so the benchmark would have been scored partly on memorised rows; 3 near-duplicates survived exact exclusion | **benchmark-invalidating** | holdout exclusion by prompt identity **plus** ≥0.80 near-duplicate filtering | **496 rows removed, 0 residual overlap** |
| 2 | **3,525 repeated prompts across 16,027 rows** — the ×8/×2 weights explain 10,745; the rest were genuine (Trendyol's 669 duplicate prompts, near-dupes in ATT&CK/NVD/NIST) | major | per-source dedupe with 0.80 near-duplicate collapse, keyed on **content** for documents and on the **prompt** for conversations | unexplained duplicates 1,153 (<2 % bar) |
| 3 | the conversational-replay slot **was not a conversation** — a fixed prompt with a flattened blob | major | re-fetched **600 real user/assistant turns** | 600 pairs |

**Three bugs in my own audit tooling** surfaced doing this: keying every source's dedupe on the prompt
collapsed **1,000 NIST rows to 5**; the Sigma check matched the word "Sigma" inside NIST prose; and the
degeneracy check counted the 1,200 *intentional* one-word verdicts as defects.

## Part 2 — the independent review (Astra), and its verdict

**Verdict: `DATA NOT CLEARED`** — 7 findings, each reproduced against the files. Fixed so far:

| finding | defect | fix | verified |
|---|---|---|---|
| **BLOCKER 1** | my generator's top-up loop padded the unknown-answer category with **defensive answers wearing an abstention label** (only 144 of 220 genuinely abstained); the auditor never checked that labelled abstentions abstain | loop deleted; abstention answers rewritten | **300 rows, 100 % abstain; 298 unique survive** (gate needs ≥200); new abstention check → 0 failures |
| **BLOCKER 2a** | **14,748 of 14,759 NVD answers omitted the CVE ID** the prompt demanded | answers now lead with the identifier | 14,847/14,847 |
| **BLOCKER 2b** | 997 NIST rows shared 5 prompts; answer embedded a persona **and a different question** | persona stripped; prompt is now the embedded question; rows with no question skipped | 835 rows, all prompts end "?" |
| **BLOCKER 2c** | 386 extraction rows asked for typed indicators, received report prose | arcspan's label field is **not retrievable** via the viewer API → **removed from training**, kept as a G-D *evaluation* corpus | extraction training support is now **absent**; G-D becomes a zero-shot test (plan edit queued) |
| MAJOR 5 | **28,709 rows carried a backslash before a real newline**, and my check looked for backslash+`n` so it reported zero | cleaned; builder scrub pattern fixed | **1 row** |
| MAJOR 5b | clipping ended answers mid-clause | cuts at sentence boundaries | 2 of 81,802 rows over 512 tokens |

**Two of my own checks were lying** and the review is what exposed them: the unknown-answer support
check counted **weighted slots (1,552 → pass)** where the truth was **194 unique (fail)**; and the
residue detector was blind to the actual artefact.

## Part 3 — open items (not closed, not hidden)

1. **Leakage instruments disagree** — builder 5-gram vs auditor 13-gram, and the auditor **ignores 142
   of 160 capability probes** because they are shorter than 13 tokens; it scans arm A only and ignores
   assistant/system text.
2. **Control-arm matching** — improved 48→144 distinct prompts and 12→24 answers, but the treatment has
   1,198/388; the control is still more repetitive and shorter.
3. **Format semantics** — Sigma *logsource* now follows the requested channel (100 % coherent), but the
   selection field/value still does not follow the stated handprint, and 41 triage rows carry a random
   label for generic network connections.
4. **Audit coverage** — both arms, full range, arm-equivalence assertion, and a real tokenizer /
   loss-mask truncation check.

## Part 4 — Muse

Muse Code 1.4.0 **is installed and ran** (headless, `muse exec --prompt-file`; it noted only that its
automatic agent-delegation is unavailable because the workspace is untrusted). It produced **no review
output** — its log stopped after startup. Astra carried this round; Muse will be re-run on the corrected
data.

## Cost to date

**Zero GPU-hours.** Every step here is CPU and data work. Nothing trains until the data is signed off by
a second family and the design review clears.
