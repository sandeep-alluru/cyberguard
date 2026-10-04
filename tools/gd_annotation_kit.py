#!/usr/bin/env python3
# SIMPLIFIED OUT by PLAN-V3 rev 11: G-D now needs one annotator + owner spot-check, not a
# two-annotator inter-rater study. Retained in case G-D is confirmed decision-relevant. Unmaintained.

"""CyberGuard v3 — G-D reference-label annotation kit (§8.9 protocol).

Why: §8.9 declares G-D `STATUS: BLOCKED` because the 100 pinned documents carry `"labels": ""` —
verified 2026-09-30: 500 rows, 500 with empty-string labels, 0 with non-empty labels. The scorer
exists (`cap_scorers.extract_iocs` + `ioc_score(gen, gold, source_text)`); the gold reference does
not. G-D therefore cannot pass, and a missing measurement is a NO-SHIP.

This kit implements the rest of the §8.9 protocol so the remaining work is human annotation, not
engineering:

  --make    write the annotator-A worksheet (all 100 pinned docs) and the annotator-B blind
            worksheet (a random 20-doc subset, pinned seed), plus schema-conformant bundle
            templates. Documents are the first 100 rows in file order (deterministic, pinned).
  --verify  validate both bundles against the schema, require all 100 docs in A, compute
            per-document span-F1 between A and B on the 20-doc subset, require mean F1 >= 0.90
            (§8.9), and emit the receipt with the bundle SHA-256, the agreement score, and the
            adjudication placeholder. Below threshold it instructs a full re-annotation.

Binding constraints honoured (`no model-drafted substitute`): this tool never proposes spans, and
`--verify` rejects a bundle whose annotator field names a model rather than a person.

Bundle schema (one JSON object per line):
  {"row_idx": <int>, "annotator": "<name>", "spans": [{"start": <int>, "end": <int>,
   "value": "<str>", "type": "<str>"}, ...]}

Usage:
  gd_annotation_kit.py --make
  gd_annotation_kit.py --verify
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "v2/candidates/arcspan-train-sample.jsonl")
OUT = os.path.join(REPO, "v3/evals/gd")
N_DOCS = 100
N_RECHECK = 20
SEED = 20260930
F1_THRESHOLD = 0.90

SPAN_TYPES = ["ipv4", "domain", "url", "md5", "sha1", "sha256", "cve", "filepath",
              "registry", "email", "mutex", "other"]


def log(m):
    print(m, flush=True)


def load_docs():
    rows = []
    with open(SRC, encoding="utf8", errors="replace") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                rows.append((i, json.loads(line)))
    return rows


def make():
    os.makedirs(OUT, exist_ok=True)
    rows = load_docs()
    pinned = rows[:N_DOCS]
    rng = random.Random(SEED)
    recheck = sorted(rng.sample(range(N_DOCS), N_RECHECK))

    # annotator A: all 100
    a_tpl = os.path.join(OUT, "bundle-A.jsonl")
    with open(a_tpl, "w") as f:
        for idx, (row_idx, _d) in enumerate(pinned):
            f.write(json.dumps({"row_idx": row_idx, "annotator": "", "spans": []}) + "\n")
    # annotator B: blind re-annotation of the 20-doc subset
    b_tpl = os.path.join(OUT, "bundle-B.jsonl")
    with open(b_tpl, "w") as f:
        for idx in recheck:
            f.write(json.dumps({"row_idx": pinned[idx][0], "annotator": "", "spans": []}) + "\n")

    ws = os.path.join(OUT, "G-D-ANNOTATION-WORKSHEET.md")
    with open(ws, "w") as f:
        f.write("# G-D reference-label worksheet — CyberGuard v3 (§8.9)\n\n")
        f.write("**What this is.** §8.9 requires human-authored gold IOC/entity spans for the %d\n"
                "pinned documents, independently re-annotated on a %d-document subset, before the G-D\n"
                "gate can be measured at all. The scorer already exists; this reference does not.\n\n"
                % (N_DOCS, N_RECHECK))
        f.write("**How to record a span.** For every IOC/entity in a document record its exact\n")
        f.write("character offsets into the document text, its normalized value, and its type.\n")
        f.write("Permitted types: `%s`.\n\n" % "`, `".join(SPAN_TYPES))
        f.write("Write into `%s` (all %d documents) with your name in `annotator`.\n\n"
                % (os.path.relpath(a_tpl, REPO), N_DOCS))
        f.write("**Second annotator (blind).** A *different* person must re-annotate the %d documents\n"
                "listed in `%s` without seeing the first pass. Span-level F1 between the two passes\n"
                "must be >= %.2f; below that the full set is re-annotated, and disagreements are\n"
                "adjudicated by a third qualified reviewer with the adjudications recorded.\n\n"
                % (N_RECHECK, os.path.relpath(b_tpl, REPO), F1_THRESHOLD))
        f.write("**Not permitted:** model-drafted spans as a substitute for human annotation.\n")
        f.write("`--verify` rejects a bundle whose `annotator` names a model.\n\n")
        f.write("Then run: `python3 tools/gd_annotation_kit.py --verify`\n\n---\n\n")
        for n, (row_idx, d) in enumerate(pinned):
            f.write("## doc %d — row_idx %d\n\n" % (n, row_idx))
            f.write("```text\n%s\n```\n\n" % d["text"])
            f.write("spans: _(fill in bundle)_\n\n")

    meta = {"source": os.path.relpath(SRC, REPO), "n_docs": N_DOCS,
            "row_idx": [r for r, _ in pinned], "recheck_row_idx": [pinned[i][0] for i in recheck],
            "seed": SEED, "f1_threshold": F1_THRESHOLD, "span_types": SPAN_TYPES}
    with open(os.path.join(OUT, "kit-meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    log("wrote %s (%d docs), %s (%d docs), %s"
        % (os.path.relpath(ws, REPO), N_DOCS, os.path.relpath(b_tpl, REPO), N_RECHECK,
           os.path.relpath(a_tpl, REPO)))
    log("recheck subset (blind, seed %d): %s" % (SEED, meta["recheck_row_idx"]))


def span_key(s, exact=True):
    if exact:
        return (int(s["start"]), int(s["end"]), str(s.get("type", "")))
    return (str(s.get("value", "")).lower(), str(s.get("type", "")))


def f1(a_spans, b_spans):
    A = {span_key(s) for s in a_spans}
    B = {span_key(s) for s in b_spans}
    if not A and not B:
        return 1.0
    if not A or not B:
        return 0.0
    tp = len(A & B)
    if tp == 0:
        return 0.0
    p, r = tp / len(A), tp / len(B)
    return 2 * p * r / (p + r)


def load_bundle(path):
    out = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                out[int(d["row_idx"])] = d
    return out


MODEL_HINTS = ("gpt", "chatgpt", "openai", "claude", "gemini", "llama", "mistral", "model", "llm")
MIN_INFORMATIVE_FRACTION = 0.80


def verify():
    meta = json.load(open(os.path.join(OUT, "kit-meta.json")))
    a = load_bundle(os.path.join(OUT, "bundle-A.jsonl"))
    b = load_bundle(os.path.join(OUT, "bundle-B.jsonl"))
    problems = []

    for name, bundle in (("A", a), ("B", b)):
        for idx, d in bundle.items():
            who = str(d.get("annotator", "")).strip()
            if not who:
                problems.append("bundle %s row_idx %d has no annotator name" % (name, idx))
            elif any(re.search(r"\b" + h + r"\b", who.lower()) for h in MODEL_HINTS):
                problems.append("bundle %s row_idx %d annotator %r looks like a model, not a person"
                                % (name, idx, who))
            for s in d.get("spans", []):
                for k in ("start", "end", "value", "type"):
                    if k not in s:
                        problems.append("bundle %s row_idx %d span missing %r" % (name, idx, k))
                if s.get("type") not in meta["span_types"]:
                    problems.append("bundle %s row_idx %d span type %r not permitted"
                                    % (name, idx, s.get("type")))

    missing_a = [r for r in meta["row_idx"] if r not in a]
    missing_b = [r for r in meta["recheck_row_idx"] if r not in b]
    if missing_a:
        problems.append("bundle A missing %d of %d documents" % (len(missing_a), meta["n_docs"]))
    if missing_b:
        problems.append("bundle B missing %d of %d recheck documents"
                        % (len(missing_b), len(meta["recheck_row_idx"])))

    per_doc, uninformative, ok = [], [], not problems
    for r in meta["recheck_row_idx"]:
        if r in a and r in b:
            sa, sb = a[r].get("spans", []), b[r].get("spans", [])
            if not sa and not sb:
                # two empty passes are not agreement -- almost certainly "not yet annotated"
                uninformative.append(r)
                continue
            per_doc.append({"row_idx": r, "span_f1": round(f1(sa, sb), 4)})
    mean = round(sum(d["span_f1"] for d in per_doc) / len(per_doc), 4) if per_doc else None
    informative_fraction = (len(per_doc) / len(meta["recheck_row_idx"])
                            if meta["recheck_row_idx"] else 0.0)
    if informative_fraction < MIN_INFORMATIVE_FRACTION:
        problems.append("only %.0f%% of recheck documents carry spans in either pass (need >= %.0f%%); "
                        "empty-vs-empty is not agreement"
                        % (100 * informative_fraction, 100 * MIN_INFORMATIVE_FRACTION))
        ok = False

    verdict = "PASS" if (ok and mean is not None and mean >= meta["f1_threshold"]) else "FAIL"
    receipt = {
        "at": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "gate": "G-D reference labels (§8.9 protocol)",
        "bundle_A": {"path": "v3/evals/gd/bundle-A.jsonl",
                     "sha256": hashlib.sha256(open(os.path.join(OUT, "bundle-A.jsonl"), "rb").read()).hexdigest(),
                     "documents": len(a), "annotators": sorted({d.get("annotator", "") for d in a.values()})},
        "bundle_B": {"path": "v3/evals/gd/bundle-B.jsonl",
                     "sha256": hashlib.sha256(open(os.path.join(OUT, "bundle-B.jsonl"), "rb").read()).hexdigest(),
                     "documents": len(b), "annotators": sorted({d.get("annotator", "") for d in b.values()})},
        "recheck_subset": meta["recheck_row_idx"], "threshold": meta["f1_threshold"],
        "mean_span_f1": mean, "per_doc": per_doc,
        "uninformative_docs_excluded": uninformative,
        "informative_fraction": round(informative_fraction, 4),
        "agreement_definition": "exact (start, end, type) match; per-doc F1 averaged over the subset",
        "problems": problems, "verdict": verdict,
        "adjudication": "PENDING — required only for documents where the two passes disagree",
        "note": "No span is model-drafted; --verify rejects model-named annotators.",
    }
    with open(os.path.join(OUT, "G-D-ANNOTATION-RECEIPT.json"), "w") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")

    log("documents: A=%d B=%d | schema problems: %d" % (len(a), len(b), len(problems)))
    for p in problems[:10]:
        log("  PROBLEM: %s" % p)
    log("mean span-F1 on the %d-doc subset: %s (threshold %s)" % (len(per_doc), mean, meta["f1_threshold"]))
    log("VERDICT: %s" % verdict)
    if verdict == "FAIL" and mean is not None and mean < meta["f1_threshold"]:
        log("  below threshold -> the full set must be re-annotated and disagreements adjudicated (§8.9)")
    return 0 if verdict == "PASS" else 1


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--make", action="store_true")
    g.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    return make() or 0 if a.make else verify()


if __name__ == "__main__":
    sys.exit(main())
