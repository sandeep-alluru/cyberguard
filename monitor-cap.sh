#!/usr/bin/env bash
set -uo pipefail
source ~/.cyberguard-env
LOG="$CYBERGUARD_ROOT/logs/monitor-cap.log"
D="$CYBERGUARD_ROOT/cap/receipts"
END=$(( $(date +%s) + 210*60 ))
sleep 180
while [ "$(date +%s)" -lt "$END" ]; do
  if [ -f "$D/cap-run.json" ]; then echo "$(date -u +%FT%TZ) cap-run.json present; monitor exiting clean" >> "$LOG"; break; fi
  alive=0
  for p in /proc/[0-9]*; do cmd=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null); case "$cmd" in *cap_harness[.]py*) alive=1;; esac; done
  if [ "$alive" = 0 ] && [ -z "$(ls "$CYBERGUARD_ROOT"/logs/ALERT-CAP-* 2>/dev/null)" ]; then
    echo "$(date -u +%FT%TZ) ALERT-CAP: harness not alive and cap-run.json absent" > "$CYBERGUARD_ROOT/logs/ALERT-CAP-$(date +%s)"
  fi
  sleep 60
done
