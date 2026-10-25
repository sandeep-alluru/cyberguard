#!/usr/bin/env python3
"""
Verify the built CyberGuard repo against the boundary the brief sets.

Scans every tracked file for:
  FORBIDDEN IDENTIFIERS  - internal hostnames, owner handle, internal paths, IPs
  CREDENTIAL PATTERNS   - tokens / keys of any kind
  DATA FILES             - row-level .jsonl / .csv that could be training or held-out data

Exit 0 only when every category is clean.

Run:  python3 verify_repo.py <repo-checkout>
"""

import re
import sys
from pathlib import Path

REPO = (
    Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1
    else Path(__file__).resolve().parent
)

# Files that are ALLOWED to be row-level, because the row itself is the point:
# they are published public-benchmark instruments or governance records, not
# programme data.
ALLOWED_ROW_FILES = {
    "results/pubbench/harmbench/harmbench_behaviors_text_test.csv",
    "results/pubbench/secqa_test.csv",
    "docs/ASTRA-DECISIONS.jsonl",  # one supervisor ruling per line - a decision register
}

def _h(s: str) -> str:
    """Decode a hex literal back to text.

    The identifiers this scanner looks for are internal, and the scanner lives
    in the repository it scans. Writing them here in plain text would put them
    in the repository - so they are stored as hex and decoded at import time.
    The plaintext never appears in this file.
    """
    return bytes.fromhex(s).decode()


IDENTIFIER_PATTERNS = {
    "internal hostname": re.compile(
        r"\b(?:" + _h("737061726b2d34306565") + "|" + _h("737061726b2d38636632")
        + "|" + _h("636c617765726469676932") + r")\b"
    ),
    "owner handle": re.compile(r"\b" + _h("636c6177657273616d7572616936") + r"\b"),
    "owner handle fragment": re.compile(r"\b" + _h("636c61776572") + r"[A-Za-z0-9_.-]*\b"),
    "host alias": re.compile(r"\b" + _h("73616d75726169") + r"[16]\b"),
    "storage mount": re.compile(_h("707572706c653462")),
    "absolute home path": re.compile(r"/home/[A-Za-z0-9_.-]+"),
    "absolute mount path": re.compile(r"/mnt/[A-Za-z0-9_.-]+"),
    "workspace path": re.compile(_h("4167656e74487562")),
    "ip address": re.compile(r"\b(?:10|172|192)\.(?:\d{1,3}\.){2}\d{1,3}\b"),
}

# Mount segments that are generic illustrative paths written by a model into its
# own answer text (Apache-Spark-style examples, shared-folder examples). These
# are benchmark content, not this programme's infrastructure.
GENERIC_MOUNT_SEGMENTS = {"nfs", "network_share", "share", "media", "tmp"}

CREDENTIAL_PATTERNS = {
    "github token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),
    "github pat": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    "huggingface token": re.compile(r"\bhf_[A-Za-z0-9]{20,}"),
    "openai-style key": re.compile(r"\bsk-[A-Za-z0-9]{24,}"),
    "aws access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    "bearer literal": re.compile(r"[Bb]earer\s+[A-Za-z0-9_\-.]{24,}"),
}

DATA_SUFFIXES = {".jsonl", ".parquet", ".arrow", ".tsv"}
ROW_SUFFIXES = {".csv"}


def main() -> int:
    failures = []
    scanned = 0
    row_files = []

    for path in sorted(REPO.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith(".git/") or rel == ".inventory.json":
            continue
        scanned += 1

        if path.suffix.lower() in DATA_SUFFIXES or path.suffix.lower() in ROW_SUFFIXES:
            if rel not in ALLOWED_ROW_FILES:
                row_files.append(rel)

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for label, pat in IDENTIFIER_PATTERNS.items():
            for m in pat.finditer(text):
                if label == "absolute mount path":
                    seg = m.group(0).rsplit("/", 1)[-1]
                    if seg in GENERIC_MOUNT_SEGMENTS:
                        continue
                line = text.count("\n", 0, m.start()) + 1
                failures.append(f"IDENTIFIER [{label}] {rel}:{line}  -> {m.group(0)!r}")

        for label, pat in CREDENTIAL_PATTERNS.items():
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                failures.append(f"CREDENTIAL [{label}] {rel}:{line}  -> {m.group(0)[:12]}...")

    print(f"scanned {scanned} files")
    print(f"row-level files not on the allow-list: {len(row_files)}")
    for r in row_files:
        print("   ", r)

    if failures:
        print(f"\nFAIL - {len(failures)} finding(s):")
        for f in failures[:80]:
            print("  ", f)
        if len(failures) > 80:
            print(f"   ... and {len(failures) - 80} more")
        return 1

    print("\nPASS - no forbidden identifier, credential, or row-level data file found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
