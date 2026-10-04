#!/usr/bin/env bash
# run-v3-arm.sh — launch the CyberGuard v3 run (single arm, approved Arm B recipe).
# Run ON the training host.  Usage: bash run-v3-arm.sh [minutes]
#
# Modeled on run-v2-arm.sh and keeps its guards:
#   * locate the root by finding train_cyberguard.py (never assume a path);
#   * REFUSE to start twice, using an exact-argv /proc scan — a substring scan would match any
#     shell merely mentioning the trainer path (that self-match bit this session twice);
#   * source ~/.cyberguard-env and use the venv interpreter, because a bare `python3` has no torch;
#   * detached via setsid+nohup so an ssh drop cannot kill the run.
#
# Scheduled inputs must already be staged and hash-verified (tools/stage-v3.sh).
#
# BUDGET NOTE (2026-09-30): the default minutes is 3300 (55 h), NOT the plan's original 1320.
# max_minutes is a TimeBox CEILING passed as MAX_MINUTES; it does not lengthen the run — the run
# ends when epoch 1.0 completes. The original 1320 was derived from v2's presentations/s, but the
# v3 mixture carries 735.1 tokens/presentation against v2's 323.4, so the measured projection is
# ~45.3 h. A 1320-minute cap would have stopped the run at ~48 % of the epoch, which §5.1 disposes
# as INCOMPLETE (not harvested, no ship verdict). Raising the ceiling changes no hyperparameter.
set -euo pipefail

MINUTES="${1:-3300}"
RUN="cyberguard-lora-v3"
ARMS_REL="data/v3/mixture/mixture-v3-no-trail.jsonl"
WANT_SHA="${WANT_SHA:-75b5099c568313f2ceada6f79746e51840b5240d943e952c2f2ebe3c3318fc90}"
WANT_ROWS=140545

ROOT=""
for c in "$HOME/cyberguard" "$HOME/AgentHub/cyberguard" "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; do
  if [ -f "$c/train_cyberguard.py" ]; then ROOT="$c"; break; fi
done
[ -n "$ROOT" ] || { echo "REFUSING: cannot locate train_cyberguard.py"; exit 5; }
ARMS="$ROOT/$ARMS_REL"
LOG="$ROOT/logs/train-${RUN}.log"
mkdir -p "$ROOT/logs"

# refuse to start twice — exact argv element match (CRAFT-O-02/O-28)
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

# the staged mixture must be exactly the reviewed artifact
[ -f "$ARMS" ] || { echo "REFUSING: mixture missing: $ARMS"; exit 4; }
GOT_SHA=$(sha256sum "$ARMS" | cut -d' ' -f1)
GOT_ROWS=$(wc -l < "$ARMS")
[ "$GOT_SHA" = "$WANT_SHA" ] || { echo "REFUSING: mixture sha256 $GOT_SHA != expected $WANT_SHA"; exit 7; }
[ "$GOT_ROWS" = "$WANT_ROWS" ] || { echo "REFUSING: mixture rows $GOT_ROWS != expected $WANT_ROWS"; exit 8; }

set -a
# shellcheck disable=SC1090
[ -f "$HOME/.cyberguard-env" ] && . "$HOME/.cyberguard-env"
set +a
PY="${CYBERGUARD_VENV:-$HOME/venvs/sglang}/bin/python"
[ -x "$PY" ] || { echo "REFUSING: no interpreter at $PY"; exit 6; }

echo "launching $RUN  minutes=$MINUTES  arms=$ARMS"
echo "  mixture sha256 ${GOT_SHA:0:16}… rows=$GOT_ROWS (verified)"
echo "  interpreter: $PY"
setsid nohup env CYBERGUARD_ROOT="$ROOT" CYBERGUARD_ARMS="$ARMS" MAX_MINUTES="$MINUTES" RUN_NAME="$RUN" \
  "$PY" "$ROOT/train_cyberguard.py" > "$LOG" 2>&1 < /dev/null &
sleep 8
PID=$(trainer_pids | head -1)
echo "  pid ${PID:-NONE}  log $LOG"
[ -n "$PID" ] || { echo "REFUSING: trainer did not start; see $LOG"; exit 9; }
