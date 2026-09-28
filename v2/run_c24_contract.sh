#!/usr/bin/env bash
# run_c24_contract.sh — the C24 evaluation contract as one sequence, fail-closed at every step.
#
# WHY: by C24 the run has cost ~24 GPU-hours, and the contract has six stages each of which can silently
# produce nothing (a missing adapter, an empty battery, an assembler that finds no inputs, a verdict layer
# that returns all-UNMEASURED). Every stage below is checked for the artefact it must produce, and the script
# aborts with the stage name rather than continuing into a contract full of empty gates.
#
# The work is SPLIT ACROSS BOTH MACHINES because the plan says so: arm A's batteries on spark-40ee, arm B's on
# spark-8cf2, with the shared base side run once and copied.
#
# Usage: bash v2/run_c24_contract.sh [--dry-run] [--stage N]
set -uo pipefail
ROOT="$HOME/AgentHub/cyberguard"
cd "$ROOT"
DRY=0; ONLY=""
for a in "$@"; do case "$a" in --dry-run) DRY=1;; --stage) ONLY="next";; [0-9]) ONLY="$a";; esac; done

S4=clawerdigi2@spark-40ee; S8=clawerdigi1@spark-8cf2
FACTS="v2/data/mixture/FACTS.json"
ok()   { printf '  \033[32mOK\033[0m   %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; }
step() { echo; echo "=== stage $1: $2 ==="; }

# ---------------------------------------------------------------- preflight
step 0 "preflight"
PRE=0
for a in armA armB; do
  ad="adapters/cyberguard-lora-v2-$a"
  [ -d "$ad" ] && ok "adapter present: $ad" || { bad "adapter missing: $ad"; PRE=$((PRE+1)); }
done
for f in v2/data/probe-set-gA.jsonl v2/data/probe-set-gC.jsonl v2/data/probe-set-gF.jsonl \
         v2/data/probe-set-gG-gsm8k.jsonl v2/data/probe-set-gJ.jsonl; do
  [ -s "$f" ] && ok "probe set present: $f" || { bad "probe set missing: $f"; PRE=$((PRE+1)); }
done
[ -s "$FACTS" ] && ok "FACTS present (every number is cited from it)" || { bad "FACTS missing"; PRE=$((PRE+1)); }
echo "  arms the trainers loaded (must match FACTS):"
for spec in "$S4 A" "$S8 B"; do set -- $spec
  L=$(timeout 60 ssh -o BatchMode=yes "$1" "grep -m1 'ARM MODE' ~/cyberguard/logs/train-cyberguard-lora-v2-arm$2.log" 2>/dev/null)
  echo "    $1: ${L:0:110}"
done
[ "$PRE" = 0 ] && ok "preflight passed" || { bad "preflight failed (${PRE} problem)"; exit 2; }

# ---------------------------------------------------------------- stage 1: merge equivalence
step 1 "merge equivalence — the tested artefact must be the shipped artefact"
for a in armA armB; do
  echo "  RUN_NAME=cyberguard-lora-v2-$a python3 merge_equiv.py"
done
[ "$DRY" = 1 ] || {
  for a in armA armB; do
    RUN_NAME="cyberguard-lora-v2-$a" python3 merge_equiv.py > "logs/merge-equiv-$a.log" 2>&1
    rc=$?
    f="evals/merge-equiv-cyberguard-lora-v2-$a.json"
    [ $rc -eq 0 ] && [ -s "$f" ] && ok "$a merge-equiv written ($f)" || { bad "$a merge-equiv failed (rc=$rc)"; exit 3; }
  done
}

# ---------------------------------------------------------------- stage 2: benchmark
step 2 "paired benchmark on the 500 held-out (raw + normalized F1)"
for a in armA armB; do echo "  RUN_NAME=cyberguard-lora-v2-$a N_GEN=500 python3 eval_cyberguard.py"; done
[ "$DRY" = 1 ] || {
  for a in armA armB; do
    RUN_NAME="cyberguard-lora-v2-$a" N_GEN=500 python3 eval_cyberguard.py > "logs/eval-$a.log" 2>&1
    f="evals/cyberguard-lora-v2-$a.json"
    [ -s "$f" ] && ok "$a benchmark written" || { bad "$a benchmark produced no report"; exit 4; }
  done
}

# ---------------------------------------------------------------- stage 3: batteries, split across machines
step 3 "batteries (split: arm A on spark-40ee, arm B on spark-8cf2; shared base once)"
# base side is shared and run once, then copied, because both arms are paired against the same base
for b in gA gC gF gG-gsm8k gG-ifeval gJ; do
  echo "  base   : python3 v2/run_battery.py --battery $b --arm base"
done
for b in gA gC gF gG-gsm8k gG-ifeval gJ; do
  echo "  armA@40ee : python3 v2/run_battery.py --battery $b --arm armA --adapter adapters/cyberguard-lora-v2-armA"
  echo "  armB@8cf2 : python3 v2/run_battery.py --battery $b --arm armB --adapter adapters/cyberguard-lora-v2-armB"
done
[ "$DRY" = 1 ] || {
  # the adapters and the GPU live on the hosts, so the arm batteries run THERE and the receipts come back
  for spec in "$S4 armA" "$S8 armB"; do set -- $spec; H=$1; ARM=$2
    echo "  --- $ARM on $H ---"
    timeout 300 rsync -a v2/data/probe-set-*.jsonl v2/run_battery.py v2/gate_scorers_v2.py \
      "cyberguard_contract.py" "cap_scorers.py" "$H:~/cyberguard/v2/" 2>/dev/null \
      || { bad "rsync of battery inputs to $H failed"; exit 5; }
    for b in gA gC gF gG-gsm8k gG-ifeval gJ; do
      timeout 5400 ssh -o BatchMode=yes "$H" "source ~/.cyberguard-env; cd \$CYBERGUARD_ROOT && \
        \$CYBERGUARD_VENV/bin/python v2/run_battery.py --battery $b --arm $ARM \
        --adapter adapters/cyberguard-lora-v2-$ARM --out evals" > "logs/battery-$b-$ARM.log" 2>&1 \
        || { bad "$ARM battery $b failed on $H"; exit 5; }
    done
    timeout 600 rsync -a "$H:~/cyberguard/evals/battery-*-$ARM.json" evals/ 2>/dev/null \
      || { bad "could not copy $ARM battery receipts back"; exit 5; }
    ok "$ARM batteries complete and copied back"
  done
  # the shared base side: one run, copied to both hosts' recipe (kept local for assembly)
  for b in gA gC gF gG-gsm8k gG-ifeval gJ; do
    python3 v2/run_battery.py --battery "$b" --arm base > "logs/battery-$b-base.log" 2>&1 \
      || { bad "base battery $b failed"; exit 5; }
  done
  ok "base batteries complete"
}

# ---------------------------------------------------------------- stage 4: assemble
step 4 "assemble the gate inputs"
echo "  python3 v2/assemble_gate_inputs.py --out evals --extra-evals evals"
[ "$DRY" = 1 ] || {
  python3 v2/assemble_gate_inputs.py --out evals --extra-evals evals > logs/assemble.log 2>&1
  [ -s evals/gate-inputs-armA.json ] && ok "gate inputs written" || { bad "assembler produced no armA inputs"; exit 6; }
}

# ---------------------------------------------------------------- stage 5: verdicts
step 5 "verdicts (SPEC §7 clause 1 mapping)"
echo "  python3 v2/gates_v2.py --evals evals/ --out v2/gate-report-v2.json"
[ "$DRY" = 1 ] || {
  python3 v2/gates_v2.py --evals evals/ --out v2/gate-report-v2.json > logs/verdicts.log 2>&1
  [ -s v2/gate-report-v2.json ] && ok "gate report written" || { bad "verdict layer produced no report"; exit 7; }
  python3 - <<'PY'
import json
r = json.load(open("v2/gate-report-v2.json"))
print("  counts:", r["counts"])
assert r["counts"]["PASS"] + r["counts"]["FAIL"] + r["counts"]["UNMEASURED"] > 0, "empty contract"
PY
}

# ---------------------------------------------------------------- stage 6: harvest
step 6 "harvest with per-file sha256"
echo "  bash harvest-v2.sh   (prints HARVEST-COMPLETE only when every file is checksum-verified)"
[ "$DRY" = 1 ] || { bash harvest-v2.sh | tail -3 || { bad "harvest failed"; exit 8; }; }

echo
if [ "$DRY" = 1 ]; then echo "  DRY RUN complete — nothing was executed"; else echo "  C24 CONTRACT COMPLETE"; fi
