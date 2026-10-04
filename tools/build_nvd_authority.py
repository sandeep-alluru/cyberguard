#!/usr/bin/env python3
"""Build the cached NVD authority for the G-C probe set — one time, then reusable forever.

Why: PLAN §8.9's G-C gate requires **verified** emitted IDs (verified = emitted − unchecked), with a
support floor of ≥300. The battery (`v2/run_battery.py`) calls `score_ids(outputs, valid_tids,
deprecated_tids)` and never passes NVD sets, so `cap_scorers.factuality_score` marks **every** emitted
CVE "unchecked" and excludes it from the denominator. The probe set has 288 unique CVEs and 12 TIDs;
the only real G-C run on disk (`research-tmp/f15/battery-gC-armA.json`) reports exactly
`unchecked_cves=288` — i.e. **zero** CVEs were ever checked — leaving verified=112 and failing the
support floor. G-C was therefore unmeasurable, and the reason was authority wiring, not the
generation count.

This script resolves that with a one-time, resumable fetch at NVD's polite unkeyed rate (6.2 s between
requests; ~30 min for 288 CVEs, or ~3 min with an NVD_API_KEY). The result is a flat authority map that
the battery can load offline, so scoring stays deterministic and repeatable and never depends on the
network at scoring time. This is a reusable harness asset, not per-job machinery.

Usage:
  python3 tools/build_nvd_authority.py --probe-set v2/data/probe-set-gC.jsonl \
      --out v2/candidates/nvd-authority-gC.json [--api-key-env NVD_API_KEY] [--limit N]
Resumable: re-running skips CVEs already present in --out.
"""
import argparse
import json
import os
import re
import time
import urllib.request

URL = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId="


def probe_cves(path):
    out = set()
    for line in open(path, encoding="utf8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        e = json.loads(line).get("expected", "")
        if re.match(r"^CVE-\d{4}-\d+$", e):
            out.add(e)
    return sorted(out)


def fetch(cve, api_key=None, timeout=20):
    req = urllib.request.Request(URL + cve)
    if api_key:
        req.add_header("apiKey", api_key)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.loads(r.read())
    total = j.get("totalResults", 0)
    return {"checked": True, "exists": total > 0, "total": total}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-set", default="v2/data/probe-set-gC.jsonl")
    ap.add_argument("--out", default="v2/candidates/nvd-authority-gC.json")
    ap.add_argument("--api-key-env", default="NVD_API_KEY")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    key = os.environ.get(a.api_key_env) or None
    delay = 0.7 if key else 6.2          # NVD allows 50/30s keyed, ~5/30s unkeyed
    cves = probe_cves(a.probe_set)
    if a.limit:
        cves = cves[:a.limit]

    cache = {}
    if os.path.exists(a.out):
        cache = json.load(open(a.out)).get("cves", {})
    todo = [c for c in cves if c not in cache]
    print("probe CVEs: %d | already cached: %d | to fetch: %d | delay %.1fs (~%.1f min)"
          % (len(cves), len(cache), len(todo), delay, len(todo) * delay / 60), flush=True)

    t0 = time.time()
    for i, cve in enumerate(todo, 1):
        try:
            cache[cve] = fetch(cve, key)
        except Exception as e:                       # noqa: BLE001
            cache[cve] = {"checked": False, "exists": None, "error": type(e).__name__}
        if i % 25 == 0 or i == len(todo):
            ok = sum(1 for v in cache.values() if v.get("checked") and v.get("exists"))
            print("  %d/%d  ok=%d  elapsed %.1f min" % (i, len(todo), ok, (time.time() - t0) / 60), flush=True)
            # Write INCREMENTALLY: a kill must not discard ~30 minutes of polite fetching. Re-running
            # then resumes from what is already on disk. (Earlier in this project generators were killed
            # mid-run by an external actor, so at-risk work is checkpointed as it is produced.)
            _write(a.out, a.probe_set, cves, cache)
        time.sleep(delay)

    checked = [c for c, v in cache.items() if v.get("checked")]
    ok = [c for c, v in cache.items() if v.get("checked") and v.get("exists")]
    _write(a.out, a.probe_set, cves, cache)
    print("wrote %s | checked %d/%d | exist %d" % (a.out, len(checked), len(cves), len(ok)))


def _write(path, probe_set, cves, cache):
    checked = [c for c, v in cache.items() if v.get("checked")]
    ok = [c for c, v in cache.items() if v.get("checked") and v.get("exists")]
    bundle = {"source": "nvd-cve-2.0-api", "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "probe_set": probe_set, "n_probe_cves": len(cves),
              "n_checked": len(checked), "n_exists": len(ok),
              "coverage": round(len(checked) / len(cves), 4) if cves else None,
              "cves": cache}
    with open(path, "w") as fh:
        json.dump(bundle, fh, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
