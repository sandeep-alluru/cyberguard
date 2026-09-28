#!/bin/bash
# monitor-cyberguard.sh — remote watchdog for the v1 training run (pod-ops exec_watchdog pattern,
# adapted to owned hardware). Usage: monitor-cyberguard.sh <deadline_epoch>
# Cadence 300s. Alerts are written; the monitor never touches the run itself.
set -u
DEADLINE=${1:?deadline epoch required}
ROOT="$HOME/cyberguard"
RUN=cyberguard-lora-v1
LOG="$ROOT/logs/train-$RUN.log"
MLOG="$ROOT/logs/monitor-v1.log"
MFILE="$ROOT/receipts/train-$RUN.json"
QUIET=0
mkdir -p "$ROOT/logs"
# Only content appended AFTER monitor start can indict the run — yesterday's crashed log of the
# same run-name sits in the tail window at launch (false-positive we actually hit 05:46Z).
SIZE0=$(stat -c %s "$LOG" 2>/dev/null || echo 0)
echo "$(date -u +%FT%TZ) MONITOR START deadline=$(date -u -d "@$DEADLINE" +%FT%TZ) logbase=$SIZE0" >> "$MLOG"
while :; do
  NOW=$(date +%s)
  # done?
  if [ -f "$MFILE" ]; then
    echo "$(date -u +%FT%TZ) COMPLETE receipt present" >> "$MLOG"; exit 0
  fi
  # deadline?
  if [ "$NOW" -gt "$DEADLINE" ]; then
    echo "$(date -u +%FT%TZ) ALERT DEADLINE passed without receipt" >> "$MLOG"
    : > "$ROOT/logs/ALERT-deadline"; exit 1
  fi
  # alive? bracketed pattern so this script's own cmdline can never self-match (corpus R25/F58)
  alive=0
  for p in /proc/[0-9]*; do
    c=$(tr "\0" " " < "$p/cmdline" 2>/dev/null) || continue
    case "$c" in *train_cyberguard[.]py*) alive=1;; esac
  done
  if [ "$alive" -eq 0 ]; then
    echo "$(date -u +%FT%TZ) ALERT PROCESS GONE (no trainer, no receipt)" >> "$MLOG"
    : > "$ROOT/logs/ALERT-process-gone"; exit 1
  fi
  # crash? — scan only bytes added since monitor start
  if tail -c +"$((SIZE0+1))" "$LOG" 2>/dev/null | tail -c 6000 | grep -qE "Traceback|CUDA out of memory|RuntimeError"; then
    echo "$(date -u +%FT%TZ) ALERT CRASH signature in log tail" >> "$MLOG"
    : > "$ROOT/logs/ALERT-crash"; exit 1
  fi
  # stall? log bytes not growing for 3 cycles
  sz=$(stat -c %s "$LOG" 2>/dev/null || echo 0)
  if [ "${sz:-0}" = "${PREV:-}" ]; then QUIET=$((QUIET+1)); else QUIET=0; fi
  PREV=$sz
  if [ "$QUIET" -ge 3 ]; then
    echo "$(date -u +%FT%TZ) ALERT STALL log quiet 15min (size $sz)" >> "$MLOG"
    : > "$ROOT/logs/ALERT-stall"; exit 1
  fi
  step=$(tr '\r' '\n' < "$LOG" 2>/dev/null | grep -oE "[0-9]+/[0-9]+ \[" | tail -1)
  echo "$(date -u +%FT%TZ) OK alive size=$sz ${step:-no-step-line-yet}" >> "$MLOG"
  sleep 300
done
