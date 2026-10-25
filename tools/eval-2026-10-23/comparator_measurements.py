#!/usr/bin/env python3
"""Every number this project has MEASURED on the public comparator, with the surface it was
measured on — and the author-reported figures, kept apart from ours.

WHY THIS FILE EXISTS
--------------------
The comparator (CyberSecQwen-4B) is the bar's reference point: B1's bar is literally
"CTI-RCM > 0.6780", the comparator's own re-measurement on this host. A bar sheet whose
reference figure cannot be traced to a surface is exactly the defect this programme has already
found once (the v4 bar was "CTI-RCM > 0.6664", which is **author-reported** — five sampled author
trials on a different surface and a different protocol — and that bar was withdrawn).

So the comparator's numbers are collected here, one record per measurement, each carrying:

  * the **surface** it was measured on (the population, the runner, the decode budget);
  * the **artefact** that holds it, so every figure can be re-derived;
  * and, where it applies, the **author-reported** figure it must never be confused with.

THE HOUSE RULE THIS ENCODES
----------------------------
An author-reported number is never presented as our measurement. CyberSecQwen-4B's own paper
reports CTI-MCQ 0.5868 and CTI-RCM 0.6664; those figures are carried here ONLY inside a block
labelled author-reported, with their own ± spread, and they are never used as a baseline.

Usage:  python3 comparator_measurements.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT_JSON = HERE / "comparator-measurements.json"
OUT_MD = HERE / "comparator-measurements.md"

MERGED = HERE / "results-merged-2026-10-23.json"
EQT = HERE / "decode-budget" / "equal-terms" / "equal-terms-table.json"
HARM = HERE / "safety" / "harmbench-results-D6-repair.json"
FRR = HERE / "safety" / "frr-results.json"
RECEIPT = HERE / "decode-budget" / "equal-terms" / "comparator-cache-receipt.json"
RUNNER = HERE / "decode-budget" / "equal-terms" / "mcq-comparator-b512" / "run_pubbench_decode.py"

TAG = "cybersecqwen-4b"


def main() -> int:
    merged = json.loads(MERGED.read_text())
    eqt = json.loads(EQT.read_text())
    harm = json.loads(HARM.read_text())["per_model"]
    frr = json.loads(FRR.read_text())["per_model"]
    receipt = json.loads(RECEIPT.read_text())

    out: dict = {
        "what_this_is": "every number this project measured on the public comparator "
                        "CyberSecQwen-4B, with the surface each was measured on, and the "
                        "author-reported figures kept in a separate labelled block",
        "comparator": {
            "hub_id": "athena129/CyberSecQwen-4B",
            "size_class": "4B",
            "role": "the bar sheet's reference point and a peer in the same size class; NOT a "
                    "release candidate",
        },
        "identity": {
            "how_the_bytes_were_obtained": "the hub id resolves OFFLINE to a local cache; the "
                                           "cache was verified against the sha256 the hub "
                                           "publishes for that revision, so the bytes measured "
                                           "here are the bytes the comparator ships",
            "published_lfs_sha256": receipt.get("hub_comparison", {}).get("published_lfs_sha256"),
            "local_weight_sha256": receipt.get("hub_comparison", {}).get("local_weight_sha256"),
            "weight_matches_published": receipt.get("hub_comparison", {}).get(
                "weight_matches_published"),
            "files_in_cache": len(receipt.get("files", [])),
            "files_matching": sum(1 for f in receipt.get("files", []) if f.get("match")),
            "receipt": str(RECEIPT.relative_to(ROOT)),
        },
        "measured": {},
        "author_reported": {},
    }

    # --- surface 1: the family re-measurement (one frozen surface, all six arms) --------------
    rows = {r["benchmark"]: r for r in merged["comparison"] if r.get("model") == TAG}
    out["measured"]["family_surface"] = {
        "surface": {
            "what": "the six-arm independent re-measurement of 2026-10-23 — one frozen surface, "
                    "one runner, one population, every arm",
            "frozen_surface": merged["frozen_surface"],
            "population": merged["population"],
        },
        "artefact": str(MERGED.relative_to(ROOT)),
        "benchmarks": {
            b: {"accuracy": r["accuracy"], "n": r["n"], "unparseable": r["unparseable"],
                "unparseable_rate": r.get("unparseable_rate"),
                "always_c_baseline": r.get("always_c_baseline")}
            for b, r in sorted(rows.items())
        },
    }

    # --- surface 2: the A-16 equal-terms ladder -------------------------------------------------
    cells = {k: v for k, v in (eqt.get("cells") or {}).items() if k.startswith(TAG + "|")}
    out["measured"]["equal_terms_cti_mcq"] = {
        "surface": {
            "what": "the A-16 equal-terms sweep — EVERY arm at every budget, one runner, one "
                    "population, one parser; max_new_tokens is the only variable",
            "population": "CTI-MCQ's 2,500 items, and nothing else",
            "runner": "the byte-identical copy of A-5's runner (sha256 "
                      "59896c5118848e7813cb17cbf56a3f9bd0a242f97166cab64c9fa8024ffac7d8)",
            "note": "the family surface above measured this same comparator at 512 tokens on the "
                    "ALL-BENCHMARKS population (2,500 MCQ items sharing batches with 3,500 foreign "
                    "items). The two numbers differ by a handful of responses, and the difference "
                    "is itself measured and reported (the surface effect). The equal-terms ladder "
                    "is the one the bar sheet's serving-budget ruling rests on.",
        },
        "artefact": str(EQT.relative_to(ROOT)),
        "ladder": {
            f"max_new_tokens={b}": {
                "accuracy": cells[f"{TAG}|{b}"]["accuracy"],
                "unparseable_rate": cells[f"{TAG}|{b}"]["unparseable_rate"],
                "n": cells[f"{TAG}|{b}"]["n"],
            }
            for b in (512, 1024, 2048) if f"{TAG}|{b}" in cells
        },
    }

    vsp = {k: v for k, v in (eqt.get("vsp_cells") or {}).items() if k.startswith(TAG + "|")}
    if vsp:
        out["measured"]["equal_terms_cti_vsp"] = {
            "surface": {
                "what": "the A-16 CTI-VSP budget ladder — the same runner and the same ladder, "
                        "on CTI-VSP's 1,000 items",
                "metric": "mean absolute deviation of the CVSS v3.1 base score (points; LOWER IS "
                          "BETTER), scored by CTI-Bench's own compute_vsp_mad, imported from "
                          "reference_eval.py",
                "denominator": "the responses whose vector the reference's scorer could parse — "
                               "the reference SKIPS unparseable responses rather than scoring "
                               "them wrong, so the denominator is not the population when a model "
                               "fails to format",
            },
            "artefact": str(EQT.relative_to(ROOT)),
            "ladder": {
                f"max_new_tokens={b.split('|')[1]}": {
                    "mad": vsp[f"{TAG}|{b}"]["mad"],
                    "n_scored": vsp[f"{TAG}|{b}"]["n_scored"],
                    "n_unparseable": vsp[f"{TAG}|{b}"]["n_unparseable"],
                    "n": vsp[f"{TAG}|{b}"]["n"],
                }
                for b in sorted(vsp) if vsp.get(b)
            },
        }

    # --- surface 3: safety ---------------------------------------------------------------------
    hb = harm.get(TAG, {})
    fr = frr.get(TAG, {})
    out["measured"]["safety"] = {
        "surface": {
            "what": "the two safety instruments, each on its own frozen population",
            "harmbench": "HarmBench standard-test, direct-request harmful compliance; the "
                         "OFFICIAL HarmBench classifier; n=159; LOWER IS BETTER",
            "mitre_frr": "CyberSecEval MITRE-FRR heuristic refusal rate on DECODED CONTENT "
                         "(the B8 repair); n=750; LOWER IS BETTER unless the prompt asks for a "
                         "refusal",
        },
        "artefacts": [str(HARM.relative_to(ROOT)), str(FRR.relative_to(ROOT))],
        "harmbench": {"n": hb.get("n"), "yes": hb.get("yes"), "rate_pct": hb.get("rate_pct"),
                      "wilson95": hb.get("wilson95"), "invalid_labels": hb.get("invalid_labels"),
                      "overflow": hb.get("overflow")},
        "mitre_frr": {"n": fr.get("n"), "refusal_count": fr.get("refusal_count"),
                      "FRR_pct": fr.get("FRR_pct"), "wilson95": fr.get("wilson95"),
                      "empty_responses": fr.get("empty_responses")},
    }

    # --- the author-reported figures, in their own labelled block --------------------------------
    try:
        src = RUNNER.read_text()
        block = src[src.index("AUTHOR_REPORTED = {"):src.index("}", src.index("AUTHOR_REPORTED = {")) + 1]
        out["author_reported"] = {
            "label": "AUTHOR-REPORTED — these are the comparator's own paper's figures, on the "
                     "authors' surface and protocol. They are NOT measurements by this project "
                     "and are never used as a baseline. The house rule: never quote an author's "
                     "published number as our measurement.",
            "source": str(RUNNER.relative_to(ROOT)),
            "block": block,
        }
    except Exception as exc:  # noqa: BLE001
        out["author_reported"] = {"label": "unreadable", "error": str(exc)}

    OUT_JSON.write_text(json.dumps(out, indent=1) + "\n")

    # --- the markdown -----------------------------------------------------------------------------
    L: list[str] = []
    A = L.append
    A("# The public comparator's measured numbers — CyberSecQwen-4B\n")
    A("*Generated by `eval-2026-10-23/comparator_measurements.py` from the artefacts it names. "
      "Re-run it to re-derive this file; no number here is typed by hand.*\n")
    A("## 0. Which bytes these numbers came from\n")
    idn = out["identity"]
    A(f"- Hub id: `{out['comparator']['hub_id']}` ({out['comparator']['size_class']}).")
    A(f"- {idn['how_the_bytes_were_obtained']}.")
    A(f"- Published sha256 for that revision: `{idn['published_lfs_sha256']}`.")
    A(f"- The local weight file hashes to: `{idn['local_weight_sha256']}` — "
      f"**match: {idn['weight_matches_published']}**.")
    A(f"- Files in the cache: **{idn['files_matching']}/{idn['files_in_cache']}** match their "
      "blob ids.")
    A(f"- Receipt: `{idn['receipt']}`.\n")

    A("## 1. Measured on the family surface (one frozen surface, all six arms)\n")
    fam = out["measured"]["family_surface"]
    A("| benchmark | n | accuracy | unparseable | always-C baseline |")
    A("|---|---:|---:|---:|---:|")
    for b, r in fam["benchmarks"].items():
        A(f"| {b} | {r['n']} | {r['accuracy']:.4f} | {r['unparseable']} | "
          f"{r.get('always_c_baseline') if r.get('always_c_baseline') is not None else '—'} |")
    A("")
    A(f"*(surface: {fam['surface']['frozen_surface']['max_new_tokens']} tokens, greedy, batch "
      f"{fam['surface']['frozen_surface']['batch']}, bf16, PEFT adapter not merged; artefact "
      f"`{fam['artefact']}`)*\n")

    A("## 2. Measured on the A-16 equal-terms surface (every arm, every budget)\n")
    eq = out["measured"]["equal_terms_cti_mcq"]
    A("| max_new_tokens | CTI-MCQ accuracy | unparseable rate | n |")
    A("|---|---:|---:|---:|")
    for k, r in eq["ladder"].items():
        A(f"| {k.split('=')[1]} | {r['accuracy']:.4f} | {r['unparseable_rate'] * 100:.2f} % | "
          f"{r['n']} |")
    A("")
    A(f"*(artifact: `{eq['artefact']}` — {eq['surface']['population']})*\n")

    if "equal_terms_cti_vsp" in out["measured"]:
        vs = out["measured"]["equal_terms_cti_vsp"]
        A("### CTI-VSP, the same ladder\n")
        A("| max_new_tokens | MAD (points, lower is better) | scored | unparseable |")
        A("|---|---:|---:|---:|")
        for k, r in vs["ladder"].items():
            A(f"| {k.split('=')[1]} | {r['mad']:.2f} | {r['n_scored']}/{r['n']} | "
              f"{r['n_unparseable']} |")
        A("")
        A(f"*({vs['surface']['denominator']})*\n")

    A("## 3. Measured on the safety instruments\n")
    sf = out["measured"]["safety"]
    hb, fr = sf["harmbench"], sf["mitre_frr"]
    A("| instrument | n | our figure | 95 % Wilson | detail |")
    A("|---|---:|---:|---|---|")
    A(f"| HarmBench standard-test harmful compliance | {hb['n']} | {hb['rate_pct']:.2f} % | "
      f"[{hb['wilson95'][0] * 100:.2f} %, {hb['wilson95'][1] * 100:.2f} %] | {hb['yes']} of "
      f"{hb['n']} yes, {hb['invalid_labels']} invalid labels, {hb['overflow']} overflow |")
    A(f"| MITRE-FRR refusal rate | {fr['n']} | {fr['FRR_pct']:.2f} % | "
      f"[{fr['wilson95'][0] * 100:.2f} %, {fr['wilson95'][1] * 100:.2f} %] | "
      f"{fr['refusal_count']} of {fr['n']} refusals |")
    A("")
    A("## 4. Author-reported — NOT ours, and never a baseline\n")
    A(f"**{out['author_reported'].get('label', '')}**\n")
    A("```")
    A(out["author_reported"].get("block", "(unreadable)"))
    A("```")
    A("")
    A(f"*(carried from `{out['author_reported'].get('source', '')}` — the runner's own "
      "AUTHOR_REPORTED block, read from the file)*\n")
    OUT_MD.write_text("\n".join(L))

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print()
    print("the comparator's MEASURED numbers:")
    for b, r in fam["benchmarks"].items():
        print(f"  family surface   {b:<18} {r['accuracy']:.4f}  ({r['unparseable']} unparseable)")
    for k, r in eq["ladder"].items():
        print(f"  equal terms      CTI-MCQ @{k.split('=')[1]:<6} {r['accuracy']:.4f}  "
              f"({r['unparseable_rate'] * 100:.2f} % unparseable)")
    if "equal_terms_cti_vsp" in out["measured"]:
        for k, r in out["measured"]["equal_terms_cti_vsp"]["ladder"].items():
            print(f"  equal terms      CTI-VSP @{k.split('=')[1]:<6} MAD {r['mad']:.2f}  "
                  f"({r['n_scored']}/{r['n']} scored)")
    print(f"  safety           HarmBench {hb['rate_pct']:.2f} % ({hb['yes']}/{hb['n']}) | "
          f"MITRE-FRR {fr['FRR_pct']:.2f} % ({fr['refusal_count']}/{fr['n']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
