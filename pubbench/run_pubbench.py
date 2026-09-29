#!/usr/bin/env python3
"""Public-benchmark baseline: CyberMetric-500 + SecQA-v1-test on base vs Arm B.

MCQ accuracy. Greedy generation, parse first A/B/C/D letter.
Saves results JSON with per-question outcomes and accuracy per model/dataset.
"""
import csv, json, re, sys, time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE = '/home/clawer-samurai-1/.cache/huggingface/hub/models--Qwen--Qwen3-4B-Instruct-2507/snapshots/cdbee75f17c01a7cc42f958dc650907174af0554'
ADAPTER_B = "/home/clawer-samurai-1/AgentHub/cyberguard/adapters/cyberguard-lora-v2-armB"
OUT = "/home/clawer-samurai-1/AgentHub/cyberguard/pubbench/results.json"

INSTR = ("Answer the following multiple choice question. "
         "Reply with only the letter of the correct answer: A, B, C, or D.\n\n")

def load_datasets():
    items = []  # (dataset, question, options dict, gold)
    d = json.load(open("/home/clawer-samurai-1/AgentHub/cyberguard/pubbench/cybermetric-500.json"))
    lst = d if isinstance(d, list) else d[list(d.keys())[0]]
    for q in lst:
        items.append(("cybermetric-500", q["question"], q["answers"], q["solution"].strip().upper()))
    with open("/home/clawer-samurai-1/AgentHub/cyberguard/pubbench/secqa_test.csv") as f:
        for row in csv.DictReader(f):
            opts = {"A": row["A"], "B": row["B"], "C": row["C"], "D": row["D"]}
            items.append(("secqa-v1-test", row["Question"], opts, row["Answer"].strip().upper()))
    return items

def build_prompt(question, options):
    body = question + "\n" + "\n".join(f"{k}. {v}" for k, v in options.items())
    return INSTR + body + "\n\nAnswer:"

LETTER = re.compile(r"\b([ABCD])\b")

@torch.inference_mode()
def run_model(tag, use_adapter, items, tok):
    print(f"[{tag}] loading...", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE, trust_remote_code=True, torch_dtype=torch.float16, device_map="cuda")
    if use_adapter:
        model = PeftModel.from_pretrained(model, ADAPTER_B)
        model = model.merge_and_unload()
    model.eval()
    results = []
    t0 = time.time()
    for i, (ds, q, opts, gold) in enumerate(items):
        prompt = build_prompt(q, opts)
        msgs = [{"role": "user", "content": prompt}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inp = tok(text, return_tensors="pt").to("cuda")
        out = model.generate(**inp, max_new_tokens=10, do_sample=False,
                             pad_token_id=tok.eos_token_id)
        gen = tok.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True)
        m = LETTER.search(gen.upper())
        pred = m.group(1) if m else "?"
        results.append({"dataset": ds, "gold": gold, "pred": pred,
                        "correct": pred == gold, "raw": gen[:60]})
        if (i + 1) % 100 == 0:
            print(f"[{tag}] {i+1}/{len(items)}", flush=True)
    dt = time.time() - t0
    acc = sum(r["correct"] for r in results) / len(results)
    print(f"[{tag}] done: acc={acc:.4f} ({dt/60:.1f} min)", flush=True)
    del model
    torch.cuda.empty_cache()
    return {"tag": tag, "accuracy": acc, "n": len(results),
            "minutes": round(dt / 60, 1), "items": results}

def main():
    items = load_datasets()
    print(f"loaded {len(items)} questions", flush=True)
    tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
    out = {}
    out["base"] = run_model("base", False, items, tok)
    out["armB"] = run_model("armB", True, items, tok)
    summary = {}
    for tag, r in out.items():
        for ds in ("cybermetric-500", "secqa-v1-test"):
            sub = [x for x in r["items"] if x["dataset"] == ds]
            acc = sum(x["correct"] for x in sub) / len(sub)
            summary[f"{tag}/{ds}"] = f"{acc:.1%} ({sum(x['correct'] for x in sub)}/{len(sub)})"
    out["summary"] = summary
    json.dump(out, open(OUT, "w"))
    print("SUMMARY:", json.dumps(summary, indent=1), flush=True)

if __name__ == "__main__":
    main()
