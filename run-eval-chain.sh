#!/usr/bin/env bash
# run-eval-chain.sh — start benchmarks the moment the trainer releases the GPU.
# Waits for the trainer process to disappear (proc scan, never pkill/pgrep -f self-match),
# then runs the merge-equivalence check and the hardened evaluator. Durable logs, real exit codes.
set -uo pipefail
source ~/.cyberguard-env
cd "$HOME"
RUN_NAME="${RUN_NAME:-cyberguard-lora-v1}"
PY="$CYBERGUARD_VENV/bin/python"
LOGDIR="$CYBERGUARD_ROOT/logs"
CHAIN="$LOGDIR/eval-chain-$RUN_NAME.log"
TRAINER_RE='*train_cyberguard[.]py*'

alive() {
  # R25 lesson, second form (2026-09-27 incident): a GLOB pattern handed to grep is NOT a regex —
  # the leading * is literal there, alive() never matched, and this chain started eval DURING
  # training (base-only smoke, killed; logs preserved as *.stray-*). Shell case-glob is the
  # correct tool and the chain's own name can never match a *train_cyberguard.py* cmdline.
  local p cmd
  for p in /proc/[0-9]*; do
    cmd=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null)
    case "$cmd" in *train_cyberguard.py*) return 0 ;; esac
  done
  return 1
}

echo "=== $(date -u +%FT%TZ) eval-chain armed, waiting for trainer to exit" >> "$CHAIN"
while alive; do sleep 60; done
echo "=== $(date -u +%FT%TZ) trainer gone; GPU free" >> "$CHAIN"
sleep 20

echo "=== $(date -u +%FT%TZ) merge_equiv start" >> "$CHAIN"
RUN_NAME="$RUN_NAME" "$PY" merge_equiv.py >> "$LOGDIR/merge-equiv-$RUN_NAME.log" 2>&1
echo "=== merge_equiv exit=$?" >> "$CHAIN"

echo "=== $(date -u +%FT%TZ) eval start" >> "$CHAIN"
RUN_NAME="$RUN_NAME" "$PY" eval_cyberguard.py >> "$LOGDIR/eval-$RUN_NAME.log" 2>&1
rc=$?
echo "=== eval exit=$rc" >> "$CHAIN"
echo "=== $(date -u +%FT%TZ) eval-chain done eval_exit=$rc" >> "$CHAIN"
