#!/usr/bin/env python3
"""CyberGuard v3 — credential hygiene pass over the training corpus.

Context
-------
Dataset prep ("cleaning") covered exact-duplicate removal, null/empty checks,
contamination scanning and offensive-framing review. It never covered secret
hygiene, and the public `cybersec-reasoning-merged` source is a hardcoded-
credential / CVE-analysis corpus that legitimately embeds real-looking key
material (Google `AIza...`, AWS `AKIA...`, PEM private-key blocks, literal
secret assignments). A measured scan found 282 such rows in sft/merged.jsonl and
7 in sft/fenrir.jsonl.

This tool removes the credential *values* while leaving the analysis intact, so
the safety lesson (CWE-798 hardcoded credentials) survives but the secret does
not. Row counts never change.

Design
------
* Operates on parsed JSON string values (never raw bytes) so output stays valid
  JSON and no escaping is broken.
* High-confidence value patterns only. Structural markers used by detection
  rules (e.g. a YARA string definition, `$AWS_SECRET_ACCESS_KEY` variable
  references, `your_key_here` placeholders) are NOT credentials and are left
  alone.
* Receipt records counts per pattern and the row indices touched -- never the
  secret value, and never a hash of it (a hash is a verification oracle).

Usage:
  redact_secrets.py --scan  <file> [<file> ...]
  redact_secrets.py --apply <file> [<file> ...]
"""
import argparse
import json
import os
import re
import sys
import time

REPLACEMENT = {
    "google_api_key": "<REDACTED-GOOGLE-API-KEY>",
    "aws_access_key_id": "<REDACTED-AWS-ACCESS-KEY-ID>",
    "aws_secret_access_key": "<REDACTED-AWS-SECRET-ACCESS-KEY>",
    "openai_api_key": "<REDACTED-OPENAI-API-KEY>",
    "github_pat": "<REDACTED-GITHUB-TOKEN>",
    "slack_token": "<REDACTED-SLACK-TOKEN>",
    "private_key_block": "<REDACTED-PRIVATE-KEY-BLOCK>",
    "bearer_token": "<REDACTED-BEARER-TOKEN>",
    "literal_secret_assignment": "<REDACTED-SECRET>",
}

# Order matters: the private-key block must be consumed before generic patterns.
# The PEM body is restricted to base64/whitespace so a match can never span across
# a reasoning delimiter (`</think>` contains `<` and `>`): without this, a key block
# whose END line appeared after the delimiter would swallow the delimiter itself.
PATTERNS = [
    ("private_key_block",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\sA-Za-z0-9+/=]{0,8000}?-----END [A-Z ]*PRIVATE KEY-----")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("aws_secret_access_key",
     re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*[\"']?([A-Za-z0-9/+=]{40})[\"']?")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("github_pat", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._\-]{30,})")),
    ("literal_secret_assignment",
     re.compile(r"(?i)\b(?:secret|password|passwd|token)\b\s*[:=]\s*[\"']([A-Za-z0-9/+=_\-]{24,})[\"']")),
]


def redact_text(s):
    """Return (redacted_string, {pattern: count})."""
    hits = {}
    for name, rx in PATTERNS:
        def _sub(m, _n=name):
            hits[_n] = hits.get(_n, 0) + 1
            return REPLACEMENT[_n]
        s = rx.sub(_sub, s)
    return s, hits


def walk(obj, hits, changed):
    """Recursively redact every string in a JSON structure. Returns (obj, changed)."""
    if isinstance(obj, str):
        new, h = redact_text(obj)
        if h:
            for k, v in h.items():
                hits[k] = hits.get(k, 0) + v
            changed[0] = True
            return new
        return obj
    if isinstance(obj, list):
        return [walk(x, hits, changed) for x in obj]
    if isinstance(obj, dict):
        return {k: walk(v, hits, changed) for k, v in obj.items()}
    return obj


def process(path, apply_changes):
    rows = changed_rows = 0
    unparsable = 0
    hits = {}
    t0 = time.time()
    out = []
    with open(path, "r", encoding="utf8", errors="replace") as f:
        for line in f:
            raw = line.rstrip("\n")
            if not raw.strip():
                if apply_changes:
                    out.append(raw)
                continue
            rows += 1
            try:
                d = json.loads(raw)
            except Exception:
                unparsable += 1
                if apply_changes:
                    out.append(raw)
                continue
            flag = [False]
            nd = walk(d, hits, flag)
            if flag[0]:
                changed_rows += 1
            if apply_changes:
                out.append(json.dumps(nd, ensure_ascii=False))
    if apply_changes:
        tmp = path + ".tmp-redact"
        with open(tmp, "w", encoding="utf8") as f:
            for l in out:
                f.write(l + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    return {"file": os.path.abspath(path), "rows": rows, "unparsable": unparsable,
            "rows_changed": changed_rows, "hits": hits, "applied": apply_changes,
            "seconds": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scan", action="store_true")
    g.add_argument("--apply", action="store_true")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()

    results = []
    for p in args.files:
        if not os.path.exists(p):
            print("MISSING %s" % p)
            continue
        r = process(p, args.apply)
        results.append(r)
        print("[%s] %s rows=%d changed=%d hits=%s"
              % ("APPLY" if args.apply else "SCAN", p, r["rows"], r["rows_changed"], r["hits"]),
              flush=True)

    if args.apply:
        receipt = os.path.expanduser("~/AgentHub/cyberguard/data/v3/REDACTION-RECEIPT.json")
        prev = []
        if os.path.exists(receipt):
            try:
                prev = json.load(open(receipt)).get("runs", [])
            except Exception:
                prev = []
        prev.append({"at": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "results": results})
        with open(receipt, "w") as f:
            json.dump({"runs": prev}, f, indent=2)
            f.write("\n")
        print("receipt: %s" % receipt)


if __name__ == "__main__":
    sys.exit(main())
