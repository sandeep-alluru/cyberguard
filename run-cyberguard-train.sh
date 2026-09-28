#!/bin/bash
# run-cyberguard-train.sh — launch the real cyber-defence fine-tune, detached, on the Spark.
#
# Sizing is measured, not guessed: the smoke runs gave ~0.92 s/sample for a Qwen3-4B LoRA at
# 2048 tokens (BATCH=2, GRAD_ACC=8). A full 53k-row epoch would be ~13.6 h, so the run is
# explicitly time-boxed and the receipt records how much of the corpus that covered. A
# time-boxed run that reports its coverage is honest; an open-ended one that gets killed
# halfway is not.
#
# Ranked throughput from the smoke runs (16 samples/step in both):
#   BATCH=2 GRAD_ACC=8 -> 14.68 s/step -> 0.92 s/sample   <- chosen
#   BATCH=8 GRAD_ACC=2 -> 19.14 s/step -> 1.20 s/sample
set -euo pipefail
source "$HOME/.cyberguard-env"
export PATH="$HOME/.local/bin:$PATH"

RUN_NAME=${RUN_NAME:-cyberguard-lora-v1}
MINUTES=${MINUTES:-170}          # fits the owner's 3-hour window
LOG="$CYBERGUARD_ROOT/logs/train-$RUN_NAME.log"
mkdir -p "$CYBERGUARD_ROOT/logs" "$CYBERGUARD_ROOT/adapters" "$CYBERGUARD_ROOT/receipts"

# Refuse to start twice — concurrent writers to one output dir would corrupt it.
n=0
for p in /proc/[0-9]*; do
  c=$(tr "\0" " " < "$p/cmdline" 2>/dev/null) || continue
  case "$c" in *train_cyberguard.py*) n=$((n+1));; esac
done
if [ "$n" -gt 0 ]; then
  echo "REFUSED: a training run is already in flight ($n process matched)"
  exit 1
fi

echo "=== $(date -u +%FT%TZ) launching $RUN_NAME, time budget ${MINUTES} min"
setsid nohup env RUN_NAME="$RUN_NAME" MAX_MINUTES="$MINUTES" \
  EPOCHS=1 BATCH=2 GRAD_ACC=8 LR=1e-4 LORA_R=32 MAX_SEQ=2048 EVAL_N=500 \
  "$CYBERGUARD_VENV/bin/python" "$HOME/train_cyberguard.py" >>"$LOG" 2>&1 </dev/null &

sleep 20
echo "--- pid(s) ---"
for p in /proc/[0-9]*; do
  c=$(tr "\0" " " < "$p/cmdline" 2>/dev/null) || continue
  case "$c" in *train_cyberguard.py*) echo "  ${p#/proc/}";; esac
done
echo "--- log ---"
tail -4 "$LOG" 2>/dev/null || echo "  (no log yet)"
echo "  log: $LOG"
