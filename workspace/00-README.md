# CyberGuard research sprint — 4 deliverables

Workspace for the 3-hour research sprint (2026), run after the v2 plan of record.
Read `ARTIFACT-MAP.md`, `docs/SPEC-V2.md`, `docs/DATASET-V2.md`, `docs/CAPABILITY-v1.md` first, so
nothing here re-recommends what already exists.

| file | answers |
|---|---|
| `datasets.md` | What datasets we need BEYOND the current 195 MB corpus (7 named gaps, per-row licence/size/format/attack class, ingestion tiers) |
| `vulnerabilities.md` | Vulnerability classes relevant to frontier-model-grade offensive use + a runnable methodology for discovering NEW vulnerabilities |
| `defense-architecture.md` | Whether a small always-on model behind MCP can give AV/adware/spyware-style protection (L0–L6 sketch, measured feasibility, tradeoffs) |
| `top-models.md` | How to obtain or train a top-tier defensive model at small scale (model table, data recipes, safety-retention techniques, 24 h recipe) |

## Headline findings

1. **The frontier risk is augmentation, not autonomy.** Real targets: agents clear **~13 %** of
   critical real CVEs (CVE-Bench) and **~20 %** of real vulnerability-reproduction tasks (CyberGym,
   which also discovered **34 zero-days** and 18 incomplete patches). Synthetic-injection targets are
   cleared at **92.85 %** (HonestCyberEval). The cheap win for attackers is recon/triage/lure
   automation, not a self-driving exploit.
2. **The new target class is our own stack.** Prompt injection is OWASP LLM01:2025; MCP ships
   confused-deputy/token-passthrough/SSRF/tool-poisoning risks in its own spec; ASB measures **84.3 %**
   average attack success across 27 methods. A local model reading telemetry *is* an injection sink —
   LogInject shows **88.2 %** undefended ASR and **8.4 % residual** even after layered defences.
3. **A local small model is a triage layer, never the blocking hot path.** Deterministic
   sensors/rules (fanotify/eBPF-LSM/AMSI/EndpointSecurity) keep the veto; the model enriches only
   pre-filtered suspicious events. Measured small-model priors are encouraging but narrow: 1.1B LoRA
   → F1 0.68 on SOC triage in <5 min on a T4; 3B–4B → macro-F1 0.85 on IoT DDoS.
4. **A 4B defensive model can be genuinely competitive if the data is reasoning-shaped.** CyberPal 2.0
   (4B) ranks **second only to Sec-Gemini v1** on threat investigation, ahead of GPT-4o/o1/o3-mini.
   But 24 h of LoRA on a GB10 buys **behaviour** (refusal, format, ID grounding — exactly v1's three
   defects), **not knowledge**; the strong open models got there via continued pretraining on
   10B+-token curated corpora.
5. **Safety degradation is the default, not a risk.** 10 adversarial examples (<$0.20) break
   GPT-3.5; <$200 on one GPU drives Llama-2-70B to ~1 % refusal. v1's collapse (24/60 → 6/60) is the
   predicted outcome. **Safe LoRA** (training-free projection onto the safety subspace) is the
   highest safety-per-effort fix for this project.
6. **The biggest dataset gaps are (a) real messy CTI text** — v1 fabricated an IOC in 65 % of reports
   on a synthetic floor — and **(b) security code**, which is missing from the plan entirely.
   Recommended minimal add: `apt-cti-reports` + `CTI-Rationale` (real text), SigmaHQ + Splunk Security
   Content (format), AgentDojo/InjecAgent/ASB (agent eval) + Aegis 2.0 (trainable safety).

## Method notes / limitations (applies to all four files)

- `web_search` was **captcha-blocked** for this sprint (DuckDuckGo/Mojeek challenge pages, Bing noise).
  All evidence came from **direct `web_fetch`** of arXiv abstract pages, HuggingFace cards/APIs, GitHub
  repos, and vendor/spec pages. This is a verified sample, not an exhaustive survey.
- Per-row markers: **[V]** fetched this sprint · **[C]** canonical URL, not fetched · **[U]** unverified.
- **Four arXiv IDs that circulate in this problem space are mislabelled** and were corrected by opening
  both: LoRA-undoes-safety is **2310.20624** (not 2410.05295); Safe LoRA is **2405.16833** (not
  2405.14734); Inoculation Prompting and Representation Rerouting IDs were not established. See
  `top-models.md` §0.
- No number in these files is a measurement by this project. Every figure is quoted from its source's
  own abstract/card and marked with that source.
- Reference material gathered by the parallel research threads is preserved at
  `../research-tmp/local-slm-mcp-endpoint-defense.md` and
  `../research-tmp/small-scale-defensive-model-report.md`.
