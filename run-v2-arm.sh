#!/usr/bin/env bash
# run-v2-arm.sh — launch ONE v2 training arm, detached, with a refuse-to-start-twice gate.
# Usage: bash run-v2-arm.sh <A|B> [minutes]        (run ON the training host)
#   A -> spark-40ee, armA.jsonl (designed mix)      B -> spark-8cf2, armB.jsonl (control)
set -euo pipefail
ARM="${1:?usage: run-v2-arm.sh <A|B> [minutes]}"
MINUTES="${2:-1440}"
ROOT=""
for c in "$HOME/cyberguard" "$HOME/AgentHub/cyberguard" "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; do
  if [ -f "$c/train_cyberguard.py" ]; then ROOT="$c"; break; fi
done
[ -n "$ROOT" ] || { echo "REFUSING: cannot locate train_cyberguard.py (looked in \$HOME/cyberguard, \$HOME/AgentHub/cyberguard, script dir)"; exit 5; }
case "$ARM" in
  A) ARMS="$ROOT/v2/data/mixture/armA.jsonl"; RUN="cyberguard-lora-v2-armA" ;;
  B) ARMS="$ROOT/v2/data/mixture/armB.jsonl"; RUN="cyberguard-lora-v2-armB" ;;
  *) echo "arm must be A or B"; exit 2 ;;
esac
LOG="$ROOT/logs/train-${RUN}.log"
mkdir -p "$ROOT/logs"
# refuse to start twice — a /proc case-scan, never a self-matching pgrep (CRAFT-O-02/O-28)
# liveness = exe is python AND an argv element is EXACTLY the trainer path.
# A substring scan matches any shell whose script merely MENTIONS the file (CRAFT-O-28 self-match).
trainer_pids() {
  for p in /proc/[0-9]*; do
    exe=$(readlink -f "$p/exe" 2>/dev/null) || continue
    case "$exe" in *python*) ;; *) continue;; esac
    while IFS= read -r -d '' a; do
      case "$a" in */train_cyberguard.py|train_cyberguard.py) echo "${p#/proc/}"; break;; esac
    done < "$p/cmdline" 2>/dev/null
  done
}
LIVE=$(trainer_pids | head -1)
[ -n "$LIVE" ] && { echo "REFUSING: a trainer is already running (pid $LIVE)"; exit 3; }
true
[ -f "$ARMS" ] || { echo "REFUSING: arm file missing: $ARMS"; exit 4; }
echo "launching $RUN  minutes=$MINUTES  arms=$ARMS"
setsid nohup env CYBERGUARD_ARMS="$ARMS" MAX_MINUTES="$MINUTES" RUN_NAME="$RUN" \
  python3 "$ROOT/train_cyberguard.py" > "$LOG" 2>&1 < /dev/null &
sleep 5
echo "pid $(pgrep -f 'train_cyberguard[.]py' | head -1)  log $LOG"
