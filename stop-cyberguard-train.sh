#!/bin/bash
# stop-cyberguard-train.sh — stop the cyber fine-tune cleanly and record where it got to.
# Run on spark-40ee.
#
# WHY: the training uses spark-40ee's GB10 continuously. That GPU also serves Flash-Next's
# RPC share, so any Flash-Next test run at the same time measures training contention rather
# than the model. The owner's test is for Flash-Next, so the test gets a clean GPU.
#
# Match by argv (arg 2 = the script path), never `pgrep -f`: the shell running this file
# carries the pattern in its own command line and would match itself.
set -u
source "$HOME/.cyberguard-env"
LOG="$CYBERGUARD_ROOT/logs/train-cyberguard-lora-v1.log"

echo "=== stopping cyber training $(date -u +%FT%TZ)"
killed=0
for p in /proc/[0-9]*; do
  a2=$(tr "\0" "\n" < "$p/cmdline" 2>/dev/null | sed -n 2p)
  case "$a2" in
    *train_cyberguard.py*) echo "  killing pid ${p#/proc/}"; kill "${p#/proc/}" 2>/dev/null; killed=$((killed+1));;
  esac
done
echo "  killed $killed process(es)"

# child workers (dataloader) follow the parent; give them a moment, then be firm
sleep 8
for p in /proc/[0-9]*; do
  a2=$(tr "\0" "\n" < "$p/cmdline" 2>/dev/null | sed -n 2p)
  case "$a2" in
    *train_cyberguard.py*) echo "  force-killing ${p#/proc/}"; kill -9 "${p#/proc/}" 2>/dev/null;;
  esac
done

echo "--- progress at stop ---"
tr '\r' '\n' < "$LOG" 2>/dev/null | grep -oE "\| +[0-9]+/[0-9]+ \[[0-9:]+<[0-9:?]+" | tail -2 | sed 's/^/  /'
tr '\r' '\n' < "$LOG" 2>/dev/null | grep -E "'loss'|'grad_norm'" | tail -3 | sed 's/^/  /'
echo "--- checkpoints on disk ---"
ls -la "$CYBERGUARD_ROOT/adapters/cyberguard-lora-v1" 2>/dev/null | head -6 | sed 's/^/  /'
echo "=== stopped $(date -u +%FT%TZ)"
