#!/usr/bin/env bash
# stage-v3.sh — stage the confirmed v3 training inputs to spark-40ee and verify them THERE.
#
# Follows stage-v2-arms.sh, including its hard-won lesson (CRAFT-O-05): transfer ONE file at a
# time and check the remote sha256 against the local value, because a multi-path transfer can
# silently move nothing while looking successful. Any mismatch aborts.
#
# DRY RUN BY DEFAULT. Nothing is written to the host without --execute. spark-40ee is read-only
# until Sandeep approves training, so this script is prepared and validated, not run.
#
# Usage:
#   bash tools/stage-v3.sh              # plan + local checks only (safe)
#   bash tools/stage-v3.sh --execute    # actually transfer (requires approval)
set -uo pipefail
HOST="${HOST:-clawerdigi2@spark-40ee}"
REMOTE_ROOT="${REMOTE_ROOT:-cyberguard}"
DRY=1
[ "${1:-}" = "--execute" ] && DRY=0
cd "$HOME/AgentHub/cyberguard" || exit 1

# local_path  remote_subdir  expected_rows
FILES=(
  "data/v3/sft/fenrir.jsonl            data/v3/sft      99730"
  "data/v3/sft/merged.jsonl            data/v3/sft      23146"
  "data/v3/sft/primus.jsonl            data/v3/sft      4891"
  "data/v3/mixture/mixture-v3-no-trail.jsonl  data/v3/mixture  140545"
)

echo "host: $HOST    mode: $([ $DRY -eq 1 ] && echo 'DRY RUN (no writes)' || echo 'EXECUTE')"
echo

# --- 1. local preconditions ---------------------------------------------------------------
fail=0
for spec in "${FILES[@]}"; do
  set -- $spec; L=$1; R=$2; N=$3
  if [ ! -f "$L" ]; then echo "  LOCAL MISSING  $L"; fail=1; continue; fi
  rows=$(wc -l < "$L")
  sha=$(sha256sum "$L" | cut -d' ' -f1)
  status="OK "
  [ "$rows" = "$N" ] || { status="ROW MISMATCH"; fail=1; }
  printf "  %-42s rows=%-7s sha=%s  %s\n" "$L" "$rows" "${sha:0:16}…" "$status"
done
[ $fail -eq 0 ] || { echo; echo "ABORT: local preconditions failed"; exit 1; }

# --- 2. host preconditions (read-only checks) ---------------------------------------------
echo
echo "  host checks (read-only):"
ssh -o BatchMode=yes -o ConnectTimeout=12 "$HOST" 'bash -s' <<'REMOTE'
set -uo pipefail
# refuse to stage while a trainer is live (same guard run-v2-arm.sh uses: match the argv element
# exactly, never a substring scan that matches any shell merely mentioning the file)
live=""
for p in /proc/[0-9]*; do
  exe=$(readlink -f "$p/exe" 2>/dev/null) || continue
  case "$exe" in *python*) ;; *) continue;; esac
  while IFS= read -r -d '' a; do
    case "$a" in */train_cyberguard.py|train_cyberguard.py) live="${p#/proc/}"; break;; esac
  done < "$p/cmdline" 2>/dev/null
  [ -n "$live" ] && break
done
[ -n "$live" ] && { echo "  TRAINER RUNNING pid=$live"; exit 3; }
echo "  no trainer running"
df -h "$HOME" | tail -1 | sed 's/^/  disk: /'
venv="${CYBERGUARD_VENV:-$HOME/venvs/sglang}"
[ -x "$venv/bin/python" ] && echo "  interpreter: $venv/bin/python (present)" || echo "  WARNING: interpreter missing at $venv/bin/python"
REMOTE
rc=$?
[ $rc -eq 0 ] || { echo; echo "ABORT: host preconditions failed (rc=$rc)"; exit 1; }

# --- 3. transfer + verify, ONE FILE AT A TIME --------------------------------------------
echo
for spec in "${FILES[@]}"; do
  set -- $spec; L=$1; R=$2; N=$3
  WANT=$(sha256sum "$L" | cut -d' ' -f1)
  echo "  $L -> $HOST:~/$REMOTE_ROOT/$R/"
  if [ $DRY -eq 1 ]; then
    echo "    (dry run: would rsync, then verify sha256 + row count on the host)"
    continue
  fi
  ssh -o BatchMode=yes "$HOST" "mkdir -p ~/$REMOTE_ROOT/$R" || { echo "    ABORT: mkdir failed"; exit 1; }
  rsync -a --info=progress2 "$L" "$HOST:~/$REMOTE_ROOT/$R/$(basename "$L")" >/dev/null 2>&1
  read -r GOT_SHA GOT_ROWS < <(ssh -o BatchMode=yes "$HOST" \
    "sha256sum ~/$REMOTE_ROOT/$R/$(basename "$L") | cut -d' ' -f1; wc -l < ~/$REMOTE_ROOT/$R/$(basename "$L")" 2>/dev/null | paste -sd' ')
  if [ "$GOT_SHA" = "$WANT" ] && [ "$GOT_ROWS" = "$N" ]; then
    echo "    OK  sha=${GOT_SHA:0:16}…  rows=$GOT_ROWS (matches local)"
  else
    echo "    MISMATCH local_sha=$WANT remote_sha=$GOT_SHA local_rows=$N remote_rows=$GOT_ROWS"
    exit 1
  fi
done

echo
if [ $DRY -eq 1 ]; then
  echo "DRY RUN complete — nothing was written to $HOST. Re-run with --execute after approval."
else
  echo "staged and hash-verified on $HOST"
fi
