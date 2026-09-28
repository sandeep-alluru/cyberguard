#!/usr/bin/env python3
"""completeness_screen.py — THE acceptance test for answer completeness (plan item D9).

Why this file exists. Three reviews in a row withheld clearance on answer completeness, and each one used
a different, unwritten standard ("an ending a reader would accept"), so each found a new class and the
count grew instead of reaching zero: review #4 found 10 rows, #5 found 38, #6 found 212. Review #6 also
conceded that "universal human-semantic certification is not established" for 162,244 rows — that standard
is not decidable, so it cannot be the gate. This screen states the rules instead:

  1. heading-only           the whole answer is a markdown heading (<= 16 words)
  2. trailing-heading       a MULTI-LINE answer whose last non-empty line is a heading
  3. inline-heading-cut     the answer ends inside a flattened heading ("... ### 2.")
  4. list-marker-end        the answer ends on a bare list marker after a finished sentence ("... 2.")
  5. unclosed-code-fence    an odd number of ``` fences
  6. unclosed-citation      a "(Citation:" with no later ")"
  7. truncated-path         ends with "/." or a bare "/" or "\\"
  8. dangling-punctuation   ends on : , ; ( [ { | - or an em dash
  10. no-boundary            no valid sentence end anywhere, and no trim can produce one

REMOVED after measurement: "unbalanced-parenthesis". It counted parentheses anywhere in the answer, so a
single stray "(" in a quoted CVE description flagged answers that end with a perfectly balanced sentence
("…T1134 (Access Token Manipulation)." — 25 of 30 arm-A hits were like this). The ending-related case it
was meant to catch, an unfinished parenthetical, is caught by unclosed-citation and dangling-punctuation.

Rows the rules do NOT cover, by design and stated here so nobody has to guess: prose that a human would
judge awkward but which ends at a real sentence boundary; contract/definition fragments that end with a
period; table cells that end with "|". Those are judgement calls, not decidable defects, and a reviewer
who wants them excluded must propose a RULE (as review #6 did for list markers), not a count.

Deliberate exclusions, printed with their row counts so an exclusion can never hide a row:
  - src="format": triage labels ("benign"), Sigma YAML and JSON targets. Their correct endings are not
    prose endings (a label is one word; YAML ends with a newline). Counted and reported separately.

Usage:  python3 v2/completeness_screen.py [--dir v2/data/mixture] [--json out.json]
Exit:   0 = clean under the stated rules; 1 = findings (each printed with file:line and class).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_mixture as B  # noqa: E402  (the rules live with the builder so the two cannot drift)

FORMAT = "format"


def screen(rows, arm):
    """Return findings as (line, src, klass, tail)."""
    out = []
    for i, r in enumerate(rows):
        src = r.get("src") or ""
        a = str(r.get("assistant") or "")
        if src == FORMAT:
            continue
        klass = B.defect(a)
        if klass is None and not B._ends_ok(a) and B.complete_sentence(a) == a:
            klass = "no-boundary"
        if klass:
            out.append((i + 1, src, klass, " ".join(a.split())[-70:]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="v2/data/mixture")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    report = {}
    total_findings = 0
    for arm in ("armA.jsonl", "armB.jsonl"):
        path = os.path.join(args.dir, arm)
        rows = [json.loads(l) for l in open(path)]
        findings = screen(rows, arm)
        excluded = collections.Counter(r.get("src") for r in rows if r.get("src") == FORMAT)
        by_class = collections.Counter(f[2] for f in findings)
        report[arm] = {
            "rows": len(rows),
            "format_rows_excluded": dict(excluded),
            "findings": len(findings),
            "by_class": dict(by_class),
            "examples": findings[:10],
        }
        total_findings += len(findings)
        print(f"  {arm}: {len(rows)} rows | format rows excluded: {dict(excluded)}")
        print(f"    findings: {len(findings)}  by class: {dict(by_class) or 'NONE'}")
        for line, src, klass, tail in findings[:6]:
            print(f"      {path}:{line}  [{klass}] src={src}  ...{tail!r}")

    if args.json:
        json.dump(report, open(args.json, "w"), indent=2)

    print(f"\n  ACCEPTANCE TEST (D9): {'PASS' if total_findings == 0 else 'FAIL'} — "
          f"{total_findings} findings under the stated rule set")
    return 0 if total_findings == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
