---
title: CyberGuard v2 checkpoint 1 — owner authorizes 24 hours and both Sparks; experiment re-cut from one arm to two, with the control arm's confound caught before launch
issued_at: 2026-09-27T23:15:00-05:00
project: CyberGuard
status: current
kind: decision
supersedes: 2026-09-27_203600CDT-cyberguard-v2-plan-ceo-brief.md
---

# Checkpoint 1 — the authorization, and what it changed

**One line:** you gave 24 hours and both machines; the single-arm design became a **two-arm parallel
experiment with a causal control**, and the hardware check that followed found a private 1 ms link
between the nodes that makes distributed training possible — which I deliberately did **not** use,
because a control arm buys more than a second epoch does.

## The authorization of record

> *"you can train for 24 hours the spark x2 is all yours you can stop the model being served and use
> the full capacity of both machines."*

This supersedes the ≤14 h single-machine ceiling that the previous plan had asked for, and it removes
the training/serving contention that was the original reason for a bounded box.

## What the hardware check found

| fact | measured |
|---|---|
| both nodes | DGX Spark GB10 |
| direct link | `10.10.20.0/24` on `enP2p1s0f0np0`; tailscale reaches the peer over it in **~1 ms** |
| `spark-8cf2` | hosts `spark-flash-next.service`; **passwordless sudo available** |
| `spark-40ee` | runs the `ggml-rpc-server` worker that shares its GPU |
| idle state | both GPUs 0 % at check time |

## The design decision

| | Arm A (`spark-40ee`) | Arm B (`spark-8cf2`) |
|---|---|---|
| training data | the designed mixture (refusal rows at weight ×8) | **the same mixture with those 1,200 rows replaced in place by matched non-refusal defensive Q&A** |
| what it answers | does the designed fix restore refusal behaviour? | **is the substitution the cause?** |
| duration | 24 h continuous, checkpoints at C8/C16/C24 | identical, in parallel |

**Why not 2-node data-parallel on one arm**, despite the fast link: one machine already reaches
**~109 % of an epoch in 24 h** (measured after the data was built), so a second machine buys a second
epoch of the *same* mixture — worth less than a causal control. The owner may override this in one line.

**The confound I caught before launch:** the control was first written as "Arm A minus the refusal
set". That shrinks Arm B's epoch by 9,600 presentations, so at 24 h Arm B would have seen >100 % of its
epoch while Arm A saw ~95 % — a *coverage* asymmetry that would have confounded the very comparison.
The replacement-in-place design removes it. The claim is still only a **substitution contrast**, not
proof that refusal data alone is causal (the replacement differs in task, prompt distribution and
answer style too) — and the plan says exactly that.

**Cost:** 48 GPU-hours of training (24 h × 2, in parallel) + ~8.1 h of batteries + 1.5 h benchmark =
**≈57.6 machine-hours, ≈28.8 h balanced elapsed**; 30 h is an allowance, not a derived number.

**Service window:** the Flash-Next endpoint is stopped on **both** nodes for the duration and restored
afterwards with a real completion probe (not a liveness ping — the runbook lesson). Nothing is stopped
until the data is signed off.
