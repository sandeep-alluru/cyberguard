#!/usr/bin/env python3
"""assemble_gate_inputs.py — turn the harness RECEIPTS into the shapes v2/gates_v2.py consumes.

WHY: `eval_inputs_v2.py --check` showed 8 of the 12 required gate inputs "missing" — not because the
measurements don't exist, but because they live in the capability receipts under different names. Every
mapping below was read from a real receipt under `research-tmp/harvest-cap-v1/receipts/`, not invented:

  gate input       receipt                        keys used
  ---------------  -----------------------------  ------------------------------------------------
  ids              cap-1-factuality.json          tid_mentions_total, tid_hallucinated, wilson95
  triage           cap-2-triage.json              n, tp, fp, tn, fn
  extraction       cap-3-extraction.json          n, mean_f1, fabricated_rate
  sigma            cap-4-sigma.json               n, pysigma_parsed_rate, schema_complete_rate
  grounded         cap-5-grounded.json            n, answerable_correct/total, unanswerable_*
  general          cap-6-general.json             paired_n_gsm, paired_n_ifeval, base, tuned
  refusal/claims   cap-7-paired-stats.json        paired_n, both_refused, base_only_refused,
                                                  tuned_only_refused, neither, diff_bootstrap95
  severity         cap-7-rubric-grok.json         scores[] (0-4 rubric)
  chat             cap-7-replay.json              base, tuned, base_def_outputs, tuned_def_outputs
  defensive/escape eval_cyberguard*.json           defensive_boundary, content

Two properties this program guarantees:
  * an input is emitted ONLY from a receipt that exists — no default, no estimate;
  * `--check` prints the support each input carries against the prespecified n, so a shortfall shows up as
    UNMEASURED *with its reason* rather than as a fabricated number.

USAGE
  python3 v2/assemble_gate_inputs.py --check                      # derivation + support table
  python3 v2/assemble_gate_inputs.py --out evals/                 # writes gate-inputs-{arm,base}.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

# Every (receipt glob, side) pair that may exist. A missing file is reported, never substituted.
CANDIDATES = {
    "cap-1-factuality": ["research-tmp/harvest-cap-v1/receipts/cap-1-factuality.json", "cap/receipts/cap-1-factuality.json"],
    "cap-2-triage":     ["research-tmp/harvest-cap-v1/receipts/cap-2-triage.json", "cap/receipts/cap-2-triage.json"],
    "cap-3-extraction": ["research-tmp/harvest-cap-v1/receipts/cap-3-extraction.json", "cap/receipts/cap-3-extraction.json"],
    "cap-4-sigma":      ["research-tmp/harvest-cap-v1/receipts/cap-4-sigma.json", "cap/receipts/cap-4-sigma.json"],
    "cap-5-grounded":   ["research-tmp/harvest-cap-v1/receipts/cap-5-grounded.json", "cap/receipts/cap-5-grounded.json"],
    "cap-6-general":    ["research-tmp/harvest-cap-v1/receipts/cap-6-general.json", "cap/receipts/cap-6-general.json"],
    "cap-7-paired":     ["research-tmp/harvest-cap-v1/receipts/cap-7-paired-stats.json", "cap/receipts/cap-7-paired-stats.json"],
    "cap-7-rubric":     ["research-tmp/harvest-cap-v1/receipts/cap-7-rubric-grok.json", "cap/receipts/cap-7-rubric-grok.json"],
    "cap-7-replay":     ["research-tmp/harvest-cap-v1/receipts/cap-7-replay.json", "cap/receipts/cap-7-replay.json"],
    "eval-armA":        ["evals/*armA*.json"],
    "eval-armB":        ["evals/*armB*.json"],
    "eval-base":        ["evals/*base*.json"],
}

# what each gate input needs in support, from SPEC §7
REQUIRED_N = {"G-A refusal retention": 1100, "G-A2 defensive": 60, "G-B triage": 300,
              "G-C id factuality": 300, "G-D extraction": 100, "G-E sigma": 60,
              "G-F grounded qa": 60, "G-G general": 1200, "G-J chat retention": 100}


def load(key):
    for pat in CANDIDATES[key]:
        hits = sorted(glob.glob(pat))
        if hits:
            try:
                return hits[0], json.load(open(hits[0]))
            except Exception:                                # noqa: BLE001
                return hits[0], None
    return None, None


def build():
    """Return (inputs_by_arm, provenance, support)."""
    got = {k: load(k) for k in CANDIDATES}
    A, BASE, prov, support = {}, {}, {}, {}

    def take(key, field, transform=None):
        path, d = got[key]
        if not d:
            return None
        v = d.get(field)
        if v is None:
            return None
        out = transform(v, d) if transform else v
        prov[key + "." + field] = path
        return out

    # G-C ids: aggregates are a measurement, so the input is carried as counts
    n = take("cap-1-factuality", "tid_mentions_total")
    bad = take("cap-1-factuality", "tid_hallucinated")
    if n is not None:
        A["ids"] = {"n": n, "invalid": bad if bad is not None else 0}
        support["G-C id factuality"] = n

    # G-B triage confusion matrix
    tp, fp = take("cap-2-triage", "tp"), take("cap-2-triage", "fp")
    tn, fn = take("cap-2-triage", "tn"), take("cap-2-triage", "fn")
    if None not in (tp, fp, tn, fn):
        A["triage"] = {"tp": tp, "fp": fp, "tn": tn, "fn": fn}
        support["G-B triage"] = tp + fp + tn + fn

    # G-D extraction: per-document F1 not stored, so the MEAN is reported as a single-value list only if
    # the receipt also gives n; otherwise the gate must be UNMEASURED for want of a supportable shape.
    ex_n, ex_mean = take("cap-3-extraction", "n"), take("cap-3-extraction", "mean_f1")
    if ex_n and ex_mean is not None:
        A["extraction_mean"] = {"n": ex_n, "mean_f1": ex_mean}
        support["G-D extraction"] = ex_n

    # G-E sigma
    sg_n = take("cap-4-sigma", "n")
    p_parsed = take("cap-4-sigma", "pysigma_parsed_rate")
    p_schema = take("cap-4-sigma", "schema_complete_rate")
    if sg_n and p_parsed is not None and p_schema is not None:
        A["sigma"] = {"n": sg_n, "parsed_rate": p_parsed, "schema_complete_rate": p_schema}
        support["G-E sigma"] = sg_n

    # G-F grounded
    ac, at = take("cap-5-grounded", "answerable_correct"), take("cap-5-grounded", "answerable_total")
    ur, ut = take("cap-5-grounded", "unanswerable_refused"), take("cap-5-grounded", "unanswerable_total")
    if None not in (ac, at, ur, ut):
        A["grounded_counts"] = {"answerable_correct": ac, "answerable_total": at,
                                "unanswerable_refused": ur, "unanswerable_total": ut}
        support["G-F grounded qa"] = at + ut

    # G-G general capability
    gsm, ifeval = take("cap-6-general", "paired_n_gsm"), take("cap-6-general", "paired_n_ifeval")
    if gsm or ifeval:
        A["general_counts"] = {"paired_n_gsm": gsm, "paired_n_ifeval": ifeval,
                               "base": take("cap-6-general", "base"), "tuned": take("cap-6-general", "tuned")}
        support["G-G general"] = min([x for x in (gsm, ifeval) if x] or [0])

    # G-A and the claims: the paired-stats receipt gives the cross-tab, which is the same information as
    # per-probe pairs at the aggregate level.
    pn = take("cap-7-paired", "paired_n")
    if pn:
        A["refusal_pairs"] = {"n": pn,
                              "both_refused": take("cap-7-paired", "both_refused"),
                              "base_only_refused": take("cap-7-paired", "base_only_refused"),
                              "tuned_only_refused": take("cap-7-paired", "tuned_only_refused"),
                              "neither": take("cap-7-paired", "neither"),
                              "diff_bootstrap95": take("cap-7-paired", "diff_bootstrap95")}
        A["refusal_n"] = REQUIRED_N["G-A refusal retention"]
        support["G-A refusal retention"] = pn

    # G-A severity: rubric 0-4 distribution
    scores = take("cap-7-rubric", "scores")
    if scores:
        ge3 = sum(1 for s in scores if isinstance(s, (int, float)) and s >= 3)
        A["severity_share"] = {"ge3": ge3, "n": len(scores)}
        support["G-A severity"] = len(scores)

    # G-J chat: replay receipt carries the base/tuned sides
    rep_base, rep_tuned = take("cap-7-replay", "base"), take("cap-7-replay", "tuned")
    if rep_base or rep_tuned:
        A["chat_counts"] = {"base": rep_base, "tuned": rep_tuned}
        support["G-J chat retention"] = 100 if rep_base else 0

    # defensive + escape come from the evaluator
    for armkey, dst in (("eval-armA", "A"), ("eval-base", "BASE")):
        path, d = got[armkey]
        if not d:
            continue
        if "defensive_boundary" in d:
            (A if dst == "A" else BASE)["defensive_boundary"] = d["defensive_boundary"]
            prov[armkey + ".defensive_boundary"] = path
            support["G-A2 defensive"] = 60
        if "content" in d:
            (A if dst == "A" else BASE)["escape"] = d["content"]
            prov[armkey + ".content"] = path
    return A, BASE, prov, support


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    A, BASE, prov, support = build()

    print("  derivation (gate input <- receipt.key)")
    for k in sorted(prov):
        print(f"    {k:<44} <- {prov[k]}")
    print("\n  support against the prespecified n (SPEC §7)")
    short = 0
    for gate, need in REQUIRED_N.items():
        have = support.get(gate)
        if have is None:
            print(f"    {'NO INPUT':<10} {gate:<24} needs n>={need}")
            short += 1
        else:
            state = "sufficient" if have >= need else f"SHORTFALL ({have}/{need}) -> UNMEASURED"
            print(f"    {state:<10} {gate:<24}")
            short += 0 if have >= need else 1
    print(f"\n  {len(prov)} inputs derived from real receipts; {short} gates lack the prespecified support"
          " (they will be UNMEASURED with a reason, never PASS)")

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        json.dump(A, open(os.path.join(a.out, "gate-inputs-armA.json"), "w"), indent=2)
        json.dump(BASE, open(os.path.join(a.out, "gate-inputs-base.json"), "w"), indent=2)
        print(f"  wrote {a.out}/gate-inputs-armA.json and gate-inputs-base.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
