# OVER-ENGINEERING REVIEW — what in this plan costs more than it buys

**Written because the owner asked for it, and treated as a self-critique rather than a defence.** Each
item: what it costs, what it buys, and the decision. Cost is in GPU-hours, wall-clock, or *plan
complexity* — the last being real, because every instrument in the plan is another thing that can be
wrong (this session produced three defects in the audit tooling alone).

## CUTS — remove; the thing bought is not worth the thing spent

| # | what | cost | what it actually buys | decision |
|---|---|---|---|---|
| C1 | **`dual-use-boundary` (160) and `defensive-redirect` (180) rows** in the refusal set — 340 of 1,200 rows, and at weight ×8, **2,720 of the 9,584 refusal slots** | those slots displace genuine refusal examples; audit showed they are ordinary defensive Q&A wearing a boundary label | nothing the refusal intervention needs — the categories were my own invention, not derived from a measured failure | **CUT at the next rebuild**; reallocate to offensive-refusal variety and unknown-answer support |
| C2 | **`yaml-report` (200 rows, 400 slots)** in the format set | 200 of 1,500 rows | the audit never validated it, and no gate tests YAML-report output (G-B tests one-word, G-E tests Sigma) | **CUT at the next rebuild** |
| C3 | **G-H judge-uplift battery** | requires a **judge model that does not exist**, is not designed, and is explicitly not costed | a gate that cannot be run this cycle | **CUT from v2.0**; recorded as UNMEASURED, with the independent rubric (already built and used in v1) as the substitute instrument |
| C4 | **U9 gate-8 process-eval unit** | an entire unit plus a battery (200 generations) and a deliverable (`GATE8-protocol.md`) that does not exist | no protocol has been authored; the unit is a stub carrying an invented item set | **CUT from v2.0 scope** → v2.1, with the reason stated |
| C5 | **U11 CPT throughput probe** | a unit + a deliverable (`v2/cpt_probe.py`) for a **deferred** decision about a version we may not build | pre-sizing v2.1 inside the v2 critical path | **MOVE to v2.1 scope** |
| C6 | **C8/C16 checkpoint evaluation on both arms, unconditionally** | 4,400 generations ≈ 1.2 h plus a saved-adapter workflow and 4 extra comparison cells | nothing confirmatory — §7 already declares them descriptive and forbids their use for selection | **REDUCE to diagnostic-on-failure**: evaluate C8/C16 **only if G-A fails at C24**, to distinguish a cliff from a trend. Otherwise C24 stands alone |

## KEEPS — examined and genuinely justified

| item | why it stays |
|---|---|
| **the second training arm** | it is the causal test, it rides free on the idle second machine, and it is what makes "the refusal data caused it" a measurement instead of an assertion. It cost a design argument, not a GPU-hour |
| **G-J chat retention** | 400 generations to verify the owner's stated chat requirement, and it is the guard against buying refusal by destroying general behaviour |
| **the receipt-bound data gate (U13)** | it exists because **three rebuilds this session each reintroduced a defect**. Without it, the fourth rebuild silently voids the clearance |
| **separate marginal claims, no multiplicity correction** | the *simpler* option; a correction would be more machinery for the same conclusion |
| **`plan-validate.py`** | six mechanical checks; it caught a real defect on its first run |
| **the trace miner / CRAFT corpus** | already paid for; it is what turned this session's mistakes into reusable rules |

## PROCESS — the expensive pattern, named

**Confirmation reviews #11, #12 and #13 produced almost entirely arithmetic and wording corrections, not
design objections.** Three full review rounds for fixes that a delta check would have covered.

**Decision:** full independent review only for **material design changes** (new arm, new gate, changed n,
changed mixture composition); wording/arithmetic fixes get a **delta check** limited to the amended
sections. The rule that produced the value — *a reviewed artifact that is not the shipped artifact is not
reviewed* — is preserved by hashing the delta, not by re-reading the whole document.

## Net effect if C1–C6 are applied

| | before | after |
|---|---|---|
| gates in the battery | 11 (G-A…G-J + gate 8) | **9** (G-H and gate 8 moved out with reasons) |
| evaluation generations | 29,008 ≈ 8.12 h | **≈ 24,200 ≈ 6.8 h** (C6 + C3 + C4) |
| units in v2 scope | 13 | **11** (U9, U11 → v2.1) |
| authored refusal rows | 1,200 (4 categories) | **860 (2 categories)** — all of them refusal-relevant |
| missing deliverables | 5 | **3** (`harvest-v2.sh`, `serve_guard_check.sh`, `MIXTURE-V2.md`) |

**Nothing here weakens the two questions the run exists to answer** — does the designed fix restore
refusal behaviour, and is the substitution the cause. Every cut is to instrumentation that no gate
consumes.
