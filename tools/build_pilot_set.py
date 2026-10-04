#!/usr/bin/env python3
"""Build the Astra-directed pilot training set: 8,000 clean examples.

Astra spec (docs/PILOT-SPEC-v3-RECOVERY.md):
  4,000 domain-task | 2,400 legitimate security requests w/ useful answers | 800 harmful w/ refusals
  | 800 general instruction-following
Targets: concise but sufficient, NO stock introductions, NO exposed reasoning traces.
Evaluation questions excluded. Broken-template rows rejected. Primus descendants rejected.
"""
import json, re, sys, collections
from pathlib import Path

ROOT = Path("/home/clawerdigi2/cyberguard")
OUT = ROOT / "data/v4-pilot"
OUT.mkdir(parents=True, exist_ok=True)

# --- reject predicates (Astra: no stock intro, no exposed reasoning, no broken template) ------------
BROKEN = re.compile(r"\b(on|through|in|to|for|with|of|at|by)\s+against\b", re.I)
STOCK = re.compile(r"^\s*(<\|reserved_special_token_\d+\|>\s*)?Okay,\s*let'?s\s+tackle", re.I)
REASON = re.compile(r"(First, I need to|Let me think|I need to (recall|consider)|Initial CVE Analysis|"
                    r"^\s*\*\*Initial|Step 1:|chain of thought)", re.I)


def clean(text):
    t = (text or "").strip()
    if not t:
        return None
    if STOCK.search(t):
        return None
    if REASON.search(t):
        return None
    if BROKEN.search(t):
        return None
    if "reserved_special_token" in t:
        return None
    return t


def concise(text, limit_words=220):
    """Astra: concise but sufficient. Drop over-long targets rather than clip mid-sentence."""
    if len(text.split()) > limit_words:
        return None
    return text


def load_jsonl(p):
    for line in open(p, encoding="utf8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue


def fields(d):
    """Normalise the several corpus shapes to (user, assistant)."""
    if "messages" in d:
        u = a = None
        for m in d["messages"]:
            if m.get("role") == "user" and u is None:
                u = m.get("content")
            elif m.get("role") == "assistant":
                a = m.get("content")
        return u, a
    return d.get("user") or d.get("prompt") or d.get("question"), d.get("assistant") or d.get("answer")


def main():
    counts = collections.Counter()
    out = []
    # ---- 4,000 domain-task: from the repaired Trendyol and Fenrir pools ----
    for src in (ROOT / "data/trendyol-cybersec/CyberSec-Dataset_escaped.jsonl",
                ROOT / "data/v3/sft/fenrir.jsonl"):
        if not src.exists():
            print(f"  SKIP {src.name} (absent)"); continue
        for d in load_jsonl(src):
            if counts["domain"] >= 4000:
                break
            u, a = fields(d)
            u, a = clean(u), clean(a)
            if not u or not a:
                counts["domain_rejected"] += 1; continue
            a = concise(a)
            if not a:
                counts["domain_too_long"] += 1; continue
            out.append({"stratum": "domain", "user": u, "assistant": a})
            counts["domain"] += 1
    # ---- 2,400 legitimate security requests with useful answers: CyberSecEval MITRE-FRR prompts ----
    frr = ROOT / "pubbench/frr/mitre_frr.json"
    if frr.exists():
        for i, d in enumerate(json.load(open(frr))):
            if counts["legit"] >= 2400:
                break
            p = clean(d.get("mutated_prompt"))
            if not p:
                continue
            out.append({"stratum": "legit", "user": p, "assistant": None})  # answer generated later
            counts["legit"] += 1
    # ---- 800 harmful with refusals: HarmBench standard ----
    hb = ROOT / "pubbench/harmbench/harmbench_behaviors_text_test.csv"
    if hb.exists():
        import csv
        for r in csv.DictReader(open(hb, encoding="utf8", errors="replace")):
            if counts["harmful"] >= 800:
                break
            if r.get("FunctionalCategory") != "standard":
                continue
            b = clean(r.get("Behavior"))
            if not b:
                continue
            out.append({"stratum": "harmful", "user": b, "assistant": None})
            counts["harmful"] += 1
    # ---- 800 general instruction-following: EXCLUDE any evaluation set ----
    print("  general stratum: requires a non-evaluation source; see note", flush=True)

    (OUT / "pilot-raw.jsonl").write_text("".join(json.dumps(x) + "\n" for x in out))
    print(f"  wrote {len(out)} rows -> {OUT/'pilot-raw.jsonl'}")
    for k in ("domain", "domain_rejected", "domain_too_long", "legit", "harmful"):
        print(f"    {k}: {counts[k]}")


if __name__ == "__main__":
    main()
