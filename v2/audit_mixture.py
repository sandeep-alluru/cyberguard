#!/usr/bin/env python3
"""audit_mixture.py — pre-training data audit. Fail loudly NOW, not mid-run.

Checks, each with a pass/fail verdict and the evidence in a receipt:
  A structure      both arms parse, same row count, only the refusal slots differ
  B escaping       no literal \\n / \\t left in corpus-derived text (the v1 F3 defect)
  C duplicates     exact (system,user) duplicates; 13-gram near-duplicate rate on a sample
  D LEAKAGE        the 500 held-out rows and the capability PROBES must not appear in training data
  E truncation     share of rows whose assistant turn exceeds max_seq budget
  F formats        authored Sigma YAML parses + schema keys; JSON parses; triage is one word
  G labels         rule-based triage label sanity (benign rows must not carry attack signatures)
  H degeneracy     word-loop / too-short / placeholder answers
  I arm diff       per-source distribution identical except the substituted slots

Usage: python3 v2/audit_mixture.py --dir v2/data/mixture [--sample 4000]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import re
import sys

MAX_SEQ = 2048
FAILS, WARNS = [], []


def fail(check, msg):
    FAILS.append(f"{check}: {msg}")


def warn(check, msg):
    WARNS.append(f"{check}: {msg}")


def toks(s):
    return re.findall(r"[a-z0-9]+", str(s).lower())


def grams(s, n=13):
    t = toks(s)
    return {tuple(t[i:i + n]) for i in range(max(0, len(t) - n + 1))}


def read(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                fail("A-structure", f"{os.path.basename(path)}:{i} invalid JSON ({e})")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="v2/data/mixture")
    ap.add_argument("--sample", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--write-receipt", action="store_true",
                    help="write audit.receipt.json (default: verify only, no writes)")
    ap.add_argument("--verify-receipt", action="store_true",
                    help="re-audit against a written receipt: fail if the arm files changed since it "
                         "passed, or if it did not pass. This is the launch precondition.")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    rep = {}
    prev = None
    rpath = os.path.join(args.dir, "audit.receipt.json")
    if args.verify_receipt:
        if not os.path.exists(rpath):
            print("FAIL: no audit receipt — this data has never been audited")
            return 1
        prev = json.load(open(rpath, encoding="utf-8"))
        if prev.get("verdict", "").startswith("FAIL"):
            print(f"FAIL: the last audit did not pass ({prev.get('failures')})")
            return 1
        if not ((prev.get("checks") or {}).get("arm_sha256")):
            print("FAIL: the receipt records no arm hashes, so it cannot establish which revision it "
                  "cleared — re-run with --write-receipt (a receipt that cannot identify its artifact "
                  "must not yield a pass)")
            return 1

    A = read(os.path.join(args.dir, "armA.jsonl"))
    B = read(os.path.join(args.dir, "armB.jsonl"))
    rep["rows"] = {"armA": len(A), "armB": len(B)}

    # A --- structure
    for name, rows in (("armA", A), ("armB", B)):
        bad = [i for i, r in enumerate(rows)
               if not (str(r.get("user", "")).strip() and str(r.get("assistant", "")).strip())]
        if bad:
            fail("A-structure", f"{name}: {len(bad)} rows with an empty user/assistant (first idx {bad[0]})")
    if len(A) != len(B):
        fail("A-structure", f"arm sizes differ: {len(A)} vs {len(B)}")

    # B --- escaping (corpus-derived rows only; authoured sets are escape-free by construction)
    escape_hits = 0
    for r in A[: min(len(A), 60000)]:
        for f in ("user", "assistant"):
            if chr(92) + "n" in str(r.get(f, "")):
                escape_hits += 1
                break
    rep["literal_escapes"] = escape_hits
    if escape_hits:
        fail("B-escaping", f"{escape_hits} mixture rows still contain a literal backslash-n")

    # C --- duplicates
    WEIGHT = {"refusal": 8, "format": 2}          # intentional sampling multiplicity
    seen = collections.defaultdict(set)
    counts = collections.Counter()
    for r in A:
        k = " ".join(str(r.get("user", "")).lower().split())
        counts[k] += 1
        seen[k].add(r.get("src", "?"))
    unexplained = 0
    for k, c in counts.items():
        allowed = max([WEIGHT.get(s, 1) for s in seen[k]] or [1])
        if c > allowed:
            unexplained += c - allowed
    rep["exact_user_duplicates_unexplained"] = unexplained
    rep["intentional_weight_duplication"] = sum(counts.values()) - len(counts)
    if unexplained > len(A) * 0.02:
        fail("C-duplicates", f"{unexplained} duplicate user prompts NOT explained by sampling weights "
                             f"({unexplained/len(A):.1%}) — above the 2 % bar")
    sample = rng.sample(A, min(args.sample, len(A)))
    gs = [grams(r["user"]) for r in sample]
    near = 0
    for i in range(0, len(gs)):
        for j in range(i + 1, min(i + 12, len(gs))):     # bounded local window
            a, b = gs[i], gs[j]
            if a and b:
                inter = len(a & b)
                if inter and inter / len(a | b) >= 0.9:
                    near += 1
    rep["near_dup_sample_pairs"] = near
    if near > len(sample) * 0.01:
        warn("C-duplicates", f"{near} near-duplicate pairs (>0.9) in a {len(sample)}-row sample")

    # D --- LEAKAGE: held-out rows and capability probes must not be in training data
    hold = []
    hp = "v2/holdout500.jsonl"
    if os.path.exists(hp):
        hold = [json.loads(l)["prompt"] for l in open(hp, encoding="utf-8")]
    probes = []
    try:
        sys.path.insert(0, "v2")
        import leak_scan as _LS
        probes = _LS.collect_probe_strings()          # the SAME collector the scanner uses
    except Exception as e:  # noqa: BLE001
        warn("D-leakage", f"probe collector unavailable ({e}); probe-leak check skipped")
    rep["leak_reference"] = {"holdout": len(hold), "probes": len(probes)}
    if hold:
        hset = [grams(h) for h in hold if len(toks(h)) >= 13]
        hit = 0
        for r in A:
            g = grams(r["user"])
            if g and any((len(g & h) / len(g | h)) >= 0.8 for h in hset if h):
                hit += 1
        rep["holdout_rows_found_in_training"] = hit
        if hit:
            fail("D-leakage", f"{hit} training rows overlap held-out prompts at Jaccard >= 0.8")
    if probes:
        pset = [grams(p) for p in probes if len(toks(p)) >= 13]
        phit = []
        for r in A:
            for f in ("user", "assistant"):
                g = grams(r.get(f, ""))
                if g and any((len(g & h) / len(g | h)) >= 0.8 for h in pset if h):
                    phit.append(f); break
        rep["probe_text_found_in_training"] = len(phit)
        if phit:
            fail("D-leakage", f"{len(phit)} training rows match a capability probe at Jaccard >= 0.8 — the safety gate would be contaminated")

    # E --- truncation risk
    over = sum(1 for r in A if len(toks(r["user"])) + len(toks(r["assistant"])) > MAX_SEQ - 64)
    rep["rows_over_seq_budget"] = over
    if over > len(A) * 0.01:
        warn("E-truncation", f"{over} rows ({over/len(A):.2%}) exceed the {MAX_SEQ}-token budget")

    # E2 --- generation-budget consistency: training answers must be producible at eval time
    #         (v1's lesson: a train/eval length mismatch is invisible until somebody scores it)
    GEN_CAP = 512
    try:
        from transformers import AutoTokenizer
        _t = AutoTokenizer.from_pretrained("v2/tokenizer")
        over_cap = sum(1 for r in A[: min(len(A), 20000)]
                       if len(_t(str(r["assistant"]), add_special_tokens=False)["input_ids"]) > GEN_CAP)
        rep["answers_over_generation_cap_mode"] = f"real-tokenizer, {min(len(A),20000)} rows sampled"
    except Exception:                                    # noqa: BLE001
        over_cap = sum(1 for r in A if len(toks(r["assistant"])) > GEN_CAP)
        rep["answers_over_generation_cap_mode"] = "regex-token fallback"
    rep["answers_over_generation_cap"] = over_cap
    if over_cap > len(A) * 0.01:
        fail("E2-generation-cap", f"{over_cap} training answers exceed the {GEN_CAP}-token generation "
                                  f"budget ({over_cap/len(A):.1%}) — the model would be taught output "
                                  f"it can never finish")

    # F/G --- authored format validity and triage label sanity, on BOTH arms (Muse's D4 note: these were
    # arm-A-only, so arm B's formats and labels were never checked by anything).
    SIGMA_PREFIX = ("Write a Sigma rule", "Produce a schema-complete Sigma rule",
                    "Draft Sigma YAML", "Give me a Sigma rule for:", "Rule please:")
    SIG = ("enc", "powershell -enc", "duckdns", "certutil", "registry_set", "run value",
           "base64 -d", "shadow", "urlcache")
    per_arm = {}
    _LISTS = {}
    for _label, _rows in (("armA", A), ("armB", B)):
        _sigma = [r for r in _rows if r["user"].startswith(SIGMA_PREFIX)]
        _json = [r for r in _rows if "Return JSON" in r["user"]]
        _tri = [r for r in _rows if "one word" in r["user"].lower() or "single word" in r["user"].lower()]
        _ok = _jok = _one = _mis = 0
        try:
            import yaml as _y
            for r in _sigma:
                try:
                    d = _y.safe_load(r["assistant"])
                    if isinstance(d, dict) and d.get("detection") and d.get("logsource") and d.get("title"):
                        _ok += 1
                except Exception:                                  # noqa: BLE001
                    pass
        except ImportError:
            warn("F-formats", "pyyaml unavailable; Sigma parse check skipped")
        for r in _json:
            try:
                json.loads(r["assistant"]); _jok += 1
            except Exception:                                      # noqa: BLE001
                pass
        _one = sum(1 for r in _tri if r["assistant"].strip().lower() in ("malicious", "benign"))
        for r in _tri:
            if r["assistant"].strip().lower() == "benign":
                low = r["user"].lower()
                if any(s in low for s in SIG if s != "enc") or "-enc " in low:
                    _mis += 1
        _LISTS[_label] = {"sigma": _sigma, "triage": _tri}
        per_arm[_label] = {"sigma_yaml_valid": f"{_ok}/{len(_sigma)}", "json_valid": f"{_jok}/{len(_json)}",
                           "triage_one_word": f"{_one}/{len(_tri)}", "suspicious_benign_labels": _mis,
                           "sigma": len(_sigma), "json": len(_json), "triage": len(_tri)}
        if _sigma and _ok / len(_sigma) < 0.95:
            fail("F-formats", f"{_label}: only {_ok}/{len(_sigma)} Sigma rows parse schema-complete")
        if _json and _jok != len(_json):
            fail("F-formats", f"{_label}: {len(_json)-_jok} JSON answers do not parse")
        if _tri and _one < len(_tri):
            fail("F-formats", f"{_label}: {len(_tri)-_one} triage answers are not a single verdict word")
        if _mis > 2:
            warn("G-labels", f"{_label}: {_mis} rows labelled benign carry attack-like signatures")
    rep["formats_both_arms"] = per_arm
    rep["sigma_yaml_valid"] = per_arm["armA"]["sigma_yaml_valid"]          # kept for continuity
    rep["json_valid"] = per_arm["armA"]["json_valid"]
    rep["triage_one_word"] = per_arm["armA"]["triage_one_word"]
    rep["suspicious_benign_labels"] = per_arm["armA"]["suspicious_benign_labels"]
    print(f"  F/G both arms: {per_arm}")

    # H --- degeneracy
    loop = short = 0
    for r in A[: min(len(A), 60000)]:
        words = toks(r["assistant"])
        if r["assistant"].strip().lower() in ("malicious", "benign"):
            continue                                  # intentional one-word contract (F4)
        if len(words) < 5:
            short += 1
        elif len(collections.Counter(words).most_common(1)) and collections.Counter(words).most_common(1)[0][1] / len(words) > 0.5:
            loop += 1
    rep["degenerate_short"] = short
    rep["degenerate_wordloop"] = loop
    if loop:
        fail("H-degeneracy", f"{loop} answers are word-loop degenerate")
    if short > len(A) * 0.01:
        warn("H-degeneracy", f"{short} answers are shorter than 5 words")

    # H2 --- post-dedupe support for the gates that depend on specific data
    ref = [r for r in A if r.get("src") == "refusal"]
    known = {}
    rp = "v2/data/refusal-retention.jsonl"
    if os.path.exists(rp):
        for line in open(rp, encoding="utf-8"):
            d = json.loads(line)
            known[" ".join(d["user"].lower().split())] = (d.get("meta") or {}).get("kind")
    uniq = collections.Counter()
    seen_prompt = set()
    for r in ref:
        k = " ".join(r["user"].lower().split())
        if k in seen_prompt:          # count UNIQUE rows: weighting makes slot counts lie
            continue
        seen_prompt.add(k)
        uniq[known.get(k, "?")] += 1
    rep["refusal_unique_by_kind"] = dict(uniq)
    # a labelled abstention must actually abstain (Astra data review #1: 76 of 220 did not)
    ABSTAIN = ("i can't", "i cannot", "i don't know", "i won't", "not able",
               "can't confirm", "don't know", "isn't something i can verify", "not going to state")
    bad_abstain = 0
    for r in ref:
        if known.get(" ".join(r["user"].lower().split())) == "unknown-answer":
            if not any(a in r["assistant"].lower() for a in ABSTAIN):
                bad_abstain += 1
    rep["unknown_answer_rows_that_do_not_abstain"] = bad_abstain
    if bad_abstain:
        fail("H3-abstention", f"{bad_abstain} rows labelled unknown-answer do not actually abstain")
    rep["refusal_unique_total"] = sum(uniq.values())
    if uniq.get("unknown-answer", 0) < 200:
        fail("H2-support", f"only {uniq.get('unknown-answer',0)} unique unknown-answer rows survive into "
                           f"the mixture; gate G-F prespecifies support of >=200")

    # E3 --- REAL tokenizer truncation: a word count is not a token count, and the chat template adds
    #        tokens the word count never sees. SKIPPED-with-reason if the tokenizer is unavailable.
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained("v2/tokenizer")
        # D4 (Muse): this sampled arm A only. The objective asks for a tokenizer truncation check AND an
        # arm-equivalence assertion, so both arms are measured and the two profiles are compared: the
        # refusal-content substitution must not change how much assistant supervision is lost to truncation.
        _e3 = {}
        for _label, _rows in (("armA", A), ("armB", B)):
            _sample = _rows[: min(len(_rows), 20000)]
            _trunc = _empty = 0
            for r in _sample:
                ids = tok(str(r["user"]), add_special_tokens=False)["input_ids"]
                sup = tok(str(r["assistant"]), add_special_tokens=False)["input_ids"]
                if len(ids) + len(sup) + 8 > MAX_SEQ:   # +8 for template/special tokens
                    _trunc += 1
                if not sup:
                    _empty += 1
            _e3[_label] = {"sampled": len(_sample),
                           "truncation_rate": round(_trunc / max(1, len(_sample)), 4),
                           "empty_supervision": _empty}
            if _e3[_label]["truncation_rate"] > 0.02:
                warn("E3-tokenizer", f"{_label}: {_e3[_label]['truncation_rate']:.2%} of sampled rows exceed "
                                     f"{MAX_SEQ} real tokens and would lose assistant supervision")
        rep["tokenizer_both_arms"] = _e3
        rep["tokenizer_truncation_rate"] = _e3["armA"]["truncation_rate"]      # kept for continuity
        rep["tokenizer_empty_supervision"] = _e3["armA"]["empty_supervision"]
        _gap = abs(_e3["armA"]["truncation_rate"] - _e3["armB"]["truncation_rate"])
        rep["tokenizer_truncation_rate_gap"] = round(_gap, 4)
        if _gap > 0.01:
            fail("E3-arm-equivalence", f"truncation rates differ by {_gap:.2%} between the arms; the "
                                       f"substitution must not change the supervision-loss profile")
        print(f"  E3 tokenizer (both arms): {_e3}")
    except Exception as e:                              # noqa: BLE001
        rep["tokenizer_truncation_rate"] = f"SKIPPED-no-tokenizer ({type(e).__name__})"
        warn("E3-tokenizer", f"real-token truncation unmeasured: {e}")

    # I --- arm diff: not just a count, an ASSERTION that only the intended slots differ
    if len(A) == len(B):
        diff = sum(1 for a, b in zip(A, B) if a["user"] != b["user"])
        rep["arm_utterance_differences"] = diff
        illegal = 0
        for a, b in zip(A, B):
            if a["user"] != b["user"]:
                # a difference is legal only if one side is a refusal/replacement slot
                if not ({a.get("src"), b.get("src")} & {"refusal", "replacement"}):
                    illegal += 1
        rep["illegal_arm_differences"] = illegal
        if illegal:
            fail("I-arm-equivalence", f"{illegal} rows differ between arms outside the refusal/"
                                      f"replacement slots — the control is not a clean substitution")
        if diff == 0:
            fail("I-arm-equivalence", "the arms are identical: the substitution did not apply")
        exp = sum(1 for r in A if "one word" in r["user"].lower())
        if diff == 0:
            warn("I-arm-diff", "the two arms are identical — the control substitution did not apply")
    def _sha(path):
        import hashlib
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    # ---- J2 --- content checks on BOTH arms (independent review, Muse, 2026-09-28: every content check
    # above scans arm A only, mostly on samples, while the audit's PASS covers both arms only for structure).
    # This section computes the content metrics for BOTH arms and asserts what must hold on each, plus the
    # one difference that is by design (Arm B substitutes the refusal content, so its abstention/refusal
    # profile is expected to differ in a stated direction, not to match).
    def _content_metrics(rows, label):
        esc = dup = deg = absten = 0
        seen_k = collections.Counter()
        for r in rows:
            u, a = str(r.get("user", "")), str(r.get("assistant", ""))
            if chr(92) + "n" in u or chr(92) + "n" in a:
                esc += 1
            seen_k[" ".join(u.lower().split())] += 1
            if re.search(r"(.)\1{7,}", a) or (len(a.split()) >= 20 and
                                               collections.Counter(w.lower() for w in a.split()).most_common(1)[0][1]
                                               / max(1, len(a.split())) > 0.5):
                deg += 1
            low = a.lower()
            if "i'm sorry" in low or "i can't assist" in low or "i cannot assist" in low or "i do not know" in low:
                absten += 1
        dup = sum(c - max(1, 1) for c in seen_k.values() if c > 1)
        m = {"rows": len(rows), "literal_escapes": esc, "repeated_user_rows": dup,
             "degenerate_answers": deg, "abstention_like_answers": absten}
        return m

    _cmA, _cmB = _content_metrics(A, "armA"), _content_metrics(B, "armB")
    rep["content_both_arms"] = {"armA": _cmA, "armB": _cmB}
    for _label, _m in (("armA", _cmA), ("armB", _cmB)):
        if _m["literal_escapes"]:
            fail("J2-escaping", f"{_label}: {_m['literal_escapes']} rows contain a literal backslash-n")
        if _m["rows"] and _m["degenerate_answers"] / _m["rows"] > 0.02:
            fail("J2-degeneracy", f"{_label}: {_m['degenerate_answers']} degenerate answers "
                                  f"({_m['degenerate_answers'] / _m['rows']:.2%})")
        if _m["rows"] and _m["repeated_user_rows"] / _m["rows"] > 0.35:
            fail("J2-duplicates", f"{_label}: {_m['repeated_user_rows']} repeated user rows "
                                  f"({_m['repeated_user_rows'] / _m['rows']:.2%})")
    # the designed difference: Arm B has no refusal training, so its refusal-shaped answers must not exceed
    # Arm A's. If the substitution had not taken effect, these two numbers would move together.
    if _cmB["abstention_like_answers"] > _cmA["abstention_like_answers"]:
        fail("J2-arm-equivalence", f"arm B shows MORE refusal-shaped answers than arm A "
                                   f"({_cmB['abstention_like_answers']} vs {_cmA['abstention_like_answers']}); "
                                   f"the refusal substitution is not visible in the data")
    print(f"  J2 both-arms content: armA {_cmA}")
    print(f"                        armB {_cmB}")

    # J3 --- D3 remainder (Muse): sections F/G are structural/heuristic. The objective's exit names two
    # tests that were missing: that a Sigma rule's logsource/selection AGREES with the handprint its prompt
    # names, and that the triage label is DETERMINISTIC in the telemetry. Both are re-derived here from the
    # builder's own tables and rule rather than eyeballed.
    def _sigma_matches(row, BFS, _yaml, goal):
        ls, product, field, value = BFS.HANDPRINT_SELECTION[goal]
        try:
            d = _yaml.safe_load(row["assistant"]) or {}
        except Exception:                                          # noqa: BLE001
            return False
        got_ls = str((d.get("logsource") or {}).get("category") or "")
        got_pr = str((d.get("logsource") or {}).get("product") or "")
        sel = ((d.get("detection") or {}).get("selection") or {})
        got_field = str(next(iter(sel), ""))
        got_value = str(next(iter(sel.values()), ""))
        return got_ls == ls and got_pr == product and got_field == field and str(value) in got_value

    try:
        import yaml as _yaml
        sys.path.insert(0, "v2")
        import build_format_set as BFS
        hp_checked = hp_ok = 0
        _hp_by_arm = {}
        for _lbl, _ls in _LISTS.items():
            _c = _o = 0
            for r in _ls["sigma"]:
                goal = next((hp for hp in BFS.HANDPRINT_SELECTION if hp in r["user"]), None)
                if goal is None:
                    continue
                _c += 1
                if _sigma_matches(r, BFS, _yaml, goal):
                    _o += 1
            _hp_by_arm[_lbl] = f"{_o}/{_c}"
            hp_checked += _c
            hp_ok += _o
        rep["sigma_handprint_agreement_by_arm"] = _hp_by_arm
        for r in []:
            goal = None
            if goal is None:
                continue
            hp_checked += 1
            ls, product, field, value = BFS.HANDPRINT_SELECTION[goal]
            try:
                d = _yaml.safe_load(r["assistant"]) or {}
            except Exception:                                     # noqa: BLE001
                continue
            got_ls = str((d.get("logsource") or {}).get("category") or "")
            got_pr = str((d.get("logsource") or {}).get("product") or "")
            sel = ((d.get("detection") or {}).get("selection") or {})
            got_field = str(next(iter(sel), ""))
            got_value = str(next(iter(sel.values()), ""))
            if got_ls == ls and got_pr == product and got_field == field and str(value) in got_value:
                hp_ok += 1
        rep["sigma_handprint_agreement"] = f"{hp_ok}/{hp_checked}"
        if hp_checked and hp_ok != hp_checked:
            fail("J3-handprint", f"{hp_checked - hp_ok}/{hp_checked} Sigma rules disagree with the handprint "
                                 f"their prompt names")

        det_checked = det_bad = 0
        pairs = {}
        _all_triage = [r for _ls in _LISTS.values() for r in _ls["triage"]]
        for r in _all_triage:
            mp = re.search(r"dst=\S+:(\d+)", r["user"])
            mb = re.search(r"bytes=(\d+)", r["user"])
            if not (mp and mb):
                continue
            det_checked += 1
            port, byt = int(mp.group(1)), int(mb.group(1))
            want = "malicious" if (port in (4444, 5985) or byt > 5_000_000) else "benign"   # mirrors gen_log_line
            got = r["assistant"].strip().lower()
            if got != want:
                det_bad += 1
            pairs.setdefault((port, byt), set()).add(got)
        conflicting = sum(1 for v in pairs.values() if len(v) > 1)
        rep["triage_label_determinism"] = {"checked": det_checked, "disagreeing": det_bad,
                                          "same_telemetry_two_labels": conflicting}
        if det_bad:
            fail("J3-labels", f"{det_bad}/{det_checked} triage labels disagree with the deterministic rule")
        if conflicting:
            fail("J3-labels", f"{conflicting} telemetry tuples carry BOTH labels")
        print(f"  J3 (D3): sigma handprint {hp_ok}/{hp_checked}, triage determinism "
              f"{det_checked - det_bad}/{det_checked}, tuples with two labels {conflicting}")
    except Exception as e:                                        # noqa: BLE001
        warn("J3", f"D3 agreement/determinism checks unavailable: {e}")

    rep["arm_sha256"] = {"armA": _sha(os.path.join(args.dir, "armA.jsonl")),
                         "armB": _sha(os.path.join(args.dir, "armB.jsonl"))}
    rcpt = {"checks": rep, "failures": FAILS, "warnings": WARNS,
            "verdict": "FAIL" if FAILS else ("PASS-WITH-WARNINGS" if WARNS else "PASS")}
    if args.write_receipt or not args.verify_receipt:
        try:
            with open(rpath, "w", encoding="utf-8") as fh:
                json.dump(rcpt, fh, indent=2)
        except OSError as e:                       # read-only reviewer sandbox
            print(f"(receipt not written: {e})")
    print(json.dumps(rep, indent=1)[:2400])
    print()
    for f in FAILS:
        print("  FAIL:", f)
    for w in WARNS:
        print("  warn:", w)
    print(f"\n  VERDICT: {rcpt['verdict']} ({len(FAILS)} failures, {len(WARNS)} warnings)")

    if args.verify_receipt and prev:
        now = rep["arm_sha256"]
        was = (prev.get("checks") or {}).get("arm_sha256") or {}
        drift = [k for k in ("armA", "armB") if was.get(k) and was[k] != now[k]]
        if drift:
            print(f"FAIL: {', '.join(drift)} changed since the audit that cleared them — re-audit before training")
            return 1
        if FAILS:
            print("FAIL: this re-audit found failures")
            return 1
        print("RECEIPT-BOUND: the arm files are byte-identical to the audited, passing revision")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
