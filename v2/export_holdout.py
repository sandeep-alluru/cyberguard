#!/usr/bin/env python3
"""export_holdout.py — write the v1/v2 held-out 500 rows to JSONL for the admission gate.

Runs on spark-40ee (where the corpus lives). Uses cyberguard_data.py so the split is by
construction the SAME 500 rows the v1 benchmark used — the v2 benchmark's comparability depends
on it, and this script refuses to write a file that is not exactly 500 rows.

Usage (on spark-40ee, from ~/cyberguard):
    python3 export_holdout.py --out v2/holdout500.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cyberguard_data as CD  # noqa: E402

CORPUS = os.environ.get(
    "CYBERGUARD_CORPUS",
    str(Path.home() / "cyberguard/data/trendyol-cybersec/CyberSec-Dataset_escaped.jsonl"),
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="v2/holdout500.jsonl")
    ap.add_argument("--corpus", default=CORPUS)
    ap.add_argument("--eval-n", type=int, default=CD.EVAL_N_DEFAULT)
    ap.add_argument("--seed", type=int, default=CD.SEED_DEFAULT)
    args = ap.parse_args()

    rows = CD.load_rows(Path(args.corpus))
    train, ev = CD.make_split(rows, eval_n=args.eval_n, seed=args.seed)
    if len(ev) != args.eval_n:
        print(f"REFUSING: split produced {len(ev)} eval rows, expected {args.eval_n}", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for i, r in enumerate(ev):
            rec = {
                "idx": i,
                "prompt": r["user"],
                "reference": r["assistant"],
                "system": r.get("system", ""),
                "prompt_sha256": hashlib.sha256(r["user"].encode()).hexdigest()[:16],
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    corpus_sha = hashlib.sha256(Path(args.corpus).read_bytes()).hexdigest()
    manifest = {
        "corpus": args.corpus,
        "corpus_sha256": corpus_sha,
        "rows_total_after_audit": len(rows),
        "rows_train": len(train),
        "rows_eval": len(ev),
        "seed": args.seed,
        "out": str(out),
        "out_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }
    (out.parent / "holdout500.manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"WROTE {out} rows={len(ev)} train={len(train)} corpus_rows={len(rows)}")
    print(f"manifest: {out.parent / 'holdout500.manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
