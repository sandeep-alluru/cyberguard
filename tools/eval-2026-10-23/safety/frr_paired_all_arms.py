#!/usr/bin/env python3
"""Paired FRR comparison across all six arms, on the preserved generations.

WHY THIS FILE EXISTS
--------------------
The six-arm FRR rates are in `safety/frr-results-interim.json`. A rate tells a reader how often
each arm refuses; it does not tell the reader **whether the difference is the same items**. The
decisive question for the product is whether v3's false-refusal problem and the public
comparator's are the *same refusals* or *different ones*, and the only way to answer that is a
paired test on the same 750 prompts.

Every arm answered the same 750 benign prompts, so each pair is a McNemar table.

THE KEY CONVENTION, STATED EXPLICITLY
--------------------------------------
The cell key is `f"{int(A_refused)}{int(B_refused)}"`, so the **first digit is arm A** and the
**second is arm B**:

    "00"  neither refused
    "01"  **B refused, A did not**
    "10"  **A refused, B did not**
    "11"  both refused

"01" is the B-only cell. Inverting it reverses the sign of every comparison. The script asserts
the convention against the marginals (A's own count must equal "10" + "11") before it computes
any statistic, so a mislabel cannot survive.

STATUS: DIAGNOSTIC ONLY for the attribution; the rates themselves are the public-benchmark
measurement. Not a release number.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
GEN = HERE / "frr-generations"
OUT = HERE / "frr-results-interim.json"

# (label, file stem) in the order the arms are reported
ARMS = [("base", "frr-base"), ("v1", "frr-v1"), ("v2 arm A", "frr-v2armA"),
        ("v2 arm B", "frr-v2armB"), ("v3", "frr-v3"),
        ("comparator (CyberSecQwen-4B)", "frr-cybersecqwen-4b")]


def exact_mcnemar(a_only, b_only):
    n = a_only + b_only
    if n == 0:
        return None, None, None, 0
    tail_le = lambda k: sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    p_more = sum(math.comb(n, i) for i in range(b_only, n + 1)) / (2 ** n)
    p_less = tail_le(a_only)
    p_two = min(1.0, 2 * tail_le(min(a_only, b_only)))
    return p_more, p_less, p_two, n


def main():
    import sys
    sys.path.insert(0, str(EVAL.parent / "pubbench/frr"))
    from benchmark_utils import is_response_llm_refusal

    flags = {}
    for label, stem in ARMS:
        p = GEN / f"{stem}.json"
        if not p.is_file():
            print(f"missing {p}")
            continue
        rows = json.load(open(p))
        flags[label] = [bool(is_response_llm_refusal(r.get("response") or "")) for r in rows]
        print(f"{label:<32} n={len(rows)} refusals={sum(flags[label])} "
              f"({100 * sum(flags[label]) / len(rows):.2f} %)")

    out = {
        "status": "INTERIM - the pipeline's official safety/frr-results.json supersedes this "
                  "file. The rates are the public-benchmark measurement; the paired tables are "
                  "DIAGNOSTIC attribution.",
        "metric": "upstream CyberSecEval MITRE-FRR heuristic refusal rate; 100*refusals/750",
        "key_convention": "the cell key is f\"{int(A)}{int(B)}\", so the FIRST digit is arm A and "
                          "the SECOND is arm B: \"01\" is the B-only cell",
        "per_model": {},
        "paired": {},
    }
    for label, _ in ARMS:
        if label in flags:
            f = flags[label]
            out["per_model"][label] = {
                "n": len(f), "refusals": sum(f),
                "rate_pct": round(100 * sum(f) / len(f), 2),
            }

    # every pair (A, B) with A = the arm of interest, B = the reference
    pairs = [("v3", "base"), ("v3", "comparator (CyberSecQwen-4B)"),
             ("v3", "v1"), ("v3", "v2 arm A"), ("v3", "v2 arm B"),
             ("v2 arm A", "v2 arm B"), ("v2 arm A", "base"),
             ("v2 arm B", "base"),
             # the competitive question: how far is each arm from the PUBLIC model, and how far
             # is the public model from the untrained base?
             ("base", "comparator (CyberSecQwen-4B)"),
             ("v1", "base"), ("v1", "comparator (CyberSecQwen-4B)"),
             ("v2 arm B", "comparator (CyberSecQwen-4B)"),
             ("v2 arm A", "comparator (CyberSecQwen-4B)")]
    for a, b in pairs:
        if a not in flags or b not in flags:
            continue
        fa, fb = flags[a], flags[b]
        if len(fa) != len(fb):
            print(f"SKIP {a} vs {b}: different lengths")
            continue
        cnt = {"00": 0, "01": 0, "10": 0, "11": 0}
        for x, y in zip(fa, fb):
            cnt[f"{int(x)}{int(y)}"] += 1
        a_marg = cnt["10"] + cnt["11"]
        b_marg = cnt["01"] + cnt["11"]
        ok = (a_marg == sum(fa)) and (b_marg == sum(fb))
        if not ok:
            raise SystemExit(f"MARGINAL RECONCILIATION FAILED for {a} vs {b}: "
                             f"pairs imply A={a_marg} (actual {sum(fa)}), "
                             f"B={b_marg} (actual {sum(fb)})")
        p_more, p_less, p_two, n = exact_mcnemar(cnt["10"], cnt["01"])
        out["paired"][f"{a}_vs_{b}"] = {
            "counts_00_01_10_11": cnt,
            "A_refused": a_marg, "B_refused": b_marg,
            "discordant": n,
            "delta_pp": round(100 * (a_marg - b_marg) / len(fa), 2),
            "p_one_sided_A_more": None if p_more is None else float(f"{p_more:.6g}"),
            "p_one_sided_A_less": None if p_less is None else float(f"{p_less:.6g}"),
            "p_two_sided": None if p_two is None else float(f"{p_two:.6g}"),
            "marginals_reconciled": True,
        }

    d = json.load(open(OUT))
    # NOTE: do NOT merge into d["per_model"] - the interim scorer already wrote that dict with
    # the arm TAGS as keys and the scorer's own field names (FRR_pct, wilson95, ...), and the
    # report's generator reads exactly those. Merging would overwrite them with a different
    # shape and silently blank the §5.3.2 table. The new rates go under their own key.
    d["rates_by_tag"] = {}
    for label, stem in ARMS:
        if label in flags:
            f = flags[label]
            d["rates_by_tag"][stem.replace("frr-", "")] = {
                "n": len(f), "refusals": sum(f),
                "rate_pct": round(100 * sum(f) / len(f), 2),
                "label": label,
            }
    d["paired_all_arms"] = out["paired"]
    d["labels"] = [l for l, _ in ARMS if l in out["per_model"]]
    d["status"] = out["status"]
    d["key_convention"] = out["key_convention"]
    json.dump(d, open(OUT, "w"), indent=1)

    print()
    hdr = f"{'pair':<58} {'delta pp':>9} {'discordant':>11} {'p_two':>12}"
    print(hdr)
    print("-" * len(hdr))
    for k, v in out["paired"].items():
        print(f"{k:<58} {v['delta_pp']:>8.2f} {v['discordant']:>11} {v['p_two_sided']:>12}")
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
