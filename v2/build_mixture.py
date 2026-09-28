#!/usr/bin/env python3
"""build_mixture.py — assemble the v2 training corpora (Arm A and its control, Arm B).

The problem this solves: NIST, ATT&CK, NVD and arcspan are *documents*, not conversations. Under
`assistant_only_loss=True` a document with no assistant turn contributes ZERO supervised tokens, so
adding them as raw text would change the mixture on paper and nothing in training. Each document is
therefore converted into an instruction/response pair, with the source text as the RESPONSE — which is
both honest and exactly the grounding behaviour v2 wants.

Sampling weights are realised by **explicit duplication** so the realised presentation counts are
inspectable rather than implicit in a sampler, and the receipt states them.

Arm A: the designed mixture.  Arm B: identical, except the refusal rows are REPLACED IN PLACE by
matched non-refusal defensive Q&A rows (same count, same weight) so size, weights, batch boundaries and
steps match and only the content of those 1,200 slots differs.

Usage:  python3 v2/build_mixture.py --outdir v2/data/mixture [--target-weighted 103000]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_refusal_set as BRS  # noqa: E402  (family defence bodies + verb/noun tables)

CORPUS = os.environ.get(
    "CYBERGUARD_CORPUS",
    os.path.expanduser("~/cyberguard/data/trendyol-cybersec/CyberSec-Dataset_escaped.jsonl"))

WEIGHTS = {"trendyol": 1.0, "nist": 1.0, "attack": 1.0, "nvd": 1.0,
           "refusal": 8.0, "format": 2.0, "arcspan": 1.0, "replay": 1.0}
CAPS = {"trendyol": 52000, "nist": 20000, "attack": 20000, "nvd": 15000,
        "format": 1500, "arcspan": 800, "replay": 3000}

QUESTION_TEMPLATES = [
    "Explain {topic} and what defenders should do about it.",
    "Summarise {topic} for a security analyst.",
    "What does the guidance say about {topic}?",
    "Give me the defensive essentials of {topic}.",
    "Brief me on {topic}.",
]

UNESCAPE = [(chr(92) + "n", "\n"), (chr(92) + "t", "\t"), (chr(92) + "r", "\r"), (chr(92) + '"', '"')]



# ---------------------------------------------------------------- split discipline (added after audit)

def _norm(s):
    return " ".join(str(s).lower().split())


def _shingles(s, k=5):
    w = re.findall(r"[a-z0-9]+", str(s).lower())
    return {tuple(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}


def load_holdout_prompts():
    """The 500 held-out prompts AND their shingle index.

    Exact matches are not enough: the corpus is templated, so a training prompt can be 80 %+ similar to
    a held-out prompt without being identical. The audit found 3 such rows after exact exclusion, so the
    exclusion is extended to the same 0.80 Jaccard the split discipline uses.
    """
    exact, sh, index = set(), [], {}
    for d in read_jsonl("v2/holdout500.jsonl"):
        pr = d.get("prompt")
        if not pr:
            continue
        exact.add(_norm(pr))
        s = _shingles(pr)
        idx = len(sh)
        sh.append(s)
        for x in s:
            index.setdefault(x, []).append(idx)
    return exact, sh, index


def near_holdout(user, hold_index):
    """True when the prompt is >= 0.80 Jaccard with any held-out prompt."""
    exact, sh, index = hold_index
    if _norm(user) in exact:
        return True
    s = _shingles(user)
    if not s:
        return False
    cand = {}
    for x in s:
        for i in index.get(x, ()):
            cand[i] = cand.get(i, 0) + 1
    for i, shared in cand.items():
        h = sh[i]
        if h and shared >= max(2, len(s) * 0.25) and len(s & h) / len(s | h) >= 0.80:
            return True
    return False


def dedupe(rows, key="user"):
    """Prompt-level dedupe + 0.80 near-duplicate collapse, the discipline cyberguard_data enforces.

    The audit found 3,525 repeated prompts and 492 rows whose prompt IS a held-out prompt; both are
    data defects that would have been discovered mid-run. First occurrence wins.
    """
    seen_prompt, kept, kept_sh, index = set(), [], [], {}
    dropped_exact = dropped_near = 0
    for r in rows:
        k = _norm(r.get(key, ""))
        if k in seen_prompt:
            dropped_exact += 1
            continue
        seen_prompt.add(k)
        sh = _shingles(r.get(key, ""))
        cand = {}
        for s in sh:
            for i in index.get(s, ()):
                cand[i] = cand.get(i, 0) + 1
        dup = False
        for i, shared in cand.items():
            if shared >= max(2, len(sh) * 0.25) and kept_sh[i] and len(sh & kept_sh[i]) / len(sh | kept_sh[i]) >= 0.80:
                dup = True
                break
        if dup:
            dropped_near += 1
            continue
        idx = len(kept)
        kept.append(r)
        kept_sh.append(sh)
        for s in sh:
            index.setdefault(s, []).append(idx)
    return kept, dropped_exact, dropped_near


def unescape(s: str) -> str:
    out = s
    for pat, rep in UNESCAPE:
        out = out.replace(pat, rep)
    return out


def read_jsonl(path, limit=None):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if limit and len(rows) >= limit:
                break
    return rows


def load_trendyol(limit):
    """The v1 core, UNESCAPED. Splits any literal escapes the source copy carries."""
    out = []
    for d in read_jsonl(CORPUS, limit):
        usr = unescape(str(d.get("user") or d.get("instruction") or "").strip())
        asst = unescape(str(d.get("assistant") or d.get("response") or d.get("output") or "").strip())
        if usr and asst:
            out.append({"system": unescape(str(d.get("system") or "").strip()),
                        "user": usr, "assistant": asst, "src": "trendyol"})
    return out


def load_nist(limit, rng):
    out = []
    for d in read_jsonl("v2/candidates/nist-sample.jsonl", limit):
        txt = unescape(str(d.get("text") or "")).strip()
        txt = re.sub(r"^You are a cybersecurity expert[^.]*\.\s*", "", txt)   # strip embedded persona
        if len(txt) < 120:
            continue
        topic = "the NIST guidance on " + " ".join(re.findall(r"[A-Za-z0-9-]+", txt)[:6])
        q = rng.choice(QUESTION_TEMPLATES).format(topic=topic)
        out.append({"system": BRS.SYS, "user": q, "assistant": txt[:4000], "src": "nist"})
    return out


def load_attack(limit, rng):
    out = []
    for d in read_jsonl("v2/candidates/attack-sample.jsonl", limit):
        txt = unescape(str(d.get("text") or "")).strip()
        if "\n" not in txt:
            continue
        name, desc = txt.split("\n", 1)
        name, desc = name.strip(), desc.strip()
        if len(desc) < 80 or not name:
            continue
        q = f"What is {name}, and how should a defender treat it?"
        out.append({"system": BRS.SYS, "user": q, "assistant": desc[:4000], "src": "attack"})
    return out


def load_nvd(limit, rng):
    out = []
    for d in read_jsonl("v2/candidates/nvd-sample.jsonl", limit):
        txt = unescape(str(d.get("text") or "")).strip()
        if "\n" not in txt:
            continue
        cid, desc = txt.split("\n", 1)
        cid, desc = cid.strip(), desc.strip()
        if not re.match(r"^CVE-\d{4}-\d+$", cid) or len(desc) < 60:
            continue
        q = (f"What does {cid} describe, and what should a defender take from it? "
             f"Quote the identifier exactly as given.")
        out.append({"system": BRS.SYS, "user": q, "assistant": desc[:4000], "src": "nvd"})
    return out


def load_arcspan(limit, rng):
    out = []
    for d in read_jsonl("v2/candidates/arcspan-train-sample.jsonl", limit):
        txt = unescape(str(d.get("text") or "")).strip()
        if len(txt) < 120:
            continue
        head = " ".join(re.findall(r"[A-Za-z0-9.-]+", txt)[:8])
        q = (f"Extract the security indicators from this incident report ({head}...) and list them by "
             f"type (IP, domain, file, hash, malware, technique).")
        out.append({"system": BRS.SYS, "user": q, "assistant": txt[:4000], "src": "arcspan"})
    return out


def load_replay(limit, rng):
    """Real user/assistant turns — this slot exists to preserve conversational behaviour (F9/G-J)."""
    out = []
    for d in read_jsonl("v2/candidates/ultrachat-pairs.jsonl", limit):
        u = unescape(str(d.get("user") or "")).strip()
        a = unescape(str(d.get("assistant") or "")).strip()
        if len(u) > 20 and len(a) > 20:
            out.append({"system": BRS.SYS, "user": u, "assistant": a, "src": "replay"})
    return out


def load_authored(path, src):
    out = []
    for d in read_jsonl(path):
        if d.get("user") and d.get("assistant"):
            out.append({"system": d.get("system") or BRS.SYS, "user": d["user"],
                        "assistant": d["assistant"], "src": src, "kind": (d.get("meta") or {}).get("kind")})
    return out


def build_replacements(refusal_rows, rng):
    """Matched non-refusal defensive Q&A occupying the same number of slots as the refusal rows."""
    body_by_fam = {k: v["defence"] for k, v in BRS.FAMILIES.items()}
    fams = list(body_by_fam)
    out = []
    for r in refusal_rows:
        fam = rng.choice(fams)
        q = rng.choice([
            "What controls reduce the risk of {n}?",
            "Summarise the defensive posture against {n}.",
            "Which detections matter most for {n}?",
            "How should we harden against {n}?",
        ]).format(n=BRS.WHAT[fam])
        out.append({"system": BRS.SYS, "user": q, "assistant": body_by_fam[fam], "src": "replacement",
                    "kind": "defensive-qa"})
    return out


def toklen(s):
    return len(re.findall(r"[a-z0-9]+", str(s).lower()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="v2/data/mixture")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    os.makedirs(args.outdir, exist_ok=True)

    pools = {
        "trendyol": load_trendyol(CAPS["trendyol"]),
        "nist": load_nist(CAPS["nist"], rng),
        "attack": load_attack(CAPS["attack"], rng),
        "nvd": load_nvd(CAPS["nvd"], rng),
        "arcspan": load_arcspan(CAPS["arcspan"], rng),
        "replay": load_replay(CAPS["replay"], rng),
        "format": load_authored("v2/data/format-compliance.jsonl", "format"),
        "refusal": load_authored("v2/data/refusal-retention.jsonl", "refusal"),
    }
    hold = load_holdout_prompts()
    n_near_removed = 0
    clean = {}
    for k, rows in pools.items():
        before = len(rows)
        rows = [r for r in rows if not near_holdout(r.get("user", ""), hold)]   # exact AND >=0.80 near
        n_near_removed += before - len(rows)
        # documents key on CONTENT (their prompt is a fixed template); conversations key on the prompt
        dkey = "assistant" if k in ("nist", "attack", "nvd", "arcspan", "replay") else "user"
        rows, de, dn = dedupe(rows, key=dkey)
        clean[k] = rows
        print(f"  loaded {k:<9} {len(pools[k]):>6} rows -> held-out removed, deduped: "
              f"{len(rows):>6} (exact dup {de}, near dup {dn})")
    pools = clean

    # realise weights by explicit duplication
    weighted = {}
    for k, rows in pools.items():
        w = WEIGHTS.get(k, 1.0)
        weighted[k] = rows * max(1, int(round(w)))
    realised = {k: len(v) for k, v in weighted.items()}

    armA = [r for k in pools for r in weighted[k]]
    rng.shuffle(armA)

    repl = build_replacements(pools["refusal"], rng)
    repl_w = repl * int(round(WEIGHTS["refusal"]))
    armB, it = [], iter(repl_w)
    for r in armA:
        if r["src"] == "refusal":
            try:
                armB.append(next(it))
            except StopIteration:
                armB.append(r)
        else:
            armB.append(r)

    def write(name, rows):
        path = os.path.join(args.outdir, name)
        with open(path, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps({"system": r["system"], "user": r["user"],
                                     "assistant": r["assistant"], "src": r.get("src", "")},
                                    ensure_ascii=False) + "\n")
        return path, hashlib.sha256(open(path, "rb").read()).hexdigest()

    pa, ha = write("armA.jsonl", armA)
    pb, hb = write("armB.jsonl", armB)

    def mean_tok(rows, src=None):
        sel = [r for r in rows if src is None or r["src"] == src]
        return round(sum(toklen(r["assistant"]) for r in sel) / max(1, len(sel)), 1)

    receipt = {
        "seed": args.seed,
        "armA": {"path": pa, "rows": len(armA), "sha256": ha},
        "armB": {"path": pb, "rows": len(armB), "sha256": hb},
        "weights": WEIGHTS, "caps": CAPS, "loaded": {k: len(v) for k, v in pools.items()},
        "realised_presentations": realised,
        "weighted_epoch": len(armA),
        "tokens_per_epoch_est": sum(toklen(r["assistant"]) for r in armA),
        "assistant_token_mean": {"armA": mean_tok(armA), "refusal_rows": mean_tok(armA, "refusal"),
                                 "replacement_rows": mean_tok(armB, "replacement")},
        "refusal_slots": {"armA": sum(1 for r in armA if r["src"] == "refusal"),
                          "armB": sum(1 for r in armB if r["src"] == "replacement")},
    }
    with open(os.path.join(args.outdir, "mixture.receipt.json"), "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"\n  held-out rows removed (exact or >=0.80 near): {n_near_removed}")
    print(f"WROTE {pa}: {len(armA)} rows | {pb}: {len(armB)} rows")
    print(f"  weighted epoch: {len(armA)} presentations")
    print(f"  refusal slots: armA={receipt['refusal_slots']['armA']} armB={receipt['refusal_slots']['armB']}")
    print(f"  assistant tokens (mean): A={receipt['assistant_token_mean']['armA']} "
          f"refusal={receipt['assistant_token_mean']['refusal_rows']} "
          f"replacement={receipt['assistant_token_mean']['replacement_rows']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
