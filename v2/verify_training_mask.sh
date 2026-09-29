#!/usr/bin/env bash
# verify_training_mask.sh — settle the loss-mask question with LIVE evidence from the running trainer.
#
# Why: the trainer ships a MASK_PROOF mode that decodes the non--100 labels of a real collated batch and
# asserts assistant-only supervision, exiting before any optimizer step. An independent review found NO
# "MASK PROOF" line in either host's logs, i.e. the proof was never run for this window, so there was no
# captured evidence that the live loss mask was correct.
#
# This runs it on each host and receipt the output. It MUST run after training has released the GPU: it loads
# the model for one batch. The contract calls it in stage 0c, i.e. after the C24 training stop.
set -uo pipefail
ROOT="$HOME/AgentHub/cyberguard"
cd "$ROOT" || exit 1
OUT="v2/data/mixture/mask-proof.receipt.json"
python3 - "$OUT" <<'PY'
import json, subprocess, sys, time
out = sys.argv[1]
HOSTS = {"armA": "clawerdigi2@spark-40ee", "armB": "clawerdigi1@spark-8cf2"}
res = {"captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "mode": "MASK_PROOF=1 (exits before any optimizer step)",
       "why": "the proof was never run for this window; this is the settling evidence", "hosts": {}}
for arm, host in HOSTS.items():
    cmd = ("cd ~/cyberguard && source ~/.cyberguard-env && "
           "RUN_NAME=cyberguard-lora-v2-%s MASK_PROOF=1 timeout 900 "
           "$CYBERGUARD_VENV/bin/python train_cyberguard.py 2>&1 | grep -E 'MASK PROOF|Error|error' | tail -6" % arm)
    try:
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, cmd],
                           capture_output=True, text=True, timeout=1200)
        res["hosts"][arm] = {"host": host, "exit": p.returncode,
                             "output": ((p.stdout or "") + (p.stderr or ""))[-1200:]}
    except Exception as e:                                            # noqa: BLE001
        res["hosts"][arm] = {"host": host, "exit": None, "output": f"SSH-FAILED {e}"}
json.dump(res, open(out, "w"), indent=2)
ok = all("MASK PROOF: PASS" in (d.get("output") or "") for d in res["hosts"].values())
for arm, d in res["hosts"].items():
    last = (d.get("output") or "").strip().splitlines()[-1:] or [""]
    print(f"  {arm}: {last[0][:100]}")
print(f"  MASK PROOF receipt: {out} | both hosts PASS: {ok}")
sys.exit(0 if ok else 1)
PY
