import json, re, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
BASE="<home>/.cache/huggingface/hub/models--Qwen--Qwen3-4B-Instruct-2507/snapshots/cdbee75f17c01a7cc42f958dc650907174af0554"
tok=AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
model=AutoModelForCausalLM.from_pretrained(BASE, trust_remote_code=True, torch_dtype=torch.float16, device_map="cuda").eval()
data=json.load(open("<home>/<workspace>/cyberguard/pubbench/cybermetric-500.json"))["questions"]
def ask(q):
    opts="\n".join(f"{chr(65+i)}. {o}" for i,o in enumerate(q["options"]))
    prompt=f"Question: {q[chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)]}\n{opts}\nAnswer with only the letter."
    msgs=[{"role":"system","content":"You are a cybersecurity expert. Answer with only the letter."},
          {"role":"user","content":prompt}]
    ids=tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out=model.generate(ids, max_new_tokens=20, do_sample=False)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
for q in data[:5]:
    r=ask(q)
    m=re.search(r"\b([ABCD])\b", r)
    print("Q:",q["question"][:70]); print("GOLD:",q["answer"],"| OUT:",repr(r),"| PARSED:",m.group(1) if m else None); print()
