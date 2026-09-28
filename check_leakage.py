#!/usr/bin/env python3
"""check_leakage.py — does the REAL held-out set contain near-paraphrases of training rows?

verify_split.py proves the split is exact-duplicate-free, row-disjoint and prompt-disjoint. But
the corpus is templated ("how would you design…", "in which scenarios would…"), so a held-out
prompt can still be a NEAR-paraphrase of a training prompt without being identical. If it is,
the evaluation partly measures memorisation and inflates the fine-tune's apparent quality.

This audits the split that training and evaluation actually use, obtained from
cyberguard_data.py. An earlier version of this file loaded the corpus and shuffled it
independently — it reported leakage on a split no run had ever used, which is worse than no
audit, because it certifies the wrong thing. It now cannot diverge: there is one loader.

Method: 3-token shingles over the user prompt, an inverted index shingle -> training row ids,
then Jaccard similarity against the training rows sharing at least one rare shingle. CPU only.

Exit code 1 if any held-out prompt reaches the 0.80 near-duplicate threshold, so this is usable
as a gate rather than a report.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROOT = Path(os.environ.get("CYBERGUARD_ROOT", Path.home() / "cyberguard"))
DATA = ROOT / "data" / "trendyol-cybersec" / "CyberSec-Dataset_escaped.jsonl"
EVAL_N = int(os.environ.get("EVAL_N", 500))
SEED = int(os.environ.get("SEED", 0))
MAX_ROWS = int(os.environ.get("MAX_ROWS", 0))
THRESHOLD = float(os.environ.get("LEAK_THRESHOLD", 0.80))

import cyberguard_data as cgdata  # noqa: E402


def main() -> int:
    canon = cgdata.load_rows(DATA)
    train, held = cgdata.make_split(canon, EVAL_N, SEED, MAX_ROWS)
    print(f"corpus {len(canon)}   held-out {len(held)}   training {len(train)}")

    index: dict[str, list[int]] = defaultdict(list)
    tr_sh: list[set] = []
    for i, r in enumerate(train):
        s = cgdata.shingles(r["user"])
        tr_sh.append(s)
        for sh in s:
            index[sh].append(i)

    worst: list[tuple[float, str, str]] = []
    sims: list[float] = []
    for h in held:
        hs = cgdata.shingles(h["user"])
        cand: dict[int, int] = defaultdict(int)
        for sh in hs:
            for i in index.get(sh, ()):
                cand[i] += 1
        best, best_i = 0.0, None
        for i, shared in cand.items():
            if shared < max(2, len(hs) * 0.25):
                continue
            j = cgdata.jaccard(hs, tr_sh[i])
            if j > best:
                best, best_i = j, i
        sims.append(best)
        worst.append((best, h["user"][:90],
                      train[best_i]["user"][:90] if best_i is not None else ""))

    sims.sort()
    n = len(sims)
    print()
    print("=== held-out vs nearest training prompt (3-token shingle Jaccard) ===")
    print(f"  max     {sims[-1]:.3f}")
    print(f"  p99     {sims[int(n * 0.99)]:.3f}")
    print(f"  p90     {sims[int(n * 0.90)]:.3f}")
    print(f"  median  {sims[n // 2]:.3f}")
    above = sum(1 for s in sims if s >= THRESHOLD)
    print(f"  rows >= {THRESHOLD:.2f} (near-duplicate, leakage risk): {above}")
    print(f"  rows >= 0.60 (substantially overlapping):    {sum(1 for s in sims if s >= 0.6)}")

    worst.sort(reverse=True)
    print()
    print("=== worst 5 ===")
    for s, hu, tu in worst[:5]:
        print(f"  {s:.3f}")
        print(f"     held : {hu!r}")
        print(f"     train: {tu!r}")

    print()
    if above:
        print(f"VERDICT: LEAKAGE — {above} held-out rows paraphrase training rows")
        return 1
    print(f"VERDICT: no near-duplicate leakage at the {THRESHOLD:.2f} threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
