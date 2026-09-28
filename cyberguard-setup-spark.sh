#!/bin/bash
# cyberguard-setup-spark.sh — prepare spark-40ee to fine-tune the cyber-defence model.
#
# WHY THIS HOST: samurai6 was the obvious choice (2x 3090 idle, existing unsloth stack) but
# its /data filesystem is 100% INODE-exhausted (119264/119264, zero free) while blocks are
# only 57% used — so nothing new can be created there, and its root has 13 GB free which is
# far too little to hold a model plus checkpoints. Its other projects' data is not ours to
# delete. spark-40ee has 3.3 TB free, 249 M inodes at 1% used, an idle GB10, and a venv that
# already carries torch 2.13 + transformers + datasets.
#
# METHOD: LoRA in bf16 (NOT QLoRA). bitsandbytes has no reliable aarch64/Blackwell CUDA
# wheel, and 4-bit quantisation is unnecessary here — with gradient checkpointing a 4B LoRA
# needs roughly 20-25 GB, and the node has ~60 GB free after Flash-Next's RPC share.
set -euo pipefail

ROOT=$HOME/cyberguard
VENV=$HOME/venvs/sglang           # reuse: torch 2.13.0+cu130, transformers, datasets
export PATH=$HOME/.local/bin:$PATH
export HF_HOME=$ROOT/hf
export HF_HUB_CACHE=$ROOT/hf/hub

echo "=== $(date -u +%FT%TZ) setting up $ROOT on $(hostname)"
mkdir -p "$ROOT"/{data,models,adapters,gguf,receipts,logs,evals}
mkdir -p "$HF_HOME/hub"

if ! grep -q "CYBERGUARD_ROOT" "$HOME/.cyberguard-env" 2>/dev/null; then
  cat > "$HOME/.cyberguard-env" <<EOF
export CYBERGUARD_ROOT=$ROOT
export HF_HOME=$ROOT/hf
export HF_HUB_CACHE=$ROOT/hf/hub
export CYBERGUARD_VENV=$VENV
export CYBERGUARD_GPU=0
EOF
  echo "  wrote ~/.cyberguard-env"
fi
# shellcheck disable=SC1090
source "$HOME/.cyberguard-env"

echo "--- adding the training libraries to $VENV"
uv pip install --python "$VENV/bin/python" peft trl accelerate 2>&1 | tail -4
echo "--- stack check"
"$VENV/bin/python" - <<'PY'
import importlib
for m in ("torch", "transformers", "datasets", "peft", "trl", "accelerate"):
    try:
        mod = importlib.import_module(m)
        print(f"  {m}: {getattr(mod, '__version__', '?')}")
    except Exception as e:
        print(f"  {m}: MISSING ({str(e)[:60]})")
import torch
print("  cuda available:", torch.cuda.is_available(), "| device:", torch.cuda.get_device_name(0))
PY

echo "--- disk + memory headroom"
df -h "$ROOT" | tail -1 | sed 's/^/  /'
free -g | head -2 | sed 's/^/  /'

echo "--- dataset: Trendyol cybersecurity instruction tuning"
"$VENV/bin/hf" download Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset \
  --repo-type dataset --local-dir "$ROOT/data/trendyol-cybersec" 2>&1 | tail -2 || \
  hf download Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset \
  --repo-type dataset --local-dir "$ROOT/data/trendyol-cybersec" 2>&1 | tail -2

ls -la "$ROOT/data/trendyol-cybersec" | sed 's/^/  /'
for f in "$ROOT/data/trendyol-cybersec"/*.jsonl; do
  [ -f "$f" ] || continue
  echo "  $(basename "$f"): $(wc -l < "$f") rows, $(du -h "$f" | cut -f1)"
  echo "  first row (600 chars):"
  head -c 600 "$f" | sed 's/^/    /'
  echo
done

echo "=== setup done $(date -u +%FT%TZ)"
