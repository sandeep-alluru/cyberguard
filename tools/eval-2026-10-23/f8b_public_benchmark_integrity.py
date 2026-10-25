#!/usr/bin/env python3
"""F-8b — the PUBLIC benchmarks' integrity on the rebuilt mixture, and the held-out finding.

WHY THIS FILE EXISTS
--------------------
F-8's own measurement (`f8_decontaminate_mixture.py`) found that **499 of the 500 rows of the
v1/v2 held-out set are inside the training corpus**, complete with their reference answers, in
the `fenrir` stream — and that the v2 admission gate never scanned Fenrir, because Fenrir was
fetched later (2026-09-29) for the v3 build, and the holdout split had been applied only to the
Trendyol copy of the same dataset family.

That finding is about an **internal, retired** battery. It says nothing by itself about the
**public** benchmarks, which are the only class of evidence this programme admits. So the public
benchmarks are checked here, on the rebuilt mixture, with the same instrument family (exact
normalised prompt identity, then the 13-gram Jaccard/containment scan).

**The question this file answers:** *is the rebuilt mixture clean with respect to the public
benchmarks the release decision rests on?*

WHAT IS CHECKED
---------------
* **CyberMetric-500** (500 questions) and **SecQA-v1-test** (110 questions) — the two public
  multiple-choice benchmarks, both on disk;
* exact normalised-prompt identity: is a benchmark item *in* the training corpus at all?;
* the v2 gate's own 13-gram Jaccard + containment scan, imported, for the residual overlap.

**A note on the fenrir corpus's own contamination report.** It states *"rows scanned: 99,870,
contaminated rows: 0"* — and it also states that its SecQA fingerprint file *"was a
failed-download placeholder ('Entry not found'), excluded"*. So the **SecQA half of that report
measured nothing**, and the zero it reports covers CyberMetric-500 alone. That is stated here
because this file measures the SecQA half properly, and the record should not have to infer it.

Output: `eval-2026-10-23/f8b-public-benchmark-integrity.json`
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("<programme-tree>")
GATE = ROOT / "v2/gate_v2.py"
MIXTURE = ROOT / "data/v4/mixture-v4.jsonl"
SECQA = ROOT / "pubbench/secqa_test.csv"
CYBERMETRIC = ROOT / "pubbench/cybermetric-500.json"
OUT = ROOT / "eval-2026-10-23/f8b-public-benchmark-integrity.json"

checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    checks.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} — {detail}", flush=True)


def norm(text: str) -> str:
    return " ".join(str(text or "").split())


def nh(text: str) -> str:
    return hashlib.sha256(norm(text).encode()).hexdigest()


def main() -> int:
    for p in (GATE, MIXTURE, SECQA, CYBERMETRIC):
        if not p.is_file():
            print(f"FATAL: {p} is missing")
            return 2
    spec = importlib.util.spec_from_file_location("v2_gate", GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    # ---------------------------------------------------------------- the public benchmarks
    cm = json.load(open(CYBERMETRIC))["questions"]
    cm_prompts = [q["question"] for q in cm]
    cm_hashes = {nh(p) for p in cm_prompts}
    cm_docs = [q["question"] + " " + " ".join(str(v) for v in q.get("answers", {}).values())
               for q in cm]

    secqa_rows = []
    with open(SECQA, encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            secqa_rows.append(row)
    secqa_prompts = [r.get("Question", "") for r in secqa_rows]
    secqa_hashes = {nh(p) for p in secqa_prompts}
    secqa_docs = [r.get("Question", "") + " " + " ".join(
        r.get(k, "") for k in ("A", "B", "C", "D")) for r in secqa_rows]

    check("both public multiple-choice benchmarks are on disk and read",
          len(cm_prompts) == 500 and len(secqa_prompts) == 110,
          f"CyberMetric-500 {len(cm_prompts)} questions, SecQA-v1-test {len(secqa_prompts)} "
          f"questions")

    # ---------------------------------------------------------------- the mixture
    by_src: dict[str, list[str]] = defaultdict(list)
    src_rows = Counter()
    exact = Counter()
    exact_examples: dict[str, list[dict]] = defaultdict(list)
    src_prompts: dict[str, list[str]] = defaultdict(list)

    def note(src: str, bench: str, prompt: str) -> None:
        exact[(src, bench)] += 1
        if len(exact_examples[(src, bench)]) < 5:
            exact_examples[(src, bench)].append({"prompt": prompt[:200]})

    with open(MIXTURE, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            src = r.get("src", "?")
            src_rows[src] += 1
            user = norm(r.get("user", ""))
            by_src[src].append(gate.doc_text(r))
            src_prompts[src].append(user)
            h = nh(user)
            if h in cm_hashes:
                note(src, "cybermetric-500", user)
            if h in secqa_hashes:
                note(src, "secqa-v1-test", user)

    total_exact = sum(exact.values())
    check("no row of the rebuilt mixture IS a public benchmark item",
          total_exact == 0,
          f"{total_exact} exact normalised-prompt matches across "
          f"{len(src_rows)} sources; per source: {dict(exact) if exact else 'none'}")

    # ---------------------------------------------------------------- residual overlap
    per_source = {}
    for src in sorted(by_src):
        texts = by_src[src]
        sample = texts[:2000]
        cm_scan = gate.overlap_scan(sample, cm_docs)
        sq_scan = gate.overlap_scan(sample, secqa_docs)
        per_source[src] = {
            "rows": src_rows[src],
            "sampled_rows": len(sample),
            "cybermetric-500": cm_scan,
            "secqa-v1-test": sq_scan,
            "exact_matches": {b: exact[(src, b)] for b in ("cybermetric-500", "secqa-v1-test")
                              if exact[(src, b)]},
        }
        check(f"{src}: the residual overlap against CyberMetric-500 is under the gate's own reject "
              f"threshold",
              cm_scan["jaccard_max"] < gate.OVERLAP_REJECT,
              f"jaccard_max {cm_scan['jaccard_max']} against the gate's reject threshold "
              f"{gate.OVERLAP_REJECT}")
        check(f"{src}: the residual overlap against SecQA-v1-test is under the gate's own reject "
              f"threshold",
              sq_scan["jaccard_max"] < gate.OVERLAP_REJECT,
              f"jaccard_max {sq_scan['jaccard_max']} against the gate's reject threshold "
              f"{gate.OVERLAP_REJECT}")

    out = {
        "what_this_is": "F-8b: the PUBLIC benchmarks' integrity on the rebuilt mixture, and the "
                        "held-out finding F-8 produced, stated in one place.",
        "instrument": {
            "exact_identity": "sha256 of the whitespace-normalised prompt, against the "
                              "benchmark's own question text",
            "residual_overlap": "v2/gate_v2.py::overlap_scan, imported — 13-gram Jaccard plus "
                                "verbatim-span containment, with the gate's own thresholds",
            "sample_rows_per_source": 2000,
        },
        "public_benchmarks": {
            "cybermetric-500": {"path": str(CYBERMETRIC), "questions": len(cm_prompts)},
            "secqa-v1-test": {"path": str(SECQA), "questions": len(secqa_prompts)},
        },
        "held_out_finding": {
            "what": "499 of the 500 rows of the v1/v2 held-out set (v2/holdout500.jsonl) are "
                    "inside the training corpus, complete with their reference answers, in the "
                    "fenrir stream — 604 rows, because some appear two or three times",
            "why": "the holdout split was applied to the Trendyol copy of "
                   "CyberSec-Dataset_escaped.jsonl (the v2 gate's admitted candidate) and never to "
                   "the Fenrir copy (AlicanKiraz0/Cybersecurity-Dataset-Fenrir-v2.1), which was "
                   "fetched on 2026-09-29 for the v3 build and never passed through the v2 "
                   "admission gate",
            "scope": "the held-out set is an INTERNAL battery. It is retired under the owner's "
                     "evidence rule, and no public number rests on it. The public benchmarks are "
                     "measured separately in this file",
            "fenrir_own_report_gap": "data/v3/fenrir-v2.1/CONTAMINATION_REPORT.md reports "
                                     "'contaminated rows: 0' over 99,870 rows, and also reports "
                                     "that its SecQA fingerprint file was a failed-download "
                                     "placeholder and was excluded — so the zero covers "
                                     "CyberMetric-500 only, and this file measures the SecQA half "
                                     "properly",
        },
        "per_source": per_source,
        "total_exact_matches": total_exact,
        "checks": [{"name": n, "pass": ok, "detail": d} for n, ok, d in checks],
        "pass": sum(1 for _, ok, _ in checks if ok),
        "total": len(checks),
        "all_pass": all(ok for _, ok, _ in checks),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    for n, ok, d in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {n} — {d}")
    print()
    print(f"exact public-benchmark matches in the mixture: {total_exact}")
    print(f"RESULT: {'PASS' if out['all_pass'] else 'FAIL'} — {out['pass']}/{out['total']}")
    print("wrote", OUT)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
