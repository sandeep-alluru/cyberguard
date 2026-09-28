#!/usr/bin/env bash
# harvest-v2.sh — checksummed pull of every v2 artifact from both training hosts.
# One file per transfer (a multi-path scp silently fetches nothing — CRAFT-O-05), then a manifest check
# that refuses to print HARVEST-COMPLETE unless every sha256 matches the remote value.
set -euo pipefail
DEST="${1:-research-tmp/harvest-v2}"
H1=clawerdigi2@spark-40ee; H2=clawerdigi1@spark-8cf2
mkdir -p "$DEST"/{receipts,evals,adapters,logs}
pull() { # host remote_local_pair
  local host="$1" rel="$2" sub="$3"
  if scp -q -o ConnectTimeout=10 "$host:./cyberguard/$rel" "$DEST/$sub/" 2>/dev/null; then
    local local_f="$DEST/$sub/$(basename "$rel")"
    local remote_sha local_sha
    remote_sha=$(ssh -o ConnectTimeout=10 "$host" "sha256sum ~/cyberguard/$rel" | awk '{print $1}')
    local_sha=$(sha256sum "$local_f" | awk '{print $1}')
    if [ "$remote_sha" = "$local_sha" ]; then
      echo "$remote_sha  $sub/$(basename "$rel")" >> "$DEST/MANIFEST.sha256"
      echo "  OK   $sub/$(basename "$rel")"
    else
      echo "  FAIL $sub/$(basename "$rel") — sha mismatch"; return 1
    fi
  else
    echo "  MISS $rel (not present on $host)"
  fi
}
: > "$DEST/MANIFEST.sha256"
# training receipts and adapters (both arms), the audit/leak receipts, the eval receipts and logs
for pair in "$H1 armA" "$H2 armB"; do
  set -- $pair; host=$1; arm=$2
  pull "$host" "receipts/cyberguard-lora-v2-$arm.json" receipts || true
  pull "$host" "evals/cyberguard-lora-v2-$arm.json" evals || true
  pull "$host" "v2/data/mixture/$arm.jsonl" adapters || true
done
pull "$H1" "v2/data/mixture/audit.receipt.json" receipts || true
pull "$H1" "v2/data/mixture/leak-scan.receipt.json" receipts || true
for f in train-cyberguard-lora-v2-armA.log train-cyberguard-lora-v2-armB.log eval-cyberguard-lora-v2-armA.log eval-cyberguard-lora-v2-armB.log; do
  pull "$H1" "logs/$f" logs || true
done
echo "HARVEST-COMPLETE  $(wc -l < "$DEST/MANIFEST.sha256") files verified"
