#!/usr/bin/env python3
"""G-D span scorer — character-offset, typed span F1 (the missing half of §8.9's G-D contract).

Why this exists: review cycle 3 found that the plan claimed G-D's scorer was present while only the
human reference was missing. It was not. `cap_scorers.ioc_score(gen, gold: set, source_text)` computes
F1 over **sets of normalized IOC strings** — it takes no offsets and no span types, and repeated
occurrences collapse into one value. `v2/gates_v2.py` merely *consumes* a per-document
`bootstrap_lower_span_f1`; nothing in the repo computed typed, offset-based span F1.

This implements the contract in §8.9: for each pinned document, gold spans carry
`{start, end, value, type}` and predictions are derived from the model's output by locating extracted
IOC values back into the source text (which is what gives them offsets and types). Scoring is:

  * **typed exact-span match** — a predicted span counts as correct iff `(start, end, type)` matches a
    gold span. Value-only matching would credit a prediction that found the right string at the wrong
    place or as the wrong entity type, which is not what "extraction with offsets" claims.
  * **micro span-F1** over the 100 documents, plus the per-document mean.
  * **bootstrap CI** for F1 — F1 is not binomial, so a Wilson interval is not available; the plan says
    bootstrap and this does bootstrap.
  * **fabricated-IOC rate** — documents containing ≥1 predicted value that appears NOWHERE in the
    source text (i.e. invented). Reported as a document share, per §8.9.

Deliberately small and dependency-free (stdlib only), matching the over-engineering directive: it
computes the specified statistics and carries no gate framework. `--self-test` covers the failure modes
that matter (offset-shifted, type-swapped, duplicate-occurrence, and invented values).

Usage:
  python3 tools/gd_span_scorer_v3.py --self-test
  python3 tools/gd_span_scorer_v3.py --gold gold.jsonl --pred preds.jsonl [--bootstrap 2000]
    gold.jsonl : {"row_idx": 0, "source": "...", "spans": [{"start":0,"end":5,"value":"x","type":"domain"}]}
    preds.jsonl: {"row_idx": 0, "output": "<model reply text>"}   (offsets derived from source)
"""
import argparse
import json
import random
import re
import sys

# IOC type detection, ordered so more specific patterns win (ip before domain, url before both).
TYPED = (
    ("url", re.compile(r"https?://[^\s\"'<>)\]]+", re.I)),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("md5", re.compile(r"\b[a-f0-9]{32}\b", re.I)),
    ("sha1", re.compile(r"\b[a-f0-9]{40}\b", re.I)),
    ("sha256", re.compile(r"\b[a-f0-9]{64}\b", re.I)),
    ("cve", re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)),
    ("domain", re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}\b", re.I)),
)


def extract_typed(text):
    """Set of (value_lower, type) candidates found in text."""
    out = set()
    for kind, pat in TYPED:
        for m in pat.finditer(text or ""):
            v = m.group(0).rstrip(".,;:")
            if kind == "ipv4" and any(int(o) > 255 for o in v.split(".")):
                continue
            out.add((v.lower(), kind))
    return out


def spans_from_output(output, source):
    """Predictions: locate each extracted IOC value in the SOURCE to obtain real offsets + type.

    Values not present in the source get no span (they are the fabricated case, counted separately),
    because an offset that does not exist in the document is not a span.
    """
    low = (source or "").lower()
    spans = []
    for value, kind in extract_typed(output):
        for m in re.finditer(re.escape(value), low):
            spans.append({"start": m.start(), "end": m.end(), "value": value, "type": kind})
    return spans


def _key(s):
    return (s["start"], s["end"], s["type"])


def span_f1(pred, gold):
    """Typed exact-span micro counts."""
    p, g = {_key(s) for s in pred}, {_key(s) for s in gold}
    tp = len(p & g)
    return tp, len(p) - tp, len(g) - tp


def bootstrap_f1(pairs, iters=2000, seed=0):
    """Percentile bootstrap CI on micro F1 over (tp, fp, fn) per document."""
    if not pairs:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    f1s = []
    for _ in range(iters):
        tp = fp = fn = 0
        for _ in range(len(pairs)):
            t, f, n = pairs[rng.randrange(len(pairs))]
            tp += t
            fp += f
            fn += n
        f1s.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    f1s.sort()
    return (f1s[int(0.025 * len(f1s))], f1s[int(0.975 * len(f1s)) - 1], sum(f1s) / len(f1s))


def score(gold_rows, pred_by_idx, iters=2000):
    pairs, per_doc, fab_docs, n_docs = [], [], 0, 0
    n_pred_missing = n_gold_missing = 0
    for g in gold_rows:
        idx = g["row_idx"]
        src = g.get("source", "")
        # ABSENT IS NOT EMPTY (Astra design pass, defect 4.3). This used `pred_by_idx.get(idx, "")`,
        # which made a MISSING prediction identical to an observed empty answer, and
        # `g.get("spans") or []`, which made a document with NO gold annotation identical to one
        # annotated as empty. Combined with the `not gold and not pred -> 1.0` branch, 100 documents
        # carrying no predictions and no gold produced mean F1 1.0, fabricated share 0.0, and a PASS.
        # Absence is now tracked explicitly and reported as unknown, never scored.
        # Astra final review (item 3): a MISSING key was handled, but a present key whose VALUE is None
        # fell through to `spans_from_output(None, src)` -> no spans -> with empty gold, F1 1.0. An
        # explicit null prediction is an absent prediction, not an observed empty answer.
        if idx not in pred_by_idx or pred_by_idx.get(idx) is None:
            n_pred_missing += 1
            n_docs += 1
            per_doc.append(None)
            continue
        # Astra final review (4.3 remainder): `"spans" not in g` caught a MISSING key, but an explicit
        # `spans: None` fell through to `or []` and became EMPTY GOLD -- which with an empty prediction
        # scores F1 1.0 and PASSes. An explicit null is an absent annotation, not an empty one.
        gold = g.get("spans")
        if gold is None:
            n_gold_missing += 1
            n_docs += 1
            per_doc.append(None)
            continue
        gold = gold or []
        out = pred_by_idx.get(idx, "")
        pred = spans_from_output(out, src)
        tp, fp, fn = span_f1(pred, gold)
        pairs.append((tp, fp, fn))
        n_docs += 1
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else (1.0 if not gold and not pred else 0.0)
        per_doc.append(f1)
        low = src.lower()
        if any(v not in low for v, _ in extract_typed(out)):
            fab_docs += 1
    tp = sum(p[0] for p in pairs)
    fp = sum(p[1] for p in pairs)
    fn = sum(p[2] for p in pairs)
    micro = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    _unknown = n_pred_missing + n_gold_missing
    # With any required document unresolved the aggregate is UNKNOWN, not a number: the population
    # was not measured. The per-document None entries above carry which documents are unresolved, and
    # the per-document list is still returned in full so nothing is silently dropped.
    _nn = [d for d in per_doc if d is not None]
    if _unknown:
        return {"per_doc_f1": [None if d is None else round(d, 6) for d in per_doc],
                "n_docs": n_docs, "n_pred_missing": n_pred_missing, "n_gold_missing": n_gold_missing,
                "n_known": len(_nn),
                "tp": tp, "fp": fp, "fn": fn,
                "span_f1_micro": None, "span_f1_micro_ci95": None,
                "span_f1_mean_per_doc": None,
                "fabricated_docs": None, "fabricated_doc_share": None,
                "reason": ("%d of %d required documents have no prediction and %d have no gold "
                           "annotation -> span-F1 and the fabricated-doc share are UNMEASURED"
                           % (n_pred_missing, n_docs, n_gold_missing)),
                "ci_method": "percentile bootstrap on per-document (tp,fp,fn)"}
    lo, hi, mean = bootstrap_f1(pairs, iters)
    return {"per_doc_f1": [round(x, 6) for x in per_doc],
            "n_docs": n_docs, "n_pred_missing": 0, "n_gold_missing": 0, "n_known": n_docs,
            "tp": tp, "fp": fp, "fn": fn,
            "span_f1_micro": round(micro, 4), "span_f1_micro_ci95": [round(lo, 4), round(hi, 4)],
            "span_f1_mean_per_doc": round(sum(per_doc) / len(per_doc), 4) if per_doc else 0.0,
            "fabricated_docs": fab_docs,
            "fabricated_doc_share": round(fab_docs / n_docs, 4) if n_docs else 0.0,
            "ci_method": "percentile bootstrap on per-document (tp,fp,fn)"}


def self_test():
    ok = True

    def chk(name, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print("  %-64s %s" % (name, "OK" if good else "FAIL got=%s want=%s" % (got, want)))

    src = "Traffic to evil.example.com and 10.0.0.5 was blocked. See CVE-2021-44228."
    gold = [{"start": 11, "end": 27, "value": "evil.example.com", "type": "domain"},
            {"start": 32, "end": 40, "value": "10.0.0.5", "type": "ipv4"}]
    pred = spans_from_output("evil.example.com 10.0.0.5", src)
    chk("exact typed spans -> perfect F1", span_f1(pred, gold)[0], 2)

    shifted = [{"start": 12, "end": 28, "type": "domain"}, {"start": 32, "end": 40, "type": "ipv4"}]
    chk("offset-shifted span is NOT credited", span_f1(pred, shifted)[0], 1)

    wrongtype = [{"start": 11, "end": 27, "type": "url"}, {"start": 32, "end": 40, "type": "ipv4"}]
    chk("type-swapped span is NOT credited", span_f1(pred, wrongtype)[0], 1)

    dup_src = "see evil.example.com then evil.example.com again"
    dup = spans_from_output("evil.example.com", dup_src)
    chk("repeated occurrence yields BOTH offsets (set-F1 collapses them)", len(dup), 2)

    s = score([{"row_idx": 0, "source": src, "spans": gold}], {0: "evil.example.com 10.0.0.5"})
    chk("micro F1 = 1.0 on a perfect extraction", s["span_f1_micro"], 1.0)
    chk("no fabricated docs when all values are in source", s["fabricated_doc_share"], 0.0)

    s2 = score([{"row_idx": 0, "source": src, "spans": gold}], {0: "evil.example.com 203.0.113.9"})
    chk("invented IOC counted as a fabricated doc", s2["fabricated_docs"], 1)
    chk("invented IOC does not create a span", s2["fn"], 1)
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--gold")
    ap.add_argument("--pred")
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--out-gate-input", help="write the {extraction, fabricated_ioc} shape the G-D gate consumes")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.gold and a.pred):
        print(__doc__)
        return 2
    gold = [json.loads(l) for l in open(a.gold) if l.strip()]
    # Astra final review P1: `.get("output", "")` made a MISSING output field an observed empty answer,
    # which against empty gold scores F1 1.0 and PASSes G-D. Absent stays absent (the scorer already treats
    # a None prediction as unmeasured); only a present, explicitly empty string is an observed empty reply.
    preds = {json.loads(l)["row_idx"]: json.loads(l).get("output") for l in open(a.pred) if l.strip()}
    out = score(gold, preds, a.bootstrap)
    if a.out_gate_input:
        # Emit EXACTLY the shape v2/gates_v2.py consumes for G-D:
        #   extraction     -> [per-document span-F1]  (>=100 docs; the gate takes a bootstrap lower bound)
        #   fabricated_ioc -> {rate, n}               (docs containing an invented IOC; bar <= 0.10)
        # Without this the gate only ever saw `extraction_mean`, a v1 aggregate it explicitly refuses to
        # accept ("a stale mean must not stand in for it"), so G-D could not be measured even WITH labels.
        sub = {"extraction": out["per_doc_f1"],
               "fabricated_ioc": {"rate": out["fabricated_doc_share"], "n": out["n_docs"]},
               "source": "tools/gd_span_scorer_v3.py", "n_docs": out["n_docs"],
               "span_f1_micro": out["span_f1_micro"], "span_f1_micro_ci95": out["span_f1_micro_ci95"]}
        json.dump(sub, open(a.out_gate_input, "w"), indent=1, sort_keys=True)
        print("wrote gate input -> %s (%d docs)" % (a.out_gate_input, out["n_docs"]))
    print(json.dumps({k: v for k, v in out.items() if k != "per_doc_f1"}, indent=2))
    print("\n§8.9 bars: span-F1 >= 0.75 ; fabricated-doc share <= 0.10")
    return 0


if __name__ == "__main__":
    sys.exit(main())
