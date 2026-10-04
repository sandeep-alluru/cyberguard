#!/usr/bin/env bash
# 3-hour soak for samurai6-qwen/qwen3.8-27b
# Cycles: small / medium / large-output / near-limit-input / bad-auth / bad-model
# Logs JSONL to logs/qwen-28b-soak-<ts>.jsonl
set -uo pipefail
BASE="http://100.105.77.125:18020/v1"
KEY="7a843cf2d8a427aa4e1c9aa17aedb554ad66538d72f35d19"
MODEL="qwen3.8-27b"
DUR=${1:-10800}  # seconds, default 3h
LOG="logs/qwen-28b-soak-$(date +%Y%m%dT%H%M%S).jsonl"
mkdir -p logs
START=$(date +%s); END=$((START + DUR)); i=0
echo "soak start dur=${DUR}s log=${LOG}" | tee -a "$LOG"
# build a ~30k-token-ish prompt once (≈120KB text)
BIG=$(python3 -c "print(('Explain quantum error correction in detail. ' * 2500)[:120000])")
while [ "$(date +%s)" -lt "$END" ]; do
  i=$((i+1))
  case $((i % 6)) in
    1) MT=100;  P="Say hello in one sentence."; M="$MODEL"; K="$KEY";;
    2) MT=1000; P="Explain TCP vs UDP in 5 bullets."; M="$MODEL"; K="$KEY";;
    3) MT=4096; P="Write a detailed essay on caching strategies."; M="$MODEL"; K="$KEY";;
    4) MT=16384; P="Write a comprehensive guide to Rust lifetimes."; M="$MODEL"; K="$KEY";;
    5) MT=16384; P="$BIG"; M="$MODEL"; K="$KEY";;   # near/over-limit -> expect 400
    0) MT=100;  P="ping"; M="does-not-exist"; K="$KEY";;  # bad model -> expect error
  esac
  t0=$(date +%s.%N)
  if [ "$MT" -gt 4000 ]; then TM=600; else TM=120; fi
  code=$(curl -s -m "$TM" -o /tmp/soak-body.txt -w "%{http_code}" "$BASE/chat/completions" \
    -H "Authorization: Bearer $K" -H "Content-Type: application/json" \
    -d "$(python3 -c "import json,sys; print(json.dumps({'model':sys.argv[1],'messages':[{'role':'user','content':open('/tmp/soak-p.txt').read() if False else sys.argv[2]}],'max_tokens':int(sys.argv[3]),'stream':False}))" "$M" "$P" "$MT")")
  t1=$(date +%s.%N)
  dt=$(echo "$t1 $t0" | awk '{printf "%.1f",$1-$2}')
  body=$(head -c 300 /tmp/soak-body.txt | tr '\n' ' ')
  echo "{\"t\":\"$(date -u +%FT%TZ)\",\"iter\":$i,\"mt\":$MT,\"http\":$code,\"dt_s\":$dt,\"body\":\"$body\"}" | tee -a "$LOG"
  sleep 20
done
echo "soak done iters=$i" | tee -a "$LOG"
