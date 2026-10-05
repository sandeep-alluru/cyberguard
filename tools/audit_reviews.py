#!/usr/bin/env python3
"""audit_reviews.py — bypass detector (Astra D18).

Nothing at the OS level stops a direct `codex exec`. So enforcement is DETECTION: every approved review
leaves a row in docs/review-accounting.jsonl; a codex session touching this project with no matching
accounting row is a BYPASS.

  python3 tools/audit_reviews.py [--since YYYYMMDD]

Exit 0 = no bypass · 1 = bypass detected · 2 = cannot run.
"""
import argparse, glob, json, os, re, sys
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
    # A12 repair: MATCH each session identity against recorded request identity. A count comparison is not
    # a match. Unmatched sessions are treated as ungoverned invocations and FAIL.
    recorded = accounted_ids()
    unmatched = []
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
        sid = os.path.basename(f).replace(".jsonl", "")   # session_id for identity comparison
        m = re.search(r"(\d{8}T\d{6}Z)-([A-Za-z0-9._-]+)", blob)
        req = m.group(0) if m else None
        if req is not None and req in recorded:
            continue
        if any(sid and sid in r for r in recorded):
            continue
        unmatched.append(sid)
    if unmatched:
        print(f"  BYPASS: {len(unmatched)} session(s) with NO matching recorded request identity.")
        for sid in unmatched[:8]:
            print(f"    {sid}")
        print("  Exit 1: reviews were invoked outside the governed path.")
        return 1
    print(f"  all {total} session(s) matched to recorded request identities")
    return 0


if __name__ == "__main__":
    sys.exit(main())
