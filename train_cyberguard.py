#!/usr/bin/env python3
"""train_cyberguard.py — LoRA fine-tune of a small model into a cyber-defence assistant.

Owner's goal: "prevent cyber attacks". Concretely this trains the model to answer
defensive-security questions — detection, hardening, incident response, framework mapping
(NIST CSF, MITRE ATT&CK) — from the Trendyol cybersecurity instruction-tuning corpus,
whose own system prompt already encodes that cyber-defence persona.

Design choices and why:
  * LoRA in bf16, NOT QLoRA. bitsandbytes has no dependable aarch64/Blackwell CUDA wheel,
    and quantisation is not needed: a 4B LoRA with gradient checkpointing fits comfortably
    in the ~71 GB free on this node. Fewer moving parts on an unusual architecture.
  * max_seq_len 2048. Measured: the corpus median is ~895 tokens and the max is ~1791, so
    2048 covers every row without padding waste.
  * Held-out split is fixed and written to the receipt, so any later claim about the model
    is measured against data the fine-tune never saw.
  * Time-boxed via MAX_STEPS / MAX_MINUTES so a run can be stopped predictably, and it
    checkpoints so stopping does not lose the work.

Writes a receipt with the real loss curve, step timing, token count, and exact library
versions — a claim about training that cannot be re-derived is not evidence.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(os.environ["CYBERGUARD_ROOT"])
DATA = ROOT / "data" / "trendyol-cybersec" / "CyberSec-Dataset_escaped.jsonl"
BASE = Path(os.environ.get("TRAIN_BASE", ROOT / "models" / "Qwen3-4B-Instruct-2507"))
MAX_ROWS = int(os.environ.get("MAX_ROWS", 0))     # >0 caps the corpus, for cheap validation
DEVICE = os.environ.get("TRAIN_DEVICE", "cuda")
OUT_ADAPTER = ROOT / "adapters" / os.environ.get("RUN_NAME", "cyberguard-lora-v1")
RECEIPT = ROOT / "receipts" / f"{OUT_ADAPTER.name}.json"

MAX_SEQ = int(os.environ.get("MAX_SEQ", 2048))
EVAL_N = int(os.environ.get("EVAL_N", 500))
MAX_STEPS = int(os.environ.get("MAX_STEPS", -1))
MAX_MINUTES = float(os.environ.get("MAX_MINUTES", 0))
EPOCHS = float(os.environ.get("EPOCHS", 1))
LR = float(os.environ.get("LR", 1e-4))
BATCH = int(os.environ.get("BATCH", 2))
GRAD_ACC = int(os.environ.get("GRAD_ACC", 8))
LORA_R = int(os.environ.get("LORA_R", 32))
SEED = int(os.environ.get("SEED", 0))

# --- system-prompt diversification -------------------------------------------------------
# Measured on this corpus: it contains exactly ONE distinct system prompt across all 53,199
# rows. A constant persona carries no per-example information, so the model can learn to ignore
# the system role entirely — and then behave unpredictably when a real user supplies their own.
# These variants are applied to TRAINING rows only, keyed deterministically by index, so the
# held-out split stays byte-identical and the evaluation remains valid.
SYS_VARIANTS = [
    None,  # no system prompt at all: teaches the model to work without one
    ("You are a cyber-defence assistant. Give accurate, actionable defensive security "
     "guidance covering detection, hardening, and incident response."),
    ("Act as a defensive security engineer. Answer with practical measures to prevent, "
     "detect and contain attacks. Stay defensive."),
    ("You are an information-security advisor specialising in prevention and response. "
     "Be specific, reference standards where useful, and keep guidance defensive."),
]
AUGMENT_SYSTEM = os.environ.get("AUGMENT_SYSTEM", "1") == "1"


def augment_system(msgs, idx):
    """Rotate the persona across variants (and sometimes drop it) on training rows."""
    if not AUGMENT_SYSTEM or not msgs or msgs[0].get("role") != "system":
        return msgs
    v = SYS_VARIANTS[idx % len(SYS_VARIANTS)]
    if v is None:
        return msgs[1:]
    out = list(msgs)
    out[0] = {"role": "system", "content": v}
    return out

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import TrainerCallback
from trl import SFTConfig, SFTTrainer

t_start = time.time()
random.seed(SEED)
torch.manual_seed(SEED)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --- corpus and split come from cyberguard_data.py, the single source of truth. Loader logic
# used to be duplicated across four scripts and diverged: this one deduped by user prompt,
# check_leakage.py did not, so the leakage audit measured a split no run had ever used.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
# In ARM MODE the corpus loader is not needed, and the second training host does not carry it — import
# lazily so the arm path runs anywhere. (Astra data review #1: the trainer must consume the arm, not the
# corpus, or the sampling weight is silently erased.)
cgdata = None
if not os.environ.get("CYBERGUARD_ARMS"):
    import cyberguard_data as cgdata


# --- v2: train on a PRE-BUILT ARM, not on the raw corpus.
# Discovery that forced this (Astra data review #1, finding 6): this trainer loaded the original corpus
# and re-split it, so passing the weighted arm files through it would have SILENTLY REMOVED the sampling
# weight (the loader dedupes by prompt) — the run would have reported the designed mixture and trained on
# something else. The arms are now consumed verbatim, in order, with duplicates preserved, and the arm's
# sha256 travels in the receipt.
ARMS = os.environ.get("CYBERGUARD_ARMS", "")
if ARMS:
    import hashlib as _hash
    arm_path = Path(ARMS)
    if not arm_path.exists():
        raise SystemExit(f"CYBERGUARD_ARMS set but not found: {arm_path}")
    _arm_sha = _hash.sha256(arm_path.read_bytes()).hexdigest()
    train_rows = []
    with arm_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            msgs = []
            if d.get("system"):
                msgs.append({"role": "system", "content": d["system"]})
            msgs.append({"role": "user", "content": d["user"]})
            msgs.append({"role": "assistant", "content": d["assistant"]})
            train_rows.append({"messages": msgs})
    eval_rows = []
    log(f"ARM MODE: {arm_path} rows={len(train_rows)} sha256={_arm_sha[:16]}")
else:
    log(f"loading dataset {DATA}")
    _canon = cgdata.load_rows(DATA)
    log(f"  usable rows: {len(_canon)}")
    if MAX_ROWS:
        log(f"  capping to {MAX_ROWS} rows (MAX_ROWS)")
    train_rows, eval_rows = cgdata.make_split(_canon, EVAL_N, SEED, MAX_ROWS)
    train_rows = [{"messages": cgdata.to_messages(r)} for r in train_rows]
    eval_rows = [{"messages": cgdata.to_messages(r)} for r in eval_rows]
log(f"  train {len(train_rows)} / held-out {len(eval_rows)}")
# augment TRAINING rows only — eval_rows are left exactly as split, so the held-out set that
# verify_split.py validates is unchanged
if AUGMENT_SYSTEM:
    train_rows = [augment_system(r["messages"], i) for i, r in enumerate(train_rows)]
    train_rows = [{"messages": m} for m in train_rows]
    variants_used = len({(r["messages"][0]["content"] if r["messages"] and r["messages"][0]["role"] == "system" else "(none)") for r in train_rows})
    log(f"  system-prompt augmentation ON: {variants_used} distinct variants across training rows")

train_ds = Dataset.from_list(train_rows)
eval_ds = Dataset.from_list(eval_rows)

log(f"loading tokenizer + model from {BASE}")
tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(
    BASE,
    torch_dtype=torch.bfloat16 if DEVICE == "cuda" else torch.float32,
    device_map={"": 0} if DEVICE == "cuda" else None,
    trust_remote_code=True,
)
model.config.use_cache = False
log(f"  params: {sum(p.numel() for p in model.parameters())/1e9:.2f} B")

lora = LoraConfig(
    r=LORA_R, lora_alpha=LORA_R * 2, lora_dropout=0.05, bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
)
_RESUME = os.environ.get("RESUME_ADAPTER", "")
if _RESUME and Path(_RESUME).exists():
    from peft import PeftModel
    # is_trainable=True is MANDATORY. PeftModel.from_pretrained defaults to is_trainable=False, which sets
    # requires_grad=False on every LoRA parameter: the run then reports "trainable params: 0", logs
    # grad_norm 0 for its entire duration, and saves an artefact that behaves exactly like its input.
    # That is precisely what the 2026-09-28 23:29 relaunch did on BOTH arms - 3.05 GPU-h per arm spent
    # proving nothing, caught only by reading one log line. Do NOT re-wrap with get_peft_model either:
    # wrapping a PeftModel in another does not make the inner adapters trainable.
    model = PeftModel.from_pretrained(model, _RESUME, is_trainable=True)
    log(f"RESUMED LoRA adapter from {_RESUME} (is_trainable=True)")
else:
    model = get_peft_model(model, lora)
# Refuse to spend GPU on a run that cannot learn. Asserting on the OUTCOME (the trainable parameter count)
# rather than on the code path is what makes this class of defect unrepeatable.
_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
if _trainable <= 0:
    raise SystemExit(
        "REFUSING TO TRAIN: 0 trainable parameters. A frozen run burns the whole budget and yields an "
        "artefact that learned nothing (2026-09-28 23:29 is_trainable=False incident)."
    )
model.print_trainable_parameters()

callbacks = []
if MAX_MINUTES > 0:
    # MUST subclass TrainerCallback so every event the trainer fires (on_init_end,
    # on_epoch_*, on_evaluate, ...) resolves to the inherited no-op. An earlier version
    # hand-listed a few methods and crashed on on_init_end — and the smoke test missed it
    # because that run had no time box at all, i.e. it never exercised this path.
    class TimeBox(TrainerCallback):
        """Stop cleanly at a wall-clock budget so a run is predictable, not open-ended."""
        def __init__(self, minutes: float):
            self.deadline = time.time() + minutes * 60
            self._announced = False

        def on_step_end(self, args, state, control, **kw):
            if time.time() >= self.deadline:
                if not self._announced:
                    log(f"time budget reached at step {state.global_step}; stopping")
                    self._announced = True
                control.should_training_stop = True
            return control
    callbacks.append(TimeBox(MAX_MINUTES))

cfg = SFTConfig(
    output_dir=str(OUT_ADAPTER),
    max_length=MAX_SEQ,
    assistant_only_loss=True,   # Codex review #1 BLOCKER (2026-09-27): TRL defaults this to
    # False, and a conversational dataset then supervises the USER turns too — the model learns
    # to imitate prompts. The first v1 launch died on this and was stopped at step 92; the smoke
    # run proved the path, never the objective. The MASK PROOF below observes the mask on a real
    # batch — configuration is not evidence (training-craft: "assistant-only loss is
    # load-bearing and must be observed").
    per_device_train_batch_size=BATCH,
    gradient_accumulation_steps=GRAD_ACC,
    num_train_epochs=EPOCHS,
    max_steps=MAX_STEPS,
    learning_rate=LR,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    logging_steps=10,
    save_steps=500,
    save_total_limit=3,
    # ARM MODE HAS NO EVAL SPLIT: the frozen arms are the whole training set (the 500 held-out prompts are
    # excluded at build time and evaluated separately by eval_cyberguard.py). Passing the empty list made TRL
    # raise StopIteration in _prepare_dataset — caught by the MASK-PROOF smoke, not inside the 24 h window.
    eval_strategy=("no" if ARMS else "steps"),
    eval_steps=500,
    bf16=(DEVICE == "cuda"),   # bf16 is invalid on CPU; training_args raises for it
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    optim="adamw_torch",
    report_to=[],
    seed=SEED,
    dataset_num_proc=2,
    packing=False,
)

trainer = SFTTrainer(
    model=model, args=cfg, train_dataset=train_ds, eval_dataset=(None if ARMS else eval_ds),
    processing_class=tok, callbacks=callbacks or None,
)

steps_per_epoch = max(1, len(train_rows) // max(1, BATCH * GRAD_ACC))
log(f"starting training: ~{steps_per_epoch} steps/epoch, epochs={EPOCHS}, "
    f"max_steps={MAX_STEPS}, time_budget={MAX_MINUTES or 'none'} min")

# --- MASK PROOF (MASK_PROOF=1): observe supervision on a real batch, then exit before any
# optimizer step. Decodes the non--100 labels of the first collated batch and refuses (exit 8)
# if the supervised span is empty or is not assistant content. This is the check whose absence
# let a whole run train on the wrong objective.
if os.environ.get("MASK_PROOF", "0") == "1":
    batch = next(iter(trainer.get_train_dataloader()))
    lab, inp = batch["labels"], batch["input_ids"]
    sup = lab != -100
    n_sup, n_tot = int(sup.sum()), int(lab.numel())
    decoded = tok.decode(inp[0][sup[0]].tolist(), skip_special_tokens=True)
    probe = " ".join(decoded.split())[:60]
    log(f"MASK PROOF: supervised {n_sup}/{n_tot} tokens ({n_sup / max(1, n_tot):.1%})")
    log(f"MASK PROOF decoded supervised span (first 160 chars): {decoded[:160]!r}")
    # The train dataloader SHUFFLES, so the batch row is not train_rows[0]. Identify the span
    # by its content instead: it must occur inside SOME corpus assistant answer, and must not
    # occur inside any user prompt (the first proof attempt failed on exactly this index
    # mismatch — the mask was fine, the proof was wrong).
    asst_keys = [" ".join(r["messages"][-1]["content"].split()) for r in train_rows]
    user_keys = [" ".join(r["messages"][-2]["content"].split())
                 for r in train_rows if len(r["messages"]) >= 2]
    if n_sup == 0:
        print("MASK REFUSAL: zero supervised tokens", file=sys.stderr)
        sys.exit(8)
    if not (probe and any(probe in k for k in asst_keys)):
        print(f"MASK REFUSAL: supervised span matches no assistant answer: {probe!r}", file=sys.stderr)
        sys.exit(8)
    if any(probe in k for k in user_keys):
        print(f"MASK REFUSAL: supervised span appears inside a user prompt: {probe!r}", file=sys.stderr)
        sys.exit(8)
    print("MASK PROOF: PASS — supervision is assistant-only", flush=True)
    sys.exit(0)

train_result = trainer.train()
t_end = time.time()

log(f"saving adapter -> {OUT_ADAPTER}")
trainer.save_model(str(OUT_ADAPTER))
tok.save_pretrained(str(OUT_ADAPTER))

OUT_ADAPTER.mkdir(parents=True, exist_ok=True)
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
receipt = {
    "run": OUT_ADAPTER.name,
    "started_utc": time.strftime("%FT%TZ", time.gmtime(t_start)),
    "finished_utc": time.strftime("%FT%TZ", time.gmtime(t_end)),
    "wall_seconds": round(t_end - t_start, 1),
    "host": os.uname().nodename,
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "base_model": str(BASE),
    "dataset": str(DATA),
    "arms": ARMS or None,
    "arms_sha256": (_arm_sha if ARMS else None),
    "rows_total": (len(_canon) if not ARMS else len(train_rows)), "rows_train": len(train_rows), "rows_eval": len(eval_rows),
    "rows_after_prompt_dedupe": (len(_canon) if not ARMS else len(train_rows)), "max_rows_cap": MAX_ROWS,
    "config": {
        "max_seq": MAX_SEQ, "epochs": EPOCHS, "lr": LR, "batch": BATCH,
        "grad_accum": GRAD_ACC, "lora_r": LORA_R, "seed": SEED,
        "max_steps": MAX_STEPS, "max_minutes": MAX_MINUTES,
        "augment_system": AUGMENT_SYSTEM, "sys_variants": len(SYS_VARIANTS),
    },
    "train_metrics": {k: (round(v, 6) if isinstance(v, float) else v)
                      for k, v in (train_result.metrics or {}).items()},
    "log_history": [
        {k: (round(v, 6) if isinstance(v, float) else v) for k, v in entry.items()}
        for entry in trainer.state.log_history
    ],
    "versions": {},
}
for m in ("torch", "transformers", "peft", "trl", "datasets", "accelerate"):
    try:
        mod = __import__(m)
        receipt["versions"][m] = getattr(mod, "__version__", "?")
    except Exception:
        receipt["versions"][m] = None
with open(RECEIPT, "w") as f:
    json.dump(receipt, f, indent=1)

log(f"receipt -> {RECEIPT}")
log(f"train metrics: {json.dumps(receipt['train_metrics'])}")
log(f"adapter size: {sum(p.stat().st_size for p in OUT_ADAPTER.rglob('*') if p.is_file())/1e6:.1f} MB")
log("DONE")
sys.exit(0)
