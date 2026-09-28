#!/usr/bin/env bash
set -uo pipefail
source ~/.cyberguard-env
cd "$CYBERGUARD_ROOT"
LOG="$CYBERGUARD_ROOT/logs/cap-harness.log"
echo "$(date -u +%FT%TZ) LAUNCH cap box budget=180min" >> "$LOG"
timeout 11400 "$CYBERGUARD_VENV/bin/python" cap_harness.py >> "$LOG" 2>&1
echo "$(date -u +%FT%TZ) cap harness exit=$?" >> "$LOG"
