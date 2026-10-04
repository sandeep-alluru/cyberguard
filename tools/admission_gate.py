#!/usr/bin/env python3
"""CyberGuard v3 — admission gate for synthetic teacher trails (§3).

Reuses the repo's existing near-duplicate primitives rather than reimplementing
them: `cyberguard_data.shingles(text, k)` and `cyberguard_data.jaccard`.

Gate definition (as specified in PLAN-V3 §3/§4):
  * **13-gram Jaccard** between each trail row (prompt and trail text, checked
    separately) and every held-out benchmark item.
  * **Verbatim-span containment**: the longest run of consecutive 13-grams of the
    row that also occurs in a held-out item, expressed in tokens.
A row is a HIT if Jaccard >= --threshold (default 0.80) or containment >= 13
tokens on either field. Hits are excluded from admission and the receipt records
which ids were excluded and why. Nothing is modified in place.

Held-out sets: CyberMetric-500 (500 Q) + SecQA test (110 Q) from pubbench/.

Usage:
  admission_gate.py [--threshold 0.80] [--limit N] [--receipt PATH]
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import cyberguard_data as cgdata  # noqa: E402  (repo primitive: shingles/jaccard)

BASE = os.path.expanduser("~/AgentHub/cyberguard/data/v3/trails-30")
TRAILS = os.path.join(BASE, "trails_deepseek_7k.jsonl")
PUB = os.path.join(REPO, "pubbench")
K = 13


def load_heldout():
    items = []
    cm = json.load(open(os.path.join(PUB, "cybermetric-500.json")))
    for q in cm["questions"]:
        items.append(("cybermetric-500", q.get("question", "")))
    with open(os.path.join(PUB, "secqa_test.csv")) as f:
        rows = list(csv.reader(f))
    for r in rows[1:]:
        if r:
            items.append(("secqa", r[0]))
    return items


def ordered_shingles(text, k=K):
    """Content tokens in order (stopwords stripped, like cgdata.shingles)."""
    import re
    stop = {"the", "a", "an", "of", "to", "and", "or", "in", "on", "for", "with", "is", "are",
            "how", "what", "would", "you", "your", "be", "that", "this", "it", "as", "at", "by"}
    w = [t for t in re.findall(r"[a-z]+", (text or "").lower()) if t not in stop]
    if len(w) < k:
        return w, []
    return w, [" ".join(w[i:i + k]) for i in range(len(w) - k + 1)]


def longest_run(shingles_list, target_set):
    """Longest run of consecutive shingles all present in target_set."""
    best = cur = 0
    for sh in shingles_list:
        if sh in target_set:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best + (K - 1) if best else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.80)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--receipt", default=os.path.join(BASE, "ADMISSION-GATE-RECEIPT.json"))
    args = ap.parse_args()

    held = load_heldout()
    print("held-out items: %d (cybermetric-500 + secqa)" % len(held))
    hl_sets, index = [], defaultdict(list)
    for i, (src, q) in enumerate(held):
        s = cgdata.shingles(q, k=K)
        hl_sets.append(s)
        for sh in s:
            index[sh].append(i)

    rows = 0
    hits = []
    worst = []
    checked = 0
    with open(TRAILS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows += 1
            if args.limit and rows > args.limit:
                break
            d = json.loads(line)
            checked += 1
            row_best = 0.0
            row_hit = None
            for field in ("prompt", "trail"):
                text = d.get(field) or ""
                _, sh_list = ordered_shingles(text)
                if not sh_list:
                    continue
                sh_set = set(sh_list)
                cand = defaultdict(int)
                for sh in sh_set:
                    for j in index.get(sh, ()):
                        cand[j] += 1
                for j, shared in cand.items():
                    if shared < 2 and len(sh_set) > 4:
                        continue
                    js = cgdata.jaccard(sh_set, hl_sets[j])
                    run = longest_run(sh_list, hl_sets[j])
                    if js > row_best:
                        row_best = js
                    if (js >= args.threshold or run >= K) and row_hit is None:
                        row_hit = {"field": field, "heldout": held[j][0],
                                   "jaccard": round(js, 4), "verbatim_tokens": run}
                worst.append(row_best)
            if row_hit:
                hits.append({"id": d["id"], **row_hit})

    worst.sort()
    n = len(worst)
    summary = {
        "trail_file": TRAILS,
        "rows_checked": checked,
        "heldout_items": len(held),
        "ngram_k": K,
        "jaccard_threshold": args.threshold,
        "hits": len(hits),
        "hit_ids": [h["id"] for h in hits],
        "hit_detail": hits[:50],
        "jaccard_max": round(worst[-1], 4) if n else 0.0,
        "jaccard_p99": round(worst[int(n * 0.99)], 4) if n else 0.0,
        "jaccard_median": round(worst[n // 2], 4) if n else 0.0,
        "verdict": "PASS (no hits)" if not hits else "HITS — exclude and re-run",
    }
    with open(args.receipt, "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print(json.dumps(summary, indent=2))
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
