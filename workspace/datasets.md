# datasets.md — datasets we need BEYOND the current corpus

**Sprint:** CYBERGUARD research sprint, 2026. **Deliverable 1 of 4.**
**Read first:** `ARTIFACT-MAP.md`, `docs/SPEC-V2.md`, `docs/DATASET-V2.md`, `docs/CAPABILITY-v1.md`.
**Question this file answers:** the existing 195 MB Trendyol SFT core plus the DATASET-V2 candidate list
leave *capability* gaps that no amount of re-weighting can close. Which datasets close them?

---

## 0. Evidence integrity (read before trusting a URL)

- `web_search` was **non-functional for this sprint** (DuckDuckGo/Mojeek returned captcha challenge
  pages; Bing returned generic noise). Everything below came from **direct `web_fetch`** of primary
  sources, the **GitHub REST API**, and the **HuggingFace `/api/datasets`** endpoint.
- Therefore this is a **verified sample, not an exhaustive survey**. Marked per row:
  - **[V]** = URL fetched successfully this sprint; license/size read from the actual card, LICENSE
    file, repo record, or portal page.
  - **[C]** = canonical, long-lived primary URL (well-known project home) **not fetched this sprint** —
    real, but verify license/size before ingesting.
  - **[U]** = **UNVERIFIED** — do not ingest on this row alone.
- Licenses drift. Public repos change LICENSE files mid-life. **Pin a commit/revision for every source
  before any token is spent** — this is exactly the U1 admission gate already specified in
  `SPEC-V2.md` §5, and this file feeds it candidates, not admissions.

## 1. What already exists — do NOT re-recommend

From `docs/DATASET-V2.md` and the v2 mixture: Trendyol (SFT core), Primus-FineWeb / Primus-Seed /
Primus-Instruct, NIST CSRC `ethanolivertroy/nist-cybersecurity-training` (CC0), NVD CVE JSON (public
domain), MITRE ATT&CK STIX (ToU + copy notice), FineWeb-Edu v1.4.0, Dolci-Instruct-SFT,
`reloading0101/threat-intelligence-dataset`, `ronaldocloud/cyberusecase-v1.0`, Fenrir v2.1 (measured
first), `HuggingFaceH4/ultrachat_200k` (chat replay). Eval-only and never-train: SecQA, CTI-Bench,
SecEval, SecBench, Primus-Reasoning. Rejected: `oi-uae/cyber-security` (NC), Wikipedia SA slices,
SlimPajama-as-default, PolySec (phantom).

**The gaps that remain, and that this file fills:**

| # | Gap | Why it matters (measured cause) | Filled by section |
|---|---|---|---|
| G1 | **Real messy CTI text** with IOCs | v1 fabricated an IOC in 65 % of reports on a *synthetic easy floor* (`CAPABILITY-v1`) | §2 |
| G2 | **Format-compliant structured output** | 61 % no verdict; Sigma schema-complete 0 %; YAML valid 6.7 % | §3 |
| G3 | **Security code understanding** | never measured at all — and it is the substrate of all exploitation | §4 |
| G4 | **Injection / jailbreak defence data** | v1 refusal collapsed to 6/60; no injection instrument exists | §5 |
| G5 | **Agentic / MCP security** | the deployment target for `defense-architecture.md` is MCP; zero corpus coverage | §6 |
| G6 | **Real endpoint telemetry & malware behaviour** | required for the always-on local service to be testable at all | §7 |
| G7 | **2025–2026 releases** | the model's knowledge and our defences both age | §8 |

---

## 2. G1 — IOC / threat-intel extraction from real, messy text

The single highest-ROI addition. v1's extraction numbers are meaningless because the input documents
were authored easy-mode. These are real.

| Name | URL | License | Size | Format | Covers | Verdict |
|---|---|---|---|---|---|---|
| APT/CTI Reports | https://huggingface.co/datasets/hackerman700000/apt-cti-reports | **MIT** [V] | 1k–10k PDFs [V] | PDF (raw text after extraction) | Real APT writeups by group (APT1/10/12/15/17/19/21/23/27/28); IOCs, TTPs, attribution | **ADMIT candidate.** Heterogeneous vendor styles, real noise — exactly the hard mode missing. Needs PDF→text + OCR pass, then IOC annotation. |
| CTI-Rationale | https://huggingface.co/datasets/EbruResul/CTI-Rationale | **CC-BY-4.0** [V] | 10k–100k rows [V] | JSONL/CSV, gated `auto` [V] | CTI→ATT&CK mapping **with evidence spans + rationale**; includes 2025 advisories (ar25-261a) [V] | **ADMIT candidate.** Rare: teaches *justified* mapping, not just labels. Gated — accept terms first. |
| abuse.ch URLhaus | https://urlhaus.abuse.ch/api/ | Free auth-key, fair-use; commercial API paid [V] | active + 90-day URL dumps, regenerate every 5 min [V] | CSV/JSON, RPZ, hostfile, Snort/Suricata, ClamAV, MISP events [V] | Malware distribution URLs, payload hashes, C2 | **ADMIT as labels/feed.** Gives IOC ground truth and a live blocklist for the local service. |
| abuse.ch MalwareBazaar | https://bazaar.abuse.ch/ | Free auth-key, fair-use [V] | millions of samples [V] | sample files + JSON/CSV metadata | Malware binaries, family tags, YARA matches | **ADMIT (metadata first; samples in lab only).** |
| abuse.ch ThreatFox | https://threatfox.abuse.ch/ | Free auth-key, fair-use [V] | ~1M+ IOCs, daily exports | JSON/CSV + MISP | IOCs w/ malware family + confidence | **ADMIT as labels.** |
| abuse.ch SSLBL | https://sslbl.abuse.ch/ | Free, fair-use [V] | cert/JA3 blocklists | CSV | Malicious TLS certs, JA3/JA3s | ADMIT as labels (network-IOC extraction). |
| abuse.ch YARAify | https://yaraify.abuse.ch/ | Free, fair-use [V] | large rule repo + scan API | YARA | Malware identification + **rule-authoring corpus** | ADMIT — cross-links §3. |
| abuse.ch Feodo Tracker | https://feodotracker.abuse.ch/ | Free, fair-use [V] | **empty since Operation Endgame** [V] | blocklist CSV/JSON | botnet C2 (historical) | Historical corpus only — **do not build a live feed on it.** |
| DNRTI | https://github.com/SCreaMxp/DNRTI-A-Large-scale-Dataset-for-Named-Entity-Recognition-in-Threat-Intelligence | **No license file** [V] | ~4.7k sentences, 13 entity classes | text + BIO tags | CTI NER / IOC entity extraction | **REVIEW-REQUIRED** — no license; legal sign-off or reject. |
| APTNER | https://github.com/wangxuren/APTNER | **No license** [V] | ~1.2k sentences, 6 entity types | text + seq labels | CTI NER | REVIEW-REQUIRED (no license). |
| CyNER | https://github.com/aiforsec/CyNER | [C] | few MB | JSON/CSV + code | cybersecurity entity recognition | [C] verify license. |
| MalwareTextDB | https://github.com/stuartbreckenridge/MalwareTextDB | ELRA/LREC terms — likely NC [C] | ~6.7k annotated sentences | JSON/XML | malware-article attribute/anaphora extraction | [C] likely eval-only; ELRA gating. |
| AlienVault OTX | https://otx.alienvault.com/ | free account, ToU [C] | millions of pulses | JSON API | IOC pulses + campaign context | [C] check redistribution terms. |
| MISP | https://github.com/MISP/MISP | **AGPL-3.0** [C] | feeds vary | MISP JSON / STIX 2.1 | IOC sharing, taxonomies | [C] platform; export rights vary per feed. |
| OpenCTI | https://github.com/OpenCTI-Platform/opencti | Apache-2.0 (core) [C] | varies | STIX 2.1 | real STIX bundles + relationships | [C] best STIX source if you populate it. |
| Malpedia | https://malpedia.caad.fkie.fraunhofer.de/ | free account, ToU [C] | ~3k+ families | YARA + JSON/API | family fingerprints, actor links | [C] registration required. |
| The DFIR Report | https://thedfirreport.com/ | site content © author, no dataset license [C] | ~100+ full intrusion walkthroughs | HTML | end-to-end ransomware/initial-access narratives | [C] **cite, don't republish** — rights unclear. |

**Practical note:** the two **ADMIT candidates** (apt-cti-reports, CTI-Rationale) plus abuse.ch feeds
give real text *and* real labels. Do not confuse a feed (a list) with a corpus (prose to extract from):
the extraction gap is only closed by the first two.

---

## 3. G2 — Format compliance / structured output

v1 could not hold a one-word verdict and produced **0 % schema-complete Sigma**. These are the
authoritative schemas and rule corpora — the ground truth for constrained generation.

| Name | URL | License | Size | Format | Covers | Verdict |
|---|---|---|---|---|---|---|
| SigmaHQ rules | https://github.com/SigmaHQ/sigma | **Detection Rule License 1.1** [V] | **>3,000 rules**, ~49 MB repo [V] | YAML (Sigma) | SIEM log detections, all ATT&CK tactics | **ADMIT candidate** — but DRL-1.1 is **not** OSI; read it before redistributing in a published adapter. |
| Sigma specification | https://github.com/SigmaHQ/sigma-specification | **public domain** [V] | small | spec text | schema ground truth for rule format | **ADMIT** (clean). |
| pySigma / sigma-cli | https://github.com/SigmaHQ/pySigma · https://github.com/SigmaHQ/sigma-cli | Apache-2.0/DRL family [C] | code | Python | rule→query translation pairs | [C] verify; excellent for "parse-checked output" reward. |
| Splunk Security Content | https://github.com/splunk/security_content | **Apache-2.0** [V] | ~319 MB repo, 1.7k stars, branch `develop` [V] | YAML (SPL detections, stories, macros) | SPL detection authoring | **ADMIT — cleanest license in this category.** Best second format after Sigma. |
| Elastic detection-rules | https://github.com/elastic/detection-rules | **NOASSERTION** ("Other") [V] | ~525 MB repo, 2.7k stars, pushed 2026-09 [V] | TOML + Python + EQL/KQL/ES\|QL | detection engineering, multi-query formats | REVIEW-REQUIRED — read `LICENSE.txt`; not OSI. Huge and current. |
| Neo23x0 signature-base | https://github.com/Neo23x0/signature-base | **DRL 1.1** (since 2021-08-13); **pre-v2.0 was CC-BY-NC** [V] | ~43 MB repo [V] | YARA + CSV IOC | malware signatures, IOCs | **ADMIT only post-2021 releases** — old tags are non-commercial. |
| Yara-Rules/rules | https://github.com/Yara-Rules/rules | per-file mix [C] | thousands of rules | YARA | rule authoring | [C] per-file licenses vary. |
| Emerging Threats Open | https://rules.emergingthreats.net/open/ | ET Open terms (free, attribution) [C] | ~50k rules | Suricata/Snort | NIDS signature generation | [C] ET **Pro** is paid — don't bundle. |
| Snort community rules | https://www.snort.org/downloads/community/ | Snort community license [C] | thousands | Snort rules | NIDS rule authoring | [C] registration historically required. |
| OSV | https://osv.dev/ · API https://api.osv.dev/v1/query | **CC-BY-4.0 data / OpenSSF schema** [V] | npm 228,744; PyPI 25,166; Go 9,203; OSS-Fuzz 4,013; Git 108,119; Chainguard 1,023,665 [V] | JSON (OSV schema) | dependency/package vulnerabilities with version ranges | **ADMIT** — ideal structured-JSON compliance data; queryable by commit hash. |
| CVE Program `cvelistV5` | https://github.com/CVEProject/cvelistV5 | CVE ToU (public, attribution) [C] | ~300k+ records | **CVE JSON 5.0** | authoritative CVE record authoring/parsing | [C] **complements, not duplicates,** the existing NVD JSON — it is the schema of record. |
| CISA KEV | https://www.cisa.gov/known-exploited-vulnerabilities-catalog | US Gov public domain [C] | ~1k+ exploited CVEs | JSON/CSV | "exploited in the wild" labels | [C] small, high-signal for risk reasoning. |
| CycloneDX / VEX | https://cyclonedx.org/ · https://github.com/CycloneDX/specification | Apache-2.0 [C] | spec + examples | JSON/XML | SBOM/VEX structured output | [C]. |
| MITRE CWE | https://cwe.mitre.org/data/downloads.html | CWE ToU, free [C] | ~900+ weaknesses | CSV/XML | weakness taxonomy/classification | [C] — and see `vulnerabilities.md` §3 for why CWE labels are weak supervision. |
| MITRE D3FEND | https://d3fend.mitre.org/ | Apache-2.0 (repo) [C] | ~150+ defensive techniques | OWL/JSON, STIX export | countermeasure mapping | [C] strong complement to ATT&CK for a *defensive* model. |

**Why this section and not just "make the model output YAML":** constrained generation is cheap at
inference, but a model that has never seen a schema-complete artefact cannot rank valid completions
above invalid ones. SigmaHQ + Splunk give tens of thousands of schema-valid, human-written examples
across two formats.

---

## 4. G3 — Security code: vulnerable/secure code corpora

**This gap is invisible in the current plan and it is the substrate of every offensive technique in
`vulnerabilities.md`.** A defensive model that cannot read a vulnerable function cannot triage a
patch, review a PR, or explain a CVE.

| Name | URL | License | Size | Format | Covers | Verdict |
|---|---|---|---|---|---|---|
| CVEfixes | https://github.com/secureIT-project/CVEfixes · paper https://arxiv.org/abs/2105.12531 | MIT code / CC-BY-4.0 data (verify) [C] | ~9.5k CVEs, ~18k+ fix commits | SQLite/CSV, code before+after | vulnerability-fix commit pairs + CWE labels | [C] best paired pre/post-fix corpus. |
| PrimeVul | https://arxiv.org/abs/2403.18624 | check card [C] | ~7k vulnerable + paired benign | JSONL | **de-biased** vuln detection; strict dedup/masking | [C] designed to fix BigVul/Devign label noise — good as a **hard eval**, not training. |
| DiverseVul | https://github.com/wagner-group/diversevul | [C] | ~330k functions | JSONL | multi-project vuln detection, broad CWE | [C] scale + diversity. |
| SecLLMHolmes | https://arxiv.org/abs/2312.12575 · https://github.com/ai4cloudops/SecLLMHolmes | check repo [C] | ~1.6k scenarios, 8 CWEs | JSON | reasoning-based vuln ID + adversarial variants | [C] best "explain *why* it is vulnerable" material. |
| BigVul | https://github.com/ZeoVan/MSR_20_Code_vulnerability_CSV_Dataset | academic [C] | ~185k functions, ~10k CVEs | CSV | function-level vuln detection | [C] **known label noise** — use with PrimeVul as a contaminant check. |
| Devign | https://github.com/epicosy/devign | [C] | ~27k functions (FFmpeg/QEMU) | JSON + graph | graph-based vuln detection | [C]. |
| Meta PurpleLlama / CyberSecEval | https://github.com/meta-llama/PurpleLlama | **NOASSERTION** [V] | ~44 MB repo, 4,407 stars, pushed 2026-08 [V] | Python harness + insecure-code / MITRE / prompt-injection data | insecure code generation, cyberattack helpfulness, injection eval | **EVAL-first**; license is "Other" — read before any training use. |
| OSS-Fuzz | https://github.com/google/oss-fuzz · harness https://github.com/google/oss-fuzz-gen | Apache-2.0 [C] / [V] | thousands of projects; crash corpus | C/C++/Rust + inputs | real fuzzing-found vulnerabilities | [C] OSS-Fuzz; **[V] oss-fuzz-gen** is the LLM-harness. |
| ARVO | https://github.com/eth-sri/arvo | check repo [C] | ~5k+ reproducible bugs | Docker per bug | **reproducible** vuln instances | [C] the gold standard for "can the model actually reproduce it." |
| Semgrep rules | https://github.com/semgrep/semgrep-rules | Semgrep Rules License (**restricts resale**) [C] | ~2k+ rules | YAML | SAST rule authoring, secure coding | [C] license restricts commercial redistribution. |
| CodeQL security queries | https://github.com/github/codeql | MIT [C] | hundreds of queries | QL | static-analysis query generation | [C]. |
| ExploitDB | https://gitlab.com/exploit-database/exploitdb | GPL-2.0 [C] | ~46k exploits | CSV + files | exploit PoC reference | [C] **dual-use** — policy-gate it; never train on it without a containment plan. |

---

## 5. G4 — Safety: prompt injection, jailbreak, dangerous-capability

The v1 collapse was a **refusal** failure; the always-on MCP service (deliverable 3) adds an
**injection** surface. Both need instruments and, separately, training data.

| Name | URL | License | Size | Format | Covers | Train or eval? |
|---|---|---|---|---|---|---|
| WMDP (`cais/wmdp`) | https://huggingface.co/datasets/cais/wmdp | **MIT** [V] | **wmdp-cyber 1,987**; bio 1,273; chem 408 (~5.9 MB) [V] | parquet MCQ [V] | hazardous-knowledge proxy (cyber/bio/chem) | **EVAL-ONLY.** MIT allows reuse but training on it destroys an unlearning benchmark. |
| JailbreakBench JBB-Behaviors | https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors | **MIT** [V] | 100 harmful + 100 benign + judge comparison [V] | CSV [V] | jailbreak robustness, harm compliance | **EVAL-ONLY** (de-facto standard). |
| AgentHarm | https://huggingface.co/datasets/ai-safety-institute/AgentHarm | **license: `other`** [V] | <1k behaviours (benign+harmful+chat) [V] | JSON [V] | **agentic** multi-step tool abuse; refusal after tool calls | **EVAL-ONLY**; custom license. Co-authored with Gray Swan + UK AISI. |
| HarmBench | https://github.com/centerforaisafety/HarmBench | MIT [C] | ~510 behaviours, ~18 attack methods | CSV/JSON | standardised red-teaming | EVAL-ONLY. |
| AdvBench | https://github.com/llm-attacks/llm-attacks | MIT [C] | ~520 behaviours | CSV | GCG-style jailbreak targets | EVAL-ONLY. |
| StrongREJECT | https://arxiv.org/abs/2402.10260 | check card [C] | ~313 prompts + rubric | JSON | **jailbreak quality scoring** | EVAL-ONLY — use the rubric, it fixes the "did it refuse?" binary that failed us. |
| BIPIA | https://github.com/microsoft/BIPIA · https://arxiv.org/abs/2312.14197 | MIT [C] | ~70k cases, 5 tasks | JSON | indirect injection via external content | EVAL-ONLY; directly relevant to the LogInject failure mode. |
| AgentDojo | https://github.com/ethz-spylab/agentdojo · https://arxiv.org/abs/2406.13352 | MIT [C] | ~97 tasks / ~629 security cases | Python + JSON | tool-using agent injection & exfiltration | EVAL-ONLY; **the** harness for the MCP service. |
| InjecAgent | https://github.com/uiuc-kang-lab/InjecAgent · https://arxiv.org/abs/2403.02691 | MIT [C] | ~1,054 cases | JSON | indirect injection against tool agents | EVAL-ONLY. |
| PINT benchmark | https://huggingface.co/datasets/lakeraai/pint-benchmark | check card [C] | ~3k (paper 2410.02814) | JSON | prompt-injection **detection** (binary) | One of few injection sets plausibly usable to **train a detector** — subject to license. |
| Aegis AI Content-Safety 2.0 | https://huggingface.co/datasets/nvidia/Aegis-AI-Content-Safety-Dataset-2.0 | **CC-BY-4.0** [V] | **33,416 interactions** (30,007/1,445/1,964) [V] | JSON [V] | content-safety classification, moderation taxonomy | **TRAIN-APPROPRIATE, clean license** — use for a guard/refusal head. |
| LLMail-Inject | Microsoft (2025) [C] | check repo [C] | unknown | JSON | email-borne indirect injection, adaptive | [U] locate + verify. |
| Gray Swan arena data | https://gray-swan.ai/ | competition terms [C] | competition-scale | mixed | jailbreaking, agent hijacking | [C] terms restrict reuse. |
| OWASP LLM Top 10 / Agentic Security | https://genai.owasp.org/llm-top-10/ · https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/ | CC-BY-SA 4.0 (docs) [V] | docs | markdown/PDF | risk taxonomy (LLM01–LLM10:2025) | **Framework, not data** — use it to structure labels, per §5.5 of `vulnerabilities.md`. |
| MITRE ATLAS data | https://github.com/mitre-atlas/atlas-data | repo license on GitHub; © MITRE, public release [V] | monthly content releases; **format 6.0.0 / content 2026.05** [V] | YAML → STIX, Navigator, Excel [V] | **adversarial-ML TTP taxonomy incl. LLM attacks** | Use as label ontology. Note: it is a *knowledge base*, not a text corpus. |

**Hard rule from the v1 evidence:** every row above except Aegis and (maybe) PINT is **eval-only**.
The v1 lesson is that a refusal battery is only useful if it is **not** also training data, and that
the *rubric* matters more than the prompt set (the 12-probe fixture passed while the 60-probe battery
failed).

---

## 6. G5 — Agentic / MCP security

This is the **newest and least-covered** gap, and it is where our own deployment lives. There is
almost no *training* data here; there are harnesses, specs, and scanners.

| Name | URL | License | Size | Format | Covers | Verdict |
|---|---|---|---|---|---|---|
| MCP specification | https://github.com/modelcontextprotocol/specification · security: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices | MIT [C]; page [V] | spec text | markdown | protocol surface; confused deputy, token passthrough, SSRF, session hijack, local server compromise, stdio proxy risk, scope minimisation [V] | **Primary threat model for deliverable 3.** |
| `rogue-security/mcp-tool-use-quality-benchmark` | https://huggingface.co/datasets/rogue-security/mcp-tool-use-quality-benchmark | not declared, `gated: auto` [V] | 1k–10k [V] | parquet [V] | tool-selection correctness under MCP tool lists + history | Only genuine MCP-security-adjacent HF dataset surfaced [V]. Gated; license unclear — **verify before training.** |
| Agent Security Bench (ASB) | https://arxiv.org/abs/2410.02644 | check repo [C] | 10 scenarios, 10 agents, 400+ tools, 27 attack/defence methods, 13 backbones | code+data | prompt injection, memory poisoning, Plan-of-Thought backdoor; **highest average ASR 84.30 %**, defences weak [V] | **EVAL.** The best single instrument for our MCP service. |
| MCP-Scan / tool-poisoning writeup | https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks | vendor blog [C] | tool | Python | tool poisoning, rug pulls, tool shadowing | EVAL/scanner, not data. |
| Agent Threat Rules (ATR) | referenced from SigmaHQ README integrators list [V] | MIT (per citation) [V] | unknown | rule format | prompt injection / tool poisoning / context-exfil detections | [U] find upstream repo, verify, then treat as a **detection rule corpus**. |
| AI Incident Database | https://incidentdatabase.ai/ | CC-BY-SA (incidents) [C] | 1,000+ incidents | web + JSON/GraphQL | real-world AI harm incidents | [C] taxonomy/context, not SFT. |
| AVID (AI Vulnerability Database) | https://avidml.org/ | check repo [C] | hundreds of vulns | YAML/JSON | AI/ML vulnerability taxonomy mapped to CWE/CVE | [C]. |

---

## 7. G6 — Real endpoint telemetry & malware behaviour

Required to make the always-on local service of `defense-architecture.md` **testable**, and to give
the model realistic event distributions instead of imagined ones.

| Name | URL | License | Size | Format | Covers | Verdict |
|---|---|---|---|---|---|---|
| EMBER 2018 | https://github.com/elastic/ember · data https://ember.elastic.co/ember_dataset_2018_2.tar.bz2 (sha256 `b6052eb8…`) [V] | repo license check; data free-download [V] | **1M PE files** (2017 set 1.1M) [V] | raw JSON features → vectorised [V] | static PE malware detection | **[V] ADMIT.** Feature **version 2**, LIEF 0.9.0 pinned — version mismatch silently breaks models [V]. |
| EMBER 2017 | https://ember.elastic.co/ember_dataset.tar.bz2 · `…_2017_2.tar.bz2` [V] | as above | 1.1M PEs | as above | malware drift studies | [V] **do not naively pool 2017+2018** — selection criteria differ [V]. |
| SOREL-20M | https://github.com/sophos/SOREL-20M | Sophos/ReversingLabs research terms [C] | ~20M files feature-level (~10 TB raw) [C] | `.jsonl` features + metadata | Windows malware at scale, family tags | [C] per-sample binaries have separate terms. |
| BODMAS | https://github.com/bodmas-cybersecurity/Bodmas-Data-Lake | research-use agreement [C] | ~57k malware + 77k benign, 2019–20 | CSV features | **concept-drift** malware classification | [C] two guessed paths 404'd — confirm host. |
| DikeDataset | https://github.com/iosifache/DikeDataset | MIT (repo) [C] | ~1k malicious + ~1k benign | PE files + labels | lightweight PE classification, clean split | [C] excellent for a *reproducible* local test set. |
| CIC-MalMem-2022 | https://www.unb.ca/cic/datasets/malmem-2022.html | CIC research terms [C] | ~58k memory dumps | CSV | obfuscated malware **memory** forensics | [C]. |
| Mordor | https://github.com/OTRF/Mordor · https://mordordata.io/ | MIT [C] | hundreds of attack datasets | JSON (Security/Sysmon) | **pre-recorded red-team telemetry mapped to ATT&CK** | [C] **best log-source corpus for detection training.** |
| Splunk attack_data / Attack Range | https://github.com/splunk/attack_data · https://github.com/splunk/attack_range | Apache-2.0 [C] | large, growing | JSON logs (Windows/AD/cloud) | Atomic Red Team simulations in log form | [C] pairs natively with Splunk Security Content [V]. |
| LogHub | https://github.com/logpai/loghub | per-dataset terms [C] | ~20 datasets, GBs | raw logs | anomaly detection (HDFS, BGL, Windows, Linux) | [C]. |
| CIC-IDS2017/2018/2019 | https://www.unb.ca/cic/datasets/ids-2017.html | CIC research terms [C] | ~2.8M+ flows (2017) | PCAP + CSV | network intrusion detection | [C] heavily used — **own-eval contamination risk**. |
| UNSW-NB15 | https://research.unsw.edu.au/projects/unsw-nb15-dataset | research terms [C] | ~2.5M records | CSV + PCAP | network intrusion, 9 attack families | [C]. |
| LANL cyber data | https://csr.lanl.gov/data/cyber1/ | LANL terms [C] | ~TBs (auth, flows, DNS) | CSV/JSON | enterprise-scale anomaly detection | [C]. |
| DARPA Transparent Computing | https://github.com/darpa-i2o/Transparent-Computing | US Gov public release [C] | 5 GB–TBs | provenance graphs (JSON/AVRO) | APT / whole-system provenance | [C] best provenance substrate for `vulnerabilities.md` §4. |
| theZoo | https://github.com/ytisf/theZoo | GPL-style/educational [C] | hundreds of live samples | passworded ZIPs | malware samples for sandbox work | [C] isolated lab only. |
| VirusShare | https://virusshare.com/ | registration + ToU, no redistribution [C] | millions, TB-scale | raw binaries + MD5 torrents | large-scale malware corpus | [C] access-gated, heavy. |

---

## 8. G7 — 2025–2026 releases worth attention

| Name | URL | License | Size | Format | Covers | Verdict |
|---|---|---|---|---|---|---|
| CTI-Rationale | https://huggingface.co/datasets/EbruResul/CTI-Rationale | CC-BY-4.0, gated auto [V] | 10k–100k [V] | JSONL/CSV [V] | ATT&CK mapping w/ rationale, **2025 advisories included** [V] | ADMIT candidate (also §2). |
| FALCON CTI→rule | https://huggingface.co/datasets/shaswatamitra/falcon-yara-cti-rule | **CC-BY-NC-ND-4.0** [V] | <1k each [V] | parquet, arXiv 2508.18684 [V] | CTI→gold YARA/Snort rule + **LLM decoy hard-negatives** [V] | **EVAL-only (ND, NC)** — but the *decoy construction* is a methodology template worth copying. |
| `echel0nn1881/kimi-cyber-reasoning` | https://huggingface.co/datasets/echel0nn1881/kimi-cyber-reasoning | **WTFPL** [V] | **997 CoT records**, 13 cyber disciplines [V] | JSON [V] | distilled cyber reasoning traces + tool invocation [V] | Small but permissive reasoning seed. **Verify distillation provenance/ToS** before training. |
| `alixansec/ctiaz` | https://huggingface.co/datasets/alixansec/ctiaz | **CC-BY-4.0** [V] | 1k–10k [V] | **STIX 2.1** JSON + parquet + CSV [V] | IOCs, vuln scans, ransomware leaks, APT campaigns [V] | Rare real STIX export (also §3). Small. |
| `ctokx/cti-attack-synthetic-augmentation` | https://huggingface.co/datasets/ctokx/cti-attack-synthetic-augmentation | **Apache-2.0** [V] | 1k–10k [V] | JSON [V] | synthetic multi-label ATT&CK sentences (49 techniques) [V] | **TRAIN-ONLY, machine-generated** — class balancing for rare techniques; **never eval.** |
| Aegis 2.0 | https://huggingface.co/datasets/nvidia/Aegis-AI-Content-Safety-Dataset-2.0 | CC-BY-4.0 [V] | 33,416 [V] | JSON [V] | content-safety | ADMIT (also §5). |
| UK AISI Inspect | https://github.com/UKGovernmentBEIS/inspect_ai | MIT [C] | tooling + eval sets | Python | standardised safety evals/logging | [C] the harness behind AgentHarm [V] — adopt for consistent eval plumbing. |
| AI Incident Database (API) | https://incidentdatabase.ai/ | CC-BY-SA [C] | 1,000+ | JSON/GraphQL | real AI incidents | [C] context. |

*Seen only as HF API index snippets, not opened — **do not cite as confirmed**:* `C-Tianyu/NanoJev-Data`,
`arjun180-new/cti_realm`, `Jake/glokta-cti`, `Rigam22/municipal-iot-cti-graph`,
`TypeSafeAI/Omni-Frontier-Distillation-SFT`. Several look like low-provenance user uploads. **[U]**

---

## 9. Cross-cutting ingestion rules (feed these into U1 / U13)

1. **License is the binding constraint, not availability.** Three tiers:
   - **train-clean** (MIT/Apache-2.0/CC-BY-4.0): Splunk Security Content, OSV, EMBER 2018, WMDP
     *(license-wise clean but eval-only by role)*, JBB-Behaviors *(same caveat)*, Aegis 2.0,
     apt-cti-reports, `ctiaz`, `ctokx` (train-only).
   - **review-required**: SigmaHQ DRL-1.1, Neo23x0 signature-base (post-2021 only), Elastic
     detection-rules, PurpleLlama, AgentHarm, DNRTI/APTNER (no license at all).
   - **eval-only, never train**: WMDP, JBB-Behaviors, HarmBench, AdvBench, StrongREJECT, BIPIA,
     AgentDojo, InjecAgent, AgentHarm, CTI-Bench, SecQA, SecEval, SecBench, FALCON, ASB.
2. **Contamination watch.** Training on any §5 row makes the corresponding number meaningless, and
   contaminates public leaderboards. Also: EMBER feature-version mismatch (LIEF 0.9.0 vs newer)
   silently corrupts reproducibility [V].
3. **Auth-key / gated resources** (record the key in the receipt, not the repo): abuse.ch family
   (free Auth-Key) [V]; `EbruResul/CTI-Rationale` and `rogue-security/mcp-tool-use-quality-benchmark`
   (`gated: auto`) [V]; VirusShare / Malpedia / OTX / CIC (registration + ToU) [C].
4. **Biggest single gap remains real messy CTI text.** `hackerman700000/apt-cti-reports` +
   `EbruResul/CTI-Rationale` + DFIR Report narratives. Everything else in §2 is a feed or a small
   NER set.
5. **Second-biggest gap is security code (§4)** — absent from the current plan entirely.
6. **Decontaminate against our own holdout first** (500 rows), *and* against CTI-Bench/SecQA, using
   the 13-gram + containment instruments already specified in `SPEC-V2.md` U1, before any of these
   are admitted. Fenrir-style sibling overlap is a real risk for CTI corpora.

## 10. Recommended minimal addition set (if only three things are added)

1. `hackerman700000/apt-cti-reports` + `EbruResul/CTI-Rationale` → real extraction + justified ATT&CK
   mapping. Closes G1, the gap the capability box measured most starkly.
2. SigmaHQ + Splunk Security Content (+ Sigma spec) → format compliance on real schemas. Closes G2.
3. AgentDojo + InjecAgent + ASB as **eval**, Aegis 2.0 + refusal rows as **train** → closes G4/G5 for
   the MCP deployment, and gives the always-on service an instrument before it is built.
