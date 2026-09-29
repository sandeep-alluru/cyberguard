#!/usr/bin/env python3
"""verify_resume_learning.py — prove an optimizer actually moved the adapter weights.

WHY THIS EXISTS
Codex review #14 (2026-09-29) accepted that the repaired resume is *trainable* (trainable params
66,060,288, whereas the frozen run reported 0) but refused to accept that it is *learning*:

    "Trainability restored is supported. Actual learning remains UNVERIFIED; a nonzero
     optimizer-applied adapter-weight change from the preserved parent settles whether updates
     occurred."

That is a decidable question, so this script decides it. It compares a candidate adapter against the
preserved parent adapter tensor by tensor and reports the delta. A candidate byte-identical to its parent
means no optimizer update was applied — the frozen-run failure mode — and this script exits 1 for it.

Two deliberate guards, because this is the exact defect class that burned 6.02 GPU-h:
  * --after  refuse to compare a candidate whose mtime predates the window under test, so a *stale*
             checkpoint left over from the previous run cannot be mistaken for evidence about this one.
  * --parent is required; there is no "compare against nothing" mode that could pass trivially.

Exit codes: 0 = weights changed (learning demonstrated); 1 = identical or missing (not demonstrated).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time


def _load(path: str):
    from safetensors import safe_open  # noqa: PLC0415

    out = {}
    with safe_open(path, framework="numpy") as f:
        for k in f.keys():
            out[k] = f.get_tensor(k)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", required=True, help="the adapter the run was initialised from")
    ap.add_argument("--candidate", required=True, help="the adapter to test (dir or .safetensors)")
    ap.add_argument("--after", type=float, default=0.0,
                    help="epoch seconds; refuse a candidate last modified before this")
    ap.add_argument("--out", default="", help="write a JSON receipt here")
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    def resolve(p: str) -> str:
        return p if p.endswith(".safetensors") else os.path.join(p, "adapter_model.safetensors")

    parent, cand = resolve(a.parent), resolve(a.candidate)
    for p in (parent, cand):
        if not os.path.exists(p):
            print(f"RESUME-LEARNING: FAIL — missing {p}")
            return 1

    if a.after and os.path.getmtime(cand) < a.after:
        age = time.time() - os.path.getmtime(cand)
        print(f"RESUME-LEARNING: FAIL — {cand} was last written {age/3600:.2f} h ago, before the window "
              f"under test ({time.strftime('%F %T', time.localtime(a.after))}). A stale checkpoint cannot "
              f"prove anything about this run.")
        return 1

    import numpy as np  # noqa: PLC0415

    P, C = _load(parent), _load(cand)
    missing = sorted(set(P) - set(C))
    extra = sorted(set(C) - set(P))
    if missing:
        print(f"RESUME-LEARNING: FAIL — candidate is missing {len(missing)} parent tensor(s): {missing[:3]}")
        return 1

    per_key, tot_sq, par_sq, changed = {}, 0.0, 0.0, 0
    for k in P:
        p, c = np.asarray(P[k], dtype=np.float64), np.asarray(C[k], dtype=np.float64)
        if p.shape != c.shape:
            print(f"RESUME-LEARNING: FAIL — shape mismatch on {k}: {p.shape} vs {c.shape}")
            return 1
        d = c - p
        n = float(np.sqrt((d * d).sum()))
        per_key[k] = n
        tot_sq += n * n
        par_sq += float((p * p).sum())
        if n > 0.0:
            changed += 1

    delta_norm = tot_sq ** 0.5
    parent_norm = par_sq ** 0.5
    top = sorted(per_key.items(), key=lambda kv: -kv[1])[:5]
    rel = delta_norm / parent_norm if parent_norm else float("inf")

    def sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()

    receipt = {
        "check": "resume-learning",
        "label": a.label,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "parent": parent, "parent_sha256": sha(parent), "parent_mtime": os.path.getmtime(parent),
        "candidate": cand, "candidate_sha256": sha(cand), "candidate_mtime": os.path.getmtime(cand),
        "tensors_total": len(P), "tensors_changed": changed,
        "delta_l2_norm": delta_norm, "parent_l2_norm": parent_norm,
        "delta_relative_to_parent": rel,
        "top5_delta_norm": {k: v for k, v in top},
        "extra_tensors": extra,
        "learning_demonstrated": bool(delta_norm > 0.0 and changed > 0),
    }
    if a.out:
        with open(a.out, "w") as f:
            json.dump(receipt, f, indent=2)
            f.write("\n")

    print(f"RESUME-LEARNING {a.label or ''}".rstrip())
    print(f"  parent    {parent} sha {receipt['parent_sha256'][:16]}")
    print(f"  candidate {cand} sha {receipt['candidate_sha256'][:16]}")
    print(f"  tensors   {changed}/{len(P)} changed | delta L2 {delta_norm:.6g} vs parent L2 {parent_norm:.6g} "
          f"({rel*100:.4g}% relative)")
    for k, v in top:
        print(f"    {k:<70} {v:.6g}")
    if not receipt["learning_demonstrated"]:
        print("  FAIL — candidate is indistinguishable from its parent: no optimizer update was applied. "
              "This is the frozen-resume failure mode, and a run in this state must not be evaluated.")
        return 1
    print("  PASS — weights moved; an optimizer update was applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
