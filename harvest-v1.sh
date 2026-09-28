#!/usr/bin/env bash
# harvest-v1.sh — checksum-verified harvest of all v1 artifacts from spark to research-tmp.
# Verify by sha256 computed on the REMOTE at harvest time; any mismatch is loud and fatal.
set -uo pipefail
REMOTE="${REMOTE:-clawerdigi2@spark-40ee}"
DEST="$(cd "$(dirname "$0")" && pwd)/research-tmp/harvest-v1"
mkdir -p "$DEST"/{adapters,receipts,evals,logs}
ssh -o BatchMode=yes "$REMOTE" bash -s <<'REMOTE_LIST' > /tmp/cg-harvest-files.txt
cd ~/cyberguard
find adapters/cyberguard-lora-v1 -maxdepth 1 -type f -name '*' \
  receipts/cyberguard-lora-v1.json \
  evals/cyberguard-lora-v1.json evals/cyberguard-lora-v1.partial.json \
  evals/merge-equiv-cyberguard-lora-v1.json \
  logs/train-cyberguard-lora-v1.log logs/eval-cyberguard-lora-v1.log \
  logs/merge-equiv-cyberguard-lora-v1.log logs/eval-chain-cyberguard-lora-v1.log \
  logs/monitor-v1.log logs/monitor-eval.log 2>/dev/null
sha256sum $(cd ~/cyberguard && find adapters/cyberguard-lora-v1 -maxdepth 1 -type f \
  receipts/cyberguard-lora-v1.json evals/cyberguard-lora-v1.json \
  evals/merge-equiv-cyberguard-lora-v1.json \
  logs/train-cyberguard-lora-v1.log logs/eval-cyberguard-lora-v1.log \
  logs/eval-chain-cyberguard-lora-v1.log 2>/dev/null) 2>/dev/null
REMOTE_LIST
grep -v '^$' /tmp/cg-harvest-files.txt | head -1 >/dev/null
# split: first block = file list until a line starting with 64-hex; simpler: recompute
ssh -o BatchMode=yes "$REMOTE" 'cd ~/cyberguard && sha256sum $(find adapters/cyberguard-lora-v1 -maxdepth 1 -type f; echo receipts/cyberguard-lora-v1.json evals/cyberguard-lora-v1.json evals/merge-equiv-cyberguard-lora-v1.json logs/train-cyberguard-lora-v1.log logs/eval-cyberguard-lora-v1.log logs/merge-equiv-cyberguard-lora-v1.log logs/eval-chain-cyberguard-lora-v1.log logs/monitor-v1.log 2>/dev/null) 2>/dev/null' > "$DEST/MANIFEST-remote.sha256"
while read -r hash path; do
  mkdir -p "$DEST/$(dirname "$path")"
  scp -q "$REMOTE:~/cyberguard/$path" "$DEST/$path" || { echo "FAIL-transfer $path"; exit 1; }
  local_h=$(sha256sum "$DEST/$path" | cut -d" " -f1)
  if [ "$local_h" = "$hash" ]; then echo "OK $path"; else echo "MISMATCH $path"; exit 1; fi
done < "$DEST/MANIFEST-remote.sha256"
echo "HARVEST-COMPLETE all checksums verified -> $DEST"
