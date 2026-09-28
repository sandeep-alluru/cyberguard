---
title: CyberGuard v2 checkpoint 5 — the 24-hour plan was blocked by the served model's memory and is now unblocked; review #5 withheld data clearance again and its two objections are being fixed
issued_at: 2026-09-28T04:00:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-28_010000CDT-cyberguard-checkpoint4-data-items-closed.md
---

# Checkpoint 5 — the real blocker was hardware, not data

**One line:** the data checks are strong (audit PASS, leak scan CLEAN, receipts bound), but two independent
reviews in a row have correctly refused clearance on *completeness of the supervision text*, and this
checkpoint also found and fixed a hard blocker that would have killed the run on launch: **the machine
serving your own Flash-Next model had committed all but 1 GB of its GPU memory, so the training arm on that
host could not have allocated a single layer.**

## What was verified since checkpoint 4

| item | finding | state |
|---|---|---|
| Two training hosts | both are DGX Spark GB10; `spark-40ee` (arm A) and `spark-8cf2` (arm B) are reachable, have the arms, and have no trainer running | **verified** |
| Arm integrity | both arms hash-verified **on the hosts**, byte-identical to the audited revision (8/8 stored hash entries agree) | **verified** |
| Arm B host readiness | it was **missing the base model, the Python environment and the config file entirely** — it had never been provisioned for training | **fixed** (see below) |
| Audit / leak scan | audit **PASS (0 failures, 0 warnings)**; leak scan **CLEAN, 0 findings in 162,290 rows**; receipt **RECEIPT-BOUND** | **verified** |
| Independent review #4 | **withheld** clearance: 10 control answers ended mid-thought; the leak scanner missed one padded prompt copy | **fixed**, re-verified |
| Independent review #5 | **withheld** clearance again: 38 incomplete targets (headings, colon-ended introductions, a truncation inside code); my control answers are slot-matched but **not topic-matched** | **fix in flight** |

## The blocker: "use the full capacity" collided with your own model

Your instruction was to stop the served model and take both machines. Measuring first, rather than assuming:

| host | free GPU memory before any work | what was holding it |
|---|---:|---|
| `spark-40ee` | 31.4 GB of 130 GB | the two-node RPC pool's model layers |
| `spark-8cf2` | **1.0 GB of 130 GB** | the Flash-Next server: 512k context, 2 slots |

A 4B LoRA needs roughly 15 GB. On `spark-8cf2` it would have failed at the first allocation.

Two further facts decide what to do about it:

1. **v1's throughput basis was measured on a free GPU.** The Flash-Next service was down for v1's entire
   measured window (no service start between the previous evening's stop and 19:16; v1 trained 01:29–04:20).
   The 0.9683 s/sample that every budget number in the plan rests on is therefore valid exactly when the pool
   is down — and would have been optimistic otherwise.
2. **Stopping the pool does not touch my supervision.** My own turns are served by a hosted provider, not by
   the local pool. I verified this before acting rather than assuming it.

Consequence: Phase 5 now stops `spark-flash-next` (arm B host) and `spark-rpc` (arm A host), proves the
memory is actually free, runs the arms, then restores both and gates the restoration on a **real generation**
from the service — not on the port being open. That probe was hardened after it first passed on an *empty*
answer: with `max_tokens=8` the whole budget went to the model's reasoning channel. It now requires non-empty
text (and reports the generation rate).

## Arm B's host had never been provisioned

| missing | action | evidence |
|---|---|---|
| the 7.3 GB base model | copied host-to-host over the direct link at ~750 MB/s | **all five files hash-match** the source |
| a Python environment with `peft`/`trl` | built one with the **exact same versions** as arm A's host (torch 2.13.0+cu130, transformers 5.12.1, peft 0.21.0, trl 1.14.0, datasets 5.0.1, accelerate 1.15.0) | CUDA available, matmul ran, device NVIDIA GB10 |
| `~/.cyberguard-env` and the output directories | written; every path checked | resolved correctly |

Two arms on different library versions would have been an uncontrolled difference in a two-arm experiment, so
the versions were pinned rather than left to whatever installed.

## Review #5, and why it is right

Review #5 cleared the things I had fixed (hashes, the leak-scanner regression, token budgets, arm pairing)
and withheld on supervision completeness. Its central finding is correct and mechanical: my sentence-end
rule accepted a colon as an ending, so targets like `… ASSESSMENT OBJECTIVE: Determine if:` shipped as
complete answers; heading-only targets (`## Methodology for …`) shipped as answers; and a target whose text
opens a ``` fence without closing it shipped as an answer. It also showed my own predicate was wrong in both
directions — it accepted `Intl.` mid-citation while wrongly rejecting five *complete* answers that end
`…etc.`.

The second objection is a design question and it deserves your decision rather than my silent fix:

> The control arm replaces every refusal slot with defensive content. For the 5,600 offensive-refusal slots
> that substitution is now **topic-matched** (a cryptojacking refusal becomes cryptojacking defensive
> guidance). But the 4,000 remaining slots are *unknown-answer abstentions* ("which CWE is assigned to …"),
> where no topic exists to match; those become generic defensive answers instead. So arm B differs from arm A
> in refusal weighting **and** in what happens on unknown questions.

My recommendation, for your call: hold those 498 unknown-answer prompts **identical in both arms**. That
leaves arm B differing from arm A only in offensive-refusal behaviour, which is exactly what the primary
comparison claims to isolate, and it keeps the abstention measurement clean. It requires re-registering one
line of the design. The alternative is to accept the confound as pre-registered and state it in the verdict.

## Cost to date

| resource | spent |
|---|---|
| GPU-hours on either Spark | **0** |
| v2 training launched | **0** runs (nothing has touched the GPU; only memory reads) |
| wall-clock this session | ~5 h of preparation, review and repair |

The two-day delay is deliberate: every hour spent here is cheaper than discovering a mid-run data defect
24 hours into a 48-hour window.

## What is open

| # | open item | owner | exit condition |
|---|---|---|---|
| O1 | design call on the 498 unknown-answer prompts (recommendation above) | **owner** | decision recorded in `docs/SPEC-V2.md` |
| O2 | build 10 in flight: completeness rules + topic-matched control | me | arms rebuilt, audit PASS, leak CLEAN, new hashes staged |
| O3 | review #6 on the rebuilt arms | codex + Astra | written clearance, or findings dispositioned |
| O4 | Phase 5 launch: stop the pool, prove the memory free, smoke both arms, launch 24 h × 2 | me | both arms training, monitor armed, checkpoint 6 brief |
| O5 | checkpoint-6 reviews by Astra (standing cadence) | Astra | review filed per checkpoint |

Nothing has been trained, nothing has been served, and the evaluation contract is unchanged. The endpoint
remains untouched and v1 remains unserved, as decided.
