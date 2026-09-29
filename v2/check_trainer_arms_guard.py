#!/usr/bin/env python3
"""check_trainer_arms_guard.py — an ARMS-mode crash must not be reintroducible.

`_canon` is bound only inside the non-ARMS branch. Every use OUTSIDE that block must be guarded
(`if not ARMS else ...`): an unguarded reference crashed both arm runs at the epoch-1 boundary on 2026-09-28
21:25/21:26, after the adapters had been saved - the most expensive defect of the window.

Block membership is computed from indentation, so the legitimate uses inside the non-ARMS branch are exempt.
"""
import os
import re
import sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train_cyberguard.py")
lines = open(P, encoding="utf-8").read().splitlines()
start = next((i for i, l in enumerate(lines) if re.match(r"^\s*_canon\s*=", l)), None)
if start is None:
    sys.exit("ARMS-GUARD CHECK: FAIL - _canon is never assigned; the file changed shape")
indent = len(lines[start]) - len(lines[start].lstrip())
# The suite ends at a STRICTLY lesser indent (the `else:` header is already outside it); same-indent
# siblings like the two uses on lines 140/143 are still INSIDE the branch. Using <= here was the bug.
end = next((i for i in range(start + 1, len(lines))
            if lines[i].strip() and (len(lines[i]) - len(lines[i].lstrip())) < indent), len(lines))
in_branch = set(range(start, end))
bad = []
for n, line in enumerate(lines, 1):
    s = line.strip()
    if "_canon" not in s or s.startswith("#") or (n - 1) in in_branch:
        continue
    if "if not ARMS else" in s:
        continue
    bad.append((n, s[:100]))
if bad:
    print("ARMS-GUARD CHECK: FAIL - unguarded _canon use outside the non-ARMS branch")
    for n, s in bad:
        print(f"  line {n}: {s}")
    sys.exit(1)
print(f"ARMS-GUARD CHECK: PASS - _canon is used only inside its branch (lines {start+1}-{end}) or guarded")
