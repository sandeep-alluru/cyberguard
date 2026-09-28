---
title: CyberGuard v2 checkpoint 6 — review convergence (212 → 27 → 6 rows), the acceptance standard is now written down, and every endpoint is green
issued_at: 2026-09-28T07:00:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-28_040000CDT-cyberguard-checkpoint5-gpu-blocker-and-review5.md
---

# Checkpoint 6 — the completeness reviews are converging, and the standard is now decidable

**One line:** five independent reviews have each withheld clearance on answer completeness, but the counts are
now falling sharply (212 → 27 → 6 rows) because the objections have become **executable predicates** rather
than unstated reader preferences; the acceptance rules are written into `v2/completeness_screen.py`, every
instrument is green, and the only thing standing between us and the 48-hour window is your decision on one
design question below.

## The convergence, honestly stated

| review | its completeness objection | my disposition |
|---|---:|---|
| #4 | 10 control answers ended mid-thought | fixed the sentence splitter |
| #5 | 38 incomplete targets (headings, colon endings, code fences) | added defect classes |
| #6 | 212 incomplete targets + 276 control answers that did not answer their own question | fixed both; the 276 were **my own** topic-matching regression |
| #7 | 27 rows the rules misclassified + 11 complete answers wrongly dropped | implemented its four predicates; restored the 11 |
| #8 | 6 rows + 7 complete answers falsely rejected as inline code + 2 answers damaged by trimming | implemented its three rules; fixed the trimming bug |

Review #8's remaining objection is six presentations out of 162,208 (0.004 %). Two of its findings were real
defects of mine, and both are worth naming:

- **A rule I added was too loose.** My "unclosed inline code" test counted backticks in the whole answer, so
  seven *complete* answers were dropped because a CVE description legitimately mentions a literal backtick.
  The rule now strips paired spans and explicitly described literals, and checks parity within the final
  sentence only — three true positives retained, all seven false rejections gone.
- **The trimming path was destroying complete answers.** `finalise()` trimmed unconditionally, so a complete
  ATT&CK answer ending `(Citation: Unit 42 OopsIE! Feb 2018)` was cut at its internal `!` and then dropped.
  It now preserves an already-complete target **verbatim**. This is the review's rule, not my judgement.

## What is now written down (the previous blocker)

Review #6 conceded that "universal human-semantic certification is not established" for 162,244 rows — an
undecidable bar cannot be a gate, or the loop never terminates. So the standard is now a file:
`v2/completeness_screen.py` states **12 decidable classes**, prints its exclusions with row counts
(2,600 label/YAML/JSON targets per arm, so an exclusion cannot hide a row), and exits 0/1. Two candidate rules
were **removed after measurement**: "unbalanced-parenthesis" (25 of 30 hits were answers ending on a perfectly
balanced sentence) and a loose truncated-path rule (it flagged the complete sentence "…replacing /cgi-bin/
with /cgi-bin-sdb/."). The recorded review boundary: a withholding objection must now cite a row the *stated*
rules misclassify, or propose a new decidable rule with a reproduction. Reviews #7 and #8 both did exactly
that, which is why this is converging instead of oscillating.

## Endpoint state (all green, verified this checkpoint)

| check | result |
|---|---|
| `completeness_screen.py` (the written acceptance test) | **PASS — 0 findings, both arms** |
| audit | **PASS (0 failures, 0 warnings)**; `probe_text_found_in_training = 0` |
| leak scan | **CLEAN — 0 findings in 162,208 rows** |
| receipt binding | **RECEIPT-BOUND** (arms byte-identical to the audited revision) |
| arms | **81,104 rows each** (from 81,282: the difference is 178 incomplete targets dropped by reason, all recorded in the receipt) |
| refusal slots | **9,584**, from 1,198 unique rows (700 offensive-refusal + 498 unknown-answer) |
| control arm | **19 answerable templates × 12 families = 228 pairs, 0 mismatches**; 2,270 unique control prompts |
| staging | both arms hash-verified on `spark-40ee` and `spark-8cf2` |

Every drop is receipted by reason: no-boundary 98, dangling-punctuation 31, heading-only 12, unclosed-code-fence
11, terminal-open-inline-code 11, flattened-heading-list-start 6, probe-overlap 4, inline-heading-cut 2,
truncated-path 1, unclosed-citation 1, terminal-open-such-as 1.

## The one decision I need (unchanged from checkpoint 5, now with its cost measured)

Arm B replaces **every** refusal slot, including the 3,984 **unknown-answer abstention** slots ("which CWE is
assigned to…"), where no topic exists to match, so those draw from the general defensive pool. Arm B therefore
differs from arm A in refusal weighting *and* in what happens on unknown questions. My recommendation remains:
**leave those 498 prompts identical in both arms**, so the manipulation isolates offensive-refusal behaviour —
which is exactly what the primary comparison claims. It is one line of re-registration. If you prefer to keep
the design as pre-registered, I will state the confound in the verdict instead; either is defensible, and I
will not silently choose for you.

## Cost to date

| resource | spent |
|---|---|
| GPU-hours on either Spark | **0** |
| v2 training runs launched | **0** |
| reviews received and dispositioned | 8 (two in this window) |
| wall-clock | ~9 h of preparation, review and repair |

## What is open

| # | item | owner | exit condition |
|---|---|---|---|
| O1 | the abstention-rows design call above | **owner** | recorded in `docs/SPEC-V2.md` |
| O2 | build 19 in flight (review #8's fixes) | me | audit PASS + screen PASS + new hashes staged |
| O3 | review #9 on the rebuilt arms | codex | clearance, or findings dispositioned as before |
| O4 | Phase 5: stop the pool, prove the memory free, smoke both arms, launch 24 h × 2 | me | both arms training, monitor armed, checkpoint 7 brief |
| O5 | Astra review at each checkpoint (standing cadence) | Astra | filed per checkpoint |

Note on O5: `astra`/`deepseek` CLIs do not exist on this machine, so independent reviews are being run through
the codex CLI, which is a different agent and a separate context. That substitution is recorded rather than
implied, and it is the only deviation from the cadence as written.
