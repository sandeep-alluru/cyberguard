#!/usr/bin/env python3
"""merge_equiv.py — Codex review #2 MAJOR 6 residual: does merge_and_unload() change behaviour?

The evaluator scores the MERGED model. If merged and unmerged adapter behaviour differ, the
adapter-equivalence claim in the verdict is void. Measures on N rows: held-out loss both ways,
plus greedy outputs on K prompts; reports max loss delta, max token-F1 delta, and exact-output
mismatch count. Run between box close and the main eval (~10 min).
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
N, K = int(os.environ.get("EQ_N", 50)), int(os.environ.get("EQ_K", 5))

tok = AutoTokenizer.from_pretrained(BASE)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
_, held = cgdata.make_split(cgdata.load_rows(DATA), 500, 0)
rows = held[:N]

t0 = time.time()
merged = load(BASE, str(ADAPTER))
loss_m, mask_m = held_out_loss(merged, tok, rows)
outs_m = [generate(merged, tok, "", r["user"]) for r in rows[:K]]
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

f1s = [tok_f1(m, u) for m, u in zip(outs_m, outs_u)]
report = {"rows_loss": N, "prompts_gen": K,
          "loss_merged": loss_m, "loss_unmerged": loss_u,
          "loss_delta": round(abs(loss_m - loss_u), 6),
          "mask_check_merged": mask_m, "mask_check_unmerged": mask_u,
          "gen_exact_mismatches": sum(1 for m, u in zip(outs_m, outs_u) if m != u),
          "gen_self_f1_min": min(f1s) if f1s else None,
          "wall_seconds": round(time.time() - t0, 1)}
out = ROOT / "evals" / f"merge-equiv-{ADAPTER.name}.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
