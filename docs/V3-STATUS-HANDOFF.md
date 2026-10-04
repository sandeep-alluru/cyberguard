# CyberGuard v3 — STATUS HANDOFF

**Single entry point.** This session produced 44 evidence files, 5 checkpoints, 8 owner decisions and
many code changes. This page says where the authoritative answer to each question lives, so nothing has to
be reconstructed from the transcript.

**As of:** 2026-09-30, training step ~1888/8783 (21 %).

---

## 1. ONE-PARAGRAPH STATE

The v3 training run is **live on spark-40ee** (launched 02:09 CDT, pid 1189450, 8,783 steps/epoch,
`MAX_MINUTES=3300`), projected to finish in **~37 h** against a 55 h ceiling — measured, with 18 h of
margin. It is verified **learning** (loss 1.2283 → 0.8873 first→last quartile, 0 NaN/Inf, grad_norm
stable). The §8 evaluation chain has been **audited end to end and repaired**: every evaluator that
provably measured something other than its written contract has been fixed or, where a decision is needed,
documented. The post-training path (harvest → classify → assemble → gate → verdict) is **built,
dry-run-validated, deployed hash-verified, and run end to end on the host**. **No ship verdict is
computable yet**, for two independent reasons: the adapter does not exist, and two specification defects
(G-A2's margin, §8.6's metric) required owner decisions — the second of which has since been resolved in
code.

## 2. THE TWO DOCUMENTS A DECISION-MAKER NEEDS

| question | read |
|---|---|
| **What must I decide, and why does it block a ship?** | `docs/V3-OWNER-DECISIONS.md` (headline first) |
| **What gate readings should I expect?** | `docs/V3-SHIP-FORECLOSURE.md` (reframed — soft bars, not blockers) |

## 3. THE AUTHORITATIVE ARTIFACTS

| thing | where | verified how |
|---|---|---|
| The plan | `docs/PLAN-V3.md` rev 11, md5 `123fbd2f015d6e140996642498e2fad9`, 1,534 lines | no dangling § refs; snapshot at `docs/PLAN-V3.md.rev11-bak` |
| Training run | spark-40ee pid 1189450, log `~/cyberguard/logs/train-cyberguard-lora-v3.log` | live; pace + loss recorded in `docs/evidence/training-pace-2026-09-30.txt` and `training-health-2026-09-30.txt` |
| The corpus being trained | `data/v3/mixture/mixture-v3-no-trail.jsonl`, sha256 `75b5099c…`, 140,545 rows | staged to the host and hash-verified from the receiving side |
| Post-training runbook | `docs/evidence/post-training-path-readiness.txt` | every step dry-run or executed; three defects found and fixed by auditing it against the chain |
| Eval-chain audit (all gates) | `docs/evidence/eval-chain-complete-audit.txt` | each gate's cited implementation compared with its written contract |
| Over-engineering cuts | `docs/OVER-ENGINEERING-AUDIT.md` + plan §13 | owner directive applied to the plan and to my own fixes |

## 4. THE EIGHT OWNER DECISIONS

| # | decision | state |
|---|---|---|
| D1 | G-A2's confidence bound is wider than its margin at the registered n=60, so a flawless result reads below the bar. | **REPORTED, NOT A BLOCKER** — the numbers are soft bars; the gate reports what it measures and its target is not moved. No action required. |
| D2 | §8.6's metric | **RESOLVED** — the metrics existed; only the loader was wrong, now serving the 610 references |
| D3 | G-B's ranking ROC-AUC | **RESOLVED** — implemented from the same probes via decision-token scores |
| D4 | G-D's human reference bundle | **OPEN** — span scorer built and wired; needs a person |
| D5 | Two-host training | **OPEN** — impossible without a recipe change (no distributed support) |
| D6 | Option B for the trail block | **OPEN** — block excluded (A7 FAIL) |
| D7 | §8.1 classifier wiring | **RESOLVED** — both halves implemented (A indicator + MIXED precedence), verified |
| D8 | Stale v1 substitution | **RESOLVED** — strict mode is now the default |

**Only D1 and D4 block the §8 run from producing verdicts.** D5/D6 are unrelated to the eval chain.

## 5. WHAT WAS FOUND THIS SESSION (the substantive results)

**Evaluators that measured the wrong thing** — each reproduced before being accepted:
* **G-A** used percentile bootstrap on *refusal* indicators where the plan mandates **Newcombe paired** on
  answers, inverting the verdict. Repaired and hand-verified.
* **§8.6** scored the old 500-row Trendyol split instead of the **610 references**. Loader fixed.
* **G-B** computed `(TPR+TNR)/2` — one operating point — where the plan requires a **ranking ROC-AUC**.
  Implemented from decision-token scores; no new instrument needed.
* **G-C** never passed NVD authority, so every emitted CVE was "unchecked" and `verified` was 112 < 300.
  Authority built (288/288) and wired; **verified 112 → 400**, support now PASSes.
* **G-D**'s span scorer was called by nothing and the gate's input was never produced. Scorer built and
  wired, including the fabricated-IOC bar that had never been enforced.

**Defects in the verdict machinery:**
* `assemble_gate_inputs.py` **silently substituted stale v1 measurements** (byte-identical to v1's
  receipts) and crashed without battery receipts. Both fixed.
* The G-A2 gate used bootstrap, which **masked D1** — the same gate could not fail for the right reason.
* The §8.1 classifier was wired into **nothing**; its absence made §8.4/§8.8/§8.10 uncomputable.
* G-E reported **FAIL when the pySigma library was merely absent** — an environment failure blamed on the
  model, a confusion the code's own docstring records happening before.

**Defects in my own runbook** — found by auditing it *against* the chain: a missing verdict stage, a
missing `RUN_NAME` (would have scored the **v1** adapter), and a missing `--adapter` (would have made
tuned ≡ base, producing a **false PASS** on the safety gate).

**One budget error caught before launch:** the plan's `max_minutes=1320` came from v2's presentation rate;
measured against the v3 mixture it would have stopped the run at **60 % of the epoch → INCOMPLETE →
NO-SHIP**. Raised to 3,300, which changes no hyperparameter.

## 6. WHAT HAPPENS NEXT

1. Training completes (~2026-10-01) → **STEP 0** of the runbook must confirm `epoch == 1.0` before anything
   else. An incomplete epoch is NO-SHIP.
2. Harvest (`tools/harvest-v3.sh --execute`) — hash-verified, adapter included.
3. **Do NOT change any gate target.** G-A2's confidence bound is wider than its margin at its
   registered sample size, so it will read poorly even for a good model — that is REPORTED, not fixed by
   moving the number. The owner's standard: the numbers are soft bars, any improvement is a betterment,
   and tests are fixed as *instruments*, never as *targets*. (An earlier draft of this line said to raise
   n or widen the margin; the owner rejected that, and review flagged that the instruction was still
   live here.) **D4** — G-D needs a human to label its 100 documents, or that test is retired — remains a
   genuine ask.
4. Run the runbook steps 3–5b, then **assert `arms_found` is non-empty** and the §8.6 receipt carries a
   `per_dataset` block before reading any verdict.
5. Compose the verdict with `write_verdict_v2.py` — it refuses to write one from an all-UNMEASURED report.

**A missing measurement is a NO-SHIP, never an assumed pass** (PLAN-V3 §8). That rule has been enforced
throughout, including against my own tooling.
