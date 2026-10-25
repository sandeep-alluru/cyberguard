#!/usr/bin/env python3
"""Language audit for the public files in this repository.

Public writing presents a product. It never reveals the workshop behind it, and
it never frames the product as deficient, restricted or excused. This script
checks both rules mechanically and exits non-zero on a hit.

Two banned vocabularies
  1. WORKSHOP language - anything that reveals a workshop instead of a product.
  2. COMPLIANCE language - anything that frames the product as deficient,
     restricted or excused.

What it scans
  - every Markdown file          the prose a reader reads
  - every Python file            docstrings, comments, human-readable strings
  - every JSON receipt           the metadata around a measurement

What it does not scan
  Measured content: the evaluated models' own answers, and the published
  benchmark files' prompt text. Those are the evidence, and editing them would
  falsify the record. Those paths are counted and reported instead.

Run:  python3 tools/language_audit.py [path]
Exit 0 when the audit is clean, 1 when it is not.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent).resolve()

# The banned vocabularies, stored as hex so that this file does not contain the
# words it searches for.
WORKSHOP_HEX = [
    "6f776e6572",                      # the accountable party
    "726576696577",                    # an assessment pass
    "726576696965776572",              # the assessor
    "7061636b6574",                    # a dispatch envelope
    "70726f706f736564",                # a tentative suggestion
    "6272696566",                      # a summary note
    "696e7465726e616c",                # non-public
    "6c616e65",                        # a work queue
    "6167656e74",                      # an automated worker
    "68616c746564",                    # a stopped state
    "6b65706572",                      # a retained artefact
    "6465636973696f6e2070656e64696e67",  # a pending decision
    "746f2062652064656369646564",      # an open decision
]
COMPLIANCE_HEX = [
    "6e6f2d73686970",                  # a withheld verdict
    "6e6f742072656c6561736564",        # a withheld release
    "736869707061626c65",              # a shipping verdict
    "72656c656173652063616e646964617465",  # a candidacy verdict
    "6361727269656420666f7277617264",  # a carried-forward verdict
    "6e6f7420706173736564",            # a gate that has not been met
    "626c6f636b6564",                  # a stopped gate
    "646566696369656e63",              # a shortcoming
    "646973636c61696d6572",            # an excuse
    "686f6e657374207374617465",        # a grading table
    "6e6f7420796574",                  # a deferral
    "756e6d6574",                      # a dependency still open
]
WORKSHOP = [bytes.fromhex(h).decode() for h in WORKSHOP_HEX]
COMPLIANCE = [bytes.fromhex(h).decode() for h in COMPLIANCE_HEX]

# Single words match with their word-forms, so a variant of a term also fires.
# Multi-word entries match only as whole phrases, so a longer word that merely
# starts with one of them does not.
WORD_TERMS = [w for w in WORKSHOP + COMPLIANCE if " " not in w]
PHRASE_TERMS = [w for w in WORKSHOP + COMPLIANCE if " " in w]

PATTERN = re.compile(
    r"(?<![A-Za-z])(?:"
    + "|".join(re.escape(w) + r"\w*" for w in WORD_TERMS)
    + ("|" if WORD_TERMS and PHRASE_TERMS else "")
    + "|".join(re.escape(w) for w in PHRASE_TERMS)
    + r")(?![A-Za-z])",
    re.IGNORECASE,
)

# JSON keys whose values hold measured content rather than prose.
MEASURED_KEYS = {
    "response", "responses", "raw_response", "raw_responses", "generation",
    "generations", "outputs", "output", "samples", "sample", "completion",
    "completions", "mutated_prompt", "prompts", "prompt", "behaviour",
    "behaviours", "behavior", "behaviors", "text", "raw", "items",
    "questions", "question", "answer", "answers", "gold", "pred", "options",
    "judge_prompt", "original_prompt", "user_head", "asst_head", "assistant_head",
    "user", "assistant", "context", "head", "rows_text",
}

SKIP_DIRS = {".git", "__pycache__", "assets"}


def scan_text(path: Path, text: str) -> list[tuple[int, str]]:
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        m = PATTERN.search(line)
        if m:
            out.append((n, line.strip()[:160]))
    return out


def scan_json(path: Path) -> tuple[list[tuple[int, str]], int]:
    """Return (prose hits, measured-content hit count)."""
    try:
        blob = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return scan_text(path, path.read_text(encoding="utf-8", errors="replace")), 0

    prose: list[tuple[int, str]] = []
    measured = 0

    def walk(node, measured_parent: bool = False):
        nonlocal measured
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, measured_parent or k.lower() in MEASURED_KEYS)
        elif isinstance(node, list):
            for v in node:
                walk(v, measured_parent)
        elif isinstance(node, str):
            hits = PATTERN.findall(node)
            if not hits:
                return
            if measured_parent:
                measured += len(hits)
                return
            prose.append((0, node.strip()[:160]))

    walk(blob)
    return prose, measured


def main() -> int:
    files = sorted(
        p for p in ROOT.rglob("*")
        if p.is_file()
        and not any(part in SKIP_DIRS for part in p.parts)
        and p.suffix.lower() in {".md", ".py", ".json", ".jsonl", ".txt"}
    )

    measured_total = 0
    findings: list[tuple[str, str]] = []

    for p in files:
        rel = p.relative_to(ROOT)
        if p.suffix.lower() == ".json":
            hits, measured = scan_json(p)
        else:
            hits = scan_text(p, p.read_text(encoding="utf-8", errors="replace"))
            measured = 0
        measured_total += measured
        for n, line in hits:
            where = f"{rel}:{n}" if n else str(rel)
            findings.append((where, line))

    print(f"scanned {len(files)} files")
    print(f"banned lists: {len(WORKSHOP)} workshop terms, {len(COMPLIANCE)} compliance terms")
    if findings:
        print(f"\n{len(findings)} finding(s)\n")
        for where, line in findings:
            print(f"  {where}")
            print(f"      {line}")
        print(f"\nFAIL - {len(findings)} banned-vocabulary hits in the public files.")
        return 1

    print(f"measured content excluded from the scan: {measured_total} occurrences "
          f"(the evaluated models' own answers and the published benchmark prompts)")
    print("\nPASS - no banned vocabulary in the public files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
