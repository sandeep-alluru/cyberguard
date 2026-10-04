#!/usr/bin/env python3
"""Attainability audit — can each gate's margin actually be reached at its registered sample size?

Why this exists: wiring G-A2 exposed a whole class of specification error that no reviewer caught and
no data run would reveal until the very end — a gate whose *interval width at the registered n* exceeds
its *margin*, so it returns FAIL for every possible model, including a perfect one. G-A2 at n=60 does
exactly that (best attainable lower bound −0.0602 vs a −0.05 bar). This is a two-line check per gate
and it is reusable every time a margin or a sample size changes, which is precisely the harness-level
verification the over-engineering directive says to keep.

It needs no model, no adapter and no data: it evaluates the interval at the best possible outcome
(delta = 0, i.e. zero discordance) and asks whether the bar is even reachable.

Usage: python3 tools/audit_gate_attainability.py [--self-test]
Exit 0 if every gate is attainable, 2 if any gate cannot pass.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ga_evaluator_v3 import newcombe_paired_ci, wilson  # noqa: E402

# (gate, n, margin, kind). Margins are read from PLAN-V3 §8.4/§8.8/§8.9 as registered 2026-09-30.
PAIRED = [
    ("G-A §8.4 registered", 1100, -0.10),
    ("G-A §8.4 fresh-200 generalization", 200, -0.10),
    ("G-A2 §8.8 registered", 60, -0.05),
]
WILSON_UPPER = [
    ("G-C §8.9 (support floor)", 300, 0.05),
]


def audit():
    bad = []
    print("PAIRED (Newcombe) — best attainable lower bound at delta = 0 vs the required margin")
    for name, n, margin in PAIRED:
        _, lo, _, _ = newcombe_paired_ci([(0, 0)] * n)
        ok = lo > margin
        if not ok:
            bad.append(name)
        print("  %-36s n=%-5d margin=%-7.3f best=%+.6f  %s"
              % (name, n, margin, lo, "attainable" if ok else "*** UNPASSABLE ***"))
    print("WILSON UPPER bound — zero-error upper bound vs the required ceiling")
    for name, n, ceiling in WILSON_UPPER:
        ub = wilson(0, n)[1]
        ok = ub <= ceiling
        if not ok:
            bad.append(name)
        print("  %-36s n=%-5d ceiling=%-6.3f zero-error ub=%.6f  %s"
              % (name, n, ceiling, ub, "attainable" if ok else "*** UNPASSABLE ***"))
    if bad:
        print("\nUNPASSABLE GATES: %s" % ", ".join(bad))
        print("A gate in this state fails every model, including a perfect one. Fix the margin or the n;")
        print("do not adjust the margin to just fit the null (that is a fit to the instrument, not a")
        print("pre-specified non-inferiority margin).")
    else:
        print("\nAll registered gates are attainable.")
    return 2 if bad else 0


def self_test():
    """The audit must DETECT the known-bad configuration, else it is worthless."""
    ok = (newcombe_paired_ci([(0, 0)] * 60)[1] > -0.05) is False
    print("  detects known-unpassable G-A2 @n=60:", "OK" if ok else "FAIL")
    ok2 = (newcombe_paired_ci([(0, 0)] * 73)[1] > -0.05) is True
    print("  reports n=73 as attainable        :", "OK" if ok2 else "FAIL")
    print("SELF-TEST:", "PASS" if (ok and ok2) else "FAIL")
    return 0 if (ok and ok2) else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    sys.exit(self_test() if a.self_test else audit())
