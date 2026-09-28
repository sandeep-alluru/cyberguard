---
title: CyberGuard — v1 RESULT: trained, benchmarked, contract PASS — tuned model beats base by 63 % held-out loss and +12.5 pp paired token-F1 (CI-clear) with boundary intact; pipeline evidence, method pilot still open
issued_at: 2026-09-27T06:45:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-26_203500CDT-cyberguard-audit-followup-ceo-brief.md
---

# CyberGuard v1 — the model is trained and benchmarked

**One line:** the owner's end state — *trained model with benchmark tests done* — **is met**:
LoRA v1 trained on spark-40ee inside the approved 170-minute box, benchmarked base-vs-adapter
on 500 held-out items with confidence intervals, **contract PASS (scoped: pipeline evidence)**,
all artifacts checksum-harvested, three Codex-Astra reviews closed with every finding
fixed-or-refused in writing. Full detail: `LEDGER.md` (chronology) and `docs/VERDICT-v1.md`
(the verdict of record).

## The numbers (held-out n=500, paired, assistant-masked)

| Measurement | Base | Tuned v1 | Delta / uncertainty |
|---|---|---|---|
| Held-out NLL | 2.360 | **0.876** | **−63 %** |
| Reference token-F1 | 0.302 | **0.427** | **+0.1249, bootstrap 95 % CI [0.1194, 0.1306]** — clear of zero and outside the 10 pp unresolved band |
| Offensive probes (n=12) | 12/12 refused | **12/12 refused, 0 tooling-marker leaks** | corrected rescoring, disclosed |
| Defensive probes (n=8) | 8/8 answered | **8/8 answered, 0 non-responsive** | over-refusal delta **0 pp** (bar ≤5 pp) |

Training receipt: 170.2-minute box, step 663/3237 (epoch 0.205 — coverage stated honestly),
train_loss 1.006, 4.86 M tokens, mean token accuracy 0.741.

**What this does and does not claim.** IS: the pipeline works end-to-end on owned hardware and
the first checkpoint crushes its base on measured domain metrics while preserving boundary
behaviour on the fixtures. IS NOT: a method claim (the brief's §5 falsification pilot is unrun),
a population-safety certification, or ship-ready product — gates 1–4, 7, 8 of the eight-gate
contract are unmeasured harness work (listed in the verdict with v2 requirements).

## The night, condensed

- **00:46** launch; **00:52** Codex-Astra review #1 finds **BLOCKER: the loss mask supervised
  user turns too** (TRL default). Run killed at step 92, fixed, permanent **MASK PROOF** gate
  added (proves supervision is assistant-only before any training). Clean restart 01:29.
- Review #2 (mid-run) finds two more BLOCKERs in our own gates — filler ("x"*200) counted as an
  answer, NaN comparisons failing **open** — both fixed with must-fail fixtures; eval masking
  verified over all 500 rows (zero mismatches); the evaluator got Wilson CIs, paired bootstrap,
  determinism/parent-identity checks, and a `ship=yes|qualified|no` band.
- **04:20:24** box closed on the minute; adapter + receipt on disk.
- **04:57** throughput catch: batch-1 generation would have taken ~5 h — killed (no results
  existed yet), batched properly (identical for both arms), **5 h → 36 min**.
- **06:09:44** benchmark complete: **contract PASS** on every gate above.
- Two honest findings disclosed: our refusal-marker vocabulary missed a genuine refusal
  (fixed; all 40 stored responses rescored offline — one flip, zero defensive, review #3
  independently reproduced); and the escaped corpus taught the model to emit literal `\n`
  artifacts — which **does** touch the F1 metric (correction of an earlier claim of ours),
  direction says our +12.5 pp is likely *understated*, v2 measures it exactly.

## Reviews (owner's Codex-Astra mandate)

Three reviews held — #1 pre-launch (blocked, we killed our own run and fixed), #2 mid-run
(2 blockers + 8 majors, all dispositioned), #3 pre-verdict ("**nothing blocks** the narrowly
scoped pipeline-evidence claim", tightened our language; caught our F1-unaffected claim as false
and a step-count error — both corrected in the ledger). Every finding: fixed, or refused with a
written reason. Reviewer has no design authority; the loop is working.

## Also closed this pass

- **License:** Trendyol corpus is **Apache-2.0** (dataset card) — v1 clean.
- **v2 data plan** (`docs/DATASET-V2.md`): 20 candidates pinned with licences/sizes/contamination
  verdicts (admit Primus-FineWeb + NIST/NVD/ATT&CK-clean sets + FineWeb-Edu replay; reject eval
  contamination, NC licences, and the same-author "Fenrir" sibling until overlap is measured).
  Nothing adopted without the written entry gate.

## Asks / next

1. **v2 go/no-go** on the falsification pilot (brief §5, <10 GPU-days): unescaped corpus,
   decontaminated mixture per the admission gate, judge-uplift harm battery, general-capability
   replay suite, post-cutoff process eval — the gates that make a *method* claim possible.
2. Nothing needed on spark-40ee; GPU idle, leftover ray/vllm daemons untouched as agreed.
3. Artifacts: `research-tmp/harvest-v1/` (adapter 264 MB, receipts, eval json, full logs — every
   sha256 verified against the remote); verdict `docs/VERDICT-v1.md`; history `LEDGER.md`.
