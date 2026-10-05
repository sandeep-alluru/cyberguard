#!/usr/bin/env bash
# micro_test.sh — live micro tests. Small, real, FAILABLE checks against the ACTUAL artifact.
#
# Owner requirement (approval 2026-10-05): every delivered artifact must be proven by a live micro test
# that can actually fail -- not a pass-count vanity metric.
#
# A micro test MUST be able to fail. Each test below asserts a specific observable property of the real
# file/behavior. Run against a deliberately broken copy to confirm the test fails; a test that cannot fail
# is not evidence.
#
#   tools/micro_test.sh [artifact ...]     run all, or only the named artifacts
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PASS=0; FAIL=0; SKIP=0
t() { # t <name> <artifact> <command...>  -- command must exit 0 on the REAL artifact
  local name="$1" art="$2"; shift 2
  if [ ! -e "$art" ]; then printf "  SKIP  %-46s (artifact absent: %s)\n" "$name" "$art"; SKIP=$((SKIP+1)); return; fi
  if "$@" >/dev/null 2>&1; then printf "  PASS  %-46s %s\n" "$name" "$art"; PASS=$((PASS+1))
  else printf "  FAIL  %-46s %s\n" "$name" "$art"; FAIL=$((FAIL+1)); fi
}
echo "== live micro tests (real artifact, failable) =="
echo "-- A01/A02: OWNER-DECISION must contain the withdrawal, not just append it"
t "withdrawal present"            docs/dsh/OWNER-DECISION.md  grep -q "I withdraw the restricted composition" docs/dsh/OWNER-DECISION.md
t "separate-identity ruling present" docs/dsh/OWNER-DECISION.md grep -q "separate OS identity" docs/dsh/OWNER-DECISION.md
echo "-- A03: ARCHITECTURE must not claim it was not persisted"
t "no stale 'not persisted' claim" docs/dsh/ARCHITECTURE.md   bash -c '! grep -q "not persisted" docs/dsh/ARCHITECTURE.md'
echo "-- A08: gate must EXECUTE, not merely print"
t "gate refuses an invented id"    tools/astra_gate.py          bash -c '! python3 tools/astra_gate.py D99 -- true'
echo "-- A10: review wrapper must NOT suppress failure status"
t "no '|| true' suppression"       tools/astra_review.sh        bash -c '! grep -q "|| true" tools/astra_review.sh'
echo "-- A11: launchers must not call codex directly"
t "review_cycle.sh clean"          tools/review_cycle.sh        bash -c '! grep -q "codex exec" tools/review_cycle.sh'
t "dispatch_review.sh clean"       v2/dispatch_review.sh        bash -c '! grep -q "codex exec" v2/dispatch_review.sh'
t "checkpoint_review.sh clean"     v2/checkpoint_review.sh      bash -c '! grep -q "codex exec" v2/checkpoint_review.sh'
echo "-- A13: accounting must not write zero placeholders"
t "no zero placeholder tokens"     docs/review-accounting.jsonl bash -c '! grep -q "\"input_tokens\": 0" docs/review-accounting.jsonl'
echo "-- A18: acceptance dir must not be empty"
t "acceptance/ has evidence"       docs/dsh/acceptance          bash -c '[ -n "$(ls -A docs/dsh/acceptance 2>/dev/null)" ]'
echo "-- A19: scanner named in gate allowance must exist"
t "scan_review_invocations exists" tools/scan_review_invocations.py test -f tools/scan_review_invocations.py
echo
echo "== result: $PASS pass  $FAIL fail  $SKIP skip =="
[ "$FAIL" -eq 0 ] || exit 1
