#!/usr/bin/env bash
# checkpoint_metrics.sh — collect both arms' live metrics for a C8/C16/C24 checkpoint, with no interpretation.
#
# Why a script: the checkpoint brief must quote REALIZED exposure, not the plan's projection. The plan's basis
# is 0.968288 s/sample (FACTS.json, measured on v1); the v2 window measured 8.36 s/step = 0.523 s/sample. Both
# are printed side by side so the brief can state which number it is quoting.
#
# Usage: bash v2/checkpoint_metrics.sh [label]        e.g. C8, C16, C24
# Writes: research-tmp/checkpoints/<label>-metrics.json and prints a summary table.
set -uo pipefail
LABEL="${1:-snapshot}"
ROOT="$HOME/AgentHub/cyberguard"
OUT="$ROOT/research-tmp/checkpoints"
mkdir -p "$OUT"
S4=clawerdigi2@spark-40ee; S8=clawerdigi1@spark-8cf2
ROWS_PER_EPOCH=$(python3 -c "import json;print(json.load(open('$ROOT/v2/data/mixture/FACTS.json'))['epoch_rows_per_arm'])")
BASIS=$(python3 -c "import json;print(json.load(open('$ROOT/v2/data/mixture/FACTS.json'))['sec_per_sample'])")
REFUSAL_SLOTS=$(python3 -c "import json;print(json.load(open('$ROOT/v2/data/mixture/FACTS.json'))['refusal_slots'])")
UNIQUE=$(python3 -c "import json;print(json.load(open('$ROOT/v2/data/mixture/FACTS.json'))['refusal_unique_rows'])")

collect() {   # host, arm
  timeout 120 ssh -o BatchMode=yes "$1" "
    L=~/cyberguard/logs/train-cyberguard-lora-v2-arm$2.log
    bar=\$(tr '\r' '\n' < \$L | grep -E '%\|' | tail -1)
    steps=\$(echo \"\$bar\" | grep -oE '[0-9]+/5068' | tail -1 | cut -d/ -f1)
    rate=\$(echo \"\$bar\" | grep -oE '[0-9.]+s/it' | tail -1 | tr -d 's/it')
    etime=\$(echo \"\$bar\" | grep -oE '[0-9]+:[0-9]{2}(:[0-9]{2})?' | tail -1)
    alive=0; for p in /proc/[0-9]*; do e=\$(readlink -f \$p/exe 2>/dev/null)||continue; case \"\$e\" in *python*) ;; *) continue;; esac; while IFS= read -r -d '' a; do case \"\$a\" in */train_cyberguard.py) alive=1;; esac; done < \$p/cmdline 2>/dev/null; done
    util=\$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader 2>/dev/null | head -1 | tr -d ' %')
    echo \"{\\\"arm\\\":\\\"$2\\\",\\\"steps\\\":\${steps:-0},\\\"sec_per_step\\\":\${rate:-0},\\\"elapsed\\\":\\\"\${etime:-}\\\",\\\"trainer_alive\\\":\$alive,\\\"gpu_util\\\":\${util:-0}}\"
  " 2>/dev/null | tail -1
}

A=$(collect "$S4" A); B=$(collect "$S8" B)
python3 - "$LABEL" "$OUT" "$A" "$B" "$ROWS_PER_EPOCH" "$BASIS" "$REFUSAL_SLOTS" "$UNIQUE" <<'PY'
import json, sys, datetime
label, out, a, b = sys.argv[1:5]
rows, basis, slots, uniq = int(sys.argv[5]), float(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8])
A, B = json.loads(a), json.loads(b)
epoch_h = rows * float(basis) / 3600
def exposure(arm, measured_epoch_h):
    r = float(arm["sec_per_step"] or 0) / 16.0            # 16 samples per step (BATCH 2 x GRAD_ACC 8)
    if not r:
        return None
    steps_done = arm["steps"]
    samples = steps_done * 16
    return {
        "measured_sec_per_sample": round(r, 4),
        "samples_done": samples,
        "epochs_done": round(samples / rows, 4),
        "refusal_presentations_done": int(samples * slots / rows),
        "passes_per_unique_refusal_row": round(samples * slots / rows / uniq, 2),
        "projected_24h_samples": int(86400 / r),
        "projected_24h_epochs": round(86400 / r / rows, 3),
        "projected_24h_refusal_presentations": int(86400 / r * slots / rows),
    }
rep = {
    "label": label,
    "taken_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%FT%TZ"),
    "facts": {"rows_per_arm": rows, "declared_sec_per_sample": float(basis),
              "declared_epoch_hours": round(epoch_h, 2), "refusal_slots": slots, "unique_refusal_rows": uniq},
    "arms": {"A": A, "B": B},
    "exposure": {"A": exposure(A, epoch_h), "B": exposure(B, epoch_h)},
}
json.dump(rep, open(f"{out}/{label}-metrics.json", "w"), indent=2)
print(f"  {label}: A {A['steps']} steps @ {A['sec_per_step']}s/it alive={A['trainer_alive']} gpu={A['gpu_util']}% | "
      f"B {B['steps']} steps @ {B['sec_per_step']}s/it alive={B['trainer_alive']} gpu={B['gpu_util']}%")
for k in ("A", "B"):
    e = rep["exposure"][k]
    if e:
        print(f"    arm {k}: {e['samples_done']} samples = {e['epochs_done']:.3f} epoch | "
              f"{e['refusal_presentations_done']} refusal presentations | "
              f"24 h projection {e['projected_24h_epochs']:.2f} epochs, {e['projected_24h_refusal_presentations']} refusal presentations")
print(f"    (declared FACTS basis: {basis} s/sample -> epoch {epoch_h:.1f} h)")
PY
