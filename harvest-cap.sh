#!/usr/bin/env bash
# harvest-cap.sh — pull capability-box receipts + logs, verify every sha256, fatals on mismatch.
set -uo pipefail
R=clawerdigi2@spark-40ee
DEST=/home/clawer-samurai-1/AgentHub/cyberguard/research-tmp/harvest-cap-v1
mkdir -p "$DEST"/{receipts,logs}
MANIFEST=$(timeout 60 ssh -o BatchMode=yes "$R" 'cd ~/cyberguard/cap/receipts 2>/dev/null && sha256sum cap-*.json 2>/dev/null; cd ~/cyberguard/logs && sha256sum cap-harness.log monitor-cap.log stage-cap-data.log cap-replay.log cap-sens.log 2>/dev/null' | grep -v '^$')
[ -n "$MANIFEST" ] || { echo "HARVEST-FATAL: empty manifest"; exit 9; }
echo "$MANIFEST" | while read -r sum name; do
  case "$name" in cap-*.json) sub=receipts;; *) sub=logs;; esac
  src=$([ "$sub" = receipts ] && echo "cap/receipts/$name" || echo "logs/$name")
  timeout 120 scp -q "$R:~/cyberguard/$src" "$DEST/$sub/" || { echo "HARVEST-FATAL: scp $name"; exit 9; }
  got=$(sha256sum "$DEST/$sub/$name" | cut -d' ' -f1)
  [ "$got" = "$sum" ] && echo "OK $name" || { echo "HARVEST-FATAL: sha256 mismatch $name"; exit 9; }
done && echo "HARVEST-COMPLETE all checksums verified -> $DEST"
