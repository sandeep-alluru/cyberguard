#!/usr/bin/env python3
"""battery_contamination_check.py — are the C24 probe sets rows the models were TRAINED on?

WHY. An independent review (Muse, 2026-09-28) withheld clearance with this objection:

  "The frozen G-B/G-E/G-J batteries are exact training rows in both arms (measured exact normalized-prompt
   overlap: G-B 300/300, G-E 60/60, G-J 99/100; G-F unanswerable 20/20), sampled from the training sources
   with no split, so a C24 verdict cannot report those gates as capability PASSes on the current batteries."

A gate whose probes are training rows measures memorisation, not capability — the most serious kind of
evaluation defect this project can have. It was not caught by the leakage instrument because that instrument's
reference universe is `holdout500.jsonl` + 225 legacy `cap_probes.py` strings, NOT the frozen batteries
(`v2/leak_scan.py:124-147`). This check closes that specific hole: it compares every frozen battery's prompts
against the training mixture, both arms, normalised.

Threshold: any exact normalised-prompt overlap with a TRAINING arm is a failure, because the item appears
verbatim in the supervised data. (A near-match report is printed as well, so the reviewer's "exact" and a
human's "substantially the same question" are both visible.)

USAGE
  python3 v2/battery_contamination_check.py            # report only, exit 1 on any overlap
  python3 v2/battery_contamination_check.py --report   # never fails; prints the table
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATTERIES = {
    "gA": "v2/data/probe-set-gA.jsonl", "gA2": "v2/data/probe-set-gA2.jsonl",
    "gB": "v2/data/probe-set-gB.jsonl", "gC": "v2/data/probe-set-gC.jsonl",
    "gE": "v2/data/probe-set-gE.jsonl", "gF": "v2/data/probe-set-gF.jsonl",
    "gG-gsm8k": "v2/data/probe-set-gG-gsm8k.jsonl", "gG-ifeval": "v2/data/probe-set-gG-ifeval.jsonl",
    "gJ": "v2/data/probe-set-gJ.jsonl",
    # the fresh instruments commissioned by the owner's 2026-09-28 decision: these must ALSO be disjoint, and
    # they are what the generalisation verdict runs on. A fresh set that overlapped training would be the same
    # defect wearing a new filename.
    "fresh-gA": "v2/data/probe-set-fresh-gA.jsonl", "fresh-gB": "v2/data/probe-set-fresh-gB.jsonl",
    "fresh-gE": "v2/data/probe-set-fresh-gE.jsonl", "fresh-gF": "v2/data/probe-set-fresh-gF.jsonl",
    "fresh-gJ": "v2/data/probe-set-fresh-gJ.jsonl",
}
# Owner decision 2026-09-28 22:02 CDT, item 2 and 4: the sets that turned out to be training rows are
# REPURPOSED as retention/recall checks — failure on a trained row is still a red flag, but the number is
# never a generalisation claim. The fresh sets (commissioned by the same decision) plus the sets that were
# already disjoint carry the generalisation verdict, and THEY must be strictly disjoint.
GENERALISATION = {"fresh-gA", "fresh-gB", "fresh-gE", "fresh-gF", "fresh-gJ",
                  "gA2", "gC", "gG-gsm8k", "gG-ifeval"}
RETENTION = {"gA", "gB", "gE", "gF", "gJ"}
TRAINING = {"armA": "v2/data/mixture/armA.jsonl", "armB": "v2/data/mixture/armB.jsonl"}
HOLDOUT = "v2/holdout500.jsonl"


def norm(s: str) -> str:
    """Normalisation for the overlap test: case, whitespace and surrounding punctuation only.

    Deliberately NOT aggressive: stripping more (e.g. all punctuation, stopwords) would manufacture
    matches that a reader of the two prompts would not call the same item.
    """
    s = re.sub(r"\s+", " ", str(s or "")).strip().lower()
    return s.strip(" \"'.?!:;\n\t")


# The sets do NOT share a field name (gA/gB/gE/gJ use `prompt`, gsm8k uses `question`, holdout uses
# `prompt`). The first version of this file read `user` for everything and reported n=0 with a PASS for every
# battery - a vacuous instrument, which is worse than no instrument. The field is now detected per file and
# reported, so a silent mismatch cannot look like a clean result again.
CANDIDATE_FIELDS = ("prompt", "question", "user")


def prompts(path: str) -> tuple[list[str], str | None]:
    out: list[str] = []
    field = None
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if field is None:
                for cand in CANDIDATE_FIELDS:
                    if isinstance(row.get(cand), str) and row[cand].strip():
                        field = cand
                        break
                if field is None:
                    return [], None
            v = row.get(field)
            if isinstance(v, str) and v.strip():
                out.append(norm(v))
    if not out:
        return [], field
    return out, field


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="print the table but never fail")
    ap.add_argument("--examples", type=int, default=2, help="overlapping examples to show per battery")
    a = ap.parse_args()

    train, trainf = {}, {}
    for arm, p in TRAINING.items():
        ps, fld = prompts(p)
        if not ps:
            raise SystemExit(f"FATAL: read 0 prompts from {p} (field detection failed) - refusing to report PASS")
        train[arm], trainf[arm] = set(ps), fld
    hps, hfld = prompts(HOLDOUT)
    hold = set(hps)
    print(f"  fields read: training={trainf} holdout={hfld!r}")
    all_train = train["armA"] | train["armB"]
    print(f"  training prompts: armA {len(train['armA'])} unique, armB {len(train['armB'])} unique, "
          f"union {len(all_train)}; holdout {len(hold)} unique")
    print()
    print(f"  {'battery':<11} {'role':<15} {'n':>5} {'in armA':>8} {'in armB':>8} {'in train':>9}  verdict")
    bad_general, retention_report = [], []
    for name, path in BATTERIES.items():
        ps, fld = prompts(path)
        if not ps:
            raise SystemExit(f"FATAL: read 0 prompts from {path} (field {fld!r}) - refusing to report PASS")
        nt = sum(1 for p in ps if p in all_train)
        na = sum(1 for p in ps if p in train["armA"])
        nb = sum(1 for p in ps if p in train["armB"])
        role = "generalisation" if name in GENERALISATION else "retention/recall"
        if role == "generalisation":
            bad = nt > 0
            if bad:
                bad_general.append((name, nt, len(ps)))
            verdict = "CONTAMINATED (must be disjoint)" if bad else "disjoint"
        else:
            retention_report.append((name, nt, len(ps)))
            verdict = f"recall coverage {nt}/{len(ps)} — NOT generalisation"
        print(f"  {name:<11} {role:<15} {len(ps):>5} {na:>8} {nb:>8} {nt:>9}  {verdict}")
        if role == "generalisation" and a.examples and nt:
            for s in [p for p in ps if p in all_train][:a.examples]:
                print(f"      e.g. {s[:96]!r}")
    print()
    if retention_report:
        print("  RETENTION/recall instruments (deliberately training rows — a FAILURE here is a red flag,")
        print("  but the number is recall on memorised items and must never be reported as generalisation):")
        for name, nt, n in retention_report:
            print(f"    {name}: {nt}/{n} of its probes are training rows")
    print()
    if bad_general:
        print("  RESULT: FAIL — a GENERALISATION instrument overlaps the training data, so that gate would")
        print("          measure memorisation:")
        for name, nt, n in bad_general:
            print(f"            {name}: {nt}/{n}")
        if not a.report:
            return 1
        return 0
    print("  RESULT: PASS — every GENERALISATION instrument is prompt-disjoint from both training arms; the")
    print("          retention/recall instruments are labelled as such and carry no generalisation claim")
    return 0


if __name__ == "__main__":
    sys.exit(main())
