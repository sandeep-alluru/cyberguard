#!/usr/bin/env bash
# checkpoint_review.sh — the Astra review the owner's cadence requires AT EVERY CHECKPOINT.
#
# Owner cadence: "a checkpoint every 3 hours, an Astra review at every checkpoint with findings fixed before
# proceeding, and a dated CEO-desk brief per checkpoint." The brief and the metrics existed; the review was
# being run by hand, which means an unattended stretch could pass a checkpoint with no review at all. This
# dispatches it against the SAME evidence the brief quotes, and leaves the finding file for the next round.
#
#   usage: bash v2/checkpoint_review.sh <label> [--dry-run]
#   writes: research-tmp/reviews/checkpoint-<label>-review.md
set -uo pipefail
LABEL="${1:?usage: checkpoint_review.sh <label> [--dry-run]}"
DRY=0; [ "${2:-}" = "--dry-run" ] && DRY=1
ROOT="$HOME/AgentHub/cyberguard"; cd "$ROOT"
M="research-tmp/checkpoints/${LABEL}-metrics.json"
OUT="research-tmp/reviews/checkpoint-${LABEL}-review.md"
PROMPT="research-tmp/reviews/checkpoint-${LABEL}-review-prompt.md"
mkdir -p research-tmp/reviews
[ -f "$M" ] || { echo "REFUSING: $M does not exist — run v2/checkpoint_metrics.sh $LABEL first"; exit 2; }

python3 - "$M" "$PROMPT" "$LABEL" <<'PY'
import json, subprocess, sys, datetime as dt
m = json.load(open(sys.argv[1])); arms, exp, facts = m.get("arms", {}), m.get("exposure", {}), m.get("facts", {})
yt = {}
try:
    yt = json.load(open("v2/data/mixture/FACTS.json")).get("training_window", {})
except Exception:
    pass
git = subprocess.run(["git", "log", "-8", "--pretty=%h %ad %s", "--date=short"],
                     capture_output=True, text=True).stdout
open(sys.argv[2], "w").write(f"""You are Codex-Astra, the independent model-training reviewer for CyberGuard v2. This is the
automatic review for checkpoint {sys.argv[3]} ({dt.datetime.now():%Y-%m-%d %H:%M %Z}), required by the owner's
cadence at every checkpoint.

BOUNDARY (mandatory). You review: training method, parent initialisation, hyperparameters, mixture and support,
sequence and mask correctness, checkpoint and arm policy, the evaluation contract, and model equivalence. You
do NOT review or design licence terms, attribution, data-admission engineering, leakage pipeline design,
receipts, validators, release process, or agent operations — one line and stop if you feel the pull. You have
NO design authority: state objections in one line each; do not redesign.

## Live measured state at this checkpoint
```json
{json.dumps({"arms": arms, "exposure": exp, "facts": facts, "training_window": yt}, indent=2)}
```

## Recent history
```
{git}```

## Context you need
Two-arm LoRA fine-tune (arm A = offensive-refusal mixture, arm B = causal control), one arm per machine.
Epoch 1 completed on both arms (11.03 h / 11.01 h, 66,060,288 trainable params, grad_norm ~0.6). The
2026-09-28 23:29 relaunch then ran FROZEN for 3.01 h per arm because `PeftModel.from_pretrained` defaults to
`is_trainable=False` (trainable params 0, grad_norm 0); that is fixed and the repaired run was relaunched
02:32:53 with a 570-minute box. Codex review #14 cleared the continuation artefact conditional on a measured
exposure description and a learning proof (a nonzero optimiser-applied weight change against the preserved
parent), both of which are implemented (contract stage 0d and the verdict's measured-exposure section).

## Your task
Judge only what the numbers above can support, and recompute rather than trusting labels:
1. Are the two arms still progressing at the same rate and exposure (steps, epoch fraction, refusal
   presentations)? If not, is the divergence material to a paired A-vs-B contrast?
2. Does anything in the live numbers contradict the declared mixture basis in FACTS, or the measured
   epoch-1 wall clock?
3. Is the run still plausibly within the owner's 24 h x 2 authorization given the GPU-hours already spent?
4. Any training-validity objection you can substantiate from these numbers.

Output: markdown, no preamble. A short findings table (severity + one line of evidence + verdict
OK / OBJECTION). Then exactly one closing line: either
  Checkpoint {sys.argv[3]}: no training-validity objection.
or your objection in one sentence. Do not manufacture a clearance, and do not manufacture an objection.
""")
print(f"prompt written: {sys.argv[2]}")
PY
if [ "$DRY" = 1 ]; then
  echo "--- DRY RUN: prompt head ---"; head -12 "$PROMPT"; exit 0
fi
nohup codex exec -s read-only --skip-git-repo-check -C "$ROOT" -o "$OUT" - \
  < "$PROMPT" > "research-tmp/reviews/checkpoint-${LABEL}-review.log" 2>&1 &
sleep 4
echo "review dispatched for checkpoint $LABEL -> $OUT"
