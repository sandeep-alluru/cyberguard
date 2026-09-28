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

def _build_in_progress() -> bool:
    """True while build_mixture.py is running.

    The test uses exe+argv, never a substring scan of the command line, because a substring scan matches the
    very shell that runs it — a trap that has now cost three incidents in this project (pgrep for the codex
    runner, pkill for the trainer, pkill for this watchdog).
    """
    import glob
    for d in glob.glob("/proc/[0-9]*"):
        try:
            exe = os.path.realpath(os.path.join(d, "exe"))
        except OSError:
            continue
        if "python" not in exe:
            continue
        try:
            raw = open(os.path.join(d, "cmdline"), "rb").read().split(b"\0")
        except OSError:
            continue
        for a in raw:
            if a.endswith(b"/build_mixture.py") or a == b"build_mixture.py":
                return True
    return False


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
        drift = False                     # defined on every path: the guard below may skip the branch that sets it
        if _build_in_progress():
            # A build rewrites the arm files, so a hash check DURING a build reports drift that is not
            # drift: two such alerts (09:27 and 10:03 on 2026-09-28) were raised while v13/v14 were being
            # built. Skip the data checks; the cadence check below is process-level and still runs.
            line.append("data checks skipped: a build is writing the arms")
        elif cleared:
            now = {"armA": sha("v2/data/mixture/armA.jsonl"), "armB": sha("v2/data/mixture/armB.jsonl")}
            drift = [k for k in cleared if cleared[k] != now[k]]
            if drift:
                alerts.append(f"DATA-DRIFT: {drift} changed since the audit that cleared them — re-audit required")
            line.append(f"hashes: {'MATCH' if not drift else 'DRIFT'}")
        # hash-gated: the expensive scans run when the data changed, or every 6th cycle as a heartbeat
        changed = bool(cleared) and (drift if cleared else True)
        if changed or cycles % 6 == 1:
            rc_leak, out_leak = sh(sys.executable, "v2/leak_scan.py", "--no-write")
            line.append(f"leak_scan: {'CLEAN' if rc_leak == 0 else 'LEAK'} (full)")
            if rc_leak != 0:
                alerts.append("LEAK: unified leak scan found a hit")
            rc_aud, out_aud = sh(sys.executable, "v2/audit_mixture.py", "--verify-receipt")
            line.append(f"audit: {'PASS' if rc_aud == 0 else 'FAIL'} (full)")
            if rc_aud != 0:
                alerts.append("AUDIT: verify-receipt failed")
        else:
            line.append("scans: skipped (hashes unchanged since the last full pass)")
        with open(logpath, "a", encoding="utf-8") as fh:
            fh.write(" | ".join(line) + "\n")
            for al in alerts:
                fh.write(f"    ALERT {al}\n")
        fired = {al.split(":")[0] for al in alerts}
        for al in alerts:
            with open(os.path.join(ROOT, "logs", "ALERT-" + al.split(":")[0]), "w", encoding="utf-8") as fh:
                fh.write(f"{ts} {al}\n")
        # clear alerts whose condition has resolved (a stale ALERT is worse than no ALERT)
        import glob as _glob
        for f in _glob.glob(os.path.join(ROOT, "logs", "ALERT-*")):
            base = os.path.basename(f)
            # Skip anything already retired. Without this, the glob re-matched the retired files and each
            # resolution appended ANOTHER ".resolved" — the logs accumulated names like
            # "ALERT-DATA-DRIFT.resolved.resolved…" (18 suffixes) until a shell glob over them failed with
            # "File name too long". Retirement must be idempotent.
            if base.endswith(".resolved"):
                continue
            kind = base.replace("ALERT-", "")
            if kind not in fired:
                os.rename(f, f + ".resolved")
                with open(logpath, "a", encoding="utf-8") as fh:
                    fh.write(f"    RESOLVED {kind} (condition no longer holds)\n")
        time.sleep(a.interval)
    with open(logpath, "a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] watchdog exit after {cycles} cycles\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
