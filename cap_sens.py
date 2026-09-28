#!/usr/bin/env python3
"""cap_sens.py — review #5 BLOCKER 2 response: decode-surface sensitivity for the harm result.

Conditions (offensive battery, 60 prompts):
  A) tuned, batch=1,  max_new=256   <- isolates batching effect vs the main run
  B) base,  batch=1,  max_new=256
  C) tuned, batch=16, max_new=512   <- isolates token-limit/truncation effect
Also: P2 full 120 tuned outputs stored (review #5 MAJOR: reparse ALL unparsed, not 30).
Refusal counts per condition + paired transition vs main run; outputs preserved.
"""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cap_probes as PB
import cap_scorers as S
import cyberguard_contract as contract

ROOT = Path(os.environ["CYBERGUARD_ROOT"])
RDIR = ROOT / "cap" / "receipts"
BASE = ROOT / "models" / "Qwen3-4B-Instruct-2507"
ADAPTER = ROOT / "adapters" / "cyberguard-lora-v1"
log = lambda m: print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
torch.manual_seed(0)
tok = AutoTokenizer.from_pretrained(BASE)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
tok.padding_side = "left"

def load(adapter=None):
    m = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map={"": 0})
    if adapter:
        from peft import PeftModel
        m = PeftModel.from_pretrained(m, str(adapter)).merge_and_unload()
    gc = m.generation_config
    gc.do_sample = False; gc.num_beams = 1; gc.temperature = 1.0; gc.top_p = 1.0; gc.repetition_penalty = 1.0
    m.eval(); return m

def gen(model, prompts, max_new, batch):
    outs = []
    for i in range(0, len(prompts), batch):
        chunk = prompts[i:i + batch]
        if batch == 1:
            enc = tok(chunk[0], return_tensors="pt", add_special_tokens=False,
                      truncation=True, max_length=2048 - max_new).to(model.device)
        else:
            enc = tok(chunk, return_tensors="pt", padding=True, add_special_tokens=False,
                      truncation=True, max_length=2048 - max_new).to(model.device)
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=max_new, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
        plen = enc.input_ids.shape[1]
        outs.extend(tok.decode(out[j][plen:], skip_special_tokens=True).strip() for j in range(len(chunk)))
        if (i // batch) % 10 == 0:
            log(f"  {len(outs)}/{len(prompts)}")
    return outs

def summary(outs):
    cls = [contract.classify(o) for o in outs]
    return {"refused": cls.count("refused"), "answered": cls.count("answered"),
            "nonresp": cls.count("non_responsive"),
            "wilson95": S.wilson(cls.count("refused"), len(cls))}

log("loading arms")
base = load()
tuned = load(ADAPTER)
OFF = PB.OFFENSIVE_60
res = {}
log("A) tuned batch1 256")
a = gen(tuned, OFF, 256, 1)
res["A_tuned_b1_256"] = summary(a)
log("B) base batch1 256")
b = gen(base, OFF, 256, 1)
res["B_base_b1_256"] = summary(b)
log("C) tuned batched 512")
c = gen(tuned, OFF, 512, 16)
res["C_tuned_b16_512"] = summary(c)
# paired transitions vs main run (batched 256) from cap-7-harm.json
main = json.loads((RDIR / "cap-7-harm.json").read_text())["tuned"]["off_classes"]
ma = [x == "refused" for x in main]
for name, outs2 in (("A", a), ("C", c)):
    m2 = [contract.classify(o) == "refused" for o in outs2]
    res[f"transition_main_vs_{name}"] = {
        "both_refused": sum(1 for x, y in zip(ma, m2) if x and y),
        "main_ref_only": sum(1 for x, y in zip(ma, m2) if x and not y),
        "cond_ref_only": sum(1 for x, y in zip(ma, m2) if y and not x),
        "neither": sum(1 for x, y in zip(ma, m2) if not x and not y)}
(RDIR / "cap-sens-decode.json").write_text(json.dumps(
    {"status": "done", "kind": "decode-sensitivity", **res,
     "A_outputs": a, "B_outputs": b, "C_outputs_first_20": c[:20]}, indent=1))
log("sens receipt written")

# P2 full outputs (tuned) for full-corpus reparse
rows = PB.triage_fallback()["rows"][:200]
p2 = ["Classify the following item as MALICIOUS or BENIGN. Answer with exactly one word.\n\n" + r["text"][:1500] for r in rows]
p2outs = gen(tuned, p2, 16, 16)
def parse_full(o):
    o2 = (o or "").lower()
    mb = __import__("re").search(r"\b(malicious|phishing|spam|threat)\b", o2)
    mo = __import__("re").search(r"\bbenign\b|\bnot malicious\b|\bsafe\b|\blegitimate\b", o2)
    if mb and mo: return "malicious" if mb.start() <= mo.start() else "benign"
    if mb: return "malicious"
    if mo: return "benign"
    return "unparsed"
fp = [parse_full(o) for o in p2outs]
golds = [r["label"] for r in rows[:len(p2outs)]]
(RDIR / "cap-2-fulloutputs.json").write_text(json.dumps(
    {"status": "done", "kind": "full-corpus-reparse",
     "window60": S.triage_confusion([S.parse_triage(o) for o in p2outs], golds),
     "fulltext": S.triage_confusion(fp, golds),
     "outputs": p2outs}, indent=1))
log("P2 full outputs written; DONE")
