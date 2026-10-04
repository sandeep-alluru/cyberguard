#!/usr/bin/env python3
"""§8.6 held-out quality — the decision layer, reusing the existing pubbench measurements.

Why this is small: the hard part of §8.6 already exists. `pubbench/run_pubbench.py` scores **base vs
tuned on exactly the 610 references** (CyberMetric-500 = 500, SecQA-v1-test = 110), on identical
support, and reports pooled + per-dataset counts. Review cycle 3's finding was that the *cited*
evaluator (`eval_cyberguard.py`) loads the wrong population — the old 500-row Trendyol split — because
it is the wrong instrument, not because no instrument exists. So this file does NOT re-run or
re-implement scoring. It applies §8.6's decision rule to whatever metric the harness produced.

§8.6 decision rule (structure, unchanged): the pooled metric AND **each dataset independently** must
satisfy the margin — one failing dataset fails the gate. Fixed denominators; missing rows stay in n.
Two paired components exist in §8.6 (loss and reference token-F1); both are applied to the same
support. This tool scores one component at a time and requires the caller to state the margin, so no
margin is invented here.

METRIC QUESTION — flagged to the owner, not decided here (over-engineering directive)
-----------------------------------------------------------------------------------------
§8.6 specifies held-out **loss** (tuned − base ≤ 0.0) and **reference token-F1** (≥ −0.02). The
existing harness computes **accuracy**. Accuracy is the more decision-relevant and cheaper figure:
it is directly interpretable, it is what v2's Arm B receipt reports, and it costs ~3 minutes per arm
(`pubbench/results.json`), whereas loss/token-F1 would be new code plus another full 610-row pass.
Token-F1 against reference answers is also a weak proxy (it rewards echoing the reference phrasing).
Recommendation: re-specify §8.6 onto the existing accuracy harness with an owner-chosen margin.
Until the owner chooses, this tool refuses to default a margin.

Usage:
  python3 tools/gate_86_heldout.py --results pubbench/results.json --base base --tuned armB \
      --metric accuracy --margin 0.02          # margin is REQUIRED, never assumed
  python3 tools/gate_86_heldout.py --self-test
"""
import argparse
import collections
import json
import sys

DATASETS = ("cybermetric-500", "secqa-v1-test")


# The registered §8.6 population. Astra design pass, defect 4.9: nothing checked these, so a SINGLE row
# per side carrying `correct: null` was accepted as a population, both arms read 0.0, the deltas were 0,
# and the gate PASSED on a population that was never measured.
REQUIRED_COUNTS = {"cybermetric-500": 500, "secqa-v1-test": 110}


def per_dataset(items):
    """counts per dataset from a harness item list: [correct, n, n_unknown_correctness]."""
    out = collections.defaultdict(lambda: [0, 0, 0])  # [correct, n, unknown]
    for it in items:
        ds = it.get("dataset", "?")
        out[ds][1] += 1
        c = it.get("correct")
        # Astra final review: `elif c` truthiness-coerced ANY non-empty value, so a population whose every
        # outcome was the string "UNKNOWN" scored as the whole population being CORRECT. Only a native
        # boolean is an outcome; anything else (None, strings, numbers) is unknown.
        if not isinstance(c, bool):
            out[ds][2] += 1                  # not a measured binary outcome -> unknown, never correct
        elif c:
            out[ds][0] += 1
    return {k: (v[0] / v[1] if v[1] else 0.0, v[0], v[1], v[2]) for k, v in out.items()}


def decide(base_items, tuned_items, margin):
    """§8.6: pooled AND every dataset must keep (tuned - base) >= -margin."""
    b, t = per_dataset(base_items), per_dataset(tuned_items)
    if set(b) != set(t):
        return {"valid": False, "why": "arms scored on different datasets: %s vs %s" % (sorted(b), sorted(t))}
    # POPULATION GUARD (Astra 4.9). Both registered datasets, at their registered sizes, with no unknown
    # correctness. An incomplete population cannot yield a §8.6 result, however clean the arithmetic looks.
    missing = [d for d in REQUIRED_COUNTS if d not in b]
    if missing:
        return {"valid": False, "why": "required dataset(s) absent: %s (registered population is %s)"
                % (sorted(missing), REQUIRED_COUNTS)}
    wrong = {d: (b[d][2], t[d][2]) for d in REQUIRED_COUNTS if (b[d][2], t[d][2]) != (REQUIRED_COUNTS[d], REQUIRED_COUNTS[d])}
    if wrong:
        return {"valid": False, "why": "dataset population does not match the registered sizes "
                "(base,tuned) vs required: %s" % {d: (wrong[d], REQUIRED_COUNTS[d]) for d in wrong}}
    unknown = {d: (b[d][3], t[d][3]) for d in REQUIRED_COUNTS if b[d][3] or t[d][3]}
    if unknown:
        return {"valid": False, "why": "unknown correctness (correct=null) is not a measured outcome: "
                "%s (base,tuned unknown counts)" % unknown}
    pooled_b = sum(v[1] for v in b.values()) / sum(v[2] for v in b.values())
    pooled_t = sum(v[1] for v in t.values()) / sum(v[2] for v in t.values())
    rows, ok = [], (pooled_t - pooled_b) >= -margin
    rows.append(("POOLED", pooled_b, pooled_t, pooled_t - pooled_b, (pooled_t - pooled_b) >= -margin))
    for ds in sorted(b):
        d = t[ds][0] - b[ds][0]
        good = d >= -margin
        ok = ok and good
        rows.append((ds, b[ds][0], t[ds][0], d, good))
    return {"valid": True, "pass": ok, "margin": margin, "rows": rows,
            "n_base": sum(v[2] for v in b.values()), "n_tuned": sum(v[2] for v in t.values())}


def show(r):
    if not r.get("valid"):
        print("INVALID:", r["why"])
        return 1
    print("§8.6 held-out decision   margin = %.4f   n_base=%d n_tuned=%d" % (r["margin"], r["n_base"], r["n_tuned"]))
    for name, b, t, d, good in r["rows"]:
        print("  %-20s base=%.4f tuned=%.4f delta=%+.4f  %s" % (name, b, t, d, "PASS" if good else "FAIL"))
    print("GATE:", "PASS" if r["pass"] else "FAIL (a failing dataset fails the gate)")
    return 0 if r["pass"] else 1


def self_test():
    ok = True

    def chk(name, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print("  %-62s %s" % (name, "OK" if good else "FAIL got=%s want=%s" % (got, want)))

    mk = lambda ds, n, c: [{"dataset": ds, "correct": i < c} for i in range(n)]
    base = mk("cybermetric-500", 500, 443) + mk("secqa-v1-test", 110, 110)
    # pooled up, one dataset down -> must FAIL (the whole point of the per-dataset clause)
    tuned = mk("cybermetric-500", 500, 447) + mk("secqa-v1-test", 110, 108)
    r = decide(base, tuned, 0.0)
    chk("pooled improves but SecQA drops -> FAIL", r["pass"], False)
    chk("fixed denominators kept (610 both arms)", (r["n_base"], r["n_tuned"]), (610, 610))
    # both datasets hold -> PASS
    tuned2 = mk("cybermetric-500", 500, 448) + mk("secqa-v1-test", 110, 110)
    chk("both datasets hold -> PASS", decide(base, tuned2, 0.0)["pass"], True)
    # different populations -> invalid, never a pass
    chk("mismatched datasets -> INVALID", decide(base, mk("cybermetric-500", 500, 500), 0.0)["valid"], False)
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--results", help="pubbench results.json produced by pubbench/run_pubbench.py")
    ap.add_argument("--base", default="base")
    ap.add_argument("--tuned", default="armB")
    ap.add_argument("--margin", type=float, help="REQUIRED: allowed drop, e.g. 0.02 for 2 pp")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.results:
        print(__doc__)
        return 2
    if a.margin is None:
        print("REFUSING: --margin is required. §8.6's written margins are loss<=0.0 and token-F1>=-0.02;")
        print("this harness measures accuracy, whose margin the owner has not chosen. No default is assumed.")
        return 3
    d = json.load(open(a.results))
    if a.base not in d or a.tuned not in d:
        print("REFUSING: %s or %s missing from %s" % (a.base, a.tuned, a.results))
        return 4
    return show(decide(d[a.base]["items"], d[a.tuned]["items"], a.margin))


if __name__ == "__main__":
    sys.exit(main())
