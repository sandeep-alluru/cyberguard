#!/usr/bin/env python3
"""leak_scan.py — ONE leakage instrument, replacing the three that disagreed.

The Astra data review found three different instruments (builder 5-gram, auditor 13-gram, admission gate
13-gram + containment) and that the auditor ignored 142 of 160 capability probes because they are shorter
than 13 tokens — so a short evaluation prompt could be trained on unnoticed. This is the single
instrument: exact match, n-gram Jaccard and containment, short references handled explicitly, all three
text fields, both arms, and both reference sets.

Usage: python3 v2/leak_scan.py --dir v2/data/mixture [--ngram 13] [--jaccard 0.80] [--containment 0.80]
Exit: 0 clean, 1 leak found, 2 usage/IO error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

SHORT_TOKENS = 13          # below this, n-gram matching is unreliable -> exact match governs


def toks(s):
    return re.findall(r"[a-z0-9]+", str(s).lower())


def norm(s):
    return " ".join(str(s).lower().split())


def grams(s, n):
    t = toks(s)
    return {tuple(t[i:i + n]) for i in range(max(0, len(t) - n + 1))}


def load_refs(path, field):
    refs = []
    if not os.path.exists(path):
        return refs
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            v = d.get(field)
            if isinstance(v, str) and v.strip():
                refs.append(v)
    return refs


def build_index(refs, n):
    """Return (exact_set, all_shingles, index) plus a short set handled by exact match only."""
    exact, sh, index, short = set(), [], {}, set()
    for r in refs:
        exact.add(norm(r))
        if len(toks(r)) < SHORT_TOKENS:
            short.add(norm(r))
            continue
        s = grams(r, n)
        i = len(sh)
        sh.append(s)
        for x in s:
            index.setdefault(x, []).append(i)
    return exact, sh, index, short


def hits(text, idx, n, jac_min, con_min):
    exact, sh, index, short = idx
    k = norm(text)
    if k in exact:
        return "exact"
    if len(toks(text)) < SHORT_TOKENS:
        # A short reference is a leak only when the field is THAT PROMPT with a few words added.
        # Two calibrations, both against reproduced false/true cases:
        #   * a 4-token noun phrase ("WMI event subscription persistence") sitting inside a different
        #     8-token question is a shared domain term, not contamination -> references under 6 tokens
        #     are handled by exact match only;
        #   * a genuine padded prompt keeps the reference contiguous and adds at most a few words, so
        #     the token-count excess is bounded.
        ft = toks(text)
        for r in short:
            rt = toks(r)
            if len(rt) < 6:                              # noun phrases are not prompts
                continue
            if len(ft) - len(rt) < 0 or len(ft) - len(rt) > 3:
                continue
            # CONTIGUOUS containment: set containment alone fired on re-orderings of the same words,
            # which is not a copied prompt. The reference's token sequence must appear as a run.
            window = len(rt)
            for i in range(0, len(ft) - window + 1):
                if tuple(ft[i:i + window]) == tuple(rt):
                    return f"short-reference-embedded (contiguous, +{len(ft) - len(rt)} words)"
        return None
        return None
    s = grams(text, n)
    if not s:
        return None
    cand = {}
    for x in s:
        for i in index.get(x, ()):
            cand[i] = cand.get(i, 0) + 1
    for i, shared in cand.items():
        h = sh[i]
        if not h:
            continue
        j = shared / len(s | h)
        if j >= jac_min:
            return f"jaccard {j:.3f}"
        if shared / min(len(s), len(h)) >= con_min:
            return f"containment {shared / min(len(s), len(h)):.3f}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="v2/data/mixture")
    ap.add_argument("--holdout", default="v2/holdout500.jsonl")
    ap.add_argument("--ngram", type=int, default=13)
    ap.add_argument("--jaccard", type=float, default=0.80)
    ap.add_argument("--containment", type=float, default=0.80)
    ap.add_argument("--out", default="v2/data/mixture/leak-scan.receipt.json")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    def strings_in(obj, out):
        """Recursively collect prompt-like strings from any item shape (str, tuple, dict, list)."""
        if isinstance(obj, str):
            if len(obj.strip()) >= 20:
                out.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                strings_in(v, out)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                strings_in(v, out)

    refs = {"holdout": load_refs(args.holdout, "prompt"), "probes": []}
    probe_sets = {}
    try:
        sys.path.insert(0, ".")
        import cap_probes as PB
        for name in dir(PB):
            v = getattr(PB, name)
            if isinstance(v, list) and name.isupper():
                out = []
                strings_in(v, out)
                if out:
                    probe_sets[name] = out
                    refs["probes"].extend(out)
        print("  evaluation sets covered: " + ", ".join(f"{k}={len(v)}" for k, v in probe_sets.items()))
    except Exception as e:                                     # noqa: BLE001
        print(f"WARNING: cap_probes not importable ({e}); probe set empty", file=sys.stderr)

    idx = {k: build_index(v, args.ngram) for k, v in refs.items()}
    print(f"  references: holdout={len(refs['holdout'])} probes={len(refs['probes'])} "
          f"(short, exact-only: holdout={len(idx['holdout'][3])} probes={len(idx['probes'][3])})")

    findings, checked = [], 0
    for arm in ("armA.jsonl", "armB.jsonl"):
        path = os.path.join(args.dir, arm)
        if not os.path.exists(path):
            print(f"FATAL: {path} missing", file=sys.stderr)
            return 2
        with open(path, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                checked += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for field in ("system", "user", "assistant"):     # all fields, not just the prompt
                    text = row.get(field) or ""
                    if not text.strip():
                        continue
                    for setname, ix in idx.items():
                        why = hits(text, ix, args.ngram, args.jaccard, args.containment)
                        if why:
                            findings.append({"arm": arm, "line": i, "field": field,
                                             "reference_set": setname, "match": why,
                                             "excerpt": str(text)[:160]})
    rcpt = {"checked_rows": checked, "references": {k: len(v) for k, v in refs.items()},
            "ngram": args.ngram, "jaccard_min": args.jaccard, "containment_min": args.containment,
            "findings": findings, "verdict": "CLEAN" if not findings else "LEAK",
            "arm_sha256": {a: hashlib.sha256(open(os.path.join(args.dir, a), "rb").read()).hexdigest()
                           for a in ("armA.jsonl", "armB.jsonl")}}
    if not args.no_write:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(rcpt, fh, indent=2)
        except OSError as e:
            print(f"(receipt not written: {e})")
    for f in findings[:10]:
        print(f"  LEAK {f['arm']}:{f['line']} {f['field']} vs {f['reference_set']} ({f['match']})")
    print(f"\n  rows checked: {checked:,} ({checked // 2:,} per arm) | findings: {len(findings)}")
    print(f"  VERDICT: {rcpt['verdict']}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
