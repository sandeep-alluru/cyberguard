#!/usr/bin/env bash
# check_eval_surface.sh — runs ON a training host. Verifies every prerequisite the evaluation contract
# assumes, BEFORE the contract needs them.
#
# WHY. Stages 1-3 of the C24 contract run on the hosts (they own CYBERGUARD_ROOT, the bf16 GPU and the base
# weights). Nothing checked those prerequisites in advance: the contract only discovers a missing base model,
# an unset CYBERGUARD_ROOT, a full disk or an absent corpus when the expensive stage fails — after the
# training window has already been spent. This is cheap, read-only, and safe to run while training continues.
#
#   usage: bash v2/check_eval_surface.sh          (on the host)
#   exit 0 = every prerequisite present; 1 = something is missing (each item is printed)
set -uo pipefail
FAILS=0
ok()  { printf '  \033[32mOK\033[0m   %s\n' "$1"; }
bad() { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAILS=$((FAILS+1)); }
chk() { if [ "$1" = "yes" ]; then ok "$2"; else bad "$2"; fi; }

ROOT_HOME="$HOME/cyberguard"
echo "eval-surface check on $(hostname) ($(date '+%F %T %Z'))"

# The env file is how CYBERGUARD_ROOT reaches every eval script; both begin with
# `ROOT = Path(os.environ["CYBERGUARD_ROOT"])`, so an unset value is an immediate KeyError.
# shellcheck disable=SC1090
set -a; . "$HOME/.cyberguard-env" 2>/dev/null; set +a
CR="${CYBERGUARD_ROOT:-$ROOT_HOME}"
CV="${CYBERGUARD_VENV:-$HOME/venvs/sglang}"
# Everything below uses project-relative paths, and this script is invoked over ssh from an unspecified
# working directory (ssh lands in $HOME). Without this cd the authority check and the scorer selftest resolved
# against $HOME and failed for the wrong reason - caught by the positive control, not by reasoning.
cd "$CR" 2>/dev/null || { echo "  cannot cd into $CR"; exit 1; }
[ -n "$CR" ] && chk yes "CYBERGUARD_ROOT set ($CR)" || bad "CYBERGUARD_ROOT unset — every eval script raises KeyError on import"
[ -d "$CR" ] && chk yes "CYBERGUARD_ROOT exists" || bad "CYBERGUARD_ROOT=$CR is not a directory"
[ -x "$CV/bin/python" ] && chk yes "interpreter present ($CV/bin/python)" || bad "no interpreter at $CV/bin/python"

PY="$CV/bin/python"
[ -x "$PY" ] && "$PY" -c 'import torch, transformers, peft, datasets' 2>/dev/null \
  && chk yes "torch/transformers/peft/datasets import" || bad "python deps do not import"

[ -d "$ROOT_HOME/models/Qwen3-4B-Instruct-2507" ] \
  && chk yes "base model present" || bad "base model missing: $ROOT_HOME/models/Qwen3-4B-Instruct-2507"
[ -f "$ROOT_HOME/data/trendyol-cybersec/CyberSec-Dataset_escaped.jsonl" ] \
  && chk yes "corpus present" || bad "corpus missing (G-G's reachable floor needs it)"
for f in cyberguard_data.py eval_cyberguard.py merge_equiv.py run-eval-chain.sh v2/holdout500.jsonl \
         v2/run_battery.py v2/gate_scorers_v2.py v2/verify_resume_learning.py; do
  [ -f "$ROOT_HOME/$f" ] || bad "eval file missing: $f"
done
[ -f "$ROOT_HOME/v2/run_battery.py" ] && ok "eval files present (stage 0b sync done)"

# SYNTAX BY COMPILATION, not by parsing. Found 2026-09-29: `ast.parse` ACCEPTED a module with a top-level `return`
# — grammar is valid, and "'return' outside function" is raised at COMPILE time — so the syntax check this project
# had been using was blind to that whole class, and a break of exactly that kind reached the verdict composer and
# was caught by the rehearsal rather than by the check. These scripts run unattended for hours on this host, so
# every evaluation script is compiled here, before stage 1's benchmark and stage 3's batteries: a compile-time
# error now costs a preflight, not a spent window.
# REQUIRED must exist AND compile (the contract runs them on this host after training). IF_PRESENT are compiled
# only when present: v2/assemble_gate_inputs.py and v2/gates_v2.py run LOCALLY, and the trainer is already done by
# stage 0b, so their absence here is not a contract failure and must not abort stage 0b (which exits 2 on any bad).
COMPILE_FAIL=""; COMPILE_MISSING=""
for f in eval_cyberguard.py merge_equiv.py cyberguard_contract.py cyberguard_data.py \
         v2/run_battery.py v2/gate_scorers_v2.py; do
  [ -f "$f" ] || { COMPILE_MISSING="$COMPILE_MISSING $f"; continue; }
  "$PY" -c 'import sys; compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")' "$f" 2>/dev/null \
    || COMPILE_FAIL="$COMPILE_FAIL $f"
done
# SHELL, not Python: `run-eval-chain.sh` is the host-side chain that invokes the two Python steps, and compiling a
# shell script as Python fails by definition - which is exactly what the first version of this gate did, reporting
# a "compile-time error" in a file that was fine. Its syntax is checked the way shell syntax should be.
if [ -f run-eval-chain.sh ]; then
  bash -n run-eval-chain.sh 2>/dev/null || COMPILE_FAIL="$COMPILE_FAIL run-eval-chain.sh(bash -n)"
else
  COMPILE_MISSING="$COMPILE_MISSING run-eval-chain.sh"
fi
for f in train_cyberguard.py v2/assemble_gate_inputs.py v2/gates_v2.py v2/verify_resume_learning.py; do
  [ -f "$f" ] || continue
  "$PY" -c 'import sys; compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")' "$f" 2>/dev/null \
    || COMPILE_FAIL="$COMPILE_FAIL $f"
done
# An ABSENT script is reported, not skipped: the first version of this check used `[ -f "$f" ] || continue`, so a
# script the contract needs could be missing entirely and the check would still print OK.
[ -z "$COMPILE_MISSING" ] || bad "host-side script(s) ABSENT, and the contract runs them here:$COMPILE_MISSING"
[ -z "$COMPILE_FAIL" ] || bad "compile-time error in:$COMPILE_FAIL - the contract would fail hours in, not here"
if [ -z "$COMPILE_FAIL" ] && [ -z "$COMPILE_MISSING" ]; then
  ok "every host-side script present and compiling (benchmark, merge, contract module, data, chain, battery, scorers)"
fi

# Batteries write many thousands of generations; a full disk mid-contract loses the whole run.
FREE_GB=$(df -BG --output=avail "$ROOT_HOME" | tail -1 | tr -dc '0-9')
[ "${FREE_GB:-0}" -ge 60 ] && chk yes "disk free ${FREE_GB} GB (>= 60 GB)" \
  || bad "disk free ${FREE_GB:-?} GB — too low for the battery outputs and adapters"

if [ -x "$PY" ]; then
  "$PY" - <<'PY' || FAILS=$((FAILS+1))
import sys
try:
    import torch
except Exception as e:
    print(f"  \033[31mFAIL\033[0m torch: {e}"); sys.exit(1)
if not torch.cuda.is_available():
    print("  \033[31mFAIL\033[0m CUDA not available"); sys.exit(1)
ok_bf16 = torch.cuda.is_bf16_supported()
free = torch.cuda.mem_get_info()[0] / 1e9
tag = "\033[32mOK\033[0m  " if ok_bf16 else "\033[31mFAIL\033[0m"
print(f"  {tag} GPU {torch.cuda.get_device_name(0)}: bf16={ok_bf16}, free={free:.1f} GB")
sys.exit(0 if ok_bf16 else 1)
PY
fi

# ---------------------------------------------------------------- the window's GPU premise
# The plan's whole premise is a DEDICATED GPU for this window, and the serving stack must stay evicted for its
# duration. Nothing checked either during the window. On 2026-09-29 an orphaned base-battery process (left by a
# killed smoke test) was found holding 7.8 GB alongside the trainer - exactly the kind of stray the evaluation
# would have contended with or OOM'd on. This runs at stage 0b, i.e. after the trainers have exited and before
# any evaluation takes the GPU, when ZERO compute processes is the correct state.
LISTEN=$(ss -ltn 2>/dev/null | grep -c ':8093')
[ "$LISTEN" -eq 0 ] && chk yes "port 8093 has no listener (serving evicted)" \
  || bad "port 8093 IS listening - the serving stack is back and will compete for the GPU"
for u in spark-flash-next.service qwen-flash-guard.timer spark-rpc.service spark-rpc-guard.timer; do
  st=$(systemctl show -p ActiveState "$u" 2>/dev/null | head -1)
  case "$st" in
    *not-found*|*ActiveState=inactive*|*ActiveState=failed*|"") ;;
    *) bad "$u is $st — the serving stack must stay evicted for this window" ;;
  esac
done
chk yes "serving units inactive (eviction in force)"
gpu_pids=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | tr -d ' ' | grep -v '^$' || true)
if [ -z "$gpu_pids" ]; then
  chk yes "no process holds the GPU (it is free for the evaluation)"
else
  # The ALLOW_GPU_PIDS escape hatch used to be applied AFTER the failure had been recorded: it printed
  # "pid N explicitly allowed" as an OK line while FAILS was already incremented, so the check still failed and
  # the allow-list did nothing. Nothing sets that variable today, which is why it went unnoticed - but an
  # operator who set it to let a known-good process stay resident would have found the check failing anyway,
  # under a log line saying the pid was allowed. The list is now applied BEFORE the decision, and the default
  # stays strict: with no allow-list, any process holding the GPU fails this check.
  unallowed=""
  for pp in $gpu_pids; do
    case " ${ALLOW_GPU_PIDS:-} " in *" $pp "*) ;; *) unallowed="$unallowed $pp" ;; esac
  done
  if [ -z "$unallowed" ]; then
    ok "GPU is held only by explicitly allowed pid(s):${ALLOW_GPU_PIDS}"
  else
    bad "GPU is NOT free — process(es) holding it that are not allowed:"
    for pp in $unallowed; do
      echo "         pid $pp: $(tr '\0' ' ' < /proc/$pp/cmdline 2>/dev/null | cut -c1-90)"
    done
  fi
fi

# ---------------------------------------------------------------- the scoring authority
# The authority decides whether a cited ATT&CK technique id is REAL. FOUND 2026-09-29: attack-stix.json (the
# 53.8 MB MITRE STIX export) and build_mixture.py were absent on BOTH hosts, so authority() returned empty and
# every legitimate citation would have scored as a hallucination - a false failure in the strict direction,
# which is precisely "the direction that manufactures failures" per this module's own note. gate_scorers_v2
# --selftest FAILED on the hosts while passing locally, and nothing checked the host copy until now: the
# contract ran its driver/scoring checks LOCALLY, while the scoring that produces the verdict happens HERE.
STIX_PATH="${STIX_PATH:-v2/candidates/attack-stix.json}"
[ -f "$STIX_PATH" ] && chk yes "scoring authority present ($STIX_PATH)" \
  || bad "scoring authority missing: $STIX_PATH - every cited ATT&CK id would score as a hallucination"
# The declared authority is a RECEIPT, not an assumption: the host's authority must match it exactly, or the
# verdict's id-factuality numbers were produced against a different table. A count-only check would not catch a
# silently stale STIX file, so the sha256 is compared too.
AUTH_REC="v2/data/mixture/scorer-authority.receipt.json"
if [ -f "$AUTH_REC" ] && [ -f "$STIX_PATH" ]; then
  want_sha=$(python3 -c "import json;print(json.load(open('$AUTH_REC'))['stix_sha256'])" 2>/dev/null)
  want_cnt=$(python3 -c "import json;print(json.load(open('$AUTH_REC'))['valid'],json.load(open('$AUTH_REC'))['deprecated'])" 2>/dev/null)
  got_sha=$(sha256sum "$STIX_PATH" 2>/dev/null | cut -d' ' -f1)
  if [ "$want_sha" = "$got_sha" ]; then
    chk yes "authority file matches the declared receipt (sha256 ${got_sha:0:16})"
  else
    bad "authority file sha256 ${got_sha:0:16} != declared ${want_sha:0:16} — the verdict's id numbers would rest on a different table"
  fi
else
  bad "authority receipt missing ($AUTH_REC) — the scoring authority is unverifiable on this host"
fi
if [ -x "$PY" ]; then
  auth=$("$PY" - "$STIX_PATH" <<'PYAUTH' 2>&1
import sys
sys.path.insert(0, "v2")
try:
    import gate_scorers_v2 as GS
    v, d = GS.authority(sys.argv[1])
except Exception as e:
    print(f"ERROR {type(e).__name__}: {e}")
    sys.exit(1)
if len(v) + len(d) < 800:
    print(f"TOO SMALL: only {len(v)+len(d)} known ids - the STIX export did not load")
    sys.exit(1)
print(f"valid={len(v)} deprecated={len(d)}")
PYAUTH
) || true
  case "$auth" in
    valid=*) chk yes "scoring authority loaded (${auth})";;
    *)       bad "scoring authority did not load: ${auth:-empty}" ;;
  esac
  st=$("$PY" v2/gate_scorers_v2.py --selftest 2>&1 | tail -1)
  case "$st" in
    *PASS*) chk yes "scorer selftest on this host: $(echo "$st" | tr -s ' ')";;
    *)      bad "scorer selftest on this host: ${st:-no output}" ;;
  esac
  # The battery driver and the family scoring dispatch, run against THIS host's copies. The contract checks
  # these locally, which is how a host-side divergence (the empty authority above) went unnoticed: the modules
  # that produce the verdict's numbers are these, here.
  for probe in --check-driver --check-scoring; do
    out=$("$PY" v2/run_battery.py "$probe" 2>&1 | tail -1)
    case "$out" in
      *PASS*) chk yes "run_battery $probe on this host";;
      *)      bad "run_battery $probe on this host: ${out:-no output}" ;;
    esac
  done
fi

echo
if [ "$FAILS" -eq 0 ]; then echo "EVAL SURFACE: PASS on $(hostname)"; exit 0; fi
echo "EVAL SURFACE: FAIL on $(hostname) — $FAILS problem(s) above"; exit 1
