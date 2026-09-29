#!/usr/bin/env bash
# early_learning_check.sh — close Codex review #14's evidence gap as soon as it CAN be closed.
#
# Review #14 accepted the repaired resume as trainable but withheld the learning claim:
#   "Actual learning remains UNVERIFIED; a nonzero optimizer-applied adapter-weight change from the preserved
#    parent settles whether updates occurred."
# The contract gates this at C24 (stage 0d), but the top-level adapter is not re-saved until the run stops at
# 12:02. The first step-500 checkpoint carries the same evidence hours earlier, so this waits for it and then
# reports both the weight delta and the gradient trace. Read-only with respect to the training run.
#
#   usage: bash v2/early_learning_check.sh [max_wait_minutes]
set -uo pipefail
WINDOW=$(date -d '2026-09-29 02:32:53' +%s)
MAX_MIN="${1:-300}"
ROOT="$HOME/AgentHub/cyberguard"
LOG="$ROOT/logs/early-learning-check.log"
say() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
HOSTS=("clawerdigi2@spark-40ee armA" "clawerdigi1@spark-8cf2 armB")

# A fresh checkpoint for one arm: its adapter_model.safetensors must postdate the repaired window.
fresh_checkpoint() {  # $1=host $2=arm -> prints the dir, or nothing
  timeout 60 ssh -o BatchMode=yes -o ConnectTimeout=10 "$1" "
    for d in \$(ls -dt ~/cyberguard/adapters/cyberguard-lora-v2-$2/checkpoint-* 2>/dev/null); do
      m=\$(stat -c %Y \"\$d/adapter_model.safetensors\" 2>/dev/null || echo 0)
      [ \"\$m\" -gt $WINDOW ] && { echo \"\$d\"; break; }
    done" 2>/dev/null
}

say "waiting for the first checkpoint written since $WINDOW (max ${MAX_MIN} min)"
deadline=$(( $(date +%s) + MAX_MIN * 60 ))
while :; do
  ready=1
  for spec in "${HOSTS[@]}"; do set -- $spec
    d=$(fresh_checkpoint "$1" "$2")
    [ -n "$d" ] || { ready=0; echo "  $2: no fresh checkpoint yet"; }
  done
  [ "$ready" = 1 ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { say "no fresh checkpoint within ${MAX_MIN} min — giving up"; exit 1; }
  sleep 300
done
say "fresh checkpoints present on both arms — running the learning proof"

for spec in "${HOSTS[@]}"; do set -- $spec; host=$1; arm=$2
  say "=== $arm ==="
  timeout 1800 ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" "
    cd ~/cyberguard
    d=\$(for c in \$(ls -dt adapters/cyberguard-lora-v2-$arm/checkpoint-* 2>/dev/null); do
          m=\$(stat -c %Y \"\$c/adapter_model.safetensors\" 2>/dev/null || echo 0)
          [ \"\$m\" -gt $WINDOW ] && { echo \"\$c\"; break; }
        done)
    echo \"  candidate: \$d (\$(stat -c %y \"\$d/adapter_model.safetensors\" | cut -d. -f1))\"
    \$HOME/venvs/sglang/bin/python v2/verify_resume_learning.py \
      --parent adapters/cyberguard-lora-v2-$arm.epoch1-final-bak --candidate \"\$d\" \
      --after $WINDOW --label '$arm-first-checkpoint' 2>&1 | tail -6
    echo -n '  grad_norm distinct values in log: '
    tr '\r' '\n' < logs/train-cyberguard-lora-v2-$arm.log | grep -a -o -E 'grad_norm.: .[0-9.]+' | sort -u | wc -l
    echo -n '  latest step: '
    tr '\r' '\n' < logs/train-cyberguard-lora-v2-$arm.log | grep -ao -E '[0-9]+/5068' | tail -1
  " 2>&1 | sed 's/^/  /' | tee -a "$LOG"
done
say "done"
