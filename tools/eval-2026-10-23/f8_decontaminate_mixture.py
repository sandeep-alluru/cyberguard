#!/usr/bin/env python3
"""F-8 — decontaminate the rebuilt mixture against the held-out set.

THE INSTRUMENT IS THE v2 GATE'S, IMPORTED
-------------------------------------------
F-8's acceptance names the instrument: the v2 admission gate's **13-gram Jaccard overlap plus
verbatim-span containment** scan, against the same **500-row held-out set** the v1 benchmark used.
This file **imports** `v2/gate_v2.py` — `tokens`, `ngrams`, `doc_text` and `overlap_scan` — and
does not re-implement any of it.

WHY A SECOND, FASTER PASS EXISTS, AND HOW IT IS PROVEN
------------------------------------------------------
The gate's `overlap_scan` is O(rows × holdout documents) with a full set intersection each time.
Over the mixture's **231,186 rows** that is 115 million intersections, which is not a
measurement anyone waits for. So the same computation is also run with an **inverted index** over
the holdout's 13-grams, which visits only the holdout documents that actually share a gram with
the row. **The indexed pass is not trusted on its own**: on every source, the indexed pass and
the imported `overlap_scan` are run over the **same 2,000-row sample** — the sample size the v2
gate itself used — and their maxima must agree exactly. The full-population figures come from
the indexed pass; the sample figures come from the reference instrument; both are in the report.

WHAT IS MEASURED
----------------
* **the held-out rows are excluded by construction** — for each source, how many rows are the
  held-out rows themselves (prompt-hash identity against the 500 held-out prompts). A non-zero
  count would be a contamination, not a residual overlap;
* **the residual overlap per source** — the maximum 13-gram Jaccard and the maximum containment
  against the held-out set, over the whole population;
* **against the v2 gate's own recorded maximum** — the gate's admitted candidates recorded a
  maximum residual overlap of **0.027** (Trendyol, 0.0266), and F-8's acceptance is that no
  source exceeds it.

Output: `eval-2026-10-23/f8-decontamination-report.json`
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("<programme-tree>")
GATE = ROOT / "v2/gate_v2.py"
HOLDOUT = ROOT / "v2/holdout500.jsonl"
HOLDOUT_MANIFEST = ROOT / "v2/holdout500.manifest.json"
GATE_REPORT = ROOT / "v2/gate-report.json"
# The mixture and the report can be pointed at a rebuilt lineage — the F-8b decontaminated corpus
# (OWNER-D3) rebuilds the mixture and is re-scanned by this same instrument. The defaults are
# unchanged, so running this file with no environment set scans exactly what it scanned before.
MIXTURE = Path(os.environ.get("MIXTURE_UNDER_TEST", ROOT / "data/v4/mixture-v4.jsonl"))
OUT = Path(os.environ.get("MIXTURE_REPORT_OUT", ROOT / "eval-2026-10-23/f8-decontamination-report.json"))

# the v2 gate's own sample size, used for the reference-vs-indexed cross-check
REFERENCE_SAMPLE = 2000

checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    checks.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} — {detail}", flush=True)


def load_gate():
    spec = importlib.util.spec_from_file_location("v2_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm_hash(text: str) -> str:
    return hashlib.sha256(" ".join(str(text or "").split()).encode()).hexdigest()


def main() -> int:
    for p in (GATE, HOLDOUT, GATE_REPORT, MIXTURE):
        if not p.is_file():
            print(f"FATAL: {p} is missing")
            return 2
    gate = load_gate()

    # ---------------------------------------------------------------- the held-out set
    holdout_rows = []
    for line in open(HOLDOUT, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line:
            holdout_rows.append(json.loads(line))
    holdout_docs = [gate.doc_text(r) for r in holdout_rows]
    holdout_prompt_hashes = {norm_hash(r.get("prompt", "")) for r in holdout_rows}
    manifest = json.load(open(HOLDOUT_MANIFEST)) if HOLDOUT_MANIFEST.is_file() else {}
    check("the held-out set is the certified 500-row split, and it is the v1 benchmark's",
          len(holdout_rows) == 500 and manifest.get("rows_eval") == 500,
          f"{len(holdout_rows)} rows, corpus sha256 {manifest.get('corpus_sha256', '?')[:16]}…, "
          f"seed {manifest.get('seed')}, out sha256 {manifest.get('out_sha256', '?')[:16]}…")

    # ---------------------------------------------------------------- the gate's own bar
    gate_report = json.load(open(GATE_REPORT))
    admitted = [c for c in gate_report["candidates"] if c.get("verdict") == "ADMIT"]
    gate_max_overlap = max((c["overlap_max"] for c in admitted if c.get("overlap_max") is not None),
                            default=None)
    gate_max_containment = max(
        (c["containment_max"] for c in admitted if c.get("containment_max") is not None), default=None)
    check("the v2 gate's own recorded maximum residual overlap is read from its report",
          gate_max_overlap is not None,
          f"max overlap across {len(admitted)} admitted candidates = {gate_max_overlap} "
          f"(containment {gate_max_containment}); the gate's n-gram is {gate.NGRAM}, its reject "
          f"thresholds are overlap {gate.OVERLAP_REJECT} and containment "
          f"{gate.CONTAINMENT_REJECT}")

    # ---------------------------------------------------------------- the holdout index
    hsets = [gate.ngrams(gate.tokens(t)) for t in holdout_docs]
    hsets = [h for h in hsets if h]
    index: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for i, h in enumerate(hsets):
        for gram in h:
            index[gram].append(i)

    def indexed_scan(texts: list[str]) -> dict:
        best_j, best_c, ge_j, ge_c = 0.0, 0.0, 0, 0
        for text in texts:
            s = gate.ngrams(gate.tokens(text))
            if not s:
                continue
            cands = set()
            for gram in s:
                for i in index.get(gram, ()):
                    cands.add(i)
            dj = dc = 0.0
            for i in cands:
                h = hsets[i]
                inter = len(s & h)
                if not inter:
                    continue
                j = inter / len(s | h)
                c = inter / min(len(s), len(h))
                if j > dj:
                    dj = j
                if inter >= gate.CONTAINMENT_MIN_SHARED and c > dc:
                    dc = c
            if dj > best_j:
                best_j = dj
            if dj >= gate.OVERLAP_REJECT:
                ge_j += 1
            if dc > best_c:
                best_c = dc
            if dc >= gate.CONTAINMENT_REJECT:
                ge_c += 1
        return {"jaccard_max": round(best_j, 4), "jaccard_docs_ge": ge_j,
                "containment_max": round(best_c, 4), "containment_docs_ge": ge_c}

    # ---------------------------------------------------------------- per source
    by_src: dict[str, list[str]] = defaultdict(list)
    src_rows = Counter()
    holdout_identity = Counter()
    src_prompt_hashes: dict[str, list[str]] = defaultdict(list)
    with open(MIXTURE, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            src = r.get("src", "?")
            src_rows[src] += 1
            text = gate.doc_text(r)
            by_src[src].append(text)
            h = norm_hash(r.get("user", ""))
            src_prompt_hashes[src].append(h)
            if h in holdout_prompt_hashes:
                holdout_identity[src] += 1

    per_source = {}
    for src in sorted(by_src):
        texts = by_src[src]
        sample = texts[:REFERENCE_SAMPLE]
        ref = gate.overlap_scan(sample, holdout_docs)
        idx = indexed_scan(sample)
        agree = (ref["jaccard_max"] == idx["jaccard_max"]
                 and ref["containment_max"] == idx["containment_max"])
        check(f"{src}: the indexed pass reproduces the imported gate's own scan on the same "
              f"{len(sample)}-row sample",
              agree,
              f"reference overlap {ref['jaccard_max']} / containment {ref['containment_max']} vs "
              f"indexed {idx['jaccard_max']} / {idx['containment_max']}")
        full = indexed_scan(texts)
        per_source[src] = {
            "rows": src_rows[src],
            "reference_sample_rows": len(sample),
            "reference_instrument": ref,
            "indexed_full_population": full,
            "holdout_rows_present_by_prompt_hash": holdout_identity[src],
            "within_the_gate_recorded_maximum": (
                full["jaccard_max"] <= gate_max_overlap if gate_max_overlap is not None else None),
        }
        check(f"{src}: no row of the mixture IS a held-out row (excluded by construction)",
              holdout_identity[src] == 0,
              f"{holdout_identity[src]} of {src_rows[src]} rows share a held-out prompt's hash")
        check(f"{src}: the residual overlap does not exceed the v2 gate's recorded maximum",
              per_source[src]["within_the_gate_recorded_maximum"],
              f"jaccard_max {full['jaccard_max']} against the gate's recorded "
              f"{gate_max_overlap}; containment {full['containment_max']} against its recorded "
              f"{gate_max_containment}")

    worst = max((v["indexed_full_population"]["jaccard_max"] for v in per_source.values()),
                default=None)
    out = {
        "what_this_is": "F-8's decontamination report: the rebuilt mixture against the certified "
                        "500-row held-out set, using the v2 admission gate's own instrument.",
        "instrument": {
            "name": "v2/gate_v2.py::overlap_scan (13-gram Jaccard + verbatim-span containment)",
            "imported_not_reimplemented": True,
            "file": str(GATE),
            "ngram": gate.NGRAM,
            "overlap_reject_threshold": gate.OVERLAP_REJECT,
            "containment_reject_threshold": gate.CONTAINMENT_REJECT,
            "containment_min_shared": gate.CONTAINMENT_MIN_SHARED,
            "gate_version": gate_report.get("gate_version"),
            "the_fast_pass": "an inverted index over the holdout's 13-grams, which visits only the "
                             "held-out documents that share a gram with the row; it is validated "
                             "against the imported scan on the same 2,000-row sample for every "
                             "source, and the validation is in this report",
        },
        "holdout": {
            "path": str(HOLDOUT),
            "rows": len(holdout_rows),
            "manifest": manifest,
            "certified_by": "the v1 benchmark's own 500-row split, exported by "
                            "v2/export_holdout.py, which refuses to write a file that is not "
                            "exactly 500 rows",
        },
        "bar": {
            "source": "v2/gate-report.json — the maximum residual overlap the gate recorded "
                      "across its admitted candidates",
            "gate_max_overlap": gate_max_overlap,
            "gate_max_containment": gate_max_containment,
            "admitted_candidates": len(admitted),
            "rule": "no source's residual overlap exceeds the gate's recorded maximum",
        },
        "per_source": per_source,
        "worst_residual_overlap": worst,
        "within_the_bar": all(v["within_the_gate_recorded_maximum"] for v in per_source.values()),
        "checks": [{"name": n, "pass": ok, "detail": d} for n, ok, d in checks],
        "pass": sum(1 for _, ok, _ in checks if ok),
        "total": len(checks),
        "all_pass": all(ok for _, ok, _ in checks),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    for n, ok, d in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {n} — {d}")
    print()
    print(f"worst residual overlap: {worst} against the gate's recorded {gate_max_overlap}")
    print(f"RESULT: {'PASS' if out['all_pass'] else 'FAIL'} — {out['pass']}/{out['total']}")
    print("wrote", OUT)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
