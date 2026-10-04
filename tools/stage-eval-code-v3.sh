#!/usr/bin/env bash
# stage-eval-code-v3.sh — push the CORRECTED eval code to the training host, hash-verified.
#
# Why this exists: the section 8 batteries must run on the host (that is where the GPU and the adapter
# are), but the host holds a STALE copy of the eval chain. Verified 2026-09-30:
#     v2/run_battery.py            local d5db85dee4f2  host 36aece11dfd6
#     v2/gate_scorers_v2.py        local ff9ad72118eb  host 968f91bd0058
#     v2/assemble_gate_inputs.py   local 65c53fa99ac1  host 6b4387e81622
# and none of the new evaluators exist there at all. Running the eval without this step would score the
# adapter with the OLD evaluators: the bootstrap G-A (whose polarity cycle 3 proved inverted), the
# assembler that crashes when no battery receipts are present, and a battery that never passes NVD
# authority (so G-C could never reach its support floor). The verdict would be wrong or missing for
# reasons that have nothing to do with the model.
#
# Same discipline as tools/stage-v3.sh: ONE FILE PER TRANSFER, then compare the DEPOSITED copy's sha256
# against the local one (CRAFT-O-05: a multi-path transfer can silently move nothing). DRY RUN BY
# DEFAULT -- pass --execute.
#
# Usage: bash tools/stage-eval-code-v3.sh [--execute]
set -uo pipefail
HOST="${HOST:-clawerdigi2@spark-40ee}"
DRY=1
[ "${1:-}" = "--execute" ] && DRY=0
cd "$HOME/AgentHub/cyberguard" || exit 1

FILES=(
  # cyberguard_contract.py carries the refusal vocabulary, the substantiveness thresholds AND the
  # ship_verdict() joint rule. The 4.10 fail-open fix lives here, and v2/run_battery.py now imports it,
  # so leaving it unstaged shipped a stale contract while shipping the code that depends on it.
  "cyberguard_contract.py"
  # v2/write_verdict_v2.py is stage 5b of the runbook and is invoked with HOST paths, so it must be
  # present on the host AND current: without --version v3 support there, the composer would cite v2's
  # adapter and mixture as the v3 verdict (Astra readiness review, defect 3).
  "v2/write_verdict_v2.py"
  # The v3 mixture identity the composer reads. Was absent from the host entirely, so a v3 verdict
  # would have had no mixture facts to cite.
  "v3/data/mixture/FACTS.json"
  "v2/run_battery.py"
  "v2/gate_scorers_v2.py"
  "v2/assemble_gate_inputs.py"
  "v2/gates_v2.py"
  # eval_cyberguard.py holds the shared generation surface. The G-B ranking path adds
  # generate_batch_scored/triage_score_from_logits there; omitting it would leave the host decoding
  # WITHOUT score capture, so G-B would silently report the ranking requirement UNMEASURED.
  "eval_cyberguard.py"
  "tools/ga_evaluator_v3.py"
  "tools/gate_86_heldout.py"
  "tools/gd_span_scorer_v3.py"
  "tools/audit_gate_attainability.py"
  # DEPENDENCIES of the evaluators above. Missing these was caught by RUNNING the deployed code on the
  # host, not by reading it: ga_evaluator_v3 imports refusal_rule_v3 for the frozen refusal rule, and the
  # section 8.1 classifier is part of the same eval chain.
  "tools/refusal_rule_v3.py"
  "tools/safety_classifier_v3.py"
  # §8.6's held-out population (CyberMetric-500 + SecQA = 610). The harness and its data must live on the
  # scoring host, and the harness paths are now env-overridable because they were hardcoded to one
  # machine's home directory and could not have run there.
  "pubbench/run_pubbench.py"
  "pubbench/cybermetric-500.json"
  "pubbench/secqa_test.csv"
  # §8.1 operational-content classifier step. Runs on a codex-capable machine (NOT the scoring host,
  # which has neither codex nor node); staged anyway so the toolset travels with the chain.
  "tools/classify_operational_v3.py"
  "v2/candidates/nvd-authority-gC.json"
)

echo "host: $HOST    mode: $([ $DRY -eq 1 ] && echo 'DRY RUN (no writes)' || echo 'EXECUTE')"
echo

# GUARD: never stage a PARTIAL NVD authority. A partial cache silently shrinks the checked-CVE set, which
# shrinks the verified-id denominator, which can drop G-C below its >=300 support floor and report a
# support shortfall that has nothing to do with the model. The authority must be complete first.
AUTH="v2/candidates/nvd-authority-gC.json"
if [ -f "$AUTH" ]; then
  read -r acov aneed <<<"$(python3 -c "
import json;d=json.load(open('$AUTH'));print(d.get('n_checked',0), d.get('n_probe_cves',0))" 2>/dev/null || echo '0 0')"
  if [ "${acov:-0}" != "${aneed:-0}" ] || [ "${aneed:-0}" = "0" ]; then
    echo "  NOTICE: $AUTH is INCOMPLETE ($acov/$aneed checked) — skipped."
    echo "          Re-run this script after tools/build_nvd_authority.py finishes, before scoring."
    _keep=(); for _f in "${FILES[@]}"; do [ "$_f" = "$AUTH" ] || _keep+=("$_f"); done; FILES=("${_keep[@]}")
  fi
fi
echo
fail=0
for f in "${FILES[@]}"; do
  if [ ! -f "$f" ]; then echo "  LOCAL MISSING  $f"; fail=1; continue; fi
  lsha=$(sha256sum "$f" | cut -d' ' -f1)
  rsha=$(ssh -o BatchMode=yes -o ConnectTimeout=12 "$HOST" "sha256sum ~/cyberguard/$f 2>/dev/null | cut -d' ' -f1")
  if [ "$lsha" = "$rsha" ]; then
    printf "  ALREADY CURRENT  %-38s %s…\n" "$f" "${lsha:0:12}"; continue
  fi
  if [ $DRY -eq 1 ]; then
    printf "  WOULD STAGE      %-38s local=%s… host=%s\n" "$f" "${lsha:0:12}" "${rsha:0:12}"
    continue
  fi
  ssh -o BatchMode=yes "$HOST" "mkdir -p ~/cyberguard/$(dirname "$f")" || { echo "  FAIL mkdir $f"; fail=1; continue; }
  rsync -a -e "ssh -o BatchMode=yes" "$f" "$HOST:cyberguard/$f" >/dev/null 2>&1
  dsha=$(ssh -o BatchMode=yes "$HOST" "sha256sum ~/cyberguard/$f 2>/dev/null | cut -d' ' -f1")
  if [ "$dsha" = "$lsha" ]; then
    printf "  STAGED+VERIFIED  %-38s %s…\n" "$f" "${lsha:0:12}"
  else
    printf "  FAIL             %-38s local=%s host=%s\n" "$f" "${lsha:0:12}" "$dsha"; fail=1
  fi
done

echo
if [ $fail -ne 0 ]; then echo "ABORT: at least one file failed"; exit 1; fi
if [ $DRY -eq 1 ]; then
  echo "DRY RUN complete — nothing written. Re-run with --execute before scoring."
else
  echo "eval code staged and hash-verified on $HOST"
fi
