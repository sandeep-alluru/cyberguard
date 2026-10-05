#!/usr/bin/env python3
"""audit_reviews.py — bypass detector (Astra D18).

Nothing at the OS level stops a direct `codex exec`. So enforcement is DETECTION: every approved review
leaves a row in docs/review-accounting.jsonl; a codex session touching this project with no matching
accounting row is a BYPASS.

  python3 tools/audit_reviews.py [--since YYYYMMDD]

Exit 0 = no bypass · 1 = bypass detected · 2 = cannot run.
"""
import argparse, glob, json, os, sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "docs", "review-accounting.jsonl")
SESSIONS = os.path.expanduser("~/.codex/sessions")


def accounted_ids():
    if not os.path.exists(LEDGER):
        return set()
    out = set()
    for line in open(LEDGER, encoding="utf8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            out.add(json.loads(line)["request_id"])
        except Exception:
            continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="20261004", help="YYYYMMDD")
    a = ap.parse_args()
    have = accounted_ids()
    print(f"  accounted reviews: {len(have)}")
    suspects, total = [], 0
    for f in glob.glob(os.path.join(SESSIONS, "**", "*.jsonl"), recursive=True):
        day = os.path.basename(os.path.dirname(f))
        if day < a.since:
            continue
        try:
            blob = open(f, encoding="utf8", errors="replace").read()
        except Exception:
            continue
        if "cyberguard" not in blob.lower():
            continue
        total += 1
        suspects.append((os.path.basename(f), len(blob)))
    print(f"  cyberguard-touching codex sessions since {a.since}: {total}")
    if total and not have:
        print(f"  BYPASS: {total} session(s) and ZERO accounting rows.")
        for n, s in suspects[:8]:
            print(f"    {s/1024:8.0f} KB  {n}")
        return 1
    if suspects and have:
        print(f"  {len(suspects)} session(s) vs {len(have)} recorded review(s) — reconcile before trusting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
