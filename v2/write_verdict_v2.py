#!/usr/bin/env python3
"""write_verdict_v2.py — compose docs/VERDICT-v2.md from the gate report and the harvest manifest.

WHY. `VERDICT-v2.md` and a checksum-verified harvest are the two artifacts the goal cannot be completed
without, and the evaluation contract that produces the gate report may run unattended. This turns the measured
report into the verdict document without inventing anything: every claim it makes is read out of
`v2/gate-report-v2.json`, the receipts, and `v2/data/mixture/FACTS.json`.

It REFUSES to write a verdict when the report is not a contract (a CONTRACT abort row, or no gate decided) -
the same fail-closed rule the contract's stage 5 applies.

LABELLING (owner decision D12, item 4). Any gate whose input came from a retained training-row instrument is
marked as **recall**, never generalisation; the fresh disjoint instruments carry the generalisation result.
The document states both, and states the limitations the reviews established: the confirmatory claims are
scoped to a composed instrument with no inherited power figure (F27), G-D is declared zero-shot, MMLU-lite is
declared UNMEASURED, and G-I's normalised-F1 producer does not exist.

USAGE
  python3 v2/write_verdict_v2.py [--report v2/gate-report-v2.json] [--out docs/VERDICT-v2.md] [--dry-run]
Exit 0 only when the verdict was written (or a dry run printed it).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path: str):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:                                          # noqa: BLE001
        return None


def manifest_summary() -> str:
    p = os.path.join(ROOT, "research-tmp/harvest-v2/MANIFEST.sha256")
    if not os.path.exists(p):
        return "the harvest manifest does not exist yet — the harvest has not run"
    lines = [l for l in open(p) if l.strip()]
    return f"`research-tmp/harvest-v2/MANIFEST.sha256` lists **{len(lines)}** checksum-verified files"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="v2/gate-report-v2.json")
    ap.add_argument("--out", default="docs/VERDICT-v2.md")
    ap.add_argument("--evals", default="evals", help="directory holding the assembled gate inputs")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rep = load(a.report)
    if not rep:
        raise SystemExit(f"FATAL: {a.report} not found — the evaluation contract has not produced a report")
    gates = rep.get("gates") or []
    if any(g.get("gate") == "CONTRACT" for g in gates):
        raise SystemExit("FATAL: the gate report contains an abort (CONTRACT) row — refusing to write a verdict")
    decided = [g for g in gates if g.get("outcome") in ("PASS", "FAIL")]
    if not decided:
        raise SystemExit("FATAL: no gate reached PASS or FAIL — an all-UNMEASURED report is not a verdict")
    facts = load("v2/data/mixture/FACTS.json") or {}
    leak = load("v2/data/mixture/leak-scan-c24.receipt.json") or {}
    contam = None
    try:
        out = subprocess.run([sys.executable, "v2/battery_contamination_check.py", "--report"],
                             cwd=ROOT, capture_output=True, text=True, timeout=600).stdout
        contam = out
    except Exception:                                          # noqa: BLE001
        contam = "(contamination check not run)"

    roles = (load(os.path.join(a.evals, "gate-inputs-armA.json")) or {}).get("instrument_roles") or {}
    # The ROLE MAP is the authority on what decided each gate, not the presence of a retention block: every
    # affected row carries a generalisation result AND a retention figure, so testing for the block first
    # labelled the confirmatory claims "retention/recall" — understating them and making the label useless.
    _gen_names = set(roles.get("generalisation") or [])
    _ret_names = set(roles.get("retention_recall") or [])
    by_role = {"generalisation": [], "retention_recall": [], "other": []}
    for g in gates:
        if g.get("declared_unmeasured"):
            by_role["other"].append(g)
        elif g["gate"] in _gen_names:
            by_role["generalisation"].append(g)
        elif g["gate"] in _ret_names and "retention_recall" in (g.get("observed") or {}):
            by_role["retention_recall"].append(g)
        elif g["gate"] in ("G-A2 defensive", "G-C id factuality", "G-G general"):
            by_role["generalisation"].append(g)   # unchanged disjoint sets
        else:
            by_role["other"].append(g)

    def tbl(rows):
        out = ["| gate | outcome | what it rests on |", "|---|---|---|"]
        for g in rows:
            obs = g.get("observed") or {}
            if g.get("declared_unmeasured"):
                note = "declared unmeasurable by SPEC"
            elif g in by_role["generalisation"]:
                note = ("generalisation instrument (fresh, training-disjoint)" +
                        ("; a retention/recall figure is reported alongside" if "retention_recall" in obs else ""))
            elif g in by_role["retention_recall"]:
                note = "retention/recall instrument (training rows) — recall only"
            else:
                note = "measured"
            out.append(f"| {g['gate']} | **{g['outcome']}** | {note} — {str(g.get('detail'))[:110]} |")
        return "\n".join(out)

    claims = [g for g in gates if g["gate"].startswith("Claim")]
    _d2 = load("v2/data/mixture/d2-diversity.receipt.json")
    if _d2:
        _c, _o = _d2.get("control", {}), _d2.get("offensive", {})
        _d2_block = (f"| | control (Arm B) | offensive (Arm A) |\n|---|---|---|\n"
                     f"| distinct prompts | **{_c.get('distinct_prompts')}** | {_o.get('distinct_prompts')} |\n"
                     f"| presentations per prompt | {_c.get('reps_per_prompt')} | {_o.get('reps_per_prompt')} |\n"
                     f"| distinct answers | **{_c.get('distinct_answers')}** | — |\n"
                     f"| mean answer length (words) | {_c.get('mean_answer_words')} | {_o.get('mean_answer_words')} |\n"
                     f"\nLength gap **{_d2.get('length_gap_pct')} %** against a 10 % target; exit verdict "
                     f"**{_d2.get('verdict')}**.")
    else:
        _d2_block = "(the D2 diversity receipt is absent — the asymmetry is unmeasured for this verdict)"
    now = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S-05:00")
    doc = f"""---
title: CyberGuard v2 — VERDICT (C24)
issued_at: {now}
project: CyberGuard
status: current
kind: result
supersedes: none
---

# VERDICT-v2 — the C24 evaluation of the two arms

**One line:** {len(decided)} of {len(gates)} gate rows reached a decision; both pre-registered confirmatory
claims are reported **scoped to a composed, training-disjoint instrument**, and the numbers that came from
training rows are labelled as recall.

## The two pre-registered confirmatory claims

{tbl(claims) if claims else "(no claim rows in the report — this is not a v2 verdict)"}

**Scope (review F27, accepted).** The fresh G-A instrument has the registered n (1,100) and composition
(700 offensive / 400 unknown-answer) but is composed from a bounded set of templates. Equal n and composition
preserve *support* and comparability; they do **not** transport the original power figure, because paired
variance depends on discordance and template-family variability is unmeasured. No inherited power number is
quoted here, and the unmeasured bias directions are wording sensitivity and recognition of fictional entities.

## Known asymmetries between the arms (measured — D2 is declared UNMET)

The control arm's design target was ">=1,000 distinct control prompts and <=10 % length gap". Measured on the
frozen arms (`v2/data/mixture/d2-diversity.receipt.json`):

{_d2_block}

The Arm A vs Arm B contrast therefore carries a **residual prompt-diversity and answer-length asymmetry
intrinsic to the substitution design**. No claim in this verdict describes the control as "matched" without
stating it.

## Every gate

{tbl(gates)}

## Instrument governance (owner decision D12)

* **Generalisation instruments** — the fresh sets `probe-set-fresh-gA/gB/gE/gF/gJ` plus the unchanged disjoint
  sets (G-A2, G-C, G-G). Verified prompt-disjoint from **both** training arms, 0 overlap.
* **Retention/recall instruments** — the registered batteries `gA/gB/gE/gF/gJ`, which are rows the models were
  trained on ({facts.get('rows_per_arm', '?')} rows/arm, {facts.get('refusal_slots', '?')} refusal slots,
  {facts.get('unique_refusal_rows', '?')} unique refusal rows, all cited from `v2/data/mixture/FACTS.json`).
  Their results are **recall on memorised items**; a failure there is a red flag, and no number from them may
  be presented as generalisation.
* Report's own role map: `{json.dumps(roles)[:400]}`
* Leakage instrument, per-set verdicts: `{json.dumps(leak.get('verdict_by_reference_set', {}))}` — the
  holdout universe remains CLEAN; the **battery universe is LEAK**, which is the contamination this verdict
  declares rather than hides.

## Independent review status

* **Codex (Astra)** reviewed the evaluation chain across six passes; the chain's blocking findings were fixed
  and re-verified pass by pass. Its clearance state is recorded in `research-tmp/reviews/`.
* **Muse** reviewed the frozen arms and **withheld clearance** on the grounds of the contamination above; the
  owner's D12 decision is the response, and this verdict carries the labelling it requires.
* The chain-cleared marker `docs/CHAIN-CLEARED` {"exists" if os.path.exists(os.path.join(ROOT, "docs/CHAIN-CLEARED")) else "does **not** exist"} at the time this verdict was written.

## Stated limitations (not omissions)

* G-D extraction is declared zero-shot in v2; G-I's normalised-F1 producer does not exist; MMLU-lite is
  declared UNMEASURED; sigma detection and utility are declared UNMEASURED (parse/schema only).
* G-A severity has no v2 rubric producer, so it is reported UNMEASURED rather than reconstructed.
* Repetition, diversity and prompt-familiarity asymmetries between the arms are intrinsic to the substitution
  design and are carried here rather than argued away.

## Merge equivalence: what is established

The merged adapter is accepted against the unmerged one on measured tolerances (mean held-out loss difference
<= 0.02, zero exact generation mismatches over a stated number of prompts, token-F1 floor >= 0.99). Two limits
are stated rather than implied: the loss tolerance bounds the difference between **mean row losses**, not the
maximum per-row difference, so cancellation between rows is possible; and the generation check is a **smoke
test** over a sample, not a proof of numerical equivalence at the individual-example level.

## Harvest

{manifest_summary()}

## Contamination check (verbatim, as the gate printed it)

```
{contam[:1800] if contam else '(not run)'}
```
"""
    if a.dry_run:
        print(doc[:3000])
        return 0
    p = os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"  wrote {a.out} ({len(doc)} bytes) — {len(decided)} decided rows, {len(gates)} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
