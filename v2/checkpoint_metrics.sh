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

probe_alive() {   # host -> 1 if a trainer process is live there, else 0
  timeout 60 ssh -o BatchMode=yes "$1" '
    alive=0
    for p in /proc/[0-9]*; do
      e=$(readlink -f $p/exe 2>/dev/null) || continue
      case "$e" in *python*) ;; *) continue;; esac
      while IFS= read -r -d "" a; do case "$a" in */train_cyberguard.py) alive=1;; esac; done < $p/cmdline 2>/dev/null
    done
    echo $alive
  ' 2>/dev/null | tail -1
}

# C24 IS THE END OF THE WINDOW, so its snapshot must be taken AFTER the trainers stop. The trainer enforces its own
# box (MAX_MINUTES=570 via a wall-clock TimeBox callback), which ends the run ~12:03, while the timeline's C24 step
# fires at 11:55 — so this snapshot would otherwise record a MOMENT INSIDE the run under a "the window closes"
# heading, reporting a step count ~60 steps short of the final one and disagreeing with the receipt-based numbers
# the verdict quotes. Polling here makes the snapshot the real end of the window. BOUNDED, and its timeout only
# warns: a trainer that never exits must not stall the timeline (the contract's stage 00 waits separately, and the
# contract is unconditional).
if [ "$LABEL" = "C24" ]; then
  WAIT_MIN="${C24_WAIT_MIN:-20}"
  _dl=$(( $(date +%s) + WAIT_MIN * 60 ))
  while :; do
    _a=$(probe_alive "$S4"); _b=$(probe_alive "$S8")
    # "0" is EXITED and "" is UNREACHABLE, and they must not be conflated: an unreachable host returns an empty
    # string, so a `!= 1` test would read a dead ssh connection as "the trainer has exited" and stop the wait with
    # a claim the evidence does not support. Only an explicit 0 on both hosts closes the window.
    _say() { case "$1" in 1) echo running ;; 0) echo exited ;; *) echo UNREACHABLE ;; esac; }
    echo "  [$(date +%T)] waiting for the window to close: armA=$(_say "$_a") armB=$(_say "$_b") (bounded ${WAIT_MIN} min)"
    if [ "$_a" = 0 ] && [ "$_b" = 0 ]; then
      echo "  both trainers have exited (both hosts reported 0) — this C24 snapshot IS the end of the window"
      break
    fi
    if [ "$(date +%s)" -ge "$_dl" ]; then
      echo "  WARNING: ${WAIT_MIN} min elapsed with a trainer still running — snapshotting anyway (a live trainer is"
      echo "  reported in the table below, and the brief states the snapshot time, so the record stays honest)"
      break
    fi
    sleep 30 & wait $!   # interruptible, so a stop signal is not deferred until the poll ends
  done
fi

A=$(collect "$S4" A); B=$(collect "$S8" B)

# The plan requires the Flash-Next serving stack EVICTED for the whole window (it is Restart=always and enabled,
# so a plain stop once brought it back mid-window holding ~50 GB per host). Nothing verified that between
# checkpoints: the eviction was confirmed by hand at C16. Since the checkpoints are exactly the 3-hourly cadence,
# the check belongs here — a resurrected serving stack is then caught within hours rather than at the contract,
# when it would compete for the GPU with the evaluation.
evict() {   # host -> {"port_8093":N,"active_units":"..."}
  timeout 120 ssh -o BatchMode=yes "$1" '
    l=$(ss -ltn 2>/dev/null | grep -c ":8093")
    act=""
    for u in spark-flash-next.service qwen-flash-guard.timer spark-rpc.service spark-rpc-guard.timer; do
      st=$(systemctl show -p ActiveState "$u" 2>/dev/null | head -1)
      case "$st" in *ActiveState=active*|*ActiveState=activating*) act="$act $u";; esac
    done
    echo "{\"port_8093\":${l:-0},\"active_units\":\"$act\"}"
  ' 2>/dev/null | tail -1
}
E4=$(evict "$S4"); E8=$(evict "$S8")
python3 - "$LABEL" "$OUT" "$A" "$B" "$ROWS_PER_EPOCH" "$BASIS" "$REFUSAL_SLOTS" "$UNIQUE" "$E4" "$E8" <<'PY'
import json, sys, datetime
label, out, a, b = sys.argv[1:5]
rows, basis, slots, uniq = int(sys.argv[5]), float(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8])
EV = {"spark-40ee": sys.argv[9] or "{}", "spark-8cf2": sys.argv[10] or "{}"}
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
# record the eviction state and SHOUT if the serving stack has come back
rep["eviction"] = {}
for _h, _raw in EV.items():
    try:
        rep["eviction"][_h] = json.loads(_raw)
    except Exception:                                              # noqa: BLE001
        rep["eviction"][_h] = {"error": "unreachable or malformed"}
_breach = [h for h, v in rep["eviction"].items()
           if isinstance(v, dict) and (v.get("port_8093") or v.get("active_units"))]
json.dump(rep, open(f"{out}/{label}-metrics.json", "w"), indent=2)
print(f"  {label}: A {A['steps']} steps @ {A['sec_per_step']}s/it alive={A['trainer_alive']} gpu={A['gpu_util']}% | "
      f"B {B['steps']} steps @ {B['sec_per_step']}s/it alive={B['trainer_alive']} gpu={B['gpu_util']}%")
if _breach:
    print(f"  !! EVICTION BREACH at {label}: " +
          "; ".join(f"{h} {rep['eviction'][h]}" for h in _breach) +
          " — the serving stack must stay evicted for the window and will compete for the GPU")
else:
    print(f"  eviction in force: both hosts report no 8093 listener and no active serving unit")
for k in ("A", "B"):
    e = rep["exposure"][k]
    if e:
        print(f"    arm {k}: {e['samples_done']} samples = {e['epochs_done']:.3f} epoch | "
              f"{e['refusal_presentations_done']} refusal presentations | "
              f"24 h projection {e['projected_24h_epochs']:.2f} epochs, {e['projected_24h_refusal_presentations']} refusal presentations")
print(f"    (declared FACTS basis: {basis} s/sample -> epoch {epoch_h:.1f} h)")
PY
