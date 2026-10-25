# CANONICAL-INSTRUMENT — which instrument governs, and which is superseded

**Ruling date:** 2026-10-23
**Ledger item:** `PLAN-LEDGER.md` **A-4** (from `EVALUATION.md` §7 step **P0-4**)
**Authority:** owner approval `OWNER-D1` (`docs/OWNER-DECISIONS.md`, 2026-10-23) — *"Make your own decisions"* — acting inside the standing rule that a metric may not be *changed* by the worker. **Nothing is changed by this ruling.** Two instruments already existed and disagreed; this ruling names which one governs and marks the other superseded. The strict protocol was already the project's declared decision surface (`ASTRA` spec §3, quoted by the frozen runner itself), so this ruling *declares* the existing state rather than selecting a new one.
**Answers:** `EVALUATION.md` §8 owner question 7 — *"Should the Sept 2026 CyberMetric base number (88.6 %) be treated as superseded rather than merely different?"* → **superseded.**

---

## 1. The canonical instrument

**ONE instrument: the frozen October protocol.**

| | |
|---|---|
| **file** | `pubbench/run_pubbench.py` |
| **sha256** | `669936a39271d88f27b6b863de2120428bfa2b03908a29ce7d6a97708640d02d` |
| **executed on this host as** | `eval-2026-10-23/base/run_pubbench_local.py`, sha256 `8341be17963dfc15f1b8fd4c05f9fea12cee6077dbd2055a36dd85f3f67f310a` |
| **why a copy** | the frozen runner hard-codes `<peer-home>/...` paths. The copy changes **only filesystem paths**. The complete diff is recorded at `eval-2026-10-23/DIFF-vs-frozen-runner.txt`, and **no decode, parse, metric, population, batch or prompt parameter is changed**. `pubbench/run_pubbench.py` itself has not been modified. |

## 2. The canonical metric

**ONE metric, named by the instrument itself:**

> **`strict format-constrained accuracy, local protocol`**

(`pubbench/run_pubbench.py:45`, `METRIC_NAME`.)

It is not the upstream authors' `strict_acc`; **parser equivalence with the authors' scorer has not been established**, and the runner says so in its own output. That caveat travels with every number produced under this metric.

The metric resolves differently per benchmark, and that difference is part of the metric:

| benchmark | parse rule | code |
|---|---|---|
| **CyberMetric-500**, **SecQA-v1-test** | the **entire** trimmed response must be exactly `A`/`B`/`C`/`D` | `parse_whole_mcq` |
| **CTI-MCQ** | the **last** non-empty trimmed line must be exactly `A`/`B`/`C`/`D` | `parse_last_line` |
| **CTI-RCM** | the **last** non-empty trimmed line must match `CWE-[0-9]{1,5}` | `parse_last_line` |

First-match extraction is **wrong** and is not used — the supervisor reproduced `A common weakness is present.\nB` scoring as `A` instead of `B`.

### The protocol, in full

Greedy (`do_sample=False`, `num_beams=1`), **one** trial, **512** new tokens, **batch 8**, **left padding with an explicit attention mask**, **BF16**, **no quantisation**, **PEFT adapter unmerged**, own tokenizer and chat template, **one user message, no system message, zero demonstrations, no truncation**, max prompt 3,584 tokens inside a 4,096 envelope.

---

## 3. The superseded instrument

**Superseded for all purposes — not deleted.**

| | |
|---|---|
| **file** | `git show 49f2057:pubbench/run_pubbench.py` (the 2026-09-29 runner) |
| **sha256** | `ef21cbd1f782bd081f0e23aa98fc150d2ea2ffa3b5c068ea30aa5fcca97b7133` |
| **its output** | `pubbench/results.json` (2026-09-29 17:12) |

### The five parameter differences

| # | parameter | September (superseded) | October (canonical) |
|---:|---|---|---|
| 1 | **decode budget** | `max_new_tokens=10` | `max_new_tokens=512` |
| 2 | **parse rule** | `LETTER = re.compile(r"\b([ABCD])\b")`, `LETTER.search(gen.upper())` — a **lenient first-letter match anywhere** in the response | whole-response (MCQ) / last-line (CTI) — **strict** |
| 3 | **precision** | `torch.float16` | `torch.bfloat16` |
| 4 | **adapter** | `merge_and_unload()` — **merged** into the base weights | PEFT adapter **unmerged** |
| 5 | **batch** | 1 | 8 |

**Difference 2 is the one that carries the 41-point gap.** The other four are protocol hygiene; number 2 is a different *measurement*.

### Why the gap is an artefact and not a finding

The same base model, on the same CyberMetric-500 items:

| instrument | base | arm B / v3 |
|---|---:|---:|
| September (superseded) | **88.6 %** (443/500) | **89.4 %** (447/500) |
| October (canonical) | **47.2 %** | **80.6 %** |
| **apparent "improvement"** | — | **+33.4 pp** vs **+0.8 pp** |

Under the September instrument the adapter appears to be worth **+0.8 pp**. Under the canonical instrument it appears to be worth **+33.4 pp**. **Both are true measurements of different instruments**, and the 41-point swing on the base model is produced entirely by the parse rule: the base model answers `"B. IP"`, which the September regex scores as `B` and the canonical parser scores as unparseable.

`docs/VERSION-COMPARISON.md:69-71` warned of exactly this, and the project suffered it anyway.

---

## 4. What the ruling means in practice

1. **Every figure published from now on** — in `EVALUATION.md`, `PRODUCT-DEFINITION.md`, `NEXT-STEPS.md`, `PRODUCT-RESEARCH.md`, the model card, or any release table — is produced by the canonical instrument and labelled with its metric name.
2. **Cross-era comparison is forbidden.** A September number and an October number may appear in the same document, and this ruling explains why they differ, but they may **not** be differenced, and neither may be presented as the other's replacement value.
3. **The September numbers are retained, not deleted.** `pubbench/results.json` still holds every figure it held. Each now carries a `superseded_by` pointer to this document.
4. **"Superseded" means exactly this:** the September instrument is not the decision instrument for anything, now or later. Its numbers are a historical record of what a different, now-retired harness produced. They are **not** evidence that the artefact changed, and they are **not** a fallback for any measurement this project is missing.
5. **A missing measurement is still a missing measurement.** Superseding an instrument does not create a number. Where a September figure was the only figure for something (e.g. `secqa-v1-test` 100.0 % for base), that thing is now **UNMEASURED under the canonical instrument** unless a canonical run covers it. The canonical runs do cover SecQA-v1-test, and the October figures are in `eval-2026-10-23/results-merged-2026-10-23.json`.

---

## 5. The open question this does not close

`EVALUATION.md` §8 Q2 recommended the strict instrument as canonical. **This ruling adopts that recommendation.** It does **not** close Q2's second half — the recommendation also said *"with the lenient one retained for the record and marked superseded"*, which is what §3 and §4 above do.

What remains open, and is **not** closed here, is the separate measurement question that the naming of a canonical instrument does not answer: **the canonical instrument measures format compliance as much as knowledge on the two multiple-choice benchmarks.** `EVALUATION.md` §5.3.7b measured that the untrained base model is the most knowledgeable arm on both once its answer is read instead of its formatting (content 0.8840 CyberMetric / 1.0000 SecQA, versus v3's 0.8120 / 0.9364), and that **91.2 %** of the base model's format-failure rows carry the correct answer. That finding stands under this ruling unchanged, and it is why the bar sheet (`PLAN-LEDGER.md` E-2) publishes the strict headline **and** the unparseable rate **and** the content figure side by side, and never publishes a both-parseable number as a content figure.

---

## 6. Evidence

| claim | evidence |
|---|---|
| the canonical runner's identity and parameters | `pubbench/run_pubbench.py`; sha256 `669936a3…640d02d`; `METRIC_NAME` at line 45 |
| the path-patched copy changes only paths | `eval-2026-10-23/DIFF-vs-frozen-runner.txt`; `eval-2026-10-23/base/run_pubbench_local.py` |
| the superseded runner's identity and parameters | `git show 49f2057:pubbench/run_pubbench.py`; sha256 `ef21cbd1…97b7133` |
| the September figures | `pubbench/results.json` — summary block; each entry now carries `superseded_by` |
| the 41-point gap is a parse artefact | `EVALUATION.md` §4.5, §5.3.7, §5.3.7b; `docs/VERSION-COMPARISON.md:69-71` |
| the base model's format-failure content | `eval-2026-10-23/knowledge-format-vs-reasoning-older-arms.json`; `eval-2026-10-23/knowledge-selection-bias.json` |
