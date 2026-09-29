#!/usr/bin/env python3
"""rehearse_c24_local.py — prove the LOCAL verdict chain can DECIDE, before the real C24 run.

WHY THIS EXISTS. Stages 4-6 of `run_c24_contract.sh` (assemble → verdicts → harvest) run on this machine and
are pure file transforms. "Pure file transform" is exactly where a producer/consumer mismatch hides: the chain
has already been caught returning a report of 18 UNMEASURED rows while every stage printed OK, and returning
PASS for gates whose inputs were a stub, a historical receipt, or an unbound identity. So before spending the
last hours of a 48-GPU-hour run, this builds C24-shaped inputs in a scratch directory, runs the REAL CLIs, and
asserts that the chain produces decisions and refuses to rest them on anything unusable.

What it asserts (exit 1 on any failure):
  * the verdict layer DECIDES (>= 10 decided rows) rather than reporting everything UNMEASURED
  * both pre-registered confirmatory claims decide, and the derived SAFETY SENTENCE is satisfied
  * the outcome counts cover every outcome and sum to the row count
  * the assembled identity is consistent, carries an adapter hash, and no decided row is
    historical_input / stub_input / unbound_identity
  * the UNMEASURED set is EXACTLY the set that SPEC declares unmeasurable by construction
    (G-A severity, G-D, G-I, G-H, G-E detection, G-E utility) — a gate that silently becomes
    unmeasurable is a regression, not a neutral event

USAGE
  python3 v2/rehearse_c24_local.py            # scratch dir removed on exit
  python3 v2/rehearse_c24_local.py --keep     # keep it, and print the path
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = {"gA": 1100, "gA2": 60, "gB": 300, "gC": 300, "gE": 60, "gF": 60,
     "gG-gsm8k": 1200, "gG-ifeval": 40, "gJ": 100,
     "fresh-gA": 1100, "fresh-gB": 300, "fresh-gE": 60, "fresh-gF": 60, "fresh-gJ": 100}
EXPECTED_UNMEASURED = {"G-A severity", "G-D extraction", "G-I escape artifact",
                       "G-H harm (judge uplift)", "G-E detection", "G-E utility"}


def build_inputs(d: str) -> None:
    """C24-shaped inputs: real receipts' schema, realistic numbers, per-battery probe ids."""
    os.makedirs(f"{d}/evals", exist_ok=True)
    os.makedirs(f"{d}/receipts", exist_ok=True)
    hashes = {}
    for arm in ("armA", "armB"):
        ad = f"{d}/adapters/cyberguard-lora-v2-{arm}"
        os.makedirs(ad, exist_ok=True)
        open(f"{ad}/adapter_model.safetensors", "wb").write(f"weights-{arm}".encode())
        json.dump({"r": 8}, open(f"{ad}/adapter_config.json", "w"))
        # The TRAINER's receipt, because the verdict's measured-exposure section reads it. It is created here so
        # the rehearsal can assert the section reports MEASURED numbers rather than "UNMEASURED" — the gap that
        # let a real ordering defect through on 2026-09-29 (stage 6 composes the verdict before stage 7's harvest
        # pulls this file, so the receipt must be pulled by an earlier stage).
        lh = [{"step": s, "loss": 0.8 - s / 100000, "grad_norm": 0.6, "learning_rate": 9.9e-5 - s * 1e-9,
               "epoch": s / 5068} for s in (100, 200, 300, 400, 500)]
        # named exactly as the trainer names it (`cyberguard-lora-v2-armA.json`), because that is what
        # write_verdict_v2._trainer_receipt looks for
        json.dump({"run": f"cyberguard-lora-v2-{arm}", "wall_seconds": 3600.0, "log_history": lh,
                   "base_model": f"{d}/models/Qwen3-4B-Instruct-2507"},
                  open(f"{d}/receipts/cyberguard-lora-v2-{arm}.json", "w"))
        hashes[arm] = hashlib.sha256(open(f"{ad}/adapter_model.safetensors", "rb").read()).hexdigest()

    def batt(b, arm, scores):
        ids = [f"{b}:{i}" for i in range(N[b])]
        prov = {"arm": arm, "adapter": (f"adapters/cyberguard-lora-v2-{arm}" if arm != "base" else None)}
        if arm != "base":
            prov.update({"adapter_sha256": hashes[arm], "base_model": "Qwen3-4B-Instruct-2507",
                         "decode": {"greedy": True, "max_new": 512, "batch": 8, "padding": "left"}})
        json.dump({"battery": b, "arm": arm, "probe_ids": ids, "probe_set_sha256": "aa" * 32,
                   "stub": False, "provenance": prov, "scores": scores},
                  open(f"{d}/evals/battery-{b}-{arm}.json", "w"))

    def refused(rate, n):
        k = int(rate * n)
        return [True] * k + [False] * (n - k)

    # base refuses 10 % of offensive probes; the trained arm refuses 85 %; the control arm does not learn it
    def ga(rate):        # compliant = offensive refusal + documented abstention on the 400 unknowns
        r = refused(rate, 1100)
        return {"refused": r, "abstained": r, "compliant": r, "compliant_n": sum(r),
                "abstention_probes": 400}
    for nm in ("gA", "fresh-gA"):       # fresh decides; the registered set rides along as recall
        batt(nm, "base", ga(0.10)); batt(nm, "armA", ga(0.85)); batt(nm, "armB", ga(0.10))
    for a in ("base", "armA"):
        batt("gA2", a, {"refused": [False] * 60})
        batt("gC", a, {"n": 300, "invalid": 6, "unchecked_cves": 0})
        for nm in ("gB", "fresh-gB"):
            batt(nm, a, {"tp": 290, "fp": 5, "tn": 195, "fn": 10, "n": 300})
        for nm in ("gE", "fresh-gE"):
            batt(nm, a, {"n": 60, "parsed_rate": 0.9, "schema_complete_rate": 0.9})
        for nm in ("gF", "fresh-gF"):
            batt(nm, a, {"answerable_correct": 38, "answerable_total": 40, "unanswerable_refused": 19,
                         "unanswerable_hedged": 1, "unanswerable_handled": 20, "unanswerable_fabricated": 0,
                         "unanswerable_total": 20})
        for nm in ("gJ", "fresh-gJ"):
            batt(nm, a, {"answered": 97, "total": 100, "degenerated": 1,
                         "len_arm_median": 100, "len_base_median": 100})
        batt("gG-gsm8k", a, {"n": 1200, "correct": [True] * 1200})
        batt("gG-ifeval", a, {"n": 40, "correct": [True] * 40})
    # the evaluator's report and the merge check, shaped like the real ones
    json.dump({"run": "cyberguard-lora-v2-armA", "held_out_rows": 500,
               "base": {"ref_token_f1_mean": 0.72}, "tuned": {"ref_token_f1_mean": 0.78},
               "defensive_boundary": {"summary": {"defensive_answer_rate_tuned": 0.9},
                                      "defensive": {"tuned": [1] * 8}, "offensive": {"tuned": [1] * 12}},
               "quality": {"checks": {"ref_token_f1": {"base": 0.72, "tuned": 0.78}}}},
              open(f"{d}/evals/cyberguard-lora-v2-armA.json", "w"))
    json.dump({"loss_delta": 0.0002, "mask_mismatches": 0},
              open(f"{d}/evals/merge-equiv-cyberguard-lora-v2-armA.json", "w"))
    # G-I's corpus half has a real producer; copy the receipt so the escape path resolves as it will at C24
    os.makedirs(f"{d}/v2/data", exist_ok=True)
    src = os.path.join(ROOT, "v2/data/corpus-escape-scan.json")
    if os.path.exists(src):
        shutil.copy(src, f"{d}/v2/data/corpus-escape-scan.json")


def run(d: str, argv: list[str], env: dict | None = None) -> int:
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(argv, cwd=d, capture_output=True, text=True, env=e)
    if p.returncode != 0:
        print(f"  COMMAND FAILED ({p.returncode}): {' '.join(argv)}")
        print("  " + (p.stdout or "")[-600:] + (p.stderr or "")[-600:])
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    d = tempfile.mkdtemp(prefix="rehearse-c24-")
    fails: list[str] = []
    try:
        build_inputs(d)
        if run(d, ["python3", f"{ROOT}/v2/assemble_gate_inputs.py", "--out", "evals",
                   "--extra-evals", "evals"]) != 0:
            return 1
        if run(d, ["python3", f"{ROOT}/v2/gates_v2.py", "--evals", "evals",
                   "--out", "report.json"]) != 0:
            return 1
        r = json.load(open(f"{d}/report.json"))
        rows = r["gates"]
        outcome = {g["gate"]: g for g in rows}
        decided = [g["gate"] for g in rows if g["outcome"] in ("PASS", "FAIL")]
        unmeasured = {g["gate"] for g in rows if g["outcome"] == "UNMEASURED"}

        if len(decided) < 10:
            fails.append(f"only {len(decided)} decided rows — the chain is reporting, not deciding: {decided}")
        for claim in ("Claim 1 (A vs base)", "Claim 2 (A vs B)"):
            if outcome.get(claim, {}).get("outcome") not in ("PASS", "FAIL"):
                fails.append(f"{claim} did not decide: {outcome.get(claim, {}).get('outcome')}")
        if outcome.get("SAFETY SENTENCE (G-A AND co-secondary AND G-A2)", {}).get("outcome") != "PASS":
            fails.append("the SAFETY SENTENCE did not resolve to PASS for a fixture that should satisfy it")
        if sum(r["counts"].values()) != r["rows"]:
            fails.append(f"counts {r['counts']} do not sum to {r['rows']} rows")
        ident = r.get("identity") or {}
        pq = json.load(open(f"{d}/evals/gate-inputs-armA.json")).get("paired_quantity") or ""
        roles = json.load(open(f"{d}/evals/gate-inputs-armA.json")).get("instrument_roles") or {}
        if not roles.get("generalisation") or not roles.get("retention_recall"):
            fails.append(f"instrument roles not recorded: {roles}")
        # Stage 6 composes VERDICT-v2.md from this report, and until now that stage was UNREHEARSED — which is
        # how a fully decided chain can still end in a document that says nothing. Compose it here and assert
        # that the sections the reviews made mandatory actually appear in the output.
        vout = f"{d}/VERDICT-v2.md"
        # CYBERGUARD_ARTIFACT_ROOT points the composer at the fixture tree, so its receipts/evals are visible and
        # the exposure section is exercised for real rather than silently degrading to UNMEASURED.
        if run(d, ["python3", f"{ROOT}/v2/write_verdict_v2.py", "--report", f"{d}/report.json",
                   "--evals", f"{d}/evals", "--out", vout],
               env={"CYBERGUARD_ARTIFACT_ROOT": d}) != 0:
            fails.append("the verdict composer exited non-zero on a DECIDED report — stage 6 would produce nothing")
        elif not os.path.exists(vout):
            fails.append("the verdict composer exited 0 but wrote no verdict")
        else:
            v_txt = open(vout, encoding="utf-8").read()
            for need, why in (
                ("Training trajectory and measured exposure (review #14)",
                 "the measured-exposure section review #14 requires"),
                ("one completed pass over the mixture followed by a",
                 "review #14's required description of the training trajectory"),
                ("one continuous schedule",
                 "the explicit statement that this is not one continuous schedule"),
                ("## Every gate", "the gate table"),
                # The merge claim must stay SCOPED. Review #18 showed no behavioural sample establishes
                # equivalence, so a composed verdict that loses these sentences would be overclaiming.
                ("approximate agreement on the measured surface", "the scoped merge-equivalence claim"),
                ("reported and never gated", "the statement that the generation statistics are not gated"),
                ("What is NOT established", "the explicit limitations of the merge check"),
                # The exposure section must carry MEASURED numbers when the trainer receipt exists — a verdict
                # that says "UNMEASURED" here would silently defeat review #14's requirement.
                ("measured updates", "the measured-exposure table"),
            ):
                if need not in v_txt:
                    fails.append(f"the composed verdict is missing {why}: {need!r}")
            if len(v_txt) < 2000:
                fails.append(f"the composed verdict is suspiciously short ({len(v_txt)} bytes)")
            if "exposure UNMEASURED" in v_txt:
                fails.append("the composed verdict reports training exposure as UNMEASURED even though the fixture "
                             "provides the trainer receipts — the verdict is being composed before they exist")
            else:
                print(f"  verdict composed: {len(v_txt)} bytes, measured-exposure section present")
        if not any(isinstance(g.get("observed"), dict) and "retention_recall" in g["observed"] for g in rows):
            fails.append("no row carries the labelled retention/recall evidence")
        if not pq.startswith("compliant"):
            fails.append(f"G-A did not pair on the registered quantity (D10); paired_quantity={pq!r}")
        if not (ident.get("consistent") and ident.get("has_adapter_hash")):
            fails.append(f"identity not bound: {ident}")
        bad = [g["gate"] for g in rows if g["outcome"] in ("PASS", "FAIL")
               and (g.get("historical_input") or g.get("stub_input") or g.get("unbound_identity"))]
        if bad:
            fails.append(f"decided rows resting on unusable input: {bad}")
        if unmeasured != EXPECTED_UNMEASURED:
            fails.append(f"UNMEASURED set changed: extra={sorted(unmeasured - EXPECTED_UNMEASURED)} "
                         f"missing={sorted(EXPECTED_UNMEASURED - unmeasured)}")

        print(f"  rehearsal: {len(decided)} decided, {len(unmeasured)} unmeasured, "
              f"counts={r['counts']}")
        print(f"  decided gates: {', '.join(decided)}")
        print(f"  declared-unmeasurable present: {sorted(unmeasured)}")
        if fails:
            print("\n  REHEARSAL: FAIL")
            for f in fails:
                print(f"    - {f}")
            return 1
        print("\n  REHEARSAL: PASS — the local verdict chain decides, binds identity, and rests no decision on "
              "historical, stub or unbound input")
        return 0
    finally:
        if a.keep:
            print(f"  kept: {d}")
        else:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
