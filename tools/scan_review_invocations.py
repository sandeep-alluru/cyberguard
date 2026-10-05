#!/usr/bin/env python3
"""scan_review_invocations.py — detect ungoverned external-model entry points.

Named in the gate's D18 repair allowance. A review must go through the governed adapter
(tools/astra_review.sh). Any direct invocation of an external model CLI in a script, Makefile or shell
wrapper is an ungoverned entry point.

  python3 tools/scan_review_invocations.py [path ...]

Exit 0 = clean · 1 = ungoverned entry point found · 2 = cannot run.
"""
import re, sys
from pathlib import Path

PATTERNS = [
    re.compile(r"\bcodex\s+exec\b"),
    re.compile(r"\bclaude\s+(-p|--print)\b"),
    re.compile(r"\b(kimi|grok)\s+(-p|--prompt)\b"),
    re.compile(r"\bopenai\s+api\b"),
]
GOVERNED = "astra_review.sh"
SCAN_EXT = {".sh", ".bash", ".py", ".mk", ".yml", ".yaml", ".toml"}


def main(argv):
    targets = [Path(a) for a in argv[1:]] or [Path(".")]
    hits = []
    for t in targets:
        files = [t] if t.is_file() else [p for p in t.rglob("*") if p.is_file() and p.suffix in SCAN_EXT]
        for f in files:
            try:
                text = f.read_text(encoding="utf8", errors="replace")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if any(p.search(line) for p in PATTERNS):
                    # a governed route is allowed
                    if GOVERNED in line or GOVERNED in f.name:
                        continue
                    hits.append((str(f), i, line.strip()[:100]))
    if hits:
        print(f"  UNGOVERNED ENTRY POINTS: {len(hits)}")
        for f, i, l in hits[:20]:
            print(f"    {f}:{i}  {l}")
        return 1
    print("  no ungoverned entry points found")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
