#!/usr/bin/env bash
# arm_c24_timeline.sh — the remaining CyberGuard v2 timeline, armed so it runs whether or not an agent round
# is scheduled. Owner instruction (2026-09-29): "if the review doesnt work you move forward dont stop with the
# work" — so the contract is NOT gated on a review marker. The reviews are still run and their state is
# recorded in the verdict; they just cannot halt the work.
#
# RE-ARMED 2026-09-29 02:45 after the no-op-resume discovery (v2/data/mixture/noop-resume.receipt.json): the
# 23:29 relaunch called PeftModel.from_pretrained(..., is_trainable=False), which froze every LoRA parameter,
# so it trained NOTHING for 3.05 h per arm while reporting "trainable params: 0" and grad_norm 0 throughout.
# Training was stopped, the defect fixed (is_trainable=True + a refuse-to-train-on-0-trainable-params guard),
# and a capped continuation relaunched at 02:32:53 with 570 min on the clock — ending 12:02 instead of 10:25.
# The contract therefore moves to 12:10, and stage 00 of the contract now waits for the trainers to exit.
#
#  11:55  C24 metrics
#  11:57  C24 brief (portal-verified)
#  12:10  C24 evaluation contract, then the harvest — unconditionally
#
# Times are overridable, so a future re-arm is a parameter rather than a rewrite:
#   C24_AT, BRIEF_AT, CONTRACT_AT, TIMELINE_LOG (and TRAINER_WAIT_MIN, which the contract reads directly).
set -uo pipefail
ROOT="$HOME/AgentHub/cyberguard"
cd "$ROOT"
C24_AT="${C24_AT:-today 11:55}"
BRIEF_AT="${BRIEF_AT:-today 11:57}"
CONTRACT_AT="${CONTRACT_AT:-today 12:10}"
LOG="${TIMELINE_LOG:-logs/timeline-$(date +%Y%m%d).log}"
say() { echo "[$(date '+%F %T %Z')] $*" | tee -a "$LOG"; }

wait_until() {  # epoch seconds
  local now; now=$(date +%s)
  local d=$(( $1 - now ))
  [ "$d" -gt 0 ] && sleep "$d"
}
at() { date -d "$1" +%s; }

say "timeline re-armed: C24 $C24_AT | brief $BRIEF_AT | contract $CONTRACT_AT  (post no-op-resume fix)"

# 3-hourly mid-window checkpoints, each with its own dated brief AND its own Astra review — the owner's cadence
# is a checkpoint every 3 hours with a review at every one, and nothing was scheduled between now and C24.
# COMMA-separated on purpose. Written space-separated first, and shell word splitting turned
# "today 05:50 today 08:50" into four values whose first was "today" -> today 00:00 -> already past -> the
# loop fired the 05:50 checkpoint at 02:51 instead of waiting three hours. Read one entry per line so a value
# can safely contain a space.
MID_AT="${MID_AT:-today 05:50,today 08:50}"
MID_LABELS="${MID_LABELS:-M2,M3}"
_i=0
while IFS= read -r _t; do
  [ -n "$_t" ] || continue
  _i=$((_i + 1))
  _lab=$(printf '%s' "$MID_LABELS" | cut -d, -f"$_i")
  [ -n "$_lab" ] || { say "no label for checkpoint time '$_t' — skipping"; continue; }
  wait_until "$(at "$_t")"
  say "checkpoint $_lab metrics"; bash v2/checkpoint_metrics.sh "$_lab" 2>&1 | tail -6 | tee -a "$LOG"
  say "checkpoint $_lab brief"; python3 v2/checkpoint_brief.py "$_lab" 2>&1 | tail -3 | tee -a "$LOG"
  say "checkpoint $_lab review (Astra)"; bash v2/checkpoint_review.sh "$_lab" 2>&1 | tail -2 | tee -a "$LOG"
done < <(printf '%s\n' "$MID_AT" | tr ',' '\n')

wait_until "$(at "$C24_AT")"
say "C24 metrics"; bash v2/checkpoint_metrics.sh C24 2>&1 | tail -6 | tee -a "$LOG"

wait_until "$(at "$BRIEF_AT")"
say "C24 brief"; python3 v2/checkpoint_brief.py C24 2>&1 | tail -3 | tee -a "$LOG"

wait_until "$(at "$CONTRACT_AT")"
say "C24 CONTRACT starting unconditionally (stage 00 waits for both trainers to exit)"
if [ -f docs/CHAIN-CLEARED ]; then
  say "review clearance present: $(head -2 docs/CHAIN-CLEARED | tr '\n' ' ')"
else
  say "no review clearance marker — proceeding anyway per owner instruction; the verdict records this"
fi
# Capture the status of the CONTRACT, not of a downstream pipe (`| tee` would report tee's exit status).
bash v2/run_c24_contract.sh > logs/c24-contract.log 2>&1
rc=$?
tail -40 logs/c24-contract.log | tee -a "$LOG"
say "contract exit=$rc (full log logs/c24-contract.log)"

say "harvest"; bash harvest-v2.sh 2>&1 | tail -5 | tee -a "$LOG"
say "timeline complete: VERDICT-v2 exists=$([ -s docs/VERDICT-v2.md ] && echo yes || echo NO)"
