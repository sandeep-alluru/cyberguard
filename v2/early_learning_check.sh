#!/usr/bin/env bash
# early_learning_check.sh — close Codex review #14's evidence gap as soon as it CAN be closed.
#
# Review #14 accepted the repaired resume as trainable but withheld the learning claim:
#   "Actual learning remains UNVERIFIED; a nonzero optimizer-applied adapter-weight change from the preserved
#    parent settles whether updates occurred."
# The contract already gates this at C24 (stage 0d), but the top-level adapter is not re-saved until the run
# stops at 12:02. The FIRST step-500 checkpoint gives the same evidence hours earlier, so this runs then and
# reports both the weight delta and the gradient trace. It is read-only with respect to the training run.
set -uo pipefail
WINDOW=$(date -d '2026-09-29 02:32:53' +%s)
LOG="$HOME/AgentHub/cyberguard/logs/early-learning-check.log"
say() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
say "waiting for the first checkpoint of the repaired run (window start $WINDOW)"
for spec in "clawerdigi2@spark-40ee armA" "clawerdigi1@spark-8cf2 armB"; do
  arm="${spec##* }"
  say "=== $arm ==="
  timeout 3600 ssh -o BatchMode=yes -o ConnectTimeout=10 "$spec" "
    cd ~/cyberguard
    W=$WINDOW
    newest=''
    for d in \$(ls -dt adapters/cyberguard-lora-v2-$arm/checkpoint-* 2>/dev/null); do
      m=\$(stat -c %Y \"\$d/adapter_model.safetensors\" 2>/dev/null || echo 0)
      if [ \"\$m\" -gt \"\$W\" ]; then newest=\"\$d\"; break; fi
    done
    if [ -z \"\$newest\" ]; then echo '  NO fresh checkpoint yet (none written since the window start)'; exit 7; fi
    echo \"  fresh checkpoint: \$newest (\$(stat -c %y \"\$newest/adapter_model.safetensors\" | cut -d. -f1))\"
    \$HOME/venvs/sglang/bin/python v2/verify_resume_learning.py \
      --parent adapters/cyberguard-lora-v2-$arm.epoch1-final-bak --candidate \"\$newest\" \
      --after \$W --label '$arm-first-checkpoint' 2>&1 | tail -6
    echo -n '  grad_norm distinct values in log: '
    tr '\r' '\n' < logs/train-cyberguard-lora-v2-$arm.log | grep -a -o -E \"grad_norm.: .[0-9.]+\" | sort -u | wc -l
    echo -n '  latest step: '; tr '\r' '\n' < logs/train-cyberguard-lora-v2-$arm.log | grep -ao -E '[0-9]+/5068' | tail -1
  " 2>&1 | sed 's/^/  /'
done
say "done"
