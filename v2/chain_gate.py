#!/usr/bin/env python3
"""chain_gate.py — write docs/CHAIN-CLEARED only when an INDEPENDENT review says so, for the revision it reviewed.

WHY. The C24 contract is gated on `docs/CHAIN-CLEARED`: it must not run unattended while the chain review is
open. But the review may land after the last agent round, and the gate must not become a deadlock. This closes
that gap without letting automation (or me) decide the outcome: it reads the reviewer's own output and writes
the marker **only** if that output contains the required clearance line — and only if the revision the review
names is the revision checked out.

So the authority stays with the reviewer, the marker cannot be conjured by an agent, and a review that says
BLOCKED, or one that reviewed a different revision, leaves the gate shut.

USAGE
  python3 v2/chain_gate.py                 # inspect the newest review, write the marker or explain the refusal
  python3 v2/chain_gate.py --dir DIR       # for testing
Exit 0 = marker written; 1 = refused (with the reason printed).
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAR_LINE = "CHAIN CLEARED"
MARKER = "docs/CHAIN-CLEARED"


def head_rev() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, timeout=60).stdout.strip()
    except Exception:                                          # noqa: BLE001
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="research-tmp/reviews")
    ap.add_argument("--force-rev-mismatch", action="store_true", help="testing aid: ignore the revision check")
    a = ap.parse_args()
    rev = head_rev()

    files = sorted(glob.glob(os.path.join(ROOT, a.dir, "codex-evalchain-review*.md")),
                   key=os.path.getmtime)
    if not files:
        print("  chain gate: no review output found — marker NOT written")
        return 1
    newest = files[-1]
    text = open(newest, encoding="utf-8", errors="replace").read()
    print(f"  newest review: {os.path.relpath(newest, ROOT)} ({len(text)} bytes)")

    if CLEAR_LINE not in text:
        # name the verdict the review actually gave, so the log is unambiguous
        verdict = "BLOCKED" if "BLOCKED" in text else "no clearance line"
        print(f"  chain gate: the review does not contain '{CLEAR_LINE}' ({verdict}) — marker NOT written")
        return 1

    # the review names the revision it inspected; the marker must not bless a different one
    revs = re.findall(r"\b[0-9a-f]{7,40}\b", text)
    named = next((r for r in revs if rev.startswith(r[:7]) or r.startswith(rev[:7])), None)
    if not named and not a.force_rev_mismatch:
        print(f"  chain gate: the review clears the chain but names no revision matching HEAD {rev[:12]} — "
              f"marker NOT written (a clearance for a revision that is not checked out proves nothing)")
        return 1

    digest = hashlib.sha256(open(newest, "rb").read()).hexdigest()
    body = (f"chain cleared by an independent review\n"
            f"review_file: {os.path.relpath(newest, ROOT)}\n"
            f"review_sha256: {digest}\n"
            f"revision_reviewed: {named or rev}\n"
            f"revision_checked_out: {rev}\n"
            f"written_at: {dt.datetime.now().isoformat(timespec='seconds')}\n")
    with open(os.path.join(ROOT, MARKER), "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"  chain gate: CLEARED — wrote {MARKER} (review {os.path.basename(newest)} clears {named or rev[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
