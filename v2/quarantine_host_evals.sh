#!/usr/bin/env bash
# quarantine_host_evals.sh — runs ON a training host. Archives every pre-existing evals/*.json.
#
# WHY. Stage 3 pulls battery receipts back with a NAME GLOB (`rsync .../evals/battery-*-$ARM.json`), and stage 2
# reads `evals/cyberguard-lora-v2-<arm>.json`. The local evals/ directory is quarantined by contract stage 0pre
# precisely because a previous run's measurements are not evidence about this one - but the HOSTS' evals/
# directories were never treated the same way, and spark-40ee was found holding five stale files from 2026-09-26
# and 09-27 (including a `cyberguard-lora-v1.partial.json` from a crashed run) plus one of my own smoke
# artefacts. A stale file whose name matches a pull glob would be consumed as this window's measurement.
#
# Archives, never deletes. Exits non-zero if anything is left outside the archive.
set -uo pipefail
cd "$HOME/cyberguard" || exit 1
mkdir -p evals/.pre-c24-archive
n=$(find evals -maxdepth 1 -name '*.json' -type f 2>/dev/null | wc -l)
if [ "$n" -gt 0 ]; then
  find evals -maxdepth 1 -name '*.json' -type f -exec mv -t evals/.pre-c24-archive {} + 2>/dev/null || {
    echo "  QUARANTINE FAILED: could not move $n file(s)"; exit 1; }
fi
left=$(find evals -maxdepth 1 -name '*.json' -type f 2>/dev/null | wc -l)
if [ "$left" -ne 0 ]; then
  echo "  QUARANTINE INCOMPLETE: $left file(s) remain"; exit 1
fi
echo "  archived $n pre-existing eval json(s); evals/ now holds only this window's outputs"
