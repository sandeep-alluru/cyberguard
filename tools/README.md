# Eval tooling — provenance, and how to run it

Every file in this directory was imported from the CyberGuard programme tree and scrubbed of
programme identifiers. The **logic was not changed**: the checks below assert the same things they
asserted in the tree, against the same documents.

## What is here

| tool | what it does | produces |
|---|---|---|
| `pubbench/run_pubbench.py` | runs the public benchmark suites (CTI-RCM, CTI-MCQ, CTI-VSP, CyberMetric-500, SecQA-v1) against an arm | scored results + raw responses |
| `pubbench/run_harmbench.py` | runs the HarmBench standard-test suite for an arm | generations for the official judge |
| `pubbench/run_frr.py` | runs the MITRE-FRR false-refusal suite for an arm | generations + the false-refusal rate |
| `pubbench/verify_eval.py` | re-checks a results file against the published expectations | pass/fail |
| `pubbench/output-contract/run_pubbench_contract.py` | runs the output-contract protocol (the model's own framing of its answer) | responses + the contract result |
| `eval-2026-10-23/e2_bar_sheet.py` | **generates** the bar sheet: the bars, their n, their baselines, the release table, and the per-arm tables | `docs/BAR-SHEET.md` |
| `eval-2026-10-23/e3_release_rule_check.py` | checks the release *rule* — that a public benchmark is release-decision evidence only when a bar names it | `results/.../e3-release-rule-check.json` |
| `eval-2026-10-23/e4_release_shape_check.py` | checks the release *shape* decision: the six artefacts, the pipeline order, and what the unresolved serving party blocks | `results/.../e4-release-shape-check.json` |
| `eval-2026-10-23/e7_release_candidates_check.py` | checks every status in the release table by re-reading each figure from the artefact it names | `results/.../e7-release-candidates-check.json` |
| `eval-2026-10-23/adapter_assessment.py` | assembles the v1/v2/v3 adapter assessment from the artefacts already on disk | `results/.../adapter-assessment.{json,md}` |
| `eval-2026-10-23/comparator_measurements.py` | the public comparator's re-measurement on the equal-terms surface | `results/.../comparator-measurements.{json,md}` |
| `eval-2026-10-23/d7_freeze_candidate.py` | freezes the corpus candidate and writes the Data Gate receipt | `qualification/data/v4/DATA-GATE.json` |
| `eval-2026-10-23/f8_decontaminate_mixture.py` | removes the rows that carry a held-out identity and rebuilds the corpus and mixture | the `f8clean` lineage + receipts |
| `eval-2026-10-23/f8c_trace_holdout_leak.py` | traces the held-out leak — the identity key, the containment, and the answer-content comparison | `results/.../f8c-holdout-leak-trace.json` |
| `eval-2026-10-23/f8b_public_benchmark_integrity.py` | checks the public benchmarks' integrity against the rebuilt mixture | `results/.../f8b-public-benchmark-integrity.json` |
| `eval-2026-10-23/safety/run_harmbench_local.py` | the HarmBench runner used for the local re-run | generations |
| `eval-2026-10-23/safety/run_frr_local.py` | the MITRE-FRR runner used for the local re-run | generations |
| `eval-2026-10-23/safety/hb_paired_all_arms.py` | pairs every arm's HarmBench outcome against the base, with an exact McNemar test | `results/.../harmbench-paired-all-arms.json` |
| `eval-2026-10-23/safety/frr_paired_all_arms.py` | pairs every arm's false-refusal outcome against the base | the paired FRR table |

## How to run them

Two categories, and the difference matters.

**The release checks (`e3`, `e4`, `e7`) resolve paths relative to the programme tree root** —
`ROOT = Path(__file__).resolve().parent.parent`, which is the tree root in the tree and `tools/`
here. They also assert on the *host state* of the tree: that the adapter directory is present,
that the merge and serve scripts exist, that the quantiser binary is built, that the GGUF
directory holds a specific number of files.

That host state is **deliberately not in this repository** — no adapters, no scripts, no GGUF.
The boundary that keeps it out is enforced mechanically by `verify_repo.py` at the repository
root: it scans every file for programme identifiers, credentials of any shape, and row-level data
files that are not on the published-benchmark allow-list, and exits non-zero if it finds one. So
run these against the programme tree, not against this checkout, and read their **receipts** here
as the results of those runs.

**The benchmark runners and the corpus instruments need the artefacts they measure**: the model,
the benchmark data, the corpora. They are the reproducible path, and they are here so that the
method is checkable — not so that a reader can re-run them without the hardware and the data.

**One tool in this repository runs anywhere, and it is the one that matters most to a reader:
`verify_repo.py` at the repository root.** It checks this tree against the boundary — programme
identifiers, credentials of any shape, and row-level data files that are not on the
published-benchmark allow-list — and exits non-zero if it finds one.

## The scrub, and what it changed in these files

75 of the 125 imported files were modified on import: programme host names, the account handle,
absolute programme paths, other programmes' names and other people's names were replaced with
generic descriptions. In this directory that means:

- `e4_release_shape_check.py` asserts `"<host-a>" in doc` where the tree's original asserted the
  host's literal name — **and the document it checks was scrubbed the same way**, so the check and
  the document still agree.
- The host-named local variables in that script (`host_rc`, `host_out`) and the receipt keys it
  writes (`host_ssh_returncode`, `host_ssh_output`) were renamed in **both** the generator and the
  receipt, so the pair stays consistent.

Every imported file is listed with its source path and source sha256, and section 3 of that
listing records the full replacement table.
