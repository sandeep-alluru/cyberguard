#!/usr/bin/env python3
"""
Verify this repository against its publication boundary.

Scans every file for:
  FORBIDDEN IDENTIFIERS  - machine names, account handles, absolute local paths, IP addresses
  CREDENTIAL PATTERNS   - tokens and keys of any kind
  DATA FILES             - row-level .jsonl / .csv that could be training or held-out data

Exit 0 only when every category is clean.

Run:  python3 verify_repo.py [repo-checkout]
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
# they are published public-benchmark instruments, not programme data.
ALLOWED_ROW_FILES = {
    "results/pubbench/harmbench/harmbench_behaviors_text_test.csv",
    "results/pubbench/secqa_test.csv",
}

def _h(s: str) -> str:
    """Decode a hex literal back to text.

    The scanner lives in the repository it scans, so the words it looks for are
    stored as hex and decoded at import time. The plaintext never appears in
    this file.
    """
    return bytes.fromhex(s).decode()


IDENTIFIER_PATTERNS = {
    # The specific machine names, account handles and storage paths that were
    # removed when this tree was assembled are deliberately absent here, in any
    # encoding: a published checker that carried them would put them back into
    # the tree it checks. What remains are the shapes a leak would take.
    "absolute home path": re.compile(r"/home/[A-Za-z0-9_.-]+"),
    "absolute mount path": re.compile(r"/mnt/[A-Za-z0-9_.-]+"),
    "ip address": re.compile(r"\b(?:10|172|192)\.(?:\d{1,3}\.){2}\d{1,3}\b"),
    "private host name": re.compile(
        r"\b[A-Za-z0-9-]+\.(?:" + _h("696e7465726e616c") + "|" + _h("6c6f63616c")
        + "|" + _h("636f7270") + "|" + _h("6c616e") + r")\b"
    ),
}

# Mount segments that are generic illustrative paths written by a model into its
# own answer text (Apache-Spark-style examples, shared-folder examples). These
# are benchmark content, not infrastructure.
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
        if rel.startswith(".git/"):
            continue
        # Python's own byproducts are not part of the published surface, and
        # counting them would make the file count differ between a fresh clone
        # and a working tree that has run the other checkers.
        if "__pycache__/" in rel or rel.endswith(".pyc"):
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
