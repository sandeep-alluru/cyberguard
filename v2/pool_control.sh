#!/usr/bin/env bash
# pool_control.sh — the flash-next pool must be STOPPED for the v2 training window and RESTORED after.
#
# Why: on spark-8cf2 the served llama-server (-c 524288, --parallel 2) commits ~129 of 130 GB of unified
# memory, leaving ~1 GB — a 4B LoRA cannot allocate. v1's measured 0.9683 s/sample was taken while this
# pool was DOWN (journal: no starts between 2026-09-26T16:32 and 2026-09-27T19:16; v1 trained
# 2026-09-27 01:29–04:20 CDT), so stopping the pool is also what makes the v2 budget arithmetic valid.
# The supervisor model is deepseek-flash (cloud) — stopping this pool does not touch it.
set -uo pipefail
ACT=${1:?usage: pool_control.sh stop|restore|verify|probe}
S8=clawerdigi1@spark-8cf2; S4=clawerdigi2@spark-40ee
ssh8() { timeout 90 ssh -o BatchMode=yes -o ConnectTimeout=10 "$S8" "$@"; }
ssh4() { timeout 90 ssh -o BatchMode=yes -o ConnectTimeout=10 "$S4" "$@"; }

free_gb() {   # free GPU bytes on a host, in GB (nvidia-smi's unified-memory column is [N/A] on GB10)
  "$1" "source ~/.cyberguard-env; \$CYBERGUARD_VENV/bin/python -c \"import torch;print('%.1f' % (torch.cuda.mem_get_info()[0]/1e9))\"" 2>/dev/null | tail -1
}

probe() {     # a REAL generation: the only proof that restoration worked
  ssh8 "timeout 120 curl -sS -X POST http://127.0.0.1:8093/v1/chat/completions \
    -H 'Content-Type: application/json' -H 'Authorization: Bearer dummy' \
    -d '{\"model\":\"qwen3.8-flash-next\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with the single word: ready\"}],\"max_tokens\":64,\"temperature\":0}'" \
    2>/dev/null | python3 -c "
import json,sys
raw = sys.stdin.read().strip()
if not raw:
    print('  PROBE FAIL: empty response'); raise SystemExit(1)
try:
    d = json.loads(raw)
    m = (d.get('choices') or [{}])[0].get('message',{}) or {}
    txt = (m.get('content') or '').strip()
    if not txt:
        print('  PROBE FAIL: parsed but the answer is EMPTY (reasoning-only)'); raise SystemExit(1)
    t = d.get('timings') or {}
    print('  PROBE OK: answered', repr(txt[:40]), ('at %.1f tok/s' % t['predicted_per_second']) if t.get('predicted_per_second') else '')
except SystemExit:
    raise
except Exception:
    print('  PROBE FAIL: unparseable response', raw[:120]); raise SystemExit(1)"
}

case "$ACT" in
  stop)
    echo "=== stopping the flash-next pool ==="
    ssh8 "sudo systemctl stop spark-flash-next.service && echo '  8cf2: spark-flash-next stopped'"
    ssh4 "sudo systemctl stop spark-rpc.service && echo '  40ee: spark-rpc stopped'"
    for i in $(seq 1 24); do
      f8=$(free_gb ssh8); f4=$(free_gb ssh4)
      echo "  free: 8cf2=${f8} GB  40ee=${f4} GB"
      awk -v a="$f8" -v b="$f4" 'BEGIN{exit !(a>40 && b>40)}' && { echo "  POOL DOWN: both hosts have >40 GB free"; break; }
      sleep 10
    done
    ssh8 "ss -ltn | grep -c ':8093'" | sed 's/^/  listener 8093 count: /'
    ;;
  restore)
    echo "=== restoring the flash-next pool ==="
    ssh4 "sudo systemctl start spark-rpc.service && echo '  40ee: spark-rpc started'"
    ssh8 "sudo systemctl start spark-flash-next.service && echo '  8cf2: spark-flash-next started'"
    for i in $(seq 1 40); do
      sleep 15
      ssh8 "ss -ltn | grep -q ':8093'" 2>/dev/null || { echo "  waiting for :8093 (${i})"; continue; }
      if probe; then echo "  RESTORED (probe passed)"; exit 0; fi
      echo "  port up but probe not ready (${i})"
    done
    echo "  RESTORE FAILED: port up but no successful completion"; exit 1
    ;;
  probe)  probe ;;
  verify)
    echo "  service states:"; ssh8 "systemctl is-active spark-flash-next.service | sed 's/^/    8cf2 spark-flash-next: /'"
    ssh4 "systemctl is-active spark-rpc.service | sed 's/^/    40ee spark-rpc: /'"
    echo "  free: 8cf2=$(free_gb ssh8) GB  40ee=$(free_gb ssh4) GB"
    echo "  listener 8093: $(ssh8 "ss -ltn | grep -c ':8093'")"
    ;;
  *) echo "unknown action: $ACT"; exit 2 ;;
esac
