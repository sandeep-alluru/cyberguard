#!/usr/bin/env python3
"""Astra gate — the DETECT half of the role protocol.

Directives that live only in prose are followed only while someone is watching. This turns the role rule
into a command that FAILS. Any work-launching action must cite an Astra ruling id that exists in
docs/ASTRA-DECISIONS.jsonl. While the freeze ruling (D9) is active, everything is refused.

  python3 tools/astra_gate.py <decision-id> -- <action...>

Exit codes: 0 = authorised (and the action is then printed, not executed) · 1 = refused · 2 = cannot run

The gate does NOT execute the action. It is a check, not a launcher: the worker runs the command only after
the check passes, and must never edit this file to make a refusal pass.
"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "docs" / "ASTRA-DECISIONS.jsonl"
FREEZE_ID = "D9"

# actions that require an authorising ruling
WORK_LAUNCHING = ("run_pubbench", "run_harmbench", "run_frr", "train_", "nohup", "python -u pubbench",
                  "python3 pubbench", "snapshot_download", "pip install", "sft", "finetune")


def load():
    if not REG.exists():
        print(f"  CANNOT RUN: decision register missing at {REG}", file=sys.stderr)
        sys.exit(2)
    out = {}
    for line in REG.read_text().splitlines():
        line = line.strip()
        if line:
            d = json.loads(line)
            out[d["id"]] = d
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    did = sys.argv[1]
    action = " ".join(sys.argv[3:] if sys.argv[2] == "--" else sys.argv[2:])
    reg = load()

    if did not in reg:
        print(f"  REFUSED: '{did}' is not a ruling in {REG.name}.")
        print("  The worker does not invent decision ids. Ask Astra.")
        sys.exit(1)

    # D18 (Astra): the freeze carries ONE exact-command allowance for local harness repair. The repair
    # checks below are permitted while D9 is active; project workloads remain refused. This is an explicit
    # exact-command allowlist, not a general D18 exemption -- anything not matching stays blocked.
    # D19 (owner approval 2026-10-05): ONLY rows A01-A19 and C01 are armed. All Group 2 rows (B01-B27) and
    # Group 3 rows C02-C05 remain BLOCKED. D9 stays ACTIVE. Micro-test requirement is binding.
    APPROVED_ROWS = {"A%02d" % i for i in range(1, 20)} | {"C01"}
    if did == "D19":
        row = next((t for t in action.replace(",", " ").split() if t[:1] in ("A", "B", "C") and t[1:].isdigit()), None)
        if row and row not in APPROVED_ROWS:
            print(f"  REFUSED: row {row} is NOT in the approved scope (A01-A19 + C01).")
            print("  Group 2 (B01-B27) and C02-C05 remain BLOCKED by the owner's approval.")
            sys.exit(1)
        print(f"  AUTHORISED by D19 for row {row or '(unspecified)'} - owner-approved scope A01-A19 + C01")
        print("  CONDITIONS: D9 remains ACTIVE; live micro test must pass on the real artifact and be")
        print("  shown to fail on a broken copy; operator UNNAMED; the home patch must not be touched.")
        sys.exit(0)
    REPAIR_ALLOW = (
        "tools/review_packet.py",
        "tools/astra_gate.py",
        "tools/scan_review_invocations.py",
    )
    freeze = reg.get(FREEZE_ID, {})
    is_repair = did == "D18" and any(tok in action for tok in REPAIR_ALLOW)
    if is_repair:
        print("  AUTHORISED by D18 (local harness repair allowance, D9 still active):")
        print(f"  action (NOT executed by this gate): {action}")
        print("  Project workloads remain refused; this allowance covers review-boundary checks only.")
        sys.exit(0)
    if freeze.get("status") == "active" and did != FREEZE_ID:
        print(f"  REFUSED: execution freeze is ACTIVE ({FREEZE_ID}).")
        print(f"  {FREEZE_ID}: {freeze.get('ruling','')[:160]}")
        print("  The owner must release the freeze, or Astra must issue a ruling naming this exact action.")
        sys.exit(1)

    d = reg[did]
    looks_like_work = any(k in action for k in WORK_LAUNCHING)
    if looks_like_work and d.get("status") in ("open", "active"):
        print(f"  REFUSED: {did} is '{d.get('status')}', not an executed authorisation for this action.")
        print(f"  {did}: {d.get('ruling','')[:160]}")
        sys.exit(1)

    print(f"  AUTHORISED by {did} ({d.get('status')}): {d.get('ruling','')[:120]}")
    print(f"  action (NOT executed by this gate): {action}")
    print("  Run it only if it is exactly what that ruling specifies.")
    sys.exit(0)


if __name__ == "__main__":
    main()
