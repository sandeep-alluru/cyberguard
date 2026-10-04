#!/usr/bin/env python3
"""Build the CyberGuard v3 training mixture (no-trail branch) + §5.3 receipt.

Stage policy — set by measurement, see PLAN-V3 §2 pre-flight and
docs/evidence/mixture-build-stage-policy.txt:

  * The three public corpora (fenrir / merged / primus) enter EXACTLY AS PREPPED.
    No near-duplicate collapse, no near-holdout removal, no boundary/defect
    dropping, no answer clipping — role-mapping from `messages` to the flat
    `{system?, user, assistant}` shape the trainer's ARM mode reads. Reason: v2's
    prompt-level 0.80 collapse removes 14,989/23,146 (64.8 %) of `merged`, because
    its prompts share a CVE-analysis template while the CVEs underneath differ.
  * The authored/reused sets go through the v2 mechanism, which reproduces all
    three pinned FACTS numbers exactly: refusal dedupe 1,200 -> 1,198;
    format dedupe 1,300 -> 1,300; replay finalise 600 -> 594.
  * Weights are realised by literal duplication: refusal x8, format x2, rest x1.
  * Any deviation from the expected per-source counts FAILS the build; it is never
    a silent adjustment.

Outputs
  --out        the mixture (default data/v3/mixture/mixture-v3-no-trail.jsonl)
  --receipt    counts + §5.3 supervision-survival statistics (JSON)
  --stats-md   human-readable §5.3 report
"""
import argparse
import importlib.util as ilu
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "data/v3")
SUP = os.path.expanduser("~/AgentHub/cyberguard/data/v3/trails-30/supervisor")

CORPORA = [("fenrir", os.path.join(BASE, "sft/fenrir.jsonl"), 99730),
           ("merged", os.path.join(BASE, "sft/merged.jsonl"), 23146),
           ("primus", os.path.join(BASE, "sft/primus.jsonl"), 4891)]
REFUSAL = os.path.join(REPO, "v2/data/refusal-retention.jsonl")
FORMAT = os.path.join(REPO, "v2/data/format-compliance.jsonl")
REPLAY = os.path.join(REPO, "v2/candidates/ultrachat-pairs.jsonl")
TOKENIZER = os.path.join(REPO, "v2/tokenizer")
MAX_SEQ = 2048
WEIGHTS = {"refusal": 8, "format": 2}
EXPECT = {"fenrir": 99730, "merged": 23146, "primus": 4891,
          "refusal": 1198, "format": 1300, "replay": 594}
EXPECT_TOTAL = 99730 + 23146 + 4891 + 1198 * 8 + 1300 * 2 + 594


def log(m):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), m), flush=True)


def load_v2():
    spec = ilu.spec_from_file_location("bm", os.path.join(REPO, "v2/build_mixture.py"))
    bm = ilu.module_from_spec(spec)
    try:
        spec.loader.exec_module(bm)
    except SystemExit:
        pass
    return bm


def flatten(row, src):
    """`messages` -> flat {system,user,assistant}. Corpora are otherwise untouched."""
    system = user = assistant = ""
    for m in row.get("messages") or []:
        role = m.get("role")
        if role == "system" and not system:
            system = m.get("content") or ""
        elif role == "user" and not user:
            user = m.get("content") or ""
        elif role == "assistant" and not assistant:
            assistant = m.get("content") or ""
    return {"system": system, "user": user, "assistant": assistant, "src": src}


def read_flat(path, src):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(flatten(json.loads(line), src))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(BASE, "mixture/mixture-v3-no-trail.jsonl"))
    ap.add_argument("--receipt", default=os.path.join(BASE, "mixture/MIXTURE-V3-RECEIPT.json"))
    ap.add_argument("--stats-md", default=os.path.join(BASE, "mixture/MIXTURE-V3-STATS.md"))
    ap.add_argument("--skip-stats", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    bm = load_v2()
    pools = {}

    for src, path, expect in CORPORA:
        rows = read_flat(path, src)
        if len(rows) != expect:
            sys.exit("FATAL %s: %d rows, expected %d — corpora must enter as prepped"
                     % (src, len(rows), expect))
        pools[src] = rows
        log("corpus %-8s %6d rows (as prepped, no stages)" % (src, len(rows)))

    ref = [{"system": (d.get("system") or ""), "user": d["user"], "assistant": d["assistant"],
            "src": "refusal"} for d in (json.loads(l) for l in open(REFUSAL) if l.strip())
           if d.get("user") and d.get("assistant")]
    ref, de, dn = bm.dedupe(ref, key="user")
    log("refusal  %6d rows (dedupe: exact %d, near %d)" % (len(ref), de, dn))
    pools["refusal"] = ref

    fmt = [{"system": (d.get("system") or ""), "user": d["user"], "assistant": d["assistant"],
            "src": "format"} for d in (json.loads(l) for l in open(FORMAT) if l.strip())
           if d.get("user") and d.get("assistant")]
    fmt, de, dn = bm.dedupe(fmt, key="user")
    log("format   %6d rows (dedupe: exact %d, near %d)" % (len(fmt), de, dn))
    pools["format"] = fmt

    rep, kept = [], 0
    for d in (json.loads(l) for l in open(REPLAY) if l.strip()):
        a = d.get("assistant") or ""
        try:
            _, good = bm.finalise(a, "replay")
        except Exception:
            good = False
        if good:
            rep.append({"system": "", "user": d.get("user") or "", "assistant": a, "src": "replay"})
            kept += 1
    log("replay   %6d rows (finalise kept %d of 600)" % (len(rep), kept))
    pools["replay"] = rep

    for k, v in EXPECT.items():
        if len(pools[k]) != v:
            sys.exit("FATAL %s: %d rows, expected %d — refusing to write a mixture whose "
                     "per-source counts drifted" % (k, len(pools[k]), v))

    order = ["fenrir", "merged", "primus", "refusal", "format", "replay"]
    allrows = []
    per_src = {}
    for src in order:
        w = WEIGHTS.get(src, 1)
        block = pools[src] * w
        allrows.extend(block)
        per_src[src] = {"unique": len(pools[src]), "weight": w, "presentations": len(block)}
        log("staged %-8s unique=%-6d x%-2d = %d" % (src, len(pools[src]), w, len(block)))
    total = len(allrows)
    if total != EXPECT_TOTAL:
        sys.exit("FATAL total %d != expected %d" % (total, EXPECT_TOTAL))

    # v2 shuffles before writing (`rng.shuffle(armA)` in v2/build_mixture.py); the trainer
    # consumes the arm file VERBATIM IN ORDER, so writing source-grouped blocks would make
    # batches source-homogeneous (e.g. ~9,584 consecutive refusal rows). Shuffle with a
    # pinned seed so the order is reproducible.
    import random as _random
    rng = _random.Random(args.seed)
    rng.shuffle(allrows)
    with open(args.out, "w") as f:
        for r in allrows:
            f.write(json.dumps(r) + "\n")
    log("mixture written: %d presentations (shuffled, seed=%d) -> %s"
        % (total, args.seed, args.out))

    receipt = {"at": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "mixture": args.out,
               "total_presentations": total, "expected_total": EXPECT_TOTAL, "shuffle_seed": args.seed,
               "per_source": per_src,
               "stage_policy": {
                   "corpora": "as prepped; messages->flat role mapping only; no dedupe/clip/drop",
                   "refusal": "v2 dedupe(key=user) -> 1198", "format": "v2 dedupe(key=user) -> 1300",
                   "replay": "v2 finalise() -> 594", "weights": "literal duplication x8/x2/x1",
                   "order": "shuffled with a pinned seed (v2 shuffles before writing; the trainer consumes in order)"}}

    if not args.skip_stats:
        log("computing §5.3 supervision-survival statistics (local tokenizer)…")
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(TOKENIZER)

        def span(msgs):
            full = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
            pref = tok.apply_chat_template(msgs[:-1], tokenize=False, add_generation_prompt=True)
            n_full = len(tok(full, add_special_tokens=False).input_ids)
            n_pref = len(tok(pref, add_special_tokens=False).input_ids)
            return n_full, n_pref

        stats = {}
        rows = 0
        with open(args.out) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows += 1
                r = json.loads(line)
                msgs = []
                if r.get("system"):
                    msgs.append({"role": "system", "content": r["system"]})
                msgs.append({"role": "user", "content": r["user"]})
                msgs.append({"role": "assistant", "content": r["assistant"]})
                n_full, n_pref = span(msgs)
                a_tok = max(0, n_full - n_pref)
                kept_a = max(0, min(n_full, MAX_SEQ) - n_pref)
                s = stats.setdefault(r["src"], {"rows": 0, "full": 0, "a_tok": 0, "kept_a": 0,
                                                "trunc": 0, "zero_sup": 0, "lens": []})
                s["rows"] += 1
                s["full"] += n_full
                s["a_tok"] += a_tok
                s["kept_a"] += kept_a
                s["lens"].append(n_full)
                if n_full > MAX_SEQ:
                    s["trunc"] += 1
                if kept_a == 0:
                    s["zero_sup"] += 1

        def agg(items):
            rows_ = sum(s["rows"] for s in items)
            a = sum(s["a_tok"] for s in items)
            k = sum(s["kept_a"] for s in items)
            tr = sum(s["trunc"] for s in items)
            z = sum(s["zero_sup"] for s in items)
            lens = sorted(x for s in items for x in s["lens"])
            return {"rows": rows_, "assistant_token_retention": round(k / a, 4) if a else None,
                    "truncated_rows_pct": round(100 * tr / rows_, 2) if rows_ else None,
                    "zero_supervision_pct": round(100 * z / rows_, 2) if rows_ else None,
                    "length_median": lens[len(lens) // 2] if lens else None,
                    "length_p99": lens[int(len(lens) * 0.99)] if lens else None,
                    "length_max": lens[-1] if lens else None}

        overall = agg(list(stats.values()))
        per = {k: agg([v]) for k, v in stats.items()}
        bounds = {"S1_zero_supervision_max_pct": 0.5, "S2_retention_min": 0.90,
                  "S3_truncated_max_pct": 10.0}
        verdicts = {
            "S1": overall["zero_supervision_pct"] <= bounds["S1_zero_supervision_max_pct"],
            "S2": overall["assistant_token_retention"] >= bounds["S2_retention_min"],
            "S3": overall["truncated_rows_pct"] <= bounds["S3_truncated_max_pct"],
            "S4_per_stream": all(
                p["zero_supervision_pct"] <= bounds["S1_zero_supervision_max_pct"]
                and p["assistant_token_retention"] >= bounds["S2_retention_min"]
                and p["truncated_rows_pct"] <= bounds["S3_truncated_max_pct"] for p in per.values()),
            "S5_trail_integrity": "n/a — no trail stream in the no-trail build",
        }
        receipt["s53"] = {"max_seq": MAX_SEQ, "bounds": bounds, "overall": overall,
                          "per_stream": per, "verdicts": {k: (v if isinstance(v, str) else bool(v))
                                                          for k, v in verdicts.items()},
                          "pass": all(v for v in verdicts.values() if isinstance(v, bool))}
        log("§5.3: retention=%s truncated=%s%% zero_sup=%s%% -> %s"
            % (overall["assistant_token_retention"], overall["truncated_rows_pct"],
               overall["zero_supervision_pct"], "PASS" if receipt["s53"]["pass"] else "FAIL"))

        with open(args.stats_md, "w") as f:
            f.write("# MIXTURE-V3 §5.3 supervision survival\n\n")
            f.write("Build: %s · rows %d · max_seq %d\n\n" % (receipt["at"], rows, MAX_SEQ))
            f.write("| stream | rows | retention | truncated %% | zero-sup %% | median len | p99 | max |\n")
            f.write("|---|---|---|---|---|---|---|---|\n")
            for k, p in sorted(per.items()):
                f.write("| %s | %d | %s | %s | %s | %s | %s | %s |\n"
                        % (k, p["rows"], p["assistant_token_retention"], p["truncated_rows_pct"],
                           p["zero_supervision_pct"], p["length_median"], p["length_p99"],
                           p["length_max"]))
            f.write("| **all** | %d | %s | %s | %s | %s | %s | %s |\n"
                    % (overall["rows"], overall["assistant_token_retention"],
                       overall["truncated_rows_pct"], overall["zero_supervision_pct"],
                       overall["length_median"], overall["length_p99"], overall["length_max"]))
            f.write("\nVerdicts: %s\n" % json.dumps(receipt["s53"]["verdicts"], indent=2))

    with open(args.receipt, "w") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    log("receipt -> %s" % args.receipt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
