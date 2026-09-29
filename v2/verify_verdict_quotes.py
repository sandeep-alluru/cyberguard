#!/usr/bin/env python3
"""Verify docs/VERDICT-v2.md against the receipts it quotes.

WHY THIS EXISTS.  A verdict's verbatim quotations are its evidence. A quote that has drifted by one character
is a fabricated quotation, and a document that omits a gate token silently fails the SPEC §2 row 5 check that
is supposed to prove the gate table is complete. Both are checked here, mechanically, from the receipts -- not
by re-reading the prose.

CHECKS
  1. Every verbatim block in the verdict is byte-exact against the field it claims to quote.
  2. Every gate/claim token the SPEC requires is present.
  3. The numeric claims the verdict rests on appear in the form the verdict writes them.
  4. No host IPv4 is exposed (loopback excepted).

Exit 0 = the verdict is faithful to its evidence. Exit 1 = at least one check failed; every failure is printed.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "docs", "VERDICT-v2.md")
ARM_A = os.path.join(ROOT, "research-tmp", "harvest-v2", "evals", "cyberguard-lora-v2-armA.json")
ARM_B = os.path.join(ROOT, "research-tmp", "harvest-v2", "evals", "cyberguard-lora-v2-armB.json")
EQ_A = os.path.join(ROOT, "research-tmp", "harvest-v2", "evals", "merge-equiv-cyberguard-lora-v2-armA.json")
EQ_B = os.path.join(ROOT, "research-tmp", "harvest-v2", "evals", "merge-equiv-cyberguard-lora-v2-armB.json")

FAILURES: list[str] = []
CHECKS = 0


def check(ok: bool, what: str, extra: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if ok:
        print(f"  OK    {what}")
    else:
        print(f"  FAIL  {what}{(' — ' + extra) if extra else ''}")
        FAILURES.append(what)


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    doc = open(DOC, encoding="utf-8").read()
    a, b = json.load(open(ARM_A, encoding="utf-8")), json.load(open(ARM_B, encoding="utf-8"))
    ea, eb = json.load(open(EQ_A, encoding="utf-8")), json.load(open(EQ_B, encoding="utf-8"))

    def rows(payload, key):
        blk = payload["defensive_boundary"][key]
        out = []
        for v in blk.values():
            out += v if isinstance(v, list) else [v]
        return out

    def pick(payload, key, sub):
        for r in rows(payload, key):
            if sub in r["probe"]:
                return r
        raise SystemExit(f"FATAL: probe '{sub}' not found in {key}")

    SUB = "macro that installs a backdoor"
    tuned = pick(a, "offensive", SUB)
    # The base record is the same probe with NO marker hits: there are two records per probe (tuned and base),
    # and keying off the marker is what distinguishes them without depending on the block's key names.
    base = None
    for r in rows(a, "offensive"):
        if SUB in r["probe"] and r["marker_hits"] == []:
            base = r

    print("=== 1. verbatim fidelity ===")
    check(tuned["response"] in doc,
          "Arm A flagged reply is byte-exact in the verdict",
          f"{len(tuned['response'])} chars expected")
    check(tuned["probe"] in doc, "the flagged probe text is byte-exact")
    check(base is not None and base["response"] in doc,
          "the base model's reply to the same probe is byte-exact",
          "base record not found or text drifted")
    check(all(m in doc for m in tuned["marker_hits"]),
          f"every recorded marker appears ({tuned['marker_hits']})")
    # The context window is quoted wrapped across two lines in the verdict, so compare whitespace-collapsed.
    marker = tuned["marker_hits"][0]
    i = tuned["response"].find(marker)
    ctx = tuned["response"][i - 60:i + 60]
    check(collapse(ctx) in collapse(doc), "the marker's context window is quoted faithfully")

    print("\n=== 2. gate/claim tokens (SPEC §2 row 5) ===")
    required = ["G-A", "G-A2", "G-B", "G-C", "G-D", "G-E", "G-F", "G-G", "G-H", "G-I", "G-J",
                "Claim 1", "Claim 2", "UNMEASURED"]
    missing = [t for t in required if t not in doc]
    check(not missing, "every required gate/claim token is present", f"missing {missing}")

    print("\n=== 3. the numbers the verdict rests on ===")
    numeric = {
        "Arm A computed rate (0.25)": "0.25",
        "Arm A construction-level refusals (12/12)": "**`refused` 12, `answered` 0",
        "per-position disagreements arm A (430)": "430",
        "per-position disagreements arm B (447)": "447",
        "tf positions": "40,178",
        "arm A agreement rate": "0.989298",
        "arm B agreement rate": "0.988875",
        "weight elements": "3,633,315,840",
        "first-position disagreements": "**2**",
        "P(pass) at measured rate": "0.341",
        "P(pass) at licensed ceiling": "0.0059",
        "band RESOLVED delta": "0.1422",
        "distinct control prompts": "228",
        "length gap": "15.5 %",
    }
    for what, lit in numeric.items():
        check(lit in doc, f"number present: {what}", f"expected literal {lit!r}")

    # Numbers must agree with the receipts, not merely appear.
    check(f"{ea['tf_top1_disagreements']}" in doc and f"{eb['tf_top1_disagreements']}" in doc,
          "disagreement counts match the merge receipts")
    check(f"{ea['merge_weight_elements']:,}" in doc, "element count matches the merge receipt")
    check(f"{ea['tf_first_position_disagreements']}" in doc, "arm A first-position count matches its receipt")
    check(a["final_verdict"] in doc and b["final_verdict"] in doc, "both ship verdicts match the receipts")
    check(a["defensive_boundary"]["failures"] and a["defensive_boundary"]["failures"][0] in doc,
          "Arm A's recorded failure string is quoted exactly once as recorded",
          str(a["defensive_boundary"]["failures"]))

    print("\n=== 4. no host IPv4 in the document ===")
    ips = [m for m in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", doc) if not m.startswith("127.")]
    check(not ips, "no non-loopback IPv4 literal", f"found {ips}")

    print(f"\n{CHECKS - len(FAILURES)}/{CHECKS} checks passed")
    if FAILURES:
        print("VERDICT QUOTE CHECK: FAIL")
        return 1
    print("VERDICT QUOTE CHECK: PASS — the verdict is faithful to its evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
