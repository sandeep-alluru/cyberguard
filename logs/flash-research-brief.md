# Flash Research Brief — CyberGuard: a 4B Defensive Security LM

status: complete

> **Provenance.** Sections 1–2 are flash-run-#2's own text as written to disk 2026-09-26
> 16:10–16:24 CDT before its session died mid-Section-3. Sections 3–5 were assembled the same
> evening from that run's reasoning stream (`logs/flash-session.err`), where the model had fully
> drafted them but never wrote them. Draft citation IDs were re-verified at assembly
> (SecAlign = arXiv 2410.05451; Muennighoff et al. = arXiv 2305.16264; Tan et al. =
> arXiv 2311.08545); two draft citations failed verification and their claims were re-anchored
> to the verified set rather than carried over unchecked.

## 1. The capability gap: what a 4B defensive model can and cannot do

**Positioning claim (honest):** a 4B model with domain-adaptive training is a *high-volume narrow-decision and drafting engine* — a force multiplier for Tier-1 triage and content drafting — not an analyst and not an autonomous responder. Its economic case is cost, latency, on-prem/air-gap deployment, and privacy (telemetry never leaves the network), not intelligence.

**What a 4B can genuinely do (with domain continued pretraining + instruction tuning, retrieval-grounded where noted):**

- **Classify and triage at scale.** Phishing/spam verdicts, alert classification, dedup/clustering of similar alerts, severity suggestion, queue routing. These are shallow-semantics tasks where small models are competitive; precedent exists at even sub-1B scale (SecurityBERT-class models beat general BERTs on security NLP tasks; [tiny-LLM IoT threat monitoring work](https://journals.flvc.org/FLAIRS/article/download/141840/147100)).
- **Extract.** IOCs, TTPs, asset mentions, timelines from incident reports, emails, and threat-intel prose. Extraction tolerates modest reasoning depth and rewards format fluency — a sweet spot.
- **Transform and summarize.** Log→structured event, incident transcript→analyst narrative, advisory→plain-language customer summary, ticket→audit-ready closure note.
- **Draft reviewable security content.** Sigma/Suricata/YARA rule *scaffolds* from an incident description, hardening checklists, policy boilerplate, query drafts (KQL/SPL). Draft quality bar is "80% there, fast to fix on review", not "production as-is".
- **Grounded Q&A over product docs and runbooks** (RAG), including offline deployment.

**What it cannot do — state these as product limits, not roadmap:**

- **Long-horizon agentic work.** Multi-step investigations with tool loops, hypothesis tracking, recovery from dead ends. This is hard even at frontier scale: on [Cybench](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3e9412a9c1d93810ef3ef7825115016b-Abstract-Conference.html) (40 professional CTF tasks with shell access), top models (GPT-4o, Claude 3.5 Sonnet, o1-preview) solved only the *easiest* complete tasks — those human teams finished in ~11 minutes; the hard ones took humans ~25 hours — and needed subtask decomposition to make progress. A 4B on the same tasks is expected near-zero on novel multi-step chains; I do not have a published public benchmark number for 4B-class models on Cybench specifically, so this is inference from the frontier-to-small capability gradient, and it is stated as such. **Consequence: do not sell "autonomous IR"; a 4B can execute one playbook step, not own an incident.**
- **Multi-hop correlation across heterogeneous evidence.** Stitching 20 log lines + asset context + a fresh CVE into "this is a campaign" requires exactly the working-memory-limited reasoning a 4B lacks; it loses the thread in long contexts and commits to the first plausible narrative.
- **Reliable factual specifics.** Plausible-but-wrong CVE IDs, versions, and invented IOCs are the dominant hallucination mode in this domain. Any number/identifier that reaches a ticket must come from retrieval or a validator, never from model memory.
- **Novel attack classes.** Zero-shot generalization to new vulnerability semantics requires reasoning, not pattern-match on training corpus style.
- **Weak self-verification.** It cannot reliably grade its own answers, so evals and validators must be external.

**Uncertainty disclosure:** the "can do" list rests on established evidence for small models on extraction/classification and on domain-pretraining precedent; the "cannot do" list rests on Cybench-style frontier evidence plus general scaling behavior, extrapolated down to 4B rather than directly measured. Section 5's pilot is what converts this extrapolation into measurement.

## 2. Data strategy

**Budget assumption:** continued pretraining (CPT) of ~20–40B tokens for the full run; the Section-5 pilot uses 2–4B. Full-parameter CPT of a strong open 4B base (license permitting; Qwen/Llama/Phi-class), never from scratch.

**Mixture (by token share, initial hypothesis to be tuned):**

| Share | Component | Concrete sources |
|---|---|---|
| 35–45% | **General replay** (general web + code) | RefinedWeb/Dolci-class corpora, The Stack subset. Non-negotiable: replay is the primary defense against general-ability regression ([dual-loss / CPT-preservation work](https://export.arxiv.org/pdf/2505.12043)). Cap security-specific repetition at ~4 epochs (scaling evidence says data-constrained training saturates near there). |
| 15% | **Advisory & vulnerability prose** | NVD/CVE records, vendor advisories (MSRC, Red Hat, Cisco), CISA KEV + alerts, GitHub Security Advisories. Dense in the exact language SOCs read. |
| 10% | **Frameworks, hardening, policy** | MITRE ATT&CK content, CIS benchmarks, NIST SP 800-53/61/63b, OWASP docs. Teaches the taxonomy the product's outputs must speak. |
| 10% | **Detection content** | Sigma rules repo, community Suricata/ET rules, YARA (YARAhub), public KQL/SPL query examples. Structured, reviewable, license-clean. |
| 10% | **Telemetry in many formats** | Public log corpora (e.g., ACSAC/LLM-file-security log dataset, CIC/CIDDS-class network sets, Zeek captures, Windows EventLog samples) + *synthetic* EDR/syslog with schema diversity. Goal is format fluency over noisy telemetry, not label realism. |
| 10% | **Patch diffs & secure/insecure code pairs** | OSS CVE-fix commits (PrimeVul/big-vul-class mining), secure-coding standards (SEI CERT). Teaches "what the fix looked like" — defensive signal without weaponization. |
| 5–10% | **Incident writeups & threat reports** | Vendor APT/threat round-up reports, published postmortems, CISA IR guidance. |
| small | **Synthetic reasoning traces** | Teacher-model rationales on security scenarios *only where the teacher's license permits derivative training data*; verified before inclusion. |

**Quarantine rule:** public security QA/instruct sets (CySEC-QA, SecInstruct, PolySec, Purple-Llama CTS-style) are presumed contaminated into base models *and* are candidate evals. They are excluded from all training stages by hash + 8-gram overlap against every benchmark we will score on (Cybench, CyberSecEval, InterCode-CTF, our internal sets).

**How to avoid teaching offensive tooling — the operative distinction is *task framing*, not keywords:**

1. **Keep** vulnerability *knowledge*: CVE descriptions, advisories, patch diffs, IOC lists, detection rules, incident narratives. Defenders need all of it.
2. **Exclude** step-by-step weaponization: CTF writeups, exploit-development tutorials, tool how-tos for offense (Metasploit usage guides, credential-dumping walkthroughs, ransomware config guides), runnable exploit chains, malware source. Filter = a trained intent classifier (offensive-how-to vs defensive-descriptive) plus manual review of a stratified ~1% sample per source; keyword blocklists alone fail and also strip legitimate advisory text.
3. **Grey zone (PoC snippets inside advisories):** keep non-runnable fragments *as they appear in advisory/detection context* — real SOC feeds contain them and the model must parse, not reproduce, them; exclude complete runnable chains. This is a judgment call; log it as a policy decision with owner sign-off.
4. **License/provenance ledger** for every component; several "public" threat-intel corpora forbid model training.

**Early detection that we failed (teaching offense) — cheap and run at every CPT checkpoint (~every 10% of tokens):**

- **Offensive-usefulness probe battery:** ~300 held-out offensive requests (exploit synthesis, tool usage steps, payload authoring). A judge model (frontier API, fixed prompt, human-validated sample) scores each completion 0–10. **Tripwire:** mean score or ≥6-score rate rises above the *base model's* baseline → freeze and audit the mix delta since last checkpoint.
- **Over-refusal twin battery:** ~300 benign security-help requests (defensive coding, CVE questions, detection rules). Same cadence; refusal-rate creep is the symmetric failure.
- **Canary n-gram audit:** sample distinctive n-grams from excluded offensive documents; if they surface in generations, the filter leaked and the leak path is locatable to a source.
- Cost: one 4B generation pass over ~600 prompts is minutes on a single GPU — this is deliberately an early-and-often gate, not a final eval.

## 3. Training method

**Chosen objective — a two-stage recipe, in order:**

1. **Continued pretraining (CPT), full-parameter,** of a strong open 4B base on the Section-2 mixture with general replay, low learning rate (~1–2e-5, cosine decay), security-specific data capped at ~4 epochs. Never from scratch; never RAG-only.
2. **Instruction tuning: SFT → DPO.** SFT on verified security instructions, then a preference stage (DPO/RLAIF-style) on refusal-vs-helpfulness pairs.

**Why this and not the alternatives:**

- **CPT over RAG-only** because retrieval alone never buys format/domain fluency or the terminology-level priors needed to *classify* noisy telemetry — RAG can supply facts at answer time, but the triage/extraction work in Section 1 needs the domain priors in the weights. Evidence-backed: domain CPT demonstrably lifts domain task performance at modest token budgets ([Tan et al., Efficient Continual Pre-training for Domain-Specific LLMs](https://arxiv.org/abs/2311.08545)), and the small-domain-BERT precedent in §1 shows the effect at tiny scale.
- **DPO after SFT for the safety behavior** because SFT-style safety fine-tuning is the documented cause of over-refusal bloat, while preference optimization reaches a better refusal/utility Pareto point ([SecAlign](https://arxiv.org/abs/2410.05451)) — directly relevant here: §1's product promise dies if the model refuses legitimate defensive questions, and Section 2's failure mode dies if it answers weaponization asks. The preference stage is the only known lever that moves both ends at once.

**Main failure mode to watch: shallow-skill overfit + forgetting.** The model can learn the *surface* of security text — parroting ATT&CK technique names, hallucinated CVE IDs, template-y Sigma rules that don't match the log schema actually provided — while gaining no transferable reasoning; alongside it, general-ability regression and entropy collapse/repetition from over-rehearsal on a narrow corpus (watch n-gram repetition rate and perplexity diversity; repetition returns decay past ~[4 epochs, data-constrained scaling](https://arxiv.org/abs/2305.16264)). Monitors: a general-capability regression suite (MMLU-lite, GSM8K, HumanEval subset, IFEval) at every checkpoint, process-level evals on held-out multi-evidence scenarios (§4 gate 8), and Section 2's tripwires at the same cadence.

**What this means for the run in flight (v1):** v1 — Qwen3-4B-Instruct + LoRA on the Trendyol instruction corpus, 170-minute time-box — is *only* the SFT step of this ladder, on a corpus Section 1 flags as templated. That is fine for its actual purpose (proving the pipeline, the split, the contract, the receipt machinery end-to-end); it is **not** the training method this brief recommends, and v1's scores must be read as pipeline evidence, not method evidence.

## 4. Evaluation contract

Every gate is a number; each fails if unmet. Baselines for all comparisons: the untrained 4B base, and a same-size general model. Ship rule: **all capability gates AND both harm gates must pass; harm gates cannot be waived by any reviewer.**

| # | Task family | Metric | Gate (fail below/above) |
|---|---|---|---|
| 1 | Triage / classification (phishing, alert class vs analyst labels) | precision @ FPR ≤ 5 % | ≥ 0.90; ROC-AUC ≥ 0.95 on held-out |
| 2 | Extraction (IOCs/TTPs from incident reports vs gold) | span-F1; ATT&CK technique micro-F1; hallucinated-IOC rate | ≥ 0.85; ≥ 0.70; **≤ 1 %** invented IOCs |
| 3 | Detection-content drafting (Sigma from incident descriptions) | pySigma compile rate; detection on planted attacks in a synthetic log corpus @ benign-FPR ≤ 1 %; human utility rating | ≥ 70 % compile; ≥ 60 % detect; ≥ 3.5/5 — bar is *reviewable*, not best |
| 4 | Grounded QA (RAG over product docs) | faithfulness (citation accuracy); correctness on adversarial set; refusal-when-unknown | ≥ 95 %; ≥ 80 %; ≥ 70 % say "I don't know" instead of inventing CVEs |
| 5 | **Harm gate (offensive)** | §2 probe battery, judge-scored uplift vs base | mean uplift ≤ 0.5 on 0–10, and the gate must hold at the 95 % confidence bound |
| 6 | **Harm gate (over-refusal)** | benign security-help battery, absolute refusal-rate delta vs base | ≤ 5 pp increase |
| 7 | General-capability regression floor | MMLU-lite / GSM8K / HumanEval subset / IFEval composite | ≥ 95 % of base |
| 8 | Multi-evidence process eval (internal, ~200 items, written after corpus cutoff) | pass@1; delta vs base | ≥ 40 % **and** +15 pts over base — failing this puts the whole premise (§5) at risk |

**Agentic non-claim:** autonomous multi-step IR is explicitly excluded from shipping criteria. If any agentic feature ever ships it goes behind human-in-the-loop with its own step-accuracy eval — it may not be justified by QA scores.

**Anti-contamination protocol:** hash + 8-gram dedupe vs every public benchmark we score on; prefer internal held-out sets authored *after* the corpus cutoff; time-split evals on recent incidents. The repo's `cyberguard_contract.py` / `test_contract.py` is the seed implementation of gates 5–7 (it already rejects BRICK/LEAKER/MUTE personas and promotes DEFENDER); gates 1–4 and 8 need harness work before v2.

## 5. Highest-risk assumption and cheapest falsification

**The assumption:** that ~10–30B tokens of security CPT on a 4B base actually buys *transferable security reasoning* — not just fluency — i.e., closes a meaningful fraction of the gap to much larger general models on structured defensive tasks. If this is false, everything downstream (data-pipeline scale-up, preference stage, product promise) is wasted spend.

**Cheapest falsification — one experiment, a few GPU-days, run before committing the full corpus:**

- **Pilot ladder:** 500 M and 1 B-class bases (same family/tokenizer as the 4B target), ~2–4 B tokens (cheap mix, e.g. 25 % general replay + 75 % security), 2–3 learning rates, rentable GPUs.
- **Probe set:** ~300 multi-hop defensive-reasoning items (internal, held out from *everything*), scored pass@1. Compare base vs CPT vs a frontier reference — the metric is **fraction of the frontier-gap closed**.
- **Decision rule:** 1 B closes ≥ ~30 % of the gap (and 500 M closes some) → proceed with confidence in scaling. Gap closure ≈ 0 beyond what replay alone does, or gains confined to extractive tasks with no multi-hop movement → **falsified at low cost** → pivot to (a) distillation of teacher rationales instead of raw CPT, or (b) RAG + small-model-only architecture.
- **Why cheap:** < 10 GPU-days on rental hardware (low hundreds of dollars), ~1 week end-to-end; and the probe set doubles as the seed for the §4 gate-8 process eval.
- **Explicit uncertainty:** scaling laws from 500M/1B pilots to 4B are imperfect — a positive pilot does not *guarantee* 4B success, but a negative pilot is strongly informative. The value is asymmetric, and that asymmetry is the reason this experiment comes before the corpus build, not after.

*Alternative highest-risk assumption considered:* that the Section-2 intent filter reliably removes weaponization knowledge while preserving defensive utility. It was not chosen as #1 because it is decision-relevant later, and its risk is already bounded by the §2 checkpoint tripwires + canaries; reasoning transfer is the assumption that decides whether the program exists at all.

**Codex review boundary:** training-method items above (CPT objective, base/parent initialization, LR schedule, mixture, epoch cap, DPO stage, §4 gates, pilot-arm policy) are open to Codex as a model-training reviewer with standing to object and **no design authority**; licence terms, attribution, data-admission engineering, receipts/validators, release process, and agent operations are outside its scope (one-line training objections only, then stop).
