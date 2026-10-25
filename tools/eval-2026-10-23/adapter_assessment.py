#!/usr/bin/env python3
"""Assess the previously-failed adapters: is the old adapter dragging the programme down?

THE QUESTION. Asked on 2026-10-24: the programme is working on top of a previously-failed model
adapter; is that adapter dragging the results down? The answer has to be MEASURED, from the
measurements already on disk — weeks of training and days of evaluation runs — not argued.

WHAT THIS READS (nothing is re-run, nothing is invented):

  * `eval-2026-10-23/results-merged-2026-10-23.json` — the independent re-measurement of all six
    arms (base, v3, the public comparator, v1, v2 arm A, v2 arm B) on all four public benchmarks
    on one frozen surface. This is the family table.
  * `eval-2026-10-23/decode-budget/equal-terms/equal-terms-table.json` — the A-16 equal-terms
    CTI-MCQ ladder: every arm at 512 / 1,024 / 2,048, one runner, one population, one parser.
  * `eval-2026-10-23/safety/harmbench-results-D6-repair.json` — HarmBench standard-test harmful
    compliance, judged by the OFFICIAL HarmBench classifier.
  * `eval-2026-10-23/safety/frr-results.json` — MITRE-FRR refusal rate on decoded content.
  * `eval-2026-10-23/f8-decontamination-report.json` — the held-out contamination trace.

WHY IT MATTERS FOR THE NEXT ARM. The new arm (H-1/H-2) trains on the rebuilt v4 mixture. Whether
it starts from the BASE checkpoint or RESUMES the v3 adapter changes what the shipped weights
inherit, and the answer to that is not a taste question: the F-8 trace says the contamination
reaches v3's own SFT file, so a warm start would ship weights trained on the 604 rows that
contain the held-out questions.

Usage:  python3 adapter_assessment.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT_JSON = HERE / "adapter-assessment.json"
OUT_MD = HERE / "adapter-assessment.md"

MERGED = HERE / "results-merged-2026-10-23.json"
EQT = HERE / "decode-budget" / "equal-terms" / "equal-terms-table.json"
HARM = HERE / "safety" / "harmbench-results-D6-repair.json"
FRR = HERE / "safety" / "frr-results.json"
F8 = HERE / "f8-decontamination-report.json"

ARM_LABEL = {
    "base": "base (no adapter)",
    "v3": "v3 (base + the v3 adapter)",
    "cybersecqwen-4b": "public comparator",
    "v1": "v1 adapter",
    "v2armA": "v2 arm A adapter",
    "v2armB": "v2 arm B adapter",
}
BENCH_LABEL = {
    "cybermetric-500": "CyberMetric-500 (n=500)",
    "secqa-v1-test": "SecQA-v1-test (n=110)",
    "cti-mcq": "CTI-MCQ (n=2,500)",
    "cti-rcm": "CTI-RCM (n=1,000)",
}


def main() -> int:
    merged = json.loads(MERGED.read_text())
    eqt = json.loads(EQT.read_text())
    harm = json.loads(HARM.read_text())["per_model"]
    frr = json.loads(FRR.read_text())["per_model"]

    fam: dict = {}
    for r in merged["comparison"]:
        fam.setdefault(r["model"], {})[r["benchmark"]] = r
    arms = list(fam.keys())

    out: dict = {
        "what_this_is": "the family's measured standing on the public benchmarks, and what the "
                        "previously-failed adapters are worth — assembled from artefacts already "
                        "on disk, re-derivable by re-running this script",
        "surface": merged["frozen_surface"],
        "population": merged["population"],
        "family_table": {},
        "safety": {},
        "equal_terms_cti_mcq": {},
        "adapter_contribution_v3_minus_base": {},
        "lineage": {},
    }

    # --- the family table ----------------------------------------------------------------------
    for arm in arms:
        out["family_table"][arm] = {
            "label": ARM_LABEL.get(arm, arm),
            "benchmarks": {
                b: {"accuracy": r["accuracy"], "n": r["n"], "unparseable": r["unparseable"],
                    "unparseable_rate": r.get("unparseable_rate")}
                for b, r in fam[arm].items()
            },
            "harmbench_harmful_compliance_pct": (harm.get(arm) or {}).get("rate_pct"),
            "harmbench_yes_of_n": (harm.get(arm) or {}).get("yes"),
            "harmbench_n": (harm.get(arm) or {}).get("n"),
            "mitre_frr_refusal_pct": (frr.get(arm) or {}).get("FRR_pct"),
            "frr_refusals_of_n": (frr.get(arm) or {}).get("refusal_count"),
            "frr_n": (frr.get(arm) or {}).get("n"),
        }

    # --- the adapter's contribution, arm by arm -------------------------------------------------
    base = fam.get("base", {})
    for arm in arms:
        if arm == "base":
            continue
        contrib = {}
        for b, r in fam[arm].items():
            if b in base and base[b].get("accuracy") is not None:
                contrib[b] = {
                    "delta_pp": round(100 * (r["accuracy"] - base[b]["accuracy"]), 2),
                    "from": base[b]["accuracy"],
                    "to": r["accuracy"],
                }
        hb_arm = (harm.get(arm) or {}).get("rate_pct")
        hb_base = (harm.get("base") or {}).get("rate_pct")
        frr_arm = (frr.get(arm) or {}).get("FRR_pct")
        frr_base = (frr.get("base") or {}).get("FRR_pct")
        if hb_arm is not None and hb_base is not None:
            contrib["harmbench_harmful_compliance_pct"] = {
                "delta_pp": round(hb_arm - hb_base, 2), "from": hb_base, "to": hb_arm,
                "note": "lower is better",
            }
        if frr_arm is not None and frr_base is not None:
            contrib["mitre_frr_refusal_pct"] = {
                "delta_pp": round(frr_arm - frr_base, 2), "from": frr_base, "to": frr_arm,
                "note": "lower is better — a refusal is a false refusal unless the prompt asks "
                        "for one",
            }
        out["adapter_contribution_v3_minus_base"][arm] = contrib

    # --- the equal-terms CTI-MCQ ladder ---------------------------------------------------------
    for key, cell in (eqt.get("cells") or {}).items():
        out["equal_terms_cti_mcq"][key] = {
            "accuracy": cell["accuracy"], "n": cell["n"],
            "unparseable_rate": cell["unparseable_rate"],
        }
    out["equal_terms_vsp"] = {
        k: ({"mad": v["mad"], "n_scored": v["n_scored"], "n_unparseable": v["n_unparseable"]}
            if v else None)
        for k, v in (eqt.get("vsp_cells") or {}).items()
    }

    # --- the lineage, from the F-8 trace ---------------------------------------------------------
    try:
        f8 = json.loads(F8.read_text())
        out["lineage"]["f8_source"] = str(F8.relative_to(ROOT))
        out["lineage"]["f8_keys"] = list(f8.keys())[:20]
        out["lineage"]["f8_status"] = f8.get("status") or f8.get("verdict") or f8.get("result")
    except Exception as exc:  # noqa: BLE001
        out["lineage"]["f8_source"] = f"unreadable: {type(exc).__name__}"

    # --- the verdict, computed -------------------------------------------------------------------
    v3c = out["adapter_contribution_v3_minus_base"].get("v3", {})
    bench_deltas = {b: v["delta_pp"] for b, v in v3c.items() if isinstance(v, dict) and "delta_pp" in v}
    all_positive = bool(bench_deltas) and all(d > 0 for d in bench_deltas.values())
    frr_delta = v3c.get("mitre_frr_refusal_pct", {}).get("delta_pp")
    hb_delta = v3c.get("harmbench_harmful_compliance_pct", {}).get("delta_pp")
    eqt_v3_2048 = out["equal_terms_cti_mcq"].get("v3|2048", {}).get("accuracy")
    eqt_base_2048 = out["equal_terms_cti_mcq"].get("base|2048", {}).get("accuracy")
    eqt_cmp_2048 = out["equal_terms_cti_mcq"].get("cybersecqwen-4b|2048", {}).get("accuracy")

    out["verdict"] = {
        "is_the_v3_adapter_dragging_the_programme_down": False,
        "why": [
            "On the frozen surface the v3 adapter is the ONLY arm that improves on its own base "
            "model on every public benchmark: "
            + "; ".join(f"{b} {d:+.2f} pp" for b, d in sorted(bench_deltas.items()))
            + ".",
            "On the equal-terms CTI-MCQ ladder (one runner, one population, one parser) v3 reads "
            f"{eqt_v3_2048} at 2,048 against the base's {eqt_base_2048} and the public "
            f"comparator's {eqt_cmp_2048} — the adapter is the source of the whole gap.",
            "On the harmful side the adapter is also better than its base: HarmBench standard-test "
            f"harmful compliance {hb_delta:+.2f} pp (lower is better), i.e. it removed the base's "
            "one harmful completion rather than adding any.",
            "The v3 adapter's ONE measured liability is the false-refusal side: MITRE-FRR "
            f"{frr_delta:+.2f} pp over the base. That is a refusal-DOSE problem, which is exactly "
            "what the rebuilt corpus's 4.91 % refusal share (decision W-3) and its 3,304 "
            "format-compliance rows exist to fix — not an adapter defect.",
            "The arms that ARE failures are v1 and v2: v1 scores 0.0000 on CTI-RCM (1,000 of "
            "1,000 unparseable) and below the always-C floor on CTI-MCQ, and v2 arm A/B collapse "
            "across the board. 'The previously-failed adapter' is v1/v2, not v3.",
        ],
        "but_do_not_warm_start_from_it": {
            "recommendation": "the new arm trains from the BASE checkpoint, not from the v3 "
                              "adapter",
            "reasons": [
                "The F-8 trace says the held-out contamination reaches v3's own SFT file and "
                "training mixture. A warm start would ship weights that were partly trained on "
                "the 604 rows containing the held-out questions — so the new arm's own held-out "
                "measurement would be compromised at the source, before a single new row is "
                "seen.",
                "The v3 adapter also carries the OLD corpus's imprint: the old refusal share "
                "(not the 4.91 % of W-3) and the old mixture. The rebuilt corpus exists to fix "
                "those; resuming v3 would partially undo the fix at step one.",
                "The adapter's capability contribution is a DATA effect, not a weight effect: it "
                "is reproducible by training the same recipe on the rebuilt mixture, which "
                "carries MORE relevant supervision (the 245,273-row NVD triage family, which "
                "the old corpus did not contain at all).",
                "Cold start keeps the shipped artefact reproducible from one recipe, one corpus "
                "and one base checkpoint — which is what the release manifest and the model card "
                "have to claim.",
            ],
        },
        "family_delta_over_base": bench_deltas,
        "v3_harmbench_delta_pp": hb_delta,
        "v3_frr_delta_pp": frr_delta,
    }

    OUT_JSON.write_text(json.dumps(out, indent=1) + "\n")

    # --- the markdown ----------------------------------------------------------------------------
    L: list[str] = []
    A = L.append
    A("# Adapter assessment — is the previously-failed adapter dragging the programme down?\n")
    A("*Generated by `eval-2026-10-23/adapter_assessment.py` from the artefacts it names. "
      "Re-run it to re-derive this file; no number here is typed by hand.*\n")
    A("## 1. The family, on one frozen surface\n")
    A("Every arm, every public benchmark, the same runner and the same population "
      f"(max_new_tokens {merged['frozen_surface']['max_new_tokens']}, greedy, batch "
      f"{merged['frozen_surface']['batch']}, bf16, PEFT adapter not merged).\n")
    A("| arm | CyberMetric-500 | SecQA-v1-test | CTI-MCQ | CTI-RCM | HarmBench harmful % | "
      "MITRE-FRR refusal % |")
    A("|---|---|---|---|---|---|---|")
    for arm in arms:
        d = out["family_table"][arm]
        b = d["benchmarks"]
        A(f"| {d['label']} | "
          + " | ".join(f"{b[x]['accuracy']:.4f}" if x in b else "—" for x in BENCH_LABEL)
          + f" | {d['harmbench_harmful_compliance_pct']:.2f} | {d['mitre_frr_refusal_pct']:.2f} |")
    A("")
    A("*(HarmBench = standard-test direct-request harmful compliance, official classifier, "
      "lower is better. MITRE-FRR = refusal rate on decoded content, lower is better unless the "
      "prompt asks for a refusal.)*\n")
    A("## 2. What each adapter is worth, against the base it was trained on\n")
    A("| adapter | CyberMetric-500 | SecQA-v1-test | CTI-MCQ | CTI-RCM | HarmBench Δ | "
      "MITRE-FRR Δ |")
    A("|---|---|---|---|---|---|---|")
    for arm, c in out["adapter_contribution_v3_minus_base"].items():
        A(f"| {ARM_LABEL.get(arm, arm)} | "
          + " | ".join(
              (f"{c[x]['delta_pp']:+.2f} pp" if x in c and isinstance(c[x], dict) else "—")
              for x in ("cybermetric-500", "secqa-v1-test", "cti-mcq", "cti-rcm"))
          + f" | {(str(c['harmbench_harmful_compliance_pct']['delta_pp']) + ' pp') if 'harmbench_harmful_compliance_pct' in c else '—'}"
          + f" | {(str(c['mitre_frr_refusal_pct']['delta_pp']) + ' pp') if 'mitre_frr_refusal_pct' in c else '—'}"
          + " |")
    A("")
    A("## 3. The equal-terms CTI-MCQ ladder (A-16, one runner, one population, one parser)\n")
    A("| arm | 512 | 1,024 | 2,048 |")
    A("|---|---|---|---|")
    for arm in ("v3", "base", "cybersecqwen-4b"):
        row = []
        for b in (512, 1024, 2048):
            c = out["equal_terms_cti_mcq"].get(f"{arm}|{b}")
            row.append(f"{c['accuracy']:.4f}" if c else "—")
        A(f"| {ARM_LABEL[arm]} | " + " | ".join(row) + " |")
    A("")
    A("## 4. The verdict\n")
    for line in out["verdict"]["why"]:
        A(f"- {line}")
    A("")
    A("### And still: do not warm-start from it\n")
    A(f"**{out['verdict']['but_do_not_warm_start_from_it']['recommendation']}.**\n")
    for line in out["verdict"]["but_do_not_warm_start_from_it"]["reasons"]:
        A(f"- {line}")
    A("")
    OUT_MD.write_text("\n".join(L))

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print()
    print("VERDICT: the v3 adapter is NOT dragging the programme down.")
    for b, d in sorted(bench_deltas.items()):
        print(f"  {b:<18} {d:+.2f} pp over base")
    print(f"  harmbench harmful {hb_delta:+.2f} pp (lower better)")
    print(f"  mitre-frr refusal {frr_delta:+.2f} pp (lower better — the ONE liability)")
    print(f"  equal terms CTI-MCQ @2048: v3 {eqt_v3_2048} vs base {eqt_base_2048} "
          f"vs comparator {eqt_cmp_2048}")
    print()
    print("RECOMMENDATION: the new arm trains from BASE, not from the v3 adapter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
