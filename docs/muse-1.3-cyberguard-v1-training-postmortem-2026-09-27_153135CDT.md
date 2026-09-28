# muse-1.3 — CyberGuard v1 training postmortem (decisions, toolcalls, failures, craft)

**Filed:** 2026-09-27 15:31 CDT · **Author:** Muse (analysis-only pass) · **Scope:** CyberGuard v1
LoRA run + eval chain + capability box on spark-40ee, 2026-09-26 → 2026-09-27 14:35 CDT.
**Method:** read-only inspection of `LEDGER.md` (503 lines, full), `SPEC.md`, `docs/VERDICT-v1.md`,
`docs/CAPABILITY-v1.md`, `docs/CRAFT/{README,04-decision-retro}.md`, harvest manifests; remote
(spark-40ee) artifacts and DSH session bodies NOT re-opened here — cited via ledger pointers.
Times Central. No secrets in this report.

**Pending input (not blocking this report):** a background synthesis workflow over DSH session
logs for this run had not delivered at filing time; its output should be appended as an
addendum, not merged silently.

## 1. Bottom line

v1 met its contract on its own fixtures (NLL 2.36 → 0.88, paired F1 +12.49 pp CI-clear, step
663/3237 honestly receipted) and the operation's review machinery then **caught its own headline
safety claim as fixture-underpowered**: the 12/12 refusal fixture collapsed to 6/60 (tuned) vs
24/60 (base) at n=60, McNemar p=4e-05, decode-robust. The model is not deployable against
adversarial traffic; the pipeline, harness, and review loop are the durable product. Nothing in
the evidence contradicts the ledger's own account; two of its retractions (escape-effect
direction, NVD flakiness) were themselves corrected in writing, which is the strongest
trust signal in the file.

## 2. Timeline (condensed from LEDGER.md; full detail there)

| When (CDT) | Event |
|---|---|
| 9-26 14:30–15:00 | Project stood up: Qwen3-4B-Instruct-2507, Trendyol 52,284 rows, LoRA r=32 bf16, seq 2048, host spark-40ee (chosen over inode-exhausted clawersamurai6), 170-min box ≈ 20 % coverage by design |
| 9-26 14:49 | v1 launch #1 crashes at init (`TimeBox.on_init_end` AttributeError) — no adapter, no receipt |
| 9-26 15:14–16:24 | 12-session endpoint wipeout on spark-local (completion timeouts); headless research #1 dies rc=124; incremental-write contract salvages run #2 |
| 9-26 17:12–18:10 | Full 16-session DSH audit; root cause established; CEO brief #1 |
| 9-26 20:05–20:15 | Research brief completed (3 arXiv IDs verified, 2 re-anchored); pre-flight gate PASS (split 51,784/500 prompt-disjoint, Jaccard max 0.773) |
| 9-26 23:44–00:10 | Housekeeping: LEDGER/SPEC/memory/checkpoint created; training launch reserved for owner |
| 9-27 00:10 | Owner go-ahead; SPEC done-means ×7 + R-CA review rule written |
| 9-27 00:46 | v1 LAUNCHED (pid 139879), monitor armed; review #1 dispatched 00:50 |
| 9-27 00:52–01:30 | Review #1: BLOCKER 1 (user-turn supervision) confirmed from source → run killed at step 92 (22 min lost, evidence preserved), `assistant_only_loss=True` + MASK PROOF gate added; clean restart 01:29:12 (pid 147621). Monitor false-CRASH on stale log fixed same window |
| 9-27 01:45–02:20 | BLOCKER 2 (empty-response detector failure) + MAJOR 3 (n=50→500, Wilson CI, ≤10 pp band, incremental partials) fixed, deployed md5-verified, REMOTE-TEST-PASS |
| 9-27 02:20–02:50 | Review #2: 2 BLOCKER + 8 MAJOR, all dispositioned (filler detector, NaN fail-open, paired bootstrap CI, mask re-measured over all 500 rows exit 0, fixture-scale honesty, v2 candidates demoted to UNVERIFIED) |
| 9-27 03:34–04:01 | Review #3 tooling staged; Grok v2-mixture research; DATASET-V2.md admission gate written; PolySec exposed as phantom |
| 9-27 04:10–04:17 | Chain false-positive incident (grep-vs-glob liveness bug): eval fired mid-training, slowed trainer ~27 s/it × 5 min, no corruption; killed, partials removed, `alive()` rewritten |
| 9-27 04:20:24 | BOX CLOSED clean: step 663/3237, epoch 0.2049, loss 1.006, token-acc 0.741, 264 MB adapter + receipt |
| 9-27 04:30–05:17 | Merge-equiv Δ=0.0002 (but 5/5 greedy generations differ — claim scoped to merged arm); batch-1 eval measured ~5 h → deliberately killed (exit 137 preserved) → batched GEN_BATCH=16 restart; watchdog ALERTs all acknowledged with cause |
| 9-27 05:24–05:30 | Batching confirmed: 5 h → 36 min eval; harvest validated (14 files, all sha256) |
| 9-27 06:09:44 | BENCHMARK RESULT: NLL −63 %, F1 +12.49 pp [0.1194, 0.1306]; refusal-marker incident found + fixed via disclosed offline rescoring (exactly one flip, review-reproduced); literal-`\n` escape leak found (100 % tuned, 0 % base) |
| 9-27 06:2x–06:50 | Review #3: 5 findings, all accepted — incl. overturning our "metrics unaffected" claim and correcting step count 677→663, G6 to measured 0 pp. VERDICT-v1 written, harvest re-run (16 files), CEO brief portal-verified. **v1 COMPLETE.** |
| 9-27 12:15–12:32 | Capability box: 16.8 min GPU, all 7 phases, receipts per phase |
| 9-27 12:53–14:07 | Audit replays reproduce aggregates EXACTLY; harm collapse confirmed real (49/54 direct-helpful); dual-authority CVE recheck overrules "NVD flaky" guess; rater-QA catches index corruption; decode-sensitivity closes BLOCKER 2 (zero flips) |
| 9-27 14:35 | CAPABILITY-v1 gap map written; 18 receipts + 5 logs harvested sha256-verified; CEO brief portal-verified; GPU released clean, monitors exited, flash box untouched |

## 3. Decisions (each with cost, condensed; full D-01…D-16 in `docs/CRAFT/04-decision-retro.md`)

Good calls that paid: train/serve isolation on separate Sparks (D-01); falsification-first 170-min box (D-03); batched greedy decode (D-04, single biggest efficiency win); mandatory pre-run review #4 and pre-publication review #5 (D-07, D-12); replay-exactness before audit (D-11); rater-QA and composite withdrawal (D-13, D-14); clean GPU release (D-16).
Right outcome / wrong process: late escape detection (D-02 — commit pipeline time before a 10-row eyeball); SHIP headline on substitutes (D-06); unpiloted P2 token budget (D-09); ops sloppiness taxed all day (D-15).
Mistakes paid for: 12-item fixture accepted as a gate (D-05, the root mistake — refuted at n=60); class-only receipts forcing a replay (D-08); "NVD flaky" guess defended once (D-10).

## 4. Toolcalls & ops (from ledger evidence, not session bodies)

- **Monitors/watchers (4 armed):** `monitor-cyberguard.sh` (300 s, /proc + log-growth + crash + receipt + deadline), eval-chain watchdog, local `watch-eval.sh`, capability monitor. All exited cleanly. Four watcher false-positives total, each acknowledged with mechanism (stale-log tail, old-monitor race, inline-ssh quoting, self-matching scan) — every one is now a codified R25-family rule.
- **Launch/detach:** `setsid nohup` + durable log + refuse-to-start-twice gate; no lost logs all operation.
- **Sync discipline:** whole training path md5-verified local↔remote before launch (zero drift); every mid-run fix redeployed + `REMOTE-TEST-PASS` before continuing.
- **Incident count (ops-side):** init crash (typo class), monitor stale-log CRASH, chain grep-glob misfire, batch-1 kill (deliberate), 2 ALERT-EVAL races (acknowledged), replay tensor crash (fixed + relaunched), scp silent no-op, ssh exit-124-while-healthy, GPU-BUSY self-match. Zero data loss; every incident preserved evidence (`*.stray-*`, `*.batch1-slow-*`, acknowledged/ dir).
- **Review machinery:** 5 Codex-Astra reviews, 30+ findings, every one dispositioned in writing (fixed / accepted-as-limit / refused+reason). Two findings reversed our own published-in-ledger claims mid-flight — the mechanism working as designed.

## 5. Failures (numbered; cost → fix → status)

- **F1 init-crash typo** — cost: first v1 attempt dead on arrival. Fix: `check.sh` path proof + step-progress ≤10 min rule. Closed.
- **F2 wrong loss mask (user-turn supervision)** — cost: 22 min + step-92 kill. Fix: `assistant_only_loss=True` + permanent MASK PROOF gate (406/436 tokens proven). Closed; highest-leverage catch of the run.
- **F3 detector fail-open (empty/filler pass)** — cost: would-have-shipped vacuous PASS. Fix: non-responsive + over-refusal gates, filler detector, NaN rejection, all as must-fail fixtures. Closed.
- **F4 12-session endpoint wipeout** — cost: ~70 min research + full audit. Fix: completion-probe gate (liveness 200 lied through the outage), fan-out caps on spark-local. Closed with CEO brief.
- **F5 chain grep-glob misfire** — cost: 5 min trainer slowdown, no corruption. Fix: shell case-glob `alive()`; R25 extended to pattern-language mismatches. Closed.
- **F6 escape artifact taught by corpus** — cost: tuned-only metric contamination (F1 delta plausibly understated; 500-row effect unmeasured). Fix: v2 (unescape + normalized harness). OPEN.
- **F7 class-only receipts** — cost: full audit replay (+20 min GPU, +1 crash-fix). Fix: store-outputs rule. Closed (paid, codified).
- **F8 NVD-flakiness guess** — cost: re-verification detour + retraction. Fix: dual-authority rule. Closed.
- **F9 blind-rater index corruption** — cost: item-level rubric claims withdrawn. Fix: rater-QA receipt; surviving claims restricted to direct-reader indices. Closed as disclosed limit.
- **F10 safety regression itself (tuned 6/60 vs base 24/60)** — not an ops failure; the finding. Cause per gap map: defensive-QA corpus taught answer-everything in 0.2 epoch. v2 requirements ordered by bite in CAPABILITY-v1 §v2.

## 6. Successes (with proof pointers)

- Contract PASS on fixtures with CIs excluding zero (VERDICT-v1 table; `harvest-v1/evals/`).
- Coverage honesty: epoch 0.2049 receipted, never rounded up; "677" corrected to 663 in writing.
- Reproducibility: replays reproduced aggregates exactly; determinism + parent-identity checks green.
- Harvest integrity: 16 + 18 files, every sha256 verified against remote manifests.
- Serving isolation: flash box untouched across an 8-hour op with two crashes.
- Review cadence held: 5/5 mandatory reviews, zero skipped, zero un-dispositioned findings.

## 7. Metrics of record (canonical values; see VERDICT-v1 + CAPABILITY-v1 for CIs/caveats)

v1 held-out paired (n=500): NLL 2.3600→0.8763; token-F1 0.3024→0.4273 (Δ+0.1249 [0.1194, 0.1306]).
Boundary fixtures: offensive 12/12 refused corrected (disclosed rescoring, original 11/12 kept);
defensive 8/8 both arms, Δ 0 pp. Train: 663 steps, loss 1.006, tok-acc 0.741, 4.86M tokens, 10271.6 s.
Capability box: P1 TID 21.4 % / CVE 18.2 % hallucinated (dual-authority confirmed); P2 format_coverage
39 %, verdicts 47/47 when emitted; P3 mean F1 .564, 65 % docs ≥1 fabricated IOC; P4 YAML-valid 6.7 %,
schema-complete 0 %; P5 13/15 + 5/5 unknown-refusal; P6 vector (no regression measured, floor unproven);
P7 tuned 6/60 vs base 24/60, McNemar p=4e-05, Δ−30 pp [−43.3, −18.3], decode-robust.

## 8. Housekeeping findings (this report's own)

- **Canonical local dirs are EMPTY:** `data/`, `evals/`, `gguf/`, `receipts/`, `training/` contain
  nothing; artifacts live on spark-40ee (`~/cyberguard/…`) plus `research-tmp/harvest-{v1,cap-v1}/`.
  The jobs/README convention (harvests to durable storage with re-runnable comparators) is met by
  the harvest dirs; the empty canonical dirs should either be populated, documented as intentionally
  remote, or removed — currently ambiguous to a fresh agent.
- **No git repo** (open item since 9-26, LEDGER). Remote `~/cyberguard` namespace still outside any
  AgentHub archive (open item). Both predate this report; restated, not newly found.
- CRAFT corpus (`docs/CRAFT/`) already exists with README + 04-decision-retro; files 01/02/03 were
  not present at filing time — the corpus the owner asked for is two-thirds unwritten.

## 9. Gaps / unknowns (labeled, not filled)

- Remote-only artifacts (adapter bytes, full logs, remote receipts) taken on ledger + manifest word;
  not independently re-hashed here.
- DSH session bodies (toolcall-level trace) not re-read here; §4 derives from LEDGER + review records.
  The pending background synthesis over session logs should land as an addendum and may refine §4–§5.
- 500-row normalized-F1 effect of the escape artifact: unmeasured (v2 requirement, known).
- Population-safety rate beyond the rubric approximation: not established (known, disclosed).

## 10b. Addendum — background synthesis workflow (delivered after filing)

An 8-agent workflow (168 tool calls) ran locator + 4 analysts + critic + gap + synthesis over
this run. Result: **partial**. Four of five primary reports returned no structured evidence
(locator, decisions, failures, metrics); synthesis rebuilt from targeted file reads instead and
converged on the same 15 evidence files this report cites — including this report itself. It
adds no new inspected evidence and no contradictions. Carried-forward unresolved (unchanged):
remote adapter bytes never re-hashed; DSH session toolcall trace never re-opened; 500-row
escape effect unmeasured; population-safety rate unestablished; CRAFT 01/02/03 unwritten; no
git repo; empty canonical local dirs. The DSH toolcall trace remains the one analysis gap neither
pass closed.

## 10. Corpus recommendation (concrete)

Do not start a second corpus: extend `docs/CRAFT/` with the missing `01-training-design.md`,
`02-measurement-eval.md`, `03-pod-ops-code.md` in the established ID/imperative/GOLD-STANDARD-ANTI
format, mining sections 4–5 of this report plus the numbered review dispositions. Suggested new
entries beyond the existing ten: (a) MASK-PROOF as a mandatory pre-launch gate for any SFT run;
(b) fixture-power prespecification per gate (D-05 class); (c) mid-run kill authority for detector
failures with evidence preservation; (d) class-vs-output receipt rule (D-08); (e) dual-authority
rule for external-knowledge disputes (D-10); (f) R25 pattern-language-mismatch form (F5).
