# LAUNCH CONFIRMATION — CyberGuard v3 (2026-09-30 02:12 CDT)

**Status: LAUNCHED AND RUNNING on spark-40ee.** Owner approval received via Ronin; training is live.

## Launch facts

| item | value |
|---|---|
| host | **spark-40ee** (`clawerdigi2@spark-40ee`), NVIDIA GB10 |
| run name | `cyberguard-lora-v3` |
| main pid | **1189450** (detached, `setsid`, ppid 1); 1190472 is its tokenization worker |
| log | `~/cyberguard/logs/train-cyberguard-lora-v3.log` |
| mixture | `data/v3/mixture/mixture-v3-no-trail.jsonl` — **sha256 `75b5099c…` verified on the host**, 140,545 rows |
| recipe | approved Arm B verbatim: LoRA r=32, lr 1e-4 cosine/warmup 0.03, batch 2 × grad_accum 8, max_seq 2048, seed 0, **epochs 1.0** |
| trainable params | 66,060,288 / 4,088,528,384 = **1.6157 %** (r=32) |
| system augmentation | ON, 4 distinct variants |
| time budget | `MAX_MINUTES=3300` (ceiling) |
| steps/epoch | **8,783** |
| started | 02:09:27 CDT (model load 02:10:17, training loop 02:12:01) |

Verified live, not inferred: GPU **96 %**, log shows `starting training: ~8784 steps/epoch, epochs=1.0,
max_steps=-1, time_budget=3300.0 min`, and steps advancing (`13/8783` at ~14.3–15.3 s/it). Exactly one
run: one process has ppid 1; the second python is that process's tokenization child (`num_proc=2`).

## ETA and why the budget was changed before launch

Measured rate ~14.5 s/step → `8,783 × 14.5 s ≈ 127,400 s` = **≈35–37 h** (rate still settling; early
steps include graph warmup). The 3300-minute ceiling (55 h) covers that with ≈19 h of margin.

**The plan's original `max_minutes = 1320` (22 h) would have been fatal.** I measured the built v3
mixture at **735.1 tokens/presentation** against v2's 323.4 (the source of the plan's 1.942
presentations/s), projecting ≈45 h and implying the run would stop at ≈48–60 % of epoch 1.0. §5.1
disposes an incomplete epoch as **INCOMPLETE — adapter not harvested, no ship verdict**, so the
original cap would have consumed 22 GPU-hours and produced nothing shippable. `max_minutes` is a
TimeBox *ceiling* (`MAX_MINUTES`), so raising it changes **no** hyperparameter — lr, batch,
grad_accum, LoRA rank, seed and epochs are untouched; it only removes the premature-stop risk. The
projection and the revised ceiling are written into PLAN-V3 §5.1 with the measurement behind them.

## Two-host instruction — cannot be honoured as given (facts, not preference)

Sandeep asked that training use **both** spark-40ee and spark-8cf2. I verified spark-8cf2 is genuinely
clear and equipped (hostname `spark-8cf2`, load 0.05, **GPU 0 %**, base model + trainer + venv
present, no processes). But the request cannot be executed without changing the approved recipe:

1. **`train_cyberguard.py` has no distributed support.** No `torchrun`, no `DDP`, no `local_rank`, no
   `MASTER_ADDR`, no accelerate-launch path — and no multi-node launch script exists anywhere in the
   repo. It is a single-process HF Trainer run.
2. **Running it multi-node would change the recipe.** Data-parallel on 2 GPUs with the current
   `batch 2 × grad_accum 8` gives an effective batch of **32**, not the approved 16; preserving 16
   requires halving `grad_accum` to 4, and multi-node DDP over the tailnet is unvalidated for this
   pipeline (rendezvous, NCCL-over-TCP, rank-safe checkpointing and the `TimeBox` callback are all
   new failure surfaces). PLAN-V3 forbids unvalidated recipe changes ("no hyperparameter search, one
   arm, reuse Arm B verbatim"), so this needs Codex-Astra re-review plus explicit approval.
3. **Splitting the mixture into two independent runs and merging adapters is not equivalent** to
   training on the mixture: two optimizer trajectories, and LoRA merging is an approximation the plan
   neither specifies nor gates. It would invalidate the Arm B reuse premise.

**Options, for the owner:** (a) **let the single-host run proceed** (already live, ≈35–37 h, recipe
exactly as approved) — recommended, since it is the only path that executes the approved recipe
today; (b) authorise a **DDP variant** with `grad_accum 4` to hold the effective batch at 16, which
needs the code, a re-review, and a restart (the ~13 steps so far would be discarded); (c) use
spark-8cf2 for recipe-neutral work such as the eval chain later. I have **not** written anything to
spark-8cf2.
