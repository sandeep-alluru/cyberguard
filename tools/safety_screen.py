#!/usr/bin/env python3
# PARKED (rev 11, over-engineering directive): measured 0/11 recall on the verified unsafe
# rows, so it is unusable, and it only served Option B (not chosen). Kept for the record; do not run.

"""CyberGuard v3 — deterministic safety screen for the teacher-trail block (A7 remediation).

Why: the A7 audit found 11/200 sampled answers giving operational offensive material
for Fenrir dual-use prompts. Admitting the block requires excluding those rows, and
exclusion needs a screen that runs over all 7,000 rows, cheaply and repeatably.

This reuses the repo's existing, unit-tested safety contract rather than inventing a
new heuristic: `cyberguard_contract.teaches_attack_production` (narrow capability list,
production-request requirement, and defensive framing always wins — see its docstring
for why a vocabulary match was rejected as an approach). Refusal detection reuses the
fixture-verified §8.4 rule in `tools/refusal_rule_v3.py`.

Risk definition per row (answer text = the part after `</think>`):
  * prompt_asks    — the prompt asks for an attack capability to be built
  * answer_complies— the answer itself reads as attack-production material
  * refused        — the answer carries refusal language (§8.4 rule)
  * FLAGGED        — answer_complies and not refused            (answer-side production)
  * HIGH_RISK      — prompt_asks and answer_complies and not refused

`--crosscheck` re-derives the A7 audit's sample (same seed/logic) and reports how many
of the audit's hand-verified unsafe rows this screen catches — a recall check, so the
screen is not trusted blindly.
"""
import argparse
import glob
import json
import os
import random
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))

import cyberguard_contract as C  # noqa: E402
from refusal_rule_v3 import refusal_present  # noqa: E402

BASE = os.path.expanduser("~/AgentHub/cyberguard/data/v3/trails-30")
TRAILS = os.path.join(BASE, "trails_deepseek_7k.jsonl")
PROMPTS = os.path.join(BASE, "prompts-7k.jsonl")
RECEIPT = os.path.join(BASE, "SAFETY-SCREEN-RECEIPT.json")
MARKER = "</think>"


def load():
    src = {}
    with open(PROMPTS) as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                src[d["id"]] = d.get("src", "?")
    rows = []
    with open(TRAILS) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows, src


def answer_of(trail):
    return trail.split(MARKER, 1)[1].strip() if MARKER in trail else (trail or "").strip()


def screen_row(r, src):
    ans = answer_of(r["trail"])
    prompt_asks = bool(C.teaches_attack_production(r["prompt"]))
    answer_complies = bool(C.teaches_attack_production(ans))
    refused = refusal_present(ans)
    flagged = answer_complies and not refused
    return {"id": r["id"], "src": src.get(r["id"], "?"),
            "prompt_asks": prompt_asks, "answer_complies": answer_complies,
            "refused": refused, "flagged": flagged,
            "high_risk": prompt_asks and flagged,
            "answer_chars": len(ans)}


def audit_sample_ids(rows, src, n=200, seed=20260930):
    """Reproduce content_audit.py's stratified draw so audit keys map back to ids."""
    by_src = {}
    for r in rows:
        by_src.setdefault(src.get(r["id"], "?"), []).append(r)
    rng = random.Random(seed)
    total = len(rows)
    sample = []
    for s, items in sorted(by_src.items()):
        k = max(1, round(n * len(items) / total))
        rng.shuffle(items)
        sample.extend(items[:k])
    rng.shuffle(sample)
    sample = sample[:n] if len(sample) > n else sample
    return {"r%03d" % i: r["id"] for i, r in enumerate(sample)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crosscheck", action="store_true")
    args = ap.parse_args()

    rows, src = load()
    results = [screen_row(r, src) for r in rows]

    flagged = [r for r in results if r["flagged"]]
    high = [r for r in results if r["high_risk"]]
    asks = [r for r in results if r["prompt_asks"]]
    refused = [r for r in results if r["refused"]]

    by_src = {}
    for r in high:
        by_src[r["src"]] = by_src.get(r["src"], 0) + 1

    print("rows screened            : %d" % len(results))
    print("prompts asking for attack production : %d (%.2f%%)"
          % (len(asks), 100 * len(asks) / len(results)))
    print("answers carrying refusal language    : %d (%.2f%%)"
          % (len(refused), 100 * len(refused) / len(results)))
    print("answers reading as attack production : %d (%.2f%%)"
          % (len(flagged), 100 * len(flagged) / len(results)))
    print("HIGH_RISK (ask + comply + no refusal): %d (%.2f%%)  by src: %s"
          % (len(high), 100 * len(high) / len(results), by_src))

    cross = None
    if args.crosscheck:
        key2id = audit_sample_ids(rows, src)
        scores = {}
        for f in sorted(glob.glob(os.path.join(BASE, "supervisor", "audit-codex", "batch-*.txt"))):
            raw = open(f).read()
            m = re.search(r"\[[\s\S]*\]", raw)
            if m:
                try:
                    for o in json.loads(m.group(0)):
                        scores[o["key"]] = o
                except Exception:
                    pass
        astra_unsafe = [key2id[k] for k, v in scores.items() if v.get("unsafe") and k in key2id]
        mine = {r["id"] for r in results if r["flagged"]}
        caught = [i for i in astra_unsafe if i in mine]
        cross = {"astra_unsafe_in_sample": len(astra_unsafe),
                 "caught_by_screen": len(caught),
                 "missed": [i for i in astra_unsafe if i not in mine]}
        print("--- recall cross-check against the A7 audit ---")
        print("Astra-flagged unsafe in sample : %d" % len(astra_unsafe))
        print("caught by this screen          : %d" % len(caught))
        print("missed ids                     : %s" % cross["missed"])

    receipt = {
        "trail_file": TRAILS,
        "rows_screened": len(results),
        "prompt_asks": len(asks),
        "answers_refusing": len(refused),
        "answers_attack_production": len(flagged),
        "high_risk": len(high),
        "high_risk_by_src": by_src,
        "high_risk_ids": [r["id"] for r in high],
        "flagged_ids": [r["id"] for r in flagged],
        "screen": "cyberguard_contract.teaches_attack_production + tools/refusal_rule_v3.refusal_present",
        "crosscheck": cross,
    }
    with open(RECEIPT, "w") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    print("receipt: %s" % RECEIPT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
