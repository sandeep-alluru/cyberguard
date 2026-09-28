# defense-architecture.md — an always-on small model + MCP for local endpoint protection

**Sprint:** CYBERGUARD research sprint, 2026. **Deliverable 3 of 4.**
**Read first:** `ARTIFACT-MAP.md`, `docs/CAPABILITY-v1.md`, `docs/SPEC-V2.md`.
**Companion:** `vulnerabilities.md` §3B (the injection class this architecture must survive),
`datasets.md` §5–§7 (the instruments), `top-models.md` (which model, and how to get it).

**Question:** can a small model (2–4B) run as an always-on service behind an MCP server and give
antivirus / anti-adware / anti-spyware-style protection on a laptop or a home lab?

**Bottom line, stated before the architecture:** **Yes as an enrichment and triage layer. No as the
blocking hot path.** The measured evidence converges: deterministic sensors/rules do the blocking;
the model is invoked only on already-suspicious events. The naive design — model reads raw telemetry —
fails specifically because attacker-controlled text *is* the input, and the measured residual for
layered defences against that is ~8.4 % ([LogInject](https://arxiv.org/abs/2607.14493)).

---

## 0. Evidence integrity

- `web_search` was captcha-blocked this sprint; evidence came from direct `web_fetch` of vendor docs,
  specs, arXiv pages and GitHub repos. **[V]** = fetched this sprint. **[C]** = canonical URL, not
  fetched. **[U]** = unverified, do not build on it.
- **No source this sprint measured a 2–4B model classifying endpoint events/second on laptop-class
  hardware.** Throughput figures below are *arithmetic on measured building blocks*, explicitly
  labelled as such. That measurement is the first task (§10, Q1).

---

## 1. What the requirement actually is

"Antivirus/adware/spyware-style protection" decomposes into four capabilities that are usually
conflated:

| Capability | What it needs | Can a local LLM do it? |
|---|---|---|
| **Pre-execution block/allow on files** | a synchronous veto at the OS API/kernel boundary; boot-time trust; tamper resistance | **No.** Requires signed kernel/driver code; see §7. |
| **Detection of known-bad** | signatures, hashes, reputation, YARA | **No** — and it shouldn't; deterministic tools are faster and exact. |
| **Triage/enrichment of suspicious events** | context joining, ATT&CK mapping, explanation, next-step suggestion | **Yes, measurably.** This is the winning role. |
| **Explaining and prioritising for a human** | natural-language synthesis over evidence | **Yes.** Removes the "read 10k alerts" bottleneck that `vulnerabilities.md` §2 identifies as the real attack on the defender. |

So the architecture below is a **triage layer with a hard boundary below it**, not an AV replacement.

## 2. Design principle that all evidence supports

**The model must never be the enforcement point, and must never see raw attacker text as trusted
instruction.**

Two independent measurements make this non-negotiable:
- **LogInject** — *passive* injection: payloads persist in log fields and execute when an analyst's
  LLM queries them. On LogInject-1.0 (12,847 entries, 2,569 adversarial) base attack success was
  **up to 88.2 % (83.4 % avg)**; context-stitched multi-entry payloads hit **76.4 %**; layered
  filtering + prompt hardening + output validation cut success by **90.4 % but left 8.4 % residual**
  ([2607.14493](https://arxiv.org/abs/2607.14493)).
- **ALIBI** — a coherent false narrative flipped **30 of 35** baseline-malicious samples to benign on
  Gemini 2.5 Pro, transferred to ELF, and verification-guided defence still left **42.9 %** of
  malicious samples reaching benign. Its own conclusion is the architectural rule: provenance checks
  that separate verified facts from attacker-controlled claims
  ([2609.19722](https://arxiv.org/abs/2609.19722)).

Corollary: **anything the model says must be re-checked by a deterministic component before it causes
an action.**

## 3. Telemetry available on endpoints (the model's raw material)

**Linux**
- **eBPF LSM** — privileged instrumentation of LSM hooks; can return `-EPERM` (enforcement)
  [kernel docs](https://docs.kernel.org/bpf/prog_lsm.html) [V]
- **fanotify** — notification **and interception**; permission events (`FAN_OPEN_EXEC_PERM`,
  `FAN_OPEN_PERM`) require the listener to grant/deny, and the API can read/modify files before other
  apps access them. The man page names **"virus scanning"** as the use case — the closest Linux
  analogue to a synchronous AV file filter [man7](https://man7.org/linux/man-pages/man7/fanotify.7.html) [V]
- **auditd** — userspace audit daemon, rules in kernel; `audit=1` needed to catch pre-daemon processes
  [man8](https://man7.org/linux/man-pages/man8/auditd.8.html) [V]
- **Falco** — CNCF runtime security, YAML rules over syscalls, modern eBPF/CO-RE probe
  [falco.org/docs](https://falco.org/docs/) [V]
- **Tetragon** — eBPF observability **and runtime enforcement**, tracing policies, enforcement modes
  [tetragon.io/docs](https://tetragon.io/docs/) [V]

**Windows**
- **Sysmon v15.22** — process creation with command line, hashes, driver/DLL loads,
  `CreateRemoteThread`, `ProcessAccess`, named pipes, WMI, DNS, `FileCreateStreamHash`,
  `ProcessTampering`; boot-start driver for early boot; protected service. **Microsoft states Sysmon
  "does not provide analysis of the events it generates"** — precisely the gap a model can fill
  [Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) [V]
- **ETW** — user/kernel event tracing [link](https://learn.microsoft.com/en-us/windows/win32/etw/event-tracing-portal) [V]
- **AMSI** — request-time scanning of files, memory/streams, URL/IP reputation, sessions correlating
  payload fragments; integrated with PowerShell/WSH/JScript/VBScript/Office VBA
  [AMSI](https://learn.microsoft.com/en-us/windows/win32/amsi/antimalware-scan-interface-portal) [V]
- **osquery** — OS-as-database; `file_events` + `yara_events` run YARA on filesystem change;
  runtime-fetchable rules [osquery](https://osquery.readthedocs.io/en/stable/) [V]

**macOS**
- **Endpoint Security** — C API system extension to **authorize pending events** or receive
  notifications (execs, mounts, forks, signals); requires entitlement
  [Apple](https://developer.apple.com/documentation/endpointsecurity) [V]
- **FSEvents** — directory-hierarchy change notifications
  [Apple](https://developer.apple.com/documentation/coreservices/file_system_events) [V]

**Practical asymmetry:** on Windows the pre-emptive controls (AMSI provider, ELAM/PPL service, kernel
minifilter) require the signed-driver/AV-vendor path ([ELAM](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/early-launch-antimalware) [V],
[PPL services](https://learn.microsoft.com/en-us/windows/win32/services/protecting-anti-malware-services-) [V]).
A user-space MCP process cannot occupy them. **This is the architectural constraint that decides the
whole design.**

## 4. Architecture

```
                      ┌───────────────────────────────────────────────┐
 APPLICATIONS/KERNEL  │ eBPF LSM · fanotify PERM · ETW/AMSI · Sysmon  │
                      │ auditd · EndpointSecurity · FSEvents ·osquery │
                      └───────────────┬───────────────────────────────┘
                                      │ raw events — NEVER model input
                      ┌───────────────▼───────────────────────────────┐
 L1 SENSORS + RULES   │ Falco / Tetragon / Sigma / YARA / osquery     │ ← BLOCK HERE
 (deterministic,      │ + hashes, reputation, static checks           │   (kernel/signed
  always on, cheap,   └───────────────┬───────────────────────────────┘    components only)
  auditable)                          │ only SUSPICIOUS events, rate-limited
                      ┌───────────────▼───────────────────────────────┐
 L2 FUSION + ENCODER  │ dedup · process-tree join · allowlist ·       │
                      │ **event-card serialiser**: bounded schema,    │
                      │ untrusted fields separated + sanitised,        │
                      │ no raw blobs, explicit provenance tags        │
                      └───────────────┬───────────────────────────────┘
                                      │ validated EventCard JSON (schema-checked)
                      ┌───────────────▼───────────────────────────────┐
 L3 LOCAL MODEL       │ 2–4B security-tuned model. ONE-SHOT scoring:  │
 (batched, prefix-    │ constrained verdict enum + confidence         │
  cached, low prio)   │ (logprobs) + ATT&CK/ATLAS technique.          │
                      │ NOT an agent loop. Continuous batching.       │
                      └───────────────┬───────────────────────────────┘
                                      │ verdict + evidence refs (NOT free text)
                      ┌───────────────▼───────────────────────────────┐
 L4 MCP TOOL SERVER   │ READ-MOSTLY, allowlisted, schema-validated:   │
 (stdio/localhost,    │ query_osquery · run_yara · get_hash_reputation│
  version-pinned)     │ get_attack_technique · sigma_render           │
                      └───────────────┬───────────────────────────────┘
                                      │
                      ┌───────────────▼───────────────────────────────┐
 L5 POLICY / RESPONSE │ auto-actions limited to REVERSIBLE enum:      │
                      │ quarantine file · kill PID · isolate net.     │
                      │ Destructive/irreversible → human approval.    │
                      └───────────────┬───────────────────────────────┘
                                      │
                      ┌───────────────▼───────────────────────────────┐
 L6 LEDGER + EVAL     │ append-only audit, signed verdicts, replayable│
                      │ corpus, FP/FN review, drift + injection tests │
                      └───────────────────────────────────────────────┘
```

**Why each layer exists (evidence-backed):**

1. **L1 blocks, and the model never votes on blocking.** Pre-execution veto needs fanotify
   `*_PERM`/eBPF-LSM/AMSI/EndpointSecurity; those are kernel/signed components, not a Python MCP
   server (see §3). Google's Mandiant-backed threat feed carries a dedicated
   *"Staying Ahead of Adversarial AI Through Agentic Source Code Review"* and CI/CD hardening work —
   the defence trend is deterministic pipelines with model assistance, not model enforcement
   ([GTIG index](https://cloud.google.com/blog/topics/threat-intelligence/)) [V].
2. **The rate limiter between L1 and L2 is what makes the design feasible.** The RuleAutoPilot pattern
   exists because noise "reduces LLM reasoning quality and increases cost": its *Benign Traffic
   Fingerprinting* stage strips benign flows before the LLM sees them, and its execution-grounded
   verification raised F1 0.443 → 0.539 ([2609.16231](https://arxiv.org/abs/2609.16231)) [V].
   OMNISEC is the same shape — detector proposes abnormal nodes/paths, LLM only adjudicates those
   with RAG evidence ([2503.03108](https://arxiv.org/abs/2503.03108)) [V].
3. **L2 event cards are the injection mitigation.** Fixed schema, capped field lengths, an explicit
   `untrusted_content` channel distinct from system instructions, escaped/clamped command lines and
   URLs. This directly targets LogInject's passive-injection and context-stitching mechanisms
   ([2607.14493](https://arxiv.org/abs/2607.14493)) [V]. **Expect residual risk anyway** — 8.4 %
   after layered defences.
4. **L3 is one-shot, not agentic.** Reasons: (a) measured throughput (below) makes multi-turn agent
   loops ~100× too slow for a live event stream; (b) Autonomy = agency = a bigger attack surface
   (OWASP **LLM06:2025 Excessive Agency**). Microsoft's shipped agent protection likewise inspects
   "a fast, inline check at one of these event points rather than continuous monitoring"
   ([Defender agent protection](https://learn.microsoft.com/en-us/defender-endpoint/ai-agent-runtime-protection-overview)) [V].
5. **L4 wraps existing tools; it does not reimplement them.** There is a real ecosystem of MCP
   servers for security work — osquery, YARA (YaraFlux), VirusTotal, Wazuh, Zeek/Suricata, Velociraptor
   — see §6. VelociraptorMCP's design note is the model to copy: *"evidence collection is
   deterministic and synthesis is model-only"*, with dangerous tools behind an explicit flag and
   bounded analyst roles ([mcp-velociraptor](https://github.com/mgreen27/mcp-velociraptor)) [V].
6. **L5 keeps actions reversible.** OWASP LLM06 exists because agents get more authority than they
   need; an LLM error must not be able to exfiltrate or destroy.
7. **L6 makes the system falsifiable.** Without a replayable ledger, false-positive and injection
   testing is theatre.

## 5. Feasibility: what the numbers actually allow

**Measured building blocks (all with URLs):**

| Measurement | Value | Source |
|---|---|---|
| llama.cpp, Llama-2-7B, Apple M4 base (Q4_0) | **221 t/s prompt, 24.1 t/s generate** | [llama.cpp #4167](https://github.com/ggml-org/llama.cpp/discussions/4167) [V] |
| Same, M4 Max | **886 t/s prompt, 83.1 t/s generate** | same [V] |
| Phi-3-mini 3.8B 4-bit on iPhone 14, offline | **>12 tok/s** | [2404.14219](https://arxiv.org/abs/2404.14219) [V] |
| Speculative decoding | **2–3×** with identical outputs (T5-XXL) | [2211.17192](https://arxiv.org/abs/2211.17192) [V] |
| Structured/constrained decoding (XGrammar) | up to **100×** speedup vs prior solutions, near-zero overhead when co-designed | [2411.15100](https://arxiv.org/abs/2411.15100) [V] |
| vLLM on DGX Spark, local recipe | `--max-num-seqs` capped at **4**; above that, per-token bandwidth tax outweighs continuous-batching gains and TTFT spikes | [vLLM blog 2026-06](https://vllm.ai/blog/2026-06-01-vllm-dgx-spark) [V] |
| vLLM on Arm CPUs | up to **6.2×** baseline throughput after allocator/atomic/prepack/kernel work | [vLLM blog 2026-07](https://vllm.ai/blog/2026-07-29-optimizing-vllm-on-arm-cpus) [V] |
| Decode is memory-bandwidth-bound; output length dominates latency | 7B FP16 @ 14 ms TPOT ≈ 1 TB/s | [Databricks](https://www.databricks.com/blog/llm-inference-performance-engineering-best-practices) [V] |

**Derived envelope (arithmetic, NOT a measurement — labelled as such):**
1. *Single-token verdicts:* at 24 t/s → **~24 verdicts/s**; at 83 t/s → **~83/s**; a 3B model roughly
   2–3× faster. So **10–100 verdicts/s is in range for one-shot classification.**
2. *Prompts are the tax:* a 300-token event at 221 t/s ≈ 1.4 s uncached ≈ **0.7 events/s**. Prefix
   caching (only the delta is expensive) restores token-bound throughput — **this is why event cards
   must be template-stable**.
3. *Agentic loops are ~100× too slow:* 3–10 tool calls with multi-turn reasoning → seconds/event →
   **≤1 event/s**.
4. *Batch, don't converse.* The 10–100 events/s band is reached by **batching × prefiltering**.
5. *Resource ceiling on a desk-side box:* vLLM's own local recipe caps sequences at 4, and KV-cache
   utilisation is <5 % single-user ([vLLM](https://vllm.ai/blog/2026-06-01-vllm-dgx-spark)) [V].
   **Return-of-experience: the machine is bandwidth-limited before it is compute-limited.**

**What prior art achieved on narrow tasks with small models:**
- **OpenSOC-AI**: LoRA on **TinyLlama-1.1B** (12.6M trainable, 1.13 % of base), 450 SOC examples,
  trained **<5 min on one T4**; held-out 50: threat-class accuracy 0 %→**68 %**, severity 28 %→58 %,
  **F1 0.68** ([2604.26217](https://arxiv.org/abs/2604.26217)) [V]
- **On-device LLM for IoT DDoS** (LLaMA 3.2 1B/3B, Gemma 3 1B/4B + CoT/RAG): up to **macro-F1 0.85**
  ([2601.14343](https://arxiv.org/abs/2601.14343)) [V]
- **SLM phishing detection from raw HTML** (15 SLMs, 1B–70B): SLMs underperform proprietary LLMs but
  are "a viable and scalable alternative", with local deployment giving data control
  ([2511.15434](https://arxiv.org/abs/2511.15434)) [V]
- **SIR-Bench** (794 cases, 129 incident patterns): **97.1 % TP detection, 73.4 % FP rejection,
  5.67 novel findings/case**, explicitly designed to distinguish investigation from "alert parroting"
  ([2604.12040](https://arxiv.org/abs/2604.12040)) [V]
- **Reality check**: a 2026 study of 8 domain-adapted LLMs/SLMs on STRIDE found domain adaptation
  "does not consistently outperform their general-purpose counterparts", and scale gains were
  "neither consistent nor sufficient for reliable threat modelling"
  ([2605.10808](https://arxiv.org/abs/2605.10808)) [V]
- **CORTEX** frames the problem: SOCs get "tens of thousands of daily alerts, with only a small
  fraction corresponding to genuine attacks" ([2510.00311](https://arxiv.org/abs/2510.00311)) [V]

## 6. The MCP layer: security design

**Real MCP servers that already exist for this work** (prefer wrapping over building):

| Domain | Server | URL |
|---|---|---|
| Endpoint inventory | Osquery MCP (Java, MIT); osqueryi STDIO MCP | https://github.com/kousen/OsqueryMcpServer · https://github.com/mdfranz/osqueryi-mcp [V] |
| YARA | YaraFlux | https://github.com/ThreatFlux/YaraFlux [V] |
| Malware RE | Reversecore_MCP (Radare2/YARA/LIEF/Capstone) | https://github.com/sjkim1127/Reversecore_MCP [V] |
| Malware lab playbooks | flarevm-mcp (48 tools) | https://github.com/zixuantemp/flarevm-mcp [V] |
| Threat intel | Official VirusTotal MCP | https://github.com/VirusTotal/virustotal-mcp [V] |
| Sandbox detonation | Malware-Sandbox-mcp (Hybrid Analysis / tria.ge / ANY.RUN) | https://github.com/mukul975/Malware-Sandbox-mcp [V] |
| SIEM | Wazuh MCP servers | https://github.com/gbrigandi/mcp-server-wazuh · https://github.com/socfortress/wazuh-mcp-server [V] |
| NSM | Zeek / Suricata / Malcolm MCP | https://github.com/lidless-labs/zeek-mcp · https://github.com/lidless-labs/suricata-mcp [V] |
| DFIR at scale | Velociraptor MCP | https://github.com/mgreen27/mcp-velociraptor · https://github.com/socfortress/velociraptor-mcp-server [V] |
| Detecting the AI itself | osquery extension for MCP servers/agent CLIs/live sockets | https://github.com/karmine05/agentic-detector [V] |

> **Dual-use warning:** HexStrike AI exposes "150+ cybersecurity tools for automated pentesting" to any
> MCP client (12k+ stars) — https://github.com/0x4m4/hexstrike-ai [V]. Never co-install it with a
> monitoring agent.

**MCP's own security model — what an MCP-based monitor inherits** (from the protocol's
security-best-practices page) [V]:
confused deputy (static client ID + dynamic registration + consent cookie → auth-code theft to an
attacker `redirect_uri`), **token passthrough** (explicitly forbidden — breaks audience validation and
auditability), **SSRF** during OAuth metadata discovery (cloud metadata `169.254.169.254`, localhost
services, DNS rebinding, redirect chains), **session hijacking**, **local MCP server compromise**,
**stdio transport in proxy scenarios**, **OAuth URL validation**, and **scope minimisation**. Required
mitigations include per-client consent storage, exact-match redirect URIs, cryptographically random
single-use `state`, HTTPS-only, and blocking private IP ranges, preferably via an egress proxy rather
than hand-rolled IP parsing.
Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices [V]

**Additional model-facing risks** (Invariant Labs) [C]: **tool poisoning** (hidden instructions in tool
descriptions the user never sees but the model obeys — their example exfiltrates `~/.ssh/id_rsa`),
**rug pulls** (a description changes after approval), **tool shadowing** (a malicious server's
description changes how the agent uses a *trusted* server's tool). https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks

**Concrete MCP rules for this design:**
1. **Local + read-mostly + stdio/localhost only.** No remote MCP servers for the monitoring path.
2. **Pin and hash tool definitions**; alert on change (defeats rug pulls).
3. **Validate every tool result as untrusted data**, same as a log line — a VirusTotal report or a
   filename is attacker-influenced.
4. **Explicit dangerous-tool flag**, default off (the `ENABLE_DANGEROUS_TOOLS` pattern).
5. **Tool output goes into the `untrusted_content` channel, never the instruction channel.**
6. **Scope minimisation** and no token passthrough; the agent's token is for the agent, not for
   downstream APIs.
7. **Test with AgentDojo / InjecAgent / ASB before shipping** (`datasets.md` §5–§6).

## 7. Tradeoffs, failure modes, and what vendor AV does that this cannot

| Axis | Reality | Evidence |
|---|---|---|
| **Prompt injection through telemetry** | The killer risk. 88.2 % ASR undefended → **8.4 % residual** with layered defences | [2607.14493](https://arxiv.org/abs/2607.14493) [V] |
| **Deceptive-narrative attacks on triage** | 30/35 malicious→benign flips; **42.9 %** still benign after defence | [2609.19722](https://arxiv.org/abs/2609.19722) [V] |
| **False-positive fatigue** | Confident wrong verdicts amplify an already bad ratio; SIR-Bench needed an adversarial judge because agents "parrot" alerts | [2510.00311](https://arxiv.org/abs/2510.00311), [2604.12040](https://arxiv.org/abs/2604.12040) [V] |
| **Resource cost** | Permanent RAM/VRAM/power + KV cache; bandwidth-limited before compute-limited; local recipe caps concurrency at 4 | [vLLM Spark](https://vllm.ai/blog/2026-06-01-vllm-dgx-spark) [V] |
| **Privacy (the pro side)** | Local deployment keeps file paths, command lines, clipboard, EVTX on-box; SLMs "can be deployed on local infrastructure, providing… greater control over data" | [2511.15434](https://arxiv.org/abs/2511.15434) [V] |
| **Drift** | Detectors relying on implementation-specific features are "vulnerable to concept drift"; a frozen model inherits its cutoff | [2608.27994](https://arxiv.org/abs/2608.27994) [V] |
| **Cannot replace: pre-execution blocking** | fanotify `*_PERM`, eBPF-LSM `-EPERM`, AMSI request-time scanning, EndpointSecurity authorisation are the only true vetoes | [fanotify](https://man7.org/linux/man-pages/man7/fanotify.7.html), [eBPF LSM](https://docs.kernel.org/bpf/prog_lsm.html), [AMSI](https://learn.microsoft.com/en-us/windows/win32/amsi/antimalware-scan-interface-portal) [V] |
| **Cannot replace: boot-time trust** | ELAM drivers start before other boot-start drivers and run as PPL | [ELAM](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/early-launch-antimalware) [V] |
| **Cannot replace: tamper resistance** | Protected anti-malware services load only trusted signed code and reject injection from non-protected processes | [PPL services](https://learn.microsoft.com/en-us/windows/win32/services/protecting-anti-malware-services-) [V] |
| **Cannot replace: memory scanning** | AMSI covers memory/streams; Sysmon detects `CreateRemoteThread` and process tampering. Both are API/kernel-level; an LLM reading logs is not in the target process | [AMSI](https://learn.microsoft.com/en-us/windows/win32/amsi/antimalware-scan-interface-portal), [Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) [V] |
| **Cannot replace: millisecond reputation/behaviour** | Defender blocks "almost all malware at first sight, in milliseconds" with behavioural/process-tree logic | [Defender](https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-antivirus-windows) [V] |

**Honest summary of the trade:** you gain explanation, correlation and ATT&CK mapping that
thresholds miss; you pay a permanent resource cost, added latency on suspicious paths, a **new
injectable surface**, and a new failure mode (confident wrong verdicts). The kernel/AMSI/fanotify
layer must not be weakened to make room for it.

## 8. Deployment shapes that fit "laptop / home lab"

| Shape | Fit | Notes |
|---|---|---|
| **A. Single laptop, 3B Q4, llama.cpp server** | good for one machine | ~2–3 GB resident; priority-nice it; expect the prompt-processing tax (§5) |
| **B. One always-on home-lab box + thin agents** | **recommended** | Sensors/rules on each endpoint; model + MCP on the box; agents ship event cards only. Centralised ledger, one GPU/CPU budget, privacy preserved for raw data |
| **C. GB10-class box (this fleet)** | best | vLLM-style serving with prefix caching; remember the `max-num-seqs`≈4 guidance before tuning |
| **D. Fully local, one process per endpoint** | avoid | duplicate models, duplicate drift, no shared ledger |

**Concrete first build (Shape B), minimum viable:**
1. L1: Falco or Tetragon on Linux endpoints (both eBPF, both enforce-capable); Sysmon on Windows;
   YARA via osquery `yara_events`.
2. L2: a card serialiser with a frozen schema — `{event_id, ts, host, process{tree}, file{hash,path},
   net{...}, provenance_tag, untrusted_content[]}`. **Template-stable** so prefix caching works.
3. L3: a 2–4B security-tuned model in one-shot constrained-label mode (start with
   `nyxspecter4/kin-cybersecurity-3b` or `Foundation-Sec-8B-GGUF`; `top-models.md` §1).
4. L4: wrap `query_osquery`, `run_yara`, `get_hash_reputation`, `get_attack_technique`,
   `sigma_render`. Read-mostly, version-pinned.
5. L5: auto-actions = {quarantine file, kill PID, isolate net} only; everything else to a human.
6. L6: append-only ledger + nightly replay.
7. **Before any auto-action:** run AgentDojo/InjecAgent/BIPIA against L2–L4 and publish the residual.

## 9. What this file deliberately does NOT claim

- It does **not** claim a local LLM can stop malware. It claims it can improve triage.
- It does **not** claim the injection residual is acceptable; 8.4 % on a *24/7 monitor* is large.
- It does **not** claim the throughput arithmetic in §5 is a benchmark. It is a hypothesis with
  numbers, and §10 Q1 is how to test it.
- It does **not** substitute for endpoint AV/EDR. It sits beside them.

## 10. Open questions — the measurement plan (in priority order)

1. **Events/second on *our exact* hardware.** Benchmark a 2–4B model doing 1-token constrained
   classification on fixed event cards: sweep `--max-num-seqs`, prefix-cache on/off, 1-token vs
   8-token outputs. **Currently UNVERIFIED for laptop CPU and consumer GPU.**
2. **FPR per 10k real benign events.** OpenSOC-AI reports on 50 examples; SIR-Bench on synthetic
   cloud replay. Neither is a home-lab file/process stream. Measure before any auto-action.
3. **Serialisation ablation.** Does compact `key=value` beat JSON? How much does field truncation cost
   accuracy? **No paper found — [U].**
4. **End-to-end injection resistance.** Re-run LogInject-style passive/stitched injection against the
   *event-card* pipeline with L2 active, and ALIBI-style narrative attacks against any file-content
   summarisation. Baselines to beat: 88.2 % undefended ASR, 8.4 % residual after layered defences.
5. **Tool-layer injection.** Audit every MCP server in §6 for tool poisoning/rug pull; test whether
   tool *outputs* (VT reports, YARA strings, filenames) can steer the verdict.
6. **Battery/thermal envelope** of an always-on 3B Q4 model, and whether priority controls prevent
   user-visible latency spikes.
7. **Drift test** — a rolling holdout, not a one-time eval.
8. **Value-add head-to-head:** L1-rules-only vs L1+L3 on analyst time-to-triage and missed detections.
   Without this number the model is plausible but unproven.

## 11. URL index

Telemetry: https://docs.kernel.org/bpf/prog_lsm.html · https://man7.org/linux/man-pages/man7/fanotify.7.html · https://man7.org/linux/man-pages/man8/auditd.8.html · https://falco.org/docs/ · https://tetragon.io/docs/ · https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon · https://learn.microsoft.com/en-us/windows/win32/etw/event-tracing-portal · https://learn.microsoft.com/en-us/windows/win32/amsi/antimalware-scan-interface-portal · https://learn.microsoft.com/en-us/windows-hardware/drivers/install/early-launch-antimalware · https://learn.microsoft.com/en-us/windows/win32/services/protecting-anti-malware-services- · https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-antivirus-windows · https://osquery.readthedocs.io/en/stable/ · https://osquery.readthedocs.io/en/stable/deployment/yara/ · https://developer.apple.com/documentation/endpointsecurity · https://developer.apple.com/documentation/coreservices/file_system_events

MCP: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices · https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks · https://learn.microsoft.com/en-us/defender-endpoint/ai-agent-runtime-protection-overview

Performance: https://github.com/ggml-org/llama.cpp/discussions/4167 · https://www.databricks.com/blog/llm-inference-performance-engineering-best-practices · https://vllm.ai/blog/2026-06-01-vllm-dgx-spark · https://vllm.ai/blog/2026-07-29-optimizing-vllm-on-arm-cpus · https://arxiv.org/abs/2404.14219 · https://arxiv.org/abs/2211.17192 · https://arxiv.org/abs/2411.15100

Papers: https://arxiv.org/abs/2604.26217 · https://arxiv.org/abs/2503.03108 · https://arxiv.org/abs/2601.14343 · https://arxiv.org/abs/2511.15434 · https://arxiv.org/abs/2605.10808 · https://arxiv.org/abs/2608.27994 · https://arxiv.org/abs/2609.16231 · https://arxiv.org/abs/2609.19722 · https://arxiv.org/abs/2607.14493 · https://arxiv.org/abs/2604.12040 · https://arxiv.org/abs/2510.00311

MCP servers: https://github.com/kousen/OsqueryMcpServer · https://github.com/mdfranz/osqueryi-mcp · https://github.com/karmine05/agentic-detector · https://github.com/ThreatFlux/YaraFlux · https://github.com/sjkim1127/Reversecore_MCP · https://github.com/zixuantemp/flarevm-mcp · https://github.com/VirusTotal/virustotal-mcp · https://github.com/w0h1v/mcp-virustotal · https://github.com/mukul975/Malware-Sandbox-mcp · https://github.com/gbrigandi/mcp-server-wazuh · https://github.com/gensecaihq/Wazuh-MCP-Server · https://github.com/socfortress/wazuh-mcp-server · https://github.com/UPinar/contrastapi · https://github.com/sredleaf-prog/detection-engineering-mcp-server · https://github.com/chiomao23/MCP-Detection-Knowledge-Bases · https://github.com/lidless-labs/zeek-mcp · https://github.com/lidless-labs/suricata-mcp · https://github.com/nagameTW/mcp-server-malcolm · https://github.com/mgreen27/mcp-velociraptor · https://github.com/socfortress/velociraptor-mcp-server · https://github.com/0x4m4/hexstrike-ai

Vendor/ecosystem: https://cloud.google.com/blog/topics/threat-intelligence/
