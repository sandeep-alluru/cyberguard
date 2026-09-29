#!/usr/bin/env python3
"""check_registration_rules.py — the acceptance rules are PRE-REGISTERED; the implementation must not drift.

WHY. SPEC §7 clause 2 fixes the two confirmatory claims' bars and the §7 gate table fixes each gate's n and
threshold. A verdict decided on a different rule than the one registered is not a verdict — and nothing stopped a
later edit to a number in `gates_v2.py` from silently moving a bar. `v2/data/mixture/registered-rules.receipt.json`
is the frozen transcription (made by reading the SPEC), and this compares the implementation against it.

  usage: python3 v2/check_registration_rules.py [--gates-file v2/gates_v2.py]
exit 0 = every registered rule matches the implementation
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECEIPT = os.path.join(ROOT, "v2/data/mixture/registered-rules.receipt.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gates-file", default=os.path.join(ROOT, "v2/gates_v2.py"))
    a = ap.parse_args()
    reg = json.load(open(RECEIPT))
    spec = importlib.util.spec_from_file_location("gv_check", a.gates_file)
    gv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gv)
    src = open(a.gates_file, encoding="utf-8").read()

    fails = []
    impl = {g[0]: g for g in gv.GATES}
    for r in reg["gates"]:
        g = impl.get(r["id"])
        if g is None:
            fails.append(f"gate {r['id']!r} is registered but absent from the implementation")
            continue
        for field, idx in (("n_req", 1), ("endpoint", 2), ("bar", 3), ("direction", 4), ("how", 5)):
            if g[idx] != r[field]:
                fails.append(f"{r['id']}: registered {field}={r[field]!r}, implemented {g[idx]!r}")
    for r in reg["claims"]:
        if r["source_literal"] not in src:
            fails.append(f"{r['id']}: the registered rule literal {r['source_literal']!r} is absent from "
                         f"{os.path.basename(a.gates_file)} — the claim would be decided on a different rule")
    if fails:
        print("REGISTRATION-RULES: FAIL — the implementation does not match the pre-registered rules")
        for f in fails:
            print(f"  {f}")
        return 1
    print(f"REGISTRATION-RULES: PASS — {len(reg['gates'])} gate rules and {len(reg['claims'])} claim rules match "
          f"the registration frozen at spec {reg['spec_sha256_at_freeze'][:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
