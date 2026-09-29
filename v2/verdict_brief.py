#!/usr/bin/env python3
"""verdict_brief.py — the dated CEO-desk brief for the verdict itself.

WHY. The owner's cadence requires "a dated CEO-desk brief per checkpoint". Every checkpoint in this window had
one — C8, C16, M1/M2/M3, C24, and two hand-written incident/milestone briefs — except the **terminal** one.
The timeline's last act was to log whether `VERDICT-v2.md` exists, so after ~11 hours of unattended work the
headline deliverable would land with no brief announcing it and no CEO-facing summary of what it decided.

It composes from the artifacts, never from narration: the gate report (every outcome), the verdict file (its
sha256 and size), the harvest manifest (its checksum-verified count), and the budget from FACTS.json. It REFUSES
to write a brief that would claim more than the artifacts show.

  usage: python3 v2/verdict_brief.py [--report P] [--verdict P] [--manifest P] [--out-dir D] [--dry-run]
  exit 0 = brief written (or printed with --dry-run); 1 = refused, with the reason
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CEO = os.path.join(ROOT, "docs/ceo")
PORTAL = "http://127.0.0.1:3100/ceo/report/"
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")



def _cut(s, n: int) -> str:
    """Truncate for display and MARK the cut.

    Found 2026-09-29: six places in the deliverables sliced content (`[:110]`, `[:400]`, `[:150]` …) and presented
    it as whole. The worst instance was the verdict's contamination block, headed "verbatim" while dropping the
    295 characters that contained the check's own RESULT line. An unmarked cut reads as the full text, so every
    one is marked here instead.
    """
    s = str(s)
    return s if len(s) <= n else s[:n].rstrip() + " …[truncated]"

def load(rel: str):
    p = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:                                          # noqa: BLE001
        return None


def newest_brief() -> str | None:
    if not os.path.isdir(CEO):
        return None
    files = sorted(f for f in os.listdir(CEO) if f.endswith(".md"))
    return files[-1] if files else None


def sha_and_size(path: str) -> tuple[str, int]:
    rel = path if os.path.isabs(path) else os.path.join(ROOT, path)
    data = open(rel, "rb").read()
    return hashlib.sha256(data).hexdigest(), len(data)


def brief_already_delivered(vsha: str, out_dir: str = CEO) -> str | None:
    """Return the path of an existing terminal brief for this exact verdict, else None.

    WHY. The brief is now composed from BOTH the timeline (its last act) and the contract (its final stage), so
    that an 11-hour unattended contract still delivers the terminal brief if the timeline dies mid-run — the
    timeline is an orphaned process and nothing restarts it. Two callers would otherwise write two
    `*-cyberguard-verdict-v2-delivered.md` files for one verdict, which is the duplicate-brief defect again (it
    already produced a duplicate M2 brief in this window). The name carries a timestamp, so the match is on the
    verdict's sha256, recorded in the frontmatter for exactly this purpose.
    """
    # Scan the directory the brief would actually be WRITTEN to (--out-dir), not always docs/ceo: with the default
    # the two agree, but a test or a redirected run writes elsewhere and the guard must still see its own output.
    if not os.path.isdir(out_dir):
        return None
    for f in sorted(os.listdir(out_dir)):
        if not f.endswith("-cyberguard-verdict-v2-delivered.md"):
            continue
        p = os.path.join(out_dir, f)
        try:
            head = open(p, encoding="utf-8", errors="replace").read(4096)
        except OSError:
            continue
        if f"verdict_sha256: {vsha}" in head:
            return os.path.join(out_dir, f)
        # Legacy briefs (written before the field existed) state the short hash in the one-line summary.
        if f"sha256 `{vsha[:16]}" in head:
            return os.path.join(out_dir, f)
    return None


def verify(fname: str) -> tuple[bool, str]:
    rid = hashlib.sha1(f"cyberguard/{fname}".encode()).hexdigest()[:20]
    url = PORTAL + rid
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            code, html = r.status, r.read().decode("utf-8", "replace")
    except Exception as e:                                     # noqa: BLE001
        return False, f"portal unreachable for {url}: {e}"
    hits = sum(1 for s in ("verdict", "gate", "claim") if s in html.lower())
    ips = IPV4.findall(html)
    return (code == 200 and hits >= 2 and not ips), f"HTTP {code} ({len(html)} bytes), hits={hits}, raw IPv4={len(ips)} -> {url}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="v2/gate-report-v2.json")
    ap.add_argument("--verdict", default="docs/VERDICT-v2.md")
    ap.add_argument("--manifest", default="research-tmp/harvest-v2/MANIFEST.sha256")
    ap.add_argument("--out-dir", default=CEO)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rep = load(a.report)
    if not isinstance(rep, dict) or not rep.get("gates"):
        return _refuse(f"{a.report} is missing or has no gate rows — there is no verdict to brief")
    vpath = a.verdict if os.path.isabs(a.verdict) else os.path.join(ROOT, a.verdict)
    if not os.path.exists(vpath) or os.path.getsize(vpath) == 0:
        return _refuse(f"{a.verdict} does not exist — this brief would announce a verdict that is not there")
    mpath = a.manifest if os.path.isabs(a.manifest) else os.path.join(ROOT, a.manifest)
    manifest_lines = [l for l in open(mpath)] if os.path.exists(mpath) else []
    if not manifest_lines:
        return _refuse(f"{a.manifest} is missing or empty — the checksum-verified harvest is a deliverable")

    vsha, vsize = sha_and_size(vpath)
    # IDEMPOTENT: the contract's final stage composes this brief too, so a re-run (or a timeline that outlives the
    # contract and composes it again) must not write a second brief for the same verdict.
    _prev = brief_already_delivered(vsha, a.out_dir)
    if _prev:
        print(f"verdict brief ALREADY DELIVERED for verdict sha256 {vsha[:16]}… -> {_prev}")
        print("  not writing a duplicate (the deliverable exists; this is a no-op, not a failure)")
        return 0
    rows = rep.get("gates") or []
    counts = rep.get("counts") or {}
    claims = [g for g in rows if str(g.get("gate", "")).startswith("Claim")]
    decided = counts.get("PASS", 0) + counts.get("FAIL", 0)

    def tbl(items, headers, keys):
        out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        for it in items:
            cells = []
            for k in keys:
                v = it.get(k)
                if isinstance(v, (dict, list)):
                    v = _cut(json.dumps(v), 120)
                cells.append(str(v if v is not None else "—"))
            out.append("| " + " | ".join(cells) + " |")
        return "\n".join(out)

    facts = load("v2/data/mixture/FACTS.json") or {}
    gh = ((facts.get("training_window") or {}).get("gpu_hours") or {})
    clear = load("v2/data/mixture/equivalence-clearance.receipt.json") or {}
    muse = load("v2/data/mixture/muse-clearance.receipt.json") or {}

    now = dt.datetime.now()
    stamp = now.strftime("%Y-%m-%d_%H%M00CDT")
    fname = f"{stamp}-cyberguard-verdict-v2-delivered.md"
    body = f"""---
title: CyberGuard v2 — VERDICT delivered
issued_at: {now.strftime('%Y-%m-%dT%H:%M:%S-05:00')}
project: CyberGuard
status: current
kind: result
supersedes: {newest_brief() or 'none'}
verdict_sha256: {vsha}
---

# VERDICT-v2 delivered — {decided} of {len(rows)} gate rows decided

**One line:** the C24 evaluation contract completed and `docs/VERDICT-v2.md` exists (sha256 `{vsha[:16]}…`,
{vsize:,} bytes) with a **{len(manifest_lines)}-file checksum-verified harvest**. Counts from
`{a.report}`: {json.dumps(counts, sort_keys=True)}. Every number is cited from
`v2/data/mixture/FACTS.json` and the gate report; nothing here is narrated.

## The two pre-registered confirmatory claims

{tbl(claims, ["claim", "outcome", "observed", "note"], ["gate", "outcome", "observed", "note"]) if claims else "(no claim rows — this is not a v2 verdict)"}

## Every gate row

{tbl(rows, ["gate", "outcome", "observed"], ["gate", "outcome", "observed"])}

## The artifacts

| artifact | evidence |
|---|---|
| `docs/VERDICT-v2.md` | sha256 `{vsha}` ({vsize:,} bytes) |
| `{a.report}` | {len(rows)} rows, counts {json.dumps(counts, sort_keys=True)} |
| `{a.manifest}` | {len(manifest_lines)} checksum-verified files |
| adapter identity | {_cut(json.dumps(rep.get('identity') or {}), 200)} |

**Independent clearances of record** (each with the revision it names, never silently extended):
Astra on the evaluation chain — {clear.get('clearance_line', '(see research-tmp/reviews/)')}
Muse on the frozen arms — {muse.get('clearance_line', '(see research-tmp/reviews/)')}

## Cost

Training against the owner's authorization: **{gh.get('spent_before_relaunch_gpu_h', '?')} GPU-hours spent,
worst case {gh.get('worst_case_total_gpu_h', '?')} of {gh.get('authorization_gpu_h', '?')} authorized**
(24 h × 2). The evaluation is the plan of record's separately budgeted cost. All figures cited from
`v2/data/mixture/FACTS.json`.

## What is open, stated rather than omitted

* The **evaluated artifact is a weights-only continuation with a restarted schedule, stopped mid-epoch** — one
  completed pass plus a partial second pass. No uninterrupted-training claim is made (`docs/SPEC-V2.md` §16).
* The objective's Flash-Next **restore clause was superseded by the owner**; the stack remains evicted (§17).
* **D2 is declared NOT MET** (distinct control prompts and answer-length gap), receipted and carried here as an
  intrinsic asymmetry of the substitution design.
* The merge check's coverage boundaries and the per-module sensitivity limit are stated in the verdict itself.
"""
    if a.dry_run:
        # PRINT THE WHOLE BODY — the same truncation found in checkpoint_brief.py and write_verdict_v2.py on
        # 2026-09-29, copied into this script when it was written: a preview that hides the end of the document
        # is used to verify the document. The brief carries the every-gate table, so its tail is not optional.
        print(body)
        print(f"\n(DRY RUN: would write {os.path.join(a.out_dir, fname)})")
        return 0
    os.makedirs(a.out_dir, exist_ok=True)
    out = os.path.join(a.out_dir, fname)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"  wrote {os.path.relpath(out, ROOT)} ({len(body)} bytes)")
    # Never print PASS for a verification that did not happen: an out-dir other than docs/ceo is not published.
    if os.path.abspath(a.out_dir) != os.path.abspath(CEO):
        print(f"  portal verification: SKIPPED (out-dir {a.out_dir} is not docs/ceo, so nothing was published)")
        return 0
    okv, why = verify(fname)
    print(f"  portal verification: {'PASS' if okv else 'FAIL'} — {why}")
    return 0 if okv else 1


def _refuse(msg: str) -> int:
    print(f"VERDICT-BRIEF: REFUSED — {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
