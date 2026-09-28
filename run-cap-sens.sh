#!/usr/bin/env bash
set -uo pipefail
source ~/.cyberguard-env
cd "$CYBERGUARD_ROOT"
LOG="$CYBERGUARD_ROOT/logs/cap-sens.log"
echo "$(date -u +%FT%TZ) LAUNCH sens" >> "$LOG"
timeout 3600 "$CYBERGUARD_VENV/bin/python" cap_sens.py >> "$LOG" 2>&1
echo "$(date -u +%FT%TZ) sens exit=$?" >> "$LOG"
