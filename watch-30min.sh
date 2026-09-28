#!/bin/bash
# 30-min CyberGuard v2 + Ornith-9B watch. Read-only. Prints concise state
# and appends one watch-check event to the 2nd-brain autonomous feed.
CG_DIR=~/.dsh/sessions/--home-clawer-samurai-1-AgentHub-cyberguard--
CGW=~/AgentHub/cyberguard
ORNITH_LOG=/mnt/purple4tb/AgentHub-archive/gpu-work/training/ornith9b-v1-continuation-20260926/monitor/part-watch.log
NOW=$(date +%s)

echo "=== cyberguard session ==="
CGS=$(cd "$CG_DIR" && for s in */; do echo "$(stat -c %Y "$s/session.v3.jsonl.zstd" 2>/dev/null) $s"; done | sort -rn | head -1 | awk '{print $2}' | tr -d /)
echo "live_session=$CGS"
LAST=$(stat -c %Y "$CG_DIR/$CGS/session.v3.jsonl.zstd")
IDLE_MIN=$(( (NOW - LAST) / 60 ))
echo "last_activity_min_ago=$IDLE_MIN"
CG_TURNSTEP=$(zstd -dc "$CG_DIR/$CGS/session.v3.jsonl.zstd" 2>/dev/null | tail -2 | python3 -c "
import sys, json
for line in sys.stdin:
    try: e=json.loads(line)
    except: continue
    d=e.get('data',{})
    if d.get('turn'): print('turn', d.get('turn'), 'step', d.get('step'))
" 2>/dev/null | tail -1)
echo "$CG_TURNSTEP"
CG_TURN=$(echo "$CG_TURNSTEP" | awk '{print $2}')
ERR30=$(zstd -dc "$CG_DIR/$CGS/session.v3.jsonl.zstd" 2>/dev/null | tail -400 | grep -ciE '"error"|FAILED|Traceback')
echo "errors_last_30m=$ERR30"

echo "=== checkpoints (3h cadence) ==="
LATEST=$(ls -t "$CGW/docs/ceo/"*checkpoint* 2>/dev/null | head -1)
echo "latest=$(basename "$LATEST" 2>/dev/null)"
CKPT_NUM=$(basename "$LATEST" 2>/dev/null | grep -oE 'checkpoint[0-9]+' | grep -oE '[0-9]+')
if [ -n "$LATEST" ]; then CKPT_AGE_MIN=$(( (NOW - $(stat -c %Y "$LATEST")) / 60 )); else CKPT_AGE_MIN="n/a"; fi
echo "age_min=$CKPT_AGE_MIN"
ASTRA3H=$(zstd -dc "$CG_DIR/$CGS/session.v3.jsonl.zstd" 2>/dev/null | tail -3000 | grep -ci 'astra')
echo "astra_mentions_last_3h=$ASTRA3H"

echo "=== ornith-9b training ==="
if [ -f "$ORNITH_LOG" ]; then
  ORNITH_AGE_MIN=$(( (NOW - $(stat -c %Y "$ORNITH_LOG")) / 60 ))
  tail -8 "$ORNITH_LOG" 2>/dev/null | grep -oE 'arm=[BC] .*step=[0-9]+' | tail -4 | cut -c1-120
  B_STEP=$(grep -oE 'arm=B .*step=[0-9]+' "$ORNITH_LOG" 2>/dev/null | tail -1 | grep -oE 'step=[0-9]+' | cut -d= -f2)
  C_STEP=$(grep -oE 'arm=C .*step=[0-9]+' "$ORNITH_LOG" 2>/dev/null | tail -1 | grep -oE 'step=[0-9]+' | cut -d= -f2)
  ORNITH_SUM="B ${B_STEP:-?}/C ${C_STEP:-?}"
else
  ORNITH_AGE_MIN="missing"; ORNITH_SUM="log missing"
fi
echo "watch_log_age_min=$ORNITH_AGE_MIN"

echo "=== qwen eviction check ==="
if curl -s -m 5 -o /dev/null http://127.0.0.1:8093/v1/models 2>/dev/null; then
  echo "qwen_8093=http_up"; QWEN_SUM="UP"
else
  echo "qwen_8093=down"; QWEN_SUM="down"
fi

# --- 2nd-brain autonomous feed: exactly one watch-check per run ---
export FEED_TITLE="30-min watch: CG turn ${CG_TURN:-?} idle ${IDLE_MIN}m err30=${ERR30}, Ornith ${ORNITH_SUM} (log ${ORNITH_AGE_MIN}m), ckpt #${CKPT_NUM:-?} age ${CKPT_AGE_MIN}m, qwen ${QWEN_SUM}"
export FEED_DETAIL="astra mentions last 3h: ${ASTRA3H}"
python3 - <<'PYEOF' 2>/dev/null
import json, os
from datetime import datetime, timezone
feed = os.path.expanduser("~/AgentHub/2ndbrain/ops/autonomous-feed.jsonl")
ev = {
    "type": "watch-check",
    "actor": "cron:cyberguard-ornith-watch",
    "title": os.environ.get("FEED_TITLE", "30-min watch")[:140],
    "detail": os.environ.get("FEED_DETAIL", ""),
    "outcome": "ok",
    "ts": datetime.now(timezone.utc).isoformat(),
}
os.makedirs(os.path.dirname(feed), exist_ok=True)
with open(feed, "a") as f:
    f.write(json.dumps(ev) + "\n")
PYEOF
echo "feed=appended"
