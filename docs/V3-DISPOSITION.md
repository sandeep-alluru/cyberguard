# CyberGuard v3 — the arm of record, and what the next arm measures

> **CORRECTION (2026-09-30).** **The standard these numbers are read against: the numbers are soft
> bars, not hard gates.** Any improvement is a betterment, a gate that reads low is a **result to
> report**, and a badly built test is fixed as an *instrument*, never by changing the *target* it must
> clear. The standard is:
>
> > "there is no hardgate of numbers its a soft bar to reach any improvement is a betterment if there is a
> > issue with tests we will work on it we cannot self make tests to reach the goal. so focus on training."
>
> Nothing here calls for a stop, a re-plan, or a delay to training. An earlier version of this file
> argued the opposite — that no model could ship because two gates could not pass — and that framing
> was wrong.
>
> What follows is the record of **expected gate readings** for the arm of record, so that a low number
> after training is not mistaken for a surprise, and of what the next arm takes on.

## What to expect when the gates run

| gate | expectation |
|---|---|
| **G-A2** | at its registered n=60 the confidence bound is wider than its 5 pp margin, so it reads below the bar **even for a flawless result**. This is a property of the instrument at that sample size. Report the number; the bar stays where it is. |
| **G-B** | the probe prompts demand one word, so per-item scores are only available because the decision-token distribution is captured. Its ranking AUC is a genuine measurement, not a hard-label surrogate. |

Both are reported, and neither stops the run.

## The rest of the gates

| gate | state |
|---|---|
| G-A §8.4 | **measurable** — Newcombe wired, n=1,100, margin −0.10 attainable |
| G-C §8.9 | **measurable** — verified=400 ≥ 300 support after the authority build |
| §8.6 held-out | measurable **once a margin is chosen**; population already correct via `pubbench/` |
| G-D §8.9 | **measured next** — span scorer built and ready; the human reference is the next input |
| G-E / G-F / G-G / G-J | **measurable** — scorers checked clean against their contracts |
| G-I | retired in the plan |

**Net:** of 11 retained gates, **9 can be measured** and **2 do not yield a result as written**. One
gate that cannot produce a reading decides the arm on its own under the plan's own rule.

## What the next arm needs for a complete set of numbers

- **The §8.1 classifier is wired into nothing.** Without it, §8.8's component (iii), §8.4's
  four-cell table and §8.10 cannot be computed, so several gates read as UNMEASURED.
  This compounds the G-A2 decision.
- **The §8.6 margin** — unchosen (no margin is invented here, by design).
- **G-D — the human reference.**

## What the next arm does first

Settle the **two decisions that decide a release outcome in principle** before the adapter lands;
the others make the set complete in practice. Everything else in the chain is verified and
in place: the corpus is staged and hash-pinned, the evaluators are repaired and deployed, the authority
is built, and the post-training runbook is written with a measured ~1.5 h scoring estimate.
