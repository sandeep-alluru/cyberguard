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
    exact, sh, index, short = set(), [], {}, {}
    for r in refs:
        exact.add(norm(r))
        rt = toks(r)
        if len(rt) < SHORT_TOKENS:
            # indexed by length: a sliding-window search per (length) beats a scan per reference
            if len(rt) >= 6 and (r.strip().endswith("?") or len(rt) >= 10):
                short.setdefault(len(rt), set()).add(tuple(rt))
            continue
        s = grams(r, n)
        i = len(sh)
        sh.append(s)
        for x in s:
            index.setdefault(x, []).append(i)
    return exact, sh, index, short


def hits(text, idx, n, jac_min, con_min):
    """Leak test, in order: exact match, contiguous short-reference copy, then n-gram overlap.

    The contiguous rule was previously reachable only when the FIELD was short, so a short reference
    padded into a longer field — the exact false negative review #3 demonstrated — was never checked.
    It now applies to fields of any length, with two guards calibrated against reproduced cases:
    references under 6 tokens are noun phrases, not prompts; and a reference must either be a question
    or be at least 10 tokens long, so shared terminology inside a different sentence is not a leak.

      Review #4 removed a THIRD guard ("slack <= 8 words"): it measured padding, not leak-hood.
      A reference copied in full and then wrapped in 9 extra words is *more* copied, not less, and
      the reviewer showed exactly that string escaping the scan. The copy's completeness is already
      established by the window being the reference's own length; the qualification rules above are
      what keep short shared phrasing out.
    """
    exact, sh, index, short = idx
    k = norm(text)
    if k in exact:
        return "exact"
    ft = toks(text)
    for length, windows in short.items():
        if length > len(ft):
            continue
        for i in range(0, len(ft) - length + 1):
            if tuple(ft[i:i + length]) in windows:
                return f"short-reference-copied (contiguous, +{len(ft) - length} words)"
    if len(ft) < SHORT_TOKENS:
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
        c = shared / min(len(s), len(h))
        if c >= con_min:
            return f"containment {c:.3f}"
    return None


def collect_probe_strings():
    """The ONE probe collector, used by both the scanner and the audit (review #3: the audit reported
    160 probes against the scanner's 225, so its PASS did not establish equivalent coverage)."""
    def strings_in(obj, out):
        if isinstance(obj, str):
            if len(obj.strip()) >= 20:
                out.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                strings_in(v, out)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                strings_in(v, out)
    out = []
    try:
        sys.path.insert(0, ".")
        import cap_probes as PB
        for name in dir(PB):
            v = getattr(PB, name)
            if isinstance(v, list) and name.isupper():
                strings_in(v, out)
    except Exception:                                          # noqa: BLE001
        pass
    return out


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

    refs = {"holdout": load_refs(args.holdout, "prompt"), "probes": collect_probe_strings()}
    probe_sets = {}
    try:
        sys.path.insert(0, ".")
        import cap_probes as PB
        for name in dir(PB):
            v = getattr(PB, name)
            if isinstance(v, list) and name.isupper():
                probe_sets[name] = len(v)
        print(f"  evaluation sets covered: {probe_sets} -> {len(refs['probes'])} reference strings")
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
