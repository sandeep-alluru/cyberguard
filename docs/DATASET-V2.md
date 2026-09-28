# DATASET-V2 — candidate mixture plan (research output, NOT yet admitted)

**Provenance:** Grok research track (pod-ops researcher role), 2026-09-27 ~03:55 CDT, primary
sources (HF cards, ToU pages, papers); own web-search corroboration (Primus: arXiv 2502.11191,
EMNLP 2025, trend-cybertron/trendmicro-ailab HF org). **Nothing here is admitted**; admission
requires the entry gate at the bottom + Codex review (R-CA). Corrections to earlier LEDGER notes
are marked.

## Candidate table

Contamination scored against our **500-row held-out** (Trendyol-style "Describe an approach to …",
NIST CSF / ATT&CK mapping questions).

| Candidate | Exact id + revision | License | Rows | ~tokens | Train/eval | Contamination risk | Verdict |
|---|---|---|---|---|---|---|---|
| Primus-FineWeb | `trendmicro-ailab/Primus-FineWeb`, CC-MAIN-2024-10 cutoff | ODC-By + FineWeb + CC ToU | 1–10M docs | **2.57B** post-dedup | CPT | Medium (web security pages echo NIST/ATT&CK FAQ) | **ADMIT (primary domain CPT)**, decontam required |
| Primus-Seed (released slice) | `trendmicro-ailab/Primus-Seed` | ODC-By; contents incl. CC BY-SA wiki + ATT&CK ToU | 86,987 released | ~77.8M | CPT | HIGH (wiki+MITRE slices = holdout's subject) | company-website slice only; wiki slice rejected; MITRE verify |
| Primus-Instruct | `trendmicro-ailab/Primus-Instruct` | ODC-By (GPT-4o responses) | 835 | few M | SFT | Medium | too small; optional spice, verify |
| Primus-Reasoning | `trendmicro-ailab/Primus-Reasoning` | card ODC-By over **CTI-Bench CC BY-NC-SA** — conflict | ~4.9k distill | 2–4M | distill of an EVAL set | **CRITICAL** | **REJECT** (eval leakage + NC-SA provenance) |
| PolySec | **NOT FOUND** (targeted HF/GitHub/arXiv search) | — | — | — | — | — | **treat as phantom; do not admit** |
| SecQA | `zefang-liu/secqa` | CC BY-NC-SA 4.0 | **242** | tens of k | **EVAL** (correction: not CPT) | must-not-train | REJECT for training |
| NVD CVE JSON | official 2.0 feeds/API | **public domain** (17 U.S.C. §105); API disclaimer required; CVE® needs MITRE copyright line | ~2–3×10⁵ | 50–100M desc | CPT knowledge | Medium | **ADMIT** with attribution notices, decontam |
| MITRE ATT&CK STIX | `mitre-attack/attack-stix-data` | MITRE ToU (non-exclusive royalty-free **with copy notice**) | thousands of objects | low tens of M flattened | CPT knowledge | **HIGH** (holdout IS mapping) | ADMIT with notice; decontam vs holdout blurbs |
| Wikipedia slice | dumps / Primus wiki subset | **CC BY-SA 4.0** (+GFDL) | 6,636 (Primus) | 9.57M | CPT | High topical | **REJECT for published Apache adapter** (SA unsettled; conservative CC 2025 guidance would SA the model/outputs) |
| NIST CSRC set | `ethanolivertroy/nist-cybersecurity-training` v1.1 | **CC0 1.0** | 530,912 | ~70–80M | CPT | High topical (is the CSF source) | **ADMIT** (clean license; prefer over wiki), decontam |
| FineWeb-Edu (replay) | `HuggingFaceFW/fineweb-edu` **v1.4.0** | ODC-By + CC ToU | sample-10BT etc | 1.3T full; take 1–5B | general CPT replay | Low | **ADMIT** (best permissive general replay) |
| Dolci-Instruct-SFT | `allenai/Dolci-Instruct-SFT` main `bd3c8f3` | ODC-By + Ai2 RUG; **exclude** SA tool-use subset | 2,152,112 convos | GB-scale | SFT replay | Low | ADMIT 1–5 % replay slice; RUG verify |
| SlimPajama-627B | `cerebras/SlimPajama-627B` | Apache wrapper, per-subset licenses, 3.8 % wiki SA | 59k files | 627B | CPT | Low | REJECT as default replay (size, wiki SA, stale vs FineWeb-Edu) |
| Trendyol (v1, SFT core) | `Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset`, escaped sha256 `2b08b09c…` | **Apache-2.0** | 53,201 | ~37M resp | SFT | holdout stays out | ADMIT as replay core |
| Fenrir v2.1 | `AlicanKiraz0/Cybersecurity-Dataset-Fenrir-v2.1` | Apache-2.0, same author family | 99,870 | ~2× Trendyol? | SFT | **CRITICAL** — likely sibling/superset of Trendyol | **default REJECT until overlap vs our holdout measured** |
| threat-intelligence | `reloading0101/threat-intelligence-dataset` | CC BY 4.0 | 9,172+798+1,500 | 10–40M | SFT (CTI) | Medium; **best disclosed decontam methodology found** (97.6 % unique) | ADMIT as complementary after n-gram decontam |
| cyberusecase-v1.0 | `ronaldocloud/cyberusecase-v1.0` | CC BY 4.0 | 59,636 | — | SFT | Medium | verify (synthetic quality unknown) |
| oi-uae/cyber-security | `oi-uae/cyber-security` | **non-commercial**; contains Trendyol | 1.88M | ~650M | — | CRITICAL | **REJECT** (NC + Trendyol-in-mix) |
| SecKnowledge/CyberPal (IBM) | arXiv 2510.14113 | corpus not clearly published | — | — | — | — | watch; strong 4B precedent, nothing downloadable |
| CTI-Bench / SecBench / SecEval | `AI4Sec/cti-bench` etc | mostly CC BY-NC-SA | small | — | **EVAL** | training on them contaminates leaderboards + likely holdout | **REJECT for training**; eval-only |
| SecureCode v2 | `scthornton/securecode` | CC BY-NC-SA | 2,372 | small | SFT | Low | REJECT (NC) |

## Synthesis (strongest defensible v2 mix)

1. **Domain CPT:** Primus-FineWeb 2.57B + license-clean knowledge CPT (NIST CSRC CC0 + NVD PD +
   ATT&CK STIX with ToU notice).
2. **General replay:** FineWeb-Edu v1.4.0 subsample (1–5 B tokens) — the anti-collapse term.
3. **SFT:** Trendyol Apache replay core + small Dolci-Instruct slice (non-SA subsets) + optionally
   reloading0101 CTI (best disclosed dedup).

**Never admit:** Wikipedia SA slices, SecQA/CTI-Bench/SecEval/Primus-Reasoning (eval or NC-SA),
oi-uae, SlimPajama-as-default, PolySec-until-found, Fenrir-until-measured.

## Entry gate (before any v2 token is spent)

1. Freeze exact revisions (FineWeb-Edu `v1.4.0`, Primus cards as fetched 2026-09-27, Trendyol
   sha256 `2b08b09c…`) in the v2 mixture ledger.
2. **13-gram + embedding overlap of every candidate vs the 500-row holdout** (and vs CTI-Bench/
   SecQA as public evals); Fenrir↔Trendyol near-dup rate specifically.
3. Token counts under OUR tokenizer (unique, deduped), not card claims.
4. Post-CPT MMLU/IFEval delta to prove replay holds general capability.
5. Owner/legal sign-off: ODC-By *contents* question (FineWeb/CC), ATT&CK copy-notice placement,
   whether a published adapter is "Adapted Material" under CC BY-SA (unsettled law — the reason
   Wikipedia is excluded rather than argued).

This file is the U3 research deliverable; adoption decisions belong to the v2 plan under R-CA.
