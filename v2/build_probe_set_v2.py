#!/usr/bin/env python3
"""build_probe_set_v2.py — freeze the G-A probe set (SPEC §7: "prespecified n AND a frozen probe set").

THE GAP THIS CLOSES. SPEC §7 pre-registers G-A at **n = 1,100 offensive probes**, and the C24 budget
(4,400 generations = 1,100 tuned per arm + a shared base per arm) assumes it. No such set existed: the only
frozen probe sets in the repository totalled 225 strings, and the largest offensive inventory in the corpus is
**700**. A gate whose n cannot be drawn cannot be measured, and discovering that at C24 would waste the
evaluation window.

THE COMPOSITION, and why it is a re-registration rather than a silent fix:
  * 700 **offensive-refusal** prompts — the entire authored offensive inventory, taken whole;
  * 400 of the 500 **unknown-answer** prompts, sampled deterministically (seed 0) — prompts where the correct
    behaviour is also non-compliance (an honest "I do not know" rather than an invented answer).
  Together 1,100, which preserves the pre-registered n and therefore the power arithmetic the SPEC quotes.
  What changes is the DESCRIPTION: G-A becomes a **non-compliance retention** gate (offensive refusal +
  documented abstention), not "offensive probes" alone. That is recorded as an owner-facing re-registration
  item (docs/PLAN-SEQUENCE.md D10) because it is a change to a pre-registered claim, not a repair.

The set is frozen to a file with a receipt (sha256) so that C8/C16/C24 and any later comparison use exactly
the same prompts — the SPEC's "probe-set substitution" rule (line 462).

Usage: python3 v2/build_probe_set_v2.py [--out v2/data/probe-set-gA.jsonl]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys

SRC = "v2/data/refusal-retention.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="v2/data/probe-set-gA.jsonl")
    ap.add_argument("--offensive", type=int, default=700)
    ap.add_argument("--abstention", type=int, default=400)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(SRC)]
    off, unk = [], []
    seen = set()
    for r in rows:
        kind = (r.get("meta") or {}).get("kind")
        key = " ".join(str(r.get("user", "")).lower().split())
        if key in seen:
            continue
        seen.add(key)
        (off if kind == "offensive-refusal" else unk if kind == "unknown-answer" else []).append(
            {"probe_id": f"{kind}:{len(off) if kind == 'offensive-refusal' else len(unk)}",
             "kind": kind, "prompt": r["user"]})

    if len(off) < a.offensive:
        sys.exit(f"FATAL: only {len(off)} offensive prompts exist, {a.offensive} required")
    if len(unk) < a.abstention:
        sys.exit(f"FATAL: only {len(unk)} abstention prompts exist, {a.abstention} required")

    rng = random.Random(0)
    sample = rng.sample(unk, a.abstention)
    probes = off[:a.offensive] + sample
    assert len(probes) == a.offensive + a.abstention == 1100, len(probes)

    with open(a.out, "w") as fh:
        for p in probes:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(open(a.out, "rb").read()).hexdigest()
    receipt = {"probes": len(probes), "offensive_refusal": a.offensive, "unknown_answer_abstention": a.abstention,
               "source": SRC, "seed": 0, "sha256": digest,
               "gate": "G-A non-compliance retention (SPEC §7 n=1100)",
               "note": "the SPEC words G-A as '1100 offensive probes'; only 700 offensive prompts exist, so the "
                       "remaining 400 are documented-abstention prompts and the gate is re-described as "
                       "non-compliance retention. Recorded as D10 for owner sign-off."}
    json.dump(receipt, open(a.out.replace(".jsonl", ".receipt.json"), "w"), indent=2)
    print(f"  froze {len(probes)} probes -> {a.out}")
    print(f"    {a.offensive} offensive-refusal + {a.abstention} unknown-answer (seed 0)")
    print(f"    sha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
