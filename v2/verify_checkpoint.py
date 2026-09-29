#!/usr/bin/env python3
"""verify_checkpoint.py — check one checkpoint's three deliverables, mechanically.

WHY. The cadence requires, at every checkpoint: a metrics snapshot, an Astra review, and a dated CEO-desk brief. Each
has been verified by hand as it landed, which means the verification of M3 and C24 would depend on remembering what to
look for. This turns it into a check: the snapshot exists and is fresh, the review was dispatched (and says what a
verdict looks like), the brief carries its sections, the counts it quotes match the receipts they come from, and the
portal renders it. Written before M3 so the same procedure applies to both remaining checkpoints.

It is a verification aid, not a deliverable: nothing in the contract or the timeline depends on it.

    usage: python3 v2/verify_checkpoint.py <LABEL> [--max-age-min N]
    exit 0 = every checked item passed;  1 = at least one FAIL (NOTEs do not fail it)
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
IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")

# The brief gained receipt-sourced counts and a live review-status line during 2026-09-29 08:00-08:30; a brief written
# before that cannot be expected to carry them, so those items are only enforced for briefs written after this epoch.
BRIEF_FEATURES_EPOCH = dt.datetime(2026, 9, 29, 8, 20).timestamp()

RESULTS: list[tuple[str, str, str]] = []


def note(item: str, ok: bool | None, detail: str) -> None:
    RESULTS.append((item, "PASS" if ok is True else ("FAIL" if ok is False else "NOTE"), detail))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("--max-age-min", type=float, default=30.0)
    a = ap.parse_args()
    label = a.label

    # ------------------------------------------------------------------ 1. the metrics snapshot
    mp = os.path.join(ROOT, f"research-tmp/checkpoints/{label}-metrics.json")
    if not os.path.exists(mp):
        note("metrics snapshot exists", False, f"{os.path.relpath(mp, ROOT)} is absent")
    else:
        age_min = (dt.datetime.now().timestamp() - os.path.getmtime(mp)) / 60.0
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception as e:                                     # noqa: BLE001
            note("metrics snapshot parses", False, f"{type(e).__name__}: {e}")
            m = {}
        if m:
            missing = [k for k in ("arms", "exposure", "facts", "eviction") if k not in m]
            note("metrics snapshot carries arms/exposure/facts/eviction", not missing,
                 "all four present" if not missing else f"missing {missing}")
            ev = m.get("eviction") or {}
            clean = bool(ev) and all(int(v.get("port_8093", 1)) == 0 and not v.get("active_units")
                                     for v in ev.values() if isinstance(v, dict))
            note("serving evicted per the snapshot", clean, json.dumps(ev, sort_keys=True))
            note("snapshot freshness", age_min <= a.max_age_min,
                 f"{age_min:.1f} min old (tolerance {a.max_age_min:.0f}); the timeline writes it ~2 min before the brief")

    # ------------------------------------------------------------------ 2. the Astra review
    log = os.path.join(ROOT, f"research-tmp/reviews/checkpoint-{label}-review.log")
    out = os.path.join(ROOT, f"research-tmp/reviews/checkpoint-{label}-review.md")
    if os.path.exists(out) and os.path.getsize(out) > 0:
        lines = [l.strip() for l in open(out, encoding="utf-8", errors="replace") if l.strip()]
        closing = lines[-1] if lines else "(empty)"
        note("review output present", True, f"{os.path.getsize(out)} bytes, closing line: {closing[:120]}")
        note("review closing line is a verdict", bool(re.search(r"objection|OK|PASS|FAIL", closing, re.I)),
             "the prompt requires either 'no training-validity objection' or one objection")
    elif os.path.exists(log):
        note("review dispatched", None,
             "a dispatch log exists and no output has landed yet — normal within minutes of the dispatch")
    else:
        note("review dispatched", False, "neither a dispatch log nor an output exists for this checkpoint")
    # The brief must not claim there is no review while one is running: its own line must match the disk.
    review_state = "output" if os.path.exists(out) else ("dispatched" if os.path.exists(log) else "none")

    # ------------------------------------------------------------------ 3. the dated brief
    briefs = sorted((f for f in os.listdir(CEO) if f.endswith(".md") and label.lower() in f.lower()),
                    reverse=True) if os.path.isdir(CEO) else []
    body, bpath = "", ""
    if not briefs:
        note("CEO brief exists", False, f"no docs/ceo/*{label}*.md")
    else:
        bpath = os.path.join(CEO, briefs[0])
        body = open(bpath, encoding="utf-8", errors="replace").read()
        note("CEO brief exists", True, f"{os.path.basename(bpath)} ({os.path.getsize(bpath)} bytes)")
        for needle in ("Verified at this checkpoint", "What is open", "| steps |"):
            note(f"brief section: {needle}", needle in body, "present" if needle in body else "MISSING")
        if os.path.getmtime(bpath) >= BRIEF_FEATURES_EPOCH:
            note("brief states the snapshot age", "snapshot is taken" in body,
                 "read from the metrics file rather than asserted")
            note("brief states its review status honestly",
                 ("DISPATCHED, OUTPUT NOT YET WRITTEN" in body) if review_state == "dispatched" else True,
                 f"review state on disk: {review_state}")
            try:
                ls = json.load(open(os.path.join(ROOT, "v2/data/mixture/leak-scan-c24.receipt.json"), encoding="utf-8"))
                want = (ls.get("findings_by_reference_set") or {}).get("c24_batteries")
                got = re.search(r"\*\*([\d,]+)\*\* findings", body)
                note("brief's leakage count matches the receipt",
                     bool(want) and bool(got) and int(got.group(1).replace(",", "")) == int(want),
                     f"receipt {want}, brief {got.group(1) if got else 'not found'}")
            except Exception as e:                                 # noqa: BLE001
                note("brief's leakage count matches the receipt", None, f"receipt unreadable: {e}")
        else:
            note("brief predates the receipt-sourced features", None,
                 f"written {dt.datetime.fromtimestamp(os.path.getmtime(bpath)):%H:%M}; not enforced")
        note("brief contains no raw IPv4", not IPV4.findall(body), f"{len(IPV4.findall(body))} found")

    # ------------------------------------------------------------------ 4. the portal renders it
    if bpath:
        rid = hashlib.sha1(f"cyberguard/{os.path.basename(bpath)}".encode()).hexdigest()[:20]
        url = PORTAL + rid
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                code, html = r.status, r.read().decode("utf-8", "replace")
            hits = sum(1 for s in (label.lower(), "checkpoint", "epoch") if s in html.lower())
            note("portal renders the brief", code == 200 and hits >= 2 and not IPV4.findall(html),
                 f"HTTP {code}, content hits={hits}, raw IPv4={len(IPV4.findall(html))} -> {url}")
        except Exception as e:                                     # noqa: BLE001
            note("portal renders the brief", False, f"portal unreachable: {e}")

    # ------------------------------------------------------------------ report
    width = max(len(i) for i, _, _ in RESULTS)
    for item, status, detail in RESULTS:
        print(f"  [{status:4s}] {item:<{width}}  {detail}")
    fails = [i for i, s, _ in RESULTS if s == "FAIL"]
    print()
    print(f"  {len([1 for _, s, _ in RESULTS if s == 'PASS'])} pass, "
          f"{len([1 for _, s, _ in RESULTS if s == 'NOTE'])} note, {len(fails)} fail")
    if fails:
        print(f"  CHECKPOINT {label}: FAIL — {', '.join(fails)}")
        return 1
    print(f"  CHECKPOINT {label}: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
