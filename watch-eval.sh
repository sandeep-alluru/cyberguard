#!/usr/bin/env bash
# watch-eval.sh — block until the remote eval chain prints its done-line or raises an ALERT.
# Script file on purpose: inline ssh one-liners are where quoting self-matches happen (R25).
for i in $(seq 1 90); do
  out=$(timeout 20 ssh -o BatchMode=yes clawerdigi2@spark-40ee \
    'grep -a "eval-chain done" ~/cyberguard/logs/eval-chain-cyberguard-lora-v1.log 2>/dev/null; ls ~/cyberguard/logs/ALERT-EVAL-* 2>/dev/null' 2>/dev/null)
  case "$out" in
    *"eval-chain done"*) echo "CHAIN-DONE: $out"; exit 0 ;;
    *ALERT*) echo "CHAIN-ALERT: $out"; exit 2 ;;
  esac
  sleep 120
done
echo "WATCHER-TIMEOUT-3H"; exit 3
