#!/usr/bin/env python3
"""attack_label_audit.py — measure ATT&CK id/name supervision in the frozen arms (review #9, item 1).

Review #9 found the shared base corpus asserting sibling ATT&CK ids against the wrong names — it taught
"T1071.004 = Web Protocols" when T1071.004 is DNS, "T1543.002 = Windows Service" when that is Systemd, and
"T1558.001 = Kerberoasting" when T1558.001 is Golden Ticket.

This audit classifies every explicit `Txxxx.xxx (Name)` assertion in both arms against MITRE's own STIX and
reports five disjoint outcomes, so the state of this class is a number rather than an adjective:

  correct        the id's canonical current name matches the text
  parent-ref     the text names the PARENT technique, not the sub-technique (not a defect)
  repaired       a wrong current id that build_mixture.repair_attack_ids() rewrote to the sibling whose
                 current name the text matches — this count must be ZERO in a built arm, because the build
                 performs the repair; a non-zero value means the repair did not run
  stale-or-loose the id is plausible but the text carries a pre-rename name or a loose synonym that MITRE's
                 current table cannot map (e.g. T1557.001 "Adversary-in-the-Middle: LLMNR/NBT-NS Poisoning",
                 the technique's name before MITRE renamed it). NOT repairable without inventing text.
  unknown-id     the id is absent from the bundled STIX export

Usage: python3 v2/attack_label_audit.py [--dir v2/data/mixture] [--json out.json]
Exit:  0 always (this is a measurement, not a gate); the gate is that `repaired` is 0 in a built arm.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_mixture as B  # noqa: E402

ASSERTION = re.compile(r"\b(T\d{4}\.\d{3})\b\s*(?:=|:)?\s*\(([^)\n]{3,90})\)")


def classify(text, table, by_leaf):
    out = []
    for eid, name in ASSERTION.findall(str(text)):
        canon = table.get(eid)
        if canon is None:
            out.append(("unknown-id", eid, name)); continue
        if B._leaf(name) == B._leaf(canon):
            out.append(("correct", eid, name)); continue
        parent = eid.split(".")[0]
        if parent in table and B._leaf(name) == B._leaf(table[parent]):
            out.append(("parent-ref", eid, name)); continue
        target = None
        if ":" in name:
            pl, lo = name.split(":", 1)
            target = (by_leaf.get("__full__") or {}).get((True, f"{B._leaf(pl)}|{B._leaf(lo)}"))
        if not target:
            target = by_leaf.get(B._leaf(name))
        if target and target != eid and target.split(".")[0] == eid.split(".")[0]:
            out.append(("repaired", eid, name))
        else:
            out.append(("stale-or-loose", eid, name))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="v2/data/mixture")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    t = B.attack_table()
    table, deprecated = t if isinstance(t, tuple) else (t, set())
    # the name index prefers an ACTIVE id, exactly as the builder's repair does
    seen = {}
    for i, nm in table.items():
        seen.setdefault(B._leaf(nm), set()).add(i)
    by_leaf = {}
    for leaf, ids in seen.items():
        act = [i for i in ids if i not in deprecated]
        if len(act) == 1:
            by_leaf[leaf] = act[0]
        elif not act and len(ids) == 1:
            by_leaf[leaf] = next(iter(ids))
    # same full-label index the builder uses (review #11): "Parent: Leaf" is unique even when the leaf is not
    full = {}
    for i, nm in table.items():
        if "." not in i:
            continue
        par = i.split(".")[0]
        if par in table:
            full[(i not in deprecated, f"{B._leaf(table[par])}|{B._leaf(nm)}")] = i
    by_leaf["__full__"] = full

    report = {}
    for arm in ("armA.jsonl", "armB.jsonl"):
        rows = [json.loads(l) for l in open(os.path.join(args.dir, arm))]
        counts = collections.Counter()
        rows_with = collections.Counter()
        examples = collections.defaultdict(list)
        for i, r in enumerate(rows):
            if r.get("src") != "trendyol":
                continue
            res = classify(r["assistant"], table, by_leaf)
            if not res:
                continue
            seen = set()
            for kind, eid, name in res:
                counts[kind] += 1
                seen.add(kind)
                if len(examples[kind]) < 4:
                    examples[kind].append((i + 1, f"{eid} (canon: {table.get(eid)}) vs {name[:52]}"))
            for k in seen:
                rows_with[k] += 1
        report[arm] = {"assertions": dict(counts), "rows": dict(rows_with),
                       "examples": {k: v for k, v in examples.items()}}
        print(f"  {arm}:")
        print(f"    assertions: {dict(counts) or 'none'}")
        print(f"    rows carrying them: {dict(rows_with) or 'none'}")
        for kind in ("repaired", "stale-or-loose", "unknown-id"):
            for line, txt in examples.get(kind, [])[:2]:
                print(f"      {kind} @ line {line}: {txt}")

    if args.json:
        json.dump(report, open(args.json, "w"), indent=2)
    ok = all(report[a]["assertions"].get("repaired", 0) == 0 for a in report)
    print(f"\n  REPAIR CHECK: {'PASS' if ok else 'FAIL'} — a built arm must contain 0 'repaired' assertions")
    print("  Stale pre-rename names are recorded, not repaired: MITRE's current table cannot map them without"
          " inventing text, and they are shared by both arms, so they cannot bias the A/B contrast.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
