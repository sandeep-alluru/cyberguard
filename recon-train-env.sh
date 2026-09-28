#!/bin/bash
# recon-train-env.sh — what can actually train here? Run on a candidate host.
# Reports each venv's stack, GPU state, and free disk on every mount, because a full root
# filesystem silently ruins a fine-tune halfway through.
set -u
echo "=== host: $(hostname)  $(date -u +%FT%TZ)"
echo "--- GPUs"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1 | sed 's/^/  /'
echo "--- disk (all real mounts)"
df -h --output=target,size,avail,pcent 2>/dev/null | grep -vE "tmpfs|udev|overlay|efivar" | sed 's/^/  /'
echo "--- venvs"
for v in "$HOME"/venvs/*/; do
  [ -d "$v" ] || continue
  n=$(basename "$v")
  py="$v/bin/python"
  if [ ! -x "$py" ]; then
    echo "  $n: no python binary"
    continue
  fi
  echo "  $n: $("$py" - <<'PY' 2>/dev/null || echo "(import failed)"
import importlib
out = []
for m in ("torch", "peft", "trl", "unsloth", "transformers", "datasets", "bitsandbytes"):
    try:
        mod = importlib.import_module(m)
        out.append(f"{m}={getattr(mod, '__version__', '?')}")
    except Exception:
        out.append(f"{m}=-")
print(" ".join(out))
PY
)"
done
echo "--- HF cache location (root may be full)"
echo "  HF_HOME=${HF_HOME:-unset}  HF_HUB_CACHE=${HF_HUB_CACHE:-unset}"
du -sh "$HOME/.cache/huggingface" 2>/dev/null | sed 's/^/  ~\/.cache\/huggingface: /'
