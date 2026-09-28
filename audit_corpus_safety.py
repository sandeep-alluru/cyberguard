#!/usr/bin/env python3
"""audit_corpus_safety.py — what does the training corpus teach, and what does the filter drop?

The question to answer BEFORE spending GPU hours, because the answer decides the data mixture and
cannot be fixed afterwards.

WHY THIS FILE LOOKS THE WAY IT DOES. The first version matched attack VOCABULARY in the user
prompt and reported 22% "offensive asks". That number was wrong, and the samples that disproved
it were in its own output:

    "Analyze encrypted C2 channels using TLS. Discuss traffic analysis techniques to
     fingerprint malicious infrastructure."
    "Analyze SQL injection variants in web applications. Propose a taint analysis-based
     static checker."

Those are BLUE-TEAM asks — the attack is the TOPIC, not the request. A vocabulary match cannot
tell "explain how attackers use process injection so I can detect it" from "write me a process
injector"; both contain the same words. Reporting the first as a corpus-safety risk would have
triggered a pointless filtering pass and presented a wrong finding as a measurement.

The corpus template is "Describe an approach to implement <TECHNIQUE> ...", and the TECHNIQUE
slot mixes defensive subjects with genuine attack capabilities. So intent is the JOINT of three
things — attack capability, production request, and absence of defensive framing — and the test
lives in cyberguard_contract.teaches_attack_production, shared with the loader and unit-tested in
test_contract.py.

This reports the corpus both ways (before and after the filter), samples the DROPPED rows so the
filter's decisions can be eyeballed rather than trusted, and writes a receipt.

CPU only. Run:  python audit_corpus_safety.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROOT = Path(os.environ.get("CYBERGUARD_ROOT", Path.home() / "cyberguard"))
DATA = ROOT / "data" / "trendyol-cybersec" / "CyberSec-Dataset_escaped.jsonl"
SAMPLE_N = int(os.environ.get("SAMPLE_N", 10))

import cyberguard_data as cgdata  # noqa: E402
import cyberguard_contract as C  # noqa: E402


def main() -> int:
    os.environ["DROP_ATTACK_PRODUCTION"] = "0"
    full = cgdata.load_rows(DATA)
    os.environ["DROP_ATTACK_PRODUCTION"] = "1"
    kept = cgdata.load_rows(DATA)

    kept_keys = {cgdata.norm_prompt(r["user"]) for r in kept}
    dropped = [r for r in full if cgdata.norm_prompt(r["user"]) not in kept_keys]

    n = len(full)
    topic = [r for r in full if C.ATTACK_CAPABILITY.search(r["user"])]
    analysis = [r for r in full
                if C.ATTACK_CAPABILITY.search(r["user"])
                and not C.teaches_attack_production(r["user"])]

    code_in_dropped = sum(1 for r in dropped if "```" in r["assistant"] or "import " in r["assistant"])

    print(f"corpus rows (prompt-deduped)      : {n}")
    print()
    print("=== the filter ===")
    print(f"  rows naming an attack capability: {len(topic):6d}  {len(topic)/max(1,n):6.2%}")
    print(f"  of those, analysis/blue-team     : {len(analysis):6d}  "
          f"{len(analysis)/max(1,n):6.2%}   <- KEPT")
    print(f"  DROPPED (teach attack production): {len(dropped):6d}  "
          f"{len(dropped)/max(1,n):6.2%}")
    print(f"  retained corpus                  : {len(kept):6d}")
    print(f"  dropped rows whose answer has code: {code_in_dropped}")

    print()
    print(f"=== sample of DROPPED rows, verbatim ({min(SAMPLE_N, len(dropped))} shown) ===")
    print("    (each must read as a request to BUILD an attack capability)")
    for r in dropped[:SAMPLE_N]:
        print(f"  [{len(r['assistant']):5d}ch] {r['user'][:132]}")

    # A dropped row that also carries defensive framing would mean the filter is over-reaching.
    over = [r for r in dropped if C.DEFENSIVE_FRAME.search(r["user"])]
    print()
    print(f"=== over-reach check ===\n  dropped rows that also contain defensive framing: {len(over)}")
    for r in over[:3]:
        print(f"    {r['user'][:120]}")

    print()
    print("=== read ===")
    share = len(dropped) / max(1, n)
    if share > 0.10:
        print(f"  ALERT: {share:.1%} of the corpus asks for attack material. The mixture needs real")
        print("         work, not a filter — that is a large fraction of the training signal.")
    else:
        print(f"  OK: {share:.2%} of the corpus teaches attack production ({len(dropped)} rows),")
        print(f"      while {len(analysis)/max(1,n):.1%} of rows discuss attacks in order to detect,")
        print("      analyse or defend against them. The corpus is analysis-framed and consistent")
        print("      with the goal once the small attack-production bucket is removed.")

    out = ROOT / "receipts" / "corpus-safety-audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "rows_before_filter": n,
            "rows_after_filter": len(kept),
            "dropped_attack_production": len(dropped),
            "dropped_share": round(share, 6),
            "attack_capability_topic_rows": len(topic),
            "attack_analysis_kept": len(analysis),
            "dropped_with_defensive_framing": len(over),
            "dropped_prompts": [r["user"] for r in dropped],
        }, f, indent=1)
    print(f"  receipt -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
