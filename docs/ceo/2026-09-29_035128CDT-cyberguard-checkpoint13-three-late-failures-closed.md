# CyberGuard v2 — checkpoint 13: the evaluation would have failed three separate times; all three are closed

**One line:** pre-flighting the C24 contract instead of waiting for it found **three independent defects that
would each have fired late, after the training window was spent** — an empty scoring authority that would have
manufactured a safety finding, a merge-equivalence gate whose outcome depends only on decode length, and a
harvest that demanded an artefact it never collected. All are fixed and gated. Separately, the repaired training
run is now **proven to be learning**, and an independent reviewer has cleared the chain.

## 1. The host-side scoring authority was empty (would have invented a failure)

The scorer's own selftest had only ever been run locally. Run **on the hosts** for the first time it **FAILED on
both**, with byte-identical files — so the difference was data. `attack-stix.json` (MITRE's 53.8 MB export) and
`build_mixture.py` were absent on both machines, leaving the authority that decides whether a cited ATT&CK
technique id is real **empty**. `run_battery.py` calls it on the host before scoring every identifier, so
**every legitimate citation — `T1071.001`, `T1071.004`, `T1558.001` — would have counted as a hallucination**.

That is a false failure in the strict direction, and it would have put a **manufactured safety finding** in the
verdict, plausibly driving a rebuild on an artefact of a missing file.

Why nothing caught it: the contract checked the driver and the scoring **locally**, while the scoring that
produces the verdict runs **on the hosts**. Nothing compared the environments. Now: stage 0b syncs every host
module and the authority; the host check asserts the authority matches a **receipted sha256 and counts**
(`dc1639ca…`, 697 valid + 161 deprecated); and the scorer selftest plus both driver checks run **host-side**.
Verified identical on all three machines.

## 2. The merge-equivalence gate measured decode length, not equivalence

The gate required `gen_exact_mismatches == 0` and token-F1 ≥ 0.99. Measured on the real adapter:

| decode length | loss delta | top-1 agreement | exact mismatches | F1 min |
|---|---|---|---|---|
| 256 tokens | 0.0001 | 100 % | **4 of 4** | 0.675 |
| 48 tokens | 0.0001 | 100 % | 1 of 6 | — |
| 32 tokens | 0.0001 | 100 % | **0 of 4** | 1.0 |

The outcome is a function of **how long the decode is**, while the measurements that speak to the merge never
move: `merge_and_unload()` evaluates `W+BA` once in bf16 where the unmerged path evaluates `x@W + (x@A)@B`
separately, and greedy decoding amplifies the difference. It would have **aborted the contract at stage 2**.

Replaced with a measurement that constrains the whole continuation: **teacher-forced per-position agreement
over the assistant span** (the surface the benchmark scores), with a **measured negative control** — merged vs
unmerged **0.9882**, merged vs the base model **0.5996**, a separation of **0.389**. The gate is grounded in that
gap rather than fitted: agreement ≥ 0.95, ≥ 20,000 positions, separation ≥ 0.20, zero first-position
disagreements. The free-running generation statistics are now **reported, never gated** — they measure
amplification, not equivalence. Verified in five directions, including proving a clause that could never fire is
actually live.

## 3. The harvest required an artefact it never collected

`harvest-v2.sh` has always failed closed on `docs/VERDICT-v2.md`, but **nothing ever copied the verdict into the
harvest** — so the requirement was unsatisfiable and a perfect run exited 1, which the contract turns into
**exit 8 at the very last step, after the verdict was written**. Proven in isolation with the verdict on disk:
still reported missing. Fixed and unit-tested three ways.

## The run is proven to be learning (an independent reviewer's outstanding gap)

Review #14 accepted the repaired resume as *trainable* but withheld the learning claim until a nonzero
optimizer-applied weight change was shown. At the first step-500 checkpoint, on both arms:

| arm | checkpoint | tensor movement | distinct grad_norm values |
|---|---|---|---|
| arm A | `checkpoint-500` (03:48:57) | ~1.0 L2 on top tensors | **48** |
| arm B | `checkpoint-500` (03:43:30) | ~1.0 L2 on top tensors | **48** |

Against the frozen run's `trainable params: 0`, `grad_norm 0` and **zero** distinct gradient values. This is
receipted, and the contract re-proves it on the final artefact.

## Independent clearance: obtained, and the gate that records it was broken

Review #17 cleared the chain on the registration amendment: *"The registration objection is resolved. No
additional training-validity blocker is established by this delta."* **`CHAIN CLEARED a91da33296ab`.**

Recording it exposed two defects in the marker gate itself: it globbed a filename pattern that could **never**
match this project's reviews, and once fixed it matched a **prompt** file — prompts contain the prescribed
clearance line as their output format, so a prompt could have cleared the chain with no reviewer involved. Both
fixed; verified four ways.

**The marker is deliberately still absent:** it is revision-bound and the revision moved after the clearance (the
equivalence-basis change now under review #18). Writing it would bless a revision nobody cleared.

## Cost

Unchanged and within the owner's authorization: **28.06 GPU-h spent, worst case 47.06 of 48** (24 h × 2). No
spend beyond it. Training continues in lockstep; nothing above has been charged to the evaluation yet.

## What is open

* Review #18 in flight on the equivalence basis (the third and, so far, best-grounded version).
* The evaluation contract runs at 12:10 after training stops at 12:02; `VERDICT-v2.md`, the checksummed harvest
  and the gate report do not exist yet, so the objective is not complete.
