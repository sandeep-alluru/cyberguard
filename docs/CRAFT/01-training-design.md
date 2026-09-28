# CRAFT 01 — Training-design craft (22 lessons)

Mined from the v1 training path (`train_cyberguard.py`, `cyberguard_data.py`, `verify_split.py`,
`verify_eval_mask.py`, `merge_equiv.py`, `README.md` decision table, `LEDGER.md` rounds 1–7,
`docs/VERDICT-v1.md`, `docs/SPEC-V2.md`) and the receipt of record
`research-tmp/harvest-v1/receipts/cyberguard-lora-v1.json`.

Grades: **GOLD** (hard-won, would have saved ≥1 GPU-hour or prevented a wrong claim) / **STANDARD**
(good practice worth templating) / **ANTI** (a mistake we actually made). **Ancestor** = the pod-ops
corpus entry that already covered it (see `00-crossref-podops.md`) — an ANTI *with* an ancestor is a
process failure (we skipped the fresh corpus read), not a new discovery.

---

**CRAFT-T-01 | Raw-inspect the corpus bytes before you commit pipeline time**
- Situation: the Trendyol corpus shipped literal `\n` escape sequences in its text fields. We built
  the whole preprocessing/escape pipeline (and a 170-minute box) before anyone printed a raw row.
- Action: after the box, `repr()` of a stored generation showed literal `\n` in **100 %** of tuned
  probe responses vs **0 %** base.
- Outcome: a model that emits escape artifacts; the 500-row metric effect of the artifact is still
  **unmeasured** (one stored example moved 0.6471 → 0.6327 once normalized).
- Rule: before any pipeline work, print `repr()` of 3 raw rows. Ten seconds of eyeballing is the
  cheapest test in the project and it is always skipped.
- Evidence: `docs/VERDICT-v1.md` incident 3; D-02. Grade: GOLD.

**CRAFT-T-02 | Train on exactly the text you intend to serve — a transformation is a behavior change**
- Situation: the corpus was preprocessed into `CyberSec-Dataset_escaped.jsonl` for escaping safety;
  the escape survived into the weights.
- Outcome: the artifact was *taught*, not merely inherited — base emits none.
- Rule: every transformation between corpus and trainer is a hypothesis about serving behaviour.
  If you escape, you teach escapes; if you truncate, you teach truncation. Prefer the on-disk text.
- Evidence: `docs/VERDICT-v1.md` incident 3; SPEC-V2 F3. Grade: GOLD.

**CRAFT-T-03 | Never declare a metric "unaffected" by a defect you just found — measure it**
- Situation: on discovering the escape artifact, the ledger recorded "NLL/F1 unaffected (scorer is an
  `[a-z0-9]+` regex)".
- Action: Codex review #3 tested the claim: the regex fragments words at literal `\n`
  (`"a\nb"` → `["a","nb"]`), and escapes are tuned-only (100 % vs 0 %) — so the **paired delta is
  affected**.
- Outcome: claim reversed in writing. The honest final state: the **500-row normalized effect is
  unmeasured**; on the five stored 400-char excerpts the paired delta moves in **both** directions
  (raw +.2653/+.4335/+.1060/+.1333/+.0769 → normalized +.2704/+.4148/+.1060/+.1333/+.0675: one up,
  two down, two unchanged), so even the *direction* is not an argument. Review #6 finding 6 forced
  this correction.
- Rule: "unaffected" is a measurement, not an intuition — and so is "the effect goes our way".
  Say "unmeasured" and put the measurement in the next plan.
- Evidence: LEDGER review #3 finding 3 + review #6 finding 6; `docs/SPEC-V2.md` §1. Grade: GOLD.

**CRAFT-T-04 | Batch your generation eval before you size it — 5 h → 36 min**
- Situation: batch-1 greedy on the GB10 measured ≈15 s per 256-token generation; 500×2 rows would
  have taken ~10 h overnight.
- Action: `GEN_BATCH=16` with **left padding + attention_mask** (transformers-correct for
  decoder-only batches), greedy decode unchanged, and — critically — the **identical batch for both
  arms**.
- Outcome: eval finished in **36 min**; the later capability box did ~1,000 generations in **16.8 min**.
- Rule: profile before sizing; left-pad + mask + `do_sample=False`; keep the batch identical across
  arms so paired fairness holds; record the batch size in the receipt.
- Evidence: LEDGER rounds 6–7; `cap_harness.py`. Grade: GOLD.

**CRAFT-T-05 | Pin the whole decode surface, and bracket it before believing a behavioural delta**
- Situation: a safety claim rested on outputs produced under one decode configuration (batched
  greedy, 256-token cap).
- Action: `cap_sens.py` re-ran the battery at batch=1/256, batched/512, and base batch=1/256.
- Outcome: tuned refusals 6/60 → 9/60 → 6/60; base 24/60 → 21/60; **zero transitions** between the
  batched conditions — the collapse is not a batching or truncation artifact.
- Rule: pin `num_beams=1, temperature=1.0, top_p=1.0, repetition_penalty=1.0, do_sample=False,
  max_new_tokens, batch` in the receipt; before publishing any behavioural difference, re-measure at
  ≥2 bracket conditions (batch-size and length are the two that bite).
- Evidence: `cap-sens-decode.json`; `00-crossref-podops.md` EXT-2. Grade: GOLD.

**CRAFT-T-06 | A smoke test that skips the production code path validates nothing**
- Situation: v1's first real launch died at trainer init —
  `AttributeError: 'TimeBox' object has no attribute 'on_init_end'` — while the smoke had passed.
- Action: the smoke ran **without** `MAX_MINUTES`, so it never constructed the callback at all.
- Outcome: first v1 attempt dead on arrival; fixed by subclassing `TrainerCallback`, then the smoke
  was re-run *with the time box* — the only version of that test worth anything.
- Rule: the smoke must construct every object the real run constructs, including the time box, the
  callbacks and the monitor; after any fix, re-run the smoke on exactly the production config.
- Evidence: `README.md` §Bug; LEDGER 2026-09-26 14:49. Grade: GOLD.

**CRAFT-T-07 | Size the LR schedule to the steps you will actually run**
- Situation: the cosine schedule was sized for the full epoch (3237 steps) but the box was budgeted
  for ~710 steps.
- Outcome: at box end (step 663) the LR was still ~90 % of peak — the model was trained almost
  entirely at high LR; recorded but not changed mid-run.
- Rule: `steps = budget_seconds / s_per_step` before choosing a schedule; state both the scheduled
  and the actually-run step counts in the receipt. A schedule is a function of the run you will
  have, not the run you would like.
- Evidence: LEDGER review #1 MAJOR 4. Grade: STANDARD.

**CRAFT-T-08 | Time-box training — and receipt the coverage honestly**
- Situation: a full 53 k-row epoch measured ≈13.6 h, which did not fit the available window.
- Action: `MAX_MINUTES=170`, run stopped at **step 663/3237 = epoch 0.2049** by design, not emergency.
- Outcome: receipt states wall 10271.6 s, step 663, epoch 0.2049, loss 1.006, tok-acc 0.741 —
  and the number "677" was later corrected to 663 in writing.
- Rule: a time-boxed partial epoch is legitimate evidence; over-claiming from it is not. Coverage
  belongs in the receipt and in every sentence that cites the run.
- Evidence: `receipts/cyberguard-lora-v1.json`; LEDGER review #3 finding 5. Grade: GOLD.

**CRAFT-T-09 | Check that the quantisation wheel exists for your architecture before planning QLoRA**
- Situation: QLoRA was the obvious choice for a 4B model until we checked.
- Outcome: bitsandbytes has no dependable aarch64/Blackwell CUDA wheel for GB10 → **bf16 LoRA r=32**
  with gradient checkpointing, which fit comfortably in the free memory anyway.
- Rule: the method follows the wheels you can actually install on the target arch; bf16 LoRA is the
  default when quantisation is unnecessary and unverifiable.
- Evidence: `README.md` decision table. Grade: STANDARD.

**CRAFT-T-10 | Recon the host's *inodes*, not just its bytes**
- Situation: `clawersamurai6` was the obvious host — 2× RTX 3090 idle and a full training stack
  already installed.
- Action: `recon-train-env.sh` reported per-mount inode use: its `/data` was **100 % inode-exhausted
  (119,264/119,264)** while blocks were only 57 % used; the root had 13 GB free — too little for a
  model plus checkpoints.
- Outcome: host switched to `spark-40ee` (3.3 TB free, 249 M inodes at 1 %). An idle GPU is not a
  usable host.
- Rule: host recon reports GPUs **and** per-mount free blocks **and** free inodes; "no space" is
  usually "no inodes".
- Evidence: `recon-train-env.sh`; `README.md` host decision. Grade: GOLD.

**CRAFT-T-11 | Set sequence length from the measured corpus token distribution**
- Situation: sequence length is usually inherited from the base model's maximum (32 k+) and burns
  compute on padding.
- Action: measured under our own tokenizer — median ≈895, p90 ≈1017, max ≈1791.
- Outcome: `max_seq = 2048` covers **every row** of the v1 corpus. It does **not** mean "no padding
  waste": the trainer runs `packing=False`, so padding is a function of each batch's composition, not
  of the corpus maximum. And the distribution is v1's corpus — not the v2 mixture's.
- Rule: measure the distribution under the serving tokenizer; pick the smallest power-of-two that
  covers p100, or cover p99 and declare the truncation rate; **re-measure on any new mixture**, and
  never claim a padding property from a length statistic.
- Evidence: `README.md` decision table; `train_cyberguard.py:195` (`packing=False`); corrected by
  review #6 finding 11. Grade: STANDARD.

**CRAFT-T-12 | Audit the corpus for safety and for leakage before training — and receipt both**
- Situation: a 53,201-row public instruction corpus with an unknown proportion of attack-enabling rows.
- Action: `audit_corpus_safety.py` dropped **178 attack-teaching rows (0.34 %)** and collapsed **62
  near-duplicates** → 52,284 rows; `check_leakage.py` measured prompt-level overlap: **max Jaccard
  0.773 < 0.80, zero near-duplicate leakage** (40 rows ≥0.60 documented, non-blocking).
- Outcome: `receipts/corpus-safety-audit.json` + a documented, reproducible filtering rule that the
  split then ran on.
- Rule: safety filtering and leakage scanning are pre-training gates with receipts, not opinions;
  record the threshold and the rows between threshold and floor.
- Evidence: `receipts/corpus-safety-audit.json`; `check_leakage.py`. Grade: GOLD.

**CRAFT-T-13 | Diversify a templated system prompt — but check what "N variants" actually is**
- Situation: the corpus audit found **every row shared one templated system prompt**, so the persona
  was a constant.
- Action: `augment_system: true`, rotating `SYS_VARIANTS` deterministically by row index.
- Outcome: the training set has **three text variants plus a no-system condition** — the receipt
  records `sys_variants: 4`, which counts the *no-system* entry as a variant. What was measured is
  prompt diversity; the claim that a constant prompt "teaches the model to ignore the field" was
  **never measured**. Corrected by review #6 finding 11.
- Rule: vary the system prompt and receipt the variant count **and** what the variants are; then
  evaluate system-conditioning behaviour separately if you want to claim it.
- Evidence: `train_cyberguard.py:57–66`; receipt `config.sys_variants`. Grade: STANDARD.

**CRAFT-T-14 | Verify the split with a third script that *replicates* the loaders**
- Situation: `train_cyberguard.py` and `eval_cyberguard.py` compute the held-out set
  independently — any drift in filter, seed or ordering would leave the numbers looking fine while
  meaning nothing.
- Action: `verify_split.py` re-implements both loaders and asserts: same 500 rows held out, disjoint
  from training, partitions the whole corpus, deterministic under the seed.
- Outcome: `PASS` on all four assertions (rows 51,784/500 of 53,199 at the time), re-runnable.
- Rule: the verifier must not import the thing it verifies; replicate the logic and compare the
  outputs. Independence is the point.
- Evidence: `verify_split.py`; `README.md` split-integrity check. Grade: GOLD.

**CRAFT-T-15 | `assistant_only_loss=True`, plus a MASK PROOF gate that fails closed (exit 8)**
- Situation: TRL defaults `assistant_only_loss=False`, so v1's first clean launch was supervising
  **user turns** as well — learning to imitate prompts.
- Action: the run was killed at **step 92** (22 min in, evidence preserved as
  `train-cyberguard-lora-v1.log.wrong-mask-20260927`) and a `MASK_PROOF=1` gate added: it decodes the
  non-`-100` labels of a real collated batch and refuses with **exit 8** unless the supervised span is
  assistant content and lies outside every user prompt.
- Outcome: proof PASS — **406/436 supervised tokens, assistant-only**; clean restart 01:29:12.
- Rule: for any SFT run, prove the mask on a real batch before launch; fail closed. Reviewing the
  config is not proof — decode the labels.
- Evidence: LEDGER review #1 BLOCKER 1; `verify_eval_mask.py`. Grade: GOLD.

**CRAFT-T-16 | Make a proof content-matched, never index-matched**
- Situation: the first MASK PROOF attempt refused — it compared a shuffled dataloader index against
  the raw dataset and found a mismatch.
- Action: the proof was wrong, not the mask; rewritten to locate the supervised span **by content**
  within the row.
- Outcome: proof PASS on the corrected logic; a false BLOCKER would have cost a debugging cycle at
  launch time.
- Rule: any check that touches a `DataLoader` with `shuffle=True` must match on content; ordering is
  not a contract.
- Evidence: LEDGER review #1 window. Grade: GOLD.

**CRAFT-T-17 | Compare arms on identical items, identical order, one harness**
- Situation: "base vs tuned" invites comparing two aggregate rates produced at different times.
- Action: one evaluator, one parser, one template, one decode surface, paired per-row items for both
  arms (and the same batch, once generation was batched).
- Outcome: paired per-row deltas enabled McNemar and bootstrapped CIs — the statistics that
  survived review; aggregate-only numbers would have supported neither.
- Rule: A/B means paired per-item records from one harness; aggregates are a derived view, and rates
  from different surfaces are not comparable.
- Evidence: `eval_cyberguard.py`; `cap_harness.py`; CRAFT-M-04. Grade: GOLD.

**CRAFT-T-18 | Prove the whole post-training chain with a throwaway adapter before the real one exists**
- Situation: merge → GGUF → quantise → serve spanned two machines with different toolchains
  (spark-40ee has `gguf` but no `llama-quantize`; the workstation has `llama-quantize` and the
  1080 Ti).
- Action: built a 3-step disposable adapter (`smoke-tb`) and ran the entire chain on **CPU**, so it
  could not disturb the GPU running the owner's test: 7672.62 MiB f16 → **2375.91 MiB Q4_K_M in
  165 s**, `HEALTHY :18081`, coherent defensive answer.
- Outcome: every step after training was known to work before the real adapter existed; the
  throwaway artifacts were then removed from both machines.
- Rule: demonstrate the full downstream path with a disposable artifact; a pipeline whose first
  execution happens on the real artifact has no error budget.
- Evidence: `README.md` serving path. Grade: GOLD.

**CRAFT-T-19 | Prove merged-vs-unmerged equivalence at the loss level and expect generation divergence**
- Situation: LoRA evaluation can be done on the adapter or on the merged model; the deployed artifact
  is the merged one, so the claim needs to be about the merged arm.
- Action: `merge_equiv.py` ran held-out loss on 50 rows for both, plus 5 greedy generations.
- Outcome: loss **0.8842 vs 0.8844 (Δ=0.0002)** — equivalence holds numerically; **5/5 greedy
  generations differ** (min self-F1 0.48), mechanism **not isolated**.
- Rule: claim loss-level equivalence only, scope every scored result to the evaluated merged arm,
  and never claim token-identical outputs across the two representations.
- Evidence: `evals/merge-equiv-cyberguard-lora-v1.json`; VERDICT-v1 integrity appendix. Grade: GOLD.

**CRAFT-T-20 | A gate a fixture can pass is not a gate — and "we scaled the same probe set" is a claim you must check (ANTI)**
- Situation: the v1 safety gates cleared on a **12-item** offensive fixture and an 8-item defensive
  fixture, and the verdict band printed `SHIP`.
- Action: the capability box ran a **60-probe** battery. We *described* it as the same probes at
  larger n. **That description was false** (caught by Codex review #6 finding 10, re-verified here):
  only **1 of v1's 12 prompts** appears in the 60 (nearest-neighbour Jaccard ≤ 0.36 for the rest), and
  the refusal classifier also changed between the two runs (refusal now requires a refusal
  construction: marker + object word within 50 chars). Three variables moved at once — probe set,
  classifier version, n.
- Outcome: tuned refusal measured **6/60 (10 %)** vs base 24/60 (40 %); McNemar p=4×10⁻⁵; Δ −30 pp
  [−43.3, −18.3]; surviving the tested decode brackets. **The conclusion stands** — the 12-probe
  fixture did not support a population safety claim, and direct harmful assistance was confirmed by
  two independent readers. The *mechanism* we told ourselves ("the same 12 prompts, more of them")
  did not. On the single prompt both batteries share, v1's harness scored it **refused** while the
  capability harness produced an **exploit-design answer** — so prompt construction is itself an
  uncontrolled variable (now frozen; CRAFT-M-27).
- Rule: before comparing two batteries, prove they are comparable — **prompt-level overlap**,
  **classifier version**, template/system prompt, and n each change the result. For every gate, write
  the minimum n required to detect the effect you claim *and* the probe set's provenance; fixtures
  may trigger exploration, never clearance.
- Evidence: `docs/CAPABILITY-v1.md`; D-05; `docs/SPEC-V2.md` §13 finding 10; CRAFT-M-02/M-27.
  Grade: ANTI. **Ancestor: partial** — the corpus sets the delta bar (≤10 pp unresolved); the
  **n-floor rule is new**, and the **comparability rule is newer**.

**CRAFT-T-21 | Boundary gates fail closed, with must-fail fixtures — and a classifier change is a behaviour change**
- Situation: the first contract accepted **empty and filler** responses as "answered", i.e. a vacuous
  PASS was one bad model away.
- Action: fixtures were added that **must fail** — SILENT-OFF (empty offensive → FAIL), OVERREFUSER
  (50 % vs base 100 % → FAIL), FILLER (`"x"*200` defensive), plus NaN/inf loss and F1 as
  `non_finite` (a NaN comparison is not evidence) — and a DEFENDER-with-bases case that must PASS
  (no false positive).
- Outcome: suite PASS locally and `REMOTE-TEST-PASS`; and when the refusal vocabulary was later
  widened, the classifier itself started **false-refusing a defensive answer** ("I will not require
  downtime") — caught because both directions are tested.
- Rule: every safety gate ships with fixtures that must fail and at least one that must pass; any
  change to a classifier is a behaviour change and needs regression tests in both directions.
- Evidence: `test_contract.py`; reviews #1/#2; CRAFT-M-19. Grade: GOLD.

**CRAFT-T-22 | Read the failure corpus fresh, every run — a remembered digest is not the corpus (ANTI)**
- Situation: the operation *ran* pod-ops discipline but skipped its step 1 (fresh corpus read) and
  worked from a condensed memory of the rules.
- Outcome: mapping the day against the corpora showed roughly **40 % of the lessons already
  existed** — A14/A10 (self-matching probes), A15 (instrument staleness), A04 (claims without
  measurement), A05/A06 (exit code ≠ value), training-craft §Evaluation (persist raw generations) —
  and each was re-paid (a self-matching GPU scan in front of the owner; a watcher reporting a stale
  traceback; the `scp` no-op; the +20 min replay tax).
- Rule: any GPU-bearing operation opens with `corpus-index-builder.sh` plus actual reads of
  `agent-craft.md`, `training-craft.md` §Run/§Evaluation and the fleet corpus sections matching the
  workload — **before** any launch, logged in the ledger. Summaries are how known mistakes get
  repaid.
- Evidence: `00-crossref-podops.md` root cause D-00. Grade: ANTI.
  **Ancestor: pod-ops step 1 ("Read the corpus, fresh, every run") — process failure.**
