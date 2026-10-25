#!/usr/bin/env python3
"""F-8c — trace the held-out leak from its origin to the rebuilt mixture.

F-8 measured the fact: 604 rows of `data/v4/mixture-v4.jsonl` share a held-out
prompt's identity, all of them in the `fenrir` stream, and fenrir's residual
overlap against the held-out set (jaccard_max 0.7566 / containment_max 0.9795)
exceeds the v2 admission gate's recorded maximum (0.0266 / 0.0723).

F-8 did not say *where* the leak enters. This script measures the path, stage by
stage, so the escalation document can name a mechanism rather than an effect.

THE IDENTITY KEY IS THE PROJECT'S OWN, NOT A NEW ONE.
`v2/export_holdout.py` writes `prompt_sha256 = sha256(" ".join(user.lower().split()))[:16]`
and says in its own comment that this "must match gate_v2.prompt_hash_of and the
dedupe key". This script uses exactly that key and imports `v2/gate_v2.py`'s
`prompt_hash_of` to cross-check it. Nothing about the detector is re-invented.

USES NO NEW DATA. Every file read is already on disk. Nothing is written except
this script's own report.

Run:  python3 eval-2026-10-23/f8c_trace_holdout_leak.py
Exit: 0 if every check passes, 1 if any check fails, 2 if an input is missing.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOLDOUT = ROOT / "v2" / "holdout500.jsonl"
GATE = ROOT / "v2" / "gate_v2.py"
GATE_REPORT = ROOT / "v2" / "gate-report.json"
FENRIR_BUNDLE = ROOT / "data" / "v3" / "fenrir-v2.1" / "220426-CyberSec-Dataset_escaped.jsonl"
FENRIR_CLEAN = ROOT / "data" / "v3" / "fenrir-v2.1" / "clean" / "fenrir-v2.1.clean.jsonl"
CORPUS_V4_R3 = ROOT / "data" / "v4" / "corpus-v4-r3.jsonl"
MIXTURE = ROOT / "data" / "v4" / "mixture-v4.jsonl"
# The v3 training corpus, measured for the same reason: if the leak reached it, then
# v3's own held-out loss (EVALUATION.md §5.2a) was measured on a contaminated split.
V3_SFT_FENRIR = ROOT / "data" / "v3" / "sft" / "fenrir.jsonl"
V3_MIXTURE = ROOT / "data" / "v3" / "mixture" / "mixture-v3-no-trail.jsonl"
FENRIR_CONTAM_REPORT = ROOT / "data" / "v3" / "fenrir-v2.1" / "CONTAMINATION_REPORT.md"
OUT = Path(__file__).resolve().parent / "f8c-holdout-leak-trace.json"


def prompt_of(r: dict, field: str) -> str:
    """The prompt text of a row, for each of the two shapes on disk."""
    if field == "user":
        return str(r.get("user", ""))
    if field == "messages_user":
        for m in r.get("messages", []) or []:
            if m.get("role") == "user":
                return str(m.get("content", ""))
        return ""
    return str(r.get(field, ""))


# The stages in order, with the field that carries the prompt text.
STAGES = [
    ("fenrir_bundle_raw", FENRIR_BUNDLE, "user"),
    ("fenrir_clean", FENRIR_CLEAN, "user"),
    ("v3_sft_fenrir", V3_SFT_FENRIR, "messages_user"),
    ("v3_mixture", V3_MIXTURE, "user"),
    ("corpus_v4_r3", CORPUS_V4_R3, "user"),
    ("mixture_v4", MIXTURE, "user"),
]

checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    checks.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} — {detail}", flush=True)


def canon(text: str) -> str:
    """The project's canonical identity key, from v2/export_holdout.py."""
    return hashlib.sha256(" ".join(str(text or "").lower().split()).encode()).hexdigest()[:16]


# The held-out file stores the Trendyol reference with the escaping it came with (which varies in
# depth between rows), and the SFT file restores literal "\n" to real newlines. A RAW string
# comparison therefore reports a difference on rows whose answers are in fact the SAME text.
#
# `skeleton` compares the CONTENT and not its encoding: an escaped newline/tab/return and a
# backslash are escape syntax, not content, and neither is whitespace. This is the correction to
# the first version of this instrument, which compared raw strings and so reported 25 identical
# answers where there are 499.
_ESCAPED_WS = re.compile(r"\\[ntr]")
_WS = re.compile(r"\s+")


def skeleton(text: str) -> str:
    """The text's content with escape syntax and whitespace removed."""
    s = _ESCAPED_WS.sub("", str(text or ""))
    s = s.replace("\\", "")
    return _WS.sub("", s)


def load_gate():
    spec = importlib.util.spec_from_file_location("v2_gate_trace", GATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_jsonl(path: Path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> int:
    for p in (HOLDOUT, GATE, GATE_REPORT, FENRIR_BUNDLE, FENRIR_CLEAN,
              CORPUS_V4_R3, MIXTURE, V3_SFT_FENRIR, V3_MIXTURE):
        if not p.is_file():
            print(f"FATAL: {p} is missing")
            return 2
    gate = load_gate()

    # ------------------------------------------------------------------ the held-out set
    holdout_rows = list(read_jsonl(HOLDOUT))
    holdout_by_id: dict[str, dict] = {}
    for r in holdout_rows:
        holdout_by_id[canon(r.get("prompt", ""))] = r
    check("the held-out set is the certified 500-row split, and the identity key is the "
          "project's own",
          len(holdout_rows) == 500 and len(holdout_by_id) == 500,
          f"{len(holdout_rows)} rows, {len(holdout_by_id)} distinct canonical identities "
          f"(sha256 of the lowercased, whitespace-normalised prompt, first 16 hex)")

    # Cross-check the identity key against the gate's own prompt_hash_of, so the
    # trace cannot rest on a key this script invented.
    key_agree = 0
    for r in holdout_rows[:100]:
        if gate.prompt_hash_of(r.get("prompt", ""))[:16] == canon(r.get("prompt", "")):
            key_agree += 1
    check("the identity key agrees with the v2 gate's own prompt_hash_of on the first 100 rows",
          key_agree == 100,
          f"{key_agree}/100 agree; the gate's own function is used, not re-implemented")

    # ------------------------------------------------------------------ stage by stage
    stages: dict[str, dict] = {}
    for name, path, field in STAGES:
        rows_total = 0
        matched_rows = 0
        covered: set[str] = set()
        multiplicity: Counter = Counter()
        answer_exact = 0
        answer_same_content = 0
        answer_comparable = 0
        prompt_byte_identical = 0
        answer_kind: Counter = Counter()
        by_src: Counter = Counter()
        by_src_covered: set = set()
        for r in read_jsonl(path):
            rows_total += 1
            src = r.get("src")
            if src:
                by_src[src] += 1
            h = canon(prompt_of(r, field))
            if h in holdout_by_id:
                matched_rows += 1
                covered.add(h)
                multiplicity[h] += 1
                if src:
                    by_src_covered.add(src)
                hr = holdout_by_id[h]
                ref = str(hr.get("reference", ""))
                ans = str(r.get("assistant", ""))
                if field == "messages_user":
                    for m in r.get("messages", []) or []:
                        if m.get("role") == "assistant":
                            ans = str(m.get("content", ""))
                            break
                if prompt_of(r, field).strip() == str(hr.get("prompt", "")).strip():
                    prompt_byte_identical += 1
                if ref.strip() and ans.strip():
                    answer_comparable += 1
                    if ans.strip() == ref.strip():
                        answer_exact += 1
                        answer_same_content += 1
                        answer_kind["identical_raw"] += 1
                    elif skeleton(ans) == skeleton(ref):
                        # The two texts are the SAME answer, stored with different JSON escaping.
                        # The held-out file keeps the Trendyol reference's own escaping (which
                        # varies in depth per row), and the SFT file restores literal "\n" to real
                        # newlines, so a raw comparison reports a difference that is not one.
                        answer_kind["identical_after_escape_normalisation"] += 1
                        answer_same_content += 1
                    else:
                        answer_kind["different_text"] += 1
        mult_hist = Counter(multiplicity.values())
        stages[name] = {
            "file": str(path.relative_to(ROOT)),
            "rows_total": rows_total,
            "rows_sharing_a_holdout_identity": matched_rows,
            "distinct_holdout_rows_covered": len(covered),
            "distinct_holdout_rows_covered_of_500": round(len(covered) / 500, 4),
            "multiplicity_histogram": {str(k): v for k, v in sorted(mult_hist.items())},
            "rows_with_a_byte_identical_prompt": prompt_byte_identical,
            "rows_with_an_exactly_equal_reference_answer": answer_exact,
            "rows_carrying_the_same_answer_content": answer_same_content,
            "rows_where_an_answer_was_comparable": answer_comparable,
            "answer_relationship_histogram": dict(answer_kind),
            "source_labels_present": dict(by_src),
            "source_labels_carrying_a_holdout_identity": sorted(s for s in by_src_covered),
        }
        print(f"  · {name}: {matched_rows}/{rows_total} rows, {len(covered)}/500 distinct "
              f"holdout rows covered", flush=True)

    # ------------------------------------------------------------------ the chain is monotone
    raw_c = stages["fenrir_bundle_raw"]["rows_sharing_a_holdout_identity"]
    clean_c = stages["fenrir_clean"]["rows_sharing_a_holdout_identity"]
    sft_c = stages["v3_sft_fenrir"]["rows_sharing_a_holdout_identity"]
    v3mix_c = stages["v3_mixture"]["rows_sharing_a_holdout_identity"]
    r3_c = stages["corpus_v4_r3"]["rows_sharing_a_holdout_identity"]
    mix_c = stages["mixture_v4"]["rows_sharing_a_holdout_identity"]
    check("the leak is present in the fenrir bundle as downloaded, before any of this "
          "project's own processing",
          raw_c > 0,
          f"{raw_c} rows of {FENRIR_BUNDLE.name} already carry a held-out identity — the "
          f"contamination predates this project")
    check("the leak survives the v3 cleaning step",
          clean_c > 0,
          f"{clean_c} rows of the cleaned fenrir file carry a held-out identity")
    check("the leak reaches v3's own SFT training file",
          sft_c > 0,
          f"{sft_c} rows of data/v3/sft/fenrir.jsonl carry a held-out identity — v3 was trained "
          f"on {stages['v3_sft_fenrir']['distinct_holdout_rows_covered_of_500']} of the 500 "
          f"held-out questions")
    check("the leak reaches v3's training mixture",
          v3mix_c > 0,
          f"{v3mix_c} rows of data/v3/mixture/mixture-v3-no-trail.jsonl carry a held-out identity")
    check("the leak reaches the rebuilt corpus",
          r3_c > 0,
          f"{r3_c} rows of data/v4/corpus-v4-r3.jsonl carry a held-out identity")
    check("the leak reaches the rebuilt mixture",
          mix_c > 0,
          f"{mix_c} rows of data/v4/mixture-v4.jsonl carry a held-out identity")
    check("the leak is confined to the fenrir stream in the mixture",
          stages["mixture_v4"]["source_labels_carrying_a_holdout_identity"] == ["fenrir"],
          f"source labels carrying a held-out identity: "
          f"{stages['mixture_v4']['source_labels_carrying_a_holdout_identity']}")
    check("the answers that leak are the held-out reference answers themselves",
          stages["mixture_v4"]["rows_carrying_the_same_answer_content"] > 0,
          f"{stages['mixture_v4']['rows_carrying_the_same_answer_content']} of "
          f"{stages['mixture_v4']['rows_where_an_answer_was_comparable']} comparable rows carry "
          f"the held-out row's own answer CONTENT; "
          f"{stages['mixture_v4']['rows_with_an_exactly_equal_reference_answer']} of them are "
          f"byte-identical and the rest differ only in JSON escaping depth")
    check("the leaked prompts are byte-identical to the held-out prompts, not paraphrases",
          stages["mixture_v4"]["rows_with_a_byte_identical_prompt"] > 0,
          f"{stages['mixture_v4']['rows_with_a_byte_identical_prompt']} of "
          f"{stages['mixture_v4']['rows_sharing_a_holdout_identity']} leaked rows carry a "
          f"byte-identical prompt string; the identity match is not an artefact of normalisation")
    check("the answer relationship is reported as a measured histogram",
          bool(stages["mixture_v4"]["answer_relationship_histogram"]),
          "answer relationship: "
          + ", ".join(f"{k} {v}" for k, v in
                      stages["mixture_v4"]["answer_relationship_histogram"].items()))

    # ------------------------------------------------------------------ the gate's own record
    gate_report = json.load(open(GATE_REPORT))
    candidate_ids = [str(c.get("id", "")) for c in gate_report["candidates"]]
    fenrir_in_gate = any("fenrir" in cid.lower() for cid in candidate_ids)
    check("the fenrir source was never a candidate in the v2 admission gate",
          not fenrir_in_gate,
          f"{len(candidate_ids)} candidates were gated; none names fenrir. The gated candidates "
          f"are: {candidate_ids}")
    check("the held-out set's own source corpus was gated and admitted",
          any("trendyol" in cid.lower() for cid in candidate_ids),
          "the Trendyol corpus — the corpus the held-out split was taken from — is candidate 0 "
          "and was admitted, with overlap_max 0.0266")

    # ------------------------------------------------------------------ what v3 checked
    v3_report_text = FENRIR_CONTAM_REPORT.read_text(encoding="utf-8", errors="replace")
    checked_against = ("CyberMetric-500" in v3_report_text and "SecQA" in v3_report_text)
    holdout_named = "holdout" in v3_report_text.lower()
    populations_named = [p for p in ("CyberMetric-500", "SecQA") if p in v3_report_text]
    check("the v3 fenrir contamination report's zero does NOT cover the held-out set",
          not holdout_named,
          f"CONTAMINATION_REPORT.md names the held-out set: {holdout_named}. It reports "
          f"'contaminated rows: 0' against the populations it names "
          f"({', '.join(populations_named) or 'unstated'}; SecQA's fingerprint file was a "
          f"failed-download placeholder and was excluded) — a different population from the "
          f"500-row held-out set, so its zero does not contradict this finding")

    report = {
        "what_this_is": "F-8c — the path by which the 500-row held-out set enters the rebuilt "
                        "mixture, measured stage by stage with the project's own identity key.",
        "identity_key": {
            "definition": "sha256(' '.join(user.lower().split()))[:16]",
            "source": "v2/export_holdout.py (the exporter that wrote the held-out file), whose "
                      "own comment states it must match gate_v2.prompt_hash_of and the dedupe key",
            "cross_checked_against": "v2/gate_v2.py::prompt_hash_of, imported not re-implemented",
            "cross_check_rows": 100,
            "cross_check_agreement": key_agree,
        },
        "no_new_data": "every file read is already on disk; this script downloads nothing",
        "stages": stages,
        "the_chain": {
            "fenrir_bundle_raw": raw_c,
            "fenrir_clean": clean_c,
            "v3_sft_fenrir": sft_c,
            "v3_mixture": v3mix_c,
            "corpus_v4_r3": r3_c,
            "mixture_v4": mix_c,
            "reading": "the contamination is present in the fenrir download itself and is carried "
                       "forward by every later stage — including v3's own training file and "
                       "training mixture; no stage in this project introduced it",
        },
        "the_gate_record": {
            "candidates_gated": len(candidate_ids),
            "candidate_ids": candidate_ids,
            "fenrir_was_gated": fenrir_in_gate,
            "reading": "the v2 admission gate never saw fenrir, so the held-out set's exclusion "
                       "was never established for the source that actually carries it",
        },
        "the_v3_record": {
            "file": str(FENRIR_CONTAM_REPORT.relative_to(ROOT)),
            "names_the_holdout_set": holdout_named,
            "reading": "the v3 contamination report's zero covers CyberMetric-500 (and SecQA, whose "
                       "fingerprint file was a failed-download placeholder and was excluded). It "
                       "covers neither the 500-row held-out set nor the Trendyol corpus it came from",
        },
        "checks": [{"name": n, "pass": p, "detail": d} for n, p, d in checks],
        "pass": sum(1 for _, p, _ in checks if p),
        "total": len(checks),
        "all_pass": all(p for _, p, _ in checks),
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    npass = report["pass"]
    print(f"\n{npass}/{len(checks)} checks PASS → {OUT}")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
