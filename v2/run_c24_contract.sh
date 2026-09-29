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

# ---------------------------------------------------------------- stage 00: wait for the trainers to exit
# Added 2026-09-29. Stages 0a/0c both need training to be OVER on both hosts: 0a rsyncs the adapter (a live
# trainer still writes adapter_model.safetensors, so the pull can capture a torn file of the right NAME and size
# - the completeness check on lines 40-42 would pass it), and 0c runs a MASK_PROOF that needs the GPU the
# trainer is holding. The contract was scheduled for 10:25 while the epoch boundary falls ~10:29, i.e. it would
# have pulled four minutes early. This waits, and FAILS LOUDLY rather than proceeding on a torn artefact: a
# contract that runs anyway produces a complete-looking verdict for an adapter that was never finished.
TRAINER_WAIT_MIN="${TRAINER_WAIT_MIN:-45}"
step 00 "wait for both trainers to exit (deadline ${TRAINER_WAIT_MIN} min)"
trainer_state() { # $1=host -> RUNNING | GONE | UNREACHABLE
  out=$(timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=10 "$1" \
        "pgrep -f '[t]rain_cyberguard\.py' >/dev/null 2>&1 && echo RUNNING || echo GONE" 2>/dev/null) || true
  echo "${out:-UNREACHABLE}"
}
waited=0
while :; do
  sa=$(trainer_state "$S4"); sb=$(trainer_state "$S8")
  echo "  t+${waited}s  armA@40ee=$sa  armB@8cf2=$sb"
  # A --dry-run is a plan preview, not an execution: it samples the gate once and continues, so previewing
  # cannot sit here for the whole deadline. The real run keeps the fail-closed wait below.
  [ "$DRY" = 1 ] && { echo "  DRY-RUN: sampling the gate once instead of waiting"; break; }
  [ "$sa" = GONE ] && [ "$sb" = GONE ] && break
  if [ "$sa" = UNREACHABLE ] || [ "$sb" = UNREACHABLE ]; then
    bad "a training host is UNREACHABLE - cannot prove training finished; not proceeding on an unverified adapter"
    exit 3
  fi
  if [ "$waited" -ge $((TRAINER_WAIT_MIN * 60)) ]; then
    bad "trainers still running after ${TRAINER_WAIT_MIN} min (armA=$sa armB=$sb) - refusing to evaluate a live adapter"
    echo "     raise TRAINER_WAIT_MIN or re-run once the runs have exited and written their receipts"
    exit 3
  fi
  sleep 60; waited=$((waited + 60))
done
# Say only what was observed. In a dry-run nothing has been proven to have exited, and printing "OK both
# trainers have exited" there would be exactly the kind of unearned success line this contract exists to avoid.
if [ "$DRY" = 1 ]; then
  echo "  DRY-RUN: trainer state sampled, not proven (armA=$sa armB=$sb) — the real run waits for GONE"
else
  ok "both trainers have exited"
fi
# Record what "exited" rests on, so the verdict cites evidence rather than a live process check that is gone by
# the time anyone reads it.
if [ "$DRY" != 1 ]; then
  mkdir -p v2/data/mixture
  { echo "{"
    echo "  \"checked_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"waited_seconds\": $waited,"
    for pair in "$S4 armA" "$S8 armB"; do set -- $pair; host=$1; arm=$2
      sha=$(timeout 60 ssh -o BatchMode=yes "$host" \
            "sha256sum ~/cyberguard/adapters/cyberguard-lora-v2-$arm/adapter_model.safetensors 2>/dev/null | cut -d' ' -f1" 2>/dev/null)
      mt=$(timeout 60 ssh -o BatchMode=yes "$host" \
            "stat -c %Y ~/cyberguard/adapters/cyberguard-lora-v2-$arm/adapter_model.safetensors 2>/dev/null" 2>/dev/null)
      echo "  \"${arm}_adapter_sha256\": \"${sha:-MISSING}\", \"${arm}_adapter_mtime\": ${mt:-0},"
    done
    echo "  \"trainer_process_gone_on_both\": true"
    echo "}"
  } > v2/data/mixture/trainer-exit.receipt.json
  ok "receipt v2/data/mixture/trainer-exit.receipt.json (adapter hashes as of exit)"
fi

# ---------------------------------------------------------------- stage 0pre: quarantine stale eval inputs
# The verdict layer classifies EVERY json in evals/, and `cyberguard-lora-v1.json` is a RECOGNISED name (the
# chain accepts `...-v1.json`, `...-armA.json`, `...-armB.json`, `...base.json`). Two Sep-27 v1 artifacts were
# still sitting in evals/ while this window's measurements are written THERE. Nothing guarantees a stale file
# is rejected rather than consumed, and "a measurement from a previous run" is not evidence about this one.
# So everything already present is archived (kept, never deleted) before any stage can write into evals/.
CONTRACT_START="${CONTRACT_START:-$(date +%s)}"
step 0pre "quarantine pre-existing evals/ inputs (the verdict must consume only this window's measurements)"
if [ -d evals ]; then
  stale=$(find evals -maxdepth 1 -name '*.json' -type f ! -newermt "@$CONTRACT_START" 2>/dev/null | wc -l)
  if [ "$stale" -gt 0 ]; then
    if [ "$DRY" = 1 ]; then
      echo "  DRY-RUN: would archive $stale pre-existing eval json(s):"
      find evals -maxdepth 1 -name '*.json' -type f ! -newermt "@$CONTRACT_START" -printf '    %p\n' 2>/dev/null
    else
      mkdir -p evals/.pre-c24-archive
      find evals -maxdepth 1 -name '*.json' -type f ! -newermt "@$CONTRACT_START" \
        -exec mv -t evals/.pre-c24-archive {} + 2>/dev/null \
        || { bad "could not quarantine stale eval inputs"; exit 2; }
      left=$(find evals -maxdepth 1 -name '*.json' -type f ! -newermt "@$CONTRACT_START" 2>/dev/null | wc -l)
      [ "$left" -eq 0 ] || { bad "quarantine incomplete: $left stale eval json(s) remain"; exit 2; }
      ok "archived $stale pre-existing eval json(s) into evals/.pre-c24-archive (kept, not deleted)"
    fi
  else
    ok "no pre-existing eval json to archive"
  fi
fi

# The HOSTS' evals/ directories get the same treatment, because stage 3 pulls battery receipts back with a NAME
# GLOB from them and a stale file whose name matches that glob would be consumed as this window's measurement.
# spark-40ee was found holding five stale files from 09-26/09-27 plus one of my own smoke artefacts.
for spec in "$S4" "$S8"; do
  echo "  ssh $spec: bash v2/quarantine_host_evals.sh"
  [ "$DRY" = 1 ] && continue
  timeout 300 rsync -a -e "ssh -o BatchMode=yes" v2/quarantine_host_evals.sh "$spec:~/cyberguard/v2/" 2>/dev/null \
    || { bad "could not install the host quarantine script on $spec"; exit 2; }
  q_out=$(timeout 300 ssh -o BatchMode=yes -o ConnectTimeout=10 "$spec" \
          "bash ~/cyberguard/v2/quarantine_host_evals.sh" 2>&1); q_rc=$?
  printf '%s\n' "$q_out"
  [ "$q_rc" = 0 ] || { bad "host evals quarantine failed on $spec"; exit 2; }
done

# ---------------------------------------------------------------- stage 0d: learning proof
# Codex review #14 (2026-09-29) accepted that the repaired resume is TRAINABLE (trainable params 66,060,288
# against the frozen run's 0) but refused to accept that it is LEARNING:
#   "Trainability restored is supported. Actual learning remains UNVERIFIED; a nonzero optimizer-applied
#    adapter-weight change from the preserved parent settles whether updates occurred."
# So it is settled here, before anything is evaluated. A candidate byte-identical to the parent it resumed
# from means no optimizer update was applied — either the frozen-run failure mode, or an adapter that was
# never re-saved — and in BOTH cases the "continuation" would be the epoch-1 artifact wearing a new mtime.
# The preserved parents (sha256 receipted in noop-resume.receipt.json) are the reference.
RESUME_WINDOW_EPOCH="${RESUME_WINDOW_EPOCH:-$(date -d '2026-09-29 02:32:53' +%s)}"
step 0d "learning proof (deliberately BEFORE the pull, so a stale adapter is caught without a 264 MB transfer)"
echo "  window start ${RESUME_WINDOW_EPOCH} ($(date -d @${RESUME_WINDOW_EPOCH} '+%F %T %Z'))"
for spec in "$S4 armA" "$S8 armB"; do set -- $spec; host=$1; arm=$2
  echo "  ssh $host: verify_resume_learning.py --parent $arm.epoch1-final-bak --candidate $arm"
  [ "$DRY" = 1 ] && continue
  # Capture the status of the REMOTE command, not of a downstream `tail` — piping would test tail's exit.
  rl_out=$(timeout 1800 ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" \
        "cd ~/cyberguard && \$HOME/venvs/sglang/bin/python v2/verify_resume_learning.py \
           --parent adapters/cyberguard-lora-v2-$arm.epoch1-final-bak \
           --candidate adapters/cyberguard-lora-v2-$arm \
           --after $RESUME_WINDOW_EPOCH --label $arm --out /tmp/rl-$arm.json" 2>&1)
  rl_rc=$?
  printf '%s\n' "$rl_out" | tail -8
  if [ "$rl_rc" != 0 ]; then
    bad "$arm: no optimizer-applied weight change since the parent (exit $rl_rc) — refusing to evaluate an"
    bad "     artifact that may never have trained (frozen resume, or an adapter that was not re-saved)"
    exit 4
  fi
  timeout 120 rsync -a -e "ssh -o BatchMode=yes" "$host:/tmp/rl-$arm.json" \
    "v2/data/mixture/resume-learning-$arm.receipt.json" 2>/dev/null \
    && ok "$arm: weights moved — receipt v2/data/mixture/resume-learning-$arm.receipt.json" \
    || bad "$arm: learning proof passed but its receipt did not arrive"
done

# ---------------------------------------------------------------- stage 0a: pull the adapters
# Added while preparing C24, because the contract as written could NOT have run: stages 1-2 (merge equivalence
# and the benchmark) execute LOCALLY, while the trained adapters exist only on the training hosts — so
# preflight would have reported "adapter missing" and exited 2, at 10:25 tomorrow, after 24 GPU-hours.
# --copy-links because HF checkpoints are symlink farms (an earlier rsync without it wrote an empty file whose
# sha256 was the empty-string hash). Intermediate `checkpoint-*` dirs are excluded: the shipped artifact is the
# top-level adapter, and the point of pulling is to evaluate THAT.
step 0a "pull the trained adapters from the hosts (the benchmark stages run locally)"
for spec in "$S4 armA" "$S8 armB"; do set -- $spec; host=$1; arm=$2
  dest="adapters/cyberguard-lora-v2-$arm"
  echo "  rsync -a --copy-links --exclude 'checkpoint-*' $host:~/cyberguard/$dest/ $dest/"
  [ "$DRY" = 1 ] && continue
  mkdir -p "$dest"
  timeout 1800 rsync -a --copy-links --exclude 'checkpoint-*' -e "ssh -o BatchMode=yes -o ConnectTimeout=10" \
    "$host:~/cyberguard/$dest/" "$dest/" || { bad "adapter pull failed for $arm"; exit 2; }
  for f in adapter_model.safetensors adapter_config.json; do
    [ -s "$dest/$f" ] || { bad "$arm adapter incomplete: $f missing (has training finished?)"; exit 2; }
  done
  sha=$(sha256sum "$dest/adapter_model.safetensors" | awk '{print $1}')
  echo "$sha" > "$dest/.sha256"
  ok "$arm adapter pulled — adapter_model.safetensors sha256 ${sha:0:16}…"
done

# ---------------------------------------------------------------- stage 0c: live loss-mask proof
# The trainer's MASK_PROOF mode asserts assistant-only supervision on a real collated batch and exits before any
# optimizer step. It was NEVER RUN for this window (zero "MASK PROOF" lines in either host's logs), so no captured
# evidence existed that the live loss mask was correct - an independent review's objection. It needs the GPU, so
# it runs HERE: after the trainers stop and before the evaluation takes the GPU.
step 0c "live loss-mask proof on both hosts (needs the GPU, so it runs after training stops)"
echo "  bash v2/verify_training_mask.sh   (MASK_PROOF=1; exits before any optimizer step)"
# Fail-CLOSED on the evidence, not on the environment: a substantive mask failure or a missing proof is
# recorded as a limitation the verdict must carry, but an SSH/model hiccup must not destroy the whole contract
# and with it the verdict. The receipt is what the verdict reads.
[ "$DRY" = 1 ] || { bash v2/verify_training_mask.sh > logs/mask-proof.log 2>&1 \
  && ok "MASK PROOF: PASS on both hosts (receipt v2/data/mixture/mask-proof.receipt.json)" \
  || { bad "mask proof not obtained - the verdict will record the loss mask as UNVERIFIED for this window"; } }

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
# Review F15: the driver once returned each G-B probe's GOLD LABEL as the prompt (and one fixed Sigma rule for
# all 60 G-E items), so those batteries would have scored the answer to nothing. This is machine-checked here
# because the defect was invisible to inspection: it lived in the real prompt path, not in the stubs.
# Round 54: the scoring dispatch is keyed on measurement family; when the fresh instruments were added their
# names matched no branch and each produced {"n": N} with no error at all. This check stub-runs every battery
# and asserts the family's fields are present - it would have caught that before C24.
SC=$(mktemp)
if python3 v2/run_battery.py --check-scoring >"$SC" 2>&1; then
  ok "every registered battery produces its family's score fields (14 checked)"
else
  bad "SCORING CHECK FAILED - batteries would produce empty receipts:"; grep -E 'FAIL|lack' "$SC" | head -8 | sed 's/^/        /'; PRE=$((PRE+1))
fi
rm -f "$SC"
DC=$(mktemp)
if python3 v2/run_battery.py --check-driver >"$DC" 2>&1; then
  ok "driver sends each probe's own frozen item text ($(grep -c 'distinct driver texts' "$DC") batteries checked)"
else
  bad "driver check FAILED — batteries would not measure the frozen items:"; sed 's/^/        /' "$DC"; PRE=$((PRE+1))
fi
rm -f "$DC"
# The local verdict chain must be able to DECIDE before the run starts: stages 4-6 are file transforms, and
# this session has already seen them emit 18 UNMEASURED rows while every stage printed OK. ~10 s, no GPU.
RS=$(mktemp)
if python3 v2/rehearse_c24_local.py >"$RS" 2>&1; then
  ok "local verdict chain rehearsed: it decides, binds identity, and rests no decision on unusable input"
else
  bad "local verdict-chain rehearsal FAILED:"; sed 's/^/        /' "$RS"; PRE=$((PRE+1))
fi
rm -f "$RS"
# Muse's objection (verified independently): the frozen batteries must be disjoint from the training data, or a
# gate measures memorisation. This is the check whose absence let 1,099/1,100 G-A probes be training rows.
CC=$(mktemp)
if python3 v2/battery_contamination_check.py >"$CC" 2>&1; then
  ok "batteries are prompt-disjoint from both training arms"
else
  bad "BATTERY CONTAMINATION — affected gates cannot be reported as capability:"; grep -E 'CONTAMINATED|RESULT|g[A-Z]' "$CC" | head -12 | sed 's/^/        /'; PRE=$((PRE+1))
fi
rm -f "$CC"
echo "  arms the trainers loaded (must match FACTS):"
for spec in "$S4 A" "$S8 B"; do set -- $spec
  L=$(timeout 60 ssh -o BatchMode=yes "$1" "grep -m1 'ARM MODE' ~/cyberguard/logs/train-cyberguard-lora-v2-arm$2.log" 2>/dev/null)
  echo "    $1: ${L:0:110}"
done
if [ "$PRE" = 0 ]; then ok "preflight passed"
elif [ "$DRY" = 1 ]; then
  bad "preflight found $PRE problem(s) — expected before C24 (the adapters are written when training ends)."
  echo "  Continuing in DRY-RUN so the plan can be previewed; the real run would stop here."
else
  bad "preflight failed ($PRE problem(s))"; exit 2
fi

# ---------------------------------------------------------------- stage 0b: sync the evaluation surface
# Added on the owner's instruction after a readiness audit of this path. Both eval scripts begin with
# `ROOT = Path(os.environ["CYBERGUARD_ROOT"])`, and that variable exists only via ~/.cyberguard-env on the
# HOSTS: this machine has no env file, no base-model weights, no peft/datasets, and a Pascal GPU that cannot do
# the bfloat16 both scripts request. So stages 1-2 run on the hosts. Verified absent there: the four scripts,
# and on spark-8cf2 the corpus as well (the corpus, 187 MB, exists only on spark-40ee).
step 0b "sync the evaluation surface to the hosts"
# verify_resume_learning.py is here because stage 0d calls it ON the hosts and runs before stage 3 syncs
# anything: without it a fresh host aborts the contract at the learning proof with a missing file.
# v2/*.py is every host-side scoring/authority module (run_battery, gate_scorers_v2, cap_scorers,
# build_mixture, build_refusal_set, cyberguard_contract, ...). attack-stix.json is the ATT&CK authority: without
# it the host's authority() is EMPTY and every legitimate technique citation scores as a hallucination. Both
# were missing on both hosts until 2026-09-29, when a host-side scorer selftest exposed it.
# scorer-authority.receipt.json is the DECLARED authority the host check compares against; without it the
# host cannot verify that its id-factuality table is the one the verdict assumes.
EVAL_FILES=(cyberguard_data.py eval_cyberguard.py merge_equiv.py run-eval-chain.sh
            v2/data/mixture/scorer-authority.receipt.json)
EVAL_MODULES=(v2/*.py)
EVAL_AUTHORITY=(v2/candidates/attack-stix.json)
for spec in "$S4" "$S8"; do
  echo "  rsync -aR ${EVAL_FILES[*]} v2/holdout500.jsonl $spec:~/cyberguard/"
  [ "$DRY" = 1 ] && continue
  timeout 600 rsync -aR -e "ssh -o BatchMode=yes" "${EVAL_FILES[@]}" "${EVAL_MODULES[@]}" \
    "${EVAL_AUTHORITY[@]}" v2/holdout500.jsonl "$spec:~/cyberguard/" \
    || { bad "sync to $spec failed"; exit 2; }
  ok "eval surface synced to $spec (incl. every v2/*.py module and the ATT&CK authority)"
done
[ "$DRY" = 1 ] || if ! timeout 60 ssh -o BatchMode=yes "$S8" \
     '[ -f ~/cyberguard/data/trendyol-cybersec/CyberSec-Dataset_escaped.jsonl ]'; then
  echo "  corpus missing on $S8 — copying from $S4 over the direct link"
  timeout 1800 ssh -o BatchMode=yes "$S8" \
    "rsync -a --copy-links -e 'ssh -o BatchMode=yes' $S4:~/cyberguard/data/trendyol-cybersec/ ~/cyberguard/data/trendyol-cybersec/" \
    || { bad "corpus copy to $S8 failed"; exit 2; }
  ok "corpus copied to $S8"
else
  ok "corpus already present on $S8"
fi

# Host prerequisites the expensive stages ASSUME. Added 2026-09-29 while pre-flighting the surface: nothing
# checked these in advance, so an unset CYBERGUARD_ROOT, an absent base model, a missing corpus, an
# unsupported bf16 or a full disk would only surface when stage 1 or 3 failed — after the training window had
# already been spent. Read-only, and safe to run while training continues.
for spec in "$S4" "$S8"; do
  echo "  ssh $spec: bash v2/check_eval_surface.sh"
  [ "$DRY" = 1 ] && continue
  # Capture the REMOTE status, not a downstream pipe's (testing `ssh | tail` tests tail).
  es_out=$(timeout 900 ssh -o BatchMode=yes -o ConnectTimeout=10 "$spec" \
           "bash ~/cyberguard/v2/check_eval_surface.sh" 2>&1); es_rc=$?
  printf '%s\n' "$es_out" | tail -14
  if [ "$es_rc" != 0 ]; then
    bad "eval surface incomplete on $spec — stage 1/3 would fail after the window is spent"
    exit 2
  fi
done

# ---------------------------------------------------------------- stage 1: merge equivalence + benchmark
step 1 "merge equivalence + paired benchmark, executed ON THE HOSTS (they own CYBERGUARD_ROOT, the model, the GPU)"
PIDS=()
for spec in "$S4 armA" "$S8 armB"; do set -- $spec; host=$1; arm=$2
  RUN="cyberguard-lora-v2-$arm"
  echo "  ssh $host: cd ~/cyberguard && N_GEN=500 RUN_NAME=$RUN bash run-eval-chain.sh"
  [ "$DRY" = 1 ] && continue
  # 12 h, not 7. Measured 2026-09-29: a 100-probe battery took 925 s WITH training contending for the GPU;
  # merge_equiv (200 loss rows, 100 generations, 100 teacher-forced rows) plus eval_cyberguard (500 generations
  # per model) is hours of GPU work, and a timeout here discards the whole window's evaluation.
  ( timeout 43200 ssh -o BatchMode=yes "$host" "cd ~/cyberguard && N_GEN=500 RUN_NAME=$RUN bash run-eval-chain.sh" \
      > "logs/eval-chain-$arm.log" 2>&1 ) &
  PIDS+=($!)
done
# both hosts run in parallel; the chain waits for each trainer to release its GPU before starting
[ "$DRY" = 1 ] || for p in "${PIDS[@]}"; do wait "$p" || true; done
# run-eval-chain.sh always exits 0 (it records the inner exit codes in its own log), so the ARTEFACTS are the
# evidence, not the exit status — the failure this replaces was a stage that "succeeded" while producing nothing.
for spec in "$S4 armA" "$S8 armB"; do set -- $spec; host=$1; arm=$2
  RUN="cyberguard-lora-v2-$arm"
  [ "$DRY" = 1 ] && continue
  for f in "evals/$RUN.json" "evals/merge-equiv-$RUN.json"; do
    timeout 900 rsync -a -e "ssh -o BatchMode=yes" "$host:~/cyberguard/$f" evals/ \
      || { bad "$arm: $f did not arrive from $host (did the chain run?)"; exit 3; }
  done
  ok "$arm: benchmark + merge-equivalence pulled from $host"
done

# ---------------------------------------------------------------- stage 2: verify the pulled artefacts
step 2 "verify the pulled artefacts are measurements, not stubs"
[ "$DRY" = 1 ] || python3 - <<'PY' || exit 4
import json, math, os, sys
for arm in ("armA", "armB"):
    run = f"cyberguard-lora-v2-{arm}"
    bench = f"evals/{run}.json"
    if not os.path.exists(bench) or os.path.getsize(bench) == 0:
        sys.exit(f"FATAL: {bench} missing or empty — the benchmark did not run")
    d = json.load(open(bench))
    if not isinstance(d.get("base"), dict) or not isinstance(d.get("tuned"), dict):
        sys.exit(f"FATAL: {bench} lacks base/tuned blocks; it is not an evaluator report")
    rows = d.get("held_out_rows") or (d.get("quality") or {}).get("held_out_rows")
    if not rows:
        sys.exit(f"FATAL: {bench} records no held_out_rows; an empty benchmark is not a measurement")
    # THE TUNED MODEL MUST ACTUALLY HAVE BEEN MEASURED. Found 2026-09-29 by testing the fallback path:
    # eval_cyberguard writes `"tuned": {"skipped": ...}` when no adapter is present, and `{"skipped": ...}` is
    # still a dict - so the block check above ACCEPTED a benchmark that measured no tuned model at all. Had the
    # adapter failed to load on a host, the entire evaluation would have scored the BASE model while the verdict
    # reported the tuned arms: a complete-looking result for an arm that was never evaluated.
    for side in ("base", "tuned"):
        blk = d.get(side)
        if not isinstance(blk, dict):
            sys.exit(f"FATAL: {bench} has no {side} block")
        if "skipped" in blk:
            sys.exit(f"FATAL: {bench} did not measure the {side} model ({blk['skipped']!r}) - the benchmark "
                     f"fell back to the base and would score the wrong model")
        loss = blk.get("held_out_loss")
        if not isinstance(loss, (int, float)) or not math.isfinite(float(loss)):
            sys.exit(f"FATAL: {bench} records no finite {side} held_out_loss ({loss!r})")
    # Parent identity (review #2 MAJOR 6): the benchmark's base model must be the one the arm was trained from,
    # as recorded by the trainer's own receipt. `None` means the receipt was unreadable, which is reported
    # rather than assumed, but a present-and-False value means the arm was evaluated against a different parent.
    pid = d.get("parent_identity") or {}
    if pid.get("match") is False:
        sys.exit(f"FATAL: {arm} was evaluated against a different base model than it was trained from: "
                 f"train={pid.get('train_base')!r} eval={pid.get('eval_base')!r}")
    if pid.get("match") is None:
        print(f"    WARNING: {arm} parent identity is UNVERIFIED (trainer receipt unreadable)")
    eq = f"evals/merge-equiv-{run}.json"
    if not os.path.exists(eq) or os.path.getsize(eq) == 0:
        sys.exit(f"FATAL: {eq} missing or empty — merge equivalence was not recorded")
    e = json.load(open(eq))
    # F19 remainder: recording a merge-equivalence report is not ACCEPTING it. Codex demonstrated that the
    # report builder wrote loss difference=100 and 999 mask mismatches without rejecting them, so the numbers
    # are enforced here: a merged adapter that does not behave like the unmerged one is not the shipped artifact.
    need = ("loss_delta", "gen_exact_mismatches")
    missing = [k for k in need if k not in e]
    if missing:
        sys.exit(f"FATAL: {eq} lacks {missing}; merge equivalence is not measurable from it")
    # Review F19 (pass eleven): NaN passed every comparison, so the stated tolerances were not enforced.
    if not math.isfinite(float(e["loss_delta"])):
        sys.exit(f"FATAL: {arm} loss_delta is not finite ({e['loss_delta']})")
    if float(e["loss_delta"]) > 0.02:
        sys.exit(f"FATAL: {arm} merged-vs-unmerged loss differs by {e['loss_delta']} (> 0.02)")
    # 2026-09-29 PRE-FLIGHT FINDING. Exact-token equality (and an F1 floor of 0.99) is NOT ACHIEVABLE for a
    # merged-vs-unmerged comparison in bf16: the two paths differ by construction, because merge_and_unload()
    # evaluates W+BA once in bf16 while the unmerged path evaluates x@W + (x@A)@B as separate bf16 ops, and a
    # greedy decode over MAX_NEW=256 amplifies any early flip into a wholly different string. Measured on
    # spark-40ee: loss_delta 0.0001, top-1 agreement 6/6, 5/6 sequences identical at 48 tokens, yet 4/4
    # differed at 256. Requiring zero mismatches would therefore abort this contract after the window had been
    # spent, on evidence that is an artefact of precision rather than of the merge. The gate is now the
    # measurement that IS sensitive to a wrong merge: does merging change the model's FIRST decision?
    # (0) THE DETERMINISTIC BASIS. Review #18 rejected every sampled behavioural basis, with an executed
    # counterexample that passed all of them, and it was right: no finite behavioural sample establishes
    # behavioural equivalence. What IS exactly decidable is whether merge_and_unload() produced the correct
    # WEIGHTS from the trained adapter, and that is checked here over every element of every adapted matrix:
    #     merged_weight  ==  base_weight + scaling * (B @ A)      in float32
    # Measured on the real adapter: max deviation 0.00195 over 3,633,315,840 elements across 252 matrices, and
    # the same measurement reports a target module never merged at 0.06354 -- 32.6x the deviation. The tolerance
    # is therefore set an order of magnitude BELOW the smallest defect it exists to catch, rather than fitted to
    # the observation.
    # GATED IN bf16 ULPs OF THE IDEAL MERGED VALUE, on a ROBUST statistic. The first version of this check used
    # an absolute tolerance of 0.01 and an absolute-error ratio; review #19 injected a REAL defect (adapter
    # contributions multiplied by 0.9) with a discrepancy of 0.00635 and it PASSED - the tolerance admitted the
    # very defect it existed to catch, while the resolution note claimed otherwise. The criterion is now
    # scale-free and its separation is measured, not asserted:
    #     correct merge                 0 of 3,633,315,840 elements beyond 2 ULP   (fraction 0)
    #     contributions mis-scaled 10%  fraction 0.2768 beyond 2 ULP
    #     a contribution dropped        fraction 0.8241 beyond 2 ULP
    # A FRACTION rather than a max, because max_ulp explodes on elements where the ideal merged value is ~0
    # (the controls reach ~1e26 ULP on those), so a single cancellation element could fail a max-based gate
    # spuriously. Rounding noise gives a fraction of 0; a systematic defect moves most elements at once.
    # GATED ON THE ELEMENT-WISE MAXIMUM, in literal bf16 ULP spacing of the ideal merged value. Review #20
    # broke the previous fraction-only gate by injecting a SPARSE defect: one weight replaced with 1024 was
    # DETECTED (4.2e6 ULP) but its exceedance fraction was 9.5e-7, below the 1e-6 threshold, so acceptance
    # discarded it - and at that threshold the criterion permitted 3,633 arbitrarily erroneous elements. #20 also
    # showed that `NaN > 2` is False, so an all-NaN merged model reported a fraction of 0 and passed.
    # The max has no sparse blind spot and no NaN blind spot, and it cannot fail spuriously: a correct merge
    # measured **0.5 ULP max over 3,633,315,840 elements**, which is the optimum for a correctly-rounded
    # operation, while a 10% mis-scaling measures 3.8e26 and a dropped contribution 3.8e27.
    for k in ("merge_weight_max_ulp", "merge_weight_elements", "merge_weight_nonfinite_elements",
              "merge_weight_nonfinite_comparisons", "merge_weight_any_nonfinite_module",
              "merge_weight_near_zero_elements", "merge_weight_near_zero_max_abs",
              "merge_weight_control_scale_0p9_max_ulp", "merge_weight_control_module_dropped_max_ulp"):
        if k not in e or e[k] is None:
            sys.exit(f"FATAL: {eq} records no {k} - the merge arithmetic is not checked by this artefact")
    mx, we = float(e["merge_weight_max_ulp"]), int(e["merge_weight_elements"])
    nf = int(e["merge_weight_nonfinite_elements"])
    if not math.isfinite(mx):
        sys.exit(f"FATAL: {arm} merge_weight_max_ulp is not finite ({e['merge_weight_max_ulp']}) - a non-finite "
                 f"comparison must never be readable as agreement")
    if we < 100000:
        sys.exit(f"FATAL: {arm} the weight-level check covered only {we} elements; it must be exhaustive")
    if nf != 0:
        sys.exit(f"FATAL: {arm} the merged model has {nf} non-finite weight(s); NaN compares False against every "
                 f"tolerance and would otherwise vanish from the exceedance count")
    # Review #21: a non-finite per-module COMPARISON could be discarded by the aggregate `max` (order-dependent
    # with NaN), so both the comparison-level count and a per-module finiteness flag are gated here.
    if int(e["merge_weight_nonfinite_comparisons"]) != 0 or bool(e["merge_weight_any_nonfinite_module"]):
        sys.exit(f"FATAL: {arm} {e['merge_weight_nonfinite_comparisons']} non-finite weight COMPARISON(s) "
                 f"(any_nonfinite_module={e['merge_weight_any_nonfinite_module']}) - a non-finite comparison must "
                 f"never be discarded before acceptance")
    # Near-zero (subnormal-scale) ideals are excluded from the ULP statistic and bounded absolutely instead,
    # because a ULP ratio is meaningless there. bf16's largest subnormal is ~1.2e-38.
    nz_abs = float(e["merge_weight_near_zero_max_abs"])
    if not math.isfinite(nz_abs) or nz_abs > 1e-38:
        sys.exit(f"FATAL: {arm} {e['merge_weight_near_zero_elements']} near-zero adapted weight(s) deviate by "
                 f"{nz_abs} in absolute terms (> 1e-38); the ULP statistic does not cover those elements")
    # NOTE ON WHAT THIS PROVES (review #21): a tolerance necessarily admits deviations below itself. The claim
    # this gate supports is therefore NOT "the merged weights are correct" but "every merged weight equals
    # base + scaling*(B@A) to within 2 bf16 ULP", with 0.5 ULP measured as shipped and controls at 4.1e36/4.1e37.
    if mx > 2.0:
        sys.exit(f"FATAL: {arm} the worst merged weight deviates from base + scaling*(B@A) by {mx:.6g} bf16 ULP "
                 f"over {we} elements. A correct merge measures 0.5 (half an ULP, the optimum for correct "
                 f"rounding); a 10% mis-scaling measures 3.8e26 and a dropped contribution 3.8e27")
    # The tolerance must never be readable without the separation that justifies it.
    csc, cdr = float(e["merge_weight_control_scale_0p9_max_ulp"]), float(e["merge_weight_control_module_dropped_max_ulp"])
    if not (math.isfinite(csc) and math.isfinite(cdr)) or min(csc, cdr) < 100.0:
        sys.exit(f"FATAL: {arm} the control defects do not separate from the tolerance (10%-scale {csc:.6g}, "
                 f"dropped {cdr:.6g} ULP); a tolerance whose separation is unmeasured is theatre")
    print(f"    weight-level: max {mx:.4f} of a bf16 ULP over {we} elements, {nf} non-finite "
          f"(controls: 10%-scale {csc:.3g} ULP, dropped {cdr:.3g} ULP)")

    # (b) SANITY, not the basis. Review #18: these can be passed by a defect, so they cannot establish
    # equivalence - they catch a grossly wrong model. Teacher-forced agreement over the assistant span.
    # the surface held_out_loss scores. The token sequence is fixed, so it is not subject to decoding chaos,
    # and it is sensitive to a change anywhere in the continuation.
    for k in ("tf_top1_agreement_rate", "tf_positions", "tf_negative_control_agreement_rate"):
        if k not in e or e[k] is None:
            sys.exit(f"FATAL: {eq} records no {k} - merge equivalence is not established by this artefact")
    tf = float(e["tf_top1_agreement_rate"])
    nc = float(e["tf_negative_control_agreement_rate"])
    pos = int(e["tf_positions"])
    if not (math.isfinite(tf) and math.isfinite(nc)):
        sys.exit(f"FATAL: {arm} teacher-forced agreement is not finite ({tf}, {nc})")
    if pos < 20000:
        sys.exit(f"FATAL: {arm} teacher-forced agreement rests on only {pos} positions; >=20000 required")
    # The threshold is GROUNDED, not fitted. Measured on the real adapter: merged-vs-unmerged 0.9882 over 3,389
    # positions, and the NEGATIVE CONTROL (merged vs the base model with the adapter disabled - what a dropped
    # merge, a wrong scale or wrong target modules would look like) 0.5996. 0.95 sits far below the equivalent
    # case and far above the non-equivalent one, and the separation itself is gated so a degenerate control
    # cannot make the floor meaningless.
    if tf < 0.95:
        sys.exit(f"FATAL: {arm} teacher-forced top-1 agreement {tf:.4f} < 0.95 over {pos} positions - that is "
                 f"a genuine merge defect, not arithmetic precision")
    if (tf - nc) < 0.20:
        sys.exit(f"FATAL: {arm} the merge is not clearly closer to the adapter path ({tf:.4f}) than to the base "
                 f"({nc:.4f}); separation {tf - nc:.4f} < 0.20 - the equivalence claim is not grounded")
    if int(e.get("tf_first_position_disagreements") or 0) != 0:
        sys.exit(f"FATAL: {arm} merged-vs-unmerged disagree at the FIRST supervised position on "
                 f"{e.get('tf_first_position_disagreements')} row(s) - a wrong merge changes the first decision")
    t1 = tf
    # Reported, never gated: how far bf16 rounding is amplified by the decoder over a full-length decode.
    # Recorded so the verdict states it instead of hiding it behind an equivalence claim.
    print(f"    reported, not gated: exact_mismatches={e['gen_exact_mismatches']}/{e.get('prompts_gen')} "
          f"f1_min={e.get('gen_self_f1_min')} f1_mean={e.get('gen_self_f1_mean')} "
          f"logit_rel_delta_mean={e.get('logit_rel_delta_mean')}")
    if int(e.get("prompts_gen") or 0) < 100:
        sys.exit(f"FATAL: {arm} merge equivalence rests on only {e.get('prompts_gen')} generated prompts; "
                 f">=100 is required so a zero-mismatch result is evidence")
    if int(e.get("rows_loss") or 0) < 100:
        sys.exit(f"FATAL: {arm} loss equivalence rests on only {e.get('rows_loss')} rows; >=100 required")
    print(f"  {arm}: held_out_rows={rows}  merge-equiv ACCEPTED (loss_delta={e['loss_delta']}, "
          f"teacher-forced top-1 agreement={t1:.4f} over {pos} positions, "
          f"negative control (base) {nc:.4f}, separation {t1 - nc:.4f})")
PY

# ---------------------------------------------------------------- stage 3: batteries, split across machines
step 3 "batteries (split: arm A on spark-40ee, arm B on spark-8cf2; base once, on spark-40ee)"
# every leg of this stage runs on a HOST: the adapters, the base-model weights and the bf16 GPUs are all there
# and none of them are here. The base side is shared, so it runs once and its receipts are copied back.
for b in gA gA2 gB gC gE gF gG-gsm8k gG-ifeval gJ fresh-gA fresh-gB fresh-gE fresh-gF fresh-gJ; do
  echo "  base@40ee : ssh spark-40ee: python3 v2/run_battery.py --battery $b --arm base --out evals"
done
for b in gA gA2 gB gC gE gF gG-gsm8k gG-ifeval gJ fresh-gA fresh-gB fresh-gE fresh-gF fresh-gJ; do
  echo "  armA@40ee : python3 v2/run_battery.py --battery $b --arm armA --adapter adapters/cyberguard-lora-v2-armA"
  echo "  armB@8cf2 : python3 v2/run_battery.py --battery $b --arm armB --adapter adapters/cyberguard-lora-v2-armB"
done
[ "$DRY" = 1 ] || {
  # the adapters and the GPU live on the hosts, so the arm batteries run THERE and the receipts come back
  for spec in "$S4 armA" "$S8 armB"; do set -- $spec; H=$1; ARM=$2
    echo "  --- $ARM on $H ---"
    # Three separate destinations, because a single rsync into v2/ FLATTENS the data files: the sets landed
    # in v2/probe-set-*.jsonl while the driver looks for v2/data/probe-set-*.jsonl (reproduced on both hosts:
    # FileNotFoundError on the first battery). Receipts travel with the sets, because load_probes refuses to run
    # a frozen set without its receipt.
    timeout 300 rsync -a -e "ssh -o BatchMode=yes" v2/data/probe-set-*.jsonl v2/data/probe-set-*.receipt.json \
      "$H:~/cyberguard/v2/data/" 2>/dev/null || { bad "rsync of probe sets+receipts to $H failed"; exit 5; }
    timeout 300 rsync -a -e "ssh -o BatchMode=yes" v2/run_battery.py v2/gate_scorers_v2.py \
      "cyberguard_contract.py" "cap_scorers.py" "$H:~/cyberguard/v2/" 2>/dev/null \
      || { bad "rsync of the driver to $H failed"; exit 5; }
    for b in gA gA2 gB gC gE gF gG-gsm8k gG-ifeval gJ fresh-gA fresh-gB fresh-gE fresh-gF fresh-gJ; do
      timeout 21600 ssh -o BatchMode=yes "$H" "source ~/.cyberguard-env; cd \$CYBERGUARD_ROOT && \
        \$CYBERGUARD_VENV/bin/python v2/run_battery.py --battery $b --arm $ARM \
        --adapter adapters/cyberguard-lora-v2-$ARM --out evals" > "logs/battery-$b-$ARM.log" 2>&1 \
        || { bad "$ARM battery $b failed on $H"; exit 5; }
    done
    timeout 600 rsync -a "$H:~/cyberguard/evals/battery-*-$ARM.json" evals/ 2>/dev/null \
      || { bad "could not copy $ARM battery receipts back"; exit 5; }
    ok "$ARM batteries complete and copied back"
  done
  # the shared base side: one run, ON A HOST, then the receipts are copied back. It used to run locally, which
  # cannot work for the same reason stages 1-2 moved: this machine has no base-model weights, no peft and no
  # bf16-capable GPU. Base is the reference for G-A/G-A2/G-G/G-J, so running it locally would have failed every
  # one of those gates after the arm batteries had already spent their GPU hours.
  H=$S4
  # BOTH the sets and their receipts: load_probes refuses to run a frozen set without its receipt, so
    # syncing only the .jsonl would have aborted the very first battery with "FATAL: no receipt".
    timeout 300 rsync -a -e "ssh -o BatchMode=yes" v2/data/probe-set-*.jsonl v2/data/probe-set-*.receipt.json \
    "$H:~/cyberguard/v2/data/" 2>/dev/null || { bad "rsync of probe sets+receipts to $H failed"; exit 5; }
  timeout 300 rsync -a -e "ssh -o BatchMode=yes" v2/run_battery.py v2/gate_scorers_v2.py \
    "cyberguard_contract.py" "cap_scorers.py" "$H:~/cyberguard/v2/" 2>/dev/null \
    || { bad "rsync of the driver to $H failed"; exit 5; }
  for b in gA gA2 gB gC gE gF gG-gsm8k gG-ifeval gJ fresh-gA fresh-gB fresh-gE fresh-gF fresh-gJ; do
    timeout 21600 ssh -o BatchMode=yes "$H" "source ~/.cyberguard-env; cd \$CYBERGUARD_ROOT && \
      \$CYBERGUARD_VENV/bin/python v2/run_battery.py --battery $b --arm base --out evals" \
      > "logs/battery-$b-base.log" 2>&1 || { bad "base battery $b failed on $H"; exit 5; }
  done
  timeout 600 rsync -a "$H:~/cyberguard/evals/battery-*-base.json" evals/ 2>/dev/null \
    || { bad "could not copy the base battery receipts back"; exit 5; }
  ok "base batteries complete on $H and copied back"
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
import json, sys
r = json.load(open("v2/gate-report-v2.json"))
print("  counts:", r["counts"])
# F19: a nonempty report is NOT a result. An aborted evaluation writes a single CONTRACT row, which the old
# check accepted (PASS+FAIL+UNMEASURED > 0). A contract must show real gate outcomes and no abort row.
if any(g["gate"] == "CONTRACT" for g in r["gates"]):
    sys.exit("FATAL: the verdict layer aborted; the report is not a contract")
decided = r["counts"]["PASS"] + r["counts"]["FAIL"]
if decided == 0:
    sys.exit("FATAL: no gate reached PASS or FAIL; an all-UNMEASURED report is not a contract")
# F18: a PASS or FAIL may not rest on a number produced outside this run. The assembler tags such gates, and
# the verdict layer turns them UNMEASURED - this is the end-to-end assertion that the tag survived the trip.
hist = [g["gate"] for g in r["gates"]
        if g.get("historical_input") and g["outcome"] in ("PASS", "FAIL")]
if hist:
    sys.exit(f"FATAL: {len(hist)} gate(s) decided on an input measured outside this run: {hist}")
# F17: a --stub chain may be reported but must never decide a gate; the assembler tags those inputs.
stub = [g["gate"] for g in r["gates"] if g.get("stub_input") and g["outcome"] in ("PASS", "FAIL")]
if stub:
    sys.exit(f"FATAL: {len(stub)} gate(s) decided on --stub outputs (no model was tested): {stub}")
# F17 identity: a gate that decided must be attributable to a tested checkpoint.
unbound = [g["gate"] for g in r["gates"] if g.get("unbound_identity") and g["outcome"] in ("PASS", "FAIL")]
if unbound:
    sys.exit(f"FATAL: {len(unbound)} gate(s) decided without a bound model identity: {unbound}")
ident = r.get("identity") or {}
if any(g["outcome"] in ("PASS", "FAIL") for g in r["gates"]) and not ident.get("has_adapter_hash"):
    sys.exit("FATAL: gates decided but no battery receipt recorded an adapter sha256")
# F17 closed end to end: the adapter the batteries ran must BE the adapter that is shipped. This is the
# comparison that makes the assembled verdict attributable to a checkpoint rather than to a claim.
import hashlib, os                                          # noqa: E402
hashes = ident.get("adapter_sha256") or []
arm = ident.get("arm")
shipped = f"adapters/cyberguard-lora-v2-{arm}/adapter_model.safetensors"
if hashes and os.path.exists(shipped):
    local = hashlib.sha256(open(shipped, "rb").read()).hexdigest()
    if local not in hashes:
        sys.exit(f"FATAL: the batteries ran adapter {[h[:16] for h in hashes]} but the shipped {arm} adapter "
                 f"hashes to {local[:16]} — the tested artifact is not the shipped artifact")
    print(f"  adapter identity: batteries and the shipped {arm} adapter agree ({local[:16]}…)")
elif hashes:
    sys.exit(f"FATAL: the batteries recorded adapter {[h[:16] for h in hashes]} but {shipped} is absent")
print(f"  identity: arm={arm} adapter_sha256={str(ident.get('adapter_sha256'))[:20]} "
      f"consistent={ident.get('consistent')} receipts={ident.get('receipts')}")
tagged = [g["gate"] for g in r["gates"] if g.get("historical_input")]
if tagged:
    print(f"  note: {len(tagged)} gate input(s) came from an earlier run and are reported UNMEASURED: {tagged}")
if len([g for g in r["gates"] if g["gate"] != "CONTRACT"]) < 14:
    sys.exit(f"FATAL: only {len(r['gates'])} gate rows; every gate must appear")
print(f"  contract accepted: {decided} decided, {r['counts']['UNMEASURED']} unmeasured")
PY
}

# ---------------------------------------------------------------- stage 6: the verdict document
step 6 "compose VERDICT-v2.md from the gate report and the harvest"
echo "  python3 v2/write_verdict_v2.py --report v2/gate-report-v2.json --evals evals --out docs/VERDICT-v2.md"
[ "$DRY" = 1 ] || {
  python3 v2/write_verdict_v2.py --report v2/gate-report-v2.json --evals evals \
    --out docs/VERDICT-v2.md > logs/verdict-doc.log 2>&1 \
    || { bad "the verdict document was not written (see logs/verdict-doc.log)"; exit 9; }
  [ -s docs/VERDICT-v2.md ] && ok "VERDICT-v2.md written ($(wc -c < docs/VERDICT-v2.md) bytes)" \
    || { bad "VERDICT-v2.md missing or empty"; exit 9; }
}

# ---------------------------------------------------------------- stage 7: harvest
step 7 "harvest with per-file sha256"
echo "  bash harvest-v2.sh   (prints HARVEST-COMPLETE only when every file is checksum-verified)"
[ "$DRY" = 1 ] || { bash harvest-v2.sh | tail -3 || { bad "harvest failed"; exit 8; }; }


echo
if [ "$DRY" = 1 ]; then echo "  DRY RUN complete — nothing was executed"; else echo "  C24 CONTRACT COMPLETE"; fi
