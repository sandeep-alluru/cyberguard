#!/bin/bash
# cyberguard-setup.sh — prepare clawersamurai6 to fine-tune the cyber-defence model.
#
# Host choice (measured, not assumed): samurai6 has 2x RTX 3090 both idle, 200 GB free on
# /data, and venvs/v2-fast already carries the full training stack (torch 2.9+cu128, peft,
# trl, unsloth, bitsandbytes). The Sparks have idle GB10s and more disk but NO peft/trl/
# unsloth at all, so they would need a training stack built from scratch.
#
# DISK DISCIPLINE: samurai6's root filesystem is 98% full (13 GB). Every cache and every
# artifact therefore lives on /data. Pointing HF_HOME at the default would fill root and
# kill the run partway.
#
# GPU: card 1. Card 0 is designated for the 27B agent by the Ornith programme's own goal.
set -euo pipefail

ROOT=/data/cyberguard
export HF_HOME=$ROOT/hf
export HF_HUB_CACHE=$ROOT/hf/hub
export PATH=$HOME/.local/bin:$PATH

echo "=== $(date -u +%FT%TZ) setting up $ROOT"
mkdir -p "$ROOT"/{data,models,adapters,gguf,receipts,logs,evals}
mkdir -p "$HF_HOME/hub"

# Persist the cache redirect so every later invocation, including systemd units, agrees.
if ! grep -q "HF_HOME=$ROOT/hf" "$HOME/.cyberguard-env" 2>/dev/null; then
  cat > "$HOME/.cyberguard-env" <<EOF
# cyber-defence model project — sourced by every step so caches never touch the full root
export CYBERGUARD_ROOT=$ROOT
export HF_HOME=$ROOT/hf
export HF_HUB_CACHE=$ROOT/hf/hub
export HF_HUB_ENABLE_HF_TRANSFER=0
export CYBERGUARD_GPU=1
export PATH=\$HOME/.local/bin:\$PATH
EOF
  echo "  wrote ~/.cyberguard-env"
fi
# shellcheck disable=SC1090
source "$HOME/.cyberguard-env"

echo "--- disk sanity"
df -h / "$ROOT" | sed 's/^/  /'
avail_root=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
if [ "${avail_root:-0}" -lt 5 ]; then
  echo "  WARNING: root has only ${avail_root}G; all writes must stay on $ROOT"
fi

echo "--- fetching dataset (Trendyol cybersecurity instruction tuning)"
hf download Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset \
  --repo-type dataset --local-dir "$ROOT/data/trendyol-cybersec" 2>&1 | tail -2

echo "--- dataset contents"
ls -la "$ROOT/data/trendyol-cybersec" | sed 's/^/  /'
for f in "$ROOT/data/trendyol-cybersec"/*.jsonl; do
  [ -f "$f" ] || continue
  echo "  $(basename "$f"): $(wc -l < "$f") rows, $(du -h "$f" | cut -f1)"
  echo "  sample row (first 400 chars):"
  head -c 400 "$f" | sed 's/^/    /'
  echo
done

echo "=== setup done $(date -u +%FT%TZ)"
