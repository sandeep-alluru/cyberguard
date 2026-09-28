#!/usr/bin/env python3
"""verify_eval_mask.py — decisive measurement for Codex review #2 MAJOR 4, tokenizer-only.

Over ALL held-out rows: does the prompt tokenization form an EXACT prefix of the template-
rendered full text? Is the first supervised target after causal shift the first assistant token?
Is terminal treatment present? Is supervision positive after 2048-token truncation?
Zero mismatches establishes "not a defect" for this dataset/tokenizer; nonzero quantifies it.
"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cyberguard_data as cgdata
from transformers import AutoTokenizer

ROOT = Path(os.environ["CYBERGUARD_ROOT"])
DATA = ROOT / "data" / "trendyol-cybersec" / "CyberSec-Dataset_escaped.jsonl"
BASE = ROOT / "models" / "Qwen3-4B-Instruct-2507"
EVAL_N, SEED, MAX_LEN = 500, 0, 2048

tok = AutoTokenizer.from_pretrained(BASE)
_, held = cgdata.make_split(cgdata.load_rows(DATA), EVAL_N, SEED)
n = pre = shift = term = zero = trunc_zero = 0
for r in held:
    n += 1
    msgs = ([{"role": "system", "content": r["system"]}] if r["system"] else []) \
        + [{"role": "user", "content": r["user"]}]
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    full = tok.apply_chat_template(msgs + [{"role": "assistant", "content": r["assistant"]}],
                                   tokenize=False, add_generation_prompt=False)
    p_ids = tok(prompt, add_special_tokens=False).input_ids
    f_ids = tok(full, add_special_tokens=False).input_ids
    if list(f_ids[:len(p_ids)]) != list(p_ids):
        pre += 1
        continue
    a_ids = tok(r["assistant"], add_special_tokens=False).input_ids
    if f_ids[len(p_ids)] != a_ids[0]:
        shift += 1
    tail = f_ids[len(p_ids):]
    if not (tok.eos_token_id in tail[-2:] if tok.eos_token_id else True):
        term += 1
    sup_after_trunc = max(0, min(len(f_ids), MAX_LEN) - len(p_ids))
    if sup_after_trunc == 0:
        trunc_zero += 1
print(f"rows={n} prompt_prefix_mismatches={pre} first_sup_target_mismatch={shift} "
      f"terminal_token_missing={term} zero_sup_after_truncation={trunc_zero}")
sys.exit(0 if pre == 0 and shift == 0 and term == 0 else 1)
