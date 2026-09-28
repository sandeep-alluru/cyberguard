#!/usr/bin/env bash
# monitor-eval-chain.sh <deadline_epoch> — watchdog for the unattended eval chain.
# Liveness by process + eval-log growth (tqdm writes \r; do not trust step regexes).
# Never pattern-matches its own name; kills nothing; writes ALERT files.
set -uo pipefail
source ~/.cyberguard-env
DEADLINE="${1:-$(( $(date +%s) + 4*3600 ))}"
LOGDIR="$CYBERGUARD_ROOT/logs"
CHAINLOG="$LOGDIR/eval-chain-cyberguard-lora-v1.log"
EVALLOG="$LOGDIR/eval-cyberguard-lora-v1.log"
MLOG="$LOGDIR/monitor-eval.log"
alert() { echo "$(date -u +%FT%TZ) ALERT $*" >> "$MLOG"; : > "$LOGDIR/ALERT-EVAL-$(date +%s)"; }
chain_alive() {
  local p cmd
  for p in /proc/[0-9]*; do
    cmd=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null)
    case "$cmd" in *run-eval-chain.sh*|*eval_cyberguard.py*) return 0 ;; esac
  done
  return 1
}
prev=-1; stalls=0
while :; do
  now=$(date +%s)
  if grep -aq 'eval-chain done' "$CHAINLOG" 2>/dev/null; then
    echo "$(date -u +%FT%TZ) DONE chain completed; monitor exits" >> "$MLOG"; exit 0
  fi
  if ! chain_alive; then
    if [ $((now - DEADLINE)) -lt 120 ]; then alert "chain process gone without done-line"; fi
  fi
  if [ -f "$EVALLOG" ]; then
    size=$(stat -c %s "$EVALLOG")
    if [ "$prev" -ge 0 ] && [ "$size" -le "$prev" ]; then
      stalls=$((stalls+1))
      [ "$stalls" -ge 3 ] && alert "eval log no growth for 3 cycles (size=$size)" && stalls=0
    else
      stalls=0
    fi
    prev=$size
    echo "$(date -u +%FT%TZ) OK size=$size" >> "$MLOG"
  else
    echo "$(date -u +%FT%TZ) OK pre-eval (merge-equiv phase)" >> "$MLOG"
  fi
  if [ "$now" -gt "$DEADLINE" ]; then alert "deadline exceeded, chain not done"; exit 1; fi
  sleep 300
done
