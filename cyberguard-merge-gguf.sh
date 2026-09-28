#!/bin/bash
# cyberguard-merge-gguf.sh — turn the trained LoRA adapter into a servable GGUF.
# Run on spark-40ee (where the base model and adapter live) once training finishes.
#
# Pipeline: merge LoRA into the base weights -> convert to GGUF (bf16) -> quantise to
# Q4_K_M. The result is ~2.5 GB, small enough for the GTX 1080 Ti on this workstation, which
# is what makes the model "available for this machine" rather than only on a Spark.
#
# Refuses to run while training is still in flight: merging a half-written adapter would
# silently produce a broken model, and that failure would look like a training problem.
set -euo pipefail
source "$HOME/.cyberguard-env"
export PATH="$HOME/.local/bin:$PATH"
PY=$CYBERGUARD_VENV/bin/python
RUN_NAME=${RUN_NAME:-cyberguard-lora-v1}
ADAPTER="$CYBERGUARD_ROOT/adapters/$RUN_NAME"
# Artifact names carry RUN_NAME so a throwaway adapter (e.g. smoke-tb) cannot be mistaken
# for the real model.
MERGED="$CYBERGUARD_ROOT/models/$RUN_NAME-merged"
GGUF16="$CYBERGUARD_ROOT/gguf/$RUN_NAME-f16.gguf"
GGUFQ4="$CYBERGUARD_ROOT/gguf/$RUN_NAME-Q4_K_M.gguf"
LC=$HOME/llama.cpp
# Force CPU: the artifact merge does not need a GPU, and on this box the GPU is busy serving
# the 3-hour Flash-Next test. Contending for it would corrupt that measurement for no gain.
export CUDA_VISIBLE_DEVICES=""

echo "=== $(date -u +%FT%TZ) merge + convert $RUN_NAME"

# --- guard: no training in flight ---
n=0
for p in /proc/[0-9]*; do
  c=$(tr "\0" " " < "$p/cmdline" 2>/dev/null) || continue
  case "$c" in *train_cyberguard.py*) n=$((n+1));; esac
done
if [ "$n" -gt 0 ]; then echo "REFUSED: training still running ($n proc)"; exit 1; fi
[ -f "$ADAPTER/adapter_model.safetensors" ] || { echo "REFUSED: no adapter at $ADAPTER"; exit 1; }

# --- 1. merge LoRA into base ---
echo "--- merging LoRA into base"
"$PY" - "$CYBERGUARD_ROOT/models/Qwen3-4B-Instruct-2507" "$ADAPTER" "$MERGED" <<'PYEOF'
import sys, torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
base, adapter, out = sys.argv[1], sys.argv[2], sys.argv[3]
tok = AutoTokenizer.from_pretrained(base)
m = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.bfloat16)
m = PeftModel.from_pretrained(m, adapter)
m = m.merge_and_unload()
m.save_pretrained(out, safe_serialization=True)
tok.save_pretrained(out)
print("  merged ->", out)
PYEOF

# --- 2. GGUF conversion ---
echo "--- converting to GGUF"
[ -d "$LC" ] || { echo "  cloning llama.cpp"; git clone --depth 1 https://github.com/ggml-org/llama.cpp "$LC" >/dev/null 2>&1; }
mkdir -p "$CYBERGUARD_ROOT/gguf"
"$PY" "$LC/convert_hf_to_gguf.py" "$MERGED" --outfile "$GGUF16" --outtype bf16 2>&1 | tail -3

# --- 3. quantisation is deliberately NOT done here ---
# This node builds only llama-server and ggml-rpc-server — there is no llama-quantize binary.
# It has the python `gguf` module for conversion, but not the quantiser. Quantisation happens
# on the workstation (serve-cyberguard-local.sh), which has llama-quantize built. Attempting
# it here would emit a misleading warning and leave a 7.5 GB f16 artifact as "servable".
echo "--- skipping quantisation (no llama-quantize on this node; done on the workstation)"

echo "--- artifacts"
ls -la "$CYBERGUARD_ROOT/gguf" | sed 's/^/  /'
echo "  merged model: $(du -sh "$MERGED" | cut -f1)"
echo "  f16 gguf:     $GGUF16 ($(du -h "$GGUF16" | cut -f1))"
echo "  next step:    copy to clawer-samurai-1 and run serve-cyberguard-local.sh $RUN_NAME"
echo "=== done $(date -u +%FT%TZ)"
