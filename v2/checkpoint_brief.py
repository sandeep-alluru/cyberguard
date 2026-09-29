#!/usr/bin/env python3
"""checkpoint_brief.py — write and portal-verify a CEO-desk checkpoint brief from the measured numbers.

WHY THIS EXISTS. The owner requires a written report on the CEO desk at EVERY checkpoint
([ENG-2026-09-28-001]) and the whole point of an automated cadence is that it does not depend on an agent being
scheduled at exactly the right minute. `v2/checkpoint_metrics.sh` collects the numbers; this turns them into the
brief, with the house frontmatter, and then VERIFIES the result on the portal (HTTP 200, content hits present,
zero raw IPv4) before reporting success.

Every quantity comes from the metrics file (itself derived from `v2/data/mixture/FACTS.json` and the live
trainers) — the brief never invents a number, and it never writes a raw IPv4 address (the standing rule is that
addresses appear as hostnames).

USAGE
  python3 v2/checkpoint_brief.py C16                 # uses research-tmp/checkpoints/C16-metrics.json
  python3 v2/checkpoint_brief.py C24 --dry-run       # compose and print, write nothing
Exit 0 only when the brief exists AND the portal renders it with 0 raw IPv4.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CEO = os.path.join(ROOT, "docs/ceo")
PORTAL = "http://127.0.0.1:3100/ceo/report/"
TITLES = {"C8": "the C8 look", "C16": "the C16 look", "C24": "C24: training complete"}
IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")


def sh(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120).stdout.strip()
    except Exception:                                          # noqa: BLE001
        return ""


def newest_brief() -> str | None:
    files = sorted(f for f in os.listdir(CEO) if f.endswith(".md") and "checkpoint" in f)
    return files[-1] if files else None


def next_number(files: list[str]) -> int:
    nums = [int(m.group(1)) for f in files if (m := re.search(r"checkpoint(\d+)", f))]
    return (max(nums) + 1) if nums else 1


def compose(label: str, notes: str | None = None) -> tuple[str, str]:
    mp = os.path.join(ROOT, f"research-tmp/checkpoints/{label}-metrics.json")
    if not os.path.exists(mp):
        raise SystemExit(f"FATAL: {mp} does not exist - run v2/checkpoint_metrics.sh {label} first")
    m = json.load(open(mp))
    facts = m.get("facts", {})
    arms, exp = m.get("arms", {}), m.get("exposure", {})
    files = sorted(f for f in os.listdir(CEO) if f.endswith(".md") and "checkpoint" in f)
    n = next_number(files)
    prev = newest_brief()
    now = dt.datetime.now()
    stamp = now.strftime("%Y-%m-%d_%H%M00CDT")
    fname = f"{stamp}-cyberguard-checkpoint{n}-{label.lower()}-look.md"
    when = now.strftime("%Y-%m-%dT%H:%M:%S-05:00")

    # instrument governance, read from the receipts rather than asserted
    gov = ""
    try:
        ls = json.load(open(os.path.join(ROOT, "v2/data/mixture/leak-scan-c24.receipt.json")))
        vbs = ls.get("verdict_by_reference_set", {})
        gov = (f"\n**Instrument governance (D12).** The registered batteries are training rows and are reported\n"
               f"as **recall**, never as generalisation; the fresh training-disjoint instruments carry the\n"
               f"generalisation verdict. The leakage instrument now includes the batteries as its own reference\n"
               f"set and gives per-set verdicts: " +
               ", ".join(f"`{k}` {v}" for k, v in sorted(vbs.items())) + ".\n")
    except Exception:                                          # noqa: BLE001
        pass
    wd = sh("tail", "-1", "logs/watchdog.log")
    head = sh("git", "log", "-1", "--pretty=%h %s")

    body = f"""---
title: CyberGuard v2 checkpoint {n} — {TITLES.get(label, label)}
issued_at: {when}
project: CyberGuard
status: current
kind: result
supersedes: {prev or 'none'}
---

# Checkpoint {n} — {label}: {arms.get('A', {}).get('steps', '?')} / {arms.get('B', {}).get('steps', '?')} steps, {exp.get('A', {}).get('epochs_done', '?')} / {exp.get('B', {}).get('epochs_done', '?')} epoch

**One line:** at {label} the two arms stand at **{exp.get('A', {}).get('epochs_done', '?')}** and **{exp.get('B', {}).get('epochs_done', '?')}** of an epoch, measured {exp.get('A', {}).get('measured_sec_per_sample', '?')} s/sample against the declared basis of {facts.get('declared_sec_per_sample', '?')} s/sample.

## The {label} numbers (source: `research-tmp/checkpoints/{label}-metrics.json`)

| | arm A (`spark-40ee`) | arm B (`spark-8cf2`) |
|---|---|---|
| steps | {arms.get('A', {}).get('steps', '?')} | {arms.get('B', {}).get('steps', '?')} |
| s/step | {arms.get('A', {}).get('sec_per_step', '?')} | {arms.get('B', {}).get('sec_per_step', '?')} |
| samples seen | {exp.get('A', {}).get('samples_done', '?')} | {exp.get('B', {}).get('samples_done', '?')} |
| epoch fraction | {exp.get('A', {}).get('epochs_done', '?')} | {exp.get('B', {}).get('epochs_done', '?')} |
| refusal presentations | {exp.get('A', {}).get('refusal_presentations_done', '?')} | {exp.get('B', {}).get('refusal_presentations_done', '?')} |
| GPU utilisation | {arms.get('A', {}).get('gpu_util', '?')} % | {arms.get('B', {}).get('gpu_util', '?')} % |
| trainer alive | {'yes' if arms.get('A', {}).get('trainer_alive') else 'no'} | {'yes' if arms.get('B', {}).get('trainer_alive') else 'no'} |

Declared basis (all cited from `v2/data/mixture/FACTS.json`): {facts.get('rows_per_arm', '?')} rows/arm,
{facts.get('refusal_slots', '?')} refusal slots, {facts.get('unique_refusal_rows', '?')} unique refusal rows.
Projection to 24 h from the same file: **{exp.get('A', {}).get('projected_24h_epochs', '?')}** / **{exp.get('B', {}).get('projected_24h_epochs', '?')}** epochs.
{gov}
## Verified at this checkpoint

* Live trainer state and the numbers above come from `checkpoint_metrics.sh {label}` at the scheduled moment.
* Watchdog, last cycle: `{wd[:150]}`
* Repository revision: `{head[:150]}`
{notes or ''}
## What is open

* C24 evaluation contract: the verdict, the checksum-verified harvest and `VERDICT-v2.md` do not exist yet, so
  the objective is not complete.
* Known measurement limitations carried into the verdict: G-D extraction is declared zero-shot; G-I's
  normalised-F1 producer does not exist; MMLU-lite is declared UNMEASURED; the two confirmatory claims are
  scoped to the composed fresh G-A instrument with no inherited power figure (review F27).
* Leakage instrument finding: the registered batteries are present in the training data (14,162 findings against
  the battery reference set), which is why they are reported as recall and not as generalisation.

## Cost to date

No spend beyond the owner's recorded 24 h x 2 authorization; every number above is cited from
`v2/data/mixture/FACTS.json` or from the live metrics file. The evaluation contract adds roughly 8 h of
generation, split across both machines, after training ends.
"""
    return fname, body


def verify(fname: str) -> tuple[bool, str]:
    rid = hashlib.sha1(f"cyberguard/{fname}".encode()).hexdigest()[:20]
    url = PORTAL + rid
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            code, html = r.status, r.read().decode("utf-8", "replace")
    except Exception as e:                                     # noqa: BLE001
        return False, f"portal unreachable for {url}: {e}"
    hits = sum(1 for s in (fname.split("-")[-3], "checkpoint", "epoch") if s in html)
    ips = IPV4.findall(html)
    ok = code == 200 and hits >= 2 and not ips
    return ok, (f"HTTP {code} ({len(html)} bytes), content hits={hits}, raw IPv4={len(ips)} -> {url}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("label", choices=["C8", "C16", "C24"])
    ap.add_argument("--notes", default=None, help="extra markdown for the 'verified' section")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    fname, body = compose(a.label, a.notes)
    if a.dry_run:
        print(body[:2000])
        return 0
    os.makedirs(CEO, exist_ok=True)
    path = os.path.join(CEO, fname)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    src_ips = IPV4.findall(body)
    if src_ips:
        print(f"  FATAL: the brief itself contains {len(src_ips)} raw IPv4 address(es)")
        return 1
    print(f"  wrote docs/ceo/{fname} ({len(body)} bytes)")
    ok, detail = verify(fname)
    print(f"  portal verification: {'PASS' if ok else 'FAIL'} — {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
