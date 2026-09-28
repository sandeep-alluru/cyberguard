#!/bin/bash
# cyberguard-data.sh — inspect the training data and fetch the base model.
# Run on spark-40ee after cyberguard-setup-spark.sh.
set -euo pipefail
source "$HOME/.cyberguard-env"
export PATH="$HOME/.local/bin:$PATH"
PY=$CYBERGUARD_VENV/bin/python

echo "=== dataset schema ==="
"$PY" - <<'PYEOF'
import json, os, statistics
p = os.path.join(os.environ["CYBERGUARD_ROOT"], "data/trendyol-cybersec/CyberSec-Dataset_escaped.jsonl")
n = 0
fields = None
sizes = []
with open(p, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        n += 1
        if fields is None:
            fields = list(d.keys())
            print("  fields:", fields)
        if n <= 2:
            for k, v in d.items():
                s = str(v)
                print(f"  [{k}] len={len(s)}: {s[:200]!r}")
        joined = " ".join(str(v) for v in d.values())
        sizes.append(len(joined))
sizes.sort()
print(f"  rows={n}")
print(f"  combined chars: median={sizes[len(sizes)//2]} p90={sizes[int(len(sizes)*0.9)]} max={sizes[-1]}")

# rough token estimate so the training config can be sized honestly
print(f"  rough token estimate (chars/4): median={sizes[len(sizes)//2]//4} "
      f"p90={sizes[int(len(sizes)*0.9)]//4} max={sizes[-1]//4}")
PYEOF

echo
echo "=== fetching base model Qwen3-4B-Instruct-2507 ==="
DEST="$CYBERGUARD_ROOT/models/Qwen3-4B-Instruct-2507"
if [ -d "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ]; then
  echo "  already present: $(du -sh "$DEST" | cut -f1)"
else
  hf download Qwen/Qwen3-4B-Instruct-2507 --local-dir "$DEST" 2>&1 | tail -3
fi
echo "  size: $(du -sh "$DEST" 2>/dev/null | cut -f1)"
ls "$DEST" 2>/dev/null | head -8 | sed 's/^/    /'

echo
echo "=== headroom after download ==="
df -h "$CYBERGUARD_ROOT" | tail -1 | sed 's/^/  /'
free -g | head -2 | sed 's/^/  /'
