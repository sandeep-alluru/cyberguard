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
EVAL_FILES=(cyberguard_data.py eval_cyberguard.py merge_equiv.py run-eval-chain.sh)
for spec in "$S4" "$S8"; do
  echo "  rsync -aR ${EVAL_FILES[*]} v2/holdout500.jsonl $spec:~/cyberguard/"
  [ "$DRY" = 1 ] && continue
  timeout 600 rsync -aR -e "ssh -o BatchMode=yes" "${EVAL_FILES[@]}" v2/holdout500.jsonl "$spec:~/cyberguard/" \
    || { bad "sync to $spec failed"; exit 2; }
  ok "eval surface synced to $spec"
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

# ---------------------------------------------------------------- stage 1: merge equivalence + benchmark
step 1 "merge equivalence + paired benchmark, executed ON THE HOSTS (they own CYBERGUARD_ROOT, the model, the GPU)"
PIDS=()
for spec in "$S4 armA" "$S8 armB"; do set -- $spec; host=$1; arm=$2
  RUN="cyberguard-lora-v2-$arm"
  echo "  ssh $host: cd ~/cyberguard && N_GEN=500 RUN_NAME=$RUN bash run-eval-chain.sh"
  [ "$DRY" = 1 ] && continue
  ( timeout 25200 ssh -o BatchMode=yes "$host" "cd ~/cyberguard && N_GEN=500 RUN_NAME=$RUN bash run-eval-chain.sh" \
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
import json, os, sys
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
    if float(e["loss_delta"]) > 0.02:
        sys.exit(f"FATAL: {arm} merged-vs-unmerged loss differs by {e['loss_delta']} (> 0.02)")
    if int(e["gen_exact_mismatches"]) != 0:
        sys.exit(f"FATAL: {arm} merged-vs-unmerged generations differ on "
                 f"{e['gen_exact_mismatches']} of {e.get('prompts_gen')} prompts")
    # F19: the F1 floor is UNCONDITIONAL (the reviewer showed an absent field was accepted), and the claim
    # must rest on real support - zero mismatches in five prompts has a ~45 % one-sided upper bound.
    if "gen_self_f1_min" not in e or e["gen_self_f1_min"] is None:
        sys.exit(f"FATAL: {eq} records no gen_self_f1_min; the F1 floor cannot be enforced")
    f1 = float(e["gen_self_f1_min"])
    if f1 < 0.99:
        sys.exit(f"FATAL: {arm} merged-vs-unmerged token-F1 floor {f1} < 0.99")
    if int(e.get("prompts_gen") or 0) < 100:
        sys.exit(f"FATAL: {arm} merge equivalence rests on only {e.get('prompts_gen')} generated prompts; "
                 f">=100 is required so a zero-mismatch result is evidence")
    if int(e.get("rows_loss") or 0) < 100:
        sys.exit(f"FATAL: {arm} loss equivalence rests on only {e.get('rows_loss')} rows; >=100 required")
    print(f"  {arm}: held_out_rows={rows}  merge-equiv ACCEPTED (loss_delta={e['loss_delta']}, "
          f"gen_mismatches={e['gen_exact_mismatches']}, self_f1_min={f1})")
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
      timeout 5400 ssh -o BatchMode=yes "$H" "source ~/.cyberguard-env; cd \$CYBERGUARD_ROOT && \
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
    timeout 5400 ssh -o BatchMode=yes "$H" "source ~/.cyberguard-env; cd \$CYBERGUARD_ROOT && \
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
