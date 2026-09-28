#!/usr/bin/env python3
"""sample_candidates.py — build the admission gate's candidate samples, reproducibly.

Every candidate the gate measures must be a *sample of real text* with its provenance recorded, not a
hand-typed row. This script is the only place samples are produced, so the gate report can always be
re-derived.

Sources handled here (network-dependent, all public):
  * NIST CSRC cybersecurity set  — HF datasets-server rows API (`ethanolivertroy/nist-cybersecurity-training`)
  * MITRE ATT&CK STIX           — the enterprise bundle from `mitre-attack/attack-stix-data`
  * Trendyol core               — a slice of the staged corpus (fetched separately from the train host)

Usage:
    python3 v2/sample_candidates.py --outdir v2/candidates [--nist-rows 1000]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse

NIST = "ethanolivertroy/nist-cybersecurity-training"
ROWS_API = "https://datasets-server.huggingface.co/rows"
ATTACK_URL = ("https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/"
              "enterprise-attack/enterprise-attack.json")


def curl_json(url: str, tries: int = 3) -> dict | None:
    for i in range(tries):
        try:
            out = subprocess.run(["curl", "-sL", "--max-time", "120", url],
                                 capture_output=True, check=True).stdout
            return json.loads(out)
        except Exception:                                    # noqa: BLE001
            time.sleep(2 + 2 * i)
    return None


def fetch_nist(outdir: str, want: int) -> dict:
    path = os.path.join(outdir, "nist-sample.jsonl")
    rows, offset, page = [], 0, 100
    while len(rows) < want:
        url = (f"{ROWS_API}?dataset={urllib.parse.quote(NIST)}&config=default&split=train"
               f"&offset={offset}&length={page}")
        d = curl_json(url)
        if not d or not d.get("rows"):
            break
        for r in d["rows"]:
            txt = r["row"].get("text") or ""
            meta = r["row"].get("metadata") or ""
            if txt:
                rows.append({"text": txt, "metadata": meta, "source": NIST,
                             "row_idx": r.get("row_idx")})
        offset += page
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"path": path, "rows": len(rows), "source": NIST,
            "license": "CC0-1.0 (dataset card)", "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def fetch_attack(outdir: str) -> dict:
    raw = os.path.join(outdir, "attack-stix.json")
    if not os.path.exists(raw) or os.path.getsize(raw) < 1_000_000:
        subprocess.run(["curl", "-sL", "--max-time", "600", ATTACK_URL, "-o", raw], check=True)
    bundle = json.load(open(raw, encoding="utf-8"))
    objs = bundle.get("objects", [])
    keep_types = {"attack-pattern", "intrusion-set", "malware", "tool", "course-of-action",
                  "x-mitre-tactic", "x-mitre-data-source", "vulnerability"}
    path = os.path.join(outdir, "attack-sample.jsonl")
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for o in objs:
            if o.get("type") not in keep_types:
                continue
            name = (o.get("name") or "").strip()
            desc = (o.get("description") or "").strip()
            if not (name or desc):
                continue
            fh.write(json.dumps({"text": f"{name}\n{desc}", "type": o.get("type"),
                                 "stix_id": o.get("id"), "source": "mitre-attack/attack-stix-data"},
                                ensure_ascii=False) + "\n")
            n += 1
    return {"path": path, "rows": n, "objects_in_bundle": len(objs),
            "source": "mitre-attack/attack-stix-data (enterprise-attack.json)",
            "license": "MITRE Terms of Use (copy-notice required)",
            "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="v2/candidates")
    ap.add_argument("--nist-rows", type=int, default=1000)
    ap.add_argument("--skip-attack", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    manifest = []
    nist = fetch_nist(args.outdir, args.nist_rows)
    manifest.append(nist)
    print(f"  NIST   : {nist['rows']} rows -> {nist['path']}")
    if not args.skip_attack:
        att = fetch_attack(args.outdir)
        manifest.append(att)
        print(f"  ATT&CK : {att['rows']} objects -> {att['path']}")

    mpath = os.path.join(args.outdir, "SAMPLES.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"  manifest -> {mpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
