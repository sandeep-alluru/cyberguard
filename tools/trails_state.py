#!/usr/bin/env python3
"""Print a compact, factual snapshot of CyberGuard v3 live state.

Used to build the "live measured state" block of every Codex-Astra review prompt
so the reviewer is judging the plan against measured reality, not against the
plan's own claims.
"""
import json
import os
import re
import subprocess

BASE = os.path.expanduser("~/AgentHub/cyberguard/data/v3/trails-30")
SFT = os.path.expanduser("~/AgentHub/cyberguard/data/v3/sft")
ID_RE = re.compile(rb'"id"\s*:\s*"([^"]+)"')
MARK = b"</think>"


def trail_state(path):
    if not os.path.exists(path):
        return {"records": 0, "unique": 0, "duplicates": 0, "missing_marker": 0}
    total = unique = marker = 0
    seen = set()
    with open(path, "rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            m = ID_RE.search(line)
            if m:
                seen.add(m.group(1))
            if MARK in line:
                marker += 1
    unique = len(seen)
    return {"records": total, "unique": unique, "duplicates": total - unique,
            "missing_marker": unique - marker}


def count_lines(path):
    if not os.path.exists(path):
        return None
    n = 0
    with open(path, "rb") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def live_processes():
    try:
        out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    except Exception:
        return {"writers": [], "supervisor": False}
    writers = []
    for line in out.splitlines():
        if "gen_deepseek_7k_api.py" in line or "gen_muse_direct.py" in line:
            if "grep" in line or "prockill" in line:
                continue
            writers.append(line.strip()[:110])
    return {"writers": writers,
            "supervisor": any("cgv3sup/supervise.py" in l for l in out.splitlines())}


def main():
    ds = trail_state(os.path.join(BASE, "trails_deepseek_7k.jsonl"))
    mu = trail_state(os.path.join(BASE, "trails_muse_7k.jsonl"))
    proc = live_processes()
    print("### Live measured state")
    print("- deepseek trails: %d unique ids (records %d, duplicates %d, missing `</think>` %d) / 7000 target"
          % (ds["unique"], ds["records"], ds["duplicates"], ds["missing_marker"]))
    print("- muse trails:     %d unique ids (records %d, duplicates %d, missing `</think>` %d) / 7000 target"
          % (mu["unique"], mu["records"], mu["duplicates"], mu["missing_marker"]))
    print("- combined teacher trails available: %d (aim: 14000)" % (ds["unique"] + mu["unique"]))
    print("- live generator processes: %d %s" % (len(proc["writers"]), proc["writers"] or "(none)"))
    print("- single-writer supervisor running: %s" % proc["supervisor"])
    for f in ("fenrir.jsonl", "merged.jsonl", "primus.jsonl"):
        print("- sft/%s rows: %s" % (f, count_lines(os.path.join(SFT, f))))
    vr = os.path.expanduser("~/AgentHub/cyberguard/data/v3/trails-30/VALIDATION-REPORT.md")
    print("- VALIDATION-REPORT.md present: %s" % os.path.exists(vr))
    plan = os.path.expanduser("~/AgentHub/cyberguard/docs/PLAN-V3.md")
    if os.path.exists(plan):
        import hashlib
        h = hashlib.md5(open(plan, "rb").read()).hexdigest()
        lines = sum(1 for _ in open(plan))
        print("- PLAN-V3.md: md5 %s, %d lines" % (h, lines))


if __name__ == "__main__":
    main()
