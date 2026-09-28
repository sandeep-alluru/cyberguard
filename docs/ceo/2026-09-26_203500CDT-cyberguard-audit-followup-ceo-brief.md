---
title: CyberGuard — audit follow-up: v1 never trained (crash found), pipeline now gate-verified, brief completed, launch awaiting owner approval
issued_at: 2026-09-26T20:35:00-05:00
project: CyberGuard
status: current
kind: status
supersedes: 2026-09-26_181000CDT-cyberguard-dsh-session-audit-ceo-brief.md
---

# CyberGuard — audit follow-up · CEO brief

**Updated** 2026-09-26 20:35 CDT · **Project** `cyberguard` · **Compute** GB10 Spark idle (0 % util)
This brief resolves the two open questions from the session audit and records what was done after it.
The audit's findings about the endpoint wipeout stand; this is the state **now**.

## 1 · The audit's open question answered: v1 never trained — and the reason is the exact defect class the pre-flight gate exists for

The training log on the Spark host ends in a crash at trainer initialization:
`'TimeBox' object has no attribute 'on_init_end'` — a renamed/missing callback method, the same
class as the two earlier "crashed after all the work was done" incidents recorded in `check.sh`'s
own header. **No v1 adapter and no v1 training receipt exist.** GPU has been idle since.

## 2 · The pipeline has since been fixed and proven — by a 2-minute smoke run, not by hope

Between 17:05 and 17:08 CDT someone ran `smoke-refactor-check` (200 rows, 2-min time-box) on the
Spark: **clean finish with receipt, eval, and a saved adapter on disk**. The corpus was also
fixed in-flight from the audit's own findings — training now reads an **escaping-repaired** copy
with **system-prompt augmentation** (the "every row shares one templated system prompt" defect),
and a corpus-safety audit receipt exists.

## 3 · The full pre-flight gate now passes — numbers, not vibes

`bash check.sh --full`, run ~20:10 CDT, **RESULT: PASS** on all five steps:

| gate | result |
|---|---|
| compile + pyflakes (10 scripts) | clean |
| evaluation contract discriminates | BRICK/LEAKER/MUTE rejected, DEFENDER promoted |
| split verification (Spark, real corpus) | **PASS** — 178 of 52,524 rows (0.34 %) dropped for teaching attack production; 62 near-duplicate prompts collapsed; **52,284 rows, 51,784/500 split, deterministic, prompt-level disjoint** |
| leakage audit @ 0.80 threshold (Spark) | **VERDICT: no near-duplicate leakage** — max similarity 0.773; 40 rows ≥ 0.60 listed with worst-pairs shown (documented, non-blocking) |

The launch path is now: owner approval → one command. Nothing else blocks.

## 4 · The research brief is complete — with its citations verified this time

`logs/flash-research-brief.md` is `status: complete`, all five sections. Sections 1–2 are the
dead run's own on-disk text; **Sections 3–5 were assembled from its reasoning stream**, where the
model had drafted them minutes before dying. Assembly re-verified every citation: three arXiv IDs
confirmed (SecAlign 2410.05451 — note its real title is about prompt injection, not jailbreak;
data-constrained scaling 2305.16264; domain CPT 2311.08545); **two draft IDs failed verification
and their claims were re-anchored rather than published unchecked** — the exact failure the flash
runs kept warning about, caught this time by checking instead of trusting.
Headline conclusions: two-stage method (full-parameter domain CPT with 35–45 % general replay →
SFT→DPO), eight numeric ship/no-ship gates with non-waivable harm gates, and the program's
highest-risk assumption — that security CPT buys *transferable reasoning* — assigned a < 10
GPU-day falsification pilot (500 M/1 B ladder, ≥ 30 % frontier-gap-closure rule) that runs
**before** any corpus scale-up spend. A Codex review boundary is stated: training-method items
open to Codex objection with no design authority; licence/receipt/release/ops out of scope.

## 5 · The launcher now has a completion gate — the check whose absence killed 12 sessions

`run-flash-session.sh` previously gated on `GET /v1/models`, **which returned 200 throughout the
entire wipeout while every chat completion timed out.** The gate now issues a real
`Reply with the word OK` completion (3 attempts, 90 s cap) and refuses to launch without it —
formalizing the manual smoke test that correctly caught the sick endpoint today. Two endpoint
facts were discovered while verifying it: `/v1/models` needs the auth header (401 without), and
thinking mode can consume the whole completion budget before visible output — the gate accounts
for both. **Current endpoint health: probe passes first try in ~3 s** — healthy now, against
today's evidence of intermittent death. The crashed `resume-flash-session.sh` was deleted earlier
today; its two bugs (`$3: unbound variable`, /proc races) are on record, and the launcher gate
makes the resume watcher largely unnecessary.

## 6 · Position, stated plainly

Everything that could be done **without the GPU** is done: audit delivered, brief complete and
citation-checked, full gate green, launcher hardened, v1's death explained. The only remaining
step is the one the owner reserved: **launching the 170-min v1 run** (measured 0.92 s/sample ⇒
~20 % corpus coverage, receipt records coverage — the README's own time-box design). It is
**not started**; awaiting explicit approval. One honest caveat for the record: v1 is the SFT step
on the corpus §1 of the brief flags as templated — v1's purpose is pipeline proof and a baseline,
and its scores should be read as pipeline evidence, not method evidence.

**Needs your decision:** launch v1 now on the Spark (single command, ~3 h, GPU time), or hold.
