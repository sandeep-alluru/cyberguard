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

# GRACE-SKIP. A re-arm is a normal event (this script has been restarted three times while the CLI, the
# trainer patch and the checkpoints changed), and plain `wait_until` treats a time already in the past as
# "fire now" — so restarting at 06:14 RE-RAN the 05:50 checkpoint, overwriting its metrics snapshot and writing
# a duplicate brief whose predecessor still cited that file as its source. An event more than GRACE_MIN past is
# now skipped, and the caller logs the skip.
GRACE_MIN="${GRACE_MIN:-5}"
wait_until() {  # epoch seconds; returns 1 if the target already passed by more than GRACE_MIN
  local now; now=$(date +%s)
  local d=$(( $1 - now ))
  [ "$d" -lt $(( -GRACE_MIN * 60 )) ] && return 1
  [ "$d" -gt 0 ] && sleep "$d"
  return 0
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
  if ! wait_until "$(at "$_t")"; then
    say "checkpoint $_lab ($_t) already passed by more than ${GRACE_MIN} min — SKIPPING, so a restart cannot"
    say "  overwrite its metrics snapshot or duplicate its brief"
    continue
  fi
  say "checkpoint $_lab metrics"; bash v2/checkpoint_metrics.sh "$_lab" 2>&1 | tail -6 | tee -a "$LOG"
  say "checkpoint $_lab brief"; python3 v2/checkpoint_brief.py "$_lab" 2>&1 | tail -3 | tee -a "$LOG"
  say "checkpoint $_lab review (Astra)"; bash v2/checkpoint_review.sh "$_lab" 2>&1 | tail -2 | tee -a "$LOG"
done < <(printf '%s\n' "$MID_AT" | tr ',' '\n')

if wait_until "$(at "$C24_AT")"; then
  say "C24 metrics"; bash v2/checkpoint_metrics.sh C24 2>&1 | tail -6 | tee -a "$LOG"
else
  say "C24 metrics ($C24_AT) already passed — skipping (see the GRACE_MIN note above)"
fi

if wait_until "$(at "$BRIEF_AT")"; then
  say "C24 brief"; python3 v2/checkpoint_brief.py C24 2>&1 | tail -3 | tee -a "$LOG"
  # The cadence is "an Astra review at EVERY checkpoint", and the mid-window loop dispatches one per checkpoint —
  # but the C24 step, the terminal and most important checkpoint, had a brief and NO review. Dispatched here; it
  # is a codex call with no GPU, so it runs concurrently with the contract starting at 12:10, and the contract is
  # not gated on it (owner instruction).
  say "C24 review (Astra)"; bash v2/checkpoint_review.sh C24 2>&1 | tail -2 | tee -a "$LOG"
else
  say "C24 brief ($BRIEF_AT) already passed — skipping (and its review, for the same reason)"
fi

wait_until "$(at "$CONTRACT_AT")"
say "C24 CONTRACT starting unconditionally (stage 00 waits for both trainers to exit)"
if [ -f docs/CHAIN-CLEARED ]; then
  say "review clearance present: $(head -2 docs/CHAIN-CLEARED | tr '\n' ' ')"
else
  say "no review clearance marker — proceeding anyway per owner instruction; the verdict records this"
fi
# Capture the status of the CONTRACT, not of a downstream pipe (`| tee` would report tee's exit status).
if [ -s docs/VERDICT-v2.md ] && [ -s v2/gate-report-v2.json ]; then
  # The deliverable exists: a restart after 12:10 must not repeat ~11 hours of GPU work. (A deliberate re-run is
  # still possible by removing the verdict, which is a visible act rather than an accident.)
  say "VERDICT-v2 and the gate report already exist — NOT re-running the contract on this arm"
  rc=0
else
bash v2/run_c24_contract.sh > logs/c24-contract.log 2>&1
rc=$?
tail -40 logs/c24-contract.log | tee -a "$LOG"
say "contract exit=$rc (full log logs/c24-contract.log)"
if [ "$rc" != 0 ]; then
  # ONE automatic re-run. The contract is ~11 h of unattended work across two hosts, and a single transient
  # failure — an ssh blip, a momentary GPU error, a killed battery — would otherwise discard the entire window's
  # evaluation. Stage 0pre quarantines the failed attempt's outputs (locally and on the hosts), so the re-run
  # starts from a clean evals/ rather than consuming a partial result. A deterministic failure simply fails
  # twice, for the cost of one more attempt.
  say "contract FAILED (exit $rc) — re-running once in 60 s; stage 0pre quarantines the failed attempt's outputs"
  sleep 60
  bash v2/run_c24_contract.sh > logs/c24-contract-attempt2.log 2>&1
  rc=$?
  tail -40 logs/c24-contract-attempt2.log | tee -a "$LOG"
  say "contract second attempt exit=$rc (full log logs/c24-contract-attempt2.log)"
fi
fi

# The contract's STAGE 7 ALREADY HARVESTED into the same DEST. Re-running it here would TRUNCATE the manifest
# stage 7 produced (`harvest-v2.sh` does `: > "$DEST/MANIFEST.sha256"` at the start of every run) and re-pull
# ~50 files from both hosts; a transient failure on any single pull would then leave a SHORTER manifest,
# silently downgrading the checksum-verified-harvest deliverable — and this line never checked the exit status
# either. Run it only when the contract did not produce a manifest, and report the status when it does.
MAN="research-tmp/harvest-v2/MANIFEST.sha256"
if [ -s "$MAN" ] && grep -qF "VERDICT-v2.md" "$MAN"; then
  say "harvest already complete in the contract's stage 7 ($(wc -l < "$MAN") files, including the verdict)"
  say "  not re-running it: the manifest must not be truncated by a redundant pass"
else
  say "harvest (the contract produced no manifest, so this is the only pass)"
  bash harvest-v2.sh > logs/harvest-timeline.log 2>&1
  hrc=$?
  tail -5 logs/harvest-timeline.log | tee -a "$LOG"
  say "harvest exit=$hrc (no manifest in the contract means a failure here leaves the deliverable missing, not partial)"
fi
# The TERMINAL checkpoint gets its brief too. The cadence requires "a dated CEO-desk brief per checkpoint", and
# this one was missing: the timeline's last act was to log whether VERDICT-v2 exists, so ~11 hours of unattended
# work would have delivered the headline artifact with no CEO-facing summary of what it decided. It composes from
# the artifacts only (the gate report, the verdict's sha256, the harvest manifest, FACTS) and REFUSES to write a
# brief that would announce a verdict which is not there - so a failed contract produces a logged refusal, not a
# confident brief.
say "verdict brief (the terminal checkpoint)"; python3 v2/verdict_brief.py 2>&1 | tail -3 | tee -a "$LOG"
say "timeline complete: VERDICT-v2 exists=$([ -s docs/VERDICT-v2.md ] && echo yes || echo NO)"
