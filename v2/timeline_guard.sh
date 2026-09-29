#!/usr/bin/env bash
# timeline_guard.sh — keep the C24 timeline alive, without the ability to duplicate it.
#
# WHY. The timeline is the only actor that runs the C24 evaluation contract, and nothing restarts it: no cron entry,
# no systemd timer (this machine's timers belong to other projects), and the watchdog is observational by design —
# it hashes the arms and writes alerts, it launches nothing. If the timeline died before 12:10 — an OOM kill, a
# stray signal, the fallout of a reboot — the contract would never run and the whole window would end with no
# verdict, no harvest and no terminal brief. Every other failure on the critical path has a second chance; this one
# had none.
#
# WHY IT CANNOT DUPLICATE THE TIMELINE. The timeline takes an atomic `mkdir` lock and REFUSES to start while a live
# timeline holds it (exit 75), reclaiming it only when the recorded pid is dead *and* its /proc cmdline no longer
# matches. So the guard's worst case is a no-op refusal and its best case is exactly the recovery needed — and it
# asks the lock, not a process name, which is what makes a supervisor safe here rather than a second source of the
# duplicate-timeline hazard it exists to prevent.
#
#   usage: bash v2/timeline_guard.sh          (GUARD_HOURS, GUARD_INTERVAL, GUARD_LOG, TL_LOCK, GUARD_LAUNCH override)
#   exit 0 after its window; it never exits because the timeline it watches has gone
set -uo pipefail
ROOT="$HOME/AgentHub/cyberguard"
cd "$ROOT"
LOCK="${TL_LOCK:-v2/.c24-timeline.lock}"
HOURS="${GUARD_HOURS:-24}"
INTERVAL="${GUARD_INTERVAL:-300}"
LOG="${GUARD_LOG:-logs/timeline-guard.log}"
LAUNCH="${GUARD_LAUNCH:-bash v2/arm_c24_timeline.sh}"
say() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

holder_alive() {   # 1 if the lock names a live arm_c24_timeline.sh
  local p
  p=$(cat "$LOCK/pid" 2>/dev/null) || return 1
  [ -n "$p" ] && [ -d "/proc/$p" ] || return 1
  tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q 'arm_c24_timeline\.sh'
}

deadline=$(( $(date +%s) + HOURS * 3600 ))
cycles=0
say "guard starting: every ${INTERVAL}s for ${HOURS}h, watching $LOCK"
while [ "$(date +%s)" -lt "$deadline" ]; do
  cycles=$((cycles + 1))
  if holder_alive; then
    # Healthy. A heartbeat every ~30 min, because a guard that is silent when healthy is indistinguishable from a
    # guard that has died — and the whole point of this process is that someone notices when nothing else does.
    [ $((cycles % 6)) -eq 0 ] && say "cycle $cycles: timeline $(cat "$LOCK/pid" 2>/dev/null) is alive"
  else
    say "cycle $cycles: NO live timeline holds $LOCK — launching one"
    setsid nohup $LAUNCH >> logs/timeline-arm.out 2>&1 &
    sleep 6
    if holder_alive; then
      say "  recovered: holder is now $(cat "$LOCK/pid" 2>/dev/null)"
    else
      say "  the launch produced no live holder (it may have refused a lock that appeared in between) — retrying next cycle"
    fi
  fi
  sleep "$INTERVAL" & wait $!      # interruptible, so a stop signal is not deferred until the poll ends
done
say "guard finished its ${HOURS}h window after $cycles cycle(s)"
