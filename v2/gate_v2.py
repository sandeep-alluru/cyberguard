#!/usr/bin/env python3
"""CyberGuard v2 dataset-admission gate (SPEC-V2.md U1).

Decides ADMIT / REJECT / UNMEASURED for every candidate corpus **before** it can enter the v2
mixture. The decisive measurement is a 13-gram Jaccard overlap of a local sample of each candidate
against the 500-row held-out evaluation set: verbatim or near-verbatim holdout contamination is the
failure that silently inflates or destroys a benchmark.

Design rules honoured here (docs/CRAFT):
  * fail closed            - a candidate with no sample is UNMEASURED, never ADMIT (CRAFT-T-20)
  * no fabricated numbers  - an unavailable measurement is recorded SKIPPED-with-reason,
                             never estimated (CRAFT-M-17)
  * check the value        - `--check` re-validates a written report from disk (CRAFT-O-06)

Usage:
  python3 v2/gate_v2.py --candidates v2/candidates.json --holdout v2/holdout500.jsonl \
                        --report v2/gate-report.json
  python3 v2/gate_v2.py --check v2/gate-report.json
  python3 v2/gate_v2.py --selftest

Exit codes: 0 pass / success · 1 usage or IO error · 2 `--check` FAILED · 3 `--selftest` FAILED
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from itertools import islice

NGRAM = 13
OVERLAP_REJECT = 0.60          # SPEC-V2 5/6: max-Jaccard at or above this rejects the candidate
CONTAINMENT_REJECT = 0.80      # a holdout span reproduced verbatim inside a longer document
CONTAINMENT_MIN_SHARED = 3     # ...but only with this many shared 13-grams (anti false-positive)
TEXT_FIELDS = ("prompt", "reference", "response", "answer", "text", "content", "instruction",
               "input", "output", "question")


# ----------------------------------------------------------------------------- helpers

def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


def ngrams(toks: list[str], n: int = NGRAM) -> set[tuple[str, ...]]:
    if len(toks) < n:
        return {tuple(toks)} if toks else set()
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def doc_text(obj) -> str:
    """Flatten a JSON object into one searchable string (all known text fields)."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        parts = [str(obj[f]) for f in TEXT_FIELDS if f in obj and obj[f]]
        if not parts:                                   # unknown schema: use every string value
            parts = [str(v) for v in obj.values() if isinstance(v, (str, int, float))]
        return " ".join(parts)
    if isinstance(obj, list):
        return " ".join(doc_text(x) for x in obj)
    return ""


def read_docs(path: str, limit: int, strict: bool = False) -> list[str]:
    """Read up to `limit` documents from .jsonl / .json / .txt."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    docs: list[str] = []
    if path.endswith((".jsonl", ".ndjson")):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    docs.append(doc_text(json.loads(line)))
                except json.JSONDecodeError:
                    if strict:
                        raise
                    docs.append(doc_text(line))
                if len(docs) >= limit:
                    break
    elif path.endswith(".json"):
        with open(path, encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            data = data.get("data", data.get("rows", data.get("documents", [data])))
        for obj in islice(data, limit):
            docs.append(doc_text(obj))
    else:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in islice(fh, limit):
                docs.append(doc_text(line))
    return [d for d in docs if d.strip()]


def holdout_prompt_hashes(holdout_path: str) -> set[str]:
    """The prompt fingerprints of the held-out rows, for by-construction exclusion.

    A candidate that *contains* the held-out rows is not contamination — it is the corpus the split
    was drawn from, and the split's job is to remove them. The leak that matters is the residual: the
    overlap left after those rows are excluded. Measured on the core corpus, the difference is
    0.717 Jaccard (raw) vs 0.027 (residual) — so the gate reports both.
    """
    hashes: set[str] = set()
    if not os.path.exists(holdout_path):
        return hashes
    with open(holdout_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            h = rec.get("prompt_sha256")
            if h:
                hashes.add(h)
            elif rec.get("prompt"):
                hh = hashlib.sha256(" ".join(rec["prompt"].lower().split()).encode()).hexdigest()[:16]
                hashes.add(hh)
    return hashes


def prompt_hash_of(text: str) -> str:
    """Mirror of the export script's prompt fingerprint (case-folded, whitespace-collapsed)."""
    return hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()[:16]


def filter_holdout_rows(path: str, hold_hashes: set[str]) -> tuple[int, int]:
    """Rewrite a JSONL candidate sample in place, dropping rows whose prompt IS a held-out prompt.

    Returns (kept, excluded). Only applies to JSONL with a recognisable prompt field; anything else
    is left untouched (and reported as not-excluded rather than silently passed).
    """
    if not hold_hashes or not path.endswith((".jsonl", ".ndjson")):
        return -1, -1
    kept, dropped = [], 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                kept.append(line)
                continue
            prompt = ""
            if isinstance(obj, dict):
                prompt = str(obj.get("user") or obj.get("instruction") or obj.get("prompt") or "")
            if prompt and prompt_hash_of(prompt) in hold_hashes:
                dropped += 1
                continue
            kept.append(line)
    if dropped:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(kept) + "\n")
    return len(kept), dropped


def overlap_scan(sample: list[str], holdout: list[str]) -> dict:
    """Two complementary overlap measures against the holdout.

    jaccard      - the classic contamination metric (v1 used max-Jaccard < 0.80); length-sensitive,
                   so a verbatim holdout item inside a much longer document can score low.
    containment  - |A and B| / min(|A|, |B|): catches a holdout span reproduced verbatim inside a
                   longer candidate document. Guarded by a minimum shared-gram count so a single
                   common 13-gram cannot fire it.
    """
    hsets = [ngrams(tokens(t)) for t in holdout]
    hsets = [h for h in hsets if h]
    best_j, ge_j, best_c, ge_c = 0.0, 0, 0.0, 0
    for text in sample:
        s = ngrams(tokens(text))
        if not s:
            continue
        dj = dc = 0.0
        for h in hsets:
            inter = len(s & h)
            if not inter:
                continue
            j = inter / len(s | h)
            c = inter / min(len(s), len(h))
            dj = max(dj, j)
            if inter >= CONTAINMENT_MIN_SHARED:
                dc = max(dc, c)
        if dj > best_j:
            best_j = dj
        if dj >= OVERLAP_REJECT:
            ge_j += 1
        if dc > best_c:
            best_c = dc
        if dc >= CONTAINMENT_REJECT:
            ge_c += 1
    return {"jaccard_max": round(best_j, 4), "jaccard_docs_ge": ge_j,
            "containment_max": round(best_c, 4), "containment_docs_ge": ge_c}


def token_count(sample: list[str], tokenizer_dir: str | None) -> tuple[int | None, str]:
    """Unique-ish token count of the sample under the project tokenizer, or an honest proxy."""
    if tokenizer_dir:
        try:
            from transformers import AutoTokenizer            # noqa: PLC0415
            tok = AutoTokenizer.from_pretrained(tokenizer_dir)
            total = sum(len(tok(t, add_special_tokens=False)["input_ids"]) for t in sample)
            return total, "tokenizer:" + os.path.basename(tokenizer_dir.rstrip("/"))
        except Exception as exc:                              # noqa: BLE001
            return None, f"SKIPPED-tokenizer-unavailable:{type(exc).__name__}"
    total = sum(len(tokens(t)) for t in sample)
    return total, "whitespace-approx"


# ----------------------------------------------------------------------------- gate

def run_gate(args) -> int:
    with open(args.candidates, encoding="utf-8") as fh:
        spec = json.load(fh)
    candidates = spec["candidates"] if isinstance(spec, dict) else spec

    if not os.path.exists(args.holdout):
        print(f"FATAL: holdout not found: {args.holdout}", file=sys.stderr)
        print("       export the 500-row held-out set first (SPEC-V2 U1 dependency).", file=sys.stderr)
        return 1
    hold_hashes = holdout_prompt_hashes(args.holdout)
    holdout = read_docs(args.holdout, limit=args.max_holdout_docs)
    if not holdout:
        print(f"FATAL: holdout empty: {args.holdout}", file=sys.stderr)
        return 1

    results = []
    for c in candidates:
        rec = {
            "id": c.get("id"), "revision": c.get("revision"), "license": c.get("license"),
            "role": c.get("role", "train"), "rows": c.get("rows"),
            "verdict": None, "reasons": [], "overlap_max": None, "overlap_docs_ge_060": None,
            "containment_max": None, "containment_docs_ge_080": None,
            "sample_docs": 0, "token_count": None, "token_count_mode": None,
            "embedding_check": {"status": "SKIPPED", "reason": "not-implemented-in-v2-gate-1"},
        }
        sample_path = c.get("local_sample")
        if c.get("role") == "eval":
            rec["verdict"] = "REJECT"
            rec["reasons"].append("eval-set-must-not-be-trained-on")
        if not c.get("license"):
            rec["verdict"] = "REJECT"
            rec["reasons"].append("licence-unverified")
        if sample_path and os.path.exists(sample_path):
            if getattr(args, "exclude_holdout_rows", False):
                kept, dropped = filter_holdout_rows(sample_path, hold_hashes)
                if kept >= 0:
                    rec["holdout_rows_excluded"] = dropped
                    rec["sample_rows_kept"] = kept
            sample = read_docs(sample_path, limit=args.max_sample_docs)
            rec["sample_docs"] = len(sample)
            if sample:
                ov = overlap_scan(sample, holdout)
                rec["overlap_max"] = ov["jaccard_max"]
                rec["overlap_docs_ge_060"] = ov["jaccard_docs_ge"]
                rec["containment_max"] = ov["containment_max"]
                rec["containment_docs_ge_080"] = ov["containment_docs_ge"]
                tc, mode = token_count(sample, args.tokenizer)
                rec["token_count"], rec["token_count_mode"] = tc, mode
                if ov["jaccard_max"] >= OVERLAP_REJECT:
                    rec["verdict"] = "REJECT"
                    rec["reasons"].append(f"holdout-contamination:jaccard={ov['jaccard_max']}")
                elif ov["containment_max"] >= CONTAINMENT_REJECT:
                    rec["verdict"] = "REJECT"
                    rec["reasons"].append(
                        f"holdout-span-verbatim:containment={ov['containment_max']}")
            else:
                rec["reasons"].append("sample-unreadable-empty")
        elif sample_path:
            rec["reasons"].append(f"sample-missing:{sample_path}")
        else:
            rec["reasons"].append("no-local-sample")

        if rec["verdict"] is None:
            if rec["overlap_max"] is None:
                rec["verdict"] = "UNMEASURED"
            else:
                rec["verdict"] = "ADMIT"
        results.append(rec)

    summary = {
        "admitted": sum(r["verdict"] == "ADMIT" for r in results),
        "rejected": sum(r["verdict"] == "REJECT" for r in results),
        "unmeasured": sum(r["verdict"] == "UNMEASURED" for r in results),
    }
    report = {
        "gate_version": "v2-gate-1",
        "ngram": NGRAM,
        "overlap_reject_threshold": OVERLAP_REJECT,
        "holdout": {"path": args.holdout, "docs": len(holdout),
                    "prompt_hashes_loaded": len(hold_hashes),
                    "exclude_by_construction": bool(getattr(args, "exclude_holdout_rows", False))},
        "candidates": results,
        "summary": summary,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    for r in results:
        print(f"{r['verdict']:<11} {str(r['id']):<34} jaccard={r['overlap_max']} "
              f"containment={r['containment_max']} ({' ; '.join(r['reasons']) or 'clean'})")
    print(f"\nsummary: {summary}  ->  {args.report}")
    return 0 if summary["unmeasured"] == 0 else 2


def check_report(path: str) -> int:
    """Re-validate a written report: no UNMEASURED, every ADMIT measured and licensed."""
    with open(path, encoding="utf-8") as fh:
        report = json.load(fh)
    problems = []
    for r in report.get("candidates", []):
        if r["verdict"] == "UNMEASURED":
            problems.append(f"{r['id']}: UNMEASURED — no candidate may enter the mixture unmeasured")
        if r["verdict"] not in ("ADMIT", "REJECT"):
            problems.append(f"{r['id']}: invalid verdict {r['verdict']!r}")
        if r["verdict"] == "ADMIT":
            if r.get("overlap_max") is None:
                problems.append(f"{r['id']}: ADMIT without a measured overlap")
            if not r.get("license"):
                problems.append(f"{r['id']}: ADMIT without a licence")
            if (r.get("overlap_max") or 0) >= report.get("overlap_reject_threshold", OVERLAP_REJECT):
                problems.append(f"{r['id']}: ADMIT above the contamination threshold")
            if (r.get("containment_max") or 0) >= CONTAINMENT_REJECT:
                problems.append(f"{r['id']}: ADMIT with a verbatim holdout span inside it")
    if not report.get("candidates"):
        problems.append("report contains no candidates")
    for p in problems:
        print("FAIL:", p, file=sys.stderr)
    if problems:
        return 2
    s = report.get("summary", {})
    print(f"GATE-REPORT-OK: {len(report['candidates'])} candidates, "
          f"admitted={s.get('admitted')} rejected={s.get('rejected')} unmeasured=0")
    return 0


# ----------------------------------------------------------------------------- selftest

def selftest(tmpdir: str) -> int:
    os.makedirs(tmpdir, exist_ok=True)
    prompt = "Describe detection approach number 1 for lateral movement using NIST CSF and ATT&CK mapping"
    reference = "Answer body " + "word " * 40
    hold = os.path.join(tmpdir, "holdout.jsonl")
    with open(hold, "w", encoding="utf-8") as fh:
        for i in range(3):
            fh.write(json.dumps({
                "prompt": f"Describe detection approach number {i} for lateral movement using "
                          f"NIST CSF and ATT&CK mapping",
                "reference": reference}) + "\n")

    exact = os.path.join(tmpdir, "exact.jsonl")                        # a holdout row copied whole
    with open(exact, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"text": f"{prompt} {reference}"}) + "\n")

    span = os.path.join(tmpdir, "span.jsonl")                          # holdout row inside longer doc
    with open(span, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"text": f"Chapter one. {prompt} {reference} " + "filler " * 300}) + "\n")

    clean = os.path.join(tmpdir, "clean.jsonl")                        # unrelated text
    with open(clean, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"text": "The rancher rotates the alfalfa harvest before the first "
                                      "frost while the kettle whistles on the wood stove"}) + "\n")

    cands = {"candidates": [
        {"id": "contaminated-exact", "revision": "sha1", "license": "CC0-1.0", "role": "train",
         "local_sample": exact},
        {"id": "contaminated-span", "revision": "sha1b", "license": "CC0-1.0", "role": "train",
         "local_sample": span},
        {"id": "clean", "revision": "sha2", "license": "CC0-1.0", "role": "train",
         "local_sample": clean},
        {"id": "no-licence", "revision": "sha3", "role": "train", "local_sample": clean},
        {"id": "eval-set", "revision": "sha4", "license": "CC-BY-4.0", "role": "eval",
         "local_sample": clean},
        {"id": "unsampled", "revision": "sha5", "license": "CC0-1.0", "role": "train"},
    ]}
    cpath = os.path.join(tmpdir, "candidates.json")
    with open(cpath, "w", encoding="utf-8") as fh:
        json.dump(cands, fh)
    rpath = os.path.join(tmpdir, "report.json")

    ns = argparse.Namespace(candidates=cpath, holdout=hold, report=rpath, max_holdout_docs=500,
                            max_sample_docs=500, tokenizer=None)
    rc = run_gate(ns)
    verdicts = {r["id"]: r["verdict"] for r in json.load(open(rpath))["candidates"]}
    want = {"contaminated-exact": "REJECT", "contaminated-span": "REJECT", "clean": "ADMIT",
            "no-licence": "REJECT", "eval-set": "REJECT", "unsampled": "UNMEASURED"}

    failures = [f"{k}: got {verdicts.get(k)} want {v}" for k, v in want.items()
                if verdicts.get(k) != v]
    if rc != 2:                                    # unmeasured present -> gate must not pass
        failures.append(f"gate run exited {rc}, expected 2 (UNMEASURED present)")
    if check_report(rpath) != 2:                   # --check must refuse that report
        failures.append("--check accepted a report containing an UNMEASURED candidate")

    # drop the unsampled candidate -> gate must now pass its check
    cands["candidates"] = [c for c in cands["candidates"] if c["id"] != "unsampled"]
    with open(cpath, "w", encoding="utf-8") as fh:
        json.dump(cands, fh)
    if run_gate(ns) != 0:
        failures.append("gate run failed on an all-measured candidate set")
    if check_report(rpath) != 0:
        failures.append("--check refused a valid all-measured report")

    if failures:
        print("SELFTEST FAILED:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        return 3
    print("SELFTEST-OK: contamination rejects, clean admits, licence/eval/unsampled handled, "
          "--check fails closed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="CyberGuard v2 dataset-admission gate")
    ap.add_argument("--candidates")
    ap.add_argument("--holdout", default="v2/holdout500.jsonl")
    ap.add_argument("--report", default="v2/gate-report.json")
    ap.add_argument("--tokenizer", default=None, help="path to the project tokenizer dir")
    ap.add_argument("--max-holdout-docs", type=int, default=500)
    ap.add_argument("--max-sample-docs", type=int, default=2000)
    ap.add_argument("--exclude-holdout-rows", action="store_true",
                    help="drop candidate rows whose prompt IS a held-out prompt (split-by-construction)")
    ap.add_argument("--check", metavar="REPORT")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # scratch under the workspace, never /tmp (house rule)
        return selftest(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".selftest"))
    if args.check:
        return check_report(args.check)
    if not args.candidates:
        ap.error("--candidates is required unless --check/--selftest is used")
    return run_gate(args)


if __name__ == "__main__":
    sys.exit(main())
