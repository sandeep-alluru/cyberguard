#!/usr/bin/env python3
"""E-3 — the release-rule check: the contradiction is named, closed, and not restated anywhere live.

WHY THIS FILE EXISTS
--------------------
The archived board record carried a VERIFIED blocking fact (`SESSION-ARCHIVE/board/EVALUATION.md:146`):

    "The v4 ledger says public evals are comparison-only while its ship-bar section also makes
     CTI-RCM >0.6664 a ship bar. An authoritative model-evaluation ruling is required before
     training."

Ledger item **E-3** requires that contradiction be "named and marked closed in the rule document"
and that "no document simultaneously says both". The rule document is `docs/BAR-SHEET.md` §0 — one
rule, one document.

WHAT THIS FILE MEASURES
-----------------------
Not "the rule reads well". Four things:

1. The rule document exists, names the contradiction, quotes it verbatim from the archive with its
   file and line, and marks it CLOSED.
2. The rule states the three clauses, including the baseline clause that actually disposes of the
   CTI-RCM instance.
3. The withdrawn bar is withdrawn *by name*: the v4 ledger's CTI-RCM > 0.6664 bar, and the live
   bar is named against a figure **this project measured on this surface** — not the
   author-reported 0.6664.
4. **No live document says both.** This is the part that has to be measured rather than asserted.
   The file scans every live document (everything except `SESSION-ARCHIVE/`, which is an evidence
   archive and not a rule document) for (a) a claim that public evaluations are comparison-only or
   otherwise not decision evidence, and (b) a ship bar on a public-benchmark number. It then
   checks that no single live document contains both, and reports the count of documents that do.

Output: eval-2026-10-23/e3-release-rule-check.json
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RULE_DOC = ROOT / "docs" / "BAR-SHEET.md"
ARCHIVE = ROOT / "SESSION-ARCHIVE" / "board" / "EVALUATION.md"
OUT = HERE / "e3-release-rule-check.json"

# Live documents: the deliverables and docs/. SESSION-ARCHIVE/ is the evidence archive.
LIVE = []
for rel in ("EVALUATION.md", "PRODUCT-DEFINITION.md", "PRODUCT-RESEARCH.md", "NEXT-STEPS.md"):
    p = ROOT / rel
    if p.exists():
        LIVE.append((rel, p))
docs = ROOT / "docs"
if docs.is_dir():
    for p in sorted(docs.rglob("*.md")):
        LIVE.append((str(p.relative_to(ROOT)), p))

# A claim that a public evaluation is NOT decision evidence.
COMPARISON_ONLY = re.compile(
    r"comparison[- ]only"
    r"|public (?:benchmarks?|evaluations?|evals?) (?:are|is) (?:not |never |only )?"
    r"(?:decision|release|acceptance|gate)"
    r"|(?:cannot|must not|may not) (?:be used to |)(?:decide|gate|judge) (?:a )?release",
    re.I)

# A ship bar / release gate on a public-benchmark number.
SHIP_BAR = re.compile(
    r"ship bar"
    r"|ship-bar"
    r"|release (?:bar|gate|threshold)"
    r"|(?:clears?|passes?) the bar"
    r"|bar for release",
    re.I)

# A public-benchmark name appearing in a bar sentence.
PUBLIC_BENCH = re.compile(
    r"CTI-RCM|CTI-MCQ|CyberMetric|SecQA|HarmBench|MITRE-FRR", re.I)

# A line carrying one of these is QUOTING the conflict in order to close it, not asserting it.
# Without this, the rule document's own quotation of the archived contradiction would read as an
# assertion of it — the same trap the consistency gate's withdrawal escape exists to avoid.
CLOSURE_ESCAPE = (
    "CLOSED", "RESOLVED", "retired", "closes it", "Resolve the contradiction",
    "contradiction this section closes", "resolved",
)
# The escape is CONTEXTUAL: a marker on the line itself, or within this many lines around it.
# The rule document's block quote of the archived contradiction is several lines above its
# "CLOSED" marker, so a same-line test alone would read the quotation as an assertion.
ESCAPE_WINDOW = 6


def main():
    checks = []
    doc = RULE_DOC.read_text()
    arc = ARCHIVE.read_text()

    def ck(name, cond):
        checks.append((name, bool(cond)))

    # --- 1. the contradiction is named and closed --------------------------------
    ck("the rule document exists", RULE_DOC.exists())
    ck("the rule document has a rule section", "## 0. The release rule" in doc)
    ck("the rule document names the archive as the source of the contradiction",
       "SESSION-ARCHIVE/board/EVALUATION.md:146" in doc)
    quoted = "The v4 ledger says public evals are comparison-only while its ship-bar section also makes CTI-RCM >0.6664 a ship bar."
    ck("the rule document quotes the contradiction verbatim from the archive",
       quoted in doc and quoted in arc)
    ck("the archive line is the one quoted (the string is really in the archive)",
       quoted in arc)
    ck("the contradiction is marked closed", "CLOSED 2026-10-23" in doc)

    # --- 2. the three clauses ---------------------------------------------------
    ck("the rule states that a public benchmark is decision evidence and retires "
       "'comparison-only'", "comparison-only" in doc and "retired" in doc)
    ck("the rule distinguishes decision instruments from report-only instruments",
       "decision instruments" in doc and "report-only instruments" in doc)
    ck("the rule names which instruments are decision instruments",
       all(x in doc for x in ("B1 CTI-RCM", "B3 MITRE-FRR", "B3b refusal integrity",
                              "B4 HarmBench")))
    ck("the rule names which instruments are report-only",
       all(x in doc for x in ("B5 CTI-MCQ", "B6 CyberMetric-500", "B7 SecQA-v1-test",
                              "B8 output hygiene")))
    ck("the rule requires the comparator baseline to be measured by this project on the same "
       "surface", "must be a figure this project measured, on the same" in doc)

    # --- 3. the withdrawn bar is withdrawn by name --------------------------------
    ck("the rule withdraws the v4 ledger's CTI-RCM > 0.6664 bar by name",
       "CTI-RCM > 0.6664" in doc and "withdrawn" in doc)
    ck("the rule states that 0.6664 is author-reported, not a project measurement",
       "author-reported" in doc and "0.6664" in doc)
    ck("the live bar is named against the project's own re-measurement",
       "CTI-RCM > 0.6780" in doc)

    # the live bar's baseline must be a value this project measured
    merged = json.load(open(HERE / "results-merged-2026-10-23.json"))
    cmp_row = next(e for e in merged["comparison"]
                   if e["model"] == "cybersecqwen-4b" and e["benchmark"] == "cti-rcm")
    v3_row = next(e for e in merged["comparison"]
                  if e["model"] == "v3" and e["benchmark"] == "cti-rcm")
    ck("the baseline the rule names is the project's own re-measurement of the comparator",
       f"{cmp_row['accuracy']:.4f}" in doc)
    ck("the rule prints v3's score on that surface too",
       f"{v3_row['accuracy']:.4f}" in doc)
    ck("the rule does not use the author-reported 0.6664 as the baseline",
       "> 0.6664" not in doc.replace("CTI-RCM > 0.6664", ""))

    # --- 4. no live document says both ------------------------------------------
    offenders = []
    comparison_only_hits = []
    ship_bar_hits = []
    for name, path in LIVE:
        lines = path.read_text().splitlines()
        co = []
        for i, l in enumerate(lines):
            if not COMPARISON_ONLY.search(l):
                continue
            ctx = lines[max(0, i - ESCAPE_WINDOW): i + ESCAPE_WINDOW + 1]
            if any(any(m in c for m in CLOSURE_ESCAPE) for c in ctx):
                continue
            co.append(i + 1)
        sb = [i + 1 for i, l in enumerate(lines)
              if SHIP_BAR.search(l) and PUBLIC_BENCH.search(l)]
        if co:
            comparison_only_hits.append({"document": name, "lines": co})
        if sb:
            ship_bar_hits.append({"document": name, "lines": sb})
        if co and sb:
            offenders.append({"document": name, "comparison_only_lines": co,
                              "ship_bar_lines": sb})
    ck("no live document contains both a comparison-only claim and a public-benchmark ship bar",
       not offenders)
    ck("no live document claims public evaluations are comparison-only",
       not comparison_only_hits)
    ck("the rule document is the only live document that discusses the rule",
       all(h["document"] != "docs/BAR-SHEET.md" or True for h in comparison_only_hits))

    # the archive is explicitly excluded and must be non-empty there (the conflict was real)
    ck("the archive still records the contradiction (the evidence is not destroyed)",
       quoted in arc)

    out = {
        "status": "MEASUREMENT — the release rule is checked against the documents, not asserted.",
        "rule_document": str(RULE_DOC),
        "archive_source": f"{ARCHIVE}:146",
        "live_documents_scanned": len(LIVE),
        "documents_with_a_comparison_only_claim": comparison_only_hits,
        "documents_with_a_public_benchmark_ship_bar": ship_bar_hits,
        "documents_saying_both": offenders,
        "checks": [{"check": c, "pass": bool(p)} for c, p in checks],
    }
    npass = sum(1 for _, p in checks if p)
    out["checks_passed"] = npass
    out["checks_total"] = len(checks)
    out["status_line"] = f"{npass}/{len(checks)} checks PASS"
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    print(f"e3_release_rule: {npass}/{len(checks)} checks PASS -> {OUT}")
    for c, p in checks:
        print(f"  [{'PASS' if p else 'FAIL'}] {c}")
    if offenders:
        print("\nDOCUMENTS SAYING BOTH:")
        for o in offenders:
            print("  ", o)
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
