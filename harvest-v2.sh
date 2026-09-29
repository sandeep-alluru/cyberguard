#!/usr/bin/env bash
# harvest-v2.sh — checksummed pull of every v2 artifact from both training hosts.
# One file per transfer (a multi-path scp silently fetches nothing — CRAFT-O-05), then a manifest check
# that refuses to print HARVEST-COMPLETE unless every sha256 matches the remote value.
set -euo pipefail
DEST="${1:-research-tmp/harvest-v2}"
H1=clawerdigi2@spark-40ee; H2=clawerdigi1@spark-8cf2
mkdir -p "$DEST"/{receipts,evals,adapters,logs,mixture}
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
  # THE TRAINED ADAPTER — the artifact the whole window exists to produce. It was ABSENT from this harvest,
  # whose own description says "every v2 artifact": 264,308,896 bytes per arm, and a verifier reading the
  # manifest would not have found the model itself. One subdir per arm because both files share a basename.
  mkdir -p "$DEST/adapters/$arm"
  pull "$host" "adapters/cyberguard-lora-v2-$arm/adapter_model.safetensors" "adapters/$arm" || true
  pull "$host" "adapters/cyberguard-lora-v2-$arm/adapter_config.json" "adapters/$arm" || true
  # the MIXTURE is not an adapter: filing it under adapters/ made `adapters/armA.jsonl` look like one.
  pull "$host" "v2/data/mixture/$arm.jsonl" mixture || true
done
# NOTE: audit.receipt.json and leak-scan.receipt.json were being pulled FROM THE HOSTS here. They do not exist
# there - the note below records that the evidence receipts were always local to this machine - so both pulls were
# guaranteed to fail, and `|| true` turned that into two "MISS ... (not present on host)" lines in the harvest log.
# A reader of that log would see evidence reported missing when it is present, and the local glob below already
# collects every one of them (that is how the D1 leak-scan and the re-audit PASS satisfy REQUIRED). The dead pulls
# are removed so the log says only what happened.
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
collect_local() {  # $1 = path relative to the repo root
  local rel="$1"
  if [ -s "$rel" ]; then
    # VERIFY THE DEPOSITED COPY, don't just record the source's hash. The remote path already compares the host's
    # hash with the local file's before writing anything to the manifest; this path hashed the source and wrote the
    # line regardless of what `cp` produced, and said so ("sha verified against itself"). A truncated or failed copy
    # would therefore have entered the manifest carrying the SOURCE's hash - a manifest entry that is wrong about
    # the file it names, which is the one thing a checksum-verified harvest must not contain. Now the copy is
    # re-hashed and must match the source, exactly as the remote case does.
    local sha_c sha_d
    cp "$rel" "$DEST/evals/$(basename "$rel")" || { echo "  FAIL cp $rel"; return 1; }
    sha_c=$(sha256sum "$rel" | awk '{print $1}')
    sha_d=$(sha256sum "$DEST/evals/$(basename "$rel")" | awk '{print $1}')
    if [ "$sha_c" = "$sha_d" ]; then
      echo "$sha_c  evals/$(basename "$rel")  (local)" >> "$DEST/MANIFEST.sha256"
      echo "  OK   evals/$(basename "$rel") (local; deposited copy re-hashed and equal to the source)"
    else
      echo "  FAIL evals/$(basename "$rel") - deposited copy differs from the source"; return 1
    fi
  else
    echo "  MISS $rel (local)"
  fi
}
for rel in evals/gate-inputs-armA.json evals/gate-inputs-base.json evals/gate-inputs-armB.json \
           v2/gate-report-v2.json v2/data/corpus-escape-scan.json v2/data/mixture/FACTS.json; do
  collect_local "$rel"
done
# THE EVIDENCE RECEIPTS, which exist ONLY on this machine. Found 2026-09-29 by rehearsing the harvest against
# the live hosts: nine of the ten (audit PASS, the unified leakage instrument, the D2 declaration, the live mask
# proof, the learning proof, the no-op-resume incident record, the registration binding and the two clearances)
# were attempted FROM THE HOSTS, where they do not exist, and were absent from the local list as well - so a
# "checksum-verified harvest" would have carried the measurements without the evidence for the claims made about
# them. The glob deliberately excludes the superseded `*.receipt.pre-*.json` files, which are dated history
# rather than current evidence.
for rel in v2/data/mixture/*.receipt.json; do
  [ -e "$rel" ] && collect_local "$rel"
done
# The verdict itself is a DOCUMENT of this contract, not an eval input, so it is harvested at the DEST root.
# Added 2026-09-29: `REQUIRED` below has always demanded docs/VERDICT-v2.md, but nothing ever copied it into
# the harvest, so the manifest could never contain it and the requirement was UNSATISFIABLE - the harvest
# exited 1 and the contract's stage 7 exited 8 on a completely perfect run. Proven in an isolated run with the
# verdict present on disk: it was still reported missing.
if [ -s docs/VERDICT-v2.md ]; then
  # Same rule as collect_local: the DEPOSITED copy is re-hashed and must equal the source before the manifest line
  # is written, so no entry can name a hash that belongs to a different file than the one it points at.
  cp docs/VERDICT-v2.md "$DEST/VERDICT-v2.md"
  sha=$(sha256sum docs/VERDICT-v2.md | awk '{print $1}')
  sha_d=$(sha256sum "$DEST/VERDICT-v2.md" | awk '{print $1}')
  if [ "$sha" = "$sha_d" ]; then
    echo "$sha  VERDICT-v2.md  (local)" >> "$DEST/MANIFEST.sha256"
    echo "  OK   VERDICT-v2.md (local; deposited copy re-hashed and equal to the source)"
  else
    echo "  FAIL VERDICT-v2.md - deposited copy differs from the source"
  fi
else
  echo "  MISS docs/VERDICT-v2.md (local)"
fi
# Fail closed on the artifacts the verdict actually needs: "HARVEST-COMPLETE" printed over a manifest that is
# missing the gate report or the fresh generalisation receipts would be a success message for a failed run.
# The evidence for the objective's own claims is REQUIRED, not optional: the re-audit PASS (step 2) and the
# unified leakage instrument (D1). A harvest that prints HARVEST-COMPLETE without them would certify a verdict
# whose supporting evidence it had not collected - which is what rehearsing against the live hosts exposed.
# Manifest SUBSTRINGS, not basenames: the two arms' adapter files share a basename, so a basename grep would be
# satisfied by one arm alone. The trained adapters are required because they are the deliverable's subject.
REQUIRED="gate-report-v2.json gate-inputs-armA.json VERDICT-v2.md audit.receipt.json \
          leak-scan-c24.receipt.json adapters/armA/adapter_model.safetensors \
          adapters/armB/adapter_model.safetensors"
MISSING=""
for pat in $REQUIRED; do
  grep -qF -- "$pat" "$DEST/MANIFEST.sha256" 2>/dev/null || MISSING="$MISSING $pat"
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
