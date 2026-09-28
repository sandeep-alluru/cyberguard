#!/usr/bin/env bash
set -uo pipefail
source ~/.cyberguard-env
cd "$CYBERGUARD_ROOT"
LOG="$CYBERGUARD_ROOT/logs/cap-replay.log"
echo "$(date -u +%FT%TZ) LAUNCH replay" >> "$LOG"
timeout 2400 "$CYBERGUARD_VENV/bin/python" cap_replay.py >> "$LOG" 2>&1
echo "$(date -u +%FT%TZ) replay exit=$?" >> "$LOG"
