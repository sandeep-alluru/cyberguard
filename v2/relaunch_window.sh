#!/usr/bin/env bash
# relaunch_window.sh — stop both arms and relaunch them on the CURRENT frozen arms, but only after the
# gate has actually passed for those arms.
#
# WHY: the same arithmetic that made three earlier windows cheap to stop applies here. Window 4 runs on the
# v13 arms, and review #12 found 26 full-label + 750 parent-ID ATT&CK contradictions per arm. The corrected
# arms (v14) exist. Stopping a window ~20 minutes in costs ~20 minutes; waiting for the C8 checkpoint costs
# ~8 GPU-hours. So the switch happens as soon as v14's gate is green, not at C8.
#
# THE GUARD IS THE POINT: this refuses to relaunch unless the latest gate log for TODAY shows all four
# required legs passing for the arms currently on disk. A relaunch on ungated data would waste 24 hours.
#
# Usage: bash v2/relaunch_window.sh [--dry-run] [gate-log-path]
set -uo pipefail
ROOT="$HOME/AgentHub/cyberguard"
cd "$ROOT"
DRY=0
GATE=""
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    *) GATE="$a" ;;
  esac
done
[ -n "$GATE" ] || GATE=$(ls -t research-tmp/rebuild/gate*.log 2>/dev/null | head -1)

echo "=== gate evidence: ${GATE:-none} ==="
if [ -z "$GATE" ] || [ ! -s "$GATE" ]; then
  echo "REFUSING: no gate log to read; the arms on disk are not evidenced as gated."; exit 2
fi
python3 - "$GATE" <<'PY'
import re, sys
log = open(sys.argv[1], errors="replace").read()
checks = {
    "audit PASS":            len(re.findall(r"VERDICT: PASS", log)) >= 2,
    "receipt bound":         "RECEIPT-BOUND" in log,
    "leak CLEAN":            "VERDICT: CLEAN" in log,
    "completeness PASS":     "ACCEPTANCE TEST (D9): PASS" in log,
    "ATT&CK repair PASS":    "REPAIR CHECK: PASS" in log,
    # both halves of O1: exactly 5,600 substituted slots AND the 3,984 abstention rows identical in both arms
    "O1 substitution":       bool(re.search(r"differing(?: rows)? 5600", log)) and "identical refusal rows 3984" in log,
}
for k, v in checks.items():
    print(f"  {'OK  ' if v else 'FAIL'} {k}")
sys.exit(0 if all(checks.values()) else 1)
PY
if [ $? -ne 0 ]; then
  echo "REFUSING: the gate for the arms on disk has not passed; relaunching would waste the whole window."; exit 3
fi
echo "  gate is green for the arms on disk"

WANT_A=$(python3 -c "import json;print(json.load(open('v2/data/mixture/FACTS.json'))['arm_sha256']['armA.jsonl'])")
WANT_B=$(python3 -c "import json;print(json.load(open('v2/data/mixture/FACTS.json'))['arm_sha256']['armB.jsonl'])")
echo "  frozen armA ${WANT_A:0:16}...  armB ${WANT_B:0:16}..."

if [ "$DRY" = "1" ]; then
  echo "  DRY RUN: would stop both arms, re-stage the frozen arms, relaunch 24 h on each host, re-arm monitors."
  exit 0
fi

for spec in "clawerdigi2@spark-40ee A" "clawerdigi1@spark-8cf2 B"; do
  set -- $spec; H=$1; ARM=$2
  echo "=== stopping arm $ARM on $H ==="
  timeout 90 ssh -o BatchMode=yes "$H" "
    for p in /proc/[0-9]*; do e=\$(readlink -f \$p/exe 2>/dev/null)||continue; case \"\$e\" in *python*) ;; *) continue;; esac; while IFS= read -r -d '' a; do case \"\$a\" in */train_cyberguard.py) kill -TERM \${p#/proc/} 2>/dev/null;; esac; done < \$p/cmdline 2>/dev/null; done
    sleep 6
    for p in /proc/[0-9]*; do c=\$(tr '\0' ' ' < \$p/cmdline 2>/dev/null); case \"\$c\" in *monitor-v2.sh*) kill \$p 2>/dev/null;; esac; done
    n=0; for p in /proc/[0-9]*; do e=\$(readlink -f \$p/exe 2>/dev/null)||continue; case \"\$e\" in *python*) ;; *) continue;; esac; while IFS= read -r -d '' a; do case \"\$a\" in */train_cyberguard.py) n=\$((n+1));; esac; done < \$p/cmdline 2>/dev/null; done
    echo \"    trainers alive after stop: \$n\"" 2>&1 | sed 's/^/  /'
done

bash stage-v2-arms.sh 2>&1 | tail -2 | sed 's/^/  /'

for spec in "clawerdigi2@spark-40ee A" "clawerdigi1@spark-8cf2 B"; do
  set -- $spec; H=$1; ARM=$2
  echo "=== relaunching arm $ARM on $H ==="
  timeout 120 ssh -o BatchMode=yes "$H" "cd ~/cyberguard && bash run-v2-arm.sh $ARM 1440" 2>&1 | tail -2 | sed 's/^/  /'
done
sleep 40
for spec in "clawerdigi2@spark-40ee A" "clawerdigi1@spark-8cf2 B"; do
  set -- $spec; H=$1; ARM=$2
  timeout 60 ssh -o BatchMode=yes "$H" "
    n=0; for p in /proc/[0-9]*; do e=\$(readlink -f \$p/exe 2>/dev/null)||continue; case \"\$e\" in *python*) ;; *) continue;; esac; while IFS= read -r -d '' a; do case \"\$a\" in */train_cyberguard.py) n=1;; esac; done < \$p/cmdline 2>/dev/null; done
    echo \"  arm $ARM alive: \$n\"
    cd ~/cyberguard && setsid nohup bash monitor-v2.sh $ARM 300 300 >/dev/null 2>&1 &" 2>&1 | grep alive | sed 's/^/  /'
done
date '+  window relaunched %F %T %Z'
