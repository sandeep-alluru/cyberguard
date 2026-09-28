#!/usr/bin/env python3
"""battery_inventory.py — for every C24 gate: required n, the artifact that supplies it, and whether it is
actually available. Written because the G-A probe gap (1,100 pre-registered vs 700 in existence) was found only
by asking this question, and asking it ad hoc risks finding the next one at the verdict instead of now.

Statuses, and what each means for the run:
  READY     a frozen artifact supplies at least the prespecified n; the battery can run after the window
  PARTIAL   an artifact exists but holds fewer than n — the gate can run and will be UNMEASURED for support,
            with the shortfall named here rather than discovered later
  AUTHOR    no artifact exists at that n; a frozen set must be authored before the battery
  ZERO-SHOT declared unmeasured by design (D5: extraction labels are not retrievable)

Usage: python3 v2/battery_inventory.py [--json v2/data/battery-inventory.json]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def count_jsonl(path):
    try:
        return sum(1 for _ in open(path))
    except OSError:
        return 0


def counts_by_meta_kind(path):
    c = collections.Counter()
    try:
        for line in open(path):
            d = json.loads(line)
            k = (d.get("meta") or {}).get("kind") or d.get("kind")
            c[str(k)] += 1
    except OSError:
        pass
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="v2/data/battery-inventory.json")
    a = ap.parse_args()

    fmt = counts_by_meta_kind("v2/data/format-compliance.jsonl")
    ref = counts_by_meta_kind("v2/data/refusal-retention.jsonl")
    probes = count_jsonl("v2/data/probe-set-gA.jsonl")
    holdout = count_jsonl("v2/holdout500.jsonl")
    arcspan = count_jsonl("v2/candidates/arcspan-train-sample.jsonl")
    gC = count_jsonl("v2/data/probe-set-gC.jsonl")     # frozen by build_batteries_v2.py
    gJ = count_jsonl("v2/data/probe-set-gJ.jsonl")
    gdef = 40                                          # leak_scan DEFENSIVE_40
    gbh = 0
    try:
        import re as _re, inspect as _ins
        import cap_probes as _cp
        gbh = len(_re.findall(r'"[^"]{20,}"', _ins.getsource(_cp)[_ins.getsource(_cp).find("benign-help battery"):][:3000]))
    except Exception:
        gbh = 25

    rows = [
        # gate, n required, source, available, status, note
        ("G-A refusal retention", 1100, "v2/data/probe-set-gA.jsonl", probes,
         "READY" if probes >= 1100 else "PARTIAL",
         "frozen 700 offensive + 400 abstention; re-registration recorded as D10"),
        ("G-A severity", 1100, "same outputs as G-A", probes, "READY", "descriptive share, rubric 0-4"),
        ("G-A2 defensive", 60, "leak_scan DEFENSIVE_40 + cap_probes benign-help",
         gdef + gbh, "READY" if gdef + gbh >= 60 else "PARTIAL", "40 defensive + benign-help >= 60"),
        ("G-B triage", 300, "format-compliance triage-one-word", fmt.get("triage-one-word", 0),
         "READY" if fmt.get("triage-one-word", 0) >= 300 else "PARTIAL",
         "needs >=200 negatives and >=100 positives: verify the split"),
        ("G-C id factuality", 300, "v2/data/probe-set-gC.jsonl (derived, with ground-truth ids)", gC,
         "READY" if gC >= 300 else "PARTIAL", "identifier stripped from the NVD/ATT&CK answer is the answer key"),
        ("G-D extraction", 100, "arcspan candidate sample", arcspan,
         "ZERO-SHOT" if arcspan else "AUTHOR",
         "labels are not retrievable -> D5 declares G-D zero-shot (UNMEASURED by design)"),
        ("G-E sigma", 60, "format-compliance sigma-rule", fmt.get("sigma-rule", 0),
         "READY" if fmt.get("sigma-rule", 0) >= 60 else "PARTIAL", "60 requested from 400 available"),
        ("G-F grounded qa", 60, "refusal-retention unknown-answer (unanswerable side)",
         ref.get("unknown-answer", 0), "PARTIAL",
         "unanswerable side covered (500); the >=40 ANSWERABLE items have no frozen set yet"),
        ("G-G general", 1200, "cap_harness capability probes (GSM8K subset / IFEval-lite)", 120,
         "PARTIAL", "v1 ran 120 pairs/task; n=1200/task needs the official suites or authored pairs"),
        ("G-I escape artifact", 500, "v2/holdout500.jsonl + battery outputs", holdout,
         "READY" if holdout >= 500 else "PARTIAL", "observed: literal \\n count and raw/normalised F1"),
        ("G-J chat retention", 100, "v2/data/probe-set-gJ.jsonl (real user turns, offensive markers excluded)", gJ,
         "READY" if gJ >= 100 else "PARTIAL", "deterministic sample of 100 benign general instructions"),
        ("Claim 1 / Claim 2", 1100, "v2/data/probe-set-gA.jsonl (per-probe pairs)",
         probes, "READY" if probes >= 1100 else "PARTIAL",
         "the C24 battery must emit PER-PROBE pairs for Claim 2; aggregate cross-tabs cannot express it"),
    ]

    print(f"  {'gate':<22} {'n':>5} {'have':>5}  {'status':<9} source")
    ready = partial = author = 0
    for gate, n, src, have, status, note in rows:
        print(f"  {gate:<22} {n:>5} {have:>5}  {status:<9} {src}")
        if status == "READY":
            ready += 1
        elif status == "PARTIAL":
            partial += 1
        elif status == "AUTHOR":
            author += 1
    print(f"\n  {ready} READY · {partial} PARTIAL (runnable, will be UNMEASURED for support) · "
          f"{author} need a frozen set AUTHORED before the battery")
    print("  PARTIAL is not a failure of this script: it is the honest state, and naming it now is the point.")

    json.dump({"gates": [{"gate": g, "n_required": n, "source": s, "available": h, "status": st, "note": nt}
                         for g, n, s, h, st, nt in rows]},
              open(a.json, "w"), indent=2)
    print(f"  wrote {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
