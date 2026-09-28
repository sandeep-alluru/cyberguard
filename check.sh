#!/bin/bash
# check.sh — the pre-flight gate for the cyberguard scripts. Run this BEFORE any training run.
#
# Why it exists. Twice now the training script has crashed AFTER all the work was done — once on
# an unguarded `summary['held_out_loss']`, once on a receipt line referencing a variable that a
# refactor had renamed. Both times the adapter was already saved, so a 3-hour run looked like a
# failure and produced no receipt. A 20-second static check would have caught the second one.
#
# A long run must never be the thing that discovers a typo. So:
#   1. every script must compile
#   2. every script must be clean under pyflakes (undefined names, unused imports) — this is the
#      check that catches the "renamed a variable, left one reference" bug
#   3. the split must verify (row- and prompt-disjoint, deterministic, one shared loader)
#   4. the leakage audit must pass at the 0.80 near-duplicate threshold
#
# Steps 3 and 4 run on the Spark against the real corpus. Steps 1-2 run locally and are cheap.
#
# usage:  bash check.sh            # static checks only (steps 1-2)
#         bash check.sh --full     # all four (needs the Spark + the corpus)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE" || exit 1
PY=${PY:-python3}
PYFLAKES=${PYFLAKES:-$HOME/.venvs/lint/bin/pyflakes}
REMOTE=${REMOTE:-clawerdigi2@spark-40ee}
SCRIPTS=(train_cyberguard.py eval_cyberguard.py cyberguard_data.py cyberguard_contract.py verify_split.py check_leakage.py audit_corpus_safety.py
         analyse_corpus.py register_cyberguard_dsh.py test_contract.py)
rc=0

echo "== 1. compile =="
for f in "${SCRIPTS[@]}"; do
  [ -f "$f" ] || { echo "  MISSING $f"; rc=1; continue; }
  if $PY -m py_compile "$f" 2>/dev/null; then echo "  ok    $f"; else echo "  FAIL  $f"; rc=1; fi
done

echo "== 2. pyflakes (undefined names) =="
if [ -x "$PYFLAKES" ]; then
  if out=$("$PYFLAKES" "${SCRIPTS[@]}" 2>&1); then
    [ -n "$out" ] && { echo "$out"; }
    echo "  clean"
  else
    echo "$out"
    echo "  FAIL — fix the above before starting any run"
    rc=1
  fi
else
  echo "  SKIPPED: no pyflakes at $PYFLAKES"
  echo "           create it once with: python3 -m venv ~/.venvs/lint && ~/.venvs/lint/bin/pip install pyflakes"
  rc=1
fi

echo "== 3. evaluation contract discriminates =="
if $PY test_contract.py > /tmp/cyberguard-contract.out 2>&1; then
  echo "  ok — BRICK/LEAKER/MUTE rejected, DEFENDER promoted, quality + joint gates active"
else
  cat /tmp/cyberguard-contract.out
  echo "  FAIL — the evaluation contract no longer discriminates; trust no verdict from it"
  rc=1
fi

if [ "${1:-}" = "--full" ]; then
  echo "== 4. split verification (Spark) =="
  timeout 600 ssh -o BatchMode=yes "$REMOTE" \
    'source ~/.cyberguard-env; cd ~; $CYBERGUARD_VENV/bin/python verify_split.py' || rc=1

  echo "== 5. leakage audit at the 0.80 threshold (Spark) =="
  timeout 900 ssh -o BatchMode=yes "$REMOTE" \
    'source ~/.cyberguard-env; cd ~; $CYBERGUARD_VENV/bin/python check_leakage.py' || rc=1
fi

echo
[ $rc -eq 0 ] && echo "RESULT: PASS" || echo "RESULT: FAIL"
exit $rc
