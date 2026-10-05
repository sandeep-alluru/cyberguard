#!/usr/bin/env bash
# A11 (owner-approved): all external-model review goes through the GOVERNED adapter.
# Direct codex invocation removed; ungoverned entry points are rejected by
# tools/scan_review_invocations.py.

# dispatch_review.sh — dispatch a Codex-Astra review with the revision and spec hash SUBSTITUTED AND VERIFIED.
#
# Two failures this exists to prevent, each of which produced a review of the wrong thing:
#   * an unquoted heredoc executed the prompt's backticks, so the reviewer received a mangled prompt;
#   * a stale revision string hardcoded inside the prompt body, so review #16 assessed a revision that was not
#     checked out ("Revision identification differs from the proposal") — its own finding, and mine to fix.
#
# usage: bash v2/dispatch_review.sh <n> <body-file> [--no-dispatch]
#   The body may use {{REV}} and {{SPEC_SHA}}; both are substituted, and the revision's presence is asserted.
set -uo pipefail
N="${1:?usage: dispatch_review.sh <n> <body-file> [--no-dispatch]}"
BODY="${2:?usage: dispatch_review.sh <n> <body-file> [--no-dispatch]}"
MODE="${3:-}"
ROOT="$HOME/AgentHub/cyberguard"; cd "$ROOT"
REV=$(git rev-parse --short=12 HEAD)
SPEC_SHA=$(sha256sum docs/SPEC-V2.md | cut -d' ' -f1)
OUT="research-tmp/reviews/codex-review-${N}.md"
PROMPT="research-tmp/reviews/codex-review-${N}-prompt.md"
[ -f "$BODY" ] || { echo "REFUSING: no prompt body at $BODY"; exit 2; }
mkdir -p research-tmp/reviews

python3 - "$BODY" "$PROMPT" "$REV" "$SPEC_SHA" <<'PY'
import pathlib, sys
body, out, rev, sha = sys.argv[1:5]
t = pathlib.Path(body).read_text()
t = t.replace("{{REV}}", rev).replace("{{SPEC_SHA}}", sha)
assert "{{" not in t, "a placeholder was left unreplaced"
assert rev in t, "the revision does not appear -- the reviewer cannot know what it is reviewing"
pathlib.Path(out).write_text(t)
print(f"  prompt written: {out} ({len(t)} bytes), rev={rev}, spec_sha={sha[:16]}")
PY
grep -qF "$REV" "$PROMPT" || { echo "REFUSING: $REV absent from the prompt"; exit 3; }

if [ "$MODE" = "--no-dispatch" ]; then
  echo "  --no-dispatch: prompt verified, nothing launched"
  exit 0
fi
nohup tools/astra_review.sh packet.json
  < "$PROMPT" > "research-tmp/reviews/codex-review-${N}.log" 2>&1 &
sleep 4
echo "  review #$N dispatched -> $OUT (rev $REV, spec $SPEC_SHA)"
