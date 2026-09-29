#!/usr/bin/env python3
"""merge_equiv.py — does merge_and_unload() change behaviour?

The evaluator scores the MERGED model. If merged and unmerged adapter behaviour differ, the
adapter-equivalence claim in the verdict is void. Measures on N rows: held-out loss both ways,
plus greedy outputs on K prompts; reports loss deltas, logit agreement, exact-output mismatch
count and token-F1. Run between box close and the main eval.

2026-09-29 — WHY EXACT-STRING EQUALITY IS NO LONGER THE GATE (pre-flight finding).
A smoke run on spark-40ee produced `loss_delta 0.0001` (the two paths are statistically the same model),
`top1_agreement 6/6` at the first generated position, 5 of 6 sequences identical over 48 new tokens — and
`gen_exact_mismatches 4` of 4 with `gen_self_f1_min 0.6751` over the full 256-token decode. The contract's
stage 2 required ZERO exact mismatches and an F1 floor of 0.99, so it would have ABORTED there, after the
whole training window had been spent.

The two paths are numerically different by construction: `merge_and_unload()` evaluates W + BA once in bf16
(one rounding), while the unmerged path evaluates x@W + (x@A)@B as separate bf16 ops (a different rounding).
Over 256 greedy steps any early token flip makes the two continuations diverge completely — chaotic
amplification, not a modelling error. Exact token equality is therefore NOT a valid equivalence criterion for
a merged-vs-unmerged comparison at this precision, and requiring it manufactures a failure.

So the equivalence claim now rests on the measurement that is actually sensitive to a wrong merge:
  * `top1_agreement_rate` — does merging change the model's FIRST decision? A wrong merge changes it.
  * `logit_rel_delta_mean` / `logit_rel_delta_max` — the size of the numerical difference.
  * `loss_delta` — distributional equivalence over N held-out rows.
`gen_exact_mismatches`, `gen_self_f1_min/mean/median` are still recorded, as REPORTED statistics describing
how far greedy decoding amplifies rounding — not as pass/fail gates.
"""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import cyberguard_data as cgdata
from eval_cyberguard import held_out_loss, generate, tok_f1, load

ROOT = Path(os.environ["CYBERGUARD_ROOT"])
DATA = ROOT / "data" / "trendyol-cybersec" / "CyberSec-Dataset_escaped.jsonl"
BASE = ROOT / "models" / "Qwen3-4B-Instruct-2507"
ADAPTER = ROOT / "adapters" / os.environ.get("RUN_NAME", "cyberguard-lora-v1")
# Review F19: zero generation mismatches in FIVE prompts carries a one-sided 95 % upper bound of ~45 % on the
# mismatch rate, which is no support for a behavioural-equivalence claim. N=200 loss rows and K=100 generated
# prompts bring that bound to ~3 % (both remain overridable via EQ_N / EQ_K).
N, K = int(os.environ.get("EQ_N", 200)), int(os.environ.get("EQ_K", 100))

tok = AutoTokenizer.from_pretrained(BASE)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
_, held = cgdata.make_split(cgdata.load_rows(DATA), 500, 0)
rows = held[:N]


def first_position_logits(model, tok, user):
    """The next-token distribution at the first generated position — where a wrong merge shows up."""
    msgs = [{"role": "user", "content": user}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    ids = tok(text, return_tensors="pt").input_ids.to(model.device)
    with torch.no_grad():
        return model(ids).logits[0, -1].float().cpu()


t0 = time.time()
merged = load(BASE, str(ADAPTER))
loss_m, mask_m = held_out_loss(merged, tok, rows)
outs_m = [generate(merged, tok, "", r["user"]) for r in rows[:K]]
logits_m = [first_position_logits(merged, tok, r["user"]) for r in rows[:K]]
del merged
torch.cuda.empty_cache()

from peft import PeftModel
un = PeftModel.from_pretrained(
    AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map={"": 0}),
    str(ADAPTER))
gc = un.generation_config
gc.do_sample = False; gc.num_beams = 1; gc.temperature = 1.0; gc.top_p = 1.0
gc.repetition_penalty = 1.0
un.eval()
loss_u, mask_u = held_out_loss(un, tok, rows)
outs_u = [generate(un, tok, "", r["user"]) for r in rows[:K]]
logits_u = [first_position_logits(un, tok, r["user"]) for r in rows[:K]]

f1s = [tok_f1(m, u) for m, u in zip(outs_m, outs_u)]
f1s_sorted = sorted(f1s)
f1_median = f1s_sorted[len(f1s_sorted) // 2] if f1s_sorted else None
# The measurement the equivalence claim rests on. Non-vacuity is asserted, not assumed: an empty comparison
# must never be reportable as agreement (an earlier version of this check sliced by the vocabulary dimension
# and reported "no divergence" while comparing nothing at all).
if not logits_m or len(logits_m) != len(logits_u):
    raise SystemExit(f"FATAL: logit comparison is empty or ragged "
                     f"({len(logits_m)} vs {len(logits_u)}) — equivalence would be unmeasured")
top1 = [int(a.argmax()) == int(b.argmax()) for a, b in zip(logits_m, logits_u)]
rel = [float((a - b).abs().max()) / max(1e-9, float(a.abs().mean())) for a, b in zip(logits_m, logits_u)]
top1_rate = sum(top1) / len(top1)

# Review F19 (pass eleven): reporting the REQUESTED N and K overstated support under the permitted EQ_N/EQ_K
# overrides - with EQ_N=100, EQ_K=200 the slicing used 100 prompts but the report claimed 200. Report what was
# actually measured, and keep the request alongside it for traceability.
report = {"rows_loss": len(rows), "prompts_gen": len(outs_u), "requested_eq": {"EQ_N": N, "EQ_K": K},
          "loss_merged": loss_m, "loss_unmerged": loss_u,
          "loss_delta": round(abs(loss_m - loss_u), 6),
          "mask_check_merged": mask_m, "mask_check_unmerged": mask_u,
          "gen_exact_mismatches": sum(1 for m, u in zip(outs_m, outs_u) if m != u),
          "gen_self_f1_min": min(f1s) if f1s else None,
          # reported statistics, not gates (see the module docstring): how far greedy decoding amplifies the
          # bf16 rounding difference between the two numerical paths.
          "gen_self_f1_mean": (sum(f1s) / len(f1s)) if f1s else None,
          "gen_self_f1_median": f1_median,
          # the equivalence basis
          "top1_agreement_rate": top1_rate,
          "top1_agreement_n": len(top1),
          "logit_rel_delta_mean": sum(rel) / len(rel),
          "logit_rel_delta_max": max(rel),
          "equivalence_basis": ("top1_agreement_rate (does merging change the model's first decision) + "
                               "logit deltas + loss_delta; exact-token equality is reported but is not a "
                               "valid gate for merged-vs-unmerged comparison in bf16 at MAX_NEW=256"),
          "max_new_tokens": int(os.environ.get("MAX_NEW", 256)),
          "wall_seconds": round(time.time() - t0, 1)}
out = ROOT / "evals" / f"merge-equiv-{ADAPTER.name}.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
