#!/bin/bash
# finish-cyberguard.sh — the post-training chain, end to end, on the control host.
#
# Sequence and why this order:
#   1. wait for the fine-tune to finish (its receipt file is the completion signal, not a
#      process check — a crashed run and a finished run must not look alike)
#   2. evaluate on the Spark while the GPU is free — eval generates, so it needs the GPU that
#      training just released
#   3. merge the LoRA and convert to GGUF on the Spark (CPU only; it has the python gguf
#      module but no llama-quantize)
#   4. fetch, quantise and serve locally on the 1080 Ti
#   5. register `cyberguard-local` in DSH — only AFTER the endpoint is live, because
#      registering a provider that points at nothing would be untidy
#
# Launch via ops/runjob.sh. Writes a step-by-step log so a partial chain is diagnosable.
set -u
HERE=/home/clawer-samurai-1/AgentHub/tessen/.runtime/spark-qwen
CG=$HOME/AgentHub/cyberguard
S4=clawerdigi2@spark-40ee
SSH="ssh -o BatchMode=yes -o ConnectTimeout=10"
RUN_NAME=${RUN_NAME:-cyberguard-lora-v1}
LOG=$CG/logs/finish-chain.log
mkdir -p "$CG/logs"
exec >>"$LOG" 2>&1
echo "############ finish-cyberguard chain start $(date -u +%FT%TZ) run=$RUN_NAME"

# --- 1. wait for the training receipt ---
echo "-- waiting for training to finish"
for i in $(seq 1 720); do   # up to 6 h at 30 s
  if $SSH "test -f ~/cyberguard/receipts/$RUN_NAME.json" 2>/dev/null; then
    echo "-- training receipt found at $(date -u +%FT%TZ)"
    break
  fi
  # surface progress occasionally
  if [ $((i % 20)) -eq 0 ]; then
    echo "   still waiting ($((i*30/60)) min) $(date -u +%FT%TZ)"
    $SSH "tr '\r' '\n' < ~/cyberguard/logs/train-$RUN_NAME.log 2>/dev/null | grep -oE \"\| +[0-9]+/[0-9]+ \[[0-9:]+<\" | tail -1" 2>/dev/null | sed 's/^/     step /'
  fi
  sleep 30
done
$SSH "test -f ~/cyberguard/receipts/$RUN_NAME.json" 2>/dev/null || {
  echo "ABORT: no training receipt after the wait window"; exit 0; }

echo "-- training receipt:"
$SSH "python3 -c \"
import json;d=json.load(open('/home/clawerdigi2/cyberguard/receipts/$RUN_NAME.json'))
print('  wallet_s',d.get('wall_seconds'),'train_loss',d.get('train_metrics',{}).get('train_loss'))
print('  rows_train',d.get('rows_train'),'rows_eval',d.get('rows_eval'))
\"" 2>&1 | sed 's/^/  /'

# --- 2. evaluation (uses the GPU training just freed) ---
echo "-- running evaluation at $(date -u +%FT%TZ)"
$SSH "source ~/.cyberguard-env; RUN_NAME=$RUN_NAME N_GEN=50 \$CYBERGUARD_VENV/bin/python ~/eval_cyberguard.py" 2>&1 | tail -12 | sed 's/^/  /'

# --- 3. merge + GGUF on the Spark (CPU) ---
echo "-- merging LoRA and converting to GGUF at $(date -u +%FT%TZ)"
$SSH "source ~/.cyberguard-env; RUN_NAME=$RUN_NAME bash ~/cyberguard-merge-gguf.sh" 2>&1 | tail -8 | sed 's/^/  /'

# --- 4. quantise + serve locally ---
echo "-- quantising and serving locally at $(date -u +%FT%TZ)"
bash "$CG/serve-cyberguard-local.sh" "$RUN_NAME" 2>&1 | tail -8 | sed 's/^/  /'

# --- 5. register in DSH (only if the endpoint answers) ---
if curl -sf --max-time 10 -H "Authorization: Bearer dummy" http://127.0.0.1:18081/v1/models >/dev/null 2>&1; then
  echo "-- endpoint live; registering in DSH at $(date -u +%FT%TZ)"
  python3 "$CG/register_cyberguard_dsh.py" --port 18081 --model-id cyberguard-4b 2>&1 | sed 's/^/  /'
else
  echo "-- SKIP registration: :18081 not answering, so we will not point DSH at nothing"
fi
echo "############ finish-cyberguard chain done $(date -u +%FT%TZ)"
exit 0
