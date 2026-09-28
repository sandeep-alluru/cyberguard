# MIXTURE-V2 — the frozen v2 mixture ledger

**Purpose (SPEC-V2 §2 row 2):** every source that may enter v2, pinned by id/revision/licence, with its
admission verdict, its realised presentation count in the built arms, and its decontamination result.
**Single source of truth for numbers:** `v2/data/mixture/FACTS.json`.

**Built epoch: 81,282 rows per arm.** Refusal contribution: 9,584 slots
from 1,198 unique rows = 11.79% of the epoch.

| source | revision pinned | licence | role | admitted | realised presentations |
|---|---|---|---|---|---|
| `Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset` | escaped copy sha256 2b08b09c41da22c9...; rows 52,284 after safety audi | Apache-2.0 | train | **ADMIT** |  |
| `ethanolivertroy/nist-cybersecurity-training` | v1.1 (dataset card); 530,912 rows claimed | CC0-1.0 | train | **ADMIT** |  |
| `mitre-attack/attack-stix-data` | enterprise-attack.json master as fetched 2026-09-27 | MITRE Terms of Use (copy-notice required) | train | **ADMIT** |  |
| `nvd-cve-json-feeds` | NVD API 2.0, fetched 2026-09-27 (2000 of 398,563 CVEs sampled) | public domain (17 USC 105); CVE(R) notice required | train | **ADMIT** |  |
| `AUTHORED-refusal-retention-set` | authored 2026-09-27 by v2/build_refusal_set.py (seed 0); receipt besid | ours + curated public refusal data (per-source gate) | train | **ADMIT** |  |
| `AUTHORED-format-compliance-set` | authored 2026-09-27 by v2/build_format_set.py (seed 0); receipt beside | ours, from public rule schemas; SigmaHQ licence verified at U1 | train | **ADMIT** |  |
| `chairulridjal/arcspan-cyber-ner` | train split as fetched 2026-09-27; test split EXCLUDED (benchmark, nev | Apache-2.0 (API cardData.license) | train | **ADMIT** |  |
| `zefang-liu/secqa` | CC BY-NC-SA 4.0, ~242 rows — an EVALUATION set | CC BY-NC-SA 4.0 | eval | **REJECT** |  |
| `HuggingFaceH4/ultrachat_200k` | train_sft split; card last-modified 2024-10-16; MIT | MIT (verified via HF API cardData.license) | train | **ADMIT** |  |

**Realised presentation counts by source key** (from `FACTS.json`):

| key | presentations |
|---|---|
| `trendyol` | 50,672 |
| `nvd` | 14,847 |
| `refusal` | 9,584 |
| `format` | 2,600 |
| `attack` | 2,144 |
| `nist` | 835 |
| `replay` | 600 |

**Decontamination:** every candidate was measured against the 500-row held-out set by the
admission gate (13-gram Jaccard + verbatim-span containment, by-construction exclusion of the corpus's own
holdout rows). Full result: `v2/gate-report.json` — 8 admitted, 1 rejected (`zefang-liu/secqa`, an
evaluation set), 0 unmeasured. Residual overlap after exclusion: Trendyol 0.027; every other source 0.000.

**Weights** (realised by explicit duplication so the count is inspectable): refusal ×8, format ×2,
everything else ×1. **Control arm:** the refusal slots are occupied by matched non-refusal defensive Q&A
(1,198 distinct prompts, 1,021 distinct answers, 3.9 % length gap).

**Known absences, stated rather than implied:** extraction training supervision is absent (arcspan's
labels are not retrievable through the viewer API; it is retained as the G-D evaluation corpus, making G-D
a zero-shot test). General text-only replay is excluded at weight 0 (it contributes no supervised tokens
to an assistant-only objective); the conversational-replay slot carries 600 real turn pairs instead.

