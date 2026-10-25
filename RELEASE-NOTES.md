# Release notes

## v0.1.0 — 2026-10-25 · the measurement programme

**What this release is.** The measurement programme for CyberGuard: the product
definition, the pre-registered thresholds, the public-benchmark results with their receipts, the
corpus qualification and gate discipline, and the tooling that produces all of it.

### What shipped

| | |
|---|---|
| **The results table** | Four models on one scoreboard — the untrained base, CyberSecQwen-4B, Cisco Foundation-Sec-8B-Instruct and the arm of record. Every figure labelled published or first-party, every figure read from a receipt in this repository. |
| **The pre-registered thresholds** | Eight instruments with their population, their baseline, their threshold and their status, plus the per-arm measurement tables. |
| **The contamination trace** | 604 rows carrying a held-out identity inside a training file, covering 499 of the 500 held-out rows, with byte-identical prompts — published, because a check that catches something is part of the record. |
| **The receipts** | Every published figure names the artefact it was read from, and the artefact is in this repository. |
| **Three checkers** | `verify_repo.py` checks the tree against its publication boundary; `tools/language_audit.py` checks the public files for banned vocabulary; `tools/reproduce_headline.py` rebuilds the headline table from the receipts and cross-checks the two. All three run on a fresh clone with the standard library alone. |
| **The media** | The wordmark, a social preview, the hero poster, two comparison charts with the threshold marked, poster thumbnails, and a 45 s teaser cut from the 19 min 5 s walkthrough. |

### The numbers

| measure | value | source |
|---|---|---|
| CTI-RCM, the arm of record | 0.6360 | first-party, measured here |
| CTI-RCM, the comparator | 0.6780 | first-party, measured here; 0.6664 published by its authors |
| CTI-VSP mean absolute deviation | comparator 1.223, base 1.32 at 2,048 tokens | first-party, with the benchmark's own scorer |
| MITRE false-refusal rate | 29.07 % against a threshold of 5.13 % | first-party, 218/750 |
| HarmBench harmful completions | 0 of 159, against a threshold of 1 of 159 | first-party |
| CyberMetric-500 | 0.8000, the best of the four | first-party |
| SecQA | 0.9364, the best of the four | first-party |

### What's next

The confirmation draw is the next measurement: it produces the three registered corpus limits —
unsafe, off-topic and shallow — and re-issues the gate. The next arm then trains from the base
checkpoint with the refusal weight as the single controlled variable, is measured against the same
thresholds on the same frozen surface, and the release pipeline builds the artefacts from its
result.

### How to check this release

```bash
git clone https://github.com/sandeep-alluru/cyberguard.git && cd cyberguard
python3 verify_repo.py
python3 tools/language_audit.py
python3 tools/reproduce_headline.py
```

### Assets

| asset | sha256 |
|---|---|
| `assets/logo.svg` | see `assets/CHECKSUMS.sha256` |
| `assets/logo.png` | see `assets/CHECKSUMS.sha256` |
| `assets/social-preview.png` | see `assets/CHECKSUMS.sha256` |
| `assets/hero-poster.png` | see `assets/CHECKSUMS.sha256` |
| `assets/chart-cti-rcm.png` | see `assets/CHECKSUMS.sha256` |
| `assets/chart-frr.png` | see `assets/CHECKSUMS.sha256` |
| `assets/teaser.mp4` | see `assets/CHECKSUMS.sha256` |

Every asset's sha256 is listed in `assets/CHECKSUMS.sha256`, and that file is checked against itself
by `verify_repo.py`.

---

*The programme's own working papers — the decision trail, the evaluation charter and the import
inventory — are held outside this tree and are not part of the public surface.*
