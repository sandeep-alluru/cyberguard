# CONSOLIDATED PICTURE — CyberGuard v4 + DSH harness

**Prepared for the owner, 2026-10-05.** This is the single consolidated view after the multi-topic session.
Nothing here has been executed. **D9 execution freeze is ACTIVE.**

Sources: Astra's consolidation ruling, the 18-entry decision register, `docs/ACTIVE-PLAN.md`,
`docs/PLAN-OF-RECORD.md`, `docs/dsh/OWNER-DECISION.md`, `docs/dsh/ARCHITECTURE.md`, `docs/FAILURE-REGISTER.md`.

---

## 1. WHERE WE STAND — two workstreams, interleaved

**A. CyberGuard v4 (the model).** v3 is research evidence, **not shippable**. The plan is a two-arm
warm/fresh recovery pilot; its selected checkpoint goes straight to product qualification; failed pilot means
**NO-SHIP** with no automatic restart. Ceilings: 260 GPU-h, 24 CPU qualification-h, 80 worker-h, 800
aggregate human-review-h, $0 rented GPU/API, 45-day target from activation.

**B. DSH harness (the machinery).** Root failure ruled: **bypassable enforcement**. Governance exists; the
cheapest route around it was always available. Rulings: keep worker shell/writes/compute, move reviewer
**credentials** outside worker control, mentor may hold dangerous permissions under a **separate identity**
with authority from an **operator record** — never from a worker invocation.

| measured | value |
|---|---|
| total tokens consumed | **29,532,513,003** |
| of 3-trillion budget | **0.9844 %** ≈ **1 %** (you said 0.10 % — it is ~10× more) |
| cacheRead share | **98.87 %** |
| decision register | 18 entries — 1 executed (D1), **1 active (D9)**, 16 open |

---

## 2. RESEARCH LEADS — captured, zero weight, nothing built

Two external sources were reviewed at your request. Both are recorded, neither changes anything.

**a) `github.com/empero-org/homebrew-ai`** — guided fine-tuning agent.
- **Useful as a reference, not as our training tool.** Do not install on the training host.
- **Borrow one concept:** display the **actual tokenized inputs and labels** the trainer consumes —
  masked context vs loss-bearing targets, special tokens, termination, sequence length — inside our existing
  **U3/P5 masking-and-gradient preflight**, using our own tokenizer/template/collator.
- Rejected: its `clean_dataset` semantics (would silently reduce support; our rejection-only policy stands),
  its recipe selection (our recipe is frozen), its cannot-skip confirmation claim (**unmeasured**),
  its pre-run estimator (planning only, never a reason to change batch/steps).
- Repo facts: **8 hours old, 3 commits, no releases, not on PyPI**, custom revenue-capped licence.

**→ ADOPTED INTO THE PLAN — training-input display (the one mechanism borrowed).**

| field | value |
|---|---|
| **Deliverable** | Display the **actual tokenized inputs and labels the trainer consumes** |
| **Must show** | **masked vs loss-bearing positions** · **special tokens** · **termination** · **sequence length** |
| **Where it lives** | Inside the **existing U3 / P5 masking-and-gradient preflight** — not a new stage, not a new tool |
| **Must use** | Our **own** tokenizer, chat template and collator — **not** a second renderer |
| **Owner** | Worker implements; Astra accepts |
| **Exit** | Preflight shows the real tensors fed to the loss, per sampled row |
| **Explicit limit** | A visual sample **never certifies all 8,000 rows** — it is a preflight, not a qualification |

| rejected from the same repo | why |
|---|---|
| `clean_dataset` semantics | would silently reduce support; **rejection-only policy stands**; shortages block training |
| recipe selection / hardware auto-fit | **our recipe is frozen**; report a mismatch and stop |
| cannot-skip confirmation claim | **UNMEASURED**; a UI claim is not demonstrated mediation |
| pre-run memory/time/cost estimator | planning information only — **never** a reason to change batch, sequence, steps or budget |

| repo facts recorded | |
|---|---|
| age at review | **8 hours** |
| commits | **3** |
| releases | **none** (not on PyPI) |
| stars / forks | 100 / 10 |
| licence | custom revenue-capped (MIT under $2M monthly revenue) |
| **installation on the training host** | **NOT AUTHORIZED** — requires immutable revision, reviewed dependencies, an independently accepted execution boundary, and real-stack evidence that the registered parent, config, rendered tokens, loss masks and checkpoint behaviour are preserved. **Review must precede training-host access.** |

**b) arXiv:2608.05643** — *"Refining Over Resampling: Test-Time Self-Correction for LLM Reasoning"*.
- **Inference technique. It trains nothing.** Relevance to the training recipe: **nil**.
- Real method: verifier-**free** breadth–depth refinement — sample N rollouts, iterate self-critique +
  self-correction D times, aggregate by plurality vote. Best reported N=8, D=4. Weak models gain most.
- Astra's ruling: **selection ≠ certification.** A vote may choose which answer we evaluate; it never counts
  as confirmation of correctness. Model agreement stays at **zero acceptance weight**; D7/D11 unchanged.
- Astra **withdrew** the claim that two models are necessary, and confirmed **its own independence is
  "weakened, not satisfied"** — its title supplies authority, not measured accuracy.
- One **research candidate** kept, not implemented: **critique-conditioned revision**.

---

## 3. ORDER OF IMPLEMENTATION

**The chain:** repair and verify the machinery → satisfy activation, backup, staffing and assessment
prerequisites → restore evidence → qualify data → run the pilot → qualify the selected checkpoint and
package. A failed pilot or qualification ends in **NO-SHIP**, with no added training.

| # | Step | Owner | Cost | Exit |
|---|---|---|---|---|
| **1** | Reconcile operating documents (credential-boundary + separate-identity rulings into the approval text) | Astra specifies; operator records | existing worker allowance | strict ledger validation passes; DSH `baseline` checks scope |
| **2** | Establish repair baseline; preserve originals; verify identity + home-patch hash; inventory actual review entry points | Operator + worker; Astra reviews | zero GPU | `check_enforcement.py baseline` |
| **3** | Repair local D18 controls (packet checks, failure propagation, accounting, routing) | Worker; Astra accepts | zero GPU/API | `check_enforcement.py boundary` |
| **4** | Implement + verify the corrected DSH boundary (worker keeps shell; credentials protected; mentor separate identity; GB10 covered) | Operator installs; Astra accepts | zero GPU | `check_enforcement.py isolated` |
| **5** | Isolated rollout + restricted canary; **home patch unchanged; external sends disabled**; rollback exercised | Operator; Astra accepts | existing labor; zero external calls | `check_enforcement.py canary` |
| **6** | Verify owner-supplied backup + restoration; finish **U0** | Worker/operator | existing | `recovery/pipeline.py check-contract` |
| **7** | **D6 restoration** — re-judge lost HarmBench vectors, re-score FRR | Worker | existing | `check-evidence` |
| **8** | **U2** — qualify the 8,000-row dataset (4,000 domain / 2,400 legit / 800 harmful / 800 general) | Worker + reviewers | existing | exact stratum counts; shortages **block** |
| **9** | **U3/U4** — two-arm warm/fresh pilot from the selected checkpoint. **Includes the adopted training-input display** inside the existing masking/gradient preflight (masked vs loss-bearing, special tokens, termination, sequence length, our own tokenizer/template/collator) | Worker | existing GPU ceiling | registered public benchmarks + preflight shows real loss-bearing tensors |
| **10** | **U5/U6** — qualify the selected checkpoint on both surfaces | Worker + reviewers | existing | paired tests, both surfaces |
| **11** | Package (BF16 merge + Q4_K_M), hard gate | Worker | existing | `pipeline.py check-release` |
| **12** | Ship, or terminal **NO-SHIP** with recorded cause | Astra; worker | remaining only | `pipeline.py check-verdict` |

Milestones remain activation-relative: U0/U1 by day 5, U2 by day 12, U3/U4 by day 25, package or NO-SHIP by
day 45. **Targets, not forecasts.**

---

## 4. DECISIONS ONLY YOU CAN TAKE

**1. Authorize the corrected operational repair and name its operator?**
Authorize (recommended, *after* the document incorporates the later rulings) / Hold.
**Do not sign the contradictory current version** — its opening clauses approve a **withdrawn** design.

**2. When to release D9?**
Keep frozen through machinery acceptance and resource/backup readiness, then release explicitly.
**A verbal "go ahead" alone does not resolve the register or the missing gates.**

**3. Who supplies the human reviews?**
**Name and fund 2 independent cybersecurity-competent reviewers + a 3rd adjudicator**, before activation.
Not staffing them blocks model acceptance. Agents cannot replace these people.

**4. Where does the off-machine backup go?**
**Supply an existing company-controlled destination + operator access**, authorizing repo history **and
required ignored/untracked evidence**, followed by restoration verification. No destination → U0 and D6
blocked. A source-only remote does not satisfy it.

**5. Commit owned hardware and labor within existing ceilings?**
Commit GB10, Linux CPU workstation, named operator/worker availability, reviewer funding, cost rates —
**only after remaining allowances are reconciled**. Ceilings are not cost estimates.

**6. How is mandatory external assessment funded?**
**Verify existing entitlement at no additional API charge** with explicit request limits (recommended);
otherwise retain $0 and keep affected advancement blocked. No priced amendment is granted here.

*No owner decision is required on datasets, model settings, sample sizes, parsers, metrics or thresholds —
those are registered technical decisions.*

---

## 5. OPEN QUESTIONS, WITH RECOMMENDATIONS

| question | known / UNMEASURED | recommended path |
|---|---|---|
| Are the machinery controls effective? | scripts exist; **mandatory mediation UNMEASURED** | steps 2–5; a script's existence is not enforcement |
| Can the junior do each task? | routing specified; **capability record absent** | build the per-family record from independently checked artifacts; verify at the three checkpoints |
| Can the mentor execute safely? | ruling exists; **deployment UNMEASURED** | operator implements; a worker invocation cannot grant authority |
| What did CyberGuard actually consume? | integers sum to 29,532,513,003; **attribution/dedup/billing unresolved** | reconcile provider request IDs + bills; retain as supplied accounting, not reconciled spend |
| Is the percentage right? | **settled: 0.9844171 %** | keep corrected arithmetic; proves neither provenance nor cost |
| Can JEV run at $0? | **availability/entitlement unverified**; D18 prohibits calls | verify entitlement first; missing coverage blocks dependent advancement |
| Does JEV improve detection? | **calibration + incremental benefit UNMEASURED**; weight zero | keep zero weight; calibration is not on this critical path |
| Were prior JEV answers valid? | receipts not inspected | inspect questions/evidence/answers; **no 0.95 threshold exists** |
| Can humans finish in 800 h? | **25,500 initial reviews**; throughput UNMEASURED | measure actual time. 800 h ÷ 25,500 = **112.94 s per review** before other obligations |
| Can damaged evidence be recovered? | HarmBench vectors missing; FRR defects | U1 reconstructs full populations on original instruments |
| Do evaluator defects affect results? | budget enforcement, HarmBench labels, result preservation unresolved | reproduce against actual paths; allow "not a defect" |
| Are instruments available? | Berkeley unavailable (D8); BFCL zero release weight (D12) | U0 maps each metric to its pinned instrument; missing ⇒ blocked |
| Can sources yield 8,000 qualified rows? | **qualified inventory does not exist** | U2 exact strata; unresolved rights bar a row |
| What contamination claim is supportable? | inherited v3 exposure **UNMEASURED** | disclose inherited limits; never claim corrective training erases exposure |
| Does system-prompt omission explain v3? | sensitivity **UNMEASURED** | **do not launch D17's diagnostic** — specified, unauthorized, unnecessary |
| Will warm or fresh work? | neither arm has evidence | the experiment decides; neither passing = NO-SHIP |
| Will the checkpoint meet the product contract? | **UNMEASURED** | U5/U6 both surfaces, all representations |
| Will the download preserve quality? | merged/Q4 equivalence, RAM, size, speed **UNMEASURED** | U6 on exact artifacts, both host types |
| Will this save money / finish in 45 days? | **both UNMEASURED** | record real costs; update forecasts from measured throughput |

---

## 6. WHAT IS BLOCKED, AND ON WHAT

| item | blocked by | who clears |
|---|---|---|
| Broader DSH installation | reconciled scope + exact authorization | Astra prepares; **owner authorizes**; operator installs |
| DSH acceptance | missing implementation + evidence | worker/operator; Astra accepts |
| Consequential mentor execution | separate identity, operator grant, verified confinement | operator |
| Live reviewer/JEV calls | authorization, known allowance, valid exposure | **owner** (resources); Astra/operator (implementation) |
| Model execution | D9 + exact stage permissions + verified machinery | **owner** releases |
| U0 | missing pipeline, resources, instrument checks, D13 restoration | worker/operator + **owner-supplied resources** |
| D6/U1 | U0 + successful off-machine restoration | operator + worker |
| Teacher generation | U1 + qualified inputs + D4 authorization | worker; Astra accepts |
| Pilot training | exact qualified 8,000 rows + valid preflight | worker/reviewers; Astra accepts |
| Pilot acceptance | complete public results + JEV coverage + **7,500 human reviews** + adjudication | worker, reviewers, Astra |
| Product qualification / package | passing pilot checkpoint | Astra applies selector |
| Additional training | **no authorization exists** | remains unauthorized |
| D17 diagnostic / extra reviewers / calibration | separate exact authorization | outside this execution |

---

## 7. WHAT IS MISLEADING IN THE RECORD TODAY

**Read these with care — none of these defects has been repaired.**

| file | problem |
|---|---|
| `docs/dsh/OWNER-DECISION.md` | opening clauses approve a **withdrawn** architecture; the correction is appended, not substituted |
| same | does not incorporate the separate-identity mentor-execution ruling |
| `docs/dsh/ARCHITECTURE.md` | copied session-status language says it was not persisted — **the file now exists** |
| `docs/ACTIVE-PLAN.md` | cites absent `pipeline.py` exits; **strict validation FAILS with 7 findings** |
| `docs/PLAN-OF-RECORD.md` | ends with a stale "all six checks passed" / "not saved" line; D6 sequence predates D13 |
| `tools/astra_gate.py` | **prints** the action rather than executing it; "exact-command" allowance is **substring matching** |
| `tools/review_packet.py` | claims serialized-request enforcement; actually a **character-based estimate** + metadata checks |
| `tools/astra_review.sh` | `codex exec … \|\| true` **suppresses failure status** |
| `review_cycle.sh`, `v2/dispatch_review.sh`, `v2/checkpoint_review.sh` | **still contain direct Codex invocations** |
| `tools/audit_reviews.py` | no session-to-request matching; can print "reconcile" and **return success** |
| `docs/review-accounting.jsonl` | rows contain **numeric zeros** alongside `telemetry: UNMEASURED` |
| `docs/FAILURE-REGISTER.md` | "CLOSED by plan" ≠ implemented and verified |
| `docs/HARMBENCH-RESULT.md` | still presents all three label populations as MEASURED; the loss is not prominent |
| `docs/FRR-RESULT.md` | "base refused, v3 answered" overstates a heuristic label transition |
| `docs/ROLE-PROTOCOL.md` | historical "only these four count" wording conflicts with current instruments |
| `docs/dsh/acceptance/` | **exists but is empty** |
| `tools/scan_review_invocations.py` | named in the gate allowance but **absent** |

**Document hashes inspected** (identify files, not correctness):
`ASTRA-DECISIONS.jsonl 0e6b73bf…` · `PLAN-OF-RECORD.md fab5f18c…` · `ACTIVE-PLAN.md 45b9654b…`

---

## 8. ONE PAGE FOR THE CEO

**Where you stand.** Two workstreams, both frozen. The model (CyberGuard v4) has a registered plan and no
running work. The machinery (DSH) has a ruled architecture and no installed enforcement.

**What the 29.5 B tokens bought.** Not a shippable model, and not enforcement. They bought a corrected
understanding: the failures were not the worker being lazy — they were **capability plus no consequence for
bypassing the governed path**. Both are now designed for; neither is built.

**Your thinking was right and Astra reversed itself twice on the strength of it:** the first repair would have
removed your worker's ability to do its job, and mentor permissions would have reopened the bypass by proxy.

**The single most important decision:** **release D9 and name the reviewers and backup destination.** Nothing
else moves until those exist. Machinery acceptance is the only work that can proceed inside the freeze.

**The one thing you must not believe yet:** that any of this works. Every control above is a **specification**,
not a verified implementation — including my own tools, which Astra found suppressing failures and writing
zero placeholders. **Zero acceptance weight, UNMEASURED, and no gate has been proven to hold.**

**And the honest residual:** Astra's own independence is *"weakened, not satisfied."* Its title supplies
authority, not measured accuracy. Paying for a second model has **not yet been justified by a measured
reduction in wrong decisions** — that is an open question, not a settled benefit.
