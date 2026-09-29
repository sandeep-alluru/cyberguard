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
  for b in gA gA2 gB gC gE gF gG-gsm8k gG-ifeval gJ fresh-gA fresh-gB fresh-gE fresh-gF fresh-gJ; do
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
# The verdict itself is a DOCUMENT of this contract, not an eval input, so it is harvested at the DEST root.
# Added 2026-09-29: `REQUIRED` below has always demanded docs/VERDICT-v2.md, but nothing ever copied it into
# the harvest, so the manifest could never contain it and the requirement was UNSATISFIABLE - the harvest
# exited 1 and the contract's stage 7 exited 8 on a completely perfect run. Proven in an isolated run with the
# verdict present on disk: it was still reported missing.
if [ -s docs/VERDICT-v2.md ]; then
  sha=$(sha256sum docs/VERDICT-v2.md | awk '{print $1}')
  cp docs/VERDICT-v2.md "$DEST/VERDICT-v2.md"
  echo "$sha  VERDICT-v2.md  (local)" >> "$DEST/MANIFEST.sha256"
  echo "  OK   VERDICT-v2.md (local, sha verified against itself)"
else
  echo "  MISS docs/VERDICT-v2.md (local)"
fi
# Fail closed on the artifacts the verdict actually needs: "HARVEST-COMPLETE" printed over a manifest that is
# missing the gate report or the fresh generalisation receipts would be a success message for a failed run.
REQUIRED="v2/gate-report-v2.json evals/gate-inputs-armA.json docs/VERDICT-v2.md"
MISSING=""
for rel in $REQUIRED; do
  base=$(basename "$rel")
  # Match the BASENAME anywhere in the manifest, fixed-string: the old form searched for "  evals/<base>",
  # which could never match a file harvested at the DEST root (and would also be fooled by a dotted basename).
  grep -qF -- "$base" "$DEST/MANIFEST.sha256" 2>/dev/null || MISSING="$MISSING $rel"
done
for b in fresh-gA fresh-gB fresh-gE fresh-gF fresh-gJ; do
  grep -q "battery-$b-armA.json" "$DEST/MANIFEST.sha256" 2>/dev/null || MISSING="$MISSING evals/battery-$b-armA.json"
done
if [ -n "$MISSING" ]; then
  echo "HARVEST-INCOMPLETE — the manifest lacks:$MISSING"
  echo "  ($(wc -l < "$DEST/MANIFEST.sha256") files verified; the missing ones mean the contract did not finish)"
  exit 1
fi
echo "HARVEST-COMPLETE  $(wc -l < "$DEST/MANIFEST.sha256") files verified, including every generalisation instrument"
