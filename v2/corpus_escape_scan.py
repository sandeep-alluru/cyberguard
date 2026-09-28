#!/usr/bin/env python3
"""corpus_escape_scan.py — the missing producer for G-I's corpus half (review F10).

WHY THIS EXISTS. SPEC §7's G-I row reads: *"observed: corpus 0 literal `\\n`; raw and normalized F1 with CIs;
escape incidence per arm"*. The verdict layer required `{literal_backslash_n, raw_f1, normalized_f1}` — but
**nothing in the repository produced `literal_backslash_n`**: the only occurrences of that name were the
consumer in `v2/gates_v2.py` and the corpus filename `CyberSec-Dataset_escaped.jsonl`. The gate therefore
could not be measured at C24 even in principle. The consumer key mismatch was called out in the F10 re-review
("assembly reads `content` while evaluator F1 is stored under base/tuned `ref_token_f1_mean`"); this file
supplies the other half.

WHAT IT MEASURES. The two-character sequence `\\` + `n` (a literal backslash-n), which is the *artifact* the
gate is about — the trained model emitting escaped newlines as text. A real newline in a JSON string is a
different thing and is not counted. Counted per file, per field, and for the supervised target (`assistant`)
separately, because that is the text the model can learn to imitate.

OUTPUT. `v2/data/corpus-escape-scan.json`, a receipt carrying each file's sha256 so the number can be traced
to the exact bytes it was computed from, plus the same table on stdout.

USAGE
  python3 v2/corpus_escape_scan.py                      # default: both arms + the held-out set
  python3 v2/corpus_escape_scan.py --check              # exit 1 if the training corpus is not clean
  python3 v2/corpus_escape_scan.py --files a.jsonl b.jsonl --out somewhere.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_FILES = ("v2/data/mixture/armA.jsonl", "v2/data/mixture/armB.jsonl", "v2/holdout500.jsonl")
TEXT_FIELDS = ("system", "user", "assistant")
LITERAL = "\\n"                       # backslash + n, i.e. what an escaped newline looks like as TEXT


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(path):
    """Count literal backslash-n occurrences per field, and flag which fields carry a real newline."""
    per_field = {f: 0 for f in TEXT_FIELDS}
    rows = 0
    rows_hit = 0
    rows_hit_assistant = 0
    real_newline_assistant = 0
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows += 1
            row = json.loads(line)
            hit = False
            for field in TEXT_FIELDS:
                v = row.get(field)
                if not isinstance(v, str):
                    continue
                n = v.count(LITERAL)
                if n:
                    per_field[field] += n
                    hit = True
                    if field == "assistant":
                        rows_hit_assistant += 1
                if field == "assistant" and "\n" in v:
                    real_newline_assistant += 1
            if hit:
                rows_hit += 1
    return {"file": path, "sha256": sha256_file(os.path.join(ROOT, path)), "rows": rows,
            "rows_with_literal_backslash_n": rows_hit,
            "rows_with_literal_in_assistant": rows_hit_assistant,
            "literal_backslash_n_by_field": per_field,
            "literal_backslash_n_total": sum(per_field.values()),
            "assistant_rows_with_real_newline": real_newline_assistant}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="*", default=list(DEFAULT_FILES))
    ap.add_argument("--out", default="v2/data/corpus-escape-scan.json")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when a TRAINING corpus file carries any literal backslash-n")
    a = ap.parse_args()

    results = []
    for path in a.files:
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            print(f"  MISSING {path} — not measured (a missing file is reported, never substituted)")
            results.append({"file": path, "missing": True})
            continue
        r = scan(path)
        results.append(r)
        print(f"  {path}")
        print(f"    rows={r['rows']:<7} sha256={r['sha256'][:16]}…")
        print(f"    literal backslash-n total={r['literal_backslash_n_total']}"
              f"  rows affected={r['rows_with_literal_backslash_n']}"
              f"  in assistant={r['rows_with_literal_in_assistant']}")
        print(f"    by field: {r['literal_backslash_n_by_field']}")
        print(f"    assistant rows with a REAL newline: {r['assistant_rows_with_real_newline']}")

    doc = {"produced_by": "v2/corpus_escape_scan.py",
           "measure": "count of the two-character sequence backslash+n in each text field",
           "literal_sequence": LITERAL,
           "files": results}
    out = os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(doc, open(out, "w"), indent=2)
    print(f"\n  wrote {a.out}")

    if a.check:
        training = [r for r in results if not r.get("missing") and "/mixture/" in r["file"]]
        dirty = [r["file"] for r in training if r["literal_backslash_n_total"] != 0]
        if dirty:
            print(f"  CORPUS ESCAPE CHECK: FAIL — literal backslash-n present in {dirty}")
            return 1
        print(f"  CORPUS ESCAPE CHECK: PASS — 0 literal backslash-n across {len(training)} training file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
