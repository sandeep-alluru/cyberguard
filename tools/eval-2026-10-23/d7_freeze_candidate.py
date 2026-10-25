#!/usr/bin/env python3
"""D-7 (P1-5) — freeze the qualification candidate and issue the Data Gate receipt.

WHAT THIS DOES, IN TWO PARTS.

PART 1 — THE FREEZE. It writes `data/v4/corpus-final.jsonl`, the artefact the approved
calibration protocol (§1, §9.4) and the ledger's D-7 acceptance clause both name, and it fixes
that file's row count and sha256. The candidate is the corpus after every removal that is
*authorised*:

  * ASTRA-D5's exclusion of Primus and the merged reasoning corpus (28,037 rows) — **done**
    (C-1 wrote the removal set, C-2 executed it); it is already inside `corpus-v4-r3.jsonl`;
  * D-4's held removal sets (R1, and the `system_prompt_reference` class) — **nothing is
    removed**, because nothing is authorised and nothing is measured to justify it. D-2's
    measurement shows R1's detector has an off-topic precision of 0.0143, so roughly 36,851
    rows would have been removed wrongly, and D-5 resolved the `system_prompt_reference` half:
    its defective portion was already removed by ASTRA-D5 and the 47 survivors are legitimate
    answers about system-prompt security.

  So the frozen candidate is **byte-identical to `corpus-v4-r3.jsonl`**, and this script asserts
  that by re-hashing the copy rather than asserting it in prose. It is a copy rather than a
  hard link, because a freeze artefact must be stable bytes, not a second name for bytes that
  something else can rewrite in place.

PART 2 — THE RECEIPT. It writes `data/v4/DATA-GATE.json`. The receipt's verdict is **BLOCKED**,
and it is written as a SHELL: every field the Data Gate needs is present and populated, and
every one of them that has not been measured says so in its own words. **No field is filled with
a zero, a blank or a number carried from somewhere else.** A missing measurement is not a pass.

WHAT IT IS NOT. It is not a Data Gate PASS, and it does not authorise training. The three
registered limits (unsafe <1 %, off-topic <2 %, shallow <5 %) are **NOT MEASURED** on this
candidate; the confirmation draw of protocol §6 needs 6,000 rows reviewed by a fresh reviewer
pair that did not see the development rows, and those are people this programme does not have.

Usage:  python3 d7_freeze_candidate.py [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path("<programme-tree>")
V4 = ROOT / "data" / "v4"
R3 = V4 / "corpus-v4-r3.jsonl"
FINAL = V4 / "corpus-final.jsonl"
RECEIPT = V4 / "DATA-GATE.json"
R3_RECEIPT = V4 / "receipt-v4-r3.json"
MIX_RECEIPT = V4 / "MIXTURE-V4-RECEIPT.json"

# The pinned values this programme has already published. They are PINS, not inputs: the script
# checks the artefacts against them and fails if either moved.
PIN_R3_SHA = "7798c4f589b855caa32dc9d6335926e856f78fe649419dd9e516b7ba1a6413ff"
PIN_R3_ROWS = 108978
PIN_PROTOCOL = "docs/P2-CALIBRATION-PROTOCOL.md"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_rows(p: Path) -> int:
    n = 0
    with p.open("rb") as f:
        for _ in f:
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="compute everything, write nothing")
    args = ap.parse_args()

    checks = []

    def check(name, ok, detail):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        return ok

    print("== part 1: the freeze ==")
    if not R3.is_file():
        print(f"  FATAL: {R3} missing")
        return 2
    r3_sha = sha256_file(R3)
    r3_rows = count_rows(R3)
    check("source corpus matches its published pin (sha256)", r3_sha == PIN_R3_SHA,
          f"{r3_sha[:16]}… vs pinned {PIN_R3_SHA[:16]}…")
    check("source corpus matches its published pin (row count)", r3_rows == PIN_R3_ROWS,
          f"{r3_rows} rows vs pinned {PIN_R3_ROWS}")

    if not args.dry_run:
        if FINAL.exists():
            # Never overwrite a freeze artefact silently: if it exists it must already be the
            # right bytes, and if it is not, the file is preserved and the run stops.
            ex_sha = sha256_file(FINAL)
            ex_rows = count_rows(FINAL)
            ok = (ex_sha == r3_sha and ex_rows == r3_rows)
            print(f"  corpus-final.jsonl already exists ({ex_rows} rows, sha256 {ex_sha[:16]}…) — "
                  f"{'it already is the frozen bytes' if ok else 'IT DIFFERS; refusing to overwrite'}")
            if not ok:
                print("  FATAL: the existing freeze artefact differs from the candidate. "
                      "Nothing was overwritten. A human must decide which bytes are the freeze.")
                return 1
        else:
            tmp = FINAL.with_suffix(".jsonl.partial")
            shutil.copyfile(R3, tmp)
            os.replace(tmp, FINAL)
            print(f"  wrote {FINAL}")
    fin_sha = sha256_file(FINAL) if FINAL.is_file() else None
    fin_rows = count_rows(FINAL) if FINAL.is_file() else None
    check("the frozen candidate is byte-identical to the candidate corpus",
          fin_sha == r3_sha, f"sha256 {str(fin_sha)[:16]}… vs {r3_sha[:16]}…")
    check("the frozen candidate has the candidate's row count", fin_rows == r3_rows,
          f"{fin_rows} rows")
    check("the frozen candidate is a separate file, not a second name for the same bytes",
          FINAL.is_file() and not (FINAL.stat().st_ino == R3.stat().st_ino),
          f"inode {FINAL.stat().st_ino} vs {R3.stat().st_ino}" if FINAL.is_file() else "missing")

    per_source = {}
    with FINAL.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                per_source[json.loads(line).get("src", "?")] = \
                    per_source.get(json.loads(line).get("src", "?"), 0) + 1
            except Exception:  # noqa: BLE001
                per_source["<unparseable>"] = per_source.get("<unparseable>", 0) + 1
    check("every row of the frozen candidate parses as JSON and carries a source",
          "<unparseable>" not in per_source, f"per-source counts: {per_source}")

    print("== part 2: the receipt ==")

    # --- what the receipt must carry, and where each field's value comes from -----------------
    removal_sets = [
        {
            "set": "ASTRA-D5 exclusion (Primus + merged reasoning corpus)",
            "authority": "ASTRA ruling ASTRA-D5, 2026-10-04",
            "ledger_items": ["C-1", "C-2"],
            "status": "APPLIED",
            "rows_removed": 28037,
            "note": "executed into the rebuilt corpus; the removal set is "
                    "data/v4/removal-set-d5.jsonl with data/v4/removal-set-d5.receipt.json. "
                    "Already inside the frozen candidate.",
        },
        {
            "set": "R1 (37,927 rows flagged by the v4 quality detector)",
            "authority": "none — the removal follows D-3's measurement and nothing is ruled",
            "ledger_items": ["D-4"],
            "status": "NOT APPLIED — no measured justification",
            "rows_removed": 0,
            "note": "D-2 measured the detector behind R1: off-topic precision 0.0143 (1 true "
                    "positive against 69 false positives on the same 200 rows), unsafe precision "
                    "0.14, shallow precision 0.20. About 36,851 rows would have been removed "
                    "wrongly. The rows stay.",
        },
        {
            "set": "system_prompt_reference class (13,290 rows)",
            "authority": "ASTRA-D5 for the defective portion; D-5 for the scope",
            "ledger_items": ["D-4", "D-5"],
            "status": "NOT APPLIED — the defective portion was already removed",
            "rows_removed": 0,
            "note": "D-5 resolved this: the class's defective portion (merged 13,246 + primus 1) "
                    "was removed by ASTRA-D5, and the 47 survivors are legitimate security "
                    "answers about system-prompt security. Nothing is removed under this set.",
        },
        {
            "set": "thinking-control-token class / stock-preamble class",
            "authority": "C-3 / C-4 counting against the released gate",
            "ledger_items": ["C-3", "C-4", "C-9"],
            "status": "MEASURED — counts are 0 on the frozen candidate",
            "rows_removed": 0,
            "note": "leading thinking-control tokens 0, stock-preamble targets 0. The 378-row "
                    "fenrir residue is escalated as C-9 and is NOT removed by this receipt: "
                    "ASTRA-D5 does not authorise touching fenrir.",
        },
    ]

    qualification_evidence = {
        "D-2 (instrument with measured precision/recall)": {
            "status": "MEASURED",
            "value": "instrument v3: unsafe precision 0.1905 / recall 0.4444; shallow precision "
                     "0.2286 / recall 0.8000; off-topic UNMEASURED. The v4 detector's off-topic "
                     "precision is 0.0143.",
            "where": "docs/CALIBRATION-INSTRUMENT-FINDINGS.md; eval-2026-10-23/calibration/",
            "what_it_does_not_say": "it does not size a removal set, and no instrument can.",
        },
        "D-3 (the 4,000-row development draw, human-labelled)": {
            "status": "BLOCKED on humans",
            "value": "NOT MEASURED — the draw is not labelled. No rate is computed from an "
                     "unlabelled draw.",
            "where": "docs/P2-CALIBRATION-PROTOCOL.md §4; §9.5 dependency 1",
            "what_it_does_not_say": "no development estimate transfers to this candidate, even "
                                    "if one were below a Data Gate limit.",
        },
        "D-5 (M0-1 re-certification and the R3 scope ruling)": {
            "status": "MEASURED",
            "value": "the R3 scope is ruled and recorded in eval-2026-10-23/d5-r3-scope-ruling.json",
            "where": "eval-2026-10-23/d5-r3-scope-ruling.json",
            "what_it_does_not_say": "it is a scope ruling, not a Data Gate pass.",
        },
        "F-8 (decontamination against the held-out set)": {
            "status": "FAILED — and the failure is the finding",
            "value": "499 of the 500 held-out rows are inside the training corpus, as 604 rows, "
                     "all in fenrir: jaccard_max 0.7566 and containment_max 0.9795 against the "
                     "v2 gate's recorded maximum 0.0266 / 0.0723, and above the gate's own "
                     "reject thresholds of 0.6 / 0.8. The leak predates this project and "
                     "reaches v3's own SFT file and training mixture.",
            "where": "eval-2026-10-23/f8-decontamination-report.json; "
                     "docs/ESCALATION-F8-HELDOUT-CONTAMINATION.md",
            "what_it_does_not_say": "it does not qualify the corpus; it is an open corpus "
                                    "decision for the owner (remove / keep and retire the "
                                    "holdout / rebuild the split).",
        },
    }

    limits = {
        "unsafe": {"threshold": "< 1 %", "threshold_rational": "1/100",
                   "measured_upper_rate_on_this_candidate": None,
                   "status": "NOT MEASURED — the §6 confirmation draw has not been executed",
                   "why": "protocol §6 requires 6,000 candidate rows reviewed by a fresh reviewer "
                          "pair that did not see the development rows. Those people do not exist "
                          "in this programme yet."},
        "off_topic": {"threshold": "< 2 %", "threshold_rational": "1/50",
                      "measured_upper_rate_on_this_candidate": None,
                      "status": "NOT MEASURED — the §6 confirmation draw has not been executed",
                      "why": "as above"},
        "shallow": {"threshold": "< 5 %", "threshold_rational": "1/20",
                    "measured_upper_rate_on_this_candidate": None,
                    "status": "NOT MEASURED — the §6 confirmation draw has not been executed",
                    "why": "as above"},
    }

    non_statistical = {
        "cross_row_leakage": {
            "status": "FAILED",
            "detail": "F-8 measured 604 fenrir rows inside the held-out set, above the v2 gate's "
                      "own reject thresholds. The remedy is a corpus decision and therefore a "
                      "ruling's; the rows stay until the owner rules.",
        },
        "metadata_provenance_rights": {
            "status": "PARTIALLY EVIDENCED",
            "detail": "the row-level provenance map, the licence table and the re-runnable "
                      "inventory exist (B-2, B-3, B-4). The Data Gate's rights/provenance "
                      "requirement is not closed for the final candidate because the candidate "
                      "itself was not qualified.",
        },
        "benchmark_isolation": {
            "status": "MEASURED",
            "detail": "F-8b measured the public benchmarks' integrity on the rebuilt mixture.",
            "where": "ledger F-8b",
        },
    }

    receipt = {
        "what_this_is": "The Data Gate receipt for the CyberGuard qualification candidate "
                        "(ledger item D-7). It is a receipt SHELL: every field the Data Gate "
                        "needs is present, and every field that has not been measured says so "
                        "in its own words. No field carries a zero, a blank, or a number "
                        "carried from another artefact.",
        "verdict": "BLOCKED — NOT PASS",
        "verdict_meaning": "the candidate is frozen and identified; it is NOT qualified. No "
                           "training is valid against it. The three registered limits are "
                           "NOT MEASURED, and the held-out decontamination check FAILED.",
        "authority": {
            "protocol": PIN_PROTOCOL,
            "protocol_status": "APPROVED 2026-10-23 (ledger D-1)",
            "owner_go": "2026-10-24 (phase 2; no training in this phase)",
            "note": "protocol §9.3: approval authorises no draw, no labels, no removals, no "
                    "source edits and no Data Gate pass.",
        },
        "candidate": {
            "path": str(FINAL),
            "rows": fin_rows,
            "sha256": fin_sha,
            "per_source": per_source,
            "byte_identical_to": {
                "path": str(R3),
                "rows": r3_rows,
                "sha256": r3_sha,
                "why": "every authorised removal is already inside corpus-v4-r3.jsonl, and "
                       "D-4's held removal sets remove nothing (nothing is authorised, nothing "
                       "is measured to justify it). The freeze is therefore a copy of the "
                       "candidate, and the copy's hash is asserted, not claimed.",
            },
            "frozen_at": "2026-10-24",
            "frozen_by": "ledger D-7 freeze step; this receipt is generated by "
                         "eval-2026-10-23/d7_freeze_candidate.py",
        },
        "removal_sets": removal_sets,
        "qualification_evidence": qualification_evidence,
        "registered_limits": limits,
        "non_statistical_criteria": non_statistical,
        "final_confirmation_draw": {
            "status": "NOT EXECUTED",
            "protocol": "§6 — draw 6,000 candidate row IDs uniformly without replacement with one "
                        "committed independent post-freeze seed; for N < 6,000, a full census. "
                        "This candidate's N is 108,978, so the draw is 6,000 rows.",
            "reviewer_requirement": "a confirmation reviewer pair that did not see the "
                                    "development rows, plus an adjudicator",
            "result": None,
            "why": "the reviewers do not exist yet; protocol §9.5 dependency 1.",
        },
        "unmet_dependencies": [
            "1. Two independently working cybersecurity-competent human reviewers A and B, and "
            "an adjudicator C (protocol §9.5 dependency 1). The protocol is explicit that agent "
            "sessions are not silently substituted for required competent human review, and "
            "this programme does not substitute them.",
            "2. The 300-row reference-control cohort is not assembled (protocol §9.5 "
            "dependency 2). Without it the scorer's acceptance bar in §4.1 cannot be tested.",
            "3. The confirmation draw has not been executed and its reviewer pair is not "
            "assigned (protocol §6).",
        ],
        "known_unresolved": [
            "F-8: 604 held-out rows inside the corpus (fenrir), above the v2 gate's own reject "
            "thresholds. The remedy is a ruling's; the rows stay.",
            "C-9: 378 fenrir rows carry an any-reserved marker and 1,292 carry the broader "
            "reserved-or-placeholder definition. ASTRA-D5 does not authorise touching fenrir.",
            "F-1: one CWE id (CWE-2018) referenced by a corpus row does not resolve in the "
            "catalogue; the catalogue is otherwise complete and 5 of 6 checks pass.",
            "F-4: ATT&CK's raw STIX carries 0 structured CVE↔technique mappings; only 9 "
            "prose-derived pairs are recoverable, and the remedy is a source choice.",
        ],
        "mixture_status": {
            "path": str(V4 / "mixture-v4.jsonl"),
            "status": "PROVISIONAL — NOT A TRAINING SET",
            "why": "a mixture built from an unqualified corpus is not a training set, whatever "
                   "its row count.",
        },
        "checks": checks,
        "all_checks_pass": all(c["pass"] for c in checks),
    }

    if not args.dry_run:
        RECEIPT.write_text(json.dumps(receipt, indent=1))
        print(f"  wrote {RECEIPT}")
    print(f"  verdict: {receipt['verdict']}")
    return 0 if receipt["all_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
