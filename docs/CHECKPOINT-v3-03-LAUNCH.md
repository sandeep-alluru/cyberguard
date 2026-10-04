# CHECKPOINT 03 — CyberGuard v3 LAUNCHED (first checkpoint)

**Date:** 2026-09-30 02:18 CDT
**Trigger:** owner approval to start training, relayed by Ronin. This is the launch checkpoint.
**Status: RUNNING.** Not a proposal — verified live.

---

## 1. Launch confirmation

| item | value |
|---|---|
| host | **spark-40ee** (`clawerdigi2@spark-40ee`), NVIDIA GB10 |
| run | `cyberguard-lora-v3`, main pid **1189450** (detached `setsid`, ppid 1) |
| log | `spark-40ee:~/cyberguard/logs/train-cyberguard-lora-v3.log` |
| mixture | `data/v3/mixture/mixture-v3-no-trail.jsonl`, **sha256 `75b5099c…` verified on the host**, 140,545 rows |
| recipe | approved Arm B verbatim — LoRA r=32, lr 1e-4 (cosine, warmup 0.03), batch 2 × grad_accum 8, max_seq 2048, seed 0, **epochs 1.0** |
| trainable | 66,060,288 / 4,088,528,384 = **1.6157 %** |
| augmentation | system-prompt augmentation ON, 4 variants |
| budget | `MAX_MINUTES=3300` (TimeBox ceiling) |
| steps/epoch | **8,783** |

**Evidence it is really training** (not just a live pid): GPU **86–96 %**; log shows
`starting training: ~8784 steps/epoch, epochs=1.0, max_steps=-1, time_budget=3300.0 min`; progress
advancing (`18/8783`, ~14.7–15.2 s/it). Exactly **one** run — one process has ppid 1, the other
python process is its tokenization child (`num_proc=2`), and the launcher's exact-argv
refuse-to-start-twice guard fired cleanly.

## 2. A budget error caught before it cost the run

The plan's `max_minutes = 1320` (22 h) was derived from **v2's** 1.942 presentations/s. I measured the
built v3 mixture at **735.1 tokens/presentation** vs v2's **323.4** — 2.27× the density, because the
rows are reasoning traces — giving a ≈45 h projection. At 1320 the run would have stopped at
≈48–60 % of epoch 1.0, which §5.1 disposes as **INCOMPLETE: adapter not harvested, no ship verdict**.
22 GPU-hours would have produced nothing shippable.

`max_minutes` is a TimeBox *ceiling*, so raising it to **3300** changes **no hyperparameter** — lr,
batch, grad_accum, LoRA rank, seed and epochs are untouched. It only removes the premature-stop risk.
PLAN-V3 §5.1 now carries the measurement, the withdrawn rev-6 figures, and the revised ceiling.

**Measured ETA: ≈35–37 h** (`8,783 × ~14.9 s`), currently finishing ~14:40 CDT on 2026-09-30.
3300 min leaves ≈19 h of margin. Actual rate may improve as warmup overhead amortises.

## 3. Two-host instruction: cannot be honoured as given

Sandeep asked that training use both spark-40ee and spark-8cf2. **spark-8cf2 verified genuinely clear
and equipped** (load 0.05, **GPU 0 %**, base model + trainer + venv present, no processes). But the
request cannot be executed without changing the approved recipe:

1. **`train_cyberguard.py` has no distributed support** — no `torchrun`, `DDP`, `local_rank`,
   `MASTER_ADDR`, and no multi-node launch script anywhere in the repo. Single-process HF Trainer.
2. **Multi-node would change the recipe**: 2 GPUs × batch 2 × grad_accum 8 = effective batch **32**,
   not the approved 16; preserving 16 needs `grad_accum 4`. DDP over the tailnet is also unvalidated
   here (rendezvous, NCCL-over-TCP, rank-safe checkpointing, `TimeBox` semantics). PLAN-V3 forbids
   unvalidated recipe changes, so this needs re-review + explicit approval.
3. **Splitting the mixture across two independent runs and merging adapters is not equivalent** —
   two optimizer trajectories, and LoRA merging is an approximation the plan neither specifies nor
   gates.

**Nothing was written to spark-8cf2.** Options for the owner: (a) **let the live single-host run
proceed** (recommended — the only path executing the approved recipe today); (b) authorise a DDP
variant with `grad_accum 4` (needs code + re-review + restart, discarding ~18 steps); (c) use
spark-8cf2 for recipe-neutral work such as the eval chain later.

## 4. Supervision in place

- Genuinely detached (`setsid`), so an ssh drop or session end cannot kill it.
- `tools/monitor-v3.sh` running as a supervised job: polls the host every 15 min, logs
  `alive / gpu / progress` to `logs/monitor-v3.log`, and exits when the trainer disappears or 60 h
  elapse — so completion or death is noticed rather than assumed.
- The launcher re-verifies the mixture sha256 and row count on every start, and refuses to run twice.

## 5. What comes next

1. Monitor to completion; record the training receipt (loss curve, epoch, wall time).
2. Then the eval chain per §8 — §8.1 classifier and §8.4 refusal rule are already built and
   acceptance-passing; G-D remains blocked on its human annotation bundle (kit ready,
   `tools/gd_annotation_kit.py`).
3. A7 trail remediation remains the owner's open decision (Option B) — unchanged by this launch.
