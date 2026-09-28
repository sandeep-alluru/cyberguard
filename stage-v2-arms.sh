#!/usr/bin/env bash
# stage-v2-arms.sh — copy the frozen arms to both training hosts and verify the hashes there.
set -uo pipefail
cd ~/AgentHub/cyberguard
A=$(sha256sum v2/data/mixture/armA.jsonl | cut -d' ' -f1)
B=$(sha256sum v2/data/mixture/armB.jsonl | cut -d' ' -f1)
for spec in "clawerdigi2@spark-40ee armA.jsonl $A" "clawerdigi1@spark-8cf2 armB.jsonl $B"; do
  set -- $spec; H=$1; F=$2; WANT=$3
  echo "  staging $F -> $H"
  rsync -a --info=progress2 "v2/data/mixture/$F" "$H:~/cyberguard/v2/data/mixture/$F" >/dev/null 2>&1
  GOT=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$H" "sha256sum ~/cyberguard/v2/data/mixture/$F" 2>/dev/null | cut -d' ' -f1)
  if [ "$GOT" = "$WANT" ]; then echo "    OK  $F  ${GOT:0:16}…  (matches local)"
  else echo "    MISMATCH $F local=$WANT remote=$GOT"; exit 1; fi
done
echo "  both arms staged and hash-verified"
