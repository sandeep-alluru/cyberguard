#!/usr/bin/env python3
"""merge_equiv.py — does merge_and_unload() change behaviour?

The evaluator scores the MERGED model. If merged and unmerged behaviour differ, the adapter-equivalence claim
in the verdict is void. Run between box close and the main eval.

HISTORY, because the acceptance basis changed twice and both changes were driven by measurement.

2026-09-29 (a) EXACT-TOKEN EQUALITY WAS UNACHIEVABLE. The gate was `gen_exact_mismatches == 0` plus
`gen_self_f1_min >= 0.99`. Measured on the real adapter, that outcome is a function of DECODE LENGTH alone:
MAX_NEW=32 → 0/4 mismatches, F1 1.0; MAX_NEW=48 → 1/6; MAX_NEW=256 → 4/4, F1 0.675 — while `loss_delta`
(1e-4) and first-position top-1 agreement (100 %) never moved. `merge_and_unload()` evaluates W + BA once in
bf16 while the unmerged path evaluates x@W + (x@A)@B as separate bf16 ops, and greedy decoding amplifies that
~15 % relative logit difference. Gating on exact equality measured decode length, not equivalence, and would
have aborted the contract after the window was spent.

2026-09-29 (b) FIRST-POSITION-ONLY AGREEMENT WAS TOO WEAK. Review #16 rejected the replacement basis:
"First-position agreement plus aggregate loss permits unrestricted continuation changes". Correct — agreeing on
the first token constrains nothing later, and aggregate loss can mask compensating errors.

So the equivalence basis is now **teacher-forced per-position agreement over the assistant span** — the exact
surface `held_out_loss` scores. The token sequence is FIXED, so this is not subject to decoding chaos; it is
sensitive to a change ANYWHERE in the continuation; and it is reported with the number of positions compared,
so it cannot be vacuous. `loss_delta` remains a second, distributional line of evidence. The free-running
generation statistics are REPORTED, never gated, because they measure amplification rather than equivalence.
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
N = int(os.environ.get("EQ_N", 200))
K = int(os.environ.get("EQ_K", 100))
# Teacher-forced agreement is cheap (no generation), so it can cover more rows than the generation sample.
TF_ROWS = int(os.environ.get("EQ_TF_ROWS", 100))

tok = AutoTokenizer.from_pretrained(BASE)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
_, held = cgdata.make_split(cgdata.load_rows(DATA), 500, 0)
rows = held[:N]


def tf_agreement(m_model, u_model, tok, rows, max_rows):
    """Per-position next-token top-1 agreement over the ASSISTANT span, teacher-forced.

    The construction is deliberately identical to eval_cyberguard.held_out_loss (same chat template, same
    add_special_tokens=False, same 2048 truncation and same prompt-prefix boundary), so this measures the
    surface the benchmark actually scores rather than a lookalike.
    """
    out = []
    for r in rows[:max_rows]:
        msgs = []
        if r["system"]:
            msgs.append({"role": "system", "content": r["system"]})
        msgs.append({"role": "user", "content": r["user"]})
        prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        full = tok.apply_chat_template(msgs + [{"role": "assistant", "content": r["assistant"]}],
                                       tokenize=False, add_generation_prompt=False)
        p_ids = tok(prompt, add_special_tokens=False).input_ids
        f_ids = tok(full, add_special_tokens=False, truncation=True, max_length=2048).input_ids
        p_len = min(len(p_ids), len(f_ids))
        lo, hi = p_len - 1, len(f_ids) - 1          # position t predicts token t+1; supervised when t+1 >= p_len
        if hi <= lo:
            continue
        ids = torch.tensor([f_ids], device=m_model.device)
        with torch.no_grad():
            lm = m_model(ids).logits[0].float()
            lu = u_model(ids).logits[0].float()
        # Raggedness must be rejected explicitly: torch broadcasts (T,V) against (1,V) without complaint, so a
        # shape mismatch would silently compare the wrong things. Review #18 verified the earlier claim of
        # "unconditional rejection" was not in fact implemented.
        if tuple(lm.shape) != tuple(lu.shape):
            raise SystemExit(f"FATAL: ragged logits: merged {tuple(lm.shape)} vs unmerged {tuple(lu.shape)}")
        am = lm[lo:hi].argmax(dim=-1)
        au = lu[lo:hi].argmax(dim=-1)
        dis = am != au
        d = (lm[lo:hi] - lu[lo:hi]).abs()
        out.append({
            "positions": int(hi - lo),
            "disagreements": int(dis.sum()),
            "first_disagreement": (int(dis.nonzero()[0]) if bool(dis.any()) else None),
            "per_position_max_delta_mean": float(d.max(dim=-1).values.mean()),
            "logit_abs_mean": float(lm[lo:hi].abs().mean()),
        })
        del lm, lu, d
    return out



def merge_weight_check(merged, un):
    """DETERMINISTIC check of the merge arithmetic: for every LoRA-wrapped linear layer, the merged model's
    weight must equal `base_weight + scaling * (B @ A)` in float32, to bf16 rounding.

    WHY THIS EXISTS (review #18, which rejected the previous basis): a sampled behavioural comparison -- even a
    teacher-forced one over every supervised position -- only constrains the paths it samples, and #18 produced an
    EXECUTED counterexample that changed the last eight of 200 supervised positions in every row yet passed all
    of the numerical conditions (0.96 agreement, 0.3604 separation, unchanged gold loss, zero first-position
    disagreements). The honest conclusion is that no finite behavioural sample establishes behavioural
    equivalence. But equivalence is not the property the evaluator actually needs. The evaluator needs to know
    that `merge_and_unload()` produced THE CORRECT WEIGHTS from the trained adapter -- and that IS decidable
    exactly, over every element of every adapted matrix, with no sampling and no decoding:

        expected = W_base + scaling * (B @ A)      in float32
        measured = the merged model's own weight

    A partial scaling error, a dropped target module, a wrong adapter order or a mangled shape all show up here
    as a large per-element difference, where they could hide from any behavioural sample.

    Returns a list of per-module results; raises if no LoRA-wrapped layer is found (an empty check must never be
    reportable as exactness).
    """
    import torch
    rows = []
    for name, mod in un.named_modules():
        if not (hasattr(mod, "lora_A") and hasattr(mod, "base_layer")):
            continue
        # PEFT wraps a target as base_model.model.<path>; the merged model has the bare <path>.
        mpath = name.split("base_model.model.", 1)[-1] if "base_model.model." in name else name
        try:
            tgt = merged.get_submodule(mpath)
        except AttributeError:
            raise SystemExit(f"FATAL: merged model has no module {mpath!r} corresponding to {name!r} -- the "
                             f"naming assumption behind the weight check is wrong and the check would be blind")
        Wb = mod.base_layer.weight
        Wm = tgt.weight
        if tuple(Wm.shape) != tuple(Wb.shape):
            raise SystemExit(f"FATAL: {mpath}: merged weight {tuple(Wm.shape)} != base weight {tuple(Wb.shape)}")
        for adapter in mod.lora_A:
            A = mod.lora_A[adapter].weight
            B = mod.lora_B[adapter].weight
            scaling = float(mod.scaling[adapter])
            with torch.no_grad():
                Wbf = Wb.float()
                exp = Wbf + scaling * (B.float() @ A.float())
                if tuple(exp.shape) != tuple(Wm.shape):
                    raise SystemExit(f"FATAL: {mpath}: expected merge {tuple(exp.shape)} != merged "
                                     f"{tuple(Wm.shape)} -- B@A does not match the base matrix")
                d = (Wm.float() - exp).abs()
                # SENSITIVITY CONTROL, by construction rather than by sampling: the error this same check would
                # report if the adapter's contribution were mis-scaled by 10 %. It makes the tolerance
                # meaningful (review #18 asked exactly this) and needs no extra model to be loaded.
                upd = scaling * (B.float() @ A.float())
                d90 = (Wm.float() - (Wbf + 0.90 * upd)).abs()
                # CONTROL A: the adapter contribution dropped for this module entirely -- what "this target
                # module was never merged" (a wrong subset of target modules) looks like.
                ddrop = (Wm.float() - Wbf).abs()
            rows.append({
                "module": mpath,
                "adapter": adapter,
                "scaling": scaling,
                "elements": int(Wm.numel()),
                "max_abs": float(d.max()),
                "mean_abs": float(d.mean()),
                "base_abs_mean": float(Wbf.abs().mean()),
                "merged_abs_mean": float(Wm.float().abs().mean()),
                # relative to the MERGED weight scale, not the base: the LoRA update dominates the merged value,
                # so dividing by the base magnitude overstates the error (found by measuring it).
                "max_rel_to_merged": float(d.max() / max(1e-12, float(Wm.float().abs().mean()))),
                "control_module_dropped_max_abs": float(ddrop.max()),
                "control_scale_0p9_max_abs": float(d90.max()),
            })
    if not rows:
        raise SystemExit("FATAL: no LoRA-wrapped layer found -- the weight-level check is empty, so it must not "
                         "be reported as exactness")
    return rows

t0 = time.time()
# Both paths stay resident so the teacher-forced comparison can read them position by position. Two bf16 4B
# models plus activations fit comfortably (the window runs with ~67 GB free), and stage 1 runs with no battery
# competing for the GPU.
merged = load(BASE, str(ADAPTER))
from peft import PeftModel
un = PeftModel.from_pretrained(
    AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map={"": 0}),
    str(ADAPTER))
gc = un.generation_config
gc.do_sample = False; gc.num_beams = 1; gc.temperature = 1.0; gc.top_p = 1.0
gc.repetition_penalty = 1.0
un.eval()

wchk = merge_weight_check(merged, un)

tf = tf_agreement(merged, un, tok, rows, TF_ROWS)

# NEGATIVE CONTROL. A threshold on tf_top1_agreement_rate is only meaningful if it SEPARATES "same model,
# different arithmetic precision" from "different model". So the same measurement is taken against the BASE
# model (the adapter disabled): that is what a real merge defect -- a dropped merge, a wrong scale, wrong
# target modules -- would look like. The gate is then justified by the measured gap rather than fitted to the
# single observed number. Cheap: the base is already resident, only the adapter is switched off.
# PAIRED: the control uses the same rows as the positive comparison, so the difference is a paired comparison
# over identical support (review #18: with 100 rows positive and 25 negative, their difference was not paired).
NC_ROWS = int(os.environ.get("EQ_NC_ROWS", TF_ROWS))
try:
    with un.disable_adapter():
        nc = tf_agreement(merged, un, tok, rows, NC_ROWS)
except Exception as e:                                                     # noqa: BLE001
    nc = []
    print(f"  WARNING: negative control could not be measured ({type(e).__name__}: {e})")
nc_positions = sum(x["positions"] for x in nc)
nc_disagree = sum(x["disagreements"] for x in nc)
nc_rate = (1.0 - nc_disagree / nc_positions) if nc_positions else None
tf_positions = sum(x["positions"] for x in tf)
tf_disagree = sum(x["disagreements"] for x in tf)
if tf_positions <= 0:
    raise SystemExit("FATAL: teacher-forced comparison covered 0 positions — equivalence would be unmeasured "
                     "and an empty comparison must never be reportable as agreement")
tf_rate = 1.0 - tf_disagree / tf_positions

loss_m, mask_m = held_out_loss(merged, tok, rows)
loss_u, mask_u = held_out_loss(un, tok, rows)

outs_m = [generate(merged, tok, "", r["user"]) for r in rows[:K]]
outs_u = [generate(un, tok, "", r["user"]) for r in rows[:K]]
f1s = [tok_f1(m, u) for m, u in zip(outs_m, outs_u)]
f1s_sorted = sorted(f1s)

# first-position agreement, kept as a separate reported figure (it is the weakest of the three signals)
first_pos = [x for x in tf if x["disagreements"] >= 0]
first_disagree = sum(1 for x in tf if x["first_disagreement"] == 0)

report = {
    "rows_loss": len(rows), "prompts_gen": len(outs_u), "requested_eq": {"EQ_N": N, "EQ_K": K,
                                                                        "EQ_TF_ROWS": TF_ROWS},
    "loss_merged": loss_m, "loss_unmerged": loss_u,
    "loss_delta": round(abs(loss_m - loss_u), 6),
    "mask_check_merged": mask_m, "mask_check_unmerged": mask_u,
    # ---- the equivalence basis: teacher-forced, over the scored surface, all positions
    "tf_rows": len(tf),
    "tf_positions": tf_positions,
    "tf_top1_disagreements": tf_disagree,
    "tf_top1_agreement_rate": tf_rate,
    "tf_first_position_disagreements": first_disagree,
    "tf_first_disagreement_examples": [x["first_disagreement"] for x in tf if x["first_disagreement"] is not None][:5],
    "tf_per_position_max_delta_mean": (sum(x["per_position_max_delta_mean"] for x in tf) / len(tf)) if tf else None,
    # ---- the DETERMINISTIC basis: the merge arithmetic, over every element of every adapted matrix
    "merge_weight_modules": len(wchk),
    "merge_weight_elements": sum(x["elements"] for x in wchk),
    "merge_weight_max_abs": max(x["max_abs"] for x in wchk),
    "merge_weight_mean_abs": sum(x["mean_abs"] for x in wchk) / len(wchk),
    "merge_weight_max_rel_to_merged": max(x["max_rel_to_merged"] for x in wchk),
    "merge_weight_worst_module": max(wchk, key=lambda x: x["max_abs"])["module"],
    # Sensitivity, stated honestly. CONTROL A (a target module never merged) separates strongly -- that is the
    # defect class the reviewer named. CONTROL B (a 10 % mis-scaling) separates by only ~3x, because a 10 %
    # change in the adapter contribution is comparable to the bf16 rounding of the merged sum itself. So this
    # check RESOLVES deviations of order the adapter update, and does NOT resolve sub-1 % mis-scalings. Reported
    # rather than hidden: a tolerance the check cannot actually resolve would be theatre.
    "merge_weight_control_module_dropped_max_abs": max(x["control_module_dropped_max_abs"] for x in wchk),
    "merge_weight_control_module_dropped_ratio": (max(x["control_module_dropped_max_abs"] for x in wchk) /
                                                  max(1e-12, max(x["max_abs"] for x in wchk))),
    "merge_weight_control_scale_0p9_max_abs": max(x["control_scale_0p9_max_abs"] for x in wchk),
    "merge_weight_control_scale_0p9_ratio": (max(x["control_scale_0p9_max_abs"] for x in wchk) /
                                             max(1e-12, max(x["max_abs"] for x in wchk))),
    "merge_weight_resolution_note": ("resolves deviations of order the adapter update (a dropped module "
                                     "separates by the measured ratio); does NOT resolve a 10 % mis-scaling, "
                                     "which is comparable to bf16 rounding of the merged sum"),
    # the separation the gate relies on: merged-vs-unmerged must be far closer than merged-vs-base
    "tf_negative_control_rows": len(nc),
    "tf_negative_control_positions": nc_positions,
    "tf_negative_control_agreement_rate": nc_rate,
    "tf_gate_separation": (tf_rate - nc_rate) if (nc_rate is not None) else None,
    "tf_logit_abs_mean": (sum(x["logit_abs_mean"] for x in tf) / len(tf)) if tf else None,
    # ---- reported, never gated: how far bf16 rounding is amplified by free-running greedy decoding
    "gen_exact_mismatches": sum(1 for m, u in zip(outs_m, outs_u) if m != u),
    "gen_self_f1_min": min(f1s) if f1s else None,
    "gen_self_f1_mean": (sum(f1s) / len(f1s)) if f1s else None,
    "gen_self_f1_median": (f1s_sorted[len(f1s_sorted) // 2] if f1s_sorted else None),
    "max_new_tokens": int(os.environ.get("MAX_NEW", 256)),
    "equivalence_basis": ("teacher-forced per-position top-1 agreement over the assistant span (the scored "
                          "surface): the token sequence is fixed, so it is not subject to decoding chaos and "
                          "it is sensitive to a change anywhere in the continuation. loss_delta is a second, "
                          "distributional line of evidence. Free-running generation statistics are reported "
                          "only, because they measure amplification rather than equivalence."),
    "wall_seconds": round(time.time() - t0, 1),
}
out = ROOT / "evals" / f"merge-equiv-{ADAPTER.name}.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
