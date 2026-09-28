#!/usr/bin/env bash
# serve_guard_check.sh — assert the serving posture recorded in SPEC-V2 §10: v1 is NOT served.
# Exit 0 means: no local listener on the project's port, and no DSH provider entry for the model.
set -uo pipefail
fail=0
if ss -tlnp 2>/dev/null | grep -qE ':18081'; then
  echo "FAIL: something is listening on :18081 — serving posture violated"; fail=1
else
  echo "OK   no listener on :18081"
fi
if grep -q "cyberguard-4b" "$HOME/.dsh/settings.yaml" 2>/dev/null; then
  echo "FAIL: a DSH provider entry exists for cyberguard-4b"; fail=1
else
  echo "OK   no DSH provider entry for cyberguard-4b"
fi
exit $fail
