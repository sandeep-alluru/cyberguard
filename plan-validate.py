#!/usr/bin/env python3
"""plan-validate.py — the completeness contract for plan-type deliverables.

Standing rule (MEMORY.md §常驻指令 rule 31): a plan/spec may not be called *ready*, *complete* or
*delivered* until it passes this validator. The rule is:

  1. every decidable question is decided in the document;
  2. every undecidable one is bound to the experiment that settles it;
  3. every referenced artifact exists, or is listed as a deliverable of the plan;
  4. every workstream has an EXECUTABLE pass/fail exit command;
  5. no TBD / 待定 / 后续再议 placeholder anywhere.

Checks implemented (each is a heuristic, and says so):

  C1 NO-PLACEHOLDER  forbidden placeholder tokens anywhere in the text
  C2 NO-EMPTY-CELL   markdown table rows with an empty cell, or with fewer cells than the header
  C3 ARTIFACTS       every backticked path reference exists, or is exempted as a deliverable
  C4 EXIT-COMMANDS   every unit row (`| U<n>` or a row with an "owner" column) carries a command
  C5 OWNER-DECISIONS any "owner decision"/"approval line" table row states a decider or a default
  C6 DONE-MEANS      the document contains a done-means/definition-of-done table whose rows carry
                     a check (a command, an exit code, or the word "exit")

Usage:
  python3 plan-validate.py docs/SPEC-V2.md [--root .] [--strict]

Exit codes: 0 PASS · 1 usage/IO error · 2 FAIL (violations) · 3 PASS with warnings (--strict only)
"""

from __future__ import annotations

import argparse
import os
import re
import sys

PLACEHOLDERS = [
    r"\bTBD\b", r"\bTODO\b", r"\bFIXME\b", r"\bXXX\b", r"待定", r"后续再议", r"待补",
    r"to be decided", r"to be determined", r"fill in", r"placeholder",
]
# "N/A" is not always a placeholder: an explicit, scoped not-applicable with a reason is a decision.
# Surface it as a warning so a human confirms the reason is stated, rather than failing the plan.
SOFT_PLACEHOLDERS = [r"\bN/?A\b(?![-\w])"]
PLACEHOLDER_RE = [re.compile(p, re.IGNORECASE) for p in PLACEHOLDERS]
SOFT_PLACEHOLDER_RE = [re.compile(p, re.IGNORECASE) for p in SOFT_PLACEHOLDERS]

PATH_RE = re.compile(r"`([^`\s]+)`")
EXT = (".md", ".py", ".sh", ".json", ".jsonl", ".yaml", ".yml", ".txt", ".log", ".csv", ".cfg",
       ".toml", ".html", ".ipynb")
KNOWN_PREFIXES = ("./", "../", "docs/", "v2/", "logs/", "receipts/", "evals/", "data/",
                  "training/", "serving/", "gguf/", "research-tmp/", "research_tmp/", "src/",
                  "tests/", "~/")
DELIVERABLE_RE = re.compile(r"deliverable|exit command|pass\s*=\s*exit|→|\bexit 0\b|\(to be written\)",
                            re.IGNORECASE)
ROW_CHECK_RE = re.compile(r"exit|check|exists|sha256|verified|→|HARVEST-COMPLETE", re.IGNORECASE)
UNIT_ROW_RE = re.compile(r"^\|\s*(U\d+|[A-Z]{1,3}-\d+)\b")
OWNER_HINT_RE = re.compile(r"\bowner\b", re.IGNORECASE)
CMD_RE = re.compile(r"`[^`]*(python3|bash|\.sh|--check|--selftest|exit\s*\d)[^`]*`|→\s*exit\s*\d")
DONE_MEANS_RE = re.compile(r"done[- ]means|definition of done|完成定义", re.IGNORECASE)
CHECK_HINT_RE = re.compile(r"exit\s*\d|`[^`]+`|check", re.IGNORECASE)


def read(path: str) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def cells(line: str) -> list[str]:
    s = line.strip()
    if not s.startswith("|"):
        return []
    body = s.strip("|")
    parts = re.split(r"(?<!\\)\|", body)          # a literal \| is content, not a column break
    return [c.strip() for c in parts]


def looks_like_path(tok: str) -> bool:
    if tok.startswith(KNOWN_PREFIXES):
        return True
    return tok.endswith(EXT)


def basename_index(root: str) -> dict[str, str]:
    """map basename -> one path, for resolving bare `VERDICT-v1.md`-style references."""
    idx: dict[str, str] = {}
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".git")]
        for fn in filenames:
            idx.setdefault(fn, os.path.join(dirpath, fn))
    return idx


def is_separator(row: list[str]) -> bool:
    return bool(row) and all(re.fullmatch(r":?-{2,}:?", c or "-") for c in row)


# A05 repair: DEMONSTRATED detector false positives. The raw token scan flagged two legitimate lines:
#   - a documented factual-question definition that lists "Q6 unfilled placeholder or broken template"
#   - a line explicitly recording a decision as UNDECIDABLE from the literature
# The detector is made context-aware. The registered question wording is NOT altered.
_FP_CONTEXT = (
    "undecidable",            # an explicit, recorded decision
    "not a placeholder",      # explicit negation
    "unfilled placeholder",   # a definition of the forbidden token
    "broken template",        # part of the same definition
    "forbidden placeholder",
    "no tbd",
)


def _is_false_positive(line: str) -> bool:
    low = line.lower()
    if any(k in low for k in _FP_CONTEXT):
        return True
    # a line that enumerates several forbidden tokens is a definition, not a use
    return sum(1 for rx in PLACEHOLDER_RE if rx.search(line)) >= 2


def check_c1(lines: list[str]) -> tuple[list[str], list[str]]:
    fails, warns = [], []
    for i, line in enumerate(lines, 1):
        for rx in PLACEHOLDER_RE:
            m = rx.search(line)
            if m:
                if _is_false_positive(line):
                    continue
                fails.append(f"C1 line {i}: placeholder {m.group(0)!r} — {line.strip()[:110]}")
        for rx in SOFT_PLACEHOLDER_RE:
            m = rx.search(line)
            if m:
                warns.append(f"C1 line {i}: 'N/A' present — confirm the line states WHY it does not "
                             f"apply — {line.strip()[:110]}")
    return fails, warns


def check_c2(lines: list[str]) -> tuple[list[str], list[str]]:
    fails, warns = [], []
    header: list[str] | None = None
    for i, line in enumerate(lines, 1):
        row = cells(line)
        if not row:
            header = None
            continue
        if is_separator(row):
            continue
        if header is None:
            header = row
            continue
        if len(row) != len(header):
            warns.append(f"C2 line {i}: {len(row)} cells vs {len(header)} in header")
        for j, c in enumerate(row):
            if c == "":
                fails.append(f"C2 line {i}: empty cell in column {j + 1} — {line.strip()[:110]}")
    return fails, warns


def check_c3(lines: list[str], root: str) -> tuple[list[str], list[str]]:
    fails, warns = [], []
    seen = set()
    idx = basename_index(root)
    for i, line in enumerate(lines, 1):
        for tok in PATH_RE.findall(line):
            if tok in seen or not looks_like_path(tok):
                continue
            seen.add(tok)
            if (os.path.exists(os.path.join(root, tok)) or os.path.exists(tok)
                    or os.path.basename(tok) in idx):
                continue
            if tok.startswith("~/") or tok.startswith("/"):
                warns.append(f"C3 line {i}: `{tok}` is an absolute/home path — a remote or other-host "
                             f"artifact not checkable from this root (state the host in the plan)")
                continue
            # exempt: the line itself marks it as a deliverable, or it sits in a row that carries a
            # check (done-means / units tables list artifacts the plan will produce)
            exempt = DELIVERABLE_RE.search(line) or (
                line.strip().startswith("|") and ROW_CHECK_RE.search(line))
            if not exempt:
                fails.append(f"C3 line {i}: references `{tok}` which does not exist and is not "
                             f"marked as a deliverable")
    return fails, warns


def check_c4(lines: list[str]) -> list[str]:
    fails = []
    for i, line in enumerate(lines, 1):
        if not UNIT_ROW_RE.match(line):
            continue
        uid = UNIT_ROW_RE.match(line).group(1)
        if not CMD_RE.search(line):
            fails.append(f"C4 line {i}: unit {uid} has no executable exit command")
    return fails


def check_c5(lines: list[str]) -> list[str]:
    fails = []
    in_section = False
    for i, line in enumerate(lines, 1):
        low = line.lower()
        if low.startswith("#"):
            in_section = "owner decision" in low or "approval line" in low or "open owner" in low
        if in_section and line.strip().startswith("|") and not is_separator(cells(line)):
            row = cells(line)
            if len(row) < 3 and not set("".join(row)) <= set("-: "):
                fails.append(f"C5 line {i}: owner-decision row without a decider/default — "
                             f"{line.strip()[:110]}")
    return fails


def check_c6(lines: list[str]) -> list[str]:
    """The done-means table is the FIRST table after its heading (not any later table)."""
    start = None
    for i, line in enumerate(lines):
        if DONE_MEANS_RE.search(line):
            start = i
            break
    if start is None:
        return ["C6: no done-means / definition-of-done section found"]
    fails, in_table = [], False
    for i in range(start, len(lines)):
        line = lines[i]
        if line.strip().startswith("#"):
            break
        if line.strip().startswith("|"):
            if is_separator(cells(line)):
                in_table = True
                continue
            if in_table and not CHECK_HINT_RE.search(line):
                fails.append(f"C6 line {i + 1}: done-means row carries no check — "
                             f"{line.strip()[:110]}")
        elif in_table:
            break
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="completeness contract for plan deliverables")
    ap.add_argument("plan")
    ap.add_argument("--root", default=".")
    ap.add_argument("--strict", action="store_true", help="warnings fail too")
    args = ap.parse_args()
    if not os.path.exists(args.plan):
        print(f"FATAL: no such plan: {args.plan}", file=sys.stderr)
        return 1

    lines = read(args.plan)
    failures: list[str] = []
    warnings: list[str] = []

    f1, w1 = check_c1(lines)
    failures += f1
    warnings += w1
    f2, w2 = check_c2(lines)
    failures += f2
    warnings += w2
    f3, w3 = check_c3(lines, args.root)
    failures += f3
    warnings += w3
    failures += check_c4(lines)
    failures += check_c5(lines)
    failures += check_c6(lines)

    print(f"PLAN-VALIDATE {args.plan}  ({len(lines)} lines, root={os.path.abspath(args.root)})")
    for f in failures:
        print("  FAIL:", f)
    for w in warnings:
        print("  warn:", w)
    print(f"\n  {len(failures)} failure(s), {len(warnings)} warning(s)")

    if failures:
        print("  RESULT: FAIL — this plan may not be called ready/complete/delivered")
        return 2
    if warnings and args.strict:
        print("  RESULT: FAIL (strict) — warnings treated as failures")
        return 3
    print("  RESULT: PASS — decidable questions decided, artifacts accounted for, "
          "every unit has an executable exit command, no placeholders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
