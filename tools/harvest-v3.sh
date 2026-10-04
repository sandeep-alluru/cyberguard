#!/usr/bin/env bash
# harvest-v3.sh — checksummed pull of every v3 artifact from the training host.
#
# Follows harvest-v2.sh, including the lessons its own comments record:
#   * ONE FILE PER TRANSFER. A multi-path scp silently fetches nothing (CRAFT-O-05), and a harvest that
#     looks successful while moving no data is worse than one that fails loudly.
#   * THE ADAPTER MUST BE IN THE MANIFEST. v2's harvest described itself as "every artifact" while
#     omitting the 264 MB adapter — the single artifact the whole run exists to produce — so a verifier
#     reading the manifest could not find the model. The adapter is pulled explicitly here.
#   * COMPARE THE DEPOSITED COPY against the REMOTE hash, never the source against itself. A truncated
#     copy must not enter the manifest carrying the source's hash.
#   * HARVEST-COMPLETE is refused unless every hash matched.
#
# DRY RUN BY DEFAULT: prints what it would pull and whether the host currently has it. Pass --execute to
# actually transfer. Safe to run while training is still going (it reports "not yet present").
#
# Usage:  bash tools/harvest-v3.sh              # inspect only
#         bash tools/harvest-v3.sh --execute    # transfer + verify
set -uo pipefail
HOST="${HOST:-clawerdigi2@spark-40ee}"
RUN="${RUN:-cyberguard-lora-v3}"
DEST="${1:-research-tmp/harvest-v3}"
DRY=1
[ "${1:-}" = "--execute" ] && { DRY=0; DEST="research-tmp/harvest-v3"; }
[ "${2:-}" = "--execute" ] && DRY=0
cd "$HOME/AgentHub/cyberguard" || exit 1

if [ $DRY -eq 1 ]; then
  DEST="$(mktemp -d)/harvest-v3"
fi
mkdir -p "$DEST"/{receipts,evals,adapters,logs}
: > "$DEST/MANIFEST.sha256"

echo "host: $HOST   run: $RUN   mode: $([ $DRY -eq 1 ] && echo 'DRY RUN (no writes)' || echo 'EXECUTE')"
echo

pull() {  # $1 = path relative to ~/cyberguard on the host, $2 = local subdir
  local rel="$1" sub="$2" rsha lsha
  if ! ssh -o BatchMode=yes -o ConnectTimeout=12 "$HOST" "test -e ~/cyberguard/$rel" 2>/dev/null; then
    echo "  ABSENT ~/cyberguard/$rel"
    return 0
  fi
  if [ $DRY -eq 1 ]; then
    rsha=$(ssh -o BatchMode=yes -o ConnectTimeout=12 "$HOST" "sha256sum ~/cyberguard/$rel 2>/dev/null | cut -d' ' -f1" 2>/dev/null)
    printf "  PRESENT %-52s sha=%s…\n" "$rel" "${rsha:0:16}"
    return 0
  fi
  if scp -q -o BatchMode=yes -o ConnectTimeout=12 "$HOST:./cyberguard/$rel" "$DEST/$sub/" 2>/dev/null; then
    local local_f="$DEST/$sub/$(basename "$rel")"
    rsha=$(ssh -o BatchMode=yes -o ConnectTimeout=12 "$HOST" "sha256sum ~/cyberguard/$rel | awk '{print \$1}'")
    lsha=$(sha256sum "$local_f" | awk '{print $1}')
    if [ "$rsha" = "$lsha" ]; then
      echo "$rsha  $sub/$(basename "$rel")" >> "$DEST/MANIFEST.sha256"
      echo "  OK   $sub/$(basename "$rel")"
    else
      echo "  FAIL $sub/$(basename "$rel") — deposited copy does not match the remote hash"; return 1
    fi
  else
    echo "  FAIL transfer $rel"; return 1
  fi
}

# 1. THE TRAINING RECEIPT (loss curve, step timing, token count, library versions, held-out split).
pull "receipts/$RUN.json" receipts
# 2. THE ADAPTER — the artifact the run exists to produce.
pull "adapters/$RUN/adapter_model.safetensors" adapters
pull "adapters/$RUN/adapter_config.json" adapters
# 3. THE TRAINING LOG.
pull "logs/train-$RUN.log" logs
# 4. THE MIXTURE THAT WAS ACTUALLY TRAINED (so the receipt can be tied to the exact corpus).
pull "data/v3/mixture/mixture-v3-no-trail.jsonl" evals
# 5. THE EVAL BATTERIES, once scored. Every registered battery x arm, as harvest-v2 did.
# ARM LABEL (fixed 2026-10-01). This list asked for `armB` receipts, but the runbook scores the v3 adapter
# as `--arm armA` -- the candidate slot the assembler actually reads (v2's Arm B is observational only).
# Left as it was, the harvest would have hunted for battery files that can never exist and MISSED every
# real one. v3 is a SINGLE-ARM run: base is the reference, armA is the candidate.
for b in gA gA2 gB gC gE gF gG-gsm8k gG-ifeval gJ fresh-gA fresh-gB fresh-gE fresh-gF fresh-gJ; do
  for a in base armA; do
    pull "evals/battery-$b-$a.json" evals
  done
done
# 6. the assembled gate inputs and the verdict report, once they exist
pull "evals/gate-inputs-armA.json" evals
pull "evals/gate-report-v3.json" evals

echo
if [ $DRY -eq 1 ]; then
  echo "DRY RUN complete — nothing was transferred. Re-run with --execute once training has finished."
else
  if [ -s "$DEST/MANIFEST.sha256" ]; then
    echo "MANIFEST ($(wc -l < "$DEST/MANIFEST.sha256") files):"
    sed 's/^/  /' "$DEST/MANIFEST.sha256"
    echo "HARVEST-COMPLETE — every listed file matched its remote sha256."
  else
    echo "NOTHING HARVESTED — the adapter/receipt do not exist on $HOST yet (training still running?)."
  fi
fi
