#!/usr/bin/env bash
# arm_c24_timeline.sh — the remaining CyberGuard v2 timeline, armed so it runs whether or not an agent round
# is scheduled. Owner instruction (2026-09-29): "if the review doesnt work you move forward dont stop with the
# work" — so the contract is NOT gated on a review marker. The reviews are still run and their state is
# recorded in the verdict; they just cannot halt the work.
#
#  02:25  C16 metrics           00:00s
#  02:27  C16 brief (portal-verified)
#  09:45  chain gate attempt 1 (records a clearance if a review gives one; nothing depends on it)
#  10:20  chain gate attempt 2
#  10:25  C24 metrics (training is scheduled to end here)
#  10:27  C24 brief (portal-verified)
#  10:28  C24 evaluation contract, then the harvest — unconditionally
#
# Usage: bash v2/arm_c24_timeline.sh          (run in the background)
set -uo pipefail
ROOT="$HOME/AgentHub/cyberguard"
cd "$ROOT"
LOG="logs/timeline-$(date +%Y%m%d).log"
say() { echo "[$(date '+%F %T %Z')] $*" | tee -a "$LOG"; }

wait_until() {  # epoch seconds
  local now; now=$(date +%s)
  local d=$(( $1 - now ))
  [ "$d" -gt 0 ] && sleep "$d"
}

at() { date -d "$1" +%s; }

say "timeline armed (C16 02:25, C24 10:25, contract 10:28 unconditional)"

wait_until "$(at 'today 02:25')"
say "C16 metrics"; bash v2/checkpoint_metrics.sh C16 2>&1 | tail -6 | tee -a "$LOG"
wait_until "$(at 'today 02:27')"
say "C16 brief"; python3 v2/checkpoint_brief.py C16 2>&1 | tail -3 | tee -a "$LOG"

wait_until "$(at 'today 09:45')"
say "chain gate attempt 1 (informational)"; python3 v2/chain_gate.py 2>&1 | tee -a "$LOG"
if [ ! -f docs/CHAIN-CLEARED ]; then
  wait_until "$(at 'today 10:20')"
  say "chain gate attempt 2"; python3 v2/chain_gate.py 2>&1 | tee -a "$LOG"
fi

wait_until "$(at 'today 10:25')"
say "C24 metrics (training end)"; bash v2/checkpoint_metrics.sh C24 2>&1 | tail -6 | tee -a "$LOG"
wait_until "$(at 'today 10:27')"
say "C24 brief"; python3 v2/checkpoint_brief.py C24 2>&1 | tail -3 | tee -a "$LOG"

wait_until "$(at 'today 10:28')"
say "C24 CONTRACT starting unconditionally"
if [ -f docs/CHAIN-CLEARED ]; then
  say "review clearance present: $(head -2 docs/CHAIN-CLEARED | tr '\n' ' ')"
else
  say "no review clearance marker — proceeding anyway per owner instruction; the verdict records this"
fi
bash v2/run_c24_contract.sh 2>&1 | tee -a "$LOG" | tail -30
say "contract exit=$?"
say "harvest"; bash harvest-v2.sh 2>&1 | tail -5 | tee -a "$LOG"
say "timeline complete: VERDICT-v2 exists=$([ -s docs/VERDICT-v2.md ] && echo yes || echo NO)"
