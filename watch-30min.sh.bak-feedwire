#!/bin/bash
# 30-min CyberGuard v2 + Ornith-9B watch. Read-only. Prints concise state.
CG_DIR=~/.dsh/sessions/--home-clawer-samurai-1-AgentHub-cyberguard--
ORNITH_DIR=~/.dsh/sessions/--mnt-purple4tb-AgentHub-archive-gpu-work--
CGW=~/AgentHub/cyberguard
NOW=$(date +%s)

echo "=== cyberguard session ==="
CGS=$(cd "$CG_DIR" && for s in */; do echo "$(stat -c %Y "$s/session.v3.jsonl.zstd" 2>/dev/null) $s"; done | sort -rn | head -1 | awk '{print $2}' | tr -d /)
echo "live_session=$CGS"
LAST=$(stat -c %Y "$CG_DIR/$CGS/session.v3.jsonl.zstd")
echo "last_activity_min_ago=$(( (NOW - LAST) / 60 ))"
zstd -dc "$CG_DIR/$CGS/session.v3.jsonl.zstd" 2>/dev/null | tail -2 | python3 -c "
import sys, json
for line in sys.stdin:
    try: e=json.loads(line)
    except: continue
    d=e.get('data',{})
    print(e.get('type'),'| turn',d.get('turn'),'| step',d.get('step'))
" 2>/dev/null
echo "errors_last_30m=$(zstd -dc "$CG_DIR/$CGS/session.v3.jsonl.zstd" 2>/dev/null | tail -400 | grep -ciE '\"error\"|FAILED|Traceback' )"

echo "=== checkpoints (3h cadence) ==="
LATEST=$(ls -t "$CGW/docs/ceo/"*checkpoint* 2>/dev/null | head -1)
echo "latest=$(basename "$LATEST" 2>/dev/null)"
if [ -n "$LATEST" ]; then echo "age_min=$(( (NOW - $(stat -c %Y "$LATEST")) / 60 ))"; fi
echo "astra_mentions_last_3h=$(zstd -dc "$CG_DIR/$CGS/session.v3.jsonl.zstd" 2>/dev/null | tail -3000 | grep -ci 'astra')"

echo "=== ornith-9b training ==="
tail -6 /mnt/purple4tb/AgentHub-archive/gpu-work/training/ornith9b-v1-continuation-20260926/part-watch.log 2>/dev/null | grep -E 'step|Step|GPU|gpu' | tail -4
echo "watch_log_age_min=$(( (NOW - $(stat -c %Y /mnt/purple4tb/AgentHub-archive/gpu-work/training/ornith9b-v1-continuation-20260926/part-watch.log 2>/dev/null || echo $NOW)) / 60 ))"

echo "=== qwen eviction check ==="
curl -s -m 5 -o /dev/null -w "qwen_8093_http=%{http_code}\n" http://127.0.0.1:8093/v1/models 2>/dev/null || echo "qwen_8093=down"
