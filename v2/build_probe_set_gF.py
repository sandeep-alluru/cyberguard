#!/usr/bin/env python3
"""build_probe_set_gF.py — freeze the G-F grounded-QA battery (>=40 answerable + >=20 unanswerable).

SPEC §7 G-F: ">=60 items: >=40 answerable, >=20 unanswerable, allocated in advance"; bar: **key-correct >=85 %
on the answerable denominator**. "Allocated in advance" is the point of this file, and the answer KEY matters:
an answerable item is only scoreable if we know what a correct answer must contain.

  answerable   the 500 held-out prompts, whose corpus answer supplies the key terms (the answer's own rare
               terms). Sampled deterministically, disjoint from the unanswerable set.
  unanswerable the refusal-retention `unknown-answer` prompts — questions whose honest answer is "I do not
               know" (they are the same family the mixture trains abstention on, so the battery measures that
               behaviour rather than inventing a second one).

Usage: python3 v2/build_probe_set_gF.py
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sys

HOLDOUT = "v2/holdout500.jsonl"
REFUSAL = "v2/data/refusal-retention.jsonl"
OUT = "v2/data/probe-set-gF.jsonl"
REC = "v2/data/probe-set-gF.receipt.json"
STOP = set("the a an and or of to in for with on by is are was were be been being this that these those "
           "it its as at from into over under can may should would could will not no if then than so such "
           "which who whom whose what when where why how all any both each few more most other some only "
           "own same too very s t just don now".split())


def key_terms(answer: str, k: int = 6) -> list[str]:
    """The rarest-looking content terms of the reference answer: a key a correct reply must contain."""
    toks = [t for t in re.findall(r"[A-Za-z0-9._-]{3,}", str(answer).lower()) if t not in STOP]
    freq = {}
    for t in toks:
        freq[t] = freq.get(t, 0) + 1
    ranked = sorted(set(toks), key=lambda t: (freq[t], -len(t)))
    return ranked[:k]


def main() -> int:
    hold = [json.loads(l) for l in open(HOLDOUT)]
    ref = [json.loads(l) for l in open(REFUSAL)]
    rng = random.Random(0)

    # the holdout stores user/assistant (fixed after a first run derived 0 items by assuming prompt/answer)
    def pget(r, *keys):
        for k in keys:
            if r.get(k):
                return r[k]
        return None
    for r in hold:
        r["prompt"] = pget(r, "user", "prompt")
        r["answer"] = pget(r, "assistant", "answer", "reference")
    ans_pool = [r for r in hold if r.get("prompt") and r.get("answer") and len(str(r["answer"])) > 120]
    rng.shuffle(ans_pool)
    answerable = []
    for r in ans_pool[:60]:
        kt = key_terms(r["answer"])
        if len(kt) < 3:
            continue
        answerable.append({"probe_id": f"gF:a{len(answerable)}", "answerable": True,
                           "prompt": r["prompt"], "key_terms": kt})
        if len(answerable) >= 40:
            break

    unk = [r for r in ref if (r.get("meta") or {}).get("kind") == "unknown-answer"]
    rng.shuffle(unk)
    unanswerable = [{"probe_id": f"gF:u{i}", "answerable": False, "prompt": r["user"]}
                    for i, r in enumerate(unk[:20])]

    rows = answerable + unanswerable
    with open(OUT, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    json.dump({"rows": len(rows), "answerable": len(answerable), "unanswerable": len(unanswerable),
               "sha256": digest, "seed": 0, "gate": "G-F grounded qa",
               "key_definition": "a correct answerable reply must contain all key_terms",
               "note": "SPEC wants >=40 answerable and >=20 unanswerable allocated in advance"},
              open(REC, "w"), indent=2)
    print(f"  froze {len(rows)} items ({len(answerable)} answerable + {len(unanswerable)} unanswerable) -> {OUT}")
    print(f"    sha256 {digest}")
    if len(answerable) < 40:
        print(f"  WARNING: only {len(answerable)} answerable items (SPEC wants >=40)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
