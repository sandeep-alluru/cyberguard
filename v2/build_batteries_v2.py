#!/usr/bin/env python3
"""build_batteries_v2.py — freeze the two prompt sets the battery inventory marked AUTHOR.

  G-C  >=300 ID-eliciting prompts WITH ground-truth identifiers, so hallucination is measurable.
       Derived from the NVD/ATT&CK answers in the mixture, which lead with their identifier: the description
       becomes the prompt and the stripped identifier is the answer key. This is derivation, not authoring of
       new content, and it yields a *validated* battery rather than one scored by a second model.
  G-J  100 benign general-instruction prompts, sampled deterministically from the 600 real turn pairs
       (v2/candidates/ultrachat-pairs.jsonl), which is the only genuine chat source in the repository.

Both are frozen with a receipt (count + sha256) so C24 and any later comparison use identical prompts
(SPEC line 462: "prespecified n AND a frozen probe set").

Usage: python3 v2/build_batteries_v2.py
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys

ARMS = "v2/data/mixture/armA.jsonl"
CHAT = "v2/candidates/ultrachat-pairs.jsonl"
ID_RE = re.compile(r"\b(CVE-\d{4}-\d{4,7}|T\d{4}(?:\.\d{3})?)\b")


def freeze(path, rows, extra, receipt_path):
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    rec = {"rows": len(rows), "sha256": digest, "seed": 0, **extra}
    json.dump(rec, open(receipt_path, "w"), indent=2)
    print(f"  froze {len(rows):>4} -> {path}  sha256 {digest[:24]}…")
    return rec


def main() -> int:
    # ---- G-C: prompts that ask for an identifier, with the identifier as ground truth
    seen, gC = set(), []
    for line in open(ARMS):
        r = json.loads(line)
        if r.get("src") not in ("nvd", "attack"):
            continue
        ans = str(r.get("assistant") or "").strip()
        m = ID_RE.search(ans)
        if not m:
            continue
        ident = m.group(1)
        # the answer should LEAD with the identifier; use what follows as the description to be identified
        desc = ans[m.end():].strip(" :-,.")
        if len(desc) < 80 or ident in seen:
            continue
        seen.add(ident)
        gC.append({"probe_id": f"gC:{ident}", "expected": ident,
                   "prompt": ("An advisory describes the following issue. Give the one identifier "
                              "(CVE or ATT&CK technique id) that matches it, then one sentence of detail.\n\n"
                              + desc[:900])})
        if len(gC) >= 300:
            break
    if len(gC) < 300:
        print(f"  WARNING: only {len(gC)} ID-eliciting prompts derivable (SPEC wants >=300)")

    # ---- G-J: 100 benign general-instruction prompts
    gJ = []
    if os.path.exists(CHAT):
        rows = [json.loads(l) for l in open(CHAT)]
        rng = random.Random(0)
        # prefer plainly benign, general prompts: no offensive markers, short and self-contained
        bad = re.compile(r"(?i)\b(exploit|malware|payload|attack|hack|bypass|inject|ransomware|phish)\b")
        pool = [r for r in rows if r.get("user") and not bad.search(r["user"]) and 30 <= len(r["user"]) <= 400]
        rng.shuffle(pool)
        for r in pool[:100]:
            gJ.append({"probe_id": f"gJ:{len(gJ)}", "prompt": r["user"]})
    if len(gJ) < 100:
        print(f"  WARNING: only {len(gJ)} benign chat prompts available (SPEC wants 100)")

    freeze("v2/data/probe-set-gC.jsonl", gC,
           {"gate": "G-C id factuality", "kind": "id-eliciting",
            "source": ARMS, "note": "derived: identifier stripped from the NVD/ATT&CK answer becomes ground truth"},
           "v2/data/probe-set-gC.receipt.json")
    freeze("v2/data/probe-set-gJ.jsonl", gJ,
           {"gate": "G-J chat retention", "kind": "benign general instruction",
            "source": CHAT, "note": "deterministic sample of real user turns, offensive markers excluded"},
           "v2/data/probe-set-gJ.receipt.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
