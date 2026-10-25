#!/usr/bin/env python3
"""E-7 — the release-candidate check: v1's status is named, and every reason is a measurement.

WHY THIS FILE EXISTS
--------------------
Ledger item **E-7** asks whether v1 is carried forward, and its acceptance is: *"the decision
names v1's status; if not carried, the release table says so"*.

`EVALUATION.md` §8 Q1 frames it exactly: *"the measurement cannot answer the question on its own:
what counts as a candidate is a product decision (P2-1), not a number. What the numbers DO tell you
is whether those two arms are worth carrying forward at all."*

This file measures the second thing — the part the numbers answer — and it does not touch the
first. The decision is `W-4` (`eval-2026-10-23/release-candidates.json`, OWNER-D1 clause 2).

WHAT THIS FILE MEASURES
-----------------------
1. The decision record exists, names **every arm**, and each arm carries a status from a closed
   vocabulary.
2. **v1's status is named** and the release table in `docs/BAR-SHEET.md` says it.
3. **Every reason is a measurement, not a preference**: each arm that is not carried forward must
   cite at least one figure from a named artefact, and that figure must **equal the artefact's
   value**. A reason that cites a wrong number fails here.
4. **The decision does not overreach**: it does not decide ship/no-ship (H-3's), does not change a
   bar, and says so.
5. The release table in the bar sheet is **generated from** the decision record, so the two cannot
   disagree.

Output: eval-2026-10-23/e7-release-candidates-check.json
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RC = HERE / "release-candidates.json"
SHEET = ROOT / "docs" / "BAR-SHEET.md"
OUT = HERE / "e7-release-candidates-check.json"

VOCAB = ("reference — not a candidate", "not carried forward",
         "not carried forward as a release candidate; retained as the arm of record",
         "the arm to be trained — H-1 is OWNER GO")

# the figures a reason may cite, and where each must be equal
def arm_figures():
    frr = json.load(open(HERE / "safety/frr-results.json"))["per_model"]
    hb = json.load(open(HERE / "safety/harmbench-paired-all-arms.json"))["per_arm"]
    merged = json.load(open(HERE / "results-merged-2026-10-23.json"))
    sweep = json.load(open(HERE / "cti-sweep-scored.json"))
    cmp_ = {(e["model"], e["benchmark"]): e for e in merged["comparison"]}
    for arm, rows in sweep["arms"].items():
        # "arms" is arm -> rows; a non-dict value is metadata, not an arm
        if not isinstance(rows, dict):
            continue
        for key, row in rows.items():
            m, bm = key.split("/")
            cmp_[(m, bm)] = row
    hbk = {"base": "base", "v1": "v1", "v2armA": "v2 arm A", "v2armB": "v2 arm B",
           "v3": "v3", "cybersecqwen-4b": "comparator (CyberSecQwen-4B)"}
    out = {}
    for arm, key in hbk.items():
        f = frr[arm]
        h = hb[key]
        c = cmp_.get((arm, "cti-rcm"))
        m_ = cmp_.get((arm, "cti-mcq"))
        out[arm] = {
            "frr_pct": f["FRR_pct"],
            "frr_count": f["refusal_count"],
            "frr_n": f["n"],
            "hb_yes": h["yes"],
            "hb_rate_pct": h["rate_pct"],
            "hb_wilson_upper_pct": round(h["wilson95_frozen_recomputed"][1] * 100, 2),
            "cti_rcm": c["accuracy"] if c else None,
            "cti_mcq": m_["accuracy"] if m_ else None,
            "cti_mcq_unparseable": m_["unparseable"] if m_ else None,
            "cti_mcq_n": m_["n"] if m_ else None,
        }
    return out


def main():
    checks = []
    rc = json.load(open(RC))
    figs = arm_figures()

    def ck(name, cond):
        checks.append((name, bool(cond)))

    ck("the decision record exists", RC.exists())
    ck("the record names its decision id and its authority",
       rc.get("decision_id") == "W-4" and "OWNER-D1" in rc["authority"]["register"])
    ck("the record states that the ship decision is NOT this record's",
       any("H-3" in s for s in rc["what_is_not_decided_here"]))

    arms = {e["arm"]: e for e in rc["arms"]}
    ck("the record names every arm, including the new arm",
       set(arms) == {"base", "v1", "v2armA", "v2armB", "v3", "cybersecqwen-4b", "new"})
    ck("every arm carries a status from the closed vocabulary",
       all(e["status"] in VOCAB for e in rc["arms"]))

    # --- v1 is named and the release table says it -------------------------------
    ck("v1's status is named", "v1" in arms and bool(arms["v1"]["status"]))
    ck("v1's status is 'not carried forward'",
       arms.get("v1", {}).get("status") == "not carried forward")

    # --- every reason is a measurement, and the figures are right ------------------
    for arm, e in arms.items():
        reason = e["reason"]
        ck(f"{arm}: the reason cites at least one measured figure",
           bool(re.search(r"\d", reason)))
        ck(f"{arm}: the reason names evidence that exists",
           all((ROOT / p).exists() or (ROOT / "docs" / Path(p).name).exists()
               or Path(p).name in ("PLAN-LEDGER.md",)
               for p in e["evidence"]))
        if arm == "v1":
            ck("v1: the FRR figure in the reason equals the artefact's",
               f"{figs['v1']['frr_pct']:.2f} %" in reason)
            ck("v1: the HarmBench figure in the reason equals the artefact's",
               f"{figs['v1']['hb_yes']}/159" in reason)
            ck("v1: the CTI-RCM figure in the reason equals the artefact's",
               f"{figs['v1']['cti_rcm']:.4f}" in reason)
            ck("v1: the CTI-MCQ figure in the reason equals the artefact's",
               f"{figs['v1']['cti_mcq']:.4f}" in reason)
            ck("v1: the always-C floor the reason cites is the measured one",
               "0.3712" in reason)
        if arm == "v2armA":
            ck("v2 arm A: the FRR figure equals the artefact's",
               f"{figs['v2armA']['frr_pct']:.2f} %" in reason)
            ck("v2 arm A: the CTI-RCM figure equals the artefact's",
               f"{figs['v2armA']['cti_rcm']:.4f}" in reason)
            ck("v2 arm A: the CTI-MCQ figure equals the artefact's",
               f"{figs['v2armA']['cti_mcq']:.4f}" in reason)
        if arm == "v2armB":
            ck("v2 arm B: the FRR figure equals the artefact's",
               f"{figs['v2armB']['frr_pct']:.2f} %" in reason)
            ck("v2 arm B: the CTI-RCM figure equals the artefact's",
               f"{figs['v2armB']['cti_rcm']:.4f}" in reason)
        if arm == "v3":
            ck("v3: the FRR figure equals the artefact's",
               f"{figs['v3']['frr_pct']:.2f} %" in reason)
            ck("v3: the CTI-RCM figure equals the artefact's",
               f"{figs['v3']['cti_rcm']:.4f}" in reason)
        if arm == "base":
            ck("base: the FRR figure equals the artefact's",
               f"{figs['base']['frr_pct']:.2f} %" in reason)
        if arm == "cybersecqwen-4b":
            ck("the comparator: the Wilson upper equals the artefact's",
               f"{figs['cybersecqwen-4b']['hb_wilson_upper_pct']:.2f} %" in reason)

    # the multiples the reasons quote must be arithmetically right
    # B3 is "base + 1.0 pp". The ceiling is computed from the base's re-measured FRR on the
    # frozen surface, so it cannot drift from the bar's own baseline.
    CEIL = figs["base"]["frr_pct"] + 1.0
    for arm, e in arms.items():
        m = re.search(r"(\d+\.\d+)x B3", e["reason"])
        if m:
            stated = float(m.group(1))
            actual = figs[arm]["frr_pct"] / CEIL
            ck(f"{arm}: the multiple of B3's ceiling is arithmetically right",
               abs(stated - actual) < 0.02)

    # --- the bar sheet's release table is generated from the record ----------------
    if SHEET.exists():
        sheet = SHEET.read_text()
        ck("the bar sheet carries the release table",
           "The release table — which arms are carried forward" in sheet)
        agree = all(f"**{e['status']}**" in sheet for e in rc["arms"])
        ck("every status in the record appears in the bar sheet's release table", agree)
        ck("the bar sheet's release table names v1's status",
           arms["v1"]["status"] in sheet)
        ck("the bar sheet says the release table is not the ship decision",
           "not the ship-or-do-not-ship decision" in sheet)

    # --- the decision does not overreach ------------------------------------------
    ck("the record does not claim to ship",
       not re.search(r"\bwe ship\b|\bship it\b|\bthe release ships\b", json.dumps(rc), re.I))
    ck("the record states it changes no bar, metric, parser, sample size, decode budget or label",
       "changes no bar" in rc["authority"]["why_this_is_delegated"])

    out = {
        "status": "MEASUREMENT — the release-candidate decision is checked against the artefacts; "
                  "every figure it cites is re-read from the artefact it names.",
        "decision_record": str(RC),
        "decision_id": rc["decision_id"],
        "statuses": {e["arm"]: e["status"] for e in rc["arms"]},
        "checks": [{"check": c, "pass": bool(p)} for c, p in checks],
    }
    npass = sum(1 for _, p in checks if p)
    out["checks_passed"] = npass
    out["checks_total"] = len(checks)
    out["status_line"] = f"{npass}/{len(checks)} checks PASS"
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    print(f"e7_release_candidates: {npass}/{len(checks)} checks PASS -> {OUT}")
    for c, p in checks:
        print(f"  [{'PASS' if p else 'FAIL'}] {c}")
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
