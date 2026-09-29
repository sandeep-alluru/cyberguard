#!/usr/bin/env python3
"""Recompute v2/data/mixture/FACTS.json from the built arms. FACTS is the single source of truth for
every number quoted in SPEC-V2/PLAN-SEQUENCE, so it must be regenerated from the artifacts, never edited."""
import collections, hashlib, json, os, sys

D = "v2/data/mixture"
SEC_PER_SAMPLE = 0.968288          # v1 whole-run wall, measured while the flash-next pool was DOWN
UNIQUE = {"offensive-refusal": 700, "unknown-answer": 498}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load(arm):
    with open(os.path.join(D, arm)) as fh:
        return [json.loads(l) for l in fh]


a, b = load("armA.jsonl"), load("armB.jsonl")
n = len(a)
src = collections.Counter(r["src"] for r in a)
ref = collections.Counter(r.get("kind") for r in a if r["src"] == "refusal")
slots = sum(ref.values())
facts = {
    "epoch_rows_per_arm": n,
    "arm_sha256": {"armA.jsonl": sha(os.path.join(D, "armA.jsonl")),
                   "armB.jsonl": sha(os.path.join(D, "armB.jsonl"))},
    "source_breakdown": dict(sorted(src.items(), key=lambda kv: -kv[1])),
    "refusal_slots_by_kind": dict(sorted(ref.items())),
    "refusal_unique_by_kind": UNIQUE,
    "refusal_unique_rows": sum(UNIQUE.values()),
    "refusal_slots": slots,
    "refusal_share": round(slots / n, 5),
    "format_authored_rows": {"triage-one-word": 600, "structured-json": 300, "sigma-rule": 400},
    "epoch_hours": round(n * SEC_PER_SAMPLE / 3600, 1),
    "sec_per_sample": SEC_PER_SAMPLE,
    "checkpoints": {},
    "checkpoint_note": ("PROJECTIONS under proportional sampling at the measured 0.968288 s/sample; these are "
                        "not measured wall-clock exposure, and realised counts are receipted after the run."),
}
for hours in (8, 16, 24):
    pres = int(hours * 3600 / SEC_PER_SAMPLE)
    rp = int(pres * slots / n)
    facts["checkpoints"][f"{hours}h"] = {
        "presentations_projected": pres,
        "pct_of_epoch_projected": round(pres / n, 4),
        "refusal_presentations_projected": rp,
        "refusal_passes_per_unique_row_projected": round(rp / sum(UNIQUE.values()), 2),
    }
old = json.load(open(os.path.join(D, "FACTS.json"))) if os.path.exists(os.path.join(D, "FACTS.json")) else {}
# `training_window` records OBSERVED runtime facts — measured wall clock, the no-op-resume incident, and the
# GPU-hour accounting. None of it is derivable from the built mixture, so a refresh must CARRY IT FORWARD:
# regenerating from scratch silently deleted the only machine-readable record of a 6.02 GPU-hour incident that
# the verdict is required to cite from this file. Assert on the outcome, not on the intent.
PRESERVE = ("training_window",)
for _k in PRESERVE:
    if _k in old:
        facts[_k] = old[_k]
_dropped = [_k for _k in PRESERVE if _k in old and _k not in facts]
assert not _dropped, f"FACTS refresh would drop preserved section(s): {_dropped}"
json.dump(facts, open(os.path.join(D, "FACTS.json"), "w"), indent=2)
print(f"  FACTS refreshed: rows/arm {old.get('epoch_rows_per_arm')} -> {n}")
print(f"    refusal slots {slots} ({facts['refusal_share']:.4%} of epoch), unique {facts['refusal_unique_rows']}")
print(f"    epoch {facts['epoch_hours']} h; 24 h = {facts['checkpoints']['24h']['pct_of_epoch_projected']:.2%} of epoch, "
      f"{facts['checkpoints']['24h']['refusal_presentations_projected']} refusal presentations")
for k in ("armA.jsonl", "armB.jsonl"):
    print(f"    {k}: {facts['arm_sha256'][k][:16]}…")
