#!/bin/bash
# run-flash-session.sh — run the cyber-defence research brief on Qwen3.8-Flash-Next inside a
# real, persisted DSH session.
#
# `dsh --profile headless` creates and PERSISTS a session keyed by working directory, so a
# session can be created programmatically after all — it is just not an HTTP endpoint.
#
# How the model is chosen: headless takes no --model flag, so a session created this way uses
# settings.yaml's agent-default-model. THIS SCRIPT DOES NOT CHANGE IT. It asserts the default is
# NOT spark-local, runs, and then asserts the value is byte-identical to what it was before — so
# an interrupted run leaves nothing to restore.
#
# settings.yaml is treated as READ-ONLY here, apart from a timestamped backup copy. It configures
# the harness running this very session, and mutating it is how a previous version switched the
# owner's own sessions onto a local model and failed to switch them back.
#
# WHAT WENT WRONG IN v1, so this does not repeat it:
#   * v1 redirected the headless run's STDOUT into the brief file. That stream is progress
#     output, not the answer, so when the 50-minute timeout fired the "brief" was 177 bytes of
#     a mid-flight sentence ("That last result was garbage..."). The work was never an artifact.
#   * v1 never asked the model to WRITE anything, so nothing durable existed to lose.
#   * v1 ran while the server was in `--reasoning off` mode. Flash-Next thinks by default; with
#     thinking disabled it FABRICATED a tool failure and stalled. Verified on the transcript:
#     zero corrupted tool results across 28 calls. The server is now started with THINKING=1.
#   * v1 was killed at 50 minutes while still researching. Real budget below.
#
# Therefore: the brief is written BY THE MODEL, INCREMENTALLY, to a file, and every partial
# rewrite survives a kill. stdout goes to a log. The timeout is generous.
set -u
PROJ=$HOME/AgentHub/cyberguard
SET=$HOME/.dsh/settings.yaml
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BAK=$HOME/.dsh/settings.yaml.bak-flashsession-$STAMP
LOG=$PROJ/logs/flash-session.log
BRIEF=$PROJ/logs/flash-research-brief.md
BUDGET=${BUDGET:-10800}          # 3 h. v1 used 3000 s and was cut off mid-research.
mkdir -p "$PROJ/logs"
exec >>"$LOG" 2>&1
echo "############ flash session run $(date -u +%FT%TZ) budget=${BUDGET}s"
echo "-- endpoint thinking mode: $(timeout 20 ssh -o BatchMode=yes clawerdigi1@spark-8cf2 \
  'tr "\0" " " < /proc/$(cat ~/qwen-run/qwen3.8-flash-next.pid)/cmdline 2>/dev/null | grep -o -- "--reasoning [a-z]*"' 2>/dev/null || echo unknown)"

# a fragment from a previous cut-off run must not be mistaken for this run's deliverable
if [ -s "$BRIEF" ]; then
  mv "$BRIEF" "$BRIEF.failed-$STAMP"
  echo "-- archived previous partial brief -> $BRIEF.failed-$STAMP"
fi

cp -p "$SET" "$BAK"
echo "-- backed up settings -> $BAK"

# HARD RULE — THIS SCRIPT MUST NEVER WRITE agent-default-model.
#
# An earlier version pointed the harness's GLOBAL default at spark-local/qwen3.8-flash-next for
# the duration of the run and restored it afterwards. When the run was interrupted the restore
# never executed, and the owner's own DSH sessions were left silently switched to a local model.
# Rewriting shared configuration so that one run can use one model is the wrong mechanism: the
# model for a run is a property of the RUN, not of the workstation.
#
# The mutation is therefore removed, not guarded. If a future run genuinely needs to pin a model,
# it must carry that pin itself (per-session selection), never by editing settings.yaml.
PREV=$(python3 -c "
import yaml,json
d=yaml.safe_load(open('$SET'))
print(json.dumps(d.get('agent-default-model') or {}))
")
echo "-- agent-default-model (READ ONLY, must stay untouched): $PREV"
if printf '%s' "$PREV" | grep -q "spark-local"; then
  echo "ABORT: agent-default-model already points at spark-local."
  echo "       Restore it to the hosted default before running anything. This script will not"
  echo "       fix it for you, because doing so is what caused the problem."
  exit 1
fi

# Endpoint health gate — NOT just liveness.
#
# On 2026-09-26 the old gate passed ("-- endpoint live") while every CHAT COMPLETION timed out:
# 24 `llm/retry` records ("Request timed out", TIMEOUT) across 12 headless sessions, all dead.
# A /v1/models 200 only proves the HTTP server is up. The gate must therefore be a real
# completion — the same "Reply with the word OK" smoke test that correctly failed on the sick
# endpoint (session-3d50bed0 never got a reply) and passed once the endpoint recovered.
ENDPOINT=${ENDPOINT:-http://100.118.142.51:8093}
FLASH_MODEL=${FLASH_MODEL:-qwen3.8-flash-next}
if ! curl -sf --max-time 10 -H "Authorization: Bearer dummy" "$ENDPOINT/v1/models" >/dev/null 2>&1; then
  echo "ABORT: spark-local endpoint is not answering /v1/models"
  exit 1
fi
echo "-- endpoint /v1/models live; probing an actual completion (this is what failed on 09-26)"
probe_ok=0
for attempt in 1 2 3; do
  body=$(timeout 90 curl -s -H "Content-Type: application/json" -H "Authorization: Bearer dummy" \
    -d "{\"model\":\"$FLASH_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with the word OK\"}],\"max_tokens\":512}" \
    "$ENDPOINT/v1/chat/completions" 2>/dev/null) || true
  # With thinking mode on, max_tokens can be consumed by reasoning_content and the visible
  # content may be empty (measured 2026-09-26). The failure this gate exists for is the 09-26
  # class: completions that never return at all. So: a well-formed JSON completion inside the
  # timeout is healthy; "OK" anywhere in the response (content or reasoning) is the bonus check.
  if printf '%s' "$body" | grep -q '"choices"' && printf '%s' "$body" | grep -qi 'OK'; then
    probe_ok=1; echo "-- completion probe passed (attempt $attempt)"; break
  fi
  echo "-- completion probe failed (attempt $attempt); retrying in 15s"
  sleep 15
done
if [ "$probe_ok" != 1 ]; then
  echo "ABORT: endpoint answers HTTP but completions fail/time out."
  echo "       Do NOT launch a headless run on it — every session would die mid-step as on 09-26."
  exit 1
fi

TASK="You are doing research work to design a NEW small language model for cyber defence.

Your DELIVERABLE is the file logs/flash-research-brief.md in this project. Nothing else counts
as done, and if you are stopped early whatever is in that file is all that survives.

WRITE IT INCREMENTALLY. Create the file before you research, with the section headings and a
'status: in progress' line. After each section you complete, REWRITE the whole file with
everything you have so far, using the write tool. Never leave finished work only in your reply
text. A partial brief on disk is a success; a perfect brief you never wrote down is a total
failure.

Cover, in this order, and write each section as soon as it is done:
1. The capability gap: what a 4B defensive-security model can and cannot do, honestly.
2. Data strategy: what mixture a cyber-defence model actually needs, how to avoid teaching
   offensive tooling, and how to detect that failure early.
3. Training method: chosen objective, why, and the main failure mode to watch.
4. Evaluation contract: the metrics that would decide ship / no-ship, stated so they can fail.
5. The single highest-risk assumption, and the cheapest experiment that would falsify it.

Then remove the 'status: in progress' line. Be specific and defensible. Where you are uncertain,
say so rather than inventing support. Do not pad. Finish inside about 40 tool calls."

echo "-- launching headless session in $PROJ (brief written by the model, not scraped)"
cd "$PROJ" || exit 1
timeout "$BUDGET" dsh --profile headless "$TASK" \
  > "$PROJ/logs/flash-session.stdout" 2> "$PROJ/logs/flash-session.err"
rc=$?
echo "-- headless rc=$rc (124 = hit the ${BUDGET}s budget)"

# NO settings restore, because there was no settings change. If the run was interrupted there is
# nothing to put back — which is the whole point of removing the mutation.
python3 - "$SET" "$PREV" <<'PYEOF'
import sys, json, yaml
p, prev = sys.argv[1], json.loads(sys.argv[2])
now = yaml.safe_load(open(p)).get('agent-default-model') or {}
if now != prev:
    print(f"!! agent-default-model CHANGED during the run: {prev} -> {now}")
    print("!! something else mutated shared configuration; investigate before running again.")
    sys.exit(2)
print("-- agent-default-model unchanged:", prev)
PYEOF

echo "-- brief: $(wc -c < "$BRIEF" 2>/dev/null || echo 0) bytes"
if grep -q "status: in progress" "$BRIEF" 2>/dev/null; then
  echo "-- WARNING: brief still marked in progress"
fi
echo "-- session dirs for this project:"
ls -dt "$HOME"/.dsh/sessions/*cyberguard* 2>/dev/null | head -3 | sed 's/^/   /'
echo "############ done $(date -u +%FT%TZ) rc=$rc"
exit $rc
