# CRAFT 04 — Decision retrospective (the whole operation, decision by decision)

The trace of every consequential decision in the CyberGuard v1 + capability-box operation, what
it was worth, and what we'd do differently. Grades: ✅ good call, ⚠️ right outcome / wrong
process, ❌ mistake we paid for.

## Phase 1 — Setup & training (morning)

**D-01 ✅ Isolate training from serving.** All work on spark-40ee (user clawerdigi2); the flash
serving box (spark-8cf2) untouched all day, enforced by an env file (`~/.cyberguard-env`) rather
than memory. Cost: zero. This is why an 8-hour operation with two crashes never touched
production.

**D-02 ⚠️ Accepted Trendyol despite escaping defect — detection was late.** The corpus shipped
literal `\n` sequences; we committed pipeline time before a 10-row raw-string eyeball would have
shown it. Unescaping was the right fix (Apache-2.0, size, on-domain), but the sequence should
have been: *raw-inspect 10 rows → then decide*. Corollary rule: NLL anomalies on "clean" data
mean inspect the bytes, not the model.

**D-03 ✅ Falsification-first training: 170-min box on a 5 h estimate.** Stopped at step
663/3237 (epoch 0.2049) by design, not emergency. Right call for a pilot — with one poison
seed: see D-05. Partial-epoch training is legitimate; *over-claiming* from it is not.

**D-04 ✅ Batched greedy decode (5 h → 36 min eval).** Chose to profile and re-engineer
generation (left padding, mask, `do_sample=False`, batch 16) rather than accept a slow eval.
The single largest efficiency win of the day; every later box (capability: 16.8 min for ~1,000
generations) rode on it.

**D-05 ❌ The G5/G6 safety gates passed on a 12-item fixture — the day's root mistake.**
Gate design accepted "substitute" evidence (12 offensive prompts) for a population claim
("boundary intact"). At n=60 the refusal rate measured 10 %, not 100 %. The SHIP verdict was
*honest about what it measured* — but a gate that can be passed by 12 prompts is not a gate.
Rule: prespecify minimum n per gate from the effect size you need to detect; fixtures may
trigger exploration, never clearance.

**D-06 ⚠️ SHIP verdict language.** Scope was technically accurate ("on substitutes") yet the
headline read as safety-clear. Lesson: when evidence is a substitute, the headline itself must
carry the word — readers read titles, not caveats.

## Phase 2 — Capability box design (midday)

**D-07 ✅ Mandatory design review before GPU (Codex #4: 2 BLOCKER + 8 MAJOR + 2 MINOR, all
fixed pre-run).** Caught: unequal arm-n (P6), GSM truncation contract, false-refusal classifier
bug *that my own earlier vocabulary fix had introduced*, 6 scorer defects. Every one of these
would have produced a wrong published number. ~30 min of review bought the credibility of every
number after it.

**D-08 ❌ Receipts stored classes, not outputs.** P2/P7 wrote derived verdicts to receipts to
keep them small. The moment the safety claim mattered, we owed an audit replay (+20 min GPU, +1
redeploy, +1 crash-fix of the replay itself). Rule: outputs are the evidence; classes are
derived views — store the evidence.

**D-09 ⚠️ Time-budgeting the box (MAX_MIN deadline + resume-unless-FORCE).** Correct
engineering (the box finished in 16.8 min of 180 budget and every phase got a receipt); but the
same harness let the 16-token P2 budget stand unpiloted — 61 % of outputs died mid-sentence and
one whole phase's headline number needed the verdict-split rescue. Rule: pilot every phase at
n=5 before arming it at n=120.

**D-10 ❌ "NVD API is flaky" — a wrong guess defended once.** When NVD returned 0 results for
hallucinated CVEs, I suspected the authority. Both flagged CVEs were genuinely unassigned
(MITRE agreed immediately). Cost: a re-verification detour and a owed retraction in the ledger.
Rule: when a measurement contradicts your model of the world, check a second authority *before*
blaming the first.

**D-11 ✅ Crash discipline on the replay (tensor `__contains__` bug).** First replay died; we
fixed, redeployed, re-ran, and demanded *exact* reproduction of the aggregates (tp24/fp43/fn36/
tn17/unparsed79 — exact). Determinism proved, then the outputs audited. Rule: a replay that
doesn't reproduce the original numbers is a different measurement — verify equality before
auditing.

## Phase 3 — Results & review cycle (afternoon)

**D-12 ✅ Ran review #5 on results before publishing the gap map.** It demanded two real
experiments (harm rubric by an independent rater; decode-surface sensitivity), not rewordings.
Both were run the same afternoon (45 min GPU + one agent call). Outcome: collapse survived all
decode surfaces; rubric confirmed severity. Rule: when a reviewer's blocker is
measurement-shaped, measure — arguments don't retire BLOCKERs.

**D-13 ✅ Caught our own independent rater's corruption.** The blind 0–4 rubric had 16/60
rationales mismatched to the wrong outputs (batch-shift). We disclosed it, withdrew item-level
rubric claims, and kept only indices two families had read directly. Rule: raters are
instruments; QA your instruments, including the ones that grade others.

**D-14 ✅ Withdrew the 103.8 % general-capability composite on review.** The unweighted two-task
average hid a format-floor zero. Replaced with a per-task vector and "G7 floor: UNMEASURED".
Cost: a weaker headline. Value: the surviving numbers are load-bearing.

**D-15 ⚠️ Ops sloppiness taxed the day.** Watcher matched a stale `Traceback` and declared the
relaunched replay's old crash as its outcome (verified the process instead — it was healthy);
`scp` multi-path quoted string silently fetched nothing; a backgrounded ssh returned exit 124
while the job ran fine; final GPU-clean scan printed BUSY — the scanner matching its own
`run-cap` pattern (R25, fifth form). None were exotic; all are now codified in `03-pod-ops-code.md`
with code idioms. Rule: every ops incident becomes a template or it recurs.

**D-16 ✅ GPU released clean, twice-verified; monitors all exited; serving box still untouched.**
Closing hygiene is part of the measurement — a "clean" claim without a /proc scan + nvidia-smi
line is noise.

## The shape of the day (meta-analysis)

- **Where time actually went:** 17 min GPU for the real measurement; the rest in *making the
  numbers honest* (reviews, replays, sensitivity, audits). That ratio is the correct shape of a
  falsification operation — the measurement is cheap, the trust is expensive.
- **Every wrong turn was a trust shortcut**: fixture-as-gate, classes-as-evidence,
  guess-about-authority, un-piloted prompt budget, log-tail watcher. Every win was
  *instrument redundancy*: replay, dual authority, paired stats, independent rater, /proc scan.
- **The one-sentence craft:** assume your measurement is lying in a specific, findable way, and
  build the one cheap check that finds it — before anyone quotes the number.
