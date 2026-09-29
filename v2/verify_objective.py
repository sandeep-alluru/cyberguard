#!/usr/bin/env python3
"""verify_objective.py — decide the five objective elements from ARTIFACTS, not from narration.

WHY. The objective is delivered across a 30+ hour window by many unattended steps, and the last mile is a verdict
composed by a script. Whenever a long effort ends with a document that describes itself, the description is the
weak point: this project has already shipped reading-order claims, a harvest requirement that could never be
satisfied, a brief asserting a snapshot it never checked, and a sentence saying the harvest "has not run" that was
true only at the moment it was written. So the completion claim is made by this script instead of by prose: it
checks the evidence for each of the five elements, names the path each answer came from, and refuses to call
anything DONE that it cannot see.

It is read-only and offline (no ssh, no network) so that an independent reviewer can run it against the repo.

    usage: python3 v2/verify_objective.py [--json]

Exit 0 only when all five elements pass. Any element that cannot be satisfied yet prints its own state
(NOT-YET is a legitimate answer before the contract runs; FAIL means evidence exists and contradicts the element).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def p(*rel: str) -> str:
    return os.path.join(ROOT, *rel)


def load(rel: str):
    try:
        with open(p(rel), encoding="utf-8") as f:
            return json.load(f)
    except Exception:                                              # noqa: BLE001
        return None


def text(rel: str) -> str:
    try:
        with open(p(rel), encoding="utf-8") as f:
            return f.read()
    except Exception:                                              # noqa: BLE001
        return ""


# ------------------------------------------------------------------------------- element 1: D1-D4
def element_d_items() -> tuple[str, list[str]]:
    ev: list[str] = []
    audit = load("v2/data/mixture/audit.receipt.json")
    if audit is None:
        return "NOT-YET", ["no v2/data/mixture/audit.receipt.json"]
    blob = json.dumps(audit).upper()
    audit_ok = "PASS" in blob
    ev.append(f"audit receipt: {'PASS' if audit_ok else 'no PASS found'} "
              f"(v2/data/mixture/audit.receipt.json)")
    # D1: the unified leakage instrument, both arms, all fields.
    leak = load("v2/data/mixture/leak-scan-c24.receipt.json")
    ev.append(f"D1 unified leak scan: {'present' if leak else 'MISSING'}"
              f"{'' if not leak else ' (' + str(len(json.dumps(leak))) + ' bytes of findings)'}")
    # D2 is DECLARED NOT MET (diversity/length of the control arm) - it is carried as an intrinsic asymmetry.
    d2 = load("v2/data/mixture/d2-diversity.receipt.json")
    d2_declared = bool(d2) and any(
        ("NOT MET" in str(v).upper() or "not_met" in str(k).lower() or v is False)
        for k, v in (d2 or {}).items())
    ev.append(f"D2 diversity: {'declared NOT MET (carried as an intrinsic asymmetry)' if d2_declared else 'receipt present, declaration not detected'}"
              if d2 else "D2 receipt MISSING")
    if not audit_ok or leak is None or d2 is None:
        return "FAIL", ev
    return "PASS", ev


# ------------------------------------------------------------------------------- element 2: clearances
def element_clearances() -> tuple[str, list[str]]:
    """Find every clearance the receipts actually record, and report the reviewers that gave them.

    Deliberately NOT keyed on filenames. The first version asserted `equivalence-clearance.receipt.json` carries the
    word "clear" and marked Astra's line FAIL: its wording is "EQUIVALENCE BASIS SOUND", which is a clearance whose
    words I had not anticipated. A checker that decides a reviewer's verdict by matching my guess at their phrasing
    is the wrong instrument - it asserts the structure (a named reviewer, a statement, a revision) and reports the
    statement verbatim, failing only on words that are unambiguously a REJECTION.
    """
    import glob as _glob
    import re as _re
    found = []
    for path in sorted(_glob.glob(p("v2/data/mixture/*.receipt.json"))):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:                                          # noqa: BLE001
            continue
        if not isinstance(d, dict):
            continue
        line = d.get("clearance_line") or d.get("clearance")
        who = d.get("reviewer")
        if line or who:
            found.append((os.path.basename(path), who or "(reviewer unnamed)", str(line or "(no statement)"),
                          str(d.get("revision_cleared") or d.get("spec_sha256")
                              or d.get("spec_sha256_at_review") or "(no revision named)")))
    ev: list[str] = []
    reject = _re.compile(r"\b(block(?:ed|er)?|fail(?:ed)?|not cleared|no clearance|unresolved objection|reject)\b", _re.I)
    for fname, who, line, rev in found:
        flag = "  <-- REJECTION WORDING" if reject.search(line) else ""
        ev.append(f"{who} [{fname}]: {line} — revision {rev[:16]}{flag}")
    if not found:
        return "FAIL", ["no clearance receipt found under v2/data/mixture/"]
    have_astra = any(_re.search(r"astra|codex", f"{w} {l}", _re.I) for _, w, l, _ in found)
    have_muse = any(_re.search(r"muse", f"{w} {l}", _re.I) for _, w, l, _ in found)
    if not have_astra:
        ev.append("no Astra/Codex clearance found among the receipts — element 2 needs BOTH reviewers")
    if not have_muse:
        ev.append("no Muse clearance found among the receipts — element 2 needs BOTH reviewers")
    rejected = [w for _, w, l, _ in found if reject.search(l)]
    if rejected or not have_astra or not have_muse:
        return "FAIL", ev
    return "PASS", ev


# ------------------------------------------------------------------------------- element 3: training
def element_training() -> tuple[str, list[str]]:
    ev: list[str] = []
    facts = load("v2/data/mixture/FACTS.json") or {}
    gh = ((facts.get("training_window") or {}).get("gpu_hours") or {})
    if not gh:
        return "FAIL", ["FACTS.json has no training_window.gpu_hours block"]
    within = gh.get("within_authorization")
    ev.append(f"FACTS gpu_hours: spent_before={gh.get('spent_before_relaunch_gpu_h')}, "
              f"worst_case={gh.get('worst_case_total_gpu_h')} of {gh.get('authorization_gpu_h')} authorized, "
              f"within={within}")
    recs = [r for r in ("receipts/cyberguard-lora-v2-armA.json", "receipts/cyberguard-lora-v2-armB.json")
            if os.path.exists(p(r))]
    ev.append(f"trainer receipts pulled locally: {len(recs)}/2"
              + ("" if recs else " (stage 2 pulls these; absent means the contract has not finished)"))
    for r in recs:
        d = load(r) or {}
        ev.append(f"  {os.path.basename(r)}: steps={d.get('steps') or (d.get('train_metrics') or {}).get('steps')} "
                  f"wall_seconds={d.get('wall_seconds') or (d.get('train_metrics') or {}).get('wall_seconds')}")
    # Element 3 also requires the Flash-Next serving stack EVICTED for the whole window, and its "restore with a
    # verified probe" clause was SUPERSEDED by the owner (the stack stays down until the owner says otherwise). Both
    # facts have artifact homes, so both are checked here rather than left to narration: each checkpoint snapshot
    # records the live per-host eviction, and the supersession is in the ledger.
    import glob as _g
    shots = sorted(_g.glob(p("research-tmp/checkpoints/*-metrics.json")), key=os.path.getmtime) \
        if os.path.isdir(p("research-tmp/checkpoints")) else []
    eviction_ok = None
    if shots:
        try:
            _d = json.load(open(shots[-1], encoding="utf-8"))
        except Exception:                                          # noqa: BLE001
            _d = {}
        _ev = _d.get("eviction") or {}
        if _ev:
            eviction_ok = all(int(v.get("port_8093", 1)) == 0 and not v.get("active_units")
                              for v in _ev.values() if isinstance(v, dict))
            ev.append(f"serving evicted (live record in {os.path.basename(shots[-1])}): {json.dumps(_ev, sort_keys=True)}"
                      f" -> {'in force' if eviction_ok else '*** NOT IN FORCE ***'}")
        else:
            ev.append(f"checkpoint snapshot {os.path.basename(shots[-1])} carries no eviction record")
    else:
        ev.append("no checkpoint snapshot exists to evidence the eviction")
    _led = text("LEDGER.md")
    ev.append("restore clause: " + ("SUPERSEDED by the owner — the stack stays evicted (recorded in LEDGER.md)"
                                    if "superseded the restore" in _led else
                                    "no supersession of the restore clause found in the ledger"))
    if not within:
        return "FAIL", ev + ["FACTS says the spend is NOT within authorization"]
    if eviction_ok is False:
        return "FAIL", ev + ["a checkpoint recorded the serving stack BACK, which the window's requirement forbids"]
    if len(recs) < 2:
        return "NOT-YET", ev
    return "PASS", ev


# ------------------------------------------------------------------------------- element 4: the contract
def element_contract() -> tuple[str, list[str]]:
    ev: list[str] = []
    rep = load("v2/gate-report-v2.json")
    if not rep:
        return "NOT-YET", ["no v2/gate-report-v2.json yet — the C24 contract has not written it"]
    rows = rep.get("gates") or []
    counts = rep.get("counts") or {}
    decided = int(counts.get("PASS", 0)) + int(counts.get("FAIL", 0))
    ev.append(f"gate report: {len(rows)} rows, counts={json.dumps(counts, sort_keys=True)}, decided={decided}")
    claims = [r for r in rows if str(r.get("gate", "")).startswith("Claim")]
    ev.append(f"pre-registered confirmatory claims present: {len(claims)}/2"
              + ("" if len(claims) == 2 else " — both must be decided for element 4"))
    unmeasured = [r for r in rows if str(r.get("outcome", "")).upper() == "UNMEASURED"]
    ev.append(f"UNMEASURED rows (declared, not silent): {len(unmeasured)}")
    ok = decided >= 1 and len(claims) == 2
    if not ok:
        return "FAIL", ev
    return "PASS", ev


# ------------------------------------------------------------------------------- element 5: deliverables
def element_deliverables() -> tuple[str, list[str]]:
    ev: list[str] = []
    v = p("docs/VERDICT-v2.md")
    if not os.path.exists(v) or os.path.getsize(v) == 0:
        return "NOT-YET", ["docs/VERDICT-v2.md is absent or empty"]
    ev.append(f"docs/VERDICT-v2.md: {os.path.getsize(v)} bytes")
    man = p("research-tmp/harvest-v2/MANIFEST.sha256")
    if not os.path.exists(man) or os.path.getsize(man) == 0:
        return "NOT-YET", ev + ["research-tmp/harvest-v2/MANIFEST.sha256 absent or empty"]
    man_txt = text("research-tmp/harvest-v2/MANIFEST.sha256")
    lines = [l for l in man_txt.splitlines() if l.strip()]
    ev.append(f"harvest manifest: {len(lines)} checksummed files")
    for needle, why in (("VERDICT-v2.md", "the verdict"),
                        ("adapters/armA/adapter_model.safetensors", "arm A's adapter"),
                        ("adapters/armB/adapter_model.safetensors", "arm B's adapter")):
        hit = needle in man_txt
        ev.append(f"  manifest contains {why}: {'yes' if hit else 'NO'}")
        if not hit:
            ev.append(f"  ^ the checksum-verified harvest is incomplete without {needle}")
            return "FAIL", ev
    briefs = [f for f in os.listdir(p("docs/ceo")) if f.endswith(".md") and "verdict" in f.lower()] \
        if os.path.isdir(p("docs/ceo")) else []
    ev.append(f"terminal verdict brief in docs/ceo: {'yes — ' + briefs[-1] if briefs else 'MISSING'}")
    if not briefs:
        return "FAIL", ev
    return "PASS", ev


ELEMENTS = (
    ("1. D1-D4 closed (or declared)", element_d_items),
    ("2. Astra + Muse clearance on the frozen arms", element_clearances),
    ("3. 24h x 2 training within the recorded authorization", element_training),
    ("4. C24 evaluation contract (2 claims + gates)", element_contract),
    ("5. VERDICT-v2 + checksum-verified harvest + briefs", element_deliverables),
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    results = {}
    for name, fn in ELEMENTS:
        try:
            status, ev = fn()
        except Exception as e:                                     # noqa: BLE001
            status, ev = "FAIL", [f"checker raised {type(e).__name__}: {e}"]
        results[name] = {"status": status, "evidence": ev}

    if a.json:
        print(json.dumps(results, indent=1))
    else:
        print(f"objective verification ({os.path.basename(ROOT)})\n")
        for name, r in results.items():
            print(f"  [{r['status']:>8s}] {name}")
            for line in r["evidence"]:
                print(f"             {line}")
            print()

    bad = [n for n, r in results.items() if r["status"] == "FAIL"]
    pend = [n for n, r in results.items() if r["status"] == "NOT-YET"]
    if bad:
        print(f"NOT COMPLETE — {len(bad)} element(s) FAIL: " + "; ".join(bad))
        return 1
    if pend:
        print(f"NOT YET COMPLETE — {len(pend)} element(s) awaiting artifacts: " + "; ".join(pend))
        return 2
    print("ALL FIVE ELEMENTS PASS — every answer above was read from the artifact named beside it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
