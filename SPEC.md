# SPEC — CyberGuard v1: **trained model + benchmark tests done**

**Owner's end goal (2026-09-27 00:10 CDT):** "the end goal is to have trained model with benchmark
tests done." Train on a Spark **not serving the v1 flash endpoint** → **spark-40ee**
(`100.123.114.95`); flash serving verified on spark-8cf2 (`100.118.142.51`, active tailscale).
Operating pattern adopted from the gpu-work pod-ops corpus (ledger → spec → armed monitor →
independent review → harvest), applied to owned hardware.

## done-means (all seven, with evidence)

| # | artifact | location | check |
|---|---|---|---|
| 1 | trained adapter | `~/cyberguard/adapters/cyberguard-lora-v1/` | safetensors + tokenizer + adapter_config, non-zero |
| 2 | training receipt | `~/cyberguard/receipts/train-cyberguard-lora-v1.json` | wall, steps, rows covered, coverage % |
| 3 | benchmark eval | `~/cyberguard/evals/eval-cyberguard-lora-v1.json` | 500 held-out items, arms BASE vs ADAPTER, one evaluator/parser/template, Wilson 95 % CI |
| 4 | verdict + gate table | `docs/VERDICT-v1.md` | 8 gates from brief §4 where measurable on v1; ≤ 10 pp = UNRESOLVED; CPT-ladder gates marked N/A (v1 is pipeline evidence, not method evidence) |
| 5 | harvest | local `research-tmp/harvest-v1/` | checksum-verified copies of 1–4 + full log |
| 6 | CEO brief (result) | `docs/ceo/` | house pattern, renders on portal |
| 7 | Codex-Astra reviews | LEDGER `R-CA` entries | per cadence below, findings closed |

## Units

- **U1 corpus orientation** — pod-ops skill + training-craft (pre-flight/run/export/eval sections) +
  fleet KNOWN_FAILURES map + jobs/ conventions. `<!-- DONE U1 2026-09-27T00:15Z -->`
- **U2 environment verified** — host spark-40ee (0 % GPU, no serving listeners, 71 GB RAM available,
  3.2 TB disk); venv `~/venvs/sglang`; dataset `~/cyberguard/data/trendyol-cybersec/CyberSec-Dataset_escaped.jsonl`
  (195 MB); base model staged; tmux present; code md5-verified local↔remote.
  `<!-- DONE U2 2026-09-27T00:25Z -->`
- **U3 datasets identified + evaluated** — v1 = Trendyol escaped 52,284 rows: safety audit receipt
  ✓ (178 attack-production rows dropped, 62 near-dupes collapsed), split 51,784/500 deterministic
  prompt-disjoint ✓, leakage max Jaccard 0.773 < 0.80 ✓. **OPEN (goal rounds):** Trendyol license
  verification via web; v2 candidate mixture (security CPT corpora, verified licenses + dual-use
  filter) — web research + Codex-Astra reviewed before adoption.
- **U4 training v1** — 170-min time-box, BATCH=2/GRAD_ACC=8 (measured 0.92 s/sample), LR 1e-4,
  LoRA r=32 bf16, seq 2048, EPOCHS=1; coverage recorded honestly.
  **Step-progress must be confirmed within 10 min of launch** — the TimeBox lesson.
- **U5 monitor armed** — `monitor-cyberguard.sh` on spark, 5-min cadence: process alive (/proc scan,
  bracketed pattern per R25), log growth (STALL at 3 quiet cycles), crash grep, receipt appearance,
  deadline. Alerts → `~/cyberguard/logs/monitor-v1.log` + `ALERT-*` file.
- **U6 benchmarks + verdict** — eval_cyberguard.py BASE vs ADAPTER on the 500 held-out (n=500,
  k=1, greedy, Wilson CI); contract verdict; gate table; harm gates non-waivable.
- **U7 harvest + receipts + CEO brief** — checksum-verified pull; result brief on CEO desk.
- **U8 Codex-Astra reviews — MANDATORY, PERIODIC (owner instruction).**
- **U9 ledger + memory current throughout** — LEDGER.md entries with evidence; project memory updated.

## R-CA — the Codex-Astra review rule (mandatory)

1. **Review #1 — pre-launch:** this SPEC + data contract + env facts. Findings fixed or refused in
   writing **before** U4 proceeds past first-step confirmation; a blocking finding stops the run.
2. **Review #2 — during training:** U3 open items (license, v2 mixture) + web research synthesis.
3. **Review #3 — pre-verdict:** eval numbers + gate table before any ship/quality claim.
4. **Cadence:** at least every 3 h while the goal is active (owner precedent, 2026-09-26 ornith
   ruling). Every review: reviewer = Codex (different family), findings recorded in LEDGER with
   disposition (fixed / refused+reason). A review that found nothing still gets a ledger line.

## Failure ladder — from the corpus, pre-applied

| risk | corpus lesson | mitigation here |
|---|---|---|
| init crash wastes the window | F: TimeBox `on_init_end` killed v1's first attempt | smoke-refactor-check proves the exact path; step-progress ≤10 min or monitor+round escalate |
| silent death / lost log | DETACH section | script self-detaches `setsid nohup` → durable log file; monitor watches growth |
| pipe hides exit code | F54/R26 | no pipes in launch or receipt path |
| pgrep self-match | F58/R25 | /proc scan, bracketed patterns |
| OOM mid-run | VRAM-headroom rule | 71 GB measured free vs ~30 GB need; fallback BATCH=1/GRAD_ACC=16 (same effective batch) |
| endpoint instability | today's 12-session wipeout | v1 path touches **no** LLM endpoint; eval is local deterministic GPU work |
| stall unnoticed | gsq-rco deadline breach | monitor STALL alert + goal-round checks |
| run double-starts | corrupt output dirs | script's /proc refuse-to-start-twice gate |

## Environment settings of record (spark-40ee)

`CYBERGUARD_ROOT=~/cyberguard` · `CYBERGUARD_VENV=~/venvs/sglang` · `HF_HOME=~/cyberguard/hf` ·
dataset escaped jsonl · base `~/cyberguard/models/Qwen3-4B-Instruct-2507` · code at `~` (md5-synced) ·
launch: `MAX_MINUTES=170 bash ~/run-cyberguard-train.sh` (RUN_NAME=cyberguard-lora-v1) ·
deadline monitor: launch + 200 min.
