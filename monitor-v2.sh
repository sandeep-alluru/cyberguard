#!/usr/bin/env bash
# monitor-v2.sh — liveness by /proc + log GROWTH (never by the log tail: a stale traceback from a previous
# attempt is not evidence about this one — CRAFT-O-01/A15).
# Usage: bash monitor-v2.sh <A|B> [cycles] [interval_s]
set -uo pipefail
ARM="${1:?}"; CYCLES="${2:-288}"; IV="${3:-300}"
ROOT="$HOME/cyberguard"
case "$ARM" in A) LOG="$ROOT/logs/train-cyberguard-lora-v2-armA.log"; REC="$ROOT/receipts/cyberguard-lora-v2-armA.json";; 
             B) LOG="$ROOT/logs/train-cyberguard-lora-v2-armB.log"; REC="$ROOT/receipts/cyberguard-lora-v2-armB.json";; esac
MLOG="$ROOT/logs/monitor-v2-$ARM.log"; mkdir -p "$ROOT/logs"
prev=0; quiet=0
for i in $(seq 1 "$CYCLES"); do
  ts=$(date '+%F %T'); alive=no
  for p in /proc/[0-9]*; do
    exe=$(readlink -f "$p/exe" 2>/dev/null) || continue
    case "$exe" in *python*) ;; *) continue;; esac
    while IFS= read -r -d '' a; do
      case "$a" in */train_cyberguard.py|train_cyberguard.py) alive=yes; break;; esac
    done < "$p/cmdline" 2>/dev/null
  done
  size=$(stat -c%s "$LOG" 2>/dev/null || echo 0)
  if [ "$size" -gt "$prev" ]; then quiet=0; else quiet=$((quiet+1)); fi
  prev=$size
  printf '%s arm=%s alive=%s log=%s quiet=%s\n' "$ts" "$ARM" "$alive" "$size" "$quiet" >> "$MLOG"
  if [ -f "$REC" ]; then echo "$ts RECEIPT-PRESENT -> monitor exit" >> "$MLOG"; exit 0; fi
  if [ "$alive" = no ] && [ "$quiet" -ge 2 ]; then
    echo "$ts ALERT arm=$ARM died without a receipt" >> "$MLOG"; exit 1
  fi
  [ "$quiet" -ge 3 ] && echo "$ts ALERT-STALL arm=$ARM no log growth for $quiet cycles" >> "$MLOG"
  sleep "$IV"
done
