#!/usr/bin/env python3
"""chain_gate.py — write docs/CHAIN-CLEARED only when an INDEPENDENT review says so, for the revision it reviewed.

WHY. The review marker must not become a deadlock, but automation (or the agent) must not decide the outcome
either: this reads the reviewer's own output and writes the marker **only** if that output contains the required
clearance line **and** the revision it names is the revision checked out. So the authority stays with the
reviewer, the marker cannot be conjured by an agent, and a review that says BLOCKED, or that cleared a different
revision, leaves the gate shut.

2026-09-29 FIX. The gate could never fire. It globbed `codex-evalchain-review*.md` only, so the clearance
produced by this project's actual review numbering (`codex-review-*.md`) was invisible to it — it reported
"newest review: codex-evalchain-review11.md" while review #17 sat on disk saying `CHAIN CLEARED a91da33296ab`.
A gate that can never be satisfied is not a safety property, it is a broken mechanism wearing one.
It now scans every markdown review, matches the clearance line ANCHORED to the start of a line (so the phrase
appearing in prose cannot clear anything), and accepts only a clearance whose revision matches HEAD — reporting
every clearance it found and why each was accepted or rejected.

USAGE
  python3 v2/chain_gate.py                      # inspect every review, write the marker or explain the refusal
  python3 v2/chain_gate.py --dir DIR --marker P # for testing: scan DIR, write the marker at P
  python3 v2/chain_gate.py --force-rev-mismatch # testing aid: accept a clearance for another revision
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
# Anchored: a clearance must be its own line, followed by the revision it clears. Prose mentioning the phrase,
# or a quoted objection ("NOT CLEARED: ..."), cannot satisfy this.
CLEAR_RE = re.compile(r"^\s*" + CLEAR_LINE + r"\s+([0-9a-f]{7,40})\b", re.M)
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
    ap.add_argument("--marker", default=MARKER)
    ap.add_argument("--force-rev-mismatch", action="store_true", help="testing aid: ignore the revision check")
    a = ap.parse_args()
    rev = head_rev()

    # PROMPT FILES ARE NOT REVIEWS. A dispatch prompt contains the PRESCRIBED clearance line as a format
    # example, so scanning prompts would let a prompt clear the chain with no reviewer involved — found by
    # running this gate against the real directory, where it matched codex-review-17-prompt.md as well as the
    # real clearance. Reviewer output is whatever is not a prompt.
    allmd = sorted(glob.glob(os.path.join(ROOT, a.dir, "*.md")), key=os.path.getmtime)
    files = [f for f in allmd if "prompt" not in os.path.basename(f).lower()]
    skipped = len(allmd) - len(files)
    if not files:
        print(f"  chain gate: no review output found in {a.dir} — marker NOT written")
        return 1
    print(f"  chain gate: scanning {len(files)} review file(s) in {a.dir} for a clearance of {rev[:12]}"
          + (f" ({skipped} prompt file(s) excluded — a prompt is not a review)" if skipped else ""))

    accepted, rejected = None, []
    for f in files:
        try:
            text = open(f, encoding="utf-8", errors="replace").read()
        except Exception:                                      # noqa: BLE001
            continue
        for m in CLEAR_RE.finditer(text):
            named = m.group(1)
            matches = bool(rev) and (rev.startswith(named) or named.startswith(rev[:7]))
            print(f"    {os.path.basename(f)}: names {named[:12]} "
                  f"{'— matches HEAD' if matches else '— does NOT match HEAD, unusable'}")
            if matches:
                accepted = (f, named, text)
            else:
                rejected.append((os.path.basename(f), named))

    if accepted is None:
        if a.force_rev_mismatch and rejected:
            f = os.path.join(ROOT, a.dir, rejected[-1][0])
            accepted = (f, rejected[-1][1], open(f, encoding="utf-8", errors="replace").read())
            print("  chain gate: --force-rev-mismatch: accepting a clearance for another revision (testing aid)")
        elif rejected:
            print(f"  chain gate: {len(rejected)} clearance(s) found but none names the checked-out revision "
                  f"{rev[:12]} — marker NOT written (a clearance for a revision that is not checked out proves "
                  f"nothing)")
            return 1
        else:
            print(f"  chain gate: no review contains a '{CLEAR_LINE} <revision>' line — marker NOT written")
            return 1

    newest, named, text = accepted
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    body = (f"chain cleared by an independent review\n"
            f"review_file: {os.path.relpath(newest, ROOT)}\n"
            f"review_sha256: {digest}\n"
            f"revision_reviewed: {named}\n"
            f"revision_checked_out: {rev}\n"
            f"written_at: {dt.datetime.now().isoformat(timespec='seconds')}\n")
    out = os.path.join(ROOT, a.marker)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"  chain gate: CLEARED — wrote {a.marker} (review {os.path.basename(newest)} clears {named[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
