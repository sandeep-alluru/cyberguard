# top-models.md — how to obtain or train a top-tier defensive model at small scale

**Sprint:** CYBERGUARD research sprint, 2026. **Deliverable 4 of 4.**
**Read first:** `ARTIFACT-MAP.md`, `docs/SPEC-V2.md` (§1 measured baseline, §6 mixture, §8 budget),
`docs/CAPABILITY-v1.md` (the gap map this recipe must close), `docs/DATASET-V2.md`.
**Companion:** `datasets.md` (what to add), `vulnerabilities.md` (what to gate).

**The decision this file supports:** CyberGuard already proved an owned-hardware training pipeline
(v1: LoRA r=32, Qwen3-4B-Instruct-2507, 10,608 samples in 10,271.6 s ⇒ **0.9683 s/sample**, 0.2049
epoch). The question now is what a *strong* defensive model costs and which parts are buyable,
borrowable, or genuinely out of reach at this scale.

---

## 0. Evidence integrity (important — read this)

- **Four arXiv IDs supplied to a research thread were wrong and were corrected by opening both.**
  Keep this list; it is a contamination risk for anyone reusing the search terms:

  | Supplied | Actually is | Correct ID |
  |---|---|---|
  | 2410.05295 | AutoDAN-Turbo (a jailbreak agent) | **2310.20624** — LoRA fine-tuning undoes safety |
  | 2405.14734 | SimPO | **2405.16833** — Safe LoRA (NeurIPS 2024) |
  | 2410.02743 | MA-RLHF | Inoculation Prompting — **not established** |
  | 2409.05076 | PIP (LVLM adversarial detection) | Representation Rerouting — **not established** |

- Tiers used below: **[V]** fetched this sprint; **[C]** canonical URL, not fetched this sprint;
  **[U]** UNVERIFIED.
- `web_search` was captcha-blocked; evidence came from direct `web_fetch` of HF APIs/cards and arXiv
  abstract pages, plus the GitHub API.
- **No number in this file is a measurement by this project.** All are quoted from sources.

---

## 1. The model landscape — what is actually obtainable

Two *different* things are called "defensive models". Conflating them is the most common planning
error:

- **Guardrail classifiers** (small, narrow, high-accuracy at one binary/multi-class judgement):
  Llama Guard, ShieldGemma, Granite Guardian, Prompt Guard, Qwen3Guard, gpt-oss-safeguard. These are
  the right component for L1/L2 filtering in `defense-architecture.md`, **not** for domain expertise.
- **Domain expert models** (continued-pretrained / SFT'd cybersecurity models): Foundation-Sec,
  Primus, CyberPal, Lily, kin-cybersecurity. These answer security questions.

A defensive stack needs **both**: a guardrail for input/output policing and an expert for triage.

| Model | HF id / URL | Params | License | Weights open? | Why it matters |
|---|---|---|---|---|---|
| **Foundation-Sec-8B** | https://huggingface.co/fdtn-ai/Foundation-Sec-8B · [arXiv 2504.21039](https://arxiv.org/abs/2504.21039) [V] | 8B (Llama-3.1) | Apache-2.0 [V on card reporting] | **Yes** (+ GGUF: https://huggingface.co/Mungert/Foundation-Sec-8B-GGUF [V]) | The closest open analogue to what this project is building. **Matches Llama-3.1-70B and GPT-4o-mini on certain cybersecurity-specific tasks** after continued pretraining on a curated security corpus [V] |
| Foundation-Sec-8B-Reasoning | https://huggingface.co/fdtn-ai/Foundation-Sec-8B-Reasoning [V] | 8B | as above | Yes | Reasoning variant; relevant to the ID-grounding/format gaps |
| **CyberPal 2.0** | [arXiv 2510.14113](https://arxiv.org/abs/2510.14113) [V] | **4B** | see report [C] | Corpus not clearly published [C] | **The single most relevant precedent:** a **4B** security SLM ranks **second only to Sec-Gemini v1** on threat-investigation tasks, ahead of GPT-4o/o1/o3-mini — via expert-in-the-loop grounded CoT data, not scale [V] |
| Primus (family) | https://huggingface.co/trendmicro-ailab · [arXiv 2502.11191](https://arxiv.org/abs/2502.11191) [V] | 8B-class | MIT (per report) [V] | Yes | CPT gives **+15.88 %** aggregate; reasoning distillation **+10 % CISSP**; the data is lopsided — **3.39 M CPT rows vs 835 instruct rows** [V] |
| Granite Guardian 3.2 5B | https://huggingface.co/ibm-granite/granite-guardian-3.2-5b [V] | 5B | **Apache-2.0** [V] | Yes | Guardrail classifier with explicit risk taxonomy (harm, jailbreak, social bias, groundedness, answer relevance, function-call validity, evasiveness) [V] |
| Qwen3Guard-Gen-{0.6B,4B,8B} | [C] | 0.6–8B | **Apache-2.0** [reported V] | Yes | Cleanest-licensed guard family; sizes fit the L3 envelope |
| gpt-oss-safeguard-{20,100}b | [C] | 20B/100B | Apache-2.0 [reported V] | Yes | Larger policy-following guardrails |
| Lily-Cybersecurity-7B-v0.2 | https://huggingface.co/segolilylabs/Lily-Cybersecurity-7B-v0.2 [V] | 7B | Apache-2.0 [V] | Yes (GGUF) | Open cyber domain model; useful as a **comparison arm**, not a base |
| kin-cybersecurity-3b | https://huggingface.co/nyxspecter4/kin-cybersecurity-3b [V] | 3B (Qwen2.5) | Apache-2.0 [V] | Yes | Explicitly SOC/DFIR/ATT&CK + local deployment — matches the `defense-architecture.md` L3 target exactly |
| Llama-Prompt-Guard-2-* | [C] | small | **gated**, Llama 4 Community License [V] | gated | Injection/prompt classifier; gating is a friction point |
| Llama-Guard / ShieldGemma / NemoGuard | [C] | small | various | yes | Guardrail baselines |
| RedSage, SecGPT, Artemis, BlindGuardian, Aegis | [C]/[U] | — | — | mixed | **Could not be verified this sprint — [U].** Do not plan around them. |

**Caveat that must temper all of the above** (measured, and directly relevant to a 4B project): a 2026
study of 8 domain-adapted LLMs/SLMs on STRIDE found domain adaptation "does not consistently
outperform their general-purpose counterparts", and scale gains were "neither consistent nor
sufficient for reliable threat modelling" ([2605.10808](https://arxiv.org/abs/2605.10808)) [V].
**Domain-adapted ≠ automatically better.** That is why `SPEC-V2.md` correctly insists on a control
arm (Arm A vs Arm B) rather than assuming the mixture helps.

---

## 2. What the strongest models actually did (the data recipe)

| Model | Data pipeline | Concrete numbers |
|---|---|---|
| **Foundation-Sec-8B** | Continued **pretraining** on a "carefully curated cybersecurity corpus" (not SFT-first) | Base Llama-3.1-8B; matches Llama-3.1-**70B** and GPT-4o-mini on certain cyber tasks [V]. Report: [2504.21039](https://arxiv.org/abs/2504.21039) |
| **Primus** | Large-scale domain **CPT** + small instruct/ reasoning distillation | **3.39 M CPT rows** vs **835 instruct rows**; CPT **+15.88 %**, reasoning distill **+10 % CISSP** [V]. Report: [2502.11191](https://arxiv.org/abs/2502.11191) |
| **CyberPal 2.0** | **Expert-in-the-loop, grounded CoT** dataset (`SecKnowledge 2.0`) | 4B model, 2nd only to Sec-Gemini v1 on threat investigation [V]. Report: [2510.14113](https://arxiv.org/abs/2510.14113) |
| **IBM Granite LLM intrinsics** | Small, composable **LoRA adapters** on Granite 3.3 8B for RAG skills | Released as adapters + vLLM interface — precedent that *capability-as-adapter* is a viable unit of work [V]. [2504.11704](https://arxiv.org/abs/2504.11704) |

**The lesson that matters most for a 24-hour budget:** every strong model above got its knowledge from
**continued pretraining on a large curated corpus**, and its behaviour from a much smaller
instruction stage. Primus's 3.39 M : 835 ratio is extreme but directionally unambiguous. This is
exactly the SFT-vs-CPT tension `SPEC-V2.md` §1.1 already flags, and it is why the honest reading of a
24 h LoRA-SFT run is **behavioural change, not new knowledge** (§4, §7).

---

## 3. Safety degradation is measured, cheap, and predictable — plan for it

v1's refusal collapse (24/60 → 6/60) is **not an anomaly**; it is the documented default.

| Finding | Number | URL |
|---|---|---|
| Fine-tuning on **10 adversarial examples for <$0.20** removes safety from GPT-3.5 | 10 examples, <$0.20 | [2310.03693](https://arxiv.org/abs/2310.03693) [C] |
| **LoRA fine-tuning undoes safety training** in open models — one GPU, **< $200** takes Llama-2-Chat-70B to **~1 % refusal** | <$200, 1 GPU, ~1 % refusal | [**2310.20624**](https://arxiv.org/abs/2310.20624) [C] |
| Safety alignment is only a **few tokens deep** — shallow alignment is why fine-tuning erases it | explains the mechanism | [2406.05946](https://arxiv.org/abs/2406.05946) [C] |
| **LIMA**: "almost all knowledge in LLMs is learned during pretraining"; SFT teaches **format** | 1,000 examples | [2305.11206](https://arxiv.org/abs/2305.11206) [C] |

**The mitigations, ordered by effort-to-benefit for a 24 h LoRA run:**

| Technique | Mechanism | Measured effect | URL |
|---|---|---|---|
| **Safe LoRA** ✦ | Training-free, data-free: project the LoRA update onto the "safety subspace" | NeurIPS 2024 | [**2405.16833**](https://arxiv.org/abs/2405.16833) [C] |
| **Circuit Breakers (RR)** | Representation-level break; re-route harmful internal states | no-jailbreak under attack in the paper's setting | [2406.04313](https://arxiv.org/abs/2406.04313) [C] |
| **Latent Adversarial Training** | Adversarial perturbations in latent space during training | improves robustness | [2407.15549](https://arxiv.org/abs/2407.15549) [C] |
| **Constitutional Classifiers** | Input+output classifiers over a constitution, adversarially trained | **0 universal jailbreaks in 3,000+ red-team hours**, +**0.38 %** production refusals, **23.7 %** inference overhead | [2501.18837](https://arxiv.org/abs/2501.18837) [C] |
| **Instruction Hierarchy** | Explicit precedence: system > user > tool output | foundational for the MCP design | [2404.13208](https://arxiv.org/abs/2404.13208) [C] |
| **Deliberative Alignment** | Teach the model to reason explicitly about the policy before answering | OpenAI's reported alignment method | [2412.16339](https://arxiv.org/abs/2412.16339) [C] |
| **TAR (tamper-resistant safeguards)** | Safeguards that resist removal fine-tuning | relevant if weights are ever shared | [2408.00761](https://arxiv.org/abs/2408.00761) [C] |
| Inoculation Prompting / Lisa / Vaccine fine-tuning / Representation Rerouting | various | **[U]** — IDs not established this sprint; verify before citing | — |

✦ **Safe LoRA is the highest safety-per-effort action available to this project** — one line, no GPU
time, no data, applied to a LoRA that is already being trained.

**Also from the safety literature, directly relevant to v1's defect set:** the measured v1 failures
(refusal loss, format non-compliance, ID fabrication) are all **behavioural**, so the appropriate
levers are data mix, loss/objective, and decoding constraints — consistent with `SPEC-V2.md`'s
testable-but-unproven hypothesis.

---

## 4. The arithmetic of a 24-hour, 4B, single-host run

Basis of record from v1: **0.9683 s/sample** (whole-run wall incl. overhead), batch 2 × grad-accum 8,
seq 2048, LoRA r=32, Qwen3-4B-Instruct-2507 (`receipts/cyberguard-lora-v1.json`).

| Quantity | Value |
|---|---|
| 24 h = 86,400 s | — |
| Samples in one 24 h arm | **86,400 / 0.9683 ≈ 89,200 samples** |
| Tokens (at ~895 tok/sample, v1's measured median) | **≈ 80 M tokens** (range ~45–160 M depending on mix) |
| A 30 k-sample dataset at 1.0 weight | **≈ 3 epochs** in 24 h |
| Two arms in parallel (Arm A / Arm B) | doubles to ~178 k samples total; `SPEC-V2.md` U3 already specifies this |

**What that buys:** enough exposure to change **format compliance, refusal behaviour, and
refusal-retention** on a specific task distribution, and enough epochs to overfit a small authored
set if not controlled. **What it does not buy:** new domain knowledge (LIMA), reasoning ability, or
robustness to adaptive attacks (Circuit Breakers/Constitutional Classifiers were trained with
adversarial loops and much more compute).

**What 10–100× more compute would buy (and is therefore explicitly out of scope now):**
- **Domain CPT** at Primus scale: 2.57 B tokens of Primus-FineWeb at the v1 SFT rate extrapolates to
  **~772 h** (`SPEC-V2.md` §1.1) — i.e. ~32× a 24 h window for one pass over the corpus, before any
  tuning. `SPEC-V2.md` U11 (CPT throughput probe) exists precisely to replace this extrapolation with
  a measurement. **Nothing here should be read as claiming a useful CPT slice is impossible** — only
  that it is unmeasured.
- **RL/RLVR or deliberative-alignment-style training** — reward models, sampling loops, verifier
  infrastructure.
- **Adversarial training loops** of the Constitutional Classifiers kind (3,000+ red-team hours).
- **A from-scratch frontier-scale model** — 3–6 orders of magnitude beyond this fleet.

---

## 5. Evaluation: what to use, and what must be held out

**Benchmarks to run (and their contamination status):**

| Benchmark | URL | Role |
|---|---|---|
| CTI-Bench | https://github.com/maveryn/cti-bench | **EVAL-ONLY.** Already eval in DATASET-V2 |
| SecQA / SecEval / SecBench | [C] | **EVAL-ONLY** (mostly NC-SA) |
| CyberSecEval (PurpleLlama) | https://github.com/meta-llama/PurpleLlama | EVAL harness; license "Other" [V] |
| CyberGym | https://arxiv.org/abs/2506.02548 | Real-vuln agent eval; 1,507 vulns, ~20 % ceiling [V] |
| CVE-Bench | https://arxiv.org/abs/2503.17332 | Real-CVE agent eval; up to 13 % [V] |
| HonestCyberEval | https://arxiv.org/abs/2410.21939 | Synthetic-injection upper bound (92.85 %) [V] |
| WMDP | https://huggingface.co/datasets/cais/wmdp | **EVAL-ONLY**; hazardous-knowledge proxy [V] |
| HarmBench / JailbreakBench / StrongREJECT / AgentHarm / AdvBench | see `datasets.md` §5 | **EVAL-ONLY** [V] |
| AgentDojo / InjecAgent / ASB | see `datasets.md` §6 | **EVAL-ONLY**; the MCP instrument [V] |
| Cybench / NYU CTF | [C]/[U] | offensive-capability eval; **not verified this sprint** |
| MITRE ATLAS (taxonomy) | https://github.com/mitre-atlas/atlas-data | label/coverage source, content **2026.05**, format **6.0.0** [V] |

**Non-negotiable rule from v1:** every benchmark above stays **out of training**. v1's own experience
is the proof of why the *fixture*, not just the data, must be held out — its 12-probe fixture passed
while the 60-probe battery measured 6/60 (`VERDICT-v1.md`, `CAPABILITY-v1.md`).

---

## 6. Recommended recipe for a 24-hour, 4B, single-GB10 run

Framed as a **behavioural** intervention (matching `SPEC-V2.md`'s SFT-first scope decision), with the
knowledge path explicitly deferred to a measured CPT probe (U11).

### Stage 0 — baseline and instruments (no GPU)
1. Freeze the parent: `Qwen/Qwen3-4B-Instruct-2507`, fresh — *not* v1's adapter (§U3).
2. Build/re-verify instruments **before** training: refusal battery at powered n, ID validator
   (CVE/ATT&CK **and ATLAS**), format-compliance checker (Sigma via pySigma), injection battery
   (AgentDojo/InjecAgent), rubric with index-integrity QA.
3. Measure parent on all of them. **A run without a measured parent is not interpretable.**

### Stage 1 — data (the part that actually decides success)
1. Unescape the corpus (v1's literal `\n` artifact), re-run split + safety audit.
2. Assemble the mixture per `SPEC-V2.md` §6 — Trendyol core, refusal set (weight 8.0), format set,
   ID grounding (NVD + ATT&CK + **ATLAS**), conversational replay in **both** arms.
3. **Add the gaps from `datasets.md`:** real CTI text (extraction), SigmaHQ/Splunk (format), Aegis 2.0
   (safety classification), and — if the MCP service is in scope — AgentHarm-style refusal-after-tool-
   call examples. Keep every eval-only set out.
4. Run the **U1 admission gate** (13-gram + containment) and **U13 data-integrity gate** before any
   GPU minute. Owner's rule: never discover bad data mid-run.

### Stage 2 — training (two arms, 24 h each, parallel)
- Arm A: designed mix. Arm B: refusal rows replaced in place by matched non-refusal rows (control).
- Effective batch 16, LR 1e-4, cosine, warmup_ratio 0.03, schedule horizon = full lineage (avoid
  v1's mid-flight re-schedule bug where cosine ended at 90 % of peak), LoRA r=32, bf16, max_seq
  re-measured on the new mixture.
- Checkpoints at C8/C16/C24; **C24 is the only confirmatory analysis** (descriptive looks at C8/C16).
- Receipts with `mask_check`, coverage in weighted presentations, parent identity, decode surface.

### Stage 3 — safety retention (cheap, do it)
- Apply **Safe LoRA** projection ([2405.16833](https://arxiv.org/abs/2405.16833)) to each arm's
  adapter — training-free.
- Optionally train a **guardrail** as a separate small component (Granite Guardian 3.2 5B or
  Qwen3Guard Apache-2.0) rather than expecting one model to be both expert and guard. Two small
  models with different jobs beat one model with a conflicted objective.

### Stage 4 — evaluation and gates
- Raw **and normalized** F1 (v1's escape artifact makes the raw number uninterpretable), paired CIs.
- Refusal gate at powered n with a rubric + index-integrity QA.
- ID validator pre/post on ≥300 emitted IDs.
- Format gates: one-word verdict, Sigma schema-complete via pySigma.
- Injection residual against the MCP pipeline if that service is being built.
- **Failure is a result**: report FAIL with CIs, never re-label (`SPEC-V2.md` §7).

### What NOT to attempt at this scale
| Not now | Why |
|---|---|
| Domain CPT over Primus-FineWeb | ~772 h extrapolated for one pass; measure first (U11) |
| RL / RLVR / reward models | needs sampling infra + compute this fleet lacks |
| Adversarial training à la Constitutional Classifiers | thousands of red-team hours |
| From-scratch pretraining | 3–6 orders of magnitude out of scope |
| Expecting a 4B model to match GPT-4o on exploitation | CVE-Bench 13 %, CyberGym ~20 % are *frontier* numbers; 4B is far below |
| One model for expert + guard + format | roles conflict; compose small specialists instead |

---

## 7. The honest bottom line

1. **The strongest open defensive models got there by continued pretraining on a large curated
   corpus** (Foundation-Sec: 8B matching 70B; Primus: 3.39 M CPT rows / +15.88 %). At 24 h and one
   GB10, **we cannot buy that**. We can buy behaviour: refusal retention, format compliance, ID
   grounding — precisely the three v1 defects that `CAPABILITY-v1` measured. That alignment is not a
   coincidence; it is the same conclusion the v2 plan reached independently.
2. **A 4B model can be genuinely competitive on a narrow task.** CyberPal 2.0 (4B) ranks second only
   to Sec-Gemini v1 on threat investigation [V]; OpenSOC-AI got F1 0.68 from a **1.1B** LoRA trained
   in <5 minutes [V]. Narrowness is the lever, not scale.
3. **Safety degradation is the default, not a risk.** Budget for it explicitly (refusal rows at high
   sampling weight + a control arm + Safe LoRA), or the run will reproduce v1's collapse.
4. **Compose, don't monolith.** One domain expert (4B, this project) + one guardrail (Apache-2.0,
   off-the-shelf) + deterministic validators outsourced to code (ID validator, pySigma, ID ledger)
   is a stronger and more auditable system than a single 8B asked to do everything.
5. **The binding constraint is verification, not training.** Every path to a "top-tier defensive
   model" in this file runs through the same gate: powered n, prespecified confidence rules, raw
   receipts, and the discipline to report FAIL. That is the asset this project already has and its
   competitors mostly don't.

---

## 8. URL index

Models: https://huggingface.co/fdtn-ai/Foundation-Sec-8B · https://huggingface.co/fdtn-ai/Foundation-Sec-8B-Reasoning · https://huggingface.co/Mungert/Foundation-Sec-8B-GGUF · https://huggingface.co/segolilylabs/Lily-Cybersecurity-7B-v0.2 · https://huggingface.co/nyxspecter4/kin-cybersecurity-3b · https://huggingface.co/ibm-granite/granite-guardian-3.2-5b

Reports/papers: https://arxiv.org/abs/2504.21039 (Foundation-Sec) · https://arxiv.org/abs/2510.14113 (CyberPal) · https://arxiv.org/abs/2502.11191 (Primus) · https://arxiv.org/abs/2504.11704 (Granite LLM intrinsics) · https://arxiv.org/abs/2605.10808 (domain adaptation ≠ better)

Safety: https://arxiv.org/abs/2310.03693 · **https://arxiv.org/abs/2310.20624** (LoRA undoes safety; NOT 2410.05295) · https://arxiv.org/abs/2406.05946 · https://arxiv.org/abs/2305.11206 · **https://arxiv.org/abs/2405.16833** (Safe LoRA; NOT 2405.14734) · https://arxiv.org/abs/2406.04313 · https://arxiv.org/abs/2407.15549 · https://arxiv.org/abs/2501.18837 · https://arxiv.org/abs/2404.13208 · https://arxiv.org/abs/2412.16339 · https://arxiv.org/abs/2408.00761

Evaluation: https://github.com/maveryn/cti-bench · https://github.com/meta-llama/PurpleLlama · https://arxiv.org/abs/2506.02548 · https://arxiv.org/abs/2503.17332 · https://arxiv.org/abs/2410.21939 · https://huggingface.co/datasets/cais/wmdp · https://github.com/mitre-atlas/atlas-data

Project internal: `receipts/cyberguard-lora-v1.json`, `docs/SPEC-V2.md`, `docs/CAPABILITY-v1.md`, `docs/DATASET-V2.md`

*Marked **[U]** in this file:* RedSage/SecGPT/Artemis/BlindGuardian/Aegis model cards; Inoculation
Prompting, Lisa, Vaccine, Representation Rerouting IDs; Cybench/NYU CTF; CyberPal corpus
availability; GB10 memory-bandwidth specifics.
