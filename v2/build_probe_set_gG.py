#!/usr/bin/env python3
"""build_probe_set_gG.py — freeze the G-G capability battery per task, with the n each task can actually reach.

WHY: SPEC §7 pre-registers G-G as **1,200 matched pairs per task** for GSM8K, IFEval and MMLU-lite. Measured:
  * GSM8K  — the official test split is cached on spark-40ee (1,319 rows), so 1,200 is reachable;
  * IFEval — `cap_probes.PB.IFEVAL` holds **40 authored** prompts (official set is 541) and the official set is
             not cached here, so 40 is what this machine can run offline;
  * MMLU   — **not implemented** in `cap_harness.py` at all.
Rather than silently running a different battery than the one pre-registered (D11), this freezes each reachable
task with its own n and records the shortfalls in the receipt, so the verdict can state which vector ran.

Usage: python3 v2/build_probe_set_gG.py [--gsm8k-parquet PATH] [--gsm8k-n 1200]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "v2")


def freeze(path, rows, extra, receipt_path):
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    json.dump({"rows": len(rows), "sha256": digest, "seed": 0, **extra}, open(receipt_path, "w"), indent=2)
    print(f"  froze {len(rows):>5} -> {path}  sha256 {digest[:24]}…")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gsm8k-parquet", default="research-tmp/gG/gsm8k-test.parquet")
    ap.add_argument("--gsm8k-n", type=int, default=1200)
    a = ap.parse_args()

    # ---- GSM8K
    gs = []
    if os.path.exists(a.gsm8k_parquet):
        import pyarrow.parquet as pq
        t = pq.read_table(a.gsm8k_parquet)
        q = t.column("question").to_pylist()
        ans = t.column("answer").to_pylist()
        idx = list(range(len(q)))
        random.Random(0).shuffle(idx)
        for i in idx[: a.gsm8k_n]:
            gs.append({"probe_id": f"gG:gsm8k:{i}", "question": q[i], "answer": ans[i]})
    freeze("v2/data/probe-set-gG-gsm8k.jsonl", gs,
           {"gate": "G-G general capability", "task": "gsm8k",
            "n_reachable": len(gs), "n_prespecified": 1200,
            "source": a.gsm8k_parquet, "note": "official GSM8K test split, cached on spark-40ee"},
           "v2/data/probe-set-gG-gsm8k.receipt.json")

    # ---- IFEval (authored set; the official 541 is not cached here)
    ife = []
    try:
        import cap_probes as PB
        for i, entry in enumerate(getattr(PB, "IFEVAL", [])):
            # entries are (prompt, kind, param) tuples; keeping ONLY the prompt made the battery
            # uncheckable, which is why every IFEval output was scored correct (review F09)
            if isinstance(entry, (list, tuple)) and len(entry) >= 3:
                ife.append({"probe_id": f"gG:ifeval:{i}", "prompt": entry[0], "kind": entry[1], "param": entry[2]})
            else:
                ife.append({"probe_id": f"gG:ifeval:{i}", "prompt": str(entry)})
    except Exception as e:                                     # noqa: BLE001
        print(f"  IFEval unavailable: {e}")
    freeze("v2/data/probe-set-gG-ifeval.jsonl", ife,
           {"gate": "G-G general capability", "task": "ifeval",
            "n_reachable": len(ife), "n_prespecified": 1200,
            "source": "cap_probes.PB.IFEVAL (authored, prompt+kind+param)", "note": "official IFEval is 541 prompts and is not cached"},
           "v2/data/probe-set-gG-ifeval.receipt.json")

    # ---- MMLU: record the absence rather than implying coverage
    json.dump({"gate": "G-G general capability", "task": "mmlu_lite", "n_reachable": 0,
               "n_prespecified": 1200, "source": "NOT IMPLEMENTED in cap_harness.py",
               "note": "grep -c mmlu cap_harness.py == 0; the pre-registered vector cannot be produced (D11)"},
              open("v2/data/probe-set-gG-mmlu.receipt.json", "w"), indent=2)
    print("  MMLU: recorded as not implemented (n_reachable 0), never as silently absent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
