#!/usr/bin/env bash
# capture_training_provenance.sh — bind the audited local files to the ACTUAL training runs, on disk.
#
# Why: an independent review (2026-09-29) blocked frozen-arms clearance because it could not verify the
# correspondence — its SSH failed, the local log held only a KeyError, and the launcher never recorded the
# trained step horizon. This captures that evidence once, locally, so any reviewer can check the binding
# without host access.
set -uo pipefail
ROOT="$HOME/AgentHub/cyberguard"
cd "$ROOT" || exit 1
OUT="v2/data/mixture/training-provenance.receipt.json"
python3 - "v2/data/mixture/training-provenance.receipt.json" <<'PY'
import hashlib, json, os, subprocess, sys, time
out = sys.argv[1]
HOSTS = {"armA": ("clawerdigi2@spark-40ee", "40ee"), "armB": ("clawerdigi1@spark-8cf2", "8cf2")}
LOCAL = {"train_cyberguard.py": None, "run-v2-arm.sh": None, "v2/data/mixture/armA.jsonl": None,
         "v2/data/mixture/armB.jsonl": None}
for f in LOCAL:
    try:
        LOCAL[f] = hashlib.sha256(open(f, "rb").read()).hexdigest()
    except Exception:                                            # noqa: BLE001
        LOCAL[f] = None
rec = {"captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "local_files": LOCAL, "hosts": {}}
ssh_opts = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
for arm, (host, label) in HOSTS.items():
    q = (
        "cd ~/cyberguard; "
        "echo ARM_MODE:; grep -m1 'ARM MODE' logs/train-cyberguard-lora-v2-arm%s.log; "
        "echo ARGV:; tr '\\0' ' ' < /proc/$(pgrep -f 'train_cyberguard[.]py' | head -1)/cmdline 2>/dev/null | cut -c1-400; "
        "echo STEPS:; tr '\\r' '\\n' < logs/train-cyberguard-lora-v2-arm%s.log | grep -oE '[0-9]+/[0-9]+' | tail -1; "
        "echo MASK_LINES:; grep -icE 'mask' logs/train-cyberguard-lora-v2-arm%s.log; "
        "echo LOG_TAIL:; tr '\\r' '\\n' < logs/train-cyberguard-lora-v2-arm%s.log | grep -E 'loss' | tail -1 | cut -c1-200; "
        "echo CHECKPOINTS:; ls -d adapters/cyberguard-lora-v2-arm*/checkpoint-* 2>/dev/null | tr '\\n' ' '; "
        "echo ADAPTER_FILES:; ls adapters/cyberguard-lora-v2-arm*/ 2>/dev/null | grep -E 'safetensors|json' | tr '\\n' ' '; "
        "echo MASK_CODE:; grep -nE 'MASK PROOF|labels\[|DataCollator|-100|label_mask' train_cyberguard.py | head -16 | tr '\\n' '|'; "
        "echo TRAINER_SHA:; sha256sum train_cyberguard.py | cut -d' ' -f1; "
        "echo LAUNCHER_SHA:; sha256sum run-v2-arm.sh 2>/dev/null | cut -d' ' -f1"
    ) % (arm[-1], arm[-1], arm[-1], arm[-1])
    try:
        p = subprocess.run(["ssh"] + ssh_opts + [host, q], capture_output=True, text=True, timeout=120)
        raw = (p.stdout or "") + (p.stderr or "")
    except Exception as e:                                        # noqa: BLE001
        raw = f"SSH-FAILED {e}"
    # A field marker can be glued to the end of the previous value (ls | tr '\n' ' ' leaves no newline), so
    # match a TRAILING marker rather than requiring the whole line to be uppercase - the first version of this
    # parser silently dropped trainer_sha for exactly that reason.
    import re as _re
    fields, key, order = {}, None, []
    for line in raw.splitlines():
        m = _re.search(r"([A-Z_]{3,}):\s*$", line)
        if m:
            if key:
                fields[key] += " " + line[:m.start()].strip()
            key = m.group(1).lower()
            if key not in fields:
                fields[key] = ""
                order.append(key)
        elif key:
            fields[key] += (line + "\n").strip() + " "
    rec["hosts"][arm] = {"host": label, "raw": raw[-2000:], **{k: v.strip() for k, v in fields.items()}}
json.dump(rec, open(out, "w"), indent=2)
print(f"  captured provenance for {len(rec['hosts'])} hosts -> {out}")
for arm, d in rec["hosts"].items():
    print(f"  {arm}: arm_mode={str(d.get('arm_mode'))[:80]}")
    print(f"       steps={d.get('steps')} trainer_sha={str(d.get('trainer_sha'))[:16]} "
          f"checkpoints={str(d.get('checkpoints'))[:70]}")
PY
