#!/usr/bin/env bash
# local watcher: prints cap-harness progress deltas every 2 min; exits on DONE or alert
R=clawerdigi2@spark-40ee
prev=""
for i in $(seq 1 120); do
  out=$(timeout 25 ssh -o BatchMode=yes "$R" 'tail -4 ~/cyberguard/logs/cap-harness.log 2>/dev/null; ls ~/cyberguard/logs/ALERT-CAP-* 2>/dev/null | head -1; grep -o "receipt cap-[0-9a-z-]*" ~/cyberguard/logs/cap-harness.log 2>/dev/null | tail -3' 2>/dev/null)
  if [ -n "$out" ] && [ "$out" != "$prev" ]; then
    echo "=== $(TZ=America/Chicago date '+%H:%M:%S') CDT"; echo "$out"
    prev="$out"
  fi
  case "$out" in *"DONE {"*|*ALERT-CAP*) break;; esac
  sleep 120
done
echo "WATCH-END"
