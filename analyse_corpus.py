#!/usr/bin/env python3
"""analyse_corpus.py — measure how homogeneous the cybersecurity corpus really is.

Motivation: the Flash-Next research session flagged that every row carries the same
1085-character system prompt, and cited the instruction-tuning literature on dataset
homogeneity causing model degeneration. That is a claim about OUR training data and it
either holds or it does not, so measure it:

  * how many DISTINCT system prompts exist (if 1, the persona is a constant, and the model
    can learn to ignore it — it carries no information)
  * how many distinct USER prompts, and how many exact duplicates
  * template similarity: the modal opening of user prompts, as a crude proxy for
    fill-in-the-blank generation
  * lexical diversity of the assistant answers (type-token ratio), which is what actually
    degrades when a corpus is templated

CPU only, no GPU, so it cannot contend with anything already running.
"""
from __future__ import annotations

import collections
import json
import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("CYBERGUARD_ROOT", Path.home() / "cyberguard"))
DATA = ROOT / "data" / "trendyol-cybersec" / "CyberSec-Dataset_escaped.jsonl"

sys_prompts: collections.Counter = collections.Counter()
user_prompts: collections.Counter = collections.Counter()
openings: collections.Counter = collections.Counter()
first_verbs: collections.Counter = collections.Counter()
tokens: collections.Counter = collections.Counter()
n = 0
src_chars = tgt_chars = 0

with open(DATA, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        u = (d.get("user") or "").strip()
        a = (d.get("assistant") or "").strip()
        s = (d.get("system") or "").strip()
        if not (u and a):
            continue
        n += 1
        sys_prompts[s] += 1
        user_prompts[u] += 1
        src_chars += len(u)
        tgt_chars += len(a)
        words = re.findall(r"[a-z]+", u.lower())
        if words:
            openings[" ".join(words[:4])] += 1
            first_verbs[words[0]] += 1
        tokens.update(re.findall(r"[a-z]+", a.lower()))

print(f"rows analysed: {n}")
print()
print("=== system prompt (the persona) ===")
print(f"  distinct system prompts: {len(sys_prompts)}")
for s, c in sys_prompts.most_common(3):
    print(f"    {c:6d} x  {len(s)} chars  {s[:90]!r}")
if len(sys_prompts) == 1:
    print("  VERDICT: constant across every row -> carries no per-example information")
else:
    print(f"  VERDICT: {len(sys_prompts)} variants; the most common covers "
          f"{sys_prompts.most_common(1)[0][1]/n:.1%} of rows")

print()
print("=== user prompts (the task) ===")
dupes = sum(c - 1 for c in user_prompts.values() if c > 1)
print(f"  distinct: {len(user_prompts)} of {n}  ({len(user_prompts)/n:.1%} unique)")
print(f"  exact duplicate rows (beyond the first): {dupes}")
print(f"  mean user length: {src_chars/n:.0f} chars | mean answer length: {tgt_chars/n:.0f} chars")

print()
print("=== templating ===")
print("  most common user-prompt openings (first 4 words):")
for o, c in openings.most_common(6):
    print(f"    {c:6d} x  {o!r}")
top_open_share = openings.most_common(1)[0][1] / n
print(f"  most common opening covers {top_open_share:.1%} of rows")
print("  most common first verbs:", ", ".join(f"{v}({c})" for v, c in first_verbs.most_common(6)))

print()
print("=== answer lexical diversity ===")
total = sum(tokens.values())
print(f"  answer tokens: {total:,}   distinct: {len(tokens):,}   "
      f"type-token ratio: {len(tokens)/max(1,total):.4f}")
print("  most frequent answer tokens:", ", ".join(f"{t}({c})" for t, c in tokens.most_common(10)))

print()
print("=== risk read ===")
risks = []
if len(sys_prompts) <= 2:
    risks.append("persona is effectively constant -> the model can learn to ignore the "
                 "system prompt instead of conditioning on it")
if top_open_share > 0.05:
    risks.append(f"{top_open_share:.0%} of user prompts share one opening -> a single "
                 "generation template is over-represented")
if len(user_prompts) / n < 0.95:
    risks.append("a meaningful share of user prompts are exact duplicates across rows")
if len(tokens) / max(1, total) < 0.05:
    risks.append("answer vocabulary is narrow -> repetitive phrasing is likely")
print("  " + ("\n  ".join(risks) if risks else "no strong homogeneity signal detected"))
