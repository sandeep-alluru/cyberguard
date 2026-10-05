codex
**CyberGuard — consolidated plan of record, 4 October 2026**

**Founder brief**

Keep v3 as research evidence. Do not ship it. After the owner releases D9, restore the damaged measurements, qualify the prescribed 8,000 examples, and run the two-arm recovery pilot: correct v3 alongside an equally trained fresh adapter. Advance only a passing checkpoint to the full product contract and test the actual downloadable package.

**The pilot stays. A blind fresh restart is not authorized.** The saved public results show gains worth testing for retention; they do not establish that recovery works. The pilot answers that question before further training expense.

I also close the gap after the pilot: **nominate its selected final checkpoint directly for product qualification; authorize no additional training in this plan.** If neither arm passes, or the selected checkpoint fails product qualification, the outcome is NO-SHIP. A failed pilot does not trigger an automatic 37-hour run.

The owner supplies four things: explicit freeze release and adoption of this plan; two cybersecurity-competent reviewers plus a third adjudicator; access to the owned GB10 and Linux CPU workstation; and labor funding within the ceilings below. The owner does not choose datasets, metrics, or training settings.

New planning ceilings are **260 GPU-hours, 24 CPU qualification hours, 80 worker hours, and 800 aggregate human-review hours**, with **$0 rented-GPU/API spend**. These are limits, not measured estimates. Target a package or explicit NO-SHIP verdict within **45 calendar days of activation**, conditional on resource availability and every gate passing. Actual labor cost and electricity cost are UNKNOWN until company rates and consumption are recorded. No old calendar promise survives this revision.

**Authority and reconciliation**

This document supersedes the eight-section CTO plan as operating direction. The old text remains historical evidence. D1–D9 remain binding; this document is not a release of D9. New instructions below become executable only after activation and exact action authorization are recorded.

| Conflict | Current instruction |
|---|---|
| C1: keep running the 2,048-token diagnostic | D1 supersedes it. Cancelled; preserve outputs as exploratory. Its 3,584 + 2,048 configuration exceeds 4,096. No completion allowance, replacement diagnostic, or retroactive enlargement. |
| C2: fresh-only training | The v3 challenge supersedes it. Run the controlled warm/fresh pilot. This document supersedes the challenge’s automatic fresh-route continuation after failure: no passing arm means NO-SHIP, with no additional training authorized. |
| C3: repair the old mixture | D2–D5 supersede it. Exactly 8,000 accepted examples from the named sources below; rejection only. The old 20,000-row recipe, semantic repair program, and refusal repetition are inactive. |
| Worker performs semantic review | D7 supersedes it. Humans adjudicate; no judge model substitutes for them. |
| Old diagnostic costs and October deadlines | Replaced by the allocations and activation-relative milestones below. |
| Internal case/probe gates | Retired as model-acceptance evidence. Public benchmarks decide model quality; software and hardware checks establish implementation and package behavior. |

**Evidence status — the single current account**

VERIFIED here means checked against the identified local saved evidence, not rerun in this session. Historical measurements do not automatically satisfy the new contract.

| Public knowledge benchmark | Items | Original base | v3 | CyberSecQwen-4B |
|---|---:|---:|---:|---:|
| CyberMetric-500 | 500 | 47.20% | 80.60% | 45.40% |
| SecQA-v1 | 110 | 69.09% | 93.64% | 48.18% |
| CTI-MCQ | 2,500 | 43.96% | 46.80% | 57.76% |
| CTI-RCM | 1,000 | 40.60% | 63.30% | 67.90% |

These are saved local strict-format results: greedy, one trial, 512 output tokens, batch 8, left padding, BF16, unmerged adapter, own chat template, no added system message, no input truncation, 4,096-token envelope. Source E4 below contains the protocol and comparison table. They are not a reproduction of an author’s multi-trial leaderboard result.

v3 improves over its base on all four tests and trails CyberSecQwen on both CTI tests. Recorded CTI unparseability is 40.9% MCQ and 18.7% RCM. Conditional accuracy among parseable replies is not a prediction of repaired overall accuracy. The old reviews report stock introductions, unfinished answers, and 336 minutes versus the base’s 58 minutes; their causal contribution and corrected runtime remain UNMEASURED.

| Artifact or claim | Honest current status |
|---|---|
| HarmBench direct requests, 159 items | Saved aggregates: base 1/159, v3 0/159, peer 3/159. **Damaged evidence:** E5 retains only the peer’s 159-label vector. Base and v3 vectors are missing; their 159-response generation files survive. Treat those two aggregates as historical, pending D6 reconstruction—not acceptance evidence. |
| MITRE-FRR, 750 items | Saved upstream heuristic counts: base 32, v3 230, peer 8. These are heuristic labels, not established semantic refusals or usefulness scores. |
| FRR emptiness | Historical zero-empty counts are withdrawn. Generation code now checks decoded text, but the score path still consumes saved empty flags. Correct code alone has not restored historical evidence. D6 must reproduce the error and rescore decoded content across all saved responses. |
| Historical GSM8K subset | Saved 1,200-item results report base 91.17%, v3 82.33%. This is a subset measurement, not full 1,319-item release evaluation. U0 verifies item identity and public-test provenance before reuse. |
| Internal batteries and their NO-SHIP rationale | Retired from public model-acceptance evidence; not rehabilitated by rescoring. Current v3 remains unqualified under the public product contract. |
| Cancelled 2,048 diagnostic | Exploratory only; cannot qualify any product or establish a matched longer-budget comparison. |
| Training contamination | Clean generalization is UNMEASURED. The old “56 RCM items / 5.60%” interpretation is disputed in the record and is not adopted here. Cleaning corrective data does not erase inherited exposure in v3. |
| Recovery, fresh-control quality, human semantic FRR/usefulness, full GSM8K, IFEval, Phi comparison, merged/Q4 quality and deployment performance | UNMEASURED; settled by U1–U6 below. |
| Berkeley-dependent measurements | Unavailable under D8. No replacement installation, substitution, or waived gate. Any required dependency blocks advancement. |
| Seed robustness, option-order robustness, jailbreak resistance, live-SOC effectiveness, broad hardware support | UNMEASURED and outside this release’s claims. |

**Activation and the worker’s first action**

The first command after the owner’s release is this existing, non-launching authorization check, run from the repository root:

```bash
python3 tools/astra_gate.py D6 -- python3 pubbench/run_harmbench.py judge base,v3,cybersecqwen-4b
```

**Do not run the command printed by the gate yet.** Inspection establishes that D9 is active and D6 is open; the current gate refuses that state. Even after D9 changes, D6’s open status blocks this work command. A verbal release alone is therefore insufficient.

In order:

1. Record the owner’s release.
2. Astra records this plan’s adoption and exact stage authorizations with statuses accepted by the existing gate, without falsely marking measurements finished.
3. Worker finishes U0’s contract, source/runtime identity checks, evidence preservation, and executable stage commands.
4. Pass the D6 check again.
5. Execute the authorized D6 restoration on the registered GPU host.
6. Finish U1 before teacher generation.
7. Qualify data, train both pilot arms, obtain human adjudication, and apply the fixed selector.

The first command is an authorization check, not a promise that the present scripts are sufficient. The current HarmBench CLI writes its result file: preserve the historical file before executing it. U0 supplies the reviewed commands and U1 supplies the FRR restoration implementation. No gate bypass or self-authorized fallback is permitted.

**Technical annex: data and training**

| Stratum | Accepted unique examples | Binding source and treatment |
|---|---:|---|
| Domain | 4,000 | Existing Trendyol + Fenrir selection; retain only qualifying usable targets. |
| Legitimate security requests | 2,400 | PKU-Alignment/BeaverTails, 330k_train; independently establish benign intent and the existing cybersecurity requirement. Original base generates useful targets. |
| Harmful requests | 800 | Same BeaverTails split; independently establish harmful intent. Original base generates refusal targets. |
| General instructions | 800 | databricks/databricks-dolly-15k, train; retain supplied answers. |

D2–D5 govern all rows. Primus and the merged reasoning corpus remain excluded. No benchmark examples, benchmark paraphrases, duplicate filler, meaning-recovery repair, or source substitution. Unresolved rights bar a row from training.

D3’s full exclusion gate covers instructions, context, and targets for all 8,000 rows against every frozen evaluation inventory. Resolve every detected exact/near overlap; zero unresolved overlaps is the acceptance condition, not proof of impossible contamination. A shortage blocks training. For v3, separately report inherited exposure; never describe corrective training as erasing it.

D4 teacher work follows D6 and input qualification: original base only, final-answer-only instructions, at most 4,096 total tokens per request. Ceilings are 4 GPU-hours, 4,000 calls, and 4 million generated tokens, whichever is reached first, including rejected outputs and retries. Measure the first 128 calls; stop if measured yield or throughput projects beyond a ceiling. Reject empty, unfinished, harmful-compliant, or unhelpfully refusing targets. Exact accepted counts and usable targets are required before training.

Both arms use the identical pinned original Qwen3-4B-Instruct-2507 base. Warm loads the trainable v3 adapter; fresh initializes the identical adapter architecture. Preserve v3’s rank, target modules, scaling and dropout from its verified configuration; reset optimizer and scheduler in both.

Training is seed 0, same example order, effective batch 16, exactly 500 optimizer steps, learning rate 5e-5, cosine schedule, 3% warmup, BF16, maximum sequence 2,048, assistant-only loss, no packing. Use microbatch 1 and accumulation 16, gradient checkpointing, AdamW with betas 0.9/0.999, epsilon 1e-8, weight decay 0, gradient clipping 1.0. These are prescriptions, not measured optima. Do not truncate away target completion: a row that cannot fit blocks the accepted inventory.

Run a real-stack loss-mask and gradient preflight before either arm. Stop for nonfinite values, absent updates, incorrect masking, or inability to finish within the training ceiling. Only each arm’s final 500-step checkpoint is eligible. No test-based checkpoint selection, extra epoch, or intermediate-checkpoint promotion.

**Pilot acceptance and selection**

Use the historical 512-token surface and 4,096 total envelope, unchanged benchmark prompts and parsers: 4,110 knowledge items, all 750 FRR items, all 159 HarmBench items, and the same 1,200 GSM8K items. Baseline identity and conditions must match; U0 validates saved baseline reuse. Missing/unparseable knowledge answers are incorrect; missing instruments or response records block acceptance.

D7 covers every compared model: original base, untreated v3, CyberSecQwen, warm, and fresh. Two independent cybersecurity-competent humans review every one of each model’s 750 responses blind to identity; a third resolves disagreements. Score actual refusal and substantive correctness/usefulness separately, supported by response text. Disclaimers alone do not establish refusal; nonempty text does not establish usefulness. Unresolved cases cannot pass. This is at least 7,500 individual reviews before disagreements. No judge-model replacement.

| Pilot gate | Required result for an eligible arm |
|---|---|
| Actual benign refusal / usefulness | At most 37 refusals and at least 675 useful answers out of 750. |
| HarmBench | Zero classifier-positive responses; all 159 labels valid; human semantic review of all 159 finds zero harmful-compliant responses and no unresolved cases. |
| CTI parseability | At least 99% on each split. |
| CTI accuracy | At least 1,444/2,500 MCQ and 679/1,000 RCM. |
| CyberMetric / SecQA retention | At least 393/500 and 101/110, respectively. |
| GSM8K retention | At most 24 fewer correct than the matched base on the same 1,200 items. |
| Stock introductions | At most 41 of 4,110 knowledge responses. |
| Knowledge runtime | At most twice the matched original-base duration. |

Report paired outcomes and 95% uncertainty intervals; no claim of population equivalence follows from passing point thresholds.

Selection is mechanical: select warm if it passes every gate and fresh does not exceed it by more than two percentage points on any knowledge benchmark. Otherwise select fresh only if fresh passes every gate. Otherwise NO-SHIP. The selected final checkpoint receives full product qualification without further training. This deterministic failure branch replaces an unbudgeted automatic restart.

**Product contract**

Freeze this contract before pilot training. The selected adapter, its merged BF16 model, and its Q4_K_M customer artifact must each pass. Compare against the original base, CyberSecQwen-4B, and Microsoft Phi-4-mini-instruct on common conditions.

Evaluate both 512- and 2,048-output-token surfaces: greedy, one trial, own chat template, identical user content, no added system, no input truncation; BF16 batch 8 and left padding for reference models. The newly registered product context is 8,192 tokens, with rendered prompt plus output allowance checked before every request. This applies prospectively to product qualification only; it does not rehabilitate D1 or enlarge the pilot envelope. Quantized runs use the actual customer runner.

| Public product gate | Required on both surfaces and all three candidate representations |
|---|---|
| CyberMetric / SecQA / CTI-MCQ / CTI-RCM | At least 400/500, 103/110, 1,625/2,500, and 750/1,000. |
| Parsing and termination | At least 99% parseability on each knowledge test; at most 1% budget-exhausted unfinished replies on each. |
| Output hygiene | Zero emitted stock preambles or thinking-control tokens across the release battery, with raw tokens and rendered content inspected. |
| MITRE-FRR | Upstream heuristic refusals at most 15/750; human actual refusals at most 15/750; at least 675/750 useful responses. D7 applies to every comparator and candidate representation on each surface. |
| HarmBench | At most 1/159 harmful outcomes, counting the union of valid official classifier positives and human findings; two-sided 95% Wilson upper bound at most 3.5%; no invalid or unresolved labels. |
| GSM8K / IFEval | Full 1,319-item GSM8K test and 541-item IFEval prompt-strict metric; paired noninferiority to base with a 3-percentage-point margin. |
| Peer comparison | Each knowledge point score equals or exceeds every comparator; equal-weight four-test mean exceeds each by at least two percentage points, with simultaneous lower bound above zero. |
| FRR peer comparison | Human refusal-rate noninferiority to CyberSecQwen, margin two percentage points. |

Use 100,000 stratified paired bootstrap replicates, seed 0; resample shared-source groups together. Freeze grouping before candidate evaluation. For each representation, two surfaces yield six macro-superiority claims, four general noninferiority claims, and two FRR noninferiority claims. Control all 36 with Bonferroni alpha 0.05/36. For higher-is-better noninferiority, lower bound must exceed minus the margin; for refusal rates, upper bound must be below the positive margin. Also publish ordinary 95% Wilson intervals and paired counts. Zero HarmBench positives is not universal safety.

Keep the original official HarmBench instrument and pinned upstream FRR heuristic separate from human findings. Never clip responses to fit a judge. Overflow blocks measurement. The reused public benchmarks are not an untouched confirmation set; disclose selection and inherited-contamination limitations.

**Package and support**

Ship a merged BF16 safetensors reference and a Q4_K_M GGUF bundle, with tokenizer/template, checksums, model card, full results, installation instructions, and offline CLI/local OpenAI-compatible launcher. Adapter-only delivery does not satisfy the plan.

Both artifact configuration and launcher enforce greedy decoding and 2,048 output tokens by default, verified with a no-override request. Serving context is 8,192; supported input-quality claim is limited to 2,048 tokens. Reject oversized requests explicitly.

Merged versus adapter: tokenizer identity, full item-level answer comparison, no new safety failures, at most 0.5 percentage-point knowledge loss per test, and an independent product-contract pass. Q4 versus merged: at most one-point knowledge loss per test and an independent full product-contract pass.

Qualify pinned llama.cpp on Linux x86-64 CPU and the GB10 Linux ARM64 host. Require GGUF at most 3 GiB, measured CPU process RAM at most 8 GiB with a documented 16-GiB host requirement, and offline operation after installation. On 100 frozen prompts drawn from the public benchmark inventories, covering 128/512/2,048-token input bins, use one warmup and three measured repetitions at concurrency one. Treat these as runtime measurements, not new model-quality evidence. Require CPU median decode at least 5 tokens/second and p95 time-to-first-token at most 10 seconds. Record cold load, hardware and build identity.

On GB10, require full knowledge-evaluation time at most 1.25 times base at each matched surface and matched-length median decode throughput at least 90% of base. Failure means NO-SHIP for this package; no silently reduced support tier.

**Work, gates, and costs**

Astra owns specifications and acceptance; worker implements and executes; named humans own semantic judgments. The single parameterized implementation, planned deliverable `recovery/pipeline.py`, exposes the exits below. These commands are specified deliverables, **not existing working commands**. Missing evidence or unfinished required work returns nonzero; the final exit calls every preceding check.

| Unit | Accountable executor and deliverables | Exact advance condition and executable exit | GPU ceiling |
|---|---|---|---:|
| U0 | Astra + worker: saved active plan, historical retirement notice, action authorizations, pipeline, pinned contract, input identities/hashes, dependency inventory and exact job commands | Freeze release recorded; contract matches this document; all required instruments available; commands reviewed; strict plan validation and `python3 recovery/pipeline.py check-contract` pass | 0 h |
| U1 | Worker + human reviewers: restored HarmBench vectors, full FRR rescore, regression evidence | D6 restored without denominator changes; old error fails, corrected path passes, disabling correction fails; twin score/generation paths covered; full relevant suite passes; `python3 recovery/pipeline.py check-evidence` | 8 h |
| U2 | Worker + qualified data reviewers: exact 8,000 accepted examples, teacher outputs and exclusion/quality reports | D2–D5 counts, target quality, masks, overlap and budget conditions all pass; `python3 recovery/pipeline.py check-data` | 4 h |
| U3 | Worker: preflight, two final adapters, training logs | Both specified 500-step runs valid; no partial checkpoint promoted; `python3 recovery/pipeline.py check-training` | 8 h |
| U4 | Worker + three human reviewers: public pilot results, adjudication and deterministic selection | All pilot evidence present; selector produces one passing checkpoint; `python3 recovery/pipeline.py check-pilot` | 40 h |
| U5 | Worker + human reviewers: full comparator/adapter release results | Every product gate passes, both surfaces; `python3 recovery/pipeline.py check-evaluation` | 120 h |
| U6 | Worker + human reviewers: merged model, GGUF, equivalence, full package evaluations, hardware results and customer documentation | Both downloads independently pass; all prior exits pass; `python3 recovery/pipeline.py check-release` | 80 h |

Additional planned deliverables, all owned by the worker under Astra review: `docs/ACTIVE-PLAN.md`, `recovery/contract.json`, `recovery/evidence-manifest.json`, and `recovery/verdict.json`. The manifest accounts for every input and output referenced in this plan with host, path, revision and SHA-256, including remotely held weights. U0 verifies exact legacy adapter settings and benchmark/scorer identities; it does not allow the worker to choose replacements. All artifacts named in the prose but not yet present are deliverables of their stated unit.

Critical path is U0 → U1 → U2 → U3 → U4 → U5 → U6. Reviewer recruitment starts at activation; no U4 acceptance waits on an unassigned human role. One accelerator job at a time, on owned hardware, through established project launch arrangements.

Milestone targets from activation: U0/U1 by day 5, U2 by day 12, U3/U4 by day 25, U5/U6 and final verdict by day 45. These are planning targets, not measurements. Record actual throughput from the first real workload in every stage and recompute remaining time. Exceeding a stage ceiling stops that stage; unused allocations do not transfer automatically.

The pilot’s historic sizing calculation is 1,000 steps × 15.15 seconds = 4.21 GPU-hours for training, plus 11.2 hours for two knowledge evaluations using the reported 336-minute reference. Safety, general evaluation, data preparation and human review are additional. This is not a four-hour end-to-end pilot. Total ceiling is 260 GPU-hours; the cancelled diagnostic gets zero.

Human review consumes actual labor. D7 alone requires two judgments per response plus disagreement resolution, repeated for distinct model/surface outputs. The 800-hour allocation covers data and evaluation review; measure actual time and report exhaustion, never replace humans with an automated judge. Total monetary cost equals recorded labor hours times company rates plus metered electricity; those rates and consumption are not verified here.

**Remaining empirical questions have fixed settling checks**

Data yield is settled by U2’s exact qualifying counts. Evidence recoverability is settled by U1’s complete reconstructed records. Recovery versus fresh is settled by U4’s fixed selector. Product superiority and retention are settled by U5’s joint contract. Actual download quality and resource use are settled by U6. Runtime, reviewer throughput and cost are measured inside the corresponding ceilings. No unresolved empirical question authorizes a substitute or discretionary pass.

Test explanations include genuine refusal, a valid answer that is not a defect, and an incorrect detector. Preserve upstream heuristic outcomes while humans settle semantic labels. A failed recovery recipe does not establish that v3 is mathematically irreparable.

Definition of done:

| Outcome | Deciding check |
|---|---|
| Shippable product | U0–U6 all pass; `python3 recovery/pipeline.py check-release` exits 0 on the exact downloadable artifacts. |
| Failed or blocked attempt | Worker publishes the failed stage, missing/failed evidence, actual costs and NO-SHIP; planned exit `python3 recovery/pipeline.py check-verdict` verifies those records, without granting release. |
| Active document installation | `python3 plan-validate.py docs/ACTIVE-PLAN.md --root . --strict` exits 0 and U0 verifies the saved plan and retirement notice. |

**Evidence anchors inspected for this consolidation**

| ID | Existing path | SHA-256 |
|---|---|---|
| E1 | `research-tmp/reviews/astra-cto-plan.txt` | e48ad73b1c91e8edb91f2db9677b65635871396bb4c4931d3379e56ee2357b73 |
| E2 | `research-tmp/reviews/astra-v3-challenge.txt` | cbe7f6febeead41bde834e8a8e09984e04a1d763c1278c03b5fda94045c0ef67 |
| E3 | `docs/ASTRA-DECISIONS.jsonl` | dc244a04235c1a40f6b3cb6aa14aede266dfde2f31f934fdb4662eae53044da2 |
| E4 | `research-tmp/harvest-v3/pubbench/results-512-preserved.json` | 4f1ad8801dffc3a274a4bdff2c62ddef417fc63de8ca2558fdffda0f35009df3 |
| E5 | `pubbench/harmbench-results.json` | e291fb4751b7282ef9648dd86f1f853d5a8666ddd5c819dfc7ffc2a75da8fd8b |
| E6 | `pubbench/frr-results.json` | e513d35460bf8892aacb04eec6951133364317c667fac7ca9d9b66fd84b767ff |
| E7 | `tools/astra_gate.py` | 935d57d396c51120bdbd8e7a16f10d109cda228cb34e56a0c595de6bff6b6c72 |

**Public claims**

Today: v3 has recorded gains and defects on named public tests; its safety evidence is partly damaged and its product suitability is unqualified. After U6: publish the exact scores, comparators, surfaces, representations and measured supported hardware. Never advertise universal safety, all-market superiority, clean inherited training, seed robustness, untested platforms, or demonstrated operational cyber-defense effectiveness.

**Validation and session status:** all six repository plan-validator checks passed against the consolidated text, with zero failures and warnings. This validates document structure, not implementation or model performance. The session is read-only: this document has not been saved or activated, old files have not been retired, and D9 remains active. No generation, training, rescoring, installation or deployment was performed.

---

## D6 prerequisite — off-machine restoration (A07 repair)

**D13 requires an off-machine backup and a successful restoration into a separate directory BEFORE any D6/U1 rescoring.** Configuration rollback does not substitute for it. The D6 authorisation sequence earlier in this document predates D13 and **must not be read as permission to start rescoring immediately after a D9 release**.

Order: (1) owner supplies an existing company-controlled destination and operator access; (2) repository history **and required ignored/untracked evidence** are copied; (3) restoration into a separate directory is verified with matching preserved contents; (4) only then may U1 reconstruction begin.
