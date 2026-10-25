#!/usr/bin/env python3
"""Public-benchmark comparison — implemented to the SUPERVISOR'S specification.

ROLE PROTOCOL (docs/ROLE-PROTOCOL.md): Astra designs and decides; this file is written by a RUNNER and
contains no design choices. Every parameter below is quoted from Astra's specification. Do not change one
without a new specification.

FROZEN SURFACE (Astra spec §2):
  greedy (do_sample=False, num_beams=1), ONE trial, 512 new tokens, batch 8, left padding with an explicit
  attention mask, BF16, no quantization, the v3 adapter loaded through PEFT WITHOUT merging, own
  tokenizer/template, one user message, no system message, zero demonstrations, no input truncation
  (every rendered prompt must fit 3,584 tokens inside a 4,096-token envelope), termination on the model's
  declared EOS or the 512-token cap.

POPULATION AND PARSING (Astra spec §3):
  CyberMetric-500 (500) and SecQA-v1-test (110): the existing INSTR + option construction.
      Scoring: the ENTIRE whitespace-trimmed response must match [ABCD].
  CTI-MCQ (2,500) and CTI-RCM (1,000): the dataset's own Prompt column, outer whitespace stripped.
      Scoring: the LAST nonempty, whitespace-trimmed line must match [ABCD] (MCQ) or CWE-[0-9]{1,5} (RCM).
  Matching is case-SENSITIVE. No Markdown removal, punctuation forgiveness, fallback regex search, semantic
  judging, or CWE-hierarchy credit. A returned but unparseable answer is INCORRECT and stays in the
  denominator. A cap-hit response is scored by the same parser and its cap-hit status recorded separately.
  Gold labels normalised with the existing strip().upper().

METRIC NAME (Astra spec §3): "strict format-constrained accuracy, local protocol".
  This is explicitly NOT the authors' `strict_acc`; parser equivalence has not been established.

POSITION BIAS (Astra spec §4): keep the original option order and unweighted accuracy; report the always-C
  baseline, the predicted A/B/C/D/unparseable counts, and accuracy conditional on each gold position.
  Do NOT subtract the baseline, rebalance, or shuffle options. Option-order robustness is UNMEASURED.

MODELS (Astra spec §5): exactly three, no fourth.
"""
import argparse, csv, hashlib, json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# --- frozen surface constants (Astra spec §2) -------------------------------------------------------
MAX_NEW = 512
EXPECTED_MAX_NEW = int(os.environ.get("PUBBENCH_EXPECT", "512"))  # supervisor-set effective budget
BATCH = 8
MAX_PROMPT_TOKENS = 3584           # 4096 envelope - 512 new tokens
ENVELOPE = 4096
METRIC_NAME = "strict format-constrained accuracy, local protocol"

MODELS = {
    "base":             ("<peer-home>/cyberguard/models/Qwen3-4B-Instruct-2507", None),
    "v3":               ("<peer-home>/cyberguard/models/Qwen3-4B-Instruct-2507",
                         "<peer-home>/cyberguard/adapters/cyberguard-lora-v3"),
    "cybersecqwen-4b":  ("athena129/CyberSecQwen-4B", None),
}
# Author-reported reference figures (Astra spec §6). NOT measured by us.
AUTHOR_REPORTED = {
    "cybersecqwen-4b/cti-mcq": {"value": 0.5868, "sd_pp": 0.29,
                                "label": "author-reported, five sampled trials, mean +/- standard deviation"},
    "cybersecqwen-4b/cti-rcm": {"value": 0.6664, "sd_pp": 0.23,
                                "label": "author-reported, five sampled trials, mean +/- standard deviation"},
}

INSTR = ("Answer the following multiple choice question. "
         "Reply with only the letter of the correct answer: A, B, C, or D.\n\n")


def _load_torch():
    global torch, AutoTokenizer, AutoModelForCausalLM, PeftModel
    import torch as _t
    from transformers import AutoTokenizer as _tok, AutoModelForCausalLM as _lm
    from peft import PeftModel as _pm
    torch, AutoTokenizer, AutoModelForCausalLM, PeftModel = _t, _tok, _lm, _pm


# --- parsing (Astra spec §3) ------------------------------------------------------------------------
_WHOLE_MCQ = re.compile(r"^[ABCD]$")
_LAST_MCQ = re.compile(r"^[ABCD]$")
_LAST_CWE = re.compile(r"^CWE-[0-9]{1,5}$")


def parse_whole_mcq(gen):
    """CyberMetric / SecQA: the ENTIRE trimmed response must be exactly one of A/B/C/D."""
    s = (gen or "").strip()
    return s if _WHOLE_MCQ.match(s) else "?"


def parse_last_line(gen, pattern):
    """CTI-MCQ / CTI-RCM: the LAST nonempty trimmed line must match the pattern. First-match is WRONG --
    the supervisor reproduced `A common weakness is present.\\nB` scoring as A instead of B."""
    for line in reversed([ln.strip() for ln in (gen or "").splitlines()]):
        if not line:
            continue
        return line if pattern.match(line) else "?"
    return "?"


def parse_reply(benchmark, gen):
    if benchmark in ("cybermetric-500", "secqa-v1-test"):
        return parse_whole_mcq(gen)
    if benchmark == "cti-mcq":
        return parse_last_line(gen, _LAST_MCQ)
    if benchmark == "cti-rcm":
        return parse_last_line(gen, _LAST_CWE)
    return "?"


# --- population (Astra spec §3) ---------------------------------------------------------------------
def _cti_dir():
    return Path(os.environ.get("PUBBENCH_CTI",
                               str(HERE.parent / "research-tmp" / "ctibench")))


def load_datasets(only=None):
    """[(benchmark, prompt, gold, row_number)] in original file row order, identical for every model."""
    items = []
    want = (lambda b: True) if not only else (lambda b: b in only)

    if want("cybermetric-500"):
        d = json.load(open(HERE / "cybermetric-500.json"))
        lst = d if isinstance(d, list) else d[list(d.keys())[0]]
        for i, q in enumerate(lst):
            opts = q["answers"]
            body = q["question"] + "\n" + "\n".join(f"{k}. {v}" for k, v in opts.items())
            items.append(("cybermetric-500", INSTR + body + "\n\nAnswer:",
                          q["solution"].strip().upper(), i))
    if want("secqa-v1-test"):
        with open(HERE / "secqa_test.csv") as f:
            for i, row in enumerate(csv.DictReader(f)):
                opts = {"A": row["A"], "B": row["B"], "C": row["C"], "D": row["D"]}
                body = row["Question"] + "\n" + "\n".join(f"{k}. {v}" for k, v in opts.items())
                items.append(("secqa-v1-test", INSTR + body + "\n\nAnswer:",
                              row["Answer"].strip().upper(), i))
    cti = _cti_dir()
    if want("cti-mcq") and (cti / "cti-mcq.tsv").exists():
        with open(cti / "cti-mcq.tsv", newline="", encoding="utf8", errors="replace") as f:
            for i, r in enumerate(csv.DictReader(f, delimiter="\t")):
                items.append(("cti-mcq", (r.get("Prompt") or "").strip(),
                              (r.get("GT") or "").strip().upper(), i))
    if want("cti-rcm") and (cti / "cti-rcm.tsv").exists():
        with open(cti / "cti-rcm.tsv", newline="", encoding="utf8", errors="replace") as f:
            for i, r in enumerate(csv.DictReader(f, delimiter="\t")):
                items.append(("cti-rcm", (r.get("Prompt") or "").strip(),
                              (r.get("GT") or "").strip().upper(), i))
    return items


BENCHMARKS = ("cybermetric-500", "secqa-v1-test", "cti-mcq", "cti-rcm")
EXPECTED_N = {"cybermetric-500": 500, "secqa-v1-test": 110, "cti-mcq": 2500, "cti-rcm": 1000}


def wilson(k, n, upper=False):
    if not n:
        return None
    import math
    z, p = 1.959963985, k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round(max(0.0, (c - h) / d) if not upper else min(1.0, (c + h) / d), 4)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _tok_for(base_path):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(base_path, trust_remote_code=True)
    tok.padding_side = "left"                       # Astra spec §2: left padding, explicit mask
    if tok.pad_token_id is None and tok.eos_token is not None:
        tok.pad_token = tok.eos_token
    return tok


def resolve_identity(path_or_repo):
    """Resolve and record an immutable revision (Astra spec §5)."""
    p = Path(path_or_repo)
    if p.exists():
        return {"kind": "local_path", "path": str(p),
                "config_sha256": sha256(p / "config.json") if (p / "config.json").is_file() else None}
    from huggingface_hub import HfApi
    info = HfApi().model_info(path_or_repo)
    return {"kind": "hub", "repo": path_or_repo, "revision": info.sha}


# --- generation -------------------------------------------------------------------------------------
def run_model(tag, items, max_new=MAX_NEW, batch=BATCH):
    _load_torch()
    base_path, adapter = MODELS[tag]
    print(f"[{tag}] loading {base_path}" + (f" + {adapter}" if adapter else ""), flush=True)
    model = AutoModelForCausalLM.from_pretrained(base_path, trust_remote_code=True,
                                                 torch_dtype=torch.bfloat16, device_map="cuda")
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)   # Astra spec: WITHOUT merging
    model.eval()
    tok = _tok_for(base_path)
    eos_ids = tok.eos_token_id
    eos_set = set(eos_ids) if isinstance(eos_ids, (list, tuple)) else ({eos_ids} if eos_ids is not None else set())

    out, t0 = [], time.time()
    for i in range(0, len(items), batch):
        chunk = items[i:i + batch]
        rendered = [tok.apply_chat_template([{"role": "user", "content": pr}], tokenize=False,
                                            add_generation_prompt=True) for _b, pr, _g, _r in chunk]
        enc = tok(rendered, return_tensors="pt", padding=True, add_special_tokens=False,
                  truncation=False).to(model.device)          # Astra spec: NO input truncation
        # RUNTIME ASSERTION (supervisor requirement): proving the effective budget reaches the actual
        # generate call. A CLI flag alone is not proof. Recorded per model into the protocol artifact.
        assert isinstance(max_new, int) and max_new == EXPECTED_MAX_NEW, \
            f"effective max_new_tokens {max_new!r} != expected {EXPECTED_MAX_NEW}"
        if i == 0:
            print(f"[{tag}] RUNTIME CONFIRM: generate(max_new_tokens={max_new})", flush=True)
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=max_new, do_sample=False, num_beams=1,
                                 repetition_penalty=1.0,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
        plen = enc.input_ids.shape[1]
        for j, (bm, _pr, gold, rowno) in enumerate(chunk):
            seq = gen[j][plen:]
            n_gen = int(seq.shape[0])
            toks = seq.tolist()
            cap_hit = n_gen >= max_new
            eos_hit = bool(toks) and (toks[-1] in eos_set)
            text = tok.decode(seq, skip_special_tokens=True)   # whole response preserved
            pred = parse_reply(bm, text)
            out.append({"benchmark": bm, "row": rowno, "gold": gold, "prediction": pred,
                        "correct": pred == gold, "response": text,
                        "generated_tokens": n_gen,
                        "termination": "cap" if cap_hit else ("eos" if eos_hit else "stop")})
        if (i + batch) % 400 < batch:
            print(f"[{tag}] {min(i+batch, len(items))}/{len(items)}", flush=True)
    print(f"[{tag}] done ({round((time.time()-t0)/60,1)} min)", flush=True)
    del model
    torch.cuda.empty_cache()
    return out


def summarize(per_model, items):
    """Astra spec §6: one row per model x benchmark, with the required fields."""
    base_by = {f"{r['benchmark']}#{r['row']}": r["correct"] for r in per_model.get("base", [])}
    rows = []
    for tag in per_model:
        for bm in BENCHMARKS:
            sub = [r for r in per_model[tag] if r["benchmark"] == bm]
            if not sub:
                continue
            n = len(sub)
            k = sum(1 for r in sub if r["correct"])
            unp = sum(1 for r in sub if r["prediction"] == "?")
            # TERMINATION WITHDRAWN (supervisor decision, option (c)). The old detector read
            # seq.shape[0] from a rectangular [batch, plen+max_gen] tensor, so it reported the BATCH's
            # maximum generated length for every item, and early-EOS items (padded with pad_token) were
            # labelled cap hits; the supervisor reproduced a counterexample. Per the decision: cap_hits
            # and cap_hit_rate are removed from every row; stored generated_tokens and termination are
            # INVALID and must not be used for summaries, filtering or interpretation; termination is
            # UNMEASURED and is NOT inferred from response text. The fields stay in the artifact for
            # provenance only.
            ALWAYS = sum(1 for r in sub if r["gold"] == "C")  # only meaningful on cti-mcq
            predmix = {}
            for r in sub:
                predmix[r["prediction"]] = predmix.get(r["prediction"], 0) + 1
            bygold = {}
            for g in sorted({r["gold"] for r in sub}):
                gg = [r for r in sub if r["gold"] == g]
                cg = sum(1 for r in gg if r["correct"])
                bygold[g] = {"n": len(gg), "correct": cg, "accuracy": round(cg / len(gg), 4)}
            paired, paired_n, paired_complete = None, 0, None
            if tag != "base" and base_by:
                diffs = [(1 if r["correct"] else 0) - (1 if base_by.get(f"{bm}#{r['row']}") else 0)
                         for r in sub if f"{bm}#{r['row']}" in base_by]
                paired_n = len(diffs)
                # Astra: a partial intersection silently produced a paired figure from whatever few rows
                # matched -- an executed counterexample gave +100 pp from ONE paired item on N=2. Report
                # the paired n and flag incomplete support instead of publishing the number bare.
                paired_complete = (paired_n == n)
                if diffs:
                    paired = round(sum(diffs) / len(diffs) * 100, 2)
            rows.append({"model": tag, "benchmark": bm, "n": n, "correct": k,
                         "accuracy": round(k / n, 4), "wilson95": [wilson(k, n), wilson(k, n, True)],
                         "unparseable": unp, "unparseable_rate": round(unp / n, 4),
                         "always_c_baseline": (round(ALWAYS / n, 4) if bm == "cti-mcq" else None),
                         "termination": "UNMEASURED",
                         "paired_pp_vs_base": paired, "paired_n": paired_n,
                         "paired_support_complete": paired_complete, "prediction_mix": predmix,
                         "accuracy_by_gold": bygold, "metric": METRIC_NAME})
    return rows


# --- modes (Astra spec §7) --------------------------------------------------------------------------
def check():
    """Nonzero on: missing datasets, count mismatch, invalid gold, missing model identity, or any rendered
    prompt exceeding 3,584 tokens (Astra spec §7)."""
    bad = 0
    items = load_datasets()
    per = {}
    for bm, _p, _g, _r in items:
        per[bm] = per.get(bm, 0) + 1
    print(f"  population: {json.dumps(per)}  total={len(items)}")
    for bm, exp in EXPECTED_N.items():
        got = per.get(bm, 0)
        if got != exp:
            print(f"  FAIL count {bm}: {got} != {exp}"); bad = 1
    valid = {"cybermetric-500": {"A", "B", "C", "D"}, "secqa-v1-test": {"A", "B", "C", "D"},
             "cti-mcq": {"A", "B", "C", "D"}}
    for bm, _p, g, r in items:
        ok = (re.fullmatch(r"CWE-[0-9]{1,5}", g) is not None) if bm == "cti-rcm" else (g in valid[bm])
        if not ok:
            print(f"  FAIL invalid gold {bm} row {r}: {g!r}"); bad = 1
    try:
        tok = _tok_for(MODELS["base"][0])
        worst = {}
        for bm, pr, _g, _r in items:
            t = tok.apply_chat_template([{"role": "user", "content": pr}], tokenize=False,
                                        add_generation_prompt=True)
            n = len(tok(t, add_special_tokens=False)["input_ids"])
            if n > worst.get(bm, 0):
                worst[bm] = n
        print(f"  longest rendered prompt per benchmark: {worst}")
        for bm, n in worst.items():
            if n > MAX_PROMPT_TOKENS:
                print(f"  FAIL prompt too long {bm}: {n} > {MAX_PROMPT_TOKENS}"); bad = 1
    except Exception as e:
        print(f"  FAIL tokenizer unavailable: {type(e).__name__}: {e}"); bad = 1
    for tag, (b, a) in MODELS.items():
        try:
            ident = resolve_identity(b)
            have = (a is None) or (Path(a) / "adapter_model.safetensors").is_file()
            print(f"  model {tag:<18} {ident.get('kind')} adapter={'n/a' if a is None else have}")
            if not have:
                print(f"  FAIL adapter weights missing for {tag}"); bad = 1
        except Exception as e:
            print(f"  FAIL model identity {tag}: {type(e).__name__}: {e}"); bad = 1
    print("  CHECK: FAIL" if bad else "  CHECK: PASS")
    return 1 if bad else 0


def self_test():
    """Both supervisor-reported failures must be corrected; strict-format rejection must hold."""
    cases = [
        ("cti-mcq", "A common weakness is present.\nB", "B"),
        ("cti-rcm", "Consider CWE-79, but the correct classification is:\nCWE-89", "CWE-89"),
        ("cti-mcq", "B", "B"),
        ("cybermetric-500", "B", "B"),
        ("cybermetric-500", "The answer is B", "?"),
        ("secqa-v1-test", " A \n", "A"),
        ("cti-mcq", "A\n\nB\n", "B"),
        ("cti-mcq", "", "?"),
        ("cti-rcm", "CWE-79\nCWE-89", "CWE-89"),
        ("cti-rcm", "cwe-89", "?"),
        ("cti-mcq", "E", "?"),
    ]
    bad = 0
    for bm, gen, want in cases:
        got = parse_reply(bm, gen)
        ok = got == want
        bad |= (0 if ok else 1)
        print(f"  {'OK  ' if ok else 'FAIL'} {bm:<16} {gen!r:>52} -> {got!r} (want {want!r})")
    print("  SELF-TEST: FAIL" if bad else "  SELF-TEST: PASS")
    return 1 if bad else 0


def verify_results(path):
    """Independently reparse every full response and verify identical support across models."""
    d = json.load(open(path))
    per_model = {tag: v["responses"] for tag, v in d["models"].items()}
    bad = 0
    # Astra: the old verifier returned PASS for EMPTY response arrays, because it only checked that the
    # models agreed with each other. An empty population is now a failure.
    if not per_model:
        print("  FAIL no models in the results file"); return 1
    for tag, rows in per_model.items():
        if not rows:
            print(f"  FAIL {tag} has zero responses"); bad = 1
    keysets = {}
    for tag, rows in per_model.items():
        for r in rows:
            want = parse_reply(r["benchmark"], r["response"])
            if want != r["prediction"]:
                print(f"  FAIL reparse {tag} {r['benchmark']}#{r['row']}: {r['prediction']} -> {want}")
                bad = 1
            if r["correct"] != (r["prediction"] == r["gold"]):
                print(f"  FAIL correctness {tag} {r['benchmark']}#{r['row']}"); bad = 1
        keysets[tag] = sorted(f"{r['benchmark']}#{r['row']}" for r in rows)
    base_keys = keysets.get("base")
    for tag, ks in keysets.items():
        if base_keys is not None and ks != base_keys:
            print(f"  FAIL support differs: {tag} has {len(ks)} vs base {len(base_keys)}"); bad = 1
    print("  VERIFY: FAIL" if bad else "  VERIFY: PASS")
    return 1 if bad else 0


# --- Astra spec §6: the required comparison artifact -------------------------------------------------
CONTAMINATION = {
    "cti-rcm": ("Repository audit (docs/V3-EVAL-FINAL-RESULTS.md) reports 56 CTI-RCM near-matches "
                "(5.61%); that audit has NOT been independently verified. Full RCM population retained."),
    "cti-mcq": "Gold labels are position-biased (C=37.12%); always-C baseline shown.",
}


def write_comparison(path_json, out_md):
    d = json.load(open(path_json))
    rows = d["comparison"]
    order = ["cybermetric-500", "secqa-v1-test", "cti-mcq", "cti-rcm"]
    by = {(r["model"], r["benchmark"]): r for r in rows}
    models = [m for m in ("base", "v3", "cybersecqwen-4b") if any(k[0] == m for k in by)]
    L = []
    L.append("# Public-benchmark comparison — CyberGuard v3 vs base vs CyberSecQwen-4B\n")
    _surf = (d.get("protocol") or {}).get("surface") or {}
    _mn = _surf.get("max_new_tokens", "UNKNOWN")
    _bt = _surf.get("batch", "UNKNOWN")
    L.append(f"Metric: **{d['metric']}**. One frozen decode surface for every model: greedy "
             "(`do_sample=False`, `num_beams=1`), one trial, "
             f"{_mn} new tokens, batch {_bt}, left padding, "
             "bfloat16, no quantization, v3 adapter loaded via PEFT without merging, no input "
             "truncation, each model's own tokenizer/template, zero demonstrations.\n")
    _pop = (d.get("protocol") or {}).get("population") or {}
    _tot = sum(_pop.values()) if _pop else None
    L.append("Populations: " + (", ".join(f"{k} {v}" for k, v in _pop.items()) if _pop else "UNKNOWN")
             + (f" ({_tot} items per model)." if _tot else "") + "\n")
    L.append("## Measured (this run)\n")
    L.append("| model | benchmark | N | correct | accuracy | Always-C baseline | Wilson 95% | "
             "unparseable | paired pp vs base | contamination caveat |")
    L.append("|---|---|---:|---:|---:|---|---:|---:|---:|---|")
    for m in models:
        for bm in order:
            r = by.get((m, bm))
            if not r:
                continue
            unp = f"{r['unparseable']} ({r['unparseable_rate']:.1%})"
            ac = r.get("always_c_baseline")
            acs = "N/A" if ac is None else f"{ac:.2%} (928/2,500)"
            pa = "—" if r["paired_pp_vs_base"] is None else f"{r['paired_pp_vs_base']:+.2f}"
            L.append(f"| {m} | {bm} | {r['n']} | {r['correct']} | {r['accuracy']:.4f} | {acs} | "
                     f"[{r['wilson95'][0]:.4f}, {r['wilson95'][1]:.4f}] | {unp} | {pa} | "
                     f"{CONTAMINATION.get(bm, '')} |")
    L.append("\n**Termination and per-item generated-token counts: UNMEASURED.** The original detector "
             "counted batch padding; its termination labels and cap-hit statistics are withdrawn.")
    L.append("\n### Selected-subset diagnostic: accuracy among PARSEABLE replies\n")
    L.append("Not a format-free measure -- each model selects a different parseable subset.\n")
    L.append("| model | benchmark | parseable | correct | accuracy among parseable |")
    L.append("|---|---|---:|---:|---:|")
    for m in models:
        for bm in order:
            r = by.get((m, bm))
            if not r:
                continue
            par = r["n"] - r["unparseable"]
            if par:
                L.append(f"| {m} | {bm} | {par} | {r['correct']} | {r['correct']/par:.2%} |")
    L.append("\n### CTI-MCQ position bias (Astra spec §4)\n")
    L.append("| model | predicted counts (A/B/C/D/unparseable) | accuracy by gold position |")
    L.append("|---|---|---|")
    for m in models:
        r = by.get((m, "cti-mcq"))
        if not r:
            continue
        mix = r["prediction_mix"]
        mixs = " / ".join(str(mix.get(k, 0)) for k in ("A", "B", "C", "D", "?"))
        gold = ", ".join(f"{g}: {v['accuracy']:.3f} (n={v['n']})"
                         for g, v in sorted(r["accuracy_by_gold"].items()))
        L.append(f"| {m} | {mixs} | {gold} |")
    L.append("\nAlways-C baseline on CTI-MCQ = **37.12%** (928/2,500). Option-order robustness: "
             "**UNMEASURED**. The label imbalance alone does not establish how much any model's accuracy "
             "is inflated, and no baseline is subtracted.\n")
    L.append("## Author-reported reference (NOT measured by us)\n")
    L.append("| model | benchmark | value | label |")
    L.append("|---|---|---:|---|")
    for k, v in (d.get("author_reported_reference") or {}).items():
        if "/" in k:
            m, bm = k.split("/", 1)
            L.append(f"| {m} | {bm} | {v['value']:.4f} ± {v['sd_pp']} pp | {v['label']} |")
    L.append("\nOur run is one greedy trial; it is **not** a reproduction of those five sampled trials, "
             "and the metric here is **not** the authors' `strict_acc` — parser equivalence has not been "
             "established.\n")
    L.append("## Standing caveats\n")
    L.append("- No pooled four-benchmark \"overall winner\" is reported, and no significance claim is made "
             "from overlapping or non-overlapping marginal Wilson intervals.")
    L.append("- These accuracy results do not satisfy the registered §8.6 loss / token-F1 requirements; "
             "accuracy does not silently replace that metric.")
    L.append("- Always-C is reported beside every CTI-MCQ accuracy; the baseline is not subtracted.\n")
    L.append(f"Artifacts: `protocol-v3-public.json`, `results-v3-public.json` "
             f"({len(rows)} measured rows).\n")
    open(out_md, "w").write("\n".join(L))
    print(f"wrote {out_md}")
    return 0


def main():
    global BATCH, EXPECTED_MAX_NEW
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="base,v3,cybersecqwen-4b")
    ap.add_argument("--datasets", default="")
    ap.add_argument("--bias", action="store_true", help="report the always-C baseline and prediction mix")
    ap.add_argument("--max-new", type=int, default=MAX_NEW)
    ap.add_argument("--batch", type=int, default=BATCH)
    args = ap.parse_args()

    EXPECTED_MAX_NEW = args.max_new    # the runtime assertion checks the value reaching generate()
    only = [d for d in args.datasets.split(",") if d] or None
    items = load_datasets(only)
    tags = [t for t in args.models.split(",") if t]
    for t in tags:
        if t not in MODELS:
            print(f"unknown model tag {t!r}"); return 2

    protocol = {
        "metric": METRIC_NAME,
        "surface": {"decoding": "greedy, do_sample=False, num_beams=1", "trials": 1,
                    "max_new_tokens": args.max_new, "batch": args.batch,
                    "padding": "left + attention mask", "precision": "bfloat16",
                    "quantization": "none", "adapter": "peft, not merged", "input_truncation": False,
                    "max_prompt_tokens": MAX_PROMPT_TOKENS, "envelope": ENVELOPE,
                    "penalties": "repetition_penalty=1.0",
                    "chat": "own tokenizer/template, 1 user message, no system, 0-shot"},
        "population": {bm: sum(1 for i in items if i[0] == bm) for bm in BENCHMARKS},
        "expected_n": EXPECTED_N,
        "inputs_sha256": {str(p): sha256(p) for p in
                          [HERE / "cybermetric-500.json", HERE / "secqa_test.csv",
                           _cti_dir() / "cti-mcq.tsv", _cti_dir() / "cti-rcm.tsv"] if p.exists()},
        "models": {t: {"base": MODELS[t][0], "adapter": MODELS[t][1]} for t in tags},
        "author_reported_reference": AUTHOR_REPORTED,
        "option_order_robustness": "UNMEASURED",
    }
    for t in tags:
        try:
            protocol["models"][t]["identity"] = resolve_identity(MODELS[t][0])
        except Exception as e:
            protocol["models"][t]["identity"] = {"error": f"{type(e).__name__}: {e}"}
    json.dump(protocol, open(HERE / "protocol-v3-public.json", "w"), indent=1)
    print(f"protocol written; population={protocol['population']}", flush=True)

    per_model = {}
    for t in tags:
        per_model[t] = run_model(t, items, args.max_new, args.batch)

    if args.bias:
        import collections
        c = collections.Counter(i[2] for i in items if i[0] == "cti-mcq")
        tot = sum(c.values())
        mode, cnt = c.most_common(1)[0]
        print(f"always-{mode} baseline on cti-mcq = {cnt}/{tot} = {round(cnt/tot,4)}", flush=True)

    rows = summarize(per_model, items)
    json.dump({"metric": METRIC_NAME, "protocol": protocol, "comparison": rows,
               "models": {t: {"responses": per_model[t]} for t in tags},
               "author_reported_reference": AUTHOR_REPORTED},
              open(HERE / "results-v3-public.json", "w"), indent=1)
    print("COMPARISON:", json.dumps(rows, indent=1), flush=True)


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if "--write-comparison" in sys.argv:
        i = sys.argv.index("--write-comparison")
        sys.exit(write_comparison(sys.argv[i + 1], sys.argv[i + 2] if len(sys.argv) > i + 2
                                  else str(HERE / "comparison-v3-public.md")))
    if "--verify-results" in sys.argv:
        i = sys.argv.index("--verify-results")
        sys.exit(verify_results(sys.argv[i + 1]))
    main()
