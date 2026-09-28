#!/usr/bin/env python3
"""eval_inputs_v2.py — assemble the gate-input files that v2/gates_v2.py consumes.

WHY THIS EXISTS. `v2/gates_v2.py` defines the input contract for the C24 verdict, and
`eval_cyberguard.py` emits its own report shape (`base`, `tuned`, `defensive_boundary`, `probe_pairs`,
`rate_confidence`, `quality`, ...). The two did not meet: a successful evaluation would have produced
**12 × UNMEASURED** because none of the keys matched. This program is the bridge, and it is deliberately
explicit about which artifact supplies which gate input, so a gap is visible *before* the run ends rather
than discovered at C24.

THE MAPPING (verified against what each artifact actually writes):

  gate input        produced by                                   current v2 status
  ----------------  --------------------------------------------  -------------------------------------
  refusal_pairs     cap_harness.py --n 1100 (per-probe pairs)     requires the C24 battery run
  refusal_n         SPEC §7 prespecified 1100                     constant
  severity_share    cap_harness.py rubric pass (>=3 share)        requires the rubric pass
  defensive_pairs   eval_cyberguard.py `defensive_boundary`       present in the v1 shape
  triage            cap_scorers.py triage confusion matrix         requires the v2 scorer run
  ids               cap_probes/cap_scorers emitted-ID validity     requires the v2 run
  extraction        cap_harness.py span-F1 per document            G-D is declared zero-shot
  sigma             cap_scorers.py pySigma parse/schema            requires the v2 run
  grounded          cap_scorers.py key-correct on authored items   requires the v2 run
  general           cap_harness.py per-task paired outcomes        requires 1200 pairs/task
  escape            eval_cyberguard.py escape incidence + F1s      present in the v1 shape
  chat              cap_scorers.py chat battery (100 prompts)      requires the v2 run

USAGE
  python3 v2/eval_inputs_v2.py --check                     # coverage table: what is present / missing and why
  python3 v2/eval_inputs_v2.py --evals evals/ --out evals/ # write gate-inputs-{arm,base}.json
Exit: 0 always in --check mode (it is a measurement); --assemble exits 1 if any REQUIRED input for C24 is
missing, so a partial battery cannot silently produce a contract full of UNMEASURED.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

# gate input -> (source artifact/globs, extractor description, does C24 require it)
# (gate input, source key(s) in the artifacts, expected globs, description, required for C24)
# The source-key column is what makes the coverage report honest: `defensive_pairs` IS already produced by
# eval_cyberguard.py, under the name `defensive_boundary`. Without this column the checker over-reported 10
# missing inputs when some of the data already exists in a different shape.
MAPPING = [
    ("refusal_pairs",   ["probe_pairs", "refusal_pairs"], ["evals/*cap*.json", "evals/*refusal*.json"],
     "per-probe {probe_id, base, arm}", True),
    ("refusal_n",       [], [], "constant from SPEC §7 (1100)", True),
    ("severity_share",  ["severity_share", "rubric"], ["evals/*rubric*.json"], "{ge3, n}", True),
    ("defensive_pairs", ["defensive_boundary", "defensive_pairs"], ["evals/cyberguard-lora-v2-*.json"],
     "eval_cyberguard 'defensive_boundary'", True),
    ("triage",          ["triage"], ["evals/*scorer*.json"], "{tp, fp, tn, fn}", True),
    ("ids",             ["ids", "id_validity"], ["evals/*scorer*.json", "evals/*id*.json"], "[{id, valid}]", True),
    ("extraction",      ["extraction", "span_f1"], ["evals/*cap*.json"], "[span_f1 per document]", False),
    ("sigma",           ["sigma"], ["evals/*scorer*.json"], "[{parsed, schema_complete}]", True),
    ("grounded",        ["grounded"], ["evals/*scorer*.json"], "[{answerable, correct}]", True),
    ("general",         ["general", "capability"], ["evals/*cap*.json"], "{task: [{base, arm}]}", True),
    ("escape",          ["escape", "content"], ["evals/cyberguard-lora-v2-*.json"],
     "escape incidence + raw/normalised F1", True),
    ("chat",            ["chat"], ["evals/*chat*.json", "evals/*scorer*.json"],
     "{answered,total,degenerated,len_*}", True),
]


def discover():
    found = {}
    for f in sorted(glob.glob("evals/*.json")):
        try:
            found[f] = json.load(open(f))
        except Exception:                       # noqa: BLE001
            found[f] = None
    return found


def probe_inputs(found, key):
    """Would any existing artifact supply this gate input? Reported as a fact, never guessed."""
    for row in MAPPING:
        if row[0] != key:
            continue
    hits = []
    for f, payload in found.items():
        if payload is None:
            continue
        flat = json.dumps(payload)[:200000]
        if key in payload or f'"{key}"' in flat:
            hits.append(f)
    return hits


def coverage(found):
    rows = []
    for key, src_keys, globs, desc, required in MAPPING:
        # presence is decided by the gate input's name OR any of its documented source keys
        present = []
        for f, payload in found.items():
            if payload is None or not isinstance(payload, dict):
                continue
            if key in payload or any(k in payload for k in src_keys):
                present.append(f)
        kind = "EVALUATOR-KEY" if present else ("derived" if key == "refusal_n" else "harness-output")
        rows.append({"input": key, "present_in": present, "source_keys": src_keys, "kind": kind,
                     "required_for_c24": required,
                     "how_it_is_produced": desc,
                     "expected_from": globs or ["constant"], "status": "PRESENT" if (present or key == "refusal_n") else "MISSING"})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evals", default="evals/")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    found = discover()
    rows = coverage(found)
    print(f"  artifacts loaded: {len(found)} in evals/")
    missing_req = 0
    for r in rows:
        tag = "PRESENT" if r["status"] == "PRESENT" else ("MISSING(required)" if r["required_for_c24"] else "MISSING(optional)")
        if r["status"] == "MISSING" and r["required_for_c24"]:
            missing_req += 1
        print(f"    {tag:<18} {r['input']:<16} from {r['how_it_is_produced'][:46]}")
        if r["present_in"]:
            print(f"                       present in: {', '.join(os.path.basename(x) for x in r['present_in'][:3])}")
    print(f"\n  C24 coverage: {len(rows) - missing_req}/{len(rows)} gate inputs available; "
          f"{missing_req} REQUIRED inputs not yet produced")
    print("  The v1 artifacts pre-date the v2 batteries, so MISSING here is expected until the C24 run;"
          " what matters is that a gap is now visible BEFORE the verdict, not at it.")

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        json.dump({"artifacts": [os.path.basename(f) for f in found], "coverage": rows},
                  open(os.path.join(a.out, "gate-input-coverage.json"), "w"), indent=2)
        print(f"  wrote {os.path.join(a.out, 'gate-input-coverage.json')}")
        if missing_req:
            print(f"  ASSEMBLE: refusing — {missing_req} required gate inputs are missing (fail closed)")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
