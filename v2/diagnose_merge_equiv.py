#!/usr/bin/env python3
"""diagnose_merge_equiv.py — WHY merged and unmerged generations can differ, and whether the merge is correct.

BACKGROUND (2026-09-29). A merge-equivalence smoke run on spark-40ee reported
`loss_delta 0.0001` — i.e. the merged and unmerged models are statistically the same model — together with
`gen_exact_mismatches 4` of 4 prompts and `gen_self_f1_min 0.6751`. The evaluation contract's stage 2 required
`gen_exact_mismatches == 0` and `gen_self_f1_min >= 0.99`, so it would have ABORTED there, after the whole
training window had been spent.

Two very different explanations fit that pair of numbers, and they have opposite consequences:
  (a) the merge is WRONG (the evaluator scores a different model than the one trained) — a fatal defect; or
  (b) the merge is right, and exact token equality is simply not achievable, because `merge_and_unload()`
      evaluates W + BA once in bf16 (one rounding) while the unmerged path evaluates x@W + (x@A)@B as separate
      bf16 ops (different rounding). A ~1e-2 relative logit difference at each step is enough for greedy
      decoding to flip a token, after which the two continuations diverge completely — chaotic amplification,
      not a modelling error.

`loss_delta` at 1e-4 points at (b), but that is inference, and inference from an aggregate can be wrong. This
measures the per-position agreement directly — while noting, per review #18, that agreement on sampled paths is
evidence about those paths and not a proof of behavioural equivalence:
  * LOGIT agreement on the same inputs — max/mean |Δlogit| and top-1 agreement. On the MEASURED surface a
    correct merge shows small deltas and high top-1 agreement, and a grossly wrong merge degrades it. It cannot
    do more than that: review #18 produced an executed counterexample that changed behaviour while passing every
    agreement condition, so agreement over sampled paths can never exclude a defect concentrated outside them.
    That is why the merge is ALSO checked at the WEIGHT level, exhaustively — see merge_equiv.merge_weight_check.
  * DIVERGENCE POINT in greedy decoding — the token index at which the two sequences first differ. Chaos shows
    as an early single flip followed by total divergence; a wrong merge shows divergence at index 0.

Usage (on a host):
  RUN_NAME=cyberguard-lora-v2-armA EQ_N=6 EQ_K=48 python v2/diagnose_merge_equiv.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(os.environ["CYBERGUARD_ROOT"])
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v2"))

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402
import cyberguard_data as cgdata  # noqa: E402
from eval_cyberguard import load  # noqa: E402

DATA = ROOT / "data" / "trendyol-cybersec" / "CyberSec-Dataset_escaped.jsonl"
BASE = ROOT / "models" / "Qwen3-4B-Instruct-2507"
ADAPTER = ROOT / "adapters" / os.environ.get("RUN_NAME", "cyberguard-lora-v2-armA")
N = int(os.environ.get("EQ_N", 6))
K_NEW = int(os.environ.get("EQ_K", 48))
OUT = ROOT / "v2" / "data" / "mixture" / f"merge-equiv-diagnosis-{ADAPTER.name}.json"


def build_ids(tok, user):
    msgs = [{"role": "user", "content": user}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    return tok(text, return_tensors="pt").input_ids


def main() -> int:
    tok = AutoTokenizer.from_pretrained(BASE)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    _, held = cgdata.make_split(cgdata.load_rows(DATA), 500, 0)
    rows = held[:N]
    prompts = [r["user"] for r in rows]
    t0 = time.time()

    # ---- merged path (exactly what the evaluator scores)
    merged = load(BASE, str(ADAPTER))
    m_logits, m_seqs, prompt_lens = [], [], []
    with torch.no_grad():
        for p in prompts:
            ids = build_ids(tok, p).to(merged.device)
            prompt_lens.append(int(ids.shape[1]))
            m_logits.append(merged(ids).logits[0, -1].float().cpu())
            m_seqs.append(merged.generate(ids, max_new_tokens=K_NEW, do_sample=False,
                                          pad_token_id=tok.pad_token_id or tok.eos_token_id)[0].tolist())
    del merged
    torch.cuda.empty_cache()

    # ---- unmerged path (base + adapter attached separately)
    from peft import PeftModel
    un = PeftModel.from_pretrained(
        AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map={"": 0}),
        str(ADAPTER))
    gc = un.generation_config
    gc.do_sample = False; gc.num_beams = 1; gc.temperature = 1.0; gc.top_p = 1.0; gc.repetition_penalty = 1.0
    un.eval()
    u_logits, u_seqs = [], []
    with torch.no_grad():
        for j, p in enumerate(prompts):
            ids = build_ids(tok, p).to(un.device)
            assert int(ids.shape[1]) == prompt_lens[j], (
                f"prompt {j} tokenised to a different length on the two paths -- the comparison would be "
                f"between different inputs")
            u_logits.append(un(ids).logits[0, -1].float().cpu())
            u_seqs.append(un.generate(ids, max_new_tokens=K_NEW, do_sample=False,
                                      pad_token_id=tok.pad_token_id or tok.eos_token_id)[0].tolist())

    per_prompt = []
    for i, p in enumerate(prompts):
        d = (m_logits[i] - u_logits[i]).abs()
        top1_same = int(m_logits[i].argmax()) == int(u_logits[i].argmax())
        # First index at which the two greedy continuations differ. The prompt length is the INPUT token
        # count, captured when the ids were built -- NOT len(logits), which is the vocabulary dimension
        # (151,936). That mistake made the slice empty and reported "first_div=None of 0" for every prompt:
        # a measurement that looked like agreement while comparing nothing at all. Assert it is non-empty.
        ml, ul = m_seqs[i], u_seqs[i]
        pref = prompt_lens[i]
        new_m, new_u = ml[pref:], ul[pref:]
        assert len(new_m) > 0 and len(new_u) > 0, (
            f"empty continuation slice for prompt {i}: prompt_len={pref} seq_len={len(ml)} -- "
            f"the divergence measurement would be vacuous")
        first = next((j for j, (a, b) in enumerate(zip(new_m, new_u)) if a != b), None)
        per_prompt.append({
            "i": i,
            "max_abs_logit_delta": float(d.max()),
            "mean_abs_logit_delta": float(d.mean()),
            "top1_agree": bool(top1_same),
            "logit_scale": float(m_logits[i].abs().mean()),
            "rel_logit_delta": float(d.max() / max(1e-9, float(m_logits[i].abs().mean()))),
            "first_divergence_token": first,
            "new_tokens_compared": min(len(new_m), len(new_u)),
        })

    n = len(per_prompt)
    report = {
        "check": "merge-equivalence diagnosis",
        "adapter": ADAPTER.name,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host": os.uname().nodename,
        "prompts": n,
        "max_new_tokens": K_NEW,
        "logit_mean_max_abs_delta": sum(x["max_abs_logit_delta"] for x in per_prompt) / n,
        "logit_mean_rel_delta": sum(x["rel_logit_delta"] for x in per_prompt) / n,
        "top1_agreement_rate": sum(1 for x in per_prompt if x["top1_agree"]) / n,
        "exact_sequence_matches": sum(1 for i in range(n) if m_seqs[i] == u_seqs[i]),
        "per_prompt": per_prompt,
        "wall_seconds": round(time.time() - t0, 1),
    }
    report["interpretation"] = (
        "top1_agreement_rate == 1.0 with a small relative logit delta means the merge is numerically correct "
        "and any string mismatch is chaotic amplification of bf16 rounding in greedy decoding; a top-1 "
        "disagreement at the FIRST position would instead indicate a genuine merge defect."
    )
    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "per_prompt"}, indent=1))
    for x in per_prompt:
        print(f"  prompt {x['i']}: rel_dlogit={x['rel_logit_delta']:.5f} top1={x['top1_agree']} "
              f"first_div={x['first_divergence_token']} of {x['new_tokens_compared']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
