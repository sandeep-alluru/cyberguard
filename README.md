# cyberguard — a small fine-tuned cyber-defence model

**Goal:** a small model that helps *prevent* cyber attacks — defensive security guidance:
detection, hardening, incident response, framework mapping (NIST CSF, MITRE ATT&CK).

Owner inputs were exactly three: the goal, that it may be a small model, and that it must be
usable from this machine. Base model, dataset, training method, host and evaluation were
delegated to the agent, so every choice below is recorded with its reason.

## Choices, and why

| decision | choice | reason |
|---|---|---|
| **base model** | `Qwen/Qwen3-4B-Instruct-2507` (7.6 GB) | small enough to run anywhere (Q4 ≈ 2.5 GB) but capable enough to be useful; family already proven on this fleet |
| **dataset** | `Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset` | 53,200 instruction rows whose own system prompt encodes the cyber-defence persona — "specialized AI assistant for advanced cyber-defense… NIST CSF and MITRE ATT&CK" |
| **method** | LoRA (r=32) in **bf16**, not QLoRA | bitsandbytes has no dependable aarch64/Blackwell CUDA wheel; quantisation is unnecessary because a 4B LoRA with gradient checkpointing fits comfortably in the free memory |
| **host** | `spark-40ee` (GB10) | see the host decision below — the obvious host turned out to be unusable |
| **sequence length** | 2048 | measured: corpus median ≈ 895 tokens, p90 ≈ 1017, max ≈ 1791 — so 2048 covers every row with no padding waste |

## Host decision (this is the interesting part)

`clawersamurai6` was the obvious choice: 2× RTX 3090 both idle, and `venvs/v2-fast` already
carries a full unsloth/peft/trl/QLoRA stack used by the Ornith programme.

**It is unusable for new work: its `/data` filesystem is 100 % inode-exhausted** —
119,264 of 119,264 inodes used, zero free, while blocks are only 57 % used. Nothing new can be
created there. Its root has 13 GB free, far too little for a model plus checkpoints, and the
existing data on `/data` (ornith-coding-release 138 GB, tessen-continuation 87 GB) belongs to
other projects and is not ours to delete.

`spark-40ee` was chosen instead: 3.3 TB free, 249 M inodes at 1 % used, idle GB10, and a venv
carrying torch 2.13 + transformers + datasets, to which peft/trl/accelerate were added.

## Measured throughput (this sizes the run)

Smoke runs, 16 samples per optimiser step in both cases:

| config | s/step | s/sample |
|---|---|---|
| BATCH=2, GRAD_ACC=8 | 14.68 | **0.92** ← chosen |
| BATCH=8, GRAD_ACC=2 | 19.14 | 1.20 |

A full 53 k-row epoch is therefore ≈ **13.6 hours**, which does not fit a 3-hour window. The run
is explicitly time-boxed (`MAX_MINUTES=170`) and the receipt records how much of the corpus that
covered — a time-boxed run that reports its coverage, rather than an open-ended one killed
halfway.

## Layout

```
cyberguard/
  data/      Trendyol cybersecurity instruction corpus
  models/    base model, and the merged model after LoRA merge
  adapters/  trained LoRA adapters + JSON receipts
  gguf/      converted + quantised servable weights
  receipts/  one JSON per training run: config, loss curve, versions, timing
  logs/      raw training logs
  evals/     held-out evaluation output
```

## Scripts

| script | runs on | purpose |
|---|---|---|
| `recon-train-env.sh` | any candidate host | reports GPUs, per-mount disk, and each venv's training stack — this is what caught the inode exhaustion |
| `cyberguard-setup-spark.sh` | spark-40ee | creates the tree, adds peft/trl/accelerate, fetches the dataset |
| `cyberguard-data.sh` | spark-40ee | inspects the dataset schema and fetches the base model |
| `train_cyberguard.py` | spark-40ee | the LoRA fine-tune; writes a receipt with the real loss curve |
| `run-cyberguard-train.sh` | spark-40ee | launches training detached, refuses to double-start |
| `cyberguard-merge-gguf.sh` | spark-40ee | merges LoRA → base, converts to GGUF, quantises to Q4_K_M; refuses to run while training is in flight |

## Bug found on the first real launch, and the lesson

The first real run died at startup:

```
AttributeError: 'TimeBox' object has no attribute 'on_init_end'
```

`TimeBox` hand-listed a handful of callback methods instead of subclassing
`transformers.TrainerCallback`, so any event it did not implement — `on_init_end` — raised.

**The smoke test passed anyway**, because it ran *without* `MAX_MINUTES`, so it never
constructed the callback at all. The smoke exercised a different code path than the real run
and therefore validated nothing about the path that mattered. Fixed by subclassing
`TrainerCallback`, and the smoke was then re-run **with the time box** — same configuration as
the real job — which is the only version of that test that is worth anything.

## GPU arbitration

spark-40ee's GB10 has two claimants: Flash-Next's RPC share and this fine-tune. Running both
at once would have (a) corrupted the owner's 3-hour Flash-Next test with training contention
and (b) slowed the fine-tune. The training was stopped before the test started, and
`.runtime/spark-qwen/resume-train-after-test.sh` relaunches it automatically once the test
releases the GPU — so the two run back to back, not interleaved.


## Serving path — **validated end to end**

The machine split is forced by what is actually built where:

* **spark-40ee** can merge the LoRA and convert to GGUF (it has the python `gguf` module) but
  has **no `llama-quantize` binary** — only `llama-server` and `ggml-rpc-server` are built.
* **this workstation** has `llama-quantize` and `llama-server` built, plus the GTX 1080 Ti
  that holds a Q4 4B model in 4.4 GB.

So: merge + convert on the Spark → copy the f16 GGUF here → **quantise here** → serve here.

**This was proven before the real adapter existed**, using a throwaway 3-step adapter
(`smoke-tb`), on CPU so it could not disturb the GPU running the owner's Flash-Next test:

```
model size  = 7672.62 MiB (16.00 BPW)
quant size  = 2375.91 MiB (4.95 BPW)      <- Q4_K_M, 2.4 GB, 165 s
HEALTHY http://127.0.0.1:18081/v1  (alias: cyberguard-4b)
```

and it generated a coherent defensive answer. Every step after training is therefore known to
work; the real run only supplies a better adapter. The throwaway artifacts were then removed
from both machines.

Verified port: **18081** (adjacent to the existing local router on 18080, so they cannot
collide). The model is **not** registered in DSH yet — registering happens once the real GGUF
exists, because pointing the harness at a dead endpoint would be untidy.

## Fully automated chain

Everything after the base setup is chained as systemd units, so no step waits on someone
remembering to run it. Each waits on a **durable signal**, not on a process check — a crashed
run and a finished run must not look alike:

```
spark-flash-test-3h          the owner's 3-hour test against Qwen3.8-Flash-Next   (running)
   |
   v  waits for that unit to go inactive
spark-cyberguard-after-test  relaunches the cyber fine-tune on spark-40ee
   |
   v  waits for ~/cyberguard/receipts/<run>.json to EXIST  (the training receipt)
spark-cyberguard-finish      eval -> merge+GGUF -> quantise+serve -> register in DSH
```

`spark-cyberguard-finish` orders its own steps deliberately:

1. **eval first**, while the GPU training just released is free — evaluation generates tokens
2. **merge + convert on the Spark** (CPU only)
3. **quantise + serve locally** on the 1080 Ti
4. **register in DSH last**, and only if `:18081` actually answers — pointing the harness at a
   dead endpoint would be untidy

Log: `cyberguard/logs/finish-chain.log`.

## Split-integrity check

`verify_split.py` proves the evaluation cannot silently score on training data. It replicates
both loaders and asserts:

```
rows  train-style=53199  eval-style=53199
PASS: both hold out the SAME 500 rows
PASS: held-out and training rows are disjoint
PASS: split partitions the whole corpus (53199 rows)
PASS: split is deterministic (seed reproducible)
```

This matters because `train_cyberguard.py` and `eval_cyberguard.py` compute the held-out set
independently. Any drift — a different filter, seed or ordering — would leave the numbers
looking fine while meaning nothing.

## Status — v1 COMPLETE (2026-09-27), v2 planned

- [x] host chosen and verified; stack installed
- [x] dataset (53,201 rows) and base model (7.6 GB) on disk
- [x] training smoke-tested, throughput measured, callback bug fixed and re-verified
- [x] merge -> GGUF -> quantise -> serve pipeline validated end to end (throwaway adapter)
- [x] evaluation harness written and deployed (`eval_cyberguard.py`)
- [x] **split-integrity verified** — eval and training hold out the same 500 rows, disjoint
- [x] DSH registration script written and tested **against a copy** of the live config
- [x] **v1 TRAINED** — 170-min box, step 663/3237 (epoch 0.2049), receipt with real loss curve
- [x] **v1 BENCHMARKED** — n=500 paired: NLL 2.3600 -> 0.8763; token-F1 0.3024 -> 0.4273
      (Δ +0.1249, paired bootstrap 95 % CI [0.1194, 0.1306]) — see `docs/VERDICT-v1.md`
- [x] **capability gap map measured** (7 phases, powered batteries) — `docs/CAPABILITY-v1.md`
- [x] **5 Codex-Astra reviews**, every finding dispositioned — `LEDGER.md`
- [x] harvests checksum-verified — `research-tmp/harvest-v1/`, `research-tmp/harvest-cap-v1/`
- [x] CRAFT corpus complete (69 lessons + 16 decisions) — `docs/CRAFT/`
- [ ] v2 plan of record written, awaiting the owner's mixture + GPU-budget approval — `docs/SPEC-V2.md`
- [ ] v1/v2 serving — **deliberately not done**, see the serving posture below

**What v1 is:** an end-to-end owned-hardware pipeline proof with a base-dominating domain checkpoint.
**What v1 is not:** deployable against adversarial traffic. The capability box measured offensive
refusal at **6/60 (10 %)** against a base of **24/60 (40 %)** (McNemar p=4×10⁻⁵, decode-robust),
with verified directly-harmful outputs; it also fabricates CVE/ATT&CK IDs in an adjacent-ID pattern,
cannot draft Sigma and cannot hold a one-word answer format. Use it as a **human-reviewed defensive
drafting assistant** and nothing else. Full picture: `docs/CAPABILITY-v1.md`.

## Serving posture — v1 is NOT served (owner decision, 2026-09-27)

The adapter exists and is measured (`~/cyberguard/adapters/cyberguard-lora-v1/`, 1.1 GB on
`spark-40ee`). It was **never merged to GGUF, never served on :18081, and never registered in DSH** —
verified 2026-09-27 19:2x CDT: no `1808x` listener, no DSH provider entry, no GGUF on either box.

That is deliberate. The model we would have served is the model we measured as not deployable, so
serving waits on v2 clearing the refusal gate (`docs/SPEC-V2.md` §7 G-A) and then goes out behind the
inference-time ID validator. The throwaway-adapter proof above shows the path *works*; it does not
argue that it *should* be used.

## Honest limit: the DSH space itself

DSH session creation is **not programmatic**. `dsh` the CLI manages *profiles*, not sessions;
the web API at :3080 requires auth that is not obtainable from inside the sandbox; and sessions
are created by the web app on first use, keyed by working directory
(`--home-clawer-samurai-1-AgentHub-cyberguard--`). Fabricating `session.v3` internals would risk
the session list and would be inventing internal state.

What *is* programmatic — and done — is making a model **selectable**: the project folder exists,
and `register_cyberguard_dsh.py` adds the provider entry (written and tested against a copy of the
live config; not applied, since there is no served v1 to point at). Registration becomes one click
once a model passes its gate.
