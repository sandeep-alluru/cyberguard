# CyberGuard v2 — checkpoint 15: both independent clearances obtained, and three defects found in the measuring instrument

**One line:** the objective's second requirement is now met — **Astra cleared the chain** and **Muse cleared the
frozen arms** — while independent review of the merged-vs-unmerged check found **three defects in the instrument
itself**, two of them in its own arithmetic, each of which would have let a real defect pass.

## The clearances the objective requires

| reviewer | scope | result | revision named |
|---|---|---|---|
| **Astra** (Codex) | the evaluation chain, on the registration amendment | `CHAIN CLEARED a91da33296ab` | the amendment revision |
| **Muse** (family-diverse) | the frozen training arms | `FROZEN ARMS CLEARED 35e9166fa0d4` | the frozen-arms revision |

Muse re-derived the overlap **itself** and reproduced the numbers behind its own earlier objection (300/300,
60/60, 99/100, 20/20 exact training-row overlap in the registered batteries), verified all five fresh instruments
are **0-overlap in both arms**, and closed its own BLOCKER under the owner's D12 decision. Both clearances are
receipted **with the revision each names** — neither is silently extended to later commits, because a clearance
for a revision that is not checked out proves nothing.

Muse's two minor findings were fixed: the plan of record claimed the fresh sets total **1,580** prompts when the
files hold **1,620** (verified: 1,100+300+60+60+100), and the registration rows carried **no inline pointer** to
the amendment that supersedes them. Its two carried caveats — the live loss-mask evidence is **one sampled batch
per host**, and the reported terminal LR is the **last logged** LR — are now stated in the verdict rather than
left in a log.

## Three defects in the measuring instrument, all found by review

The check asks a simple question: do the merged weights equal `base + scaling·(B·A)`? Three rounds of independent
review found the *apparatus* answering it wrongly:

| defect | what it would have let through | fix |
|---|---|---|
| the exponent was `floor(log2)` in float32, which **rounds up** just below a power of two | spacing **2× too large** → measured error **halved**, so a deviation beyond the 2-ULP bound **passed** | exponent taken from the float32 **exponent field** (exact); the logarithm is gone |
| subnormal spacing computed as `2⁻¹³⁴` where bf16's uniform subnormal spacing is `2⁻¹³³` | **both sensitivity controls doubled** — a matrix whose true separation is **61 ULP** reported 122 and passed a 100-ULP requirement | exponent clamped at the minimum normal exponent |
| the gate was a **fraction** of elements, and `NaN > 2` is `False` | a **single** corrupted weight was *detected* but discarded (fraction 9.5e-7); an **all-NaN** model reported fraction 0 and passed | gate on the **element-wise maximum**; non-finite weights **and comparisons** counted and gated at zero |

Each was demonstrated with an executed counterexample by the reviewer and is now a **regression test** in the
repository — including the reviewer's own constructed matrix re-derived against the corrected arithmetic. The
measurement as it now stands, on the real adapter:

| quantity | measured |
|---|---|
| worst merged weight vs the exact merge | **0.5 of a bf16 ULP** (half an ULP is the arithmetic's optimum) |
| elements compared | **3,633,315,840** over 252 matrices |
| non-finite weights / comparisons | **0 / 0** |
| control: a target module never merged | **4.14e37 ULP** |
| control: adapter mis-scaled 10 % | **4.14e36 ULP** |

The two controls moved from `8.27e36 / 8.27e37` to `4.14e36 / 4.14e37` once the subnormal denominator was
corrected — i.e. **the defect was inflating the reported separation of the real measurement by 2×**, not merely
affecting a contrived matrix.

## A failure mode eliminated by measuring instead of planning

Timing one real battery (100 probes, **925 s** with training contending for the GPU) showed the largest batteries
need **185 minutes** (`gG-gsm8k`, 1,200 probes) and **170 minutes** (`gA`/`fresh-gA`, 1,100 probes) against the
**90-minute** per-battery ceiling. The two largest would have been **killed**, failing the evaluation stage and
producing **no verdict** after the whole window. Ceilings raised to 6 h per battery and 12 h for the benchmark
stage. Every number is recorded with the measurement it came from.

## Hardening for an eleven-hour unattended run

* **each battery retries once** before failing (42 sequential runs sit on the critical path; one transient
  failure would otherwise cost the verdict) — verified in both directions;
* the schedule **re-runs the whole contract once** on a non-zero exit, with the failed attempt's outputs
  quarantined first — verified that a success does *not* trigger a wasteful second attempt;
* the **3-hourly checkpoints now verify the eviction** the plan requires (port 8093 closed, no serving unit
  active), which had only ever been confirmed by hand once. It ran in this checkpoint and reports eviction in
  force on both hosts.

## State and cost

Training healthy at M2: **arm A 1,409 steps (0.278 epoch), arm B 1,339 (0.264)**, both alive, GPU 95 %.
The evaluation contract runs at **12:10** after training stops at 12:02; its dry-run renders all **14 stages**,
and the local verdict chain rehearsal passes.

Cost is unchanged and inside the owner's authorization: **28.06 GPU-hours spent, worst case 47.06 of the 48**
(24 h × 2). The evaluation is the plan of record's separately budgeted cost (28,808 generations ≈ 8 h across both
machines), and the measured throughput corroborates it.

## What is open

* the merged-vs-unmerged criterion is under its **eighth** review; six of seven previous rounds found a real
  defect, three of them in the instrument, which is why the loop continues;
* **D2 remains declared NOT MET** (228 distinct control prompts vs ≥1,000; 15.5 % length gap vs ≤10 %), receipted
  and carried in the verdict as an intrinsic asymmetry of the substitution design;
* `VERDICT-v2.md`, the checksummed harvest and the gate report do not exist yet, so the objective is not complete.
