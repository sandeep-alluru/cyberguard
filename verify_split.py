#!/usr/bin/env python3
"""verify_split.py — prove the held-out set is real, and prove nobody re-implemented the loader.

Two distinct jobs, because two distinct things went wrong.

1. SPLIT INVARIANTS. train_cyberguard.py holds out the first EVAL_N rows of the seeded shuffle
   and trains on the rest; eval_cyberguard.py must score on exactly that same set. If they ever
   disagree the evaluation silently scores on memorised data and the numbers look fine while
   meaning nothing. So: row-disjoint, PROMPT-disjoint, a partition of the whole corpus, and
   deterministic across runs.

   The prompt-disjointness check is not decoration. An earlier version only compared whole rows
   (assistant, user) pairs. The corpus repeats 675 user prompts with different answers, so
   held-out rows passed the row check while their QUESTIONS were in the training set — 15 of
   them at shingle-Jaccard 1.000. Deduplicating by user prompt before the split is what fixes
   it, and this check is what keeps it fixed.

2. NO DUPLICATE LOADER. The original bug was four hand-written copies of the same loader in
   train/eval/verify/leakage scripts, one of which forgot the dedupe. Encoding the rule once in
   cyberguard_data.py only helps if nothing quietly re-implements it, so this asserts each
   consumer imports the shared module and does not open the corpus itself. The fingerprint of a
   hand-rolled loader is `open(DATA` — that is what this forbids.

CPU only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROOT = Path(os.environ["CYBERGUARD_ROOT"])
DATA = ROOT / "data" / "trendyol-cybersec" / "CyberSec-Dataset_escaped.jsonl"
EVAL_N = int(os.environ.get("EVAL_N", 500))
SEED = int(os.environ.get("SEED", 0))

import cyberguard_data as cgdata  # noqa: E402

CONSUMERS = ["train_cyberguard.py", "eval_cyberguard.py", "check_leakage.py"]


def check_no_duplicate_loader() -> bool:
    ok = True
    for name in CONSUMERS:
        p = HERE / name
        if not p.exists():
            print(f"FAIL: {name} is missing")
            ok = False
            continue
        src = p.read_text(encoding="utf-8")
        problems = []
        if "import cyberguard_data" not in src:
            problems.append("does not import cyberguard_data")
        if "cgdata.load_rows" not in src:
            problems.append("does not call cgdata.load_rows")
        if "cgdata.make_split" not in src:
            problems.append("does not call cgdata.make_split")
        if "open(DATA" in src:
            problems.append("opens the corpus directly (hand-rolled loader)")
        if problems:
            print(f"FAIL: {name}: " + "; ".join(problems))
            ok = False
        else:
            print(f"PASS: {name} uses the shared loader/split and does not re-read the corpus")
    return ok


def main() -> int:
    ok = check_no_duplicate_loader()

    canon = cgdata.load_rows(DATA)
    print(f"corpus rows after prompt-dedupe: {len(canon)}")

    train_rows, eval_rows = cgdata.make_split(canon, EVAL_N, SEED)
    print(f"train {len(train_rows)}  held-out {len(eval_rows)}")

    n_dup_prompts = len(canon) - len({cgdata.norm_prompt(r["user"]) for r in canon})
    if n_dup_prompts:
        print(f"FAIL: {n_dup_prompts} duplicate user prompts survived the dedupe")
        ok = False
    else:
        print("PASS: every user prompt in the corpus is unique after dedupe")

    tr_keys = {(r["assistant"], r["user"]) for r in train_rows}
    ev_keys = {(r["assistant"], r["user"]) for r in eval_rows}
    if ev_keys & tr_keys:
        print(f"FAIL: {len(ev_keys & tr_keys)} held-out rows also appear in training")
        ok = False
    else:
        print("PASS: held-out and training rows are disjoint")

    ev_prompts = {cgdata.norm_prompt(r["user"]) for r in eval_rows}
    tr_prompts = {cgdata.norm_prompt(r["user"]) for r in train_rows}
    leaked = ev_prompts & tr_prompts
    if leaked:
        print(f"FAIL: {len(leaked)} held-out USER PROMPTS also appear in training")
        for x in list(leaked)[:3]:
            print(f"      e.g. {x[:90]!r}")
        ok = False
    else:
        print("PASS: no user prompt appears on both sides (prompt-level disjoint)")

    total = len(tr_keys | ev_keys)
    if total != len(canon) or len(tr_keys) != len(train_rows) or len(ev_keys) != len(eval_rows):
        print(f"FAIL: split loses or collapses rows — union {total} vs corpus {len(canon)}")
        ok = False
    else:
        print(f"PASS: split partitions the whole corpus ({total} rows)")

    again_train, again_eval = cgdata.make_split(canon, EVAL_N, SEED)
    if [r["user"] for r in again_eval] != [r["user"] for r in eval_rows]:
        print("FAIL: split is not deterministic across runs")
        ok = False
    else:
        print("PASS: split is deterministic (seed reproducible)")

    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
