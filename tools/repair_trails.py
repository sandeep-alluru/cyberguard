#!/usr/bin/env python3
"""CyberGuard v3 — repair pass for a teacher-trail file.

Why: two defect classes can survive a generation run --
  * a trail that came back without the `</think>` marker (~1% of DeepSeek rows),
  * rows from an older generator batch with tool_calls != 0.
Both are *droppable*: the generators are resume-safe and regenerate every id that
is absent from the output file. So repair is:

    drop the invalid records  ->  run the generator (it refills the gaps)  ->  dedupe

repeated for a bounded number of rounds. No generator source is modified, and no
record is ever invented: every surviving record is a real teacher output.

Missing ids (e.g. Muse refusals) are attempted the same way; deterministic
refusals simply never appear and are reported as residual.

Usage:
  repair_trails.py <deepseek|muse> [--rounds N] [--timeout SECONDS]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

BASE = os.path.expanduser("~/AgentHub/cyberguard/data/v3/trails-30")
SUP = os.path.join(BASE, "supervisor")
MARKER = "</think>"
TOTAL = 7000

TEACHERS = {
    "deepseek": {
        "out": os.path.join(BASE, "trails_deepseek_7k.jsonl"),
        "cmd": ["python3", "-u", os.path.join(BASE, "gen_deepseek_7k_api.py")],
    },
    "muse": {
        "out": os.path.join(BASE, "trails_muse_7k.jsonl"),
        "cmd": ["python3", os.path.join(BASE, "gen_muse_direct.py")],
    },
}


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def canonical_ids():
    ids = []
    with open(os.path.join(BASE, "prompts-7k.jsonl")) as f:
        for line in f:
            line = line.strip()
            if line:
                ids.append(json.loads(line)["id"])
    return ids


def analyse(path, canon):
    """Return (kept_records, bad_ids, stats). Dedupes by id, prefers valid rows."""
    best = {}
    order = []
    stats = {"records": 0, "unparsable": 0}
    with open(path, "rb") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            stats["records"] += 1
            try:
                d = json.loads(raw)
            except Exception:
                stats["unparsable"] += 1
                continue
            rid = d["id"]
            valid = (MARKER in (d.get("trail") or "")) and d.get("tool_calls") == 0
            score = (1 if valid else 0, len(d.get("trail") or ""))
            if rid not in best:
                best[rid] = (score, d, valid)
                order.append(rid)
            elif score > best[rid][0]:
                best[rid] = (score, d, valid)
    bad_set = {i for i in order if not best[i][2]}
    kept = [best[i][1] for i in order if i in canon and i not in bad_set]
    missing = [i for i in canon if i not in best]
    stats.update({"unique": len(order), "dropped_invalid": len(bad_set),
                  "missing": len(missing)})
    return kept, sorted(bad_set | set(missing)), stats


def write_records(path, records):
    tmp = path + ".tmp-repair"
    with open(tmp, "w") as f:
        for d in records:
            f.write(json.dumps(d) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def run_generator(cfg, timeout):
    log("running generator to refill gaps: %s" % " ".join(cfg["cmd"]))
    t0 = time.time()
    with open(os.path.join(SUP, "repair-generator.log"), "a") as lf:
        lf.write("\n=== repair run %s ===\n" % time.strftime("%F %T"))
        lf.flush()
        p = subprocess.Popen(cfg["cmd"], cwd=BASE, stdout=lf, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL)
        try:
            p.wait(timeout=timeout)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            p.kill()
            rc = "timeout"
    log("generator finished rc=%s in %.1f min" % (rc, (time.time() - t0) / 60))
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("teacher", choices=sorted(TEACHERS))
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=7200)
    args = ap.parse_args()

    cfg = TEACHERS[args.teacher]
    canon = canonical_ids()
    receipt = {"teacher": args.teacher, "file": cfg["out"], "rounds": []}

    for rnd in range(1, args.rounds + 1):
        kept, bad, stats = analyse(cfg["out"], canon)
        log("round %d: records=%d unique=%d invalid_or_missing=%d"
            % (rnd, stats["records"], stats["unique"], len(bad)))
        receipt["rounds"].append({"round": rnd, "bad_before": len(bad), **stats})
        if not bad:
            log("nothing to repair")
            break

        write_records(cfg["out"], kept)          # drop invalid rows -> they become pending
        run_generator(cfg, args.timeout)
        # dedupe whatever came back
        subprocess.run([sys.executable, os.path.join(SUP, "dedupe.py"), cfg["out"]],
                       capture_output=True, text=True)

    kept, bad, stats = analyse(cfg["out"], canon)
    receipt["final"] = {"unique": stats["unique"], "bad": len(bad),
                        "residual_invalid_or_missing": bad[:50],
                        "residual_count": len(bad)}
    with open(os.path.join(SUP, "repair-receipt-%s.json" % args.teacher), "w") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    log("FINAL %s: unique=%d residual=%d" % (args.teacher, stats["unique"], len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
