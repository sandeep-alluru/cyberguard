#!/usr/bin/env python3
"""cyberguard_data.py — THE single source of truth for corpus loading and the train/eval split.

Why this module exists. Loader logic was duplicated in four places (train_cyberguard.py,
eval_cyberguard.py, verify_split.py, check_leakage.py) and they diverged: the trainer deduped
by user prompt before splitting, but check_leakage.py did not, so the leakage audit measured a
split that no run had ever used. A clean audit of the wrong split is worse than no audit — it
licenses a leaky evaluation.

The contract, and the order is load-bearing:

    1. read rows, keep those with a non-empty user AND assistant
    2. drop system content from the dedupe decision, keep it for the record
    3. DEDUPLICATE BY NORMALISED USER PROMPT (first occurrence wins, file order)
    4. optionally cap the corpus (MAX_ROWS, for cheap smoke runs) — BEFORE the shuffle
    5. seed, shuffle, then take the first EVAL_N as held-out and the rest as training

Step 3 must precede step 5. The corpus repeats 675 user prompts with differing answers;
splitting on row identity alone left 15 held-out prompts at shingle-Jaccard 1.000 against
training rows, i.e. the evaluation asked questions the model had already been trained on.

Every consumer imports this. Do not re-implement it anywhere.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

EVAL_N_DEFAULT = 500
SEED_DEFAULT = 0


def norm_prompt(user: str) -> str:
    """The dedupe/identity key for a user prompt: case-folded, whitespace-collapsed."""
    return " ".join((user or "").lower().split())


def load_rows(data: Path | str) -> list[dict]:
    """Load the corpus into canonical rows, deduplicated by normalised user prompt.

    Canonical row: {"system": str, "user": str, "assistant": str}
    """
    rows: list[dict] = []
    with open(data, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            usr = (d.get("user") or d.get("instruction") or "").strip()
            asst = (d.get("assistant") or d.get("response") or d.get("output") or "").strip()
            if not (usr and asst):
                continue
            rows.append({
                "system": (d.get("system") or "").strip(),
                "user": usr,
                "assistant": asst,
            })

    seen: set[str] = set()
    deduped: list[dict] = []
    for r in rows:
        key = norm_prompt(r["user"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    # Drop rows that ASK FOR AN ATTACK CAPABILITY TO BE BUILT. Training on those teaches the
    # behaviour the evaluation gate refuses to ship. Roughly 1.8% of the corpus; the cost of
    # dropping them is negligible against the cost of shipping a model that writes rootkits.
    # Set DROP_ATTACK_PRODUCTION=0 to train on everything (and expect the boundary gate to say no).
    if os.environ.get("DROP_ATTACK_PRODUCTION", "1") == "1":
        from cyberguard_contract import teaches_attack_production
        before = len(deduped)
        kept, dropped = [], 0
        for r in deduped:
            if teaches_attack_production(r["user"]):
                dropped += 1
                continue
            kept.append(r)
        if dropped:
            import sys as _sys
            print(f"  dropped {dropped} of {before} rows that teach attack production "
                  f"({dropped / max(1, before):.2%}); {len(kept)} remain", file=_sys.stderr)
        deduped = kept

    # Collapse NEAR-duplicates, not only exact ones.
    #
    # Exact-prompt dedupe is not enough for this corpus. It is templated, so two prompts can be
    # 0.82 Jaccard-similar without being identical — "Describe an approach to implement X" versus
    # "How would you implement X" — and both survive. Whether such a pair lands on opposite sides
    # of the split then depends purely on where the shuffle puts them. That is exactly what
    # happened: removing 178 attack-production rows shifted the split and the leakage audit went
    # from 0 rows at >= 0.80 to 1 row at 0.824. A split whose cleanliness depends on how many
    # unrelated rows were filtered is not clean, it is lucky.
    #
    # So collapse them BEFORE the split, using the same shingle/Jaccard definition and the same
    # 0.80 threshold the leakage audit gates on. First occurrence in file order wins.
    near_dup_threshold = float(os.environ.get("NEAR_DUP_THRESHOLD", "0.80"))
    if os.environ.get("COLLAPSE_NEAR_DUP", "1") == "1":
        from collections import defaultdict
        import sys as _sys
        index: dict[str, list[int]] = defaultdict(list)
        kept_sh: list[set] = []
        collapsed: list[dict] = []
        dropped_near = 0
        for r in deduped:
            s = shingles(r["user"])
            cand: dict[int, int] = defaultdict(int)
            for sh in s:
                for i in index.get(sh, ()):
                    cand[i] += 1
            if any(shared >= max(2, len(s) * 0.25) and jaccard(s, kept_sh[i]) >= near_dup_threshold
                   for i, shared in cand.items()):
                dropped_near += 1
                continue
            idx = len(collapsed)
            collapsed.append(r)
            kept_sh.append(s)
            for sh in s:
                index[sh].append(idx)
        if dropped_near:
            print(f"  collapsed {dropped_near} near-duplicate prompts "
                  f"(Jaccard >= {near_dup_threshold}); {len(collapsed)} remain", file=_sys.stderr)
        deduped = collapsed

    return deduped


def make_split(
    rows: list[dict],
    eval_n: int = EVAL_N_DEFAULT,
    seed: int = SEED_DEFAULT,
    max_rows: int = 0,
) -> tuple[list[dict], list[dict]]:
    """Return (train_rows, eval_rows) for the canonical row list. Deterministic given seed."""
    if max_rows:
        rows = rows[:max_rows]
    r = list(rows)
    random.seed(seed)
    random.shuffle(r)
    return r[eval_n:], r[:eval_n]


def to_messages(row: dict) -> list[dict]:
    """Canonical row -> chat messages, system message omitted when empty."""
    msgs: list[dict] = []
    if row.get("system"):
        msgs.append({"role": "system", "content": row["system"]})
    msgs.append({"role": "user", "content": row["user"]})
    msgs.append({"role": "assistant", "content": row["assistant"]})
    return msgs


def shingles(text: str, k: int = 3) -> set[str]:
    """Content shingles for near-duplicate detection (stopwords stripped)."""
    import re
    stop = {"the", "a", "an", "of", "to", "and", "or", "in", "on", "for", "with", "is", "are",
            "how", "what", "would", "you", "your", "be", "that", "this", "it", "as", "at", "by"}
    w = [t for t in re.findall(r"[a-z]+", (text or "").lower()) if t not in stop]
    if len(w) < k:
        return {" ".join(w)} if w else set()
    return {" ".join(w[i:i + k]) for i in range(len(w) - k + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)
