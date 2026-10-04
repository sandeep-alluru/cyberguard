#!/usr/bin/env bash
# supervise-v3.sh — check the CyberGuard v3 run every 3 hours and keep a progress log.
#
# Requested by the owner: "do checks every 3 hours keep track of progress".
# This is deliberately the opposite of the poller that was cut earlier: a 15-minute ssh watchdog was
# over-engineering because it produced noise at a cadence faster than the thing it watched. Three-hourly,
# each line records a genuinely different point in a ~37 h run, and the log is the deliverable.
#
# It appends one timestamped line per check to logs/v3-progress.log, then sleeps. It EXITS when:
#   * the receipt appears  -> training finished (harvest is then possible), or
#   * the process is gone  -> the run ended some other way and needs a human look.
# Either exit is a state change worth being told about, so the job's completion is the notification.
#
# Usage: bash tools/supervise-v3.sh [interval_seconds]
set -uo pipefail
HOST="${HOST:-clawerdigi2@spark-40ee}"
INTERVAL="${1:-10800}"          # 3 hours
LOG="$HOME/AgentHub/cyberguard/logs/v3-progress.log"
mkdir -p "$(dirname "$LOG")"

echo "# CyberGuard v3 supervision — one line per check, every $((INTERVAL/3600))h" >> "$LOG"

while true; do
  status=$(ssh -o BatchMode=yes -o ConnectTimeout=20 "$HOST" '
    L=~/cyberguard/logs/train-cyberguard-lora-v3.log
    line=$(tail -c 400 "$L" 2>/dev/null | tr "\r" "\n" | grep -a "8783" | tail -1)
    pct=$(printf "%s" "$line" | grep -oE "^ *[0-9]+%" | tr -d " %")
    step=$(printf "%s" "$line" | grep -oE "[0-9]+/8783" | head -1)
    eta=$(printf "%s" "$line" | grep -oE "<[0-9:]+" | tr -d "<")
    gpu=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader 2>/dev/null | tr -d " %")
    if ps -p 1189450 >/dev/null 2>&1; then alive="yes $(ps -p 1189450 -o etime= | tr -d " ")"; else alive="NO"; fi
    if [ -f ~/cyberguard/receipts/cyberguard-lora-v3.json ]; then r="RECEIPT-WRITTEN"; else r="pending"; fi
    echo "step=${step:-?} (${pct:-?}%) eta=${eta:-?} gpu=${gpu:-?}% alive=${alive} receipt=${r}"
  ' 2>/dev/null)
  rc=$?

  if [ $rc -ne 0 ]; then
    echo "$(date '+%F %T') SSH-FAILED rc=$rc" >> "$LOG"
  else
    echo "$(date '+%F %T') $status" >> "$LOG"
    case "$status" in
      *receipt=RECEIPT-WRITTEN*) echo "$(date '+%F %T') training finished -> supervisor exit" >> "$LOG"; break ;;
      *alive=NO*)                echo "$(date '+%F %T') process gone without a receipt -> needs a look" >> "$LOG"; break ;;
    esac
  fi
  sleep "$INTERVAL"
done
