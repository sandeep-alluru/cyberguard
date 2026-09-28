# vulnerabilities.md — AI-powered attack classes + a methodology for finding NEW ones

**Sprint:** CYBERGUARD research sprint, 2026. **Deliverable 2 of 4.**
**Read first:** `ARTIFACT-MAP.md`, `docs/CAPABILITY-v1.md`, `docs/SPEC-V2.md`. Companion:
`datasets.md` (G3/G4/G5 map to §3/§4/§5 here), `defense-architecture.md`, `top-models.md`.

**The scope question this file answers:** what attack classes become materially more dangerous when
the attacker has frontier-model-grade assistance, and how do we *discover vulnerabilities we do not
yet know about* — including the ones our own deployment will create.

**Position statement up front, because it is the honest reading of the evidence:** the frontier risk
is **not** a model that "hacks by itself". As of the sources fetched this sprint, autonomous agents
clear ~13 % (CVE-Bench) to ~20 % (CyberGym) of *real* tasks, while single-shot synthetic-injection
tasks are cleared at 92.85 % (HonestCyberEval). **The measured risk is cheap, fast, high-volume
augmentation of the parts of the kill chain that used to require a human hours** — recon, triage,
lure-writing, rule/patch analysis, exploit adaptation — plus **a brand-new class of targets: the AI
systems themselves, and the agents we are about to deploy.** Both halves are in scope below.

---

## 0. Evidence integrity

- `web_search` was captcha-blocked this sprint. All claims come from **direct `web_fetch`** of arXiv
  abstract pages, GitHub repos, SPEC pages and vendor portals. Full URL list in §9.
- Numbers are **quoted from the source's own abstract/card** and are marked with the source. Where a
  number is a *synthetic* or *sandboxed* measurement, it says so. No number here is an independent
  replication by this project — **nothing in this file is a measurement by us.**
- **These are capability upper bounds for capable models, not for our 4B model.** v1's own capability
  box (see `CAPABILITY-v1.md`) is the relevant comparison: our model fabricated IDs and leaked harmful
  content. It is not near frontier offensive capability. The frontier numbers matter because they are
  the threat we are defending against, not because they describe us.

---

## 1. Tier map: what actually became more dangerous

Legend: **[A]** autonomous/agentic; **[P]** human-driven with model assistance (the *dominant* real
class); **[S]** new AI-system target class.

| Tier | Attack class | What changed vs. 2023 | Measured evidence (source's own number) |
|---|---|---|---|
| [A] | **Autonomous web-app exploitation** | Real CVEs (not CTF abstractions) are now reachable end-to-end | CVE-Bench: best agent resolves **up to 13 %** of critical-severity CVEs; real-world sandbox, evaluation of unpredictable exploits ([2503.17332](https://arxiv.org/abs/2503.17332)) |
| [A] | **Autonomous vulnerability reproduction at scale** | Agents given a text description + codebase can write a PoC | CyberGym: **1,507 real vulns / 188 projects**; top combos **~20 %** success; **34 zero-days and 18 incomplete historical patches discovered** ([2506.02548](https://arxiv.org/abs/2506.02548)) |
| [A] | **IP-to-shell on real hosts** | Planning + exploit retrieval + command feedback loop, no human | RapidPen: shell on an HTB target in **200–400 s**, **~$0.3–$0.6 per run**, **60 % success** with success-case reuse ([2502.16730](https://arxiv.org/abs/2502.16730)) |
| [A] | **Synthetic-vuln exploitation** (upper bound, *synthetic*) | Near-total success on purpose-built targets | HonestCyberEval: Nginx + synthetic vulns; **o1-preview 92.85 %** highest, o3-mini and Claude-3.7-sonnet cost-effective but lower ([2410.21939](https://arxiv.org/abs/2410.21939)) |
| [A] | **Fuzz-target generation as a discovery engine** | LLMs write the harness, existing fuzzers do the work | oss-fuzz-gen: **30 reported bugs**, 160 projects with non-zero coverage gain, **max +29 % line coverage**, 1300+ benchmarks / 297 projects ([google/oss-fuzz-gen](https://github.com/google/oss-fuzz-gen)) |
| [P] | **Phishing / vishing / pretext at scale** | Fluency, per-target personalisation, multi-language, cost collapse | Documented **directly-harmful v1 outputs include a ready spear-phish pretext recipe** (`CAPABILITY-v1`) — a 4B model already does this |
| [P] | **Malware strain variation / obfuscation / custom tooling** | XOR-0x41 .exe-infector mechanics and backdoor specs were emitted by v1 | v1 harmful output audit (`CAPABILITY-v1`, probes 0,1,4,6,18) |
| [P] | **Rule/patch literacy** | Reading a diff, locating the vulnerable function, adapting an exploit | The inverse of CyberGym/PrimeVul capability; no direct defensive measurement exists here |
| [S] | **Prompt injection, direct and indirect** | Now the #1 LLM risk and a *persistence* mechanism in logs/documents | OWASP **LLM01:2025 Prompt Injection** ([link](https://genai.owasp.org/llm-top-10/)); LogInject passive injection **up to 88.2 % ASR**, **8.4 % residual** after layered defences ([2607.14493](https://arxiv.org/abs/2607.14493)) |
| [S] | **Agent/tool compromise** (confused deputy, tool poisoning, rug pull, token passthrough) | Protocol-level, ships in MCP today | MCP security best practices: confused deputy, token passthrough, SSRF incl. `169.254.169.254`, session hijack, local server compromise ([spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices)); tool poisoning/rug pull/shadowing ([Invariant Labs](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)) |
| [S] | **Memory / RAG poisoning and backdoors** | Agent memory is an attack surface across turns | ASB: 27 attack/defence methods, memory poisoning + Plan-of-Thought backdoor, **max average ASR 84.30 %**, weak defences ([2410.02644](https://arxiv.org/abs/2410.02644)) |
| [S] | **Deceptive narratives against analyst models** | Malware triage flipped by coherent false context | ALIBI: **30/35** baseline-malicious samples flipped benign on Gemini 2.5 Pro; defence still left **42.9 %** benign ([2609.19722](https://arxiv.org/abs/2609.19722)) |
| [S] | **Model/supply-chain and data poisoning** | Weights, adapters, datasets, MCP servers are all supply chain | OWASP **LLM03:2025 Supply Chain**, **LLM04:2025 Data and Model Poisoning** ([link](https://genai.owasp.org/llm-top-10/)) |
| [S] | **Excessive agency / unbounded consumption** | An agent with tools can be *used* against its owner | OWASP **LLM06:2025 Excessive Agency**, **LLM10:2025 Unbounded Consumption** ([link](https://genai.owasp.org/llm-top-10/)) |
| [S] | **AI-expanded 0-click surface** (a painful irony) | AI features decode attacker data *before* the user opens anything | Project Zero: audio transcription in Google Messages put decoders into the **0-click attack surface of most Android phones**; Dolby UDC CVE-2025-54957, sandbox escape CVE-2025-36934, Pixel 10 chain ([Project Zero, 2026-05-13](https://googleprojectzero.blogspot.com/)) |
| [P] | **Cyber-physical / OT-style effects** | Model-assisted recon + protocol reasoning lowers the bar | No measurement found this sprint — **[U]** |

**Reading the tiers.** [P] is where almost all real damage happens today and where even a 4B model is
useful to an attacker. [A] is improving fast on *narrow, verifiable* subtasks. [S] is where the
*defender's own tools* become targets — and it is the tier this project is about to enter with
`defense-architecture.md`.

---

## 2. The AI-assistance multiplier, stated precisely

Frontier assistance does not remove any step of the kill chain. It changes the **cost function**:

| Kill-chain step | Pre-AI cost | With frontier assistance | Evidence |
|---|---|---|---|
| Target/asset discovery | hours of manual recon | minutes; parallel agents | RapidPen automates scan→exploit from one IP ([2502.16730](https://arxiv.org/abs/2502.16730)) |
| Vulnerability identification | expert-days per app | agent-hours; ~13–20 % success on *real* targets | [2503.17332](https://arxiv.org/abs/2503.17332), [2506.02548](https://arxiv.org/abs/2506.02548) |
| PoC / exploit construction | days; scarce talent | ~20 % reproduction success, 34 zero-days found | [2506.02548](https://arxiv.org/abs/2506.02548) |
| Harness / fuzz-target writing | specialist work | LLM-generated targets reach code human targets never did | [oss-fuzz-gen](https://github.com/google/oss-fuzz-gen) |
| Lure / pretext writing | hours, native fluency bottleneck | seconds; already reproducible in a 4B model | `CAPABILITY-v1` |
| Malware variation | skilled development | prompt-driven mutation; v1 emitted infector mechanics | `CAPABILITY-v1` |
| **Detection evasion** | requires reading defender code | model summarises and adversarially adapts | implied by ASB/ALIBI results |

**Implication for CyberGuard's threat model:** the defender's *time budget* is the asset under attack.
Any defensive product whose value depends on a human reading everything loses. This is the argument
for the tiered architecture in `defense-architecture.md` and for the emphasis on **format compliance
and ID grounding** in `SPEC-V2.md` — output that cannot be parsed and trusted cannot be automated.

---

## 3. Vulnerability classes to train and evaluate against

Two orthogonal lists: (A) classes **AI makes more exploitable**, (B) classes **AI systems themselves
introduce**.

### 3A. Target classes where AI assistance moves the needle

Ordered by measured or strongly-implied evidence, not by severity-fashion.

1. **Web/application logic flaws and injections** — the only class with a *real-CVE* autonomous
   benchmark. CVE-Bench targets critical-severity CVEs in sandboxed replicas; up to 13 % solved
   ([2503.17332](https://arxiv.org/abs/2503.17332)). Sub-classes to instrument: SQLi/NoSQLi, template
   injection, SSRF, deserialisation, authz/IDOR, request smuggling, path traversal.
2. **Memory-safety bugs in C/C++** — OOB read/write, UAF, stack underflow, uninitialised memory. This
   is where LLM-generated fuzz targets produced 30 reported bugs and up to +29 % coverage
   ([oss-fuzz-gen](https://github.com/google/oss-fuzz-gen)), and where CyberGym's 1,507 real vulns
   live ([2506.02548](https://arxiv.org/abs/2506.02548)).
3. **Kernel / driver / sandbox-escape** — Project Zero's 2026 consumer-device work found three bugs in
   `/dev/bigwave` after "a couple hours of auditing", one giving arbitrary kernel read/write from the
   mediacodec sandbox ([Project Zero](https://googleprojectzero.blogspot.com/)). Auditing a driver is
   exactly the kind of bounded, high-context task where model assistance compresses expert-hours.
4. **Race conditions / TOCTOU** — hard for a human *and* hard for a fuzzer. Project Zero's 2026-09-08
   post is explicitly about testing races with memory-access tracing and stack-based delay injection
   ([Project Zero](https://googleprojectzero.blogspot.com/)); the AFL++-style "AI proposes delay
   points" framing is the tractable version.
5. **Media/codec/parser bugs reachable with no user interaction** — the 0-click chain is the canonical
   example, and the *reason* is AI: audio is transcribed before the user opens the message
   ([Project Zero](https://googleprojectzero.blogspot.com/)).
6. **Privilege-escalation on modern OS defences** — Windows Administrator Protection drew **9 bypasses**
   during insider preview, all fixed; UAC/UI-Access issues were long under-appreciated (Project Zero,
   2026-01/02). Defences that are *new* are also *unaudited*.
7. **Authentication/identity and OAuth flows** — the MCP confused-deputy attack is an OAuth flow bug
   (static client ID + dynamic registration + consent cookie → code theft to an attacker redirect URI)
   ([spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices)).
   Cryptographic/protocol reasoning is a natural LLM strength because it is text-shaped.
8. **Deterministic regex/DoS and resource exhaustion** — an "undisclosed regexp DoS" appears among
   oss-fuzz-gen's reported bugs; LLM-generated patterns are a plausible amplifier of a class humans
   keep shipping ([oss-fuzz-gen](https://github.com/google/oss-fuzz-gen)).
9. **Supply-chain and CI/CD** — this is where model assistance meets a documented real-world trend:
   Google's Threat Intelligence feed carries *"Proactive Defense: Hardening Code Pipelines and CI/CD
   Infrastructure"* and *"Batten Down Your Packages: Mitigation Guidance for Supply Chain Compromise"*
   ([GTIG index](https://cloud.google.com/blog/topics/threat-intelligence/)), and Google is publishing
   work on adversarial-AI evolution *"From Prompting to Autonomy"* (same index).
10. **AI-expanded consumer surface** — every "AI feature" that ingests attacker data before user
    interaction adds a decoder/parser to the 0-click surface. This class grows *as AI is adopted*.

### 3B. AI-system classes (the new targets — our own future attack surface)

Mapped onto OWASP's LLM Top 10:2025 and MITRE ATLAS so labels attach to a maintained taxonomy.

| ID | Class | Why it is a *vulnerability class* and not a single bug |
|---|---|---|
| LLM01 | **Prompt injection** (direct + indirect + persistent) | Untrusted data and trusted instructions compete for the same attention channel; no clean privilege boundary exists inside the context window. LogInject proves *passive* injection persists in log fields and fires when an analyst queries the model ([2607.14493](https://arxiv.org/abs/2607.14493)). |
| LLM02 | **Sensitive information disclosure** | Output channel exfiltrates system prompts, tool outputs, memory. |
| LLM03 | **Supply chain** | Model weights, adapters, datasets, tokenizers, MCP servers, plugins — all interchangeable components with no default provenance check. |
| LLM04 | **Data and model poisoning** | Fine-tuning on a poisoned slice, or a poisoned adapter, is cheap (see `top-models.md` §3 on how cheap safety removal is). |
| LLM05 | **Improper output handling** | Model text fed to a shell/SQL/browser without validation. In this project this is *literal*: a model that emits a command and a harness that runs it. |
| LLM06 | **Excessive agency** | Tools + memory + autonomy = the model's mistakes become actions. |
| LLM07 | **System prompt leakage** | Relevant because a leaked system prompt tells an attacker exactly which refusals to attack. |
| LLM08 | **Vector and embedding weaknesses** | RAG corpora are attacker-influenceable and are usually *trusted more* than user input. |
| LLM09 | **Misinformation** | The measured v1 failure: 21 % ATT&CK-ID and 18 % CVE fabrication with an adjacent-ID signature (`CAPABILITY-v1`). In a defensive product this is a **safety-critical** bug, not a quality bug. |
| LLM10 | **Unbounded consumption** | Cost/DoS; also the *defender's* resource envelope in `defense-architecture.md`. |
| — | **Agentic-specific** (ATLAS/ASB) | Confused deputy, tool poisoning, rug pull, tool shadowing, token passthrough, SSRF via metadata URLs, session hijack, memory poisoning, Plan-of-Thought backdoor. Sources: [MCP security](https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices), [Invariant Labs](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks), [ASB](https://arxiv.org/abs/2410.02644). |

**One-line synthesis:** class 3A is what AI *does to* systems; class 3B is what AI *adds to* the
system. A defensive model must be trained and gated on both, and the project's current corpus covers
neither deliberately.

---

## 4. Methodology: how to discover NEW vulnerabilities

This is the part that is actually reusable. It is written to be run by this project, on assets we own,
with receipts — matching the `SPEC-V2.md` receipt discipline.

### 4.1 Principles

1. **Novelty is not the deliverable; *verified* novelty is.** Every source is full of plausible
   findings. CyberGym's own protocol is the model: generate, then confirm the PoC reproduces on the
   real codebase — and it found 18 *incomplete historical patches*, i.e. the most valuable output is
   often "the fix was wrong". ([2506.02548](https://arxiv.org/abs/2506.02548))
2. **Ground every candidate in an executable oracle.** A crash, a failing assertion, a coverage delta,
   a differential between patched/unpatched — never "the model says so". oss-fuzz-gen's four metrics
   (compilability, crashes, coverage, coverage-diff vs human targets) are a good template
   ([oss-fuzz-gen](https://github.com/google/oss-fuzz-gen)).
3. **Keep the model out of the trust path.** Per LogInject and ALIBI, the discovery pipeline must
   separate *verified facts* from *attacker/`model-controlled claims* and must not allow a narrative to
   flip a verdict ([2607.14493](https://arxiv.org/abs/2607.14493), [2609.19722](https://arxiv.org/abs/2609.19722)).
4. **Report even when nothing is found.** A null result with the instrument stated is evidence; the
   v1 12-probe-passed-while-60-probe-failed episode is our cautionary tale (`VERDICT-v1.md`/`CAPABILITY-v1.md`).
5. **Responsible disclosure first.** New findings go to the maintainer/vendor through their channel
   before any public write-up. Budget the disclosure time in the plan; it is not optional overhead.

### 4.2 Stage 0 — instrumentation and ground truth (before any model call)

- **Assets:** our own endpoints, our own services, our own MCP server (per `defense-architecture.md`),
  plus open-source projects with public disclosure channels.
- **Telemetry:** eBPF-LSM/Falco/Tetragon (enforcement + tracing), fanotify permission events
  (blocking), auditd, Sysmon/ETW on Windows, EndpointSecurity/FSEvents on macOS, osquery for
  inventory. Sources and capabilities in `defense-architecture.md` §3.
- **Provenance substrate:** DARPA Transparent Computing provenance graphs
  ([repo](https://github.com/darpa-i2o/Transparent-Computing)) or equivalent — this is what lets a
  finding be traced to a causal chain rather than a log line.
- **Reproducibility corpus:** ARVO's Docker-per-bug instances ([repo](https://github.com/eth-sri/arvo))
  let a candidate be re-run deterministically.

### 4.3 Stage 1 — candidate generation (six complementary engines)

Run all six; they fail differently.

| Engine | Method | Strength | Failure mode to control |
|---|---|---|---|
| E1 **Coverage-guided fuzzing** | AFL++/libFuzzer on existing harnesses | cheap, real crashes | plateaus on parsers with checksums/grammars |
| E2 **LLM fuzz-target generation** | model writes the *harness* into an existing fuzzer (the oss-fuzz-gen pattern) | reaches code human targets never did; +29 % line coverage measured | invalid targets; compile failures — filter on build success first |
| E3 **Grammar-/knowledge-driven fuzzing** | structure-preserving mutation; Project Zero's "knowledge-driven fuzzing" found a macOS type confusion + double-free | finds deep parser bugs; 2026 work documents its flaws *and* counters | subtle corpus/config traps; the PZ post is required reading before running it |
| E4 **Static/LLM code reasoning** | LLM reads a diff/function, proposes a concrete failing input; verified by E1/E2 | finds *logic* bugs fuzzing misses | hallucinated feasibility; **every claim must become an executable input** |
| E5 **Race/TOCTOU directed search** | stack-based delay injection + memory-access tracing to hit interleavings | reaches a class fuzzers cannot | timing flakiness — require N-of-M reproductions |
| E6 **Differential/repair auditing** | compare patched vs unpatched; ask "is the fix complete?" | found **18 incomplete patches** in CyberGym | needs both binaries built reproducibly |

**For *our own* AI/MCP stack specifically**, add two engines:
- **E7 Adversarial-agent red teaming** — AgentDojo/InjecAgent-style attacks against our MCP server,
  plus ASB's 27 methods, measured with attack-success-rate *and* utility (ASB's balance metric)
  ([2410.02644](https://arxiv.org/abs/2410.02644)).
- **E8 Automated red-team synthesis** — AutoRedTeamer: strategy-proposer agent reads new research and
  implements new attacks, +20 % ASR on HarmBench vs Llama-3.1-70B at 46 % lower cost
  ([2503.15754](https://arxiv.org/abs/2503.15754)). Use it to keep the battery current, not as the
  final judge.

### 4.4 Stage 2 — verification pipeline (fail-closed)

1. **Determinism gate:** the candidate reproduces ≥3/3 in a clean environment (ARVO container / clean
   VM). Races: ≥N/M with the delay-injection harness.
2. **Isolation gate:** reproduced only in a sandbox with no production credentials, no network beyond
   the target, and a logged egress allowlist.
3. **Novelty gate:** dedupe against the project's own CVE/ATT&CK corpora *and* public databases
   (`cvelistV5` [link](https://github.com/CVEProject/cvelistV5), OSV [link](https://osv.dev/),
   GitHub advisories). Adjacent-ID extrapolation is exactly the v1 fabrication signature — treat a
   "new ID" claim as *fabrication until a database returns it*.
4. **Impact gate:** classify against CWE/ATT&CK-ATLAS, state preconditions and required privilege
   honestly. "Model says critical" is not a classification.
5. **Independent-reader gate:** a *different model family* reads the raw artefact, not the summary —
   our v1 rubric review found 16/60 rationale/index mismatches and forced withdrawal of item-level
   claims (`CAPABILITY-v1`). Design the pipeline to survive that discovery.

### 4.5 Stage 3 — disposition and receipts

- **Disclose** through the project's/vendor's channel; record the date, channel, and reply.
- **Receipt** every run in the style of this repo: instrument, revision, seeds, raw outputs,
  disposition, and what was *not* measured. A finding without a receipt does not exist here.
- **Feed back**: confirmed true positives and *disproved* candidates both become eval items. The
  disproved ones are the anti-hallucination training data the project lacks.

### 4.6 Discovery-program metrics (proposed gates)

| Metric | Definition | Why |
|---|---|---|
| Reproducibility rate | fraction of reported candidates that pass the 3/3 gate | measures the pipeline, not the model's prose |
| False-positive rate per 1k candidates | candidates rejected at normalisation/novelty gate | v1's 65 % IOC fabrication says our FPR is the real problem |
| Blind-spot coverage | distinct CWE/ATLAS classes touched | prevents a pipeline that only finds one bug type |
| Time-to-first-verified-finding | wall clock | the actual value proposition vs. a human |
| Incomplete-patch share | fraction of findings that are bad fixes | historically the highest-value output |
| Cost per verified finding | GPU $ + human hours | decides whether the local service is worth running |

### 4.7 Honest limits of this methodology

- **We cannot discover what our instruments cannot observe.** Kernel memory corruption found by an
  LLM reading source still needs an executor to confirm.
- **Discovery capability is dual-use.** The same engines find offensive advantage. Containment
  (E1): own assets only, no exploit development beyond PoC-for-disclosure, and a written
  authorisation per target.
- **The strongest evidence this sprint is about *narrow* tasks.** Anything claiming general autonomy
  is contradicted by the 13–20 % real-world success rates.

---

## 5. What to train and gate on (ties this file to `SPEC-V2.md` and `top-models.md`)

| Need | From this file | Where it lands |
|---|---|---|
| ID/number grounding gates (CVE, ATT&CK, ATLAS) | §3B LLM09, §4.4.3 | `id_validator.py`, `SPEC-V2.md` U6 — extend to **ATLAS** IDs, not just ATT&CK |
| Injection battery | §3B LLM01, §1 [S] | new gate, using AgentDojo/InjecAgent/BIPIA/ASB as instruments |
| Refusal set that covers agentic harm, not just "make a bomb" | §1 [A]/[P] | the U5 powered battery; AgentHarm as an external check |
| Format compliance under adversarial input | §3A + `CAPABILITY-v1` format failures | Sigma/Splunk corpora, `datasets.md` §3 |
| Agentic-harm refusal after tool calls | ASB, AgentHarm | a "refuses *after* a tool result" sub-gate — absence of this is how MCP services get hijacked |
| Anti-deception in triage | ALIBI ([2609.19722](https://arxiv.org/abs/2609.19722)) | provenance-separated inputs + an eval that tries to flip verdicts with coherent false narratives |

**ATLAS as the missing taxonomy:** the project currently grounds IDs against NVD + ATT&CK. MITRE
ATLAS distributes a maintained adversarial-ML / LLM TTP taxonomy in YAML with **format 6.0.0, content
2026.05**, with STIX export and typed IDs (`AML.T####`, `AML.M####`) ([atlas-data](https://github.com/mitre-atlas/atlas-data)).
Since the deployment target is an AI/MCP system, **ATLAS should be a first-class label source.

---

## 6. The project-specific conclusion

v1 was measured as **not deployable** because it lost refusal and fabricated identifiers. The threat
picture above says the *defender* is now on the clock: attack-side recon/triage/lure steps are cheap,
and the defender's own AI tools are injectable. So:

1. **Refusal and grounding are table stakes**, not polish — `SPEC-V2.md` F1/F5 are correct priorities.
2. **The new high-value gap is injection defence** for the always-on service, which needs the
   instruments in `datasets.md` §5/§6 before the service exists.
3. **Discovery is a product feature**, not research overhead: a pipeline whose metrics are
   reproducibility and false-positive rate (§4.6) is both a defensive asset and the honest way to
   earn any "finds new vulnerabilities" claim.
4. **Never let the model's narrative be the evidence.** That single rule, applied consistently,
   is worth more than any single model improvement — and it is precisely the failure mode that
   LogInject (88.2 % → 8.4 % residual) and ALIBI (42.9 % still flipped) measure.

---

## 7. Open questions / to measure

- **Our own frontier gap:** no one has measured what a *4B local* model adds to defensive triage vs a
  rules engine. The honest comparison is analyst-time and missed-detections; no source this sprint
  did that comparison ([U]).
- **Serialisation ablation:** no paper found that isolates event-to-text encoding for endpoint events
  ([U]).
- **Injection residual on our pipeline:** LogInject's 8.4 % residual is on *their* pipeline with
  layered defences; ours is unmeasured.
- **ATLAS coverage of our own stack:** we have not enumerated which AML techniques apply to the
  MCP service we intend to run.
- **Disclosure logistics:** no vendor-channel inventory yet for the assets we would test.

---

## 8. URL index (every citation in this file)

AI-offensive-capability benchmarks:
- CVE-Bench — https://arxiv.org/abs/2503.17332
- CyberGym — https://arxiv.org/abs/2506.02548
- RapidPen — https://arxiv.org/abs/2502.16730
- HonestCyberEval — https://arxiv.org/abs/2410.21939
- oss-fuzz-gen — https://github.com/google/oss-fuzz-gen
- Agent Security Bench — https://arxiv.org/abs/2410.02644
- AutoRedTeamer — https://arxiv.org/abs/2503.15754
- DataSentinel (injection detection, IEEE S&P 2025 distinguished paper) — https://arxiv.org/abs/2504.11358

AI-system security:
- MCP security best practices — https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices
- Invariant Labs tool poisoning — https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks
- OWASP LLM Top 10:2025 — https://genai.owasp.org/llm-top-10/
- OWASP Agentic AI threats & mitigations — https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/
- MITRE ATLAS data (content 2026.05 / format 6.0.0) — https://github.com/mitre-atlas/atlas-data
- LogInject — https://arxiv.org/abs/2607.14493
- ALIBI — https://arxiv.org/abs/2609.19722
- Microsoft Defender AI agent runtime protection — https://learn.microsoft.com/en-us/defender-endpoint/ai-agent-runtime-protection-overview
- NIST AI RMF / AI Resource Center — https://airc.nist.gov/

Discovery substrate / corpora:
- ARVO — https://github.com/eth-sri/arvo
- DARPA Transparent Computing — https://github.com/darpa-i2o/Transparent-Computing
- CVE Program cvelistV5 — https://github.com/CVEProject/cvelistV5
- OSV — https://osv.dev/
- Project Zero blog (2026 device/exploitation research) — https://googleprojectzero.blogspot.com/
- Google Threat Intelligence index — https://cloud.google.com/blog/topics/threat-intelligence/

Project-internal (evidence for the readings above):
- `docs/CAPABILITY-v1.md`, `docs/VERDICT-v1.md`, `docs/SPEC-V2.md`

*Marked **[U]** in this file:* OT/cyber-physical measurements; any claim that a *local 4B* model
materially improves defensive triage without a measured head-to-head.
