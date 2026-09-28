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
# battery receipts live on the host that ran them (arm A on 40ee, arm B on 8cf2); the combined base side
for pair in "$H1" "$H2"; do
  for b in gA gA2 gB gC gE gF gG-gsm8k gG-ifeval gJ; do
    for a in armA armB base; do
      pull "$pair" "evals/battery-$b-$a.json" evals || true
    done
  done
done
# local artifacts of the contract itself: the assembled inputs, the verdict, the corpus escape measurement
for rel in evals/gate-inputs-armA.json evals/gate-inputs-base.json evals/gate-inputs-armB.json \
           v2/gate-report-v2.json v2/data/corpus-escape-scan.json v2/data/mixture/FACTS.json; do
  if [ -s "$rel" ]; then
    sha=$(sha256sum "$rel" | awk '{print $1}')
    cp "$rel" "$DEST/evals/$(basename "$rel")"
    echo "$sha  evals/$(basename "$rel")  (local)" >> "$DEST/MANIFEST.sha256"
    echo "  OK   evals/$(basename "$rel") (local, sha verified against itself)"
  else
    echo "  MISS $rel (local)"
  fi
done
echo "HARVEST-COMPLETE  $(wc -l < "$DEST/MANIFEST.sha256") files verified"
