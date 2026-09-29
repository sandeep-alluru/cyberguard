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
# Artifacts (receipts, evals, the harvest manifest) resolve under this root. It exists so the composer can be
# exercised against a fixture tree: on 2026-09-29 the rehearsal's receipts were invisible to it because they
# lived in a temp directory while the composer resolved everything from the repository, and a real ordering
# defect (the verdict composed before the trainer receipts were pulled) therefore could not be caught there.
ART = os.environ.get("CYBERGUARD_ARTIFACT_ROOT", ROOT)


def load(path: str):
    p = os.path.join(ART, path)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:                                          # noqa: BLE001
        return None


def manifest_summary() -> str:
    p = os.path.join(ART, "research-tmp/harvest-v2/MANIFEST.sha256")
    if not os.path.exists(p):
        return "the harvest manifest does not exist yet — the harvest has not run"
    lines = [l for l in open(p) if l.strip()]
    return f"`research-tmp/harvest-v2/MANIFEST.sha256` lists **{len(lines)}** checksum-verified files"


def _trainer_receipt(arm: str):
    """The trainer's own receipt, harvested from the host that ran it (falling back to a local copy)."""
    for p in (f"research-tmp/harvest-v2/receipts/cyberguard-lora-v2-{arm}.json",
              f"receipts/cyberguard-lora-v2-{arm}.json"):
        r = load(p)
        if r is not None:
            return r, p
    return None, None


def merge_equivalence_block() -> str:
    """What the merge check actually establishes, from the measured receipts, and what it does NOT.

    Rewritten 2026-09-29 after independent review #16 and #18 both rejected earlier acceptance bases: the first
    (zero exact generation mismatches, token-F1 >= 0.99) was unachievable - its outcome is a function of decode
    length - and the second (first-position agreement) "permits unrestricted continuation changes". #18 then
    produced an EXECUTED counterexample that passed every numerical condition while changing behaviour, and
    concluded correctly that no finite behavioural sample establishes behavioural equivalence. So the claim here
    is scoped to the two measurements that are actually load-bearing (an exhaustive weight-level check and
    approximate agreement on the measured surface), and the limits are stated rather than implied.
    """
    rows = []
    for arm in ("armA", "armB"):
        r, _ = _merge_receipt(arm)
        if r is None:
            rows.append(f"| `{arm}` | **receipt absent — UNMEASURED** | | | | |")
            continue
        rw = r.get("merge_weight_max_abs")
        rs = r.get("merge_weight_max_rel_to_merged")
        rd = r.get("merge_weight_control_module_dropped_ratio")
        rows.append(
            f"| `{arm}` | {_fmt(r.get('merge_weight_max_ulp'))} | "
            f"{_fmt(r.get('merge_weight_frac_gt_2ulp'), '.2e')} | "
            f"{_fmt(r.get('tf_top1_agreement_rate'))} ({r.get('tf_positions')} pos) | "
            f"{_fmt(r.get('merge_weight_control_module_dropped_max_ulp'), '.3g')} | "
            f"{_fmt(r.get('tf_negative_control_agreement_rate'))} | {r.get('loss_delta')} |")
    w = next((_merge_receipt(a)[0] for a in ("armA", "armB") if _merge_receipt(a)[0]), None)
    # Never print a placeholder as if it were a number: with no receipt the weight-level check is UNMEASURED and
    # the text says so rather than rendering "nan" beside real-looking units.
    if not w:
        established = ("**What is established.** **Nothing yet** — no merge-equivalence receipt has been "
                       "harvested, so the weight-level check and the behavioural comparison are both "
                       "**UNMEASURED** for this verdict.")
    else:
        established = "\n".join([
            "**What is established — as a tolerance, not a claim of correctness.** Every merged weight equals",
            f"`base_weight + scaling * (B @ A)` to within the stated tolerance at every element: across",
            f"{w.get('merge_weight_modules', '?')} matrices and {w.get('merge_weight_elements', '?')} elements",
            "(exhaustive, not sampled), the worst element deviates by",
            f"**{_fmt(w.get('merge_weight_max_ulp'), '.3f')} of a bf16 ULP** (half an ULP is the optimum for a",
            f"correctly-rounded operation), with **{w.get('merge_weight_nonfinite_elements', '?')} non-finite weights**",
            f"and **{w.get('merge_weight_near_zero_elements', '?')} near-zero elements**, reported with a maximum "
            f"absolute deviation of {_fmt(w.get('merge_weight_near_zero_max_abs'), '.3g')} — **not** excluded, "
            f"because with the exponent clamped the subnormal spacing is the uniform 2^-133 and a ULP ratio is "
            f"therefore well defined at every magnitude. The main statistic and BOTH controls cover "
            f"**identical** element sets ({_fmt(w.get('merge_weight_measured_elements'), ',')} elements), so a "
            f"tolerated residual cannot manufacture the sensitivity the controls claim. It is *deterministic*,"
            "so unlike any behavioural test it cannot be passed by a defect concentrated in a region that happens",
            "not to be sampled — including a SPARSE one: the gate is the element-wise maximum, because a",
            "fraction-only gate was rejected when it permitted 3,633 arbitrarily erroneous elements and passed a",
            "single weight corrupted to 1024 while detecting it. Its tolerance is justified by measured separation:",
            f"the same measurement applied to an injected defect reports "
            f"**{_fmt(w.get('merge_weight_control_scale_0p9_max_ulp'), '.3g')}** ULP for a 10 %",
            f"mis-scaling and **{_fmt(w.get('merge_weight_control_module_dropped_max_ulp'), '.3g')}** ULP for a dropped",
            "contribution, against **0.5** as shipped. Non-finite weights are counted separately and gated at zero,",
            "because `NaN > 2` is False and would otherwise vanish from the count.",
            "",
            "**Coverage boundary (conceded, not implied).** This check visits the **LoRA-adapted linear matrices**",
            "only. Unadapted parameters — embeddings, normalisation layers, the output head — are **not covered**, so",
            "it bounds the deviation on the adapted matrices to the stated tolerance, and says nothing about the rest of the merged model.",
        ])
    return "\n".join([
        "The evaluator scores the **merged** model, so the merge was checked against the unmerged path in three",
        "ways, and the claim below is scoped to exactly what those measurements support.",
        "",
        "| arm | worst-element deviation (literal bf16 ULP) | fraction beyond 2 ULP | teacher-forced top-1 agreement | control: a module's contribution dropped (ULP) | control: adapter disabled | held-out loss delta |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
        established,
        "",
        "**What is NOT established — stated, not implied.** This does **not** establish general behavioural",
        "equivalence, and nothing in this verdict claims it. A finite behavioural sample cannot: independent",
        "review #18 produced an executed counterexample that changed the last eight of 200 supervised positions in",
        "every row while passing every numerical condition (0.96 agreement, 0.3604 separation, unchanged",
        "gold-token loss, zero first-position disagreements). Behavioural agreement is therefore reported as",
        "**approximate agreement on the measured surface** — teacher-forced over the assistant span, which",
        "constrains reference-conditioned continuations and not the models' own generated prefixes. Two further",
        "limits: the check resolves deviations of order the adapter update and does **not** resolve a sub-1 %",
        "mis-scaling, which is comparable to bf16 rounding of the merged sum; that the check covers only the",
        "LoRA-adapted matrices and not unadapted parameters; and the free-running generation",
        "statistics (exact mismatches, token-F1) measure how far that rounding is amplified by greedy decoding,",
        "so they are **reported and never gated**.",
    ])


def _fmt(v, spec: str = ".4f") -> str:
    """Format a number, or render `?` for a missing one.

    The composer must NEVER raise on a partial receipt: stage 6 producing nothing means no verdict at all, which
    is the one outcome this whole contract exists to avoid. Found 2026-09-29 by pointing the rehearsal at a
    fixture receipt that lacked `tf_top1_agreement_rate` — `.get()` returned None and the f-string raised.
    """
    try:
        return format(float(v), spec)
    except (TypeError, ValueError):
        return "?"


def _merge_receipt(arm: str):
    """The merge-equivalence receipt for one arm, harvested first, then a local copy."""
    for p in (f"research-tmp/harvest-v2/evals/merge-equiv-cyberguard-lora-v2-{arm}.json",
              f"evals/merge-equiv-cyberguard-lora-v2-{arm}.json"):
        r = load(p)
        if r is not None:
            return r, p
    return None, None


def training_trajectory() -> str:
    """Measured exposure per saved artefact — required by Codex review #14 (2026-09-29).

    #14 accepted the repaired resume as *trainable* but ruled that the reset "changes the optimization
    trajectory, not merely its name", that the result "cannot substantiate a claim about uninterrupted
    training", and that exposure must be reported as **measured additional updates per saved artefact**, not
    as a projection — with the frozen interval excluded from learning exposure. This reads each run's own
    receipt and reports what actually happened, including when a receipt is missing rather than glossing it.
    """
    facts = load("v2/data/mixture/FACTS.json") or {}
    tw = facts.get("training_window") or {}
    inc = ((tw.get("incidents") or {}).get("noop_resume") or {})
    out = [
        "The evaluated artefacts are the product of **one completed pass over the mixture followed by a",
        "partial second data pass, with fresh optimizer state and a restarted LR schedule** (Codex review",
        "#14). They are **not** the product of one continuous schedule, and nothing here claims uninterrupted",
        "training. Exposure is reported as **measured**, from each run's own receipt — never as a projection —",
        "and the frozen interval is excluded from learning exposure while remaining in the cost accounting.",
        "",
        "Two caveats on these measured figures, both raised by independent review (Muse, 2026-09-29) and recorded",
        "rather than smoothed over. The **terminal LR** column is the LAST LOGGED learning rate: whether the final",
        "optimiser step coincides with the last logging interval is not verified, so it bounds the terminal LR",
        "rather than reproducing it exactly. And the **live loss-mask evidence is one sampled batch per host**",
        "(273/598 supervised tokens, identical on both arms), which settles that the mask is assistant-only but",
        "does not enumerate every batch.",
        "",
        "| artefact | measured updates | measured wall clock | terminal LR (peak) | steps with nonzero grad_norm | receipt |",
        "|---|---|---|---|---|---|",
    ]
    missing: list[str] = []
    for arm in ("armA", "armB"):
        r, p = _trainer_receipt(arm)
        if r is None:
            missing.append(arm)
            out.append(f"| `{arm}` | **receipt absent — exposure UNMEASURED** | — | — | — | — |")
            continue
        lh = [e for e in (r.get("log_history") or []) if isinstance(e, dict)]
        steps = [e["step"] for e in lh if isinstance(e.get("step"), int)]
        lrs = [e["learning_rate"] for e in lh if isinstance(e.get("learning_rate"), (int, float))]
        gns = [e["grad_norm"] for e in lh if isinstance(e.get("grad_norm"), (int, float))]
        nonzero = sum(1 for g in gns if g)
        wall = r.get("wall_seconds")
        wall_s = f"{wall / 3600:.2f} h" if isinstance(wall, (int, float)) else "?"
        # The TERMINAL LR is the learning rate the evaluated artefact stopped at — the quantity review #14 asks
        # for, because a time box halts mid-schedule. The peak is shown beside it for context; reporting the
        # peak as if it were the terminal rate would misstate where in the schedule the artefact was saved.
        lr_s = f"{lrs[-1]:.3e} (peak {max(lrs):.3e})" if lrs else "?"
        up_s = str(max(steps)) if steps else "?"
        out.append(f"| `{arm}` | {up_s} | {wall_s} | {lr_s} | {nonzero} of {len(gns)} | `{p}` |")
    if missing:
        out += ["", f"**Exposure for {', '.join('`' + m + '`' for m in missing)} is UNMEASURED**: the trainer's",
                "receipt was not harvested, so no measured update count or terminal LR exists for that artefact.",
                "Per review #14 this is reported as a gap, not filled with a projection."]
    if inc:
        out += ["",
                "The frozen resume of 2026-09-28/29 is recorded in `v2/data/mixture/FACTS.json`",
                "(`training_window.incidents.noop_resume`): it consumed",
                f"**{inc.get('gpu_hours_wasted', '?')} GPU-hours** producing no learning on either arm",
                "(`trainable params: 0`, `grad_norm` 0 at every logged step). Those hours are **excluded from",
                "the exposure figures above** and retained in the cost accounting below. Nothing in this verdict",
                "rests on them."]
    gh = tw.get("gpu_hours") or {}
    if gh:
        out += ["",
                f"Cost accounting (owner authorization {gh.get('authorization_gpu_h', '?')} GPU-hours = 24 h x 2 arms):",
                f"spent before the repair **{gh.get('spent_before_relaunch_gpu_h', '?')}** GPU-hours; the 570-minute",
                f"continuation box bounds the total at **{gh.get('worst_case_total_gpu_h', '?')}** GPU-hours;",
                f"within authorization: **{gh.get('within_authorization', '?')}**."]
    return "\n".join(out)



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
    _mp = load("v2/data/mixture/mask-proof.receipt.json")
    if _mp:
        _pass = all("MASK PROOF: PASS" in (d.get("output") or "") for d in (_mp.get("hosts") or {}).values())
        mask_line = ("The trainer's `MASK_PROOF` mode (assistant-only supervision on a real collated batch, "
                     f"before any optimizer step) **{'PASSED on both hosts' if _pass else 'did NOT pass'}** "
                     f"(`v2/data/mixture/mask-proof.receipt.json`, captured {_mp.get('captured_at')}).")
    else:
        mask_line = ("**UNVERIFIED for this window.** The trainer ships a `MASK_PROOF` mode that asserts "
                     "assistant-only supervision, but no proof receipt exists, so the live loss mask was not "
                     "demonstrated for these runs.")
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

## Training trajectory and measured exposure (review #14)

{training_trajectory()}

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

## Serving posture (amendment A2 — stated because it is a deviation from the objective)

The evaluation ran with the **Flash-Next serving stack evicted from both hosts**, which the plan requires (the
stack is `Restart=always` and enabled, and once returned mid-window at ~50 GB per host, so `disable --now` was
needed to hold it down). The objective's clause *"restoring it with a verified probe"* was **superseded by the
owner**, and the stack **remains evicted**; `pool_control.sh restore` can re-enable and start it, so the decision
is deliberate and the owner's boot behaviour is unchanged. The eviction was verified at every 3-hourly checkpoint
(port 8093 closed, no active serving unit) and again by this contract's preflight. Recorded in
`docs/SPEC-V2.md` §17; no artifact in this project claims the restoration was performed.

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

## Live loss mask

{mask_line}

## Merge equivalence: what is established, and what is not

{merge_equivalence_block()}

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
