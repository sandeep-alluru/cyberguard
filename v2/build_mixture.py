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
# Sources that MUST contribute rows. 'arcspan' is deliberately absent: its extraction labels are not
# retrievable from the shipped sample, so G-D is declared zero-shot (docs/SPEC-V2.md §5 U7).
REQUIRED_SOURCES = {"trendyol", "nist", "attack", "nvd", "replay", "format", "refusal"}

ASSISTANT_MAX_WORDS = 400   # fallback when the tokenizer is unavailable
ASSISTANT_MAX_TOKENS = 512  # the evaluation's generation budget (review #2 finding 3: measuring in
                            # regex words under-counted; 1,300 answers per arm exceeded the real budget)
_TOK = None


def _tokenizer():
    global _TOK
    if _TOK is None:
        from transformers import AutoTokenizer
        _TOK = AutoTokenizer.from_pretrained("v2/tokenizer")
    return _TOK


ABBREV = {"i.e", "e.g", "etc", "vs", "co", "inc", "ltd", "fig", "dr", "st", "mr", "ms", "no", "al",
          "approx", "cf", "pp", "vol", "jr", "sr",
          # review #4: citation/prose abbreviations that were being taken for sentence ends
          "dept", "univ", "inst", "assn", "bros", "corp", "govt", "est", "ed", "eds", "trans",
          "repr", "sec", "art", "figs", "eq", "ref", "refs", "ch", "pt", "cit", "ibid",
          "avg", "min", "max", "ext", "a.k.a", "aka", "u.s", "u.k", "u.n", "intl"}


def _ends_sentence(tok):
    """True only for a REAL sentence end.

    Review #4 found 10 control answers ending mid-thought ("(e.g.", "(i.e.", "(a.k.a.", "U.S.") and two
    truncated citations ("(Citation: US Dept."): the old splitter took any period followed by whitespace
    for a sentence boundary. A terminator counts only if the token before it is prose — not an
    abbreviation, not an initial ("D."), not an intialism ("U.S.").
    """
    t = str(tok).strip().strip('\"\u201d\u2019\'`')
    if not t:
        return False
    if t[-1] in "!?":
        return True
    if not t.endswith("."):
        return False
    core = t[:-1].strip("([{<\"'`").lower()
    if not core:
        return False
    if len(core) == 1 and core.isalpha():     # a letter initial: "D." (but "0." is a real end)
        return False
    if re.fullmatch(r"[a-z](\.[a-z])+", core):  # initialism: "U.S" "i.e" "a.k.a"
        return False
    # NB: a period INSIDE the token does not by itself disqualify it — "1.2.3" (a version) and
    # "example.com" (a host) are ordinary sentence ends, and treating them as non-ends made 898 NVD
    # answers look boundary-less when they were complete.
    return core not in ABBREV


def split_sentences(text):
    """Split prose into sentences using _ends_sentence, so abbreviations cannot end a sentence."""
    out, buf = [], []
    for tok in str(text).split():
        buf.append(tok)
        if _ends_sentence(tok):
            out.append(" ".join(buf))
            buf = []
    if buf:
        out.append(" ".join(buf))
    return out


def complete_sentence(text):
    """Drop a trailing incomplete fragment.

    Reviews #3/#4: the trim accepted an abbreviation's period ("(i.e.", "U.S.", "Dept.") or found no
    boundary in ATT&CK prose ending at a link/citation. Scan for the NEWEST real sentence end; an
    unclosed "(Citation: ..." fragment is removed rather than half-kept.
    """
    s = str(text).rstrip()
    w = s.split()
    for i in range(len(w) - 1, 6, -1):            # newest valid end first; keep >= 8 words
        if _ends_sentence(w[i]):
            return " ".join(w[:i + 1])
    low = s.lower()
    i = low.rfind("(citation:")
    if i > 0 and s[i:].count(")") == 0:
        head = s[:i].rstrip()
        if len(head.split()) >= 8:
            return head
    return s


# Review #4, residual: a row can end mid-thought even when it is UNDER the token budget, because a loader
# cut it at a CHARACTER cap (NIST rows are sliced at 4000 chars) and clip_answer() leaves short text alone.
# Prose sources must end at a real boundary. Format rows are deliberately excluded: their target is a
# triage label, a Sigma rule or a JSON object, and "completing" those would corrupt them.
PROSE_SOURCES = {"nist", "attack", "nvd", "replay", "refusal"}


def _ends_ok(text):
    """True if the text already ends at something a reader would accept as an end.

    Review #5 corrected two errors here: accepting ":"/";" let 9 unfinished introductions through, and
    rejecting every abbreviation period dropped 5 complete NVD answers ending "...etc." plus 5 ending on a
    separated period. A trailing "etc." is a normal sentence tail; a truncated citation is not — that case
    is caught by defect() below, not by the abbreviation list.
    """
    w = str(text).rstrip().split()
    if not w:
        return True
    t = w[-1]
    if _ends_sentence(t):
        return True
    if t.lower().strip(".") == "etc":                 # "...Java, Javascript, etc."
        return True
    if t in (".", "!", "?") and len(w) >= 2 and _ends_sentence(w[-2] + "."):
        return True                                    # a period separated by a space
    # closed citation, bracket, code fence, table cell — complete as stored
    return t.endswith((")", "]", "`", '"'))


def defect(text):
    """Mechanical incompleteness a reader would recognise, with the reason (reviews #4/#5).

    The classes the reviewers actually found: heading-only targets, an introduction ending on its colon,
    an open ``` fence, a citation that never closes, and a dangling connective/punctuation.
    Returns None when nothing is wrong.
    """
    s = str(text).strip()
    w = s.split()
    if not w:
        return "empty"
    if s.startswith("#") and len(w) <= 16:
        return "heading-only"
    lines = [ln for ln in s.splitlines() if ln.strip()]
    if lines and lines[-1].lstrip().startswith("#"):
        return "trailing-heading"
    if s.count("```") % 2:
        return "unclosed-code-fence"
    low = s.lower()
    if "(citation:" in low and low.rfind("(citation:") > s.rfind(")"):
        return "unclosed-citation"
    if s.rstrip().endswith((":", ",", ";", "(", "[", "{", "|", "-", "—")):
        return "dangling-punctuation"
    return None


def clip_answer(text):
    """Trim to <= ASSISTANT_MAX_TOKENS real tokens, then to the last sentence boundary."""
    tok = _tokenizer()
    w = str(text).split()
    if len(tok(" ".join(w), add_special_tokens=False)["input_ids"]) <= ASSISTANT_MAX_TOKENS:
        return text, False
    lo, hi = 0, len(w)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if len(tok(" ".join(w[:mid]), add_special_tokens=False)["input_ids"]) <= ASSISTANT_MAX_TOKENS:
            lo = mid
        else:
            hi = mid - 1
    cut = " ".join(w[:lo])
    m = re.search(r"^[\s\S]*[.!?](?=\s|$)", cut)
    if m and len(m.group(0).split()) > lo * 0.5:
        cut = m.group(0).strip()
    return cut.rstrip(" ,;:-"), True
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

UNESCAPE = [(chr(92) + "n", "\n"), (chr(92) + "t", "\t"), (chr(92) + "r", "\r"),
            (chr(92) + '"', '"'),
            # narrow-NO-BREAK-space safe: a backslash before a REAL newline is residue
            (chr(92) + "\n", "\n"), (chr(92) + "\t", "\t"), (chr(92) + chr(92), chr(92))]



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
        if not h or shared < max(2, len(s) * 0.25):
            continue
        if len(s & h) / len(s | h) >= 0.80:          # near-duplicate (what the audit instrument used)
            return True
        if shared / min(len(s), len(h)) >= 0.80:     # CONTAINMENT: a held-out prompt embedded in a longer
            return True                              # training row. leak_scan found exactly this case and
    return False                                     # the Jaccard-only filter had let it through.


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
    for _ in range(3):                       # iterate: doubled patterns leave a stray on pass 1
        for pat, rep in UNESCAPE:
            out = out.replace(pat, rep)
    return re.sub(r"[\\](?=[\s])", "", out)   # a backslash before whitespace is always residue here


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
        txt = re.sub(r"^You are a cybersecurity expert[^.]*\.\s*", "", txt)
        txt = re.sub(r"^You provide accurate[^.]*\.\s*", "", txt)          # both embedded personas
        if len(txt) < 120:
            continue
        # The prompt must identify what is being asked. These rows are question+answer prose, so use the
        # embedded question as the prompt and the remainder as the target; skip rows with no question
        # rather than shipping a prompt that points at nothing (Astra data review #2).
        m = re.search(r"([A-Z][^?]{20,300}\?)", txt)
        if not m:
            continue
        question = m.group(1).strip()
        answer = (txt[:m.start()] + txt[m.end():]).strip() or txt
        out.append({"system": BRS.SYS, "user": question, "assistant": answer[:4000], "src": "nist"})
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
        q = (f"What does {cid} describe, and what should a defender take from it?")
        # the answer must actually satisfy the prompt: lead with the identifier it was asked about
        out.append({"system": BRS.SYS, "user": q, "assistant": f"{cid}: {desc}"[:4000], "src": "nvd"})
    return out


def load_arcspan(limit, rng):
    out = []
    for d in read_jsonl("v2/candidates/arcspan-train-sample.jsonl", limit):
        txt = unescape(str(d.get("text") or "")).strip()
        if len(txt) < 120:
            continue
        labels = str(d.get("labels") or "").strip()
        if not labels or labels in ("[]", "''", '""'):
            continue                       # no extraction target: a prose answer would be a mismatch
        q = ("Extract the security indicators from the incident report below and list them by type "
             "(IP, domain, file, hash, malware, technique).\n\n" + txt[:2000])
        out.append({"system": BRS.SYS, "user": q, "assistant": labels[:4000], "src": "arcspan"})
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


REPLACEMENT_QUESTIONS = [
    "What controls reduce the risk of {n}?",
    "Summarise the defensive posture against {n}.",
    "Which detections matter most for {n}?",
    "How should we harden against {n}?",
    "Which logging sources expose {n}?",
    "How do we validate coverage against {n}?",
    "What does an incident runbook say about {n}?",
    "Which NIST CSF functions apply to {n}?",
    "How should we brief leadership on {n}?",
    "What does a purple-team exercise for {n} cover?",
    "Which compensating controls help when patching lags on {n}?",
    "How do we measure our response time to {n}?",
    "What does ATT&CK recommend for {n}?",
    "Which preventive control is cheapest against {n}?",
    "How do we test that our controls hold against {n}?",
    "What telemetry would betray {n} early?",
    "How should we prioritise remediation for {n}?",
    "What does a tabletop exercise for {n} need to cover?",
    "Which identity controls blunt {n}?",
    "How do we segment to limit {n}?",
    "What would a post-incident review of {n} ask?",
    "Which metrics show we are improving against {n}?",
]
REPLACEMENT_LEADS = [
    "Defensively: ", "For detection and hardening: ", "The defensive reading: ",
    "Concretely, for defenders: ", "What reduces risk here: ", "In practice: ",
]


def build_replacements(refusal_rows, rng):
    """A matched control: same slot count, same weight, comparable length, and genuinely diverse.

    The first version produced 48 distinct prompts and 12 answers against the treatment's 1,198 and 388 —
    the Astra data review called that "a substantially more repetitive, shorter treatment", which is not
    a matched substitution. This pools TWO sources of real defensive content: the family grid (families x
    questions x leads) and ATT&CK technique/mitigation objects already admitted to the mixture. Both are
    defensive text the model is entitled to see; the point is that the *refusal slots* are occupied by
    something that teaches defence rather than by refusal behaviour.
    """
    bodies = [(k, v["defence"]) for k, v in BRS.FAMILIES.items()]
    pool = []
    by_fam = {}
    for fam, body in bodies:
        # Review #5 MAJOR 2: the control must be matched to the row it replaces, not merely equal in slot
        # count. Every template for this family is kept, and the assignment below draws from the SAME
        # family as the refusal prompt it replaces, so a cryptojacking refusal becomes cryptojacking
        # defensive guidance. All questions x all leads (not just two) keeps per-family diversity at ~132.
        for q in REPLACEMENT_QUESTIONS:
            for lead in REPLACEMENT_LEADS:
                item = (q.format(n=BRS.WHAT[fam]), lead + body)
                pool.append(item)
                by_fam.setdefault(fam, []).append(item)
    # second pool: ATT&CK objects (name/description pairs already in the mixture)
    for d in read_jsonl("v2/candidates/attack-sample.jsonl"):
        txt = unescape(str(d.get("text") or "")).strip()
        if "\n" not in txt:
            continue
        name, desc = (x.strip() for x in txt.split("\n", 1))
        if len(desc) < 80 or not name:
            continue
        # Reviews #2/#3: truncating a prefix leaves incomplete endings, and these descriptions often
        # have no sentence boundary inside the token budget. Build the answer from WHOLE SENTENCES that
        # fit, and skip the document if even its first sentence does not — a complete shorter answer
        # beats a longer truncated one.
        # accumulate WHOLE SENTENCES against the TOKEN budget (the word budget under-counts link- and
        # punctuation-heavy ATT&CK prose, which is why 8 answers were still clipped mid-thought)
        try:
            _tk = _tokenizer()
        except Exception:                                   # noqa: BLE001
            _tk = None
        sents = split_sentences(desc)
        txt_ok = ""
        for s in sents:
            cand = (txt_ok + " " + s).strip()
            if _tk is not None and len(_tk(cand, add_special_tokens=False)["input_ids"]) > ASSISTANT_MAX_TOKENS:
                break
            txt_ok = cand
        if len(txt_ok.split()) < 8:          # first sentence alone blows the budget -> not usable
            continue
        pool.append((f"What does ATT&CK document about {name}, and what should a defender take from it?",
                     txt_ok))
    rng.shuffle(pool)
    out, seen = [], set()
    for q, a in pool:
        k = " ".join(q.lower().split())
        if k in seen:
            continue
        seen.add(k)
        out.append({"system": BRS.SYS, "user": q, "assistant": a, "src": "replacement",
                    "kind": "defensive-qa"})
    # repeat the pool if it is smaller than the refusal row count (diversity is maximised either way)
    while len(out) < len(refusal_rows):
        out.append(out[len(out) % max(1, len(seen))])
    # family -> [{row}, ...] for topic-matched assignment (a family's pool is never smaller than its demand
    # by accident: 22 questions x 6 leads = 132 entries per family)
    fam_rows = {f: [{"system": BRS.SYS, "user": q, "assistant": a, "src": "replacement",
                     "kind": "defensive-qa"} for q, a in v] for f, v in by_fam.items()}
    return out, fam_rows


def refusal_families():
    """normalised refusal prompt -> meta.family, so a substitution can be matched to its topic."""
    out = {}
    for d in read_jsonl("v2/data/refusal-retention.jsonl"):
        if d.get("user"):
            out[_norm(str(d["user"]))] = (d.get("meta") or {}).get("family")
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

    # Fail closed, loudly — but only when BUILDING, never on import (a module-level exit broke the
    # regression checks that import complete_sentence()).
    if not os.path.exists(CORPUS):
        sys.exit(f"FATAL: corpus not found: {CORPUS}\n"
                 f"       set CYBERGUARD_CORPUS to the CyberSec-Dataset_escaped.jsonl you mean\n"
                 f"       (this repository keeps it at v2/data/corpus/trendyol-escaped.jsonl)")
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
    n_clipped = 0
    n_boundary_fixed = 0
    n_dropped_noend = 0
    drop_reasons = {}
    clean = {}
    for k, rows in pools.items():
        before = len(rows)
        rows = [r for r in rows if not near_holdout(r.get("user", ""), hold)]   # exact AND >=0.80 near
        n_near_removed += before - len(rows)
        # documents key on CONTENT (their prompt is a fixed template); conversations key on the prompt
        dkey = "assistant" if k in ("nist", "attack", "nvd", "arcspan", "replay") else "user"
        rows, de, dn = dedupe(rows, key=dkey)
        for r in rows:                       # clip to the eval's generation budget, in REAL tokens
            try:
                new, clipped = clip_answer(r["assistant"])
            except Exception:                # tokenizer unavailable -> word-based fallback
                a = str(r["assistant"])
                if len(a.split()) > ASSISTANT_MAX_WORDS:
                    new, clipped = " ".join(a.split()[:ASSISTANT_MAX_WORDS]), True
                else:
                    new, clipped = a, False
            if clipped:
                r["assistant"] = new
                n_clipped += 1
            if k in PROSE_SOURCES:
                reason = defect(r["assistant"])
                if reason:
                    fixed = complete_sentence(r["assistant"])
                    if fixed != r["assistant"] and not defect(fixed):
                        r["assistant"] = fixed              # repairable: trim to a real boundary
                        n_boundary_fixed += 1
                    elif k != "refusal":
                        r["_drop"] = reason
                        drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
                elif not _ends_ok(r["assistant"]):
                    fixed = complete_sentence(r["assistant"])
                    if fixed != r["assistant"]:
                        r["assistant"] = fixed
                        n_boundary_fixed += 1
        # Reviews #4/#5: a target that cannot be re-ended (NIST index/table fragments, heading-only
        # answers, an open code fence, an unclosed citation) is NOT admitted — shipping it would teach the
        # model to stop mid-thought. Refusals are exempt: their slot count is a pre-registered quantity.
        if k in PROSE_SOURCES and k != "refusal":
            keep = [r for r in rows if not r.pop("_drop", None)]
            n_dropped_noend += len(rows) - len(keep)
            rows = keep
        clean[k] = rows
        print(f"  loaded {k:<9} {len(pools[k]):>6} rows -> held-out removed, deduped: "
              f"{len(rows):>6} (exact dup {de}, near dup {dn})")
        if k in REQUIRED_SOURCES and not rows:
            sys.exit(f"FATAL: source '{k}' contributed 0 rows. Its input is missing or unreadable; "
                     f"refusing to write a mixture that silently drops a source.")
    pools = clean

    # realise weights by explicit duplication
    weighted = {}
    for k, rows in pools.items():
        w = WEIGHTS.get(k, 1.0)
        weighted[k] = rows * max(1, int(round(w)))
    realised = {k: len(v) for k, v in weighted.items()}

    armA = [r for k in pools for r in weighted[k]]
    rng.shuffle(armA)

    repl, by_fam = build_replacements(pools["refusal"], rng)
    repl_w = repl * int(round(WEIGHTS["refusal"]))
    armB, it = [], iter(repl_w)
    fam_of, cursors, matched, unmatched = refusal_families(), {}, 0, 0
    for r in armA:
        if r["src"] == "refusal":
            fam = fam_of.get(_norm(r["user"]))
            lst = by_fam.get(fam) or []
            if lst:
                i = cursors.get(fam, 0)
                cursors[fam] = i + 1
                armB.append(lst[i % len(lst)])       # topic-matched control row
                matched += 1
            else:
                try:
                    armB.append(next(it))            # 'factuality' prompts: no topic to match
                except StopIteration:
                    armB.append(r)
                unmatched += 1
        else:
            armB.append(r)
    print(f"  control substitution: {matched} topic-matched, {unmatched} from the general pool "
          f"(family with no defensive body)")

    def scrub(s):
        """Last-resort residue removal at write time: a backslash followed by whitespace is never
        meaningful in this data (Windows paths are backslash+letter), so it is always residue."""
        return re.sub(r"[\\](?=[\s])", "", str(s))   # character class: a bare backslash would escape the group

    def write(name, rows):
        path = os.path.join(args.outdir, name)
        with open(path, "w", encoding="utf-8") as fh:
            for r in rows:
                # clip AFTER the scrub: removing a backslash changes whitespace and can shift
                # tokenisation by a token, which is why 36 answers sat one token over the budget
                a = scrub(r["assistant"])
                # enforce on the STORED form: tokenising "a  b" or "a\nb" differs from "a b", so a
                # whitespace-normalised measurement can pass while the stored string exceeds the budget
                if r.get("src") in ("trendyol", "nvd", "nist", "attack", "replacement", "replay"):
                    a = complete_sentence(a)      # prose only: JSON/YAML targets must not be trimmed
                try:
                    tok = _tokenizer()
                    while len(a.split()) > 1 and len(tok(a, add_special_tokens=False)["input_ids"]) > ASSISTANT_MAX_TOKENS:
                        a = " ".join(a.split()[:-1])
                        m = re.search(r"^[\s\S]*[.!?](?=\s|$)", a)
                        if m and len(m.group(0).split()) > len(a.split()) * 0.5:
                            a = m.group(0).strip()
                except Exception:
                    pass
                fh.write(json.dumps({"system": scrub(r["system"]), "user": scrub(r["user"]),
                                     "assistant": a, "src": r.get("src", "")},
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
        "answers_clipped_at_max": n_clipped,
        "prose_answers_re_ended": n_boundary_fixed,
        "prose_rows_dropped_no_boundary": n_dropped_noend,
        "prose_rows_dropped_by_reason": drop_reasons,
        "assistant_max_words": ASSISTANT_MAX_WORDS,
        "refusal_slots": {"armA": sum(1 for r in armA if r["src"] == "refusal"),
                          "armB": sum(1 for r in armB if r["src"] == "replacement")},
    }
    with open(os.path.join(args.outdir, "mixture.receipt.json"), "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"\n  held-out rows removed (exact or >=0.80 near): {n_near_removed}")
    print(f"  answers clipped at {ASSISTANT_MAX_WORDS} words: {n_clipped}")
    print(f"  prose answers re-ended at a real boundary: {n_boundary_fixed}")
    print(f"  prose rows DROPPED (no sentence boundary exists): {n_dropped_noend}")
    print(f"    by reason: {drop_reasons}")
    print(f"WROTE {pa}: {len(armA)} rows | {pb}: {len(armB)} rows")
    print(f"  weighted epoch: {len(armA)} presentations")
    print(f"  refusal slots: armA={receipt['refusal_slots']['armA']} armB={receipt['refusal_slots']['armB']}")
    print(f"  assistant tokens (mean): A={receipt['assistant_token_mean']['armA']} "
          f"refusal={receipt['assistant_token_mean']['refusal_rows']} "
          f"replacement={receipt['assistant_token_mean']['replacement_rows']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
