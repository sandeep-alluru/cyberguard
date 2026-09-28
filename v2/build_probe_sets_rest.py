#!/usr/bin/env python3
"""build_probe_sets_rest.py — freeze the remaining battery sets: G-B triage, G-E sigma, G-A2 defensive.

The contract's battery list covered G-A/G-C/G-F/G-G/G-J, leaving G-B, G-E and G-A2 with no producer at all —
their gate inputs would have fallen back to the stale v1 receipts. The sources all exist:

  G-B  format-compliance `triage-one-word` (600 rows, 335 malicious / 265 benign) — freeze a balanced 300
       (200 benign + 100 malicious) which meets SPEC's ">=300 items, >=200 negatives, >=100 positives"
  G-E  format-compliance `sigma-rule` (400 requests) — freeze the 60 SPEC asks for
  G-A2 `cap_probes.DEFENSIVE_40` (40 must-answer prompts) + 20 benign-help prompts scraped from the same
       module's source, since the benign-help battery is built inside a function rather than as a constant

Usage: python3 v2/build_probe_sets_rest.py
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "v2")


def freeze(path, rows, extra, receipt):
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    d = hashlib.sha256(open(path, "rb").read()).hexdigest()
    json.dump({"rows": len(rows), "sha256": d, "seed": 0, **extra}, open(receipt, "w"), indent=2)
    print(f"  froze {len(rows):>4} -> {path}  sha256 {d[:24]}…")
    return d


def main() -> int:
    fmt = [json.loads(l) for l in open("v2/data/format-compliance.jsonl")]

    # G-B: balanced 300
    tri = [r for r in fmt if (r.get("meta") or {}).get("kind") == "triage-one-word"]
    ben = [r for r in tri if r["assistant"].strip().lower() == "benign"]
    mal = [r for r in tri if r["assistant"].strip().lower() == "malicious"]
    rng = random.Random(0)
    rng.shuffle(ben); rng.shuffle(mal)
    gB = [{"probe_id": f"gB:{i}", "prompt": r["user"], "gold": "benign"} for i, r in enumerate(ben[:200])]
    gB += [{"probe_id": f"gB:m{i}", "prompt": r["user"], "gold": "malicious"} for i, r in enumerate(mal[:100])]
    freeze("v2/data/probe-set-gB.jsonl", gB,
           {"gate": "G-B triage", "kind": "triage-one-word", "source": "v2/data/format-compliance.jsonl",
            "note": "SPEC needs >=300 with >=200 negatives and >=100 positives"},
           "v2/data/probe-set-gB.receipt.json")

    # G-E: 60 sigma requests
    sig = [r for r in fmt if (r.get("meta") or {}).get("kind") == "sigma-rule"]
    rng.shuffle(sig)
    gE = [{"probe_id": f"gE:{i}", "prompt": r["user"]} for i, r in enumerate(sig[:60])]
    freeze("v2/data/probe-set-gE.jsonl", gE,
           {"gate": "G-E sigma", "kind": "sigma-rule request",
            "source": "v2/data/format-compliance.jsonl", "note": "60 requested rules per SPEC §7"},
           "v2/data/probe-set-gE.receipt.json")

    # G-A2: 40 defensive + 20 benign-help
    import cap_probes as PB
    src = open("cap_probes.py").read()
    block = src[src.find("benign-help battery"):]
    benign = re.findall(r'"([^"]{25,200})"', block)[:20]
    gA2 = [{"probe_id": f"gA2:d{i}", "prompt": p, "kind": "defensive"} for i, p in enumerate(getattr(PB, "DEFENSIVE_40", [])[:40])]
    gA2 += [{"probe_id": f"gA2:b{i}", "prompt": p, "kind": "benign-help"} for i, p in enumerate(benign)]
    freeze("v2/data/probe-set-gA2.jsonl", gA2,
           {"gate": "G-A2 defensive preservation", "kind": "defensive + benign-help",
            "source": "cap_probes.DEFENSIVE_40 + benign-help block", "benign_scraped": len(benign),
            "note": "SPEC: 40 defensive + 20 benign-help, NEW and disjoint"},
           "v2/data/probe-set-gA2.receipt.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
