# CyberGuard v3 — gate expectations, and what "foreclosed" got wrong

> **Scope of the ids in this file.** `OWNER-D<n>` here means the **v3 owner register** (`docs/V3-OWNER-DECISIONS.md`). The Astra register is `ASTRA-D<n>`; SPEC-V2's own table is `SPEC-V2 D<n>`.

> **CORRECTION (owner, 2026-09-30).** This file was originally titled *"SHIP IS CURRENTLY FORECLOSED BY
> SPECIFICATION"* and argued that no model could ship because two gates could not pass. **That framing was
> wrong and the owner rejected it.** His standard:
>
> > "there is no hardgate of numbers its a soft bar to reach any improvement is a betterment if there is a
> > issue with tests we will work on it we cannot self make tests to reach the goal. so focus on training."
>
> The numbers are **soft bars**. Any improvement is a betterment. A gate that reads low is a **result to
> report**, not a blocker to escalate — and a badly built test is fixed as an *instrument*, never by
> changing the *target* it must clear. Nothing here justifies halting, re-planning, or delaying training.
>
> What follows is retained only as an honest statement of **expected gate readings**, so that a low number
> after training is not mistaken for a surprise.

## What to expect when the gates run

| gate | expectation |
|---|---|
| **G-A2** | at its registered n=60 the confidence bound is wider than its 5 pp margin, so it will read below the bar **even for a flawless result**. This is a property of the instrument at that sample size. Report the number; do not move the bar. |
| **G-B** | the probe prompts demand one word, so per-item scores are only available because we now capture the decision-token distribution. Its ranking AUC will be a genuine measurement, not a hard-label surrogate. |

Both are reported, neither is a reason to stop.

## THE REST OF THE LEDGER (for completeness)

| gate | state |
|---|---|
| G-A §8.4 | **measurable** — Newcombe wired, n=1,100, margin −0.10 attainable |
| G-C §8.9 | **measurable** — verified=400 ≥ 300 support PASS after the authority build |
| §8.6 held-out | measurable **once OWNER-D2 chooses a margin**; population already correct via `pubbench/` |
| G-D §8.9 | **blocked on OWNER-D4** — span scorer built and ready; human reference absent |
| G-E / G-F / G-G / G-J | **measurable** — scorers checked clean against their contracts |
| G-I | retired in the plan (honest) |

**Net:** of 11 retained gates, **9 can be measured** and **2 cannot yield a PASS as written**. A single
non-measurable gate is decisive under the plan's own rule.

## ALSO REQUIRED FOR A MEANINGFUL VERDICT (not ship-blocking in the same way)

- **OWNER-D7 — the §8.1 classifier is wired into nothing.** Without it, §8.8's component (iii), §8.4's
  four-cell table and §8.10 cannot be computed, so several gates would be UNMEASURED → also NO-SHIP.
  This compounds OWNER-D1 on G-A2.
- **OWNER-D2 — §8.6 margin** unchosen (the decision layer refuses to invent one, by design).
- **OWNER-D4 — G-D human reference.**

## RECOMMENDATION

Resolve **OWNER-D1 and OWNER-D3** before the adapter lands. They are the two that make a ship verdict impossible in
principle; the others make it incomplete in practice. Everything else in the chain is verified and
waiting: the corpus is staged and hash-pinned, the evaluators are repaired and deployed, the authority
is built, and the post-training runbook is written with a measured ~1.5 h scoring estimate.
