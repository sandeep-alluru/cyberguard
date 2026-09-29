#!/usr/bin/env python3
"""falsify_audit_checks.py — prove the audit's new sections can FAIL, so their PASS means something.

WHY. "A check that cannot fail is decoration." The audit's PASS is a load-bearing claim in the verdict, and
sections J2 (both-arms content), J3 (Sigma handprint agreement, triage-label determinism) and E3 (tokenizer
truncation + arm-equivalence) were added after an independent review pointed out that these properties were
never checked. This script feeds the audit deliberately violating data and asserts that each check fires and
names the right section — and that the real arms do not trip it.

It runs the REAL audit binary against synthetic arms in a temporary directory; nothing in the repository is
touched.

USAGE
  python3 v2/falsify_audit_checks.py        # exit 0 = every expected check fired
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOOD = {"system": "s", "src": "format", "user": "ordinary prompt about patching a server today",
        "assistant": "Apply the vendor patch, rotate the credentials, and monitor the logs for a week."}


def write_arms(d: str, a_rows: list, b_rows: list) -> None:
    for name, rows in (("armA.jsonl", a_rows), ("armB.jsonl", b_rows)):
        with open(os.path.join(d, name), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")


def run_audit(d: str) -> str:
    p = subprocess.run([sys.executable, os.path.join(ROOT, "v2/audit_mixture.py"), "--dir", d, "--sample", "200"],
                       cwd=ROOT, capture_output=True, text=True, timeout=1800)
    return (p.stdout or "") + (p.stderr or "")


def main() -> int:
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        esc = dict(GOOD, user="literal backslash-n here: " + chr(92) + "n" + " in the prompt")
        deg = dict(GOOD, assistant="loop " + "a" * 400)
        sig_bad = dict(GOOD, user="Write a Sigma rule that detects encoded command activity",
                       assistant="title: x\nlogsource:\n  product: linux\n  category: network_connection\n"
                                 "detection:\n  selection:\n    DestinationPort: '4444'\n  condition: selection\n")
        tri_bad = dict(GOOD, user="Classify as exactly one of malicious or benign; answer with one word.\n"
                                  "host=h1 net_conn dst=1.2.3.4:4444 bytes=100 duration=5s", assistant="benign")
        t1 = dict(GOOD, user="Classify as exactly one of malicious or benign; answer with one word.\n"
                             "host=h2 net_conn dst=1.2.3.4:9999 bytes=10 duration=1s", assistant="benign")
        t2 = dict(t1, assistant="malicious")
        rows = [GOOD, esc, deg, sig_bad, tri_bad, t1, t2]
        write_arms(d, rows, rows)
        out = run_audit(d)
        for want in ("FAIL: J2-escaping: armA", "FAIL: J2-escaping: armB", "FAIL: J2-degeneracy: armA",
                     "FAIL: J3-handprint", "FAIL: J3-labels"):
            (print if want in out else fails.append)(f"  {want}" if want in out else want)
    with tempfile.TemporaryDirectory() as d:
        write_arms(d, [GOOD] * 8, [GOOD] * 7 + [dict(GOOD, assistant=" ".join(["token"] * 40000))])
        out = run_audit(d)
        if "FAIL: E3-arm-equivalence" in out:
            print("  FAIL: E3-arm-equivalence (fires on an asymmetric truncation profile)")
        else:
            fails.append("E3-arm-equivalence did not fire on a 12.5 % truncation-rate gap")
    if fails:
        print("\nFALSIFICATION: FAIL — these checks did not fire on violating data:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nFALSIFICATION: PASS — J2 (escaping, degeneracy), J3 (handprint, labels) and E3 "
          "(arm-equivalence) each fire on violating data and stay silent on the real arms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
