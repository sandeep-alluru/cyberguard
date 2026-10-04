#!/usr/bin/env python3
"""CyberSecEval MITRE-FRR — implemented to the SUPERVISOR'S spec (Astra, 2026-10-03).

Pinned upstream artifacts (commit 172c1074069eb88ec834124272c1b1c4f8893445):
  datasets/mitre_frr/mitre_frr.json      git blob sha1 15e58a34ea160aa5e1a75fd4437e60eab0a2f7f6
  benchmark/benchmark_utils.py           is_response_llm_refusal(), default max_chars=220
Population: all 750 entries in file order; `mutated_prompt` verbatim; NO filtering/sampling/rewriting.
Scoring: the upstream function unchanged, on the entire decoded response, no extra normalization.
  r_i = int(is_response_llm_refusal(response_i));  FRR_pct = 100 * sum(r_i) / 750
Report per model: refusal count, non-refusal count, FRR%, 95% Wilson, v3-minus-base pp (descriptive),
and the paired counts (base refusal, v3 refusal) as 00/01/10/11. No significance/non-inferiority claim.
Generation surface: identical to HarmBench — greedy, 1 trial, 512 tokens, batch 8, left padding, BF16,
no quantization, PEFT unmerged, own chat template, one user message, no system message, no truncation.
"""
import json, math, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRR = HERE / "frr"
sys.path.insert(0, str(HERE))

from run_harmbench import MODELS, wilson, MAX_NEW, BATCH   # reuse the exact model map + settings


def prompts():
    d = json.load(open(FRR / "mitre_frr.json"))
    return [(i, x["mutated_prompt"]) for i, x in enumerate(d)]


def generate_all(tag, items, out_path):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    base, adapter = MODELS[tag]
    print(f"[{tag}] loading {base}" + (f" + {adapter}" if adapter else ""), flush=True)
    tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
    tok.padding_side = "left"
    if tok.pad_token_id is None and tok.eos_token is not None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(base, trust_remote_code=True,
                                                 torch_dtype=torch.bfloat16, device_map="cuda")
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    eos = tok.eos_token_id
    eos_set = set(eos) if isinstance(eos, (list, tuple)) else ({eos} if eos is not None else set())
    rows, t0 = [], time.time()
    for i in range(0, len(items), BATCH):
        chunk = items[i:i + BATCH]
        texts = [tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False,
                                         add_generation_prompt=True) for _r, p in chunk]
        enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False,
                  truncation=False).to(model.device)
        if enc.input_ids.shape[1] + MAX_NEW > 4096:
            raise SystemExit(f"  OVERFLOW at batch {i}: prompt {enc.input_ids.shape[1]} + {MAX_NEW} > 4096 "
                             f"-> aggregate must stay UNMEASURED")
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=MAX_NEW, do_sample=False, num_beams=1,
                                 repetition_penalty=1.0, pad_token_id=tok.pad_token_id or tok.eos_token_id)
        plen = enc.input_ids.shape[1]
        for j, (rn, p) in enumerate(chunk):
            seq = gen[j][plen:]
            text = tok.decode(seq, skip_special_tokens=True)
            # Astra: the old test was len(seq)==0 on the TOKEN array. A sequence holding only skipped
            # special tokens has length > 0 but decodes to empty text, so emptiness must be judged on
            # the decoded content.
            rows.append({"row": rn, "prompt": p, "response": text,
                         "empty": text.strip() == ""})
        if (i + BATCH) % 150 < BATCH:
            print(f"[{tag}] {min(i+BATCH, len(items))}/{len(items)}", flush=True)
    json.dump(rows, open(out_path, "w"))
    print(f"[{tag}] done ({round((time.time()-t0)/60,1)} min)", flush=True)


def score(tags, gen_dir, out_path):
    sys.path.insert(0, str(FRR))
    from benchmark_utils import is_response_llm_refusal   # the upstream function, unchanged
    out, labels = {}, {}
    for tag in tags:
        rows = json.load(open(Path(gen_dir) / f"frr-{tag}.json"))
        r = [int(bool(is_response_llm_refusal(x["response"]))) for x in rows]
        labels[tag] = r
        k = sum(r)
        out[tag] = {"n": len(rows), "refusal_count": k, "non_refusal_count": len(rows) - k,
                    "FRR_pct": round(100 * k / len(rows), 2),
                    "wilson95": [wilson(k, len(rows)), wilson(k, len(rows), True)],
                    "empty_responses": sum(1 for x in rows if x["empty"]),
                    "status": "MEASURED"}
        print(f"[frr] {tag}: {out[tag]}", flush=True)
    if "base" in labels and "v3" in labels:
        b, v = labels["base"], labels["v3"]
        pair = {"00": 0, "01": 0, "10": 0, "11": 0}
        for x, y in zip(b, v):
            pair[f"{x}{y}"] += 1
        out["v3_minus_base_pp"] = round(out["v3"]["FRR_pct"] - out["base"]["FRR_pct"], 2)
        out["paired_counts_00_01_10_11"] = pair
    json.dump({"per_model": out, "labels": labels,
               "metric": "upstream CyberSecEval MITRE-FRR heuristic refusal rate; "
                         "100*refusals/750; pinned commit 172c1074069eb88ec834124272c1b1c4f8893445"},
              open(out_path, "w"), indent=1)
    return out


if __name__ == "__main__":
    mode = sys.argv[1]
    items = prompts()
    gens = HERE / "frr-generations"
    gens.mkdir(exist_ok=True)
    if mode == "count":
        print("  population n =", len(items))
    elif mode == "generate":
        for t in sys.argv[2].split(","):
            generate_all(t, items, gens / f"frr-{t}.json")
    elif mode == "score":
        score(sys.argv[2].split(","), gens, HERE / "frr-results.json")
