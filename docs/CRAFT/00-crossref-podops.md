# CRAFT 00 — cross-reference vs the pod-ops corpus (the accountability map)

The pod-ops skill maintains the machine's authoritative failure corpora:
`references/training-craft.md` (F-records incl. 44–69), `references/agent-craft.md` (A01–A15),
and the fleet corpus `~/AgentHub/Pioneer-Content-Foundry/foundry-editing/model-bakeoff/KNOWN_FAILURES.md`.
The CyberGuard operation (2026-09-27) ran *pod-ops discipline* but did **not** execute pod-ops
step 1 — read the corpus fresh, every run — at the start of the day. Consequence, mapped honestly:

## Class 1 — ALREADY IN THE CORPUS, WE PAID AGAIN (the shame table)

| CyberGuard incident (04-decision-retro) | Corpus entry that already covered it | What actually happened |
|---|---|---|
| Final GPU-clean scan printed BUSY — scanner matched its own `run-cap` pattern string | **A14** ("a probe matched its own command line… never let a self-matching probe support a claim about absence") + **A10** (bracket trick fails when pattern appears elsewhere in the same cmdline) | Fifth R25-form rediscovery, live in front of the owner |
| Watcher matched a stale `Traceback` and reported the relaunched replay's old crash as its outcome | **A15** ("a monitor is an instrument: it needs the same treatment as the metric it reports" — verify against an independent reading) | Verified process instead; rule restated below as EXTENSION-1 |
| "NVD API is flaky" — asserted, then overruled by MITRE | **A04 critical** ("claims without measurement… every status line names its evidence") | Detour + written retraction |
| `scp` multi-path quoted string silently fetched nothing | **A05/A06 class** ("a command that succeeds can still be wrong — check the value, not the exit code") | Loop one-file-per-scp + manifest verify |
| Receipts stored classes, not outputs → forced audit replay | **training-craft §Evaluation** ("Persist per-item raw generations and derive verdict rates from those fields") | +20 min GPU replay tax |
| Backgrounded ssh returned exit 124 while the job ran fine | **A05 class** again (plausible result, wrong meaning) | /proc liveness check adopted |

**Root cause (the corpus's one entry that matters most):** pod-ops step 1 exists for exactly this —
*"Read the corpus, fresh, every run… do not summarise from filenames."* We ran from a
memory-condensed digest of the rules instead. **D-00 (ANTI): a discipline you carry in memory is a
summary of the corpus, and summaries are how known mistakes get re-paid. Rule: any GPU-bearing
operation opens with `corpus-index-builder.sh` + actual reads of `agent-craft.md` +
`training-craft.md` §Run/§Evaluation + fleet-corpus sections matching the workload — before any
launch, every time.**

## Class 2 — EXTENSIONS of known entries (new forms; fold back into pod-ops)

- **EXT-1 → A15**: watcher staleness has a *re-run* form — a log-matching watcher trips on text
  left by a **previous** crashed attempt. Fix: match liveness markers with timestamps newer than
  launch epoch, or watch `/proc`, never the raw log tail across relaunches.
- **EXT-2 → training-craft §Evaluation "decode/template ablation"**: extend to *behavioral*
  claims — any behavioral difference (refusal, safety) must be bracketed against batch-size and
  max-token decode conditions before publication (our batch=1/256 vs batched/512 run settled the
  harm-collapse in 45 min).
- **EXT-3 → A06**: `sed` patterns that don't match exit 0 in a `sed && next` chain — the chain
  silently skips or, worse, proceeds with the old file. Check `grep -c` the change landed before
  consuming the file.

## Class 3 — NEW craft from this operation (candidates to fold into pod-ops/corpora)

These had **no corpus ancestor** — the CyberGuard corpus is where they live first:

1. **Gate-power rule**: a gate may not be passable by a fixture. Prespecify minimum n per safety gate
   from the effect size claimed (12-item "12/12 refused" vs 6/60 at n=60; McNemar p=4e-05). The
   corpus's "≤10 pp UNRESOLVED" sets the delta bar; this sets the **n floor**.
   **Corrected by review #6 finding 10 (2026-09-27):** the two batteries are *not* the same probes —
   only 1 of the 12 appears in the 60, and the refusal classifier changed between runs. So the rule is
   **three-part: probe-set provenance + classifier version + n**, and a comparison must prove
   comparability before it is allowed to attribute a difference to any one of them. On the single
   shared prompt the two harnesses disagreed on the safety class outright (CRAFT-M-27).
2. **Receipts = outputs; classes = derived views** (corpus has the raw-generation rule for eval
   scores; extend to *safety batteries*: store every output verbatim + marker list in the receipt).
3. **Verdict-split**: report format-failure and capability-failure separately
   (47/47 correct when it emitted a verdict; 73/120 never emitted one — one blended number would
   have misfiled the model's best-behaved failure mode).
4. **Dual-authority rule for external facts**: before blaming an authority for contradicting a
   finding, verify the fact against a second independent authority (NVD+MITRE, minutes, settled).
5. **Rater QA**: independent human/LLM raters need index-integrity checks (rationale-vs-text
   overlap test caught 16/60 batch-shift mismatches in our blind rubric). QA your instruments that
   grade other instruments.
6. **Deterministic replay as a publication gate**: a behavior claim requires a replay that
   reproduces the original aggregates exactly; equality first, audit second.
7. **Authored-probe labeling + easy-mode floor discipline**; failed fetches recorded SKIPPED with
   reason, fallbacks labeled — never a silent dataset substitution.
8. **Composite honesty**: withdraw single blended capability composites; report per-task vectors
   with per-task margins (the 103.8 % composite hid a zero floor — same honesty family as the
   corpus's "don't report pass@k under that name").
9. **Pilot every prompt-contract at n=5 before arming at n=120** (the 16-token triage contract
   would have died in a two-minute pilot instead of needing rescue by verdict-split).
10. **Train/serve isolation via env-file indirection** (`~/.project-env`): the serving box stays
    untouched because isolation is a file, not a memory.

## Standing rules adopted going forward

1. GPU op ⇒ pod-ops step 1 corpus read, fresh, logged in the LEDGER (`corpus.verified`-style line),
   **before** any launch. Memory digests don't count.
2. Every CyberGuard CRAFT lesson graded ANTI must cite its corpus ancestor if one exists — an
   ANTI with an ancestor is a process failure (fix the process), an ANTI without one is a new
   discovery (fold it back).
3. Fold-back duty: EXT-1/2/3 + Class-3 items ≥1–5 proposed upstream to the pod-ops corpus at the
   next skill maintenance (owner-approved, same append pattern the Ornith campaign used).
