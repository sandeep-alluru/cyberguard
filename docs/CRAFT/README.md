# CRAFT — the CyberGuard training-operation corpus

Distilled from the CyberGuard v1 operation (2026-09-27): dataset escape → LoRA training in a
170-min box → 8-gate eval → capability measurement box → safety regression discovery → two
Codex-Astra review cycles. Every lesson here was **paid for in GPU-minutes, review findings, or
retracted claims** — none are theoretical.

## Structure

| File | Domain | ID prefix | Entries |
|---|---|---|---|
| `00-crossref-podops.md` | accountability map vs the pod-ops corpora: what already existed, what is new | — | 6 re-paid + 3 extensions + 10 new |
| `01-training-design.md` | corpus/tokenizer/LoRA/box-budget/decode craft | `CRAFT-T-` | 22 |
| `02-measurement-eval.md` | harnesses, gates, statistics, safety evaluation | `CRAFT-M-` | 27 |
| `03-pod-ops-code.md` | fleet ops, shell discipline, watchdogs, serving invariants | `CRAFT-O-` | 28 |
| `04-decision-retro.md` | the decision trace: what was decided, why, what it cost | `D-nn` | 16 |
| `05-toolcall-trace.md` | the session traces mined: tool mix, failure taxonomy, what worked | — | 2 traces, 517+202 tool calls |

**77 lessons + 16 graded decisions**, plus the trace analysis that closes the postmortem's stated
gap (the toolcall-level trace had never been re-opened). All files are written; the corpus was
reviewed by Codex-Astra (review #6) and three lessons were corrected as a result — see
`docs/SPEC-V2.md` §13 and the `R-CA` entries in `LEDGER.md`.

## Lesson format

**ID | imperative rule** — Situation → Decision/Action → Outcome (with the proving number) →
Rule (transferable) → Evidence (repo path) → Grade:

- **GOLD** — hard-won, non-obvious, would have saved ≥1 GPU-hour or prevented a wrong claim.
- **STANDARD** — good practice worth template-ing.
- **ANTI** — a mistake we actually made; the rule is phrased as what to do instead.

## The ten that bite hardest (owner TL;DR)

1. **A fixture is not a gate — and two batteries are not "the same probes".** The 12-item refusal
   fixture did not survive scaling, but the comparison also changed the **probe set** (only 1 of the
   12 prompts appears in the 60) and the **classifier version**, so it cannot be attributed to n
   alone. Freeze probe provenance + classifier version + n, and prove comparability before comparing.
   *(CRAFT-T-20, CRAFT-M-02/M-27)*
2. **Store outputs in receipts, derive classes.** Class-only receipts cost a full replay re-run
   the moment anyone asks "are these really refusals?" *(CRAFT-M)*
3. **Separate format-failure from capability-failure.** 47/47 correct *when it emitted a verdict*,
   73/120 never emitted one — one number would have misfiled this as "can't triage". *(CRAFT-M)*
4. **Batched greedy decode is the biggest single speedup** (5 h → 36 min): left padding +
   attention mask + `do_sample=False`, GEN_BATCH=16. *(CRAFT-T/O)*
5. **Cross-check authorities before blaming them.** "NVD is flaky" was wrong twice; MITRE agreed
   with NVD in minutes. *(CRAFT-M)*
6. **R25: process scans self-match.** Seven distinct forms found, including the scanner containing
   its own pattern string, a *waiter* that `pgrep`'d its own command line and waited on itself
   forever, and a *kill* that matched its own command line and killed the shell running it. Use
   `case "$cmd" in *foo[.]py*)` on `/proc/cmdline`, exclude `$$`, and never echo the bare pattern.
   *(CRAFT-O)*
7. **Review before results, review after results.** #4 caught scorer bugs pre-GPU; #5 caught
   over-claims pre-publication. Dispositions in writing, fix-or-refuse each. *(CRAFT-M)*
8. **When a reviewer's BLOCKER is measurement-shaped, run the experiment** — the 45-min
   decode-sensitivity rerun settled it with data instead of argument. *(CRAFT-M)*
9. **Watchers that grep logs trip on stale text; verify the process.** Match liveness
   (/proc, marker timestamps), not the log tail. *(CRAFT-O)*
10. **Label every proxy and re-track every retraction** — composite withdrawn, fixture claim
    retired, flakiness guess overruled; the ledger that shows the reversals is what makes the
    surviving numbers trustworthy. *(CRAFT-M)*

Provenance: mined from `LEDGER.md`, `docs/SPEC.md`, `docs/SPEC-V2.md`, `docs/VERDICT-v1.md`,
`docs/CAPABILITY-v1.md`, `docs/DATASET-V2.md`, the CEO briefs, `RUNBOOK-qwen-flash-serving.md`,
harvested receipts under `research-tmp/harvest-{v1,cap-v1}/`, and the harness/ops code in repo root.
Cross-referenced against the pod-ops corpora (`references/training-craft.md`,
`references/agent-craft.md`, fleet `KNOWN_FAILURES.md`) in `00-crossref-podops.md`.
Codex-Astra review status: see `LEDGER.md` (`R-CA` entries).
