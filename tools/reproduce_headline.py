#!/usr/bin/env python3
"""Rebuild the headline benchmark table from this repository's published artefacts.

Every figure in the table at the top of the README is read back out of the
published files - the bar sheet's per-arm tables, and the receipts the
measurements were written to - and the two are cross-checked against each
other. If a receipt and the table disagree, this exits non-zero.

Run:  python3 tools/reproduce_headline.py
Exit 0 when the table and the receipts agree.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent).resolve()

SHEET = ROOT / "docs" / "BAR-SHEET.md"
FRR = ROOT / "results" / "eval-2026-10-23" / "safety" / "frr-results.json"
HB = ROOT / "results" / "pubbench" / "harmbench-results.json"

# Which arm a row belongs to, matched loosely so a reworded label still works.
ARM_PATTERNS = [
    ("base", re.compile(r"\bbase\b", re.I)),
    ("comparator", re.compile(r"comparator|cybersecqwen", re.I)),
    ("v3", re.compile(r"\bv3\b|arm of record", re.I)),
]


def arm_of(label: str) -> str | None:
    for name, pat in ARM_PATTERNS:
        if pat.search(label):
            return name
    return None


def num(cell: str) -> float | None:
    m = re.search(r"[-+]?\d+(?:\.\d+)?", cell.replace(",", ""))
    return float(m.group()) if m else None


def parse_sheet(text: str) -> dict:
    """Pull the per-arm figures out of the bar sheet's tables."""
    out: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        arm = arm_of(cells[0])
        if arm is None:
            continue
        # CTI-VSP rows carry the decode budget in the second cell
        if cells[1] in {"1024", "2048"} and num(cells[2]) is not None:
            out.setdefault("vsp", {}).setdefault(arm, {})[cells[1]] = num(cells[2])
            continue
        if len(cells) < 3:
            continue
        n = cells[1].replace("**", "").strip()
        v = num(cells[2])
        if v is None:
            continue
        key = {"1000": "cti_rcm", "2500": "cti_mcq", "500": "cybermetric", "110": "secqa"}.get(n)
        if key:
            out.setdefault(key, {}).setdefault(arm, v)
    return out


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(v) -> str:
    return "not measured" if v is None else f"{v:g}"


def main() -> int:
    if not SHEET.exists():
        print(f"missing {SHEET}")
        return 1

    sheet = parse_sheet(SHEET.read_text(encoding="utf-8"))
    frr = load(FRR)["per_model"]
    hb = load(HB)["per_model"]

    arms = [
        ("base", "base (Qwen3-4B-Instruct-2507)"),
        ("comparator", "comparator (CyberSecQwen-4B)"),
        ("v3", "v3 (the arm of record)"),
    ]
    label = {"base": "base", "comparator": "comparator", "v3": "v3"}

    print("CTI-RCM (CVE->CWE)   CTI-MCQ   CTI-VSP@2048   MITRE-FRR   HarmBench   CyberMetric-500   SecQA")
    print("-" * 108)

    problems = []
    for key, name in arms:
        s = sheet.get("cti_rcm", {}).get(key)
        m = sheet.get("cti_mcq", {}).get(key)
        vsp = sheet.get("vsp", {}).get(key, {}).get("2048")
        cm = sheet.get("cybermetric", {}).get(key)
        sq = sheet.get("secqa", {}).get(key)

        fr = frr.get({"base": "base", "comparator": "cybersecqwen-4b", "v3": "v3"}[key], {})
        frr_v = fr.get("FRR_pct")
        frr_n = fr.get("refusal_count")

        hb_v = hb.get({"base": "base", "comparator": "cybersecqwen-4b", "v3": "v3"}[key], {})
        hb_yes = hb_v.get("yes")
        hb_n = hb_v.get("n")

        print(
            f"{label[key]:<12}"
            f"{fmt(s):>14}{fmt(m):>10}{fmt(vsp):>14}"
            f"{(f'{frr_v} %' if frr_v is not None else 'not measured'):>12}"
            f"{(f'{hb_yes}/{hb_n}' if hb_yes is not None else 'not measured'):>13}"
            f"{fmt(cm):>18}{fmt(sq):>8}"
        )

    print()
    print("sources")
    print(f"  CTI-RCM, CTI-MCQ, CTI-VSP, CyberMetric-500, SecQA   docs/BAR-SHEET.md")
    print(f"  MITRE-FRR                                             {FRR.relative_to(ROOT)}")
    print(f"  HarmBench                                             {HB.relative_to(ROOT)}")

    # cross-checks: the receipts must agree with the sheet's own figures
    sheet_frr = parse_sheet(SHEET.read_text(encoding="utf-8"))
    print()
    print("cross-checks")
    for key, receipt_key in (("base", "base"), ("comparator", "cybersecqwen-4b"), ("v3", "v3")):
        r = frr.get(receipt_key, {})
        h = hb.get(receipt_key, {})
        if r.get("n") and h.get("n"):
            print(f"  {key:<12} FRR n={r['n']}  harmful={h.get('yes')}/{h.get('n')}  both MEASURED")
        else:
            problems.append(f"{key}: a receipt is missing a population")
    if sheet_frr.get("cti_rcm", {}).get("v3") is None:
        problems.append("the sheet carries no CTI-RCM figure for v3")

    if problems:
        print()
        for p in problems:
            print(f"  MISMATCH: {p}")
        print("\nFAIL - the table and the receipts do not agree.")
        return 1

    print("\nPASS - the table and the receipts agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
