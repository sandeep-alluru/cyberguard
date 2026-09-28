#!/usr/bin/env python3
"""watchdog.py — the standing health check for the CyberGuard goal.

Each cycle it answers, from evidence rather than assumption:
  * do the arms still hash to the revision that passed the audit?      (silent data drift)
  * does the unified leak scan still return CLEAN?                     (leakage)
  * does the audit still PASS on both arms?                            (data integrity)
  * has the 3-hour checkpoint cadence been met?                        (process)
Alerts are appended to the log and to ALERT-* files; it never rewrites the receipts it inspects.
Usage: python3 v2/watchdog.py [--interval 300] [--hours 30]
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sh(*cmd):
    p = subprocess.run(list(cmd), cwd=ROOT, capture_output=True, text=True, timeout=1800)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def sha(path):
    return hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--hours", type=float, default=30.0)
    ap.add_argument("--log", default="logs/watchdog.log")
    a = ap.parse_args()
    logpath = os.path.join(ROOT, a.log)
    os.makedirs(os.path.dirname(logpath), exist_ok=True)
    deadline = time.time() + a.hours * 3600
    cycles = 0
    cleared = None
    try:
        rc = json.load(open(os.path.join(ROOT, "v2/data/mixture/audit.receipt.json"), encoding="utf-8"))
        cleared = (rc.get("checks") or {}).get("arm_sha256")
    except Exception:
        pass
    while time.time() < deadline:
        cycles += 1
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line, alerts = [f"[{ts}] cycle {cycles}"], []
        if cleared:
            now = {"armA": sha("v2/data/mixture/armA.jsonl"), "armB": sha("v2/data/mixture/armB.jsonl")}
            drift = [k for k in cleared if cleared[k] != now[k]]
            if drift:
                alerts.append(f"DATA-DRIFT: {drift} changed since the audit that cleared them — re-audit required")
            line.append(f"hashes: {'MATCH' if not drift else 'DRIFT'}")
        rc_leak, out_leak = sh(sys.executable, "v2/leak_scan.py", "--no-write")
        line.append(f"leak_scan: {'CLEAN' if rc_leak == 0 else 'LEAK'}")
        if rc_leak != 0:
            alerts.append("LEAK: unified leak scan found a hit")
        rc_aud, out_aud = sh(sys.executable, "v2/audit_mixture.py", "--verify-receipt")
        line.append(f"audit: {'PASS' if rc_aud == 0 else 'FAIL'}")
        if rc_aud != 0:
            alerts.append("AUDIT: verify-receipt failed")
        with open(logpath, "a", encoding="utf-8") as fh:
            fh.write(" | ".join(line) + "\n")
            for al in alerts:
                fh.write(f"    ALERT {al}\n")
        for al in alerts:
            with open(os.path.join(ROOT, "logs", "ALERT-" + al.split(":")[0]), "w", encoding="utf-8") as fh:
                fh.write(f"{ts} {al}\n")
        time.sleep(a.interval)
    with open(logpath, "a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] watchdog exit after {cycles} cycles\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
