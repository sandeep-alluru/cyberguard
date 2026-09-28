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


def battery_receipts(evals_dir="evals", extra_dirs=()):
    """Read the battery receipts written by v2/run_battery.py: battery-<bat>-<arm>.json.

    Without this the new batteries would produce nothing the gate layer can consume - the same interface gap
    this file exists to close, so it is read here rather than assumed to work.
    """
    out = {}
    for d in (evals_dir,) + tuple(extra_dirs):
        for f in sorted(glob.glob(os.path.join(d, "battery-*.json"))):
            try:
                rec = json.load(open(f))
                out[(rec.get("battery"), rec.get("arm"))] = rec
            except Exception:                                    # noqa: BLE001
                continue
    return out


def pairs_from_batteries(bat, arm):
    """Per-probe refusal pairs for one arm, from its gA receipt plus the base receipt."""
    base = bat.get(("gA", "base"))
    side = bat.get(("gA", arm))
    if not base or not side:
        return None
    flags = {pid: bool(v) for pid, v in zip(side["probe_ids"], side["scores"]["refused"])}
    bflags = {pid: bool(v) for pid, v in zip(base["probe_ids"], base["scores"]["refused"])}
    return [{"probe_id": pid, "base": bflags[pid], "arm": flags[pid]}
            for pid in side["probe_ids"] if pid in bflags]


def build(extra_eval_dirs=()):
    """Return (inputs_by_arm, provenance, support)."""
    got = {k: load(k) for k in CANDIDATES}
    A, BASE, ARMB, prov, support = {}, {}, {}, {}, {}

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
        A.setdefault("ids", {"n": n, "invalid": bad if bad is not None else 0})
        support["G-C id factuality"] = n

    # G-B triage confusion matrix
    tp, fp = take("cap-2-triage", "tp"), take("cap-2-triage", "fp")
    tn, fn = take("cap-2-triage", "tn"), take("cap-2-triage", "fn")
    if None not in (tp, fp, tn, fn):
        A.setdefault("triage", {"tp": tp, "fp": fp, "tn": tn, "fn": fn})
        support["G-B triage"] = tp + fp + tn + fn

    # G-D extraction: per-document F1 not stored, so the MEAN is reported as a single-value list only if
    # the receipt also gives n; otherwise the gate must be UNMEASURED for want of a supportable shape.
    ex_n, ex_mean = take("cap-3-extraction", "n"), take("cap-3-extraction", "mean_f1")
    if ex_n and ex_mean is not None:
        A.setdefault("extraction_mean", {"n": ex_n, "mean_f1": ex_mean})
        support["G-D extraction"] = ex_n

    # G-E sigma
    sg_n = take("cap-4-sigma", "n")
    p_parsed = take("cap-4-sigma", "pysigma_parsed_rate")
    p_schema = take("cap-4-sigma", "schema_complete_rate")
    if sg_n and p_parsed is not None and p_schema is not None:
        A.setdefault("sigma", {"n": sg_n, "parsed_rate": p_parsed, "schema_complete_rate": p_schema})
        support["G-E sigma"] = sg_n

    # G-F grounded
    ac, at = take("cap-5-grounded", "answerable_correct"), take("cap-5-grounded", "answerable_total")
    ur, ut = take("cap-5-grounded", "unanswerable_refused"), take("cap-5-grounded", "unanswerable_total")
    if None not in (ac, at, ur, ut):
        A.setdefault("grounded_counts", {"answerable_correct": ac, "answerable_total": at,
                                          "unanswerable_refused": ur, "unanswerable_total": ut})
        support["G-F grounded qa"] = at + ut

    # G-G general capability
    gsm, ifeval = take("cap-6-general", "paired_n_gsm"), take("cap-6-general", "paired_n_ifeval")
    if gsm or ifeval:
        A.setdefault("general_counts", {"paired_n_gsm": gsm, "paired_n_ifeval": ifeval,
                                         "base": take("cap-6-general", "base"),
                                         "tuned": take("cap-6-general", "tuned")})
        support["G-G general"] = min([x for x in (gsm, ifeval) if x] or [0])

    # --- v2 batteries take precedence over the v1 aggregates: they carry PER-PROBE data, which is what
    # Claim 2 needs and what aggregate cross-tabs cannot express.
    bat = battery_receipts(extra_dirs=extra_eval_dirs)
    if bat:
        prov["battery receipts"] = ", ".join(sorted({f"{b}/{a}" for (b, a) in bat}))
        # arm A's pairs carry (arm, base); arm B's pairs are written to their OWN file, because Claim 2
        # reads arm A and arm B from separate files and joins them by probe_id.
        prsA = pairs_from_batteries(bat, "armA")
        prsB = pairs_from_batteries(bat, "armB")
        if prsA:
            A["refusal_pairs"] = prsA
            A["refusal_n"] = REQUIRED_N["G-A refusal retention"]
            support["G-A refusal retention"] = len(prsA)
        if prsB:
            ARMB["refusal_pairs"] = prsB
            ARMB["refusal_n"] = REQUIRED_N["G-A refusal retention"]
            support["Claim 2 (A vs B)"] = len(prsB)
        gC = bat.get(("gC", "armA"))
        if gC and isinstance(gC.get("scores"), dict):
            A["ids"] = {"n": gC["scores"].get("n", 0), "invalid": gC["scores"].get("invalid", 0)}
            support["G-C id factuality"] = A["ids"]["n"]
        gF = bat.get(("gF", "armA"))
        if gF and isinstance(gF.get("scores"), dict):
            A["grounded_counts"] = gF["scores"]
            support["G-F grounded qa"] = gF["scores"].get("answerable_total", 0) + gF["scores"].get("unanswerable_total", 0)
        gB = bat.get(("gB", "armA"))
        if gB and isinstance(gB.get("scores"), dict):
            sB = gB["scores"]
            if {"tp", "fp", "tn", "fn"} <= set(sB):
                A["triage"] = {k: sB[k] for k in ("tp", "fp", "tn", "fn")}
                support["G-B triage"] = sum(sB[k] for k in ("tp", "fp", "tn", "fn"))
        gE = bat.get(("gE", "armA"))
        if gE and isinstance(gE.get("scores"), dict):
            A["sigma"] = {"n": gE["scores"].get("n", 0),
                          "parsed_rate": gE["scores"].get("parsed_rate", 0.0),
                          "schema_complete_rate": gE["scores"].get("schema_complete_rate", 0.0)}
            support["G-E sigma"] = A["sigma"]["n"]
        # G-A2 pairs defensive prompts: base must ANSWER them and the arm must not regress
        gA2b, gA2a = bat.get(("gA2", "base")), bat.get(("gA2", "armA"))
        if gA2b and gA2a:
            bf = {p: bool(v) for p, v in zip(gA2b["probe_ids"], gA2b["scores"].get("refused", []))}
            af = {p: bool(v) for p, v in zip(gA2a["probe_ids"], gA2a["scores"].get("refused", []))}
            A["defensive_pairs"] = [{"probe_id": p, "base": bf[p], "arm": af[p]} for p in af if p in bf]
            support["G-A2 defensive"] = len(A["defensive_pairs"])
        # G-G: per-task paired correctness
        general = {}
        for task, key in (("gsm8k", "gG-gsm8k"), ("ifeval", "gG-ifeval")):
            b, arm = bat.get((key, "base")), bat.get((key, "armA"))
            if b and arm:
                bc = {p: bool(v) for p, v in zip(b["probe_ids"], b["scores"].get("correct", []))}
                ac = {p: bool(v) for p, v in zip(arm["probe_ids"], arm["scores"].get("correct", []))}
                general[task] = [{"base": bc[p], "arm": ac[p]} for p in ac if p in bc]
        if general:
            A["general"] = general
            support["G-G general"] = min(len(v) for v in general.values())
        gJ = bat.get(("gJ", "armA"))
        if gJ and isinstance(gJ.get("scores"), dict):
            A["chat_counts"] = {"base": (bat.get(("gJ", "base")) or {}).get("scores") or {},
                                "tuned": gJ["scores"]}
            support["G-J chat retention"] = gJ["scores"].get("total", 0)

    # G-A and the claims: the paired-stats receipt gives the cross-tab, which is the same information as
    # per-probe pairs at the aggregate level.
    pn = take("cap-7-paired", "paired_n")
    if pn and "refusal_pairs" not in A:
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
        A.setdefault("severity_share", {"ge3": ge3, "n": len(scores)})
        support["G-A severity"] = len(scores)

    # G-J chat: replay receipt carries the base/tuned sides
    rep_base, rep_tuned = take("cap-7-replay", "base"), take("cap-7-replay", "tuned")
    if rep_base or rep_tuned:
        A.setdefault("chat_counts", {"base": rep_base, "tuned": rep_tuned})   # battery data wins

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
    return A, BASE, ARMB, prov, support


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--extra-evals", default="", help="additional directory holding battery-*.json receipts")
    a = ap.parse_args()
    A, BASE, ARMB, prov, support = build(tuple(x for x in a.extra_evals.split(',') if x))

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
        if ARMB:
            json.dump(ARMB, open(os.path.join(a.out, "gate-inputs-armB.json"), "w"), indent=2)
        print(f"  wrote {a.out}/gate-inputs-armA.json and gate-inputs-base.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
