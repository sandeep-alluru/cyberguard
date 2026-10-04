#!/usr/bin/env bash
# monitor-v3.sh — supervise the live CyberGuard v3 run on spark-40ee.
#
# Logs one compact status line every INTERVAL seconds: progress step, last loss, GPU utilisation,
# and whether the trainer is still alive. Exits when the trainer is gone (completed or died) so a
# supervisor job is notified rather than polling forever.
#
# Usage: bash tools/monitor-v3.sh [interval_seconds] [max_hours]
set -uo pipefail
HOST="${HOST:-clawerdigi2@spark-40ee}"
INTERVAL="${1:-900}"
MAX_HOURS="${2:-60}"
LOG="$HOME/AgentHub/cyberguard/logs/monitor-v3.log"
mkdir -p "$(dirname "$LOG")"

start=$(date +%s)
echo "[$(date '+%F %T')] monitor start host=$HOST interval=${INTERVAL}s max=${MAX_HOURS}h -> $LOG" >> "$LOG"

while true; do
  now=$(date +%s)
  elapsed_h=$(( (now - start) / 3600 ))
  if [ "$elapsed_h" -ge "$MAX_HOURS" ]; then
    echo "[$(date '+%F %T')] monitor stop: max hours reached" >> "$LOG"; break
  fi

  status=$(ssh -o BatchMode=yes -o ConnectTimeout=15 "$HOST" '
    alive=$(for p in /proc/[0-9]*; do exe=$(readlink -f $p/exe 2>/dev/null) || continue;
      case "$exe" in *python*) ;; *) continue;; esac
      while IFS= read -r -d "" a; do case "$a" in */train_cyberguard.py) echo yes; break 2;; esac
      done < $p/cmdline 2>/dev/null; done)
    gpu=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader 2>/dev/null | tr -d " %")
    prog=$(tail -c 2000 ~/cyberguard/logs/train-cyberguard-lora-v3.log 2>/dev/null | tr "\r" "\n" | grep -a "[0-9]*/8783" | tail -1)
    echo "alive=${alive:-no} gpu=${gpu:-?}% ${prog:-<no progress line>}"
  ' 2>/dev/null)
  rc=$?

  if [ $rc -ne 0 ]; then
    echo "[$(date '+%F %T')] SSH-FAILED rc=$rc" >> "$LOG"
  else
    echo "[$(date '+%F %T')] $status" >> "$LOG"
    case "$status" in
      alive=yes*) : ;;
      *) echo "[$(date '+%F %T')] trainer no longer running -> monitor stop" >> "$LOG"; break ;;
    esac
  fi
  sleep "$INTERVAL"
done
