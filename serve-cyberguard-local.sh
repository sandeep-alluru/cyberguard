#!/bin/bash
# serve-cyberguard-local.sh — quantise and serve the fine-tuned model on THIS workstation.
#
# Why the split: spark-40ee can merge the LoRA and convert to GGUF (it has the python `gguf`
# module) but has NO llama-quantize binary built. This workstation has llama-quantize and
# llama-server built already, plus the GTX 1080 Ti that will serve the model. So the f16 GGUF
# is produced on the Spark and quantised + served here.
#
# Port 18081 sits next to the existing local router on 18080 so they cannot collide.
#
# Usage: serve-cyberguard-local.sh [RUN_NAME]      (default: cyberguard-lora-v1)
set -euo pipefail
RUN_NAME=${1:-${RUN_NAME:-cyberguard-lora-v1}}
LC=/mnt/purple4tb/gpu-work/build/llama.cpp/build/bin
ROOT=$HOME/AgentHub/cyberguard
GGUF_DIR=$ROOT/gguf
F16=$GGUF_DIR/$RUN_NAME-f16.gguf
Q4=$GGUF_DIR/$RUN_NAME-Q4_K_M.gguf
PORT=${PORT:-18081}
ALIAS=${ALIAS:-cyberguard-4b}
LOG=$ROOT/logs/serve-local.log
SRC=clawerdigi2@spark-40ee
SRC_DIR=/home/clawerdigi2/cyberguard/gguf

mkdir -p "$GGUF_DIR" "$ROOT/logs"
echo "=== $(date -u +%FT%TZ) quantise + serve local ($RUN_NAME)"

for b in llama-server llama-quantize; do
  [ -x "$LC/$b" ] || { echo "REFUSED: $b not built at $LC"; exit 1; }
done

# --- 1. fetch the f16 GGUF if we do not have it ---
if [ ! -s "$F16" ]; then
  echo "--- fetching f16 GGUF from $SRC"
  scp -q -o BatchMode=yes "$SRC:$SRC_DIR/$RUN_NAME-f16.gguf" "$F16" || {
    echo "REFUSED: could not fetch $RUN_NAME-f16.gguf (has the merge run?)"; exit 1; }
fi
echo "  f16: $(du -h "$F16" | cut -f1)"

# --- 2. quantise ---
if [ -s "$Q4" ]; then
  echo "--- Q4_K_M already present: $(du -h "$Q4" | cut -f1)"
else
  echo "--- quantising to Q4_K_M"
  "$LC/llama-quantize" "$F16" "$Q4" Q4_K_M 2>&1 | tail -6
fi
echo "  q4: $(du -h "$Q4" | cut -f1)"

# --- 3. serve ---
if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  echo "REFUSED: something is already listening on :$PORT"; exit 1
fi
echo "--- starting llama-server on :$PORT (GTX 1080 Ti)"
setsid nohup "$LC/llama-server" \
  -m "$Q4" \
  -c 8192 -n 2048 \
  --host 0.0.0.0 --port "$PORT" \
  --api-key dummy -a "$ALIAS" \
  -ngl 99 --jinja --metrics \
  --reasoning off --no-reasoning-preserve \
  >>"$LOG" 2>&1 </dev/null &

for i in $(seq 1 60); do
  sleep 5
  if curl -sf --max-time 5 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    echo "HEALTHY http://127.0.0.1:$PORT/v1  (alias: $ALIAS)"
    exit 0
  fi
done
echo "FAILED: no /health on :$PORT; log tail:"
tail -20 "$LOG"
exit 1
