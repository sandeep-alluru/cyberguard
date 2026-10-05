#!/usr/bin/env bash
# CyberGuard v3 — recurring Codex-Astra review cycle.
#
# Usage:  tools/review_cycle.sh <cycle_number> [--delay-seconds N]
#
# Every cycle:
#   0. is CHANGE-TRIGGERED, not timed (owner directive 2026-09-30): run it after training completes,
#      before any eval scoring run, and after any substantive plan revision. The old 3-hourly timer was
#      cut as over-engineering -- re-reading a frozen document burns budget without catching defects.
#      `--delay-seconds` remains available but should not be used as a standing timer.
#   1. snapshots the live measured state (tools/trails_state.py) and the plan hash;
#   2. builds a BOUNDARY-scoped read-only review prompt;
#   3. runs `codex exec -m gpt-6-astra -s read-only --skip-git-repo-check`;
#   4. writes prompt + output + stderr and appends to docs/PLAN-V3-cycle-review.log;
#   5. prints the verdict line so a supervising job can surface it.
#
# NOTE ON FLAGS: the install is codex-cli 0.155.1, which has no `--approval-mode`
# flag (it errors out). The working equivalent used for passes 1-5 is
# `-s read-only --skip-git-repo-check` with stdin closed, which cannot prompt and
# cannot write. That is what this script uses.
set -u
REPO=/home/clawer-samurai-1/AgentHub/cyberguard
cd "$REPO" || exit 1

N="${1:?usage: review_cycle.sh <cycle_number> [--delay-seconds N]}"
DELAY=0
if [ "${2:-}" = "--delay-seconds" ]; then DELAY="${3:-0}"; fi

OUTDIR="$REPO/research-tmp/reviews"
mkdir -p "$OUTDIR"
PROMPT="$OUTDIR/plan-v3-cycle${N}-prompt.md"
OUTPUT="$OUTDIR/plan-v3-cycle${N}-output.txt"
STDERR="$OUTDIR/plan-v3-cycle${N}-stderr.txt"
LOG="$REPO/docs/PLAN-V3-cycle-review.log"

if [ "$DELAY" -gt 0 ]; then
  echo "[cycle $N] sleeping ${DELAY}s before review ($(date '+%F %T'))"
  sleep "$DELAY"
fi

TS=$(date '+%Y-%m-%d %H:%M:%S %Z')
STATE=$(python3 "$REPO/tools/trails_state.py" 2>&1)
PREV=$(ls -1 "$OUTDIR"/plan-v3-cycle*-output.txt 2>/dev/null | tail -3 | sed 's#.*/##')

cat > "$PROMPT" <<PROMPT_EOF
# Codex-Astra independent review — CyberGuard v3 (recurring cycle $N)

You are an independent technical reviewer. This is recurring review cycle $N of the
CyberGuard v3 training plan, commissioned by the owner to run every 3 hours.
Review history lives in \`docs/PLAN-V3-review.log\` and \`docs/PLAN-V3-cycle-review.log\`.
Previous cycle outputs (most recent last): ${PREV:-none}

Your job is adversarial technical review. Find real problems. Do not rubber-stamp.
VERIFY claims against the actual files, recompute the math, and confirm that every
cross-reference exists and says what the text claims. If something is asserted but
not evidenced, that is a finding.

## BOUNDARY

- You are READ-ONLY review. Do not modify any file, do not start training, do not
  touch or re-derive any dataset, do not run anything that writes to the repo.
- Scope is strictly \`/home/clawer-samurai-1/AgentHub/cyberguard/docs/PLAN-V3.md\`
  as a plan document, plus the live measured state supplied below. Judge what it
  says, not what you would design instead.
- Owner constraints that any suggestion must respect: no hyperparameter search for
  this ship run; one arm (no A/B contrast); no new data source without an
  admission-gate run; no training start before the owner's explicit final approval;
  no \`dsh\` CLI invocation anywhere.
- Output a numbered list of FINDINGS. Each finding: severity (Critical / Major /
  Minor), what is wrong or unverified, and the concrete fix or evidence required.
  End with an overall verdict line: APPROVE, APPROVE-WITH-CHANGES, or REJECT,
  followed by a one-paragraph reason.

## Over-engineering lens (MANDATORY — owner directive, permanent)

Every validation step, gate, check and piece of machinery must earn its place. Sandeep's standing rule:
nothing may slow, block or tax the work; verification stays harness-level and reusable; per-job gates
and watchdogs that burn budget without catching real defects are out. You MUST include a section
titled **"Over-engineering"** that:
- names machinery in the plan that does not change the ship decision, and says what to cut;
- names machinery added by the fixes in response to earlier review rounds that is now
  disproportionate to what it decides (review-driven accretion is the most common form here);
- explicitly lists what EARNS its place, so cuts are not blind;
- if nothing is over-engineered, says so plainly rather than inventing a finding.
Cutting is a legitimate and expected finding; a plan that only grows is a failing plan.

## Review checklist (cover each)

1. Do the declared row counts and derived presentation totals recompute exactly
   from the stated inputs (including the teacher-trail block actually described)?
2. Is every gate in §8 falsifiable and measurable as written, with acceptance
   criteria, and does §8.7's ship rule follow from them?
3. Does the plan's description of the trails match the live measured state below
   (counts, coverage, missing-marker rows, refusals), and is the admission gate
   specified well enough to be run?
4. Are the training host and pre-flight claims accurate for the host now named?
5. Does any section contradict another, and did this revision weaken any gate
   relative to the prior reviewed revision?
6. Anything previously-reviewed and now stale, or any new unfalsifiable claim?

## Live measured state (supplied by the supervisor, $TS)

$STATE

## Plan under review

Read the file yourself at the path in BOUNDARY. Report what it actually says.
PROMPT_EOF

echo "[cycle $N] prompt built ($(wc -c < "$PROMPT") bytes); invoking gpt-6-astra at $TS"
timeout 2700 codex exec -m gpt-6-astra -s read-only --skip-git-repo-check \
  "$(cat "$PROMPT")" > "$OUTPUT" 2> "$STDERR" < /dev/null
RC=$?
{
  echo "EXIT:$RC"
} >> "$OUTPUT"

{
  echo ""
  echo "==================================================================="
  echo "## Cycle $N — $TS  (exit $RC)"
  echo "prompt: research-tmp/reviews/plan-v3-cycle${N}-prompt.md"
  echo "output: research-tmp/reviews/plan-v3-cycle${N}-output.txt"
  echo "-------------------------------------------------------------------"
  cat "$OUTPUT"
} >> "$LOG"

VERDICT=$(grep -aoE 'APPROVE-WITH-CHANGES|APPROVE|REJECT' "$OUTPUT" | tail -1)
echo "[cycle $N] exit=$RC verdict=${VERDICT:-UNKNOWN} output=$OUTPUT"
