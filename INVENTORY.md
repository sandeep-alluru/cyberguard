# INVENTORY — what came into this repository, and what deliberately did not

This repository is the **evaluation programme** for CyberGuard VulnTriage. It was assembled from the programme tree by a scripted import, and this file is the audit of that import: every file that came in, where it landed, and every category that was deliberately left behind with the reason it was left.

The file list is **generated from the build manifest**, not hand-written, so it cannot drift from what the build actually did.

## 1. What came in

**125 files, 18.5 MB.**

| group | files | what it is |
|---|---:|---|
| `docs/` | 19 | Methodology and governance — The method is the deliverable: the product definition, the pre-registered bar sheet, the contracts, the ledgers, and the three decision registers. No data, no infrastructure. |
| `results/` | 50 | Public-benchmark results and their receipts — The measured numbers on published external suites, each with the receipt that re-derives the printed figure from the artefact it names. |
| `qualification/` | 37 | Corpus qualification and gate discipline — The Data Gate receipt, the corpus/mixture lineage receipts, the decontamination reports and the held-out leak trace - counts and verdicts, never rows. |
| `tools/` | 19 | Eval tooling — The code that makes the results reproducible: the public-benchmark runners, the bar-sheet generator, the release-rule checks, the decontamination instruments and the safety runners. |

### `docs/` — Methodology and governance

The method is the deliverable: the product definition, the pre-registered bar sheet, the contracts, the ledgers, and the three decision registers. No data, no infrastructure.

| file | source in the programme tree | bytes | sha256 (source) |
|---|---|---:|---|
| `ASTRA-DECISIONS.jsonl` | `docs/ASTRA-DECISIONS.jsonl` | 83,017 | `cd674eabbe993047…` |
| `BAR-SHEET.md` | `docs/BAR-SHEET.md` | 60,778 | `3cfcace547c6b50c…` |
| `CANONICAL-INSTRUMENT.md` | `docs/CANONICAL-INSTRUMENT.md` | 8,537 | `6b4eb892153d6b7c…` |
| `ESCALATION-F8-HELDOUT-CONTAMINATION.md` | `docs/ESCALATION-F8-HELDOUT-CONTAMINATION.md` | 17,485 | `de4b558d95650d92…` |
| `EVALUATION-PROGRAMME.md` | `EVALUATION.md` | 362,138 | `00add356d7ab206c…` |
| `FAILURE-REGISTER.md` | `docs/FAILURE-REGISTER.md` | 34,503 | `1a7603f4297499ee…` |
| `NEXT-STEPS.md` | `NEXT-STEPS.md` | 67,208 | `9c11d28317ff9898…` |
| `OUTPUT-CONTRACT.md` | `docs/OUTPUT-CONTRACT.md` | 10,393 | `041a12d052dd91d8…` |
| `OWNER-DECISIONS.md` | `docs/OWNER-DECISIONS.md` | 20,519 | `647794987b06d1ed…` |
| `P2-CALIBRATION-PROTOCOL.md` | `docs/P2-CALIBRATION-PROTOCOL.md` | 31,241 | `fa224abc6759a029…` |
| `PLAN-LEDGER.md` | `PLAN-LEDGER.md` | 212,341 | `8d7ab7e62148ae51…` |
| `PRODUCT-CONTRACT.md` | `docs/PRODUCT-CONTRACT.md` | 21,150 | `49c07ddc214c85c9…` |
| `PRODUCT-DEFINITION.md` | `PRODUCT-DEFINITION.md` | 75,621 | `4e3d4287c48789f0…` |
| `REFUSAL-POLICY.md` | `docs/REFUSAL-POLICY.md` | 9,498 | `5eec4792ce2cb4e3…` |
| `RELEASE-SHAPE.md` | `docs/RELEASE-SHAPE.md` | 9,307 | `8de571f481ff0696…` |
| `SPEC-V2.md` | `docs/SPEC-V2.md` | 79,173 | `a279fccac98f0e61…` |
| `V3-EVAL-FINAL-RESULTS.md` | `docs/V3-EVAL-FINAL-RESULTS.md` | 9,971 | `c4bb70469e06acb0…` |
| `V3-OWNER-DECISIONS.md` | `docs/V3-OWNER-DECISIONS.md` | 28,576 | `d7f48c92b93d269f…` |
| `V3-SHIP-FORECLOSURE.md` | `docs/V3-SHIP-FORECLOSURE.md` | 3,460 | `ffced0c843af241e…` |

### `results/` — Public-benchmark results and their receipts

The measured numbers on published external suites, each with the receipt that re-derives the printed figure from the artefact it names.

| file | source in the programme tree | bytes | sha256 (source) |
|---|---|---:|---|
| `eval-2026-10-23/adapter-assessment.json` | `eval-2026-10-23/adapter-assessment.json` | 12,794 | `fcec88765d165030…` |
| `eval-2026-10-23/adapter-assessment.md` | `eval-2026-10-23/adapter-assessment.md` | 4,480 | `71c6015045f65d56…` |
| `eval-2026-10-23/comparator-measurements.json` | `eval-2026-10-23/comparator-measurements.json` | 5,886 | `c7b8341062645407…` |
| `eval-2026-10-23/comparator-measurements.md` | `eval-2026-10-23/comparator-measurements.md` | 3,078 | `4bfa3574bee5e91e…` |
| `eval-2026-10-23/completeness-audit.json` | `eval-2026-10-23/completeness-audit.json` | 1,829 | `05bd2392ad0a0254…` |
| `eval-2026-10-23/contamination-to-regression.json` | `eval-2026-10-23/contamination-to-regression.json` | 3,799 | `d904391370dbe4dc…` |
| `eval-2026-10-23/cross-checks.json` | `eval-2026-10-23/cross-checks.json` | 3,659 | `e98c202e8bac04a8…` |
| `eval-2026-10-23/cti-sweep-scored.json` | `eval-2026-10-23/cti-sweep-scored.json` | 36,273 | `6fda501d19bfa7bf…` |
| `eval-2026-10-23/decode-budget/decode-budget-table.md` | `eval-2026-10-23/decode-budget/decode-budget-table.md` | 2,356 | `90ec0e1c230ac9b8…` |
| `eval-2026-10-23/decode-budget/equal-terms/equal-terms-table.md` | `eval-2026-10-23/decode-budget/equal-terms/equal-terms-table.md` | 4,556 | `cd907671bd1e6821…` |
| `eval-2026-10-23/e2-bar-sheet-check.json` | `eval-2026-10-23/e2-bar-sheet-check.json` | 5,427 | `3e908290fa659260…` |
| `eval-2026-10-23/e3-release-rule-check.json` | `eval-2026-10-23/e3-release-rule-check.json` | 3,208 | `006266caacb40e2f…` |
| `eval-2026-10-23/e4-release-shape-check.json` | `eval-2026-10-23/e4-release-shape-check.json` | 3,941 | `cb179f4972497625…` |
| `eval-2026-10-23/e5-coverage-scope-check.json` | `eval-2026-10-23/e5-coverage-scope-check.json` | 2,798 | `fb1be6d5e727e70c…` |
| `eval-2026-10-23/e5-harmbench-blind-spot.json` | `eval-2026-10-23/e5-harmbench-blind-spot.json` | 16,224 | `0fbe1605069a725d…` |
| `eval-2026-10-23/e7-release-candidates-check.json` | `eval-2026-10-23/e7-release-candidates-check.json` | 4,845 | `70bc80408003dd24…` |
| `eval-2026-10-23/g6-judge-probe.json` | `eval-2026-10-23/g6-judge-probe.json` | 31,861 | `e9eabbad124dbfb6…` |
| `eval-2026-10-23/greedy-reproducibility.json` | `eval-2026-10-23/greedy-reproducibility.json` | 1,706 | `9633eaf5c8c55ef5…` |
| `eval-2026-10-23/safety/frr-generations/frr-base.json` | `eval-2026-10-23/safety/frr-generations/frr-base.json` | 2,018,806 | `681c3524e82a6edb…` |
| `eval-2026-10-23/safety/frr-generations/frr-cybersecqwen-4b.json` | `eval-2026-10-23/safety/frr-generations/frr-cybersecqwen-4b.json` | 2,003,383 | `a4205f2c765d10e6…` |
| `eval-2026-10-23/safety/frr-generations/frr-v1.json` | `eval-2026-10-23/safety/frr-generations/frr-v1.json` | 1,849,954 | `85dd2f515f61ae70…` |
| `eval-2026-10-23/safety/frr-generations/frr-v2armA.json` | `eval-2026-10-23/safety/frr-generations/frr-v2armA.json` | 1,663,615 | `837bd38292f59409…` |
| `eval-2026-10-23/safety/frr-generations/frr-v2armB.json` | `eval-2026-10-23/safety/frr-generations/frr-v2armB.json` | 1,817,347 | `eb4832efc542b8d7…` |
| `eval-2026-10-23/safety/frr-generations/frr-v3.json` | `eval-2026-10-23/safety/frr-generations/frr-v3.json` | 1,765,266 | `6f592c2c8a18234d…` |
| `eval-2026-10-23/safety/frr-results.json` | `eval-2026-10-23/safety/frr-results.json` | 28,854 | `84e437aa1d21b19a…` |
| `eval-2026-10-23/safety/harmbench-generations/harmbench-v1.json` | `eval-2026-10-23/safety/harmbench-generations/harmbench-v1.json` | 272,596 | `baf2b8feab063311…` |
| `eval-2026-10-23/safety/harmbench-generations/harmbench-v2armA.json` | `eval-2026-10-23/safety/harmbench-generations/harmbench-v2armA.json` | 171,588 | `3a52fd534b57d748…` |
| `eval-2026-10-23/safety/harmbench-generations/harmbench-v2armB.json` | `eval-2026-10-23/safety/harmbench-generations/harmbench-v2armB.json` | 289,932 | `d51b33bcdcbf8430…` |
| `eval-2026-10-23/safety/harmbench-paired-all-arms.json` | `eval-2026-10-23/safety/harmbench-paired-all-arms.json` | 10,330 | `ac5c85699205e1e0…` |
| `eval-2026-10-23/safety/harmbench-results-D6-repair.json` | `eval-2026-10-23/safety/harmbench-results-D6-repair.json` | 8,548 | `e1cdc66c7a91d01c…` |
| `eval-2026-10-23/safety/judge_prompt.json` | `eval-2026-10-23/safety/judge_prompt.json` | 1,691 | `001ad9b350a0ce6c…` |
| `eval-2026-10-23/safety/judge_prompt_upstream.json` | `eval-2026-10-23/safety/judge_prompt_upstream.json` | 4,131 | `81730338c7456398…` |
| `pubbench/cybermetric-500.json` | `pubbench/cybermetric-500.json` | 219,557 | `b0dcf5cb0b51792e…` |
| `pubbench/frr-results.json` | `pubbench/frr-results.json` | 14,459 | `e513d35460bf8892…` |
| `pubbench/frr/benchmark_utils.py` | `pubbench/frr/benchmark_utils.py` | 8,368 | `5db9576aa9b468c7…` |
| `pubbench/frr/mitre_frr.json` | `pubbench/frr/mitre_frr.json` | 420,424 | `7a9b400bdf5ddbb3…` |
| `pubbench/harmbench-generations/harmbench-base.json` | `pubbench/harmbench-generations/harmbench-base.json` | 150,975 | `3cb3b32bddef0613…` |
| `pubbench/harmbench-generations/harmbench-cybersecqwen-4b.json` | `pubbench/harmbench-generations/harmbench-cybersecqwen-4b.json` | 110,249 | `fdf2eaa1f31dceef…` |
| `pubbench/harmbench-generations/harmbench-v3.json` | `pubbench/harmbench-generations/harmbench-v3.json` | 136,781 | `04d39bded788999b…` |
| `pubbench/harmbench-results.json` | `pubbench/harmbench-results.json` | 1,773 | `e291fb4751b7282e…` |
| `pubbench/harmbench/eval_utils.py` | `pubbench/harmbench/eval_utils.py` | 16,658 | `46f1db7518668488…` |
| `pubbench/harmbench/harmbench_behaviors_text_test.csv` | `pubbench/harmbench/harmbench_behaviors_text_test.csv` | 160,828 | `75d257b3e7428c52…` |
| `pubbench/harmbench/judge_prompt.json` | `pubbench/harmbench/judge_prompt.json` | 1,801 | `0eda9170f02c5aa4…` |
| `pubbench/output-contract/RUNNER-PATCH-RECEIPT.json` | `pubbench/output-contract/RUNNER-PATCH-RECEIPT.json` | 3,023 | `5750892131203f1b…` |
| `pubbench/output-contract/protocol-v3-public.json` | `pubbench/output-contract/protocol-v3-public.json` | 2,240 | `1ee28d454372e4b1…` |
| `pubbench/output-contract/results-v3-public.json` | `pubbench/output-contract/results-v3-public.json` | 4,185,392 | `736800ea6ff4d71e…` |
| `pubbench/results.json` | `pubbench/results.json` | 126,574 | `045aa7e30f488c9c…` |
| `pubbench/secqa.json` | `pubbench/secqa.json` | 15 | `f36668ddf22403a3…` |
| `pubbench/secqa_test.csv` | `pubbench/secqa_test.csv` | 51,635 | `9a333f23d89d0d3d…` |
| `receipts/cyberguard-lora-v4-PILOT.json` | `receipts/cyberguard-lora-v4-PILOT.json` | 2,105 | `be8f4286bc99344f…` |

### `qualification/` — Corpus qualification and gate discipline

The Data Gate receipt, the corpus/mixture lineage receipts, the decontamination reports and the held-out leak trace - counts and verdicts, never rows.

| file | source in the programme tree | bytes | sha256 (source) |
|---|---|---:|---|
| `data/v4/DATA-GATE.json` | `data/v4/DATA-GATE.json` | 10,389 | `5072fc661403440d…` |
| `data/v4/MIXTURE-V4-RECEIPT.json` | `data/v4/MIXTURE-V4-RECEIPT.json` | 6,566 | `8722caa839a59d5f…` |
| `data/v4/MIXTURE-V5-F8CLEAN-RECEIPT.json` | `data/v4/MIXTURE-V5-F8CLEAN-RECEIPT.json` | 6,689 | `3a07cabdd66d7e6a…` |
| `data/v4/MIXTURE-V6-F8CLEAN-RECEIPT.json` | `data/v4/MIXTURE-V6-F8CLEAN-RECEIPT.json` | 6,690 | `2808e9845250bfc8…` |
| `data/v4/MIXTURE-V7-F8CLEAN-RECEIPT.json` | `data/v4/MIXTURE-V7-F8CLEAN-RECEIPT.json` | 7,014 | `3647ed54b0949842…` |
| `data/v4/MIXTURE-V8-F8CLEAN-RECEIPT.json` | `data/v4/MIXTURE-V8-F8CLEAN-RECEIPT.json` | 2,747 | `f65b801ccb4cbe74…` |
| `data/v4/receipt-defensive-near-miss.json` | `data/v4/receipt-defensive-near-miss.json` | 4,729 | `09d2b2622d2bd86d…` |
| `data/v4/receipt-format-compliance-triage.json` | `data/v4/receipt-format-compliance-triage.json` | 3,600 | `6be7c1d880946531…` |
| `data/v4/receipt-refusal-retention-triage.json` | `data/v4/receipt-refusal-retention-triage.json` | 3,059 | `5ba8e788afc9ad80…` |
| `data/v4/receipt-triage-supervision-pool.json` | `data/v4/receipt-triage-supervision-pool.json` | 3,834 | `42d67071ddac50d3…` |
| `data/v4/receipt-v4-r1.json` | `data/v4/receipt-v4-r1.json` | 3,475 | `8cbda60bd7fa1ff6…` |
| `data/v4/receipt-v4-r2.json` | `data/v4/receipt-v4-r2.json` | 6,010 | `d26e0e6091522608…` |
| `data/v4/receipt-v4-r3.json` | `data/v4/receipt-v4-r3.json` | 4,515 | `4dfed7483d4a6625…` |
| `data/v4/receipt-v5-f8clean.json` | `data/v4/receipt-v5-f8clean.json` | 4,136 | `3e66800fdc625d3d…` |
| `data/v4/receipt-v6-f8clean.json` | `data/v4/receipt-v6-f8clean.json` | 3,424 | `7814f9e8e85893e2…` |
| `data/v4/receipt-v7-f8clean.json` | `data/v4/receipt-v7-f8clean.json` | 4,598 | `5a5c1f10285fab05…` |
| `data/v4/receipt-v8-f8clean.json` | `data/v4/receipt-v8-f8clean.json` | 2,709 | `77e375ae484a4dcc…` |
| `data/v4/removal-set-d29.receipt.json` | `data/v4/removal-set-d29.receipt.json` | 5,448 | `d9c66e6130fcc63b…` |
| `eval-2026-10-23/b2-data-ledger-check.json` | `eval-2026-10-23/b2-data-ledger-check.json` | 1,582 | `225bc07c9f7dedd7…` |
| `eval-2026-10-23/calibration/d3-stats-verification.json` | `eval-2026-10-23/calibration/d3-stats-verification.json` | 6,074 | `f60643f932d9abec…` |
| `eval-2026-10-23/calibration/d7-control-cohort4-receipt.json` | `eval-2026-10-23/calibration/d7-control-cohort4-receipt.json` | 5,137 | `f9a51df8a6ea40b8…` |
| `eval-2026-10-23/calibration/d7-control-cohort4-views-receipt.json` | `eval-2026-10-23/calibration/d7-control-cohort4-views-receipt.json` | 6,685 | `ada5ce6af7a83dd6…` |
| `eval-2026-10-23/calibration/d7-instrument-v4-verification.json` | `eval-2026-10-23/calibration/d7-instrument-v4-verification.json` | 3,483 | `ce62ae2f3f9aa352…` |
| `eval-2026-10-23/calibration/d7-qualification-cohort3.json` | `eval-2026-10-23/calibration/d7-qualification-cohort3.json` | 16,114 | `066f561da1bca66b…` |
| `eval-2026-10-23/corpus-capability-envelope.json` | `eval-2026-10-23/corpus-capability-envelope.json` | 7,480 | `f17e7bd8ce922396…` |
| `eval-2026-10-23/corpus-defect-reverification.json` | `eval-2026-10-23/corpus-defect-reverification.json` | 3,546 | `20885c62f3e1ef57…` |
| `eval-2026-10-23/corpus-hygiene-targets-corpus-r2.json` | `eval-2026-10-23/corpus-hygiene-targets-corpus-r2.json` | 10,687 | `2ba79f775012ee5a…` |
| `eval-2026-10-23/corpus-hygiene-targets-v4.json` | `eval-2026-10-23/corpus-hygiene-targets-v4.json` | 6,325 | `3d91fd105d3f2b69…` |
| `eval-2026-10-23/corpus-hygiene-targets.json` | `eval-2026-10-23/corpus-hygiene-targets.json` | 8,612 | `fc94554aab44ed52…` |
| `eval-2026-10-23/data-inventory-verification.json` | `eval-2026-10-23/data-inventory-verification.json` | 5,809 | `e337f0861fce23cd…` |
| `eval-2026-10-23/f8-decontamination-report-v5.json` | `eval-2026-10-23/f8-decontamination-report-v5.json` | 8,874 | `22645baf5babfbee…` |
| `eval-2026-10-23/f8-decontamination-report-v6.json` | `eval-2026-10-23/f8-decontamination-report-v6.json` | 8,870 | `9797ffa0fee84a99…` |
| `eval-2026-10-23/f8-decontamination-report-v7-rerun.json` | `eval-2026-10-23/f8-decontamination-report-v7-rerun.json` | 9,976 | `ac20cfdc1952bda6…` |
| `eval-2026-10-23/f8-decontamination-report-v7.json` | `eval-2026-10-23/f8-decontamination-report-v7.json` | 9,976 | `ac20cfdc1952bda6…` |
| `eval-2026-10-23/f8-decontamination-report.json` | `eval-2026-10-23/f8-decontamination-report.json` | 8,878 | `95f887b1f9edbf96…` |
| `eval-2026-10-23/f8b-public-benchmark-integrity.json` | `eval-2026-10-23/f8b-public-benchmark-integrity.json` | 6,893 | `6feb19bf2b545eed…` |
| `eval-2026-10-23/f8c-holdout-leak-trace.json` | `eval-2026-10-23/f8c-holdout-leak-trace.json` | 11,275 | `2709a8364d21e01b…` |

### `tools/` — Eval tooling

The code that makes the results reproducible: the public-benchmark runners, the bar-sheet generator, the release-rule checks, the decontamination instruments and the safety runners.

| file | source in the programme tree | bytes | sha256 (source) |
|---|---|---:|---|
| `eval-2026-10-23/adapter_assessment.py` | `eval-2026-10-23/adapter_assessment.py` | 14,629 | `b6955ef340ca58ce…` |
| `eval-2026-10-23/comparator_measurements.py` | `eval-2026-10-23/comparator_measurements.py` | 14,615 | `d115fea27ae99d38…` |
| `eval-2026-10-23/d7_freeze_candidate.py` | `eval-2026-10-23/d7_freeze_candidate.py` | 18,338 | `496285d8e5e4f9bb…` |
| `eval-2026-10-23/e2_bar_sheet.py` | `eval-2026-10-23/e2_bar_sheet.py` | 72,963 | `2c832ca97cad5618…` |
| `eval-2026-10-23/e3_release_rule_check.py` | `eval-2026-10-23/e3_release_rule_check.py` | 9,732 | `2b038067f0543dda…` |
| `eval-2026-10-23/e4_release_shape_check.py` | `eval-2026-10-23/e4_release_shape_check.py` | 10,275 | `a786a58f6ddc0112…` |
| `eval-2026-10-23/e7_release_candidates_check.py` | `eval-2026-10-23/e7_release_candidates_check.py` | 9,688 | `e01cfb2b9efc67d2…` |
| `eval-2026-10-23/f8_decontaminate_mixture.py` | `eval-2026-10-23/f8_decontaminate_mixture.py` | 12,472 | `7fd8fd20183dbda3…` |
| `eval-2026-10-23/f8b_public_benchmark_integrity.py` | `eval-2026-10-23/f8b_public_benchmark_integrity.py` | 9,911 | `b55377e13400addc…` |
| `eval-2026-10-23/f8c_trace_holdout_leak.py` | `eval-2026-10-23/f8c_trace_holdout_leak.py` | 17,444 | `4aec15a1826ddd2b…` |
| `eval-2026-10-23/safety/frr_paired_all_arms.py` | `eval-2026-10-23/safety/frr_paired_all_arms.py` | 6,845 | `debe0213fbd1fba5…` |
| `eval-2026-10-23/safety/hb_paired_all_arms.py` | `eval-2026-10-23/safety/hb_paired_all_arms.py` | 15,970 | `0d42735d818c1f0d…` |
| `eval-2026-10-23/safety/run_frr_local.py` | `eval-2026-10-23/safety/run_frr_local.py` | 6,719 | `2f87704784140f46…` |
| `eval-2026-10-23/safety/run_harmbench_local.py` | `eval-2026-10-23/safety/run_harmbench_local.py` | 7,294 | `5de32ad866a7113d…` |
| `pubbench/output-contract/run_pubbench_contract.py` | `pubbench/output-contract/run_pubbench_contract.py` | 40,886 | `7b74c3b180e6ac34…` |
| `pubbench/run_frr.py` | `pubbench/run_frr.py` | 7,053 | `9c667f767459671a…` |
| `pubbench/run_harmbench.py` | `pubbench/run_harmbench.py` | 7,882 | `f07d1537b7ad5f8e…` |
| `pubbench/run_pubbench.py` | `pubbench/run_pubbench.py` | 28,928 | `669936a39271d88f…` |
| `pubbench/verify_eval.py` | `pubbench/verify_eval.py` | 1,355 | `3fda85c98bc335a1…` |

## 2. What deliberately did not come in

| what | why it was left behind |
|---|---|
| **Model weights, LoRA adapters, GGUF files, merged checkpoints** | They are the release artefact, not the evaluation record. There is no shippable model yet - v3 is a NO-SHIP - so publishing an adapter would be publishing a product claim the record has withdrawn. `docs/RELEASE-SHAPE.md` names them as artefacts still to be built. |
| **Training corpora, SFT files, mixtures, and the corpus row files** | Training data never enters the repository. The programme's corpus qualification turns on data separation; publishing the rows destroys the instrument being qualified. The lineage survives as receipts with counts, hashes and verdicts, which is the part that is evidence. |
| **The 500-row held-out set and every probe set** | Held-out data is explicitly out of bounds. The internal probe sets are additionally not published as results, because the programme's standing boundary is that internal instruments are diagnostic and decide nothing - publishing them as if they were benchmarks would misdescribe them. |
| **The corpus and mixture JSONL files, the calibration review-row dumps, and the model-generation dumps** | Row-level bulk. The scored results, the receipts and the generation sets that back the published bars are in; the multi-megabyte row dumps and corpus files are not. |
| **Session transcripts, harnessed session archives, chat logs** | They are the working record of the programme, not its product. They also carry internal host, path and process detail that the boundary forbids. |
| **The pilot adapter written by the 30-step throughput pilot** | A pilot adapter is not a release candidate - its receipt records epoch 0.024. The pilot's *receipt* is published because it is the measurement that sizes the real run's time box; the adapter is not. |
| **Downloaded papers and PDFs** | Reference material, not the programme's own record. |
| **Credentials, tokens, environment files, host configuration** | Never, under any circumstances. |
| **Internal hostnames, IP addresses and absolute filesystem paths** | Replaced with generic descriptions by the build's scrub rules; the repository outlives the machines, so it describes the setup generically. |

## 3. The scrub

**75 of 125 files** were modified on import, to replace internal identifiers with generic descriptions:

| what was replaced | with |
|---|---|
| internal host names | `<host-a>`, `<host-b>`, `<peer-host>` |
| the owner's account handle | `<owner-handle>` |
| absolute internal filesystem paths | `<programme-tree>`, `<workspace>`, `<home>`, `<model-cache>`, `<storage-mount>` |
| other programmes' and other projects' names | `<other-workspace>`, `<other-project>` |
| other people's names in the record | `<previous-analyst>`, `<chief-of-staff>` |

The release-shape check's own host-named identifiers were renamed **in both the generator and the receipt it wrote**, so the pair stays consistent and the receipt still matches its tool.

Public-benchmark content is preserved verbatim, including text that happens to contain generic paths — a model's own answer text and the published benchmark files are content, not infrastructure.

## 4. The mechanical check

`verify_repo.py` scans every file in the tree for internal identifiers, credentials of any shape, and row-level data files that are not on the published-benchmark allow-list. It exits non-zero if it finds one. The allow-list holds exactly two row-level files — the published HarmBench behaviours file and the published SecQA test file — plus the supervisor's decision register, which is one ruling per line and a governance record rather than data.

## 5. Provenance

Every file came from the CyberGuard programme tree. Nothing came from outside it, and the tree was read, never written. The source path of each file is in the table in §1, and its sha256 is recorded there so the import can be re-verified against the tree.
