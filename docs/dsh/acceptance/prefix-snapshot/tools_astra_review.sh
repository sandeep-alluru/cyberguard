#!/usr/bin/env bash
# astra_review.sh — THE single entry point for any Astra review (Astra D18).
# Enforcement = only blessed path + pre-send validation + per-review accounting + bypass detection
# (tools/audit_reviews.py).   Usage: tools/astra_review.sh <packet.json> [output.txt]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKT="${1:?usage: astra_review.sh <packet.json> [output.txt]}"
OUT="${2:-$ROOT/research-tmp/reviews/$(basename "${PKT%.json}")-verdict.txt}"
LEDGER="$ROOT/docs/review-accounting.jsonl"
PY=python3
[ -f "$PKT" ] || { echo "  REFUSED: no packet at $PKT"; exit 1; }

echo "== validating the packet BEFORE any send =="
for m in check-batch check-packet check-extractions check-exposure; do
  $PY "$ROOT/tools/review_packet.py" "$m" "$PKT" | tail -1
  $PY "$ROOT/tools/review_packet.py" "$m" "$PKT" >/dev/null 2>&1 || {
    echo "  REFUSED: $m failed — nothing was sent"; exit 1; }
done
$PY "$ROOT/tools/review_packet.py" test-budget "$PKT" | tail -1
$PY "$ROOT/tools/review_packet.py" test-budget "$PKT" >/dev/null 2>&1 || {
  echo "  REFUSED: budget check failed — nothing was sent"; exit 1; }

PKT_HASH=$($PY -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$PKT")
RID=$($PY -c "import json,sys;print(json.load(open(sys.argv[1])).get('review_id','UNKNOWN'))" "$PKT")
REQ_ID="$(date -u +%Y%m%dT%H%M%SZ)-$RID"
PROMPT="$ROOT/research-tmp/reviews/prompt-cache/$RID.prompt.txt"

# The review prompt is the PACKET ONLY: no repo reading, no inherited worker transcript.
$PY - "$PKT" > "$PROMPT" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
print("You are Astra, CTO and reviewer. Answer ONLY from the packet below. Do not read the repository.")
print("Return a disposition for every question id: supported | contradicted | unresolved.")
print("If the packet does not settle a question, answer 'unresolved'. Treat 'not a defect' and")
print("'the detector is wrong' as valid outcomes. Do not approve while any answer is unresolved.")
print()
print(json.dumps(p, indent=1))
PY

echo "== packet validated; sending review_id=$RID =="
codex exec -m gpt-6-astra -s read-only --skip-git-repo-check < "$PROMPT" > "$OUT" 2>&1 || true

$PY - "$LEDGER" "$REQ_ID" "$RID" "$PKT_HASH" "$OUT" <<'PY'
import json,sys,os
ledger,req,rid,pkthash,out = sys.argv[1:6]
size=os.path.getsize(out) if os.path.exists(out) else 0
rec={"review_id":rid,"request_id":req,"packet_sha256":pkthash,"prompt_bytes":os.path.getsize(
      os.path.join(os.path.dirname(ledger),"..","research-tmp","reviews","prompt-cache",rid+".prompt.txt")) if True else 0,
     "verdict_bytes":size,"input_tokens":0,"cached_input_tokens":0,"output_tokens":0,
     "usage_records":0,"outcome":"recorded","telemetry":"UNMEASURED"}
with open(ledger,"a") as f: f.write(json.dumps(rec)+"\n")
print("  accounting appended -> docs/review-accounting.jsonl")
PY
echo "  verdict -> $OUT"
