#!/usr/bin/env python3
"""CyberGuard v3 — Phase 2 validation for the teacher-trail deliverable.

Checks, per the owner's resume prompt:

  1. Each trail file: ids exactly k0001..k7000 once each; every trail contains the
     exact marker `</think>`; no credential-like strings; tool_calls == 0;
     the stored `prompt` is byte-identical to the canonical prompts-7k.jsonl text.
  2. Cross-teacher: identical prompt id sets; no id present that is not in the
     canonical prompt set.
  3. Base SFT: row counts match data/v3/sft/SFT_MANIFEST.md (127,767).

Writes data/v3/trails-30/VALIDATION-REPORT.md with pass/fail and exact counts,
and data/v3/trails-30/supervisor/repair-targets-<teacher>.txt listing ids that
need regeneration (missing or missing-marker). Never prints credential values.
"""
import hashlib
import json
import os
import re
import sys

BASE = os.path.expanduser("~/AgentHub/cyberguard/data/v3/trails-30")
SFT = os.path.expanduser("~/AgentHub/cyberguard/data/v3/sft")
REPORT = os.path.join(BASE, "VALIDATION-REPORT.md")
SUP = os.path.join(BASE, "supervisor")
PROMPTS = os.path.join(BASE, "prompts-7k.jsonl")
MARKER = "</think>"
TOTAL = 7000

# Teachers whose rows are NOT admitted to the mixture (owner decision 2026-09-30:
# Muse retired on measured throughput; its rows are retained on disk only). Their
# files are still reported for the record, but their checks do not gate admission.
RETIRED = {"muse"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redact_secrets import redact_text  # noqa: E402

TEACHERS = {
    "deepseek": os.path.join(BASE, "trails_deepseek_7k.jsonl"),
    "muse": os.path.join(BASE, "trails_muse_7k.jsonl"),
}
# From SFT_MANIFEST.md (authoritative expected counts)
SFT_EXPECT = {"fenrir.jsonl": 99730, "merged.jsonl": 23146, "primus.jsonl": 4891}
SFT_TOTAL = 127767

CRED_PATTERNS = [
    ("openai-style key", re.compile(r"sk-[A-Za-z0-9_\-]{16,}")),
    ("api key assignment", re.compile(r"(?i)api[_-]?key\s*[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{16,}")),
    ("bearer token", re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}")),
    ("aws access key id", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("aws secret", re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*\S{20,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("generic long secret", re.compile(r"(?i)(secret|token|password)\s*[:=]\s*[\"']?[A-Za-z0-9/+=_\-]{24,}")),
]


def load_canonical():
    ids, prompts = [], {}
    with open(PROMPTS, "rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            ids.append(d["id"])
            prompts[d["id"]] = d["prompt"]
    return ids, prompts


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def check_teacher(name, path, canon_ids, canon_prompts):
    r = {"name": name, "path": path, "exists": os.path.exists(path)}
    if not r["exists"]:
        r["fatal"] = "file missing"
        return r
    records = 0
    unparsable = 0
    ids = []
    by_id = {}
    missing_marker = []
    bad_toolcalls = []
    bad_prompt = []
    cred_hits = []
    schema_bad = []
    trail_chars = 0
    models = {}
    with open(path, "rb") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            records += 1
            try:
                d = json.loads(line)
            except Exception:
                unparsable += 1
                continue
            for k in ("id", "prompt", "trail", "gen_ms", "model", "tool_calls"):
                if k not in d:
                    schema_bad.append((lineno, "missing key %s" % k))
                    break
            rid = d.get("id")
            ids.append(rid)
            by_id.setdefault(rid, []).append(d)
            trail = d.get("trail") or ""
            trail_chars += len(trail)
            if MARKER not in trail:
                missing_marker.append(rid)
            if d.get("tool_calls") != 0:
                bad_toolcalls.append(rid)
            if rid in canon_prompts and d.get("prompt") != redact_text(canon_prompts[rid])[0]:
                bad_prompt.append(rid)
            models[d.get("model", "?")] = models.get(d.get("model", "?"), 0) + 1
            for label in (redact_text(trail)[1], redact_text(d.get("prompt") or "")[1]):
                if label:
                    cred_hits.append((rid, ",".join(sorted(label))))
                    break

    uniq = set(ids)
    dups = sorted({i for i in ids if ids.count(i) > 1})
    canon = set(canon_ids)
    r.update({
        "records": records,
        "unparsable": unparsable,
        "unique_ids": len(uniq),
        "duplicate_ids": dups,
        "duplicate_record_count": records - len(uniq) - unparsable,
        "missing_ids": sorted(canon - uniq),
        "foreign_ids": sorted(uniq - canon),
        "missing_marker": sorted(set(missing_marker)),
        "bad_toolcalls": sorted(set(bad_toolcalls)),
        "prompt_mismatch": sorted(set(bad_prompt)),
        "credential_hits": cred_hits[:20],
        "credential_hit_count": len(cred_hits),
        "schema_violations": schema_bad[:20],
        "schema_violation_count": len(schema_bad),
        "models": models,
        "mean_trail_chars": round(trail_chars / records, 1) if records else 0,
        "sha256": sha256(path),
    })
    os.makedirs(SUP, exist_ok=True)
    targets = sorted(set(r["missing_ids"]) | set(r["missing_marker"]))
    with open(os.path.join(SUP, "repair-targets-%s.txt" % name), "w") as f:
        for i in targets:
            f.write(i + "\n")
    r["repair_target_count"] = len(targets)
    return r


def check_sft():
    out = {}
    for fn, expect in SFT_EXPECT.items():
        p = os.path.join(SFT, fn)
        n = 0
        if os.path.exists(p):
            with open(p, "rb") as f:
                for line in f:
                    if line.strip():
                        n += 1
        out[fn] = {"rows": n, "expected": expect, "match": n == expect}
    out["_total"] = {"rows": sum(v["rows"] for k, v in out.items() if not k.startswith("_")),
                     "expected": SFT_TOTAL}
    out["_total"]["match"] = out["_total"]["rows"] == SFT_TOTAL
    return out


def main():
    canon_ids, canon_prompts = load_canonical()
    results = {n: check_teacher(n, p, canon_ids, canon_prompts) for n, p in TEACHERS.items()}
    sft = check_sft()

    ds, mu = results["deepseek"], results["muse"]
    checks = []

    def chk(label, ok, detail):
        checks.append((label, bool(ok), detail))

    for n, r in results.items():
        if r.get("fatal"):
            chk("%s: file present" % n, False, r["fatal"])
            continue
        if n in RETIRED:
            chk("%s: NOT ADMITTED (retired by owner decision 2026-09-30)" % n, True,
                "rows=%d retained on disk and excluded from the admitted block; its checks are "
                "reported for the record only" % r["records"])
            continue
        chk("%s: all 7000 ids present exactly once" % n,
            r["unique_ids"] == TOTAL and not r["duplicate_ids"] and not r["missing_ids"],
            "unique=%d missing=%d duplicate_ids=%d" % (r["unique_ids"], len(r["missing_ids"]),
                                                       len(r["duplicate_ids"])))
        chk("%s: every trail contains </think>" % n, not r["missing_marker"],
            "missing_marker=%d" % len(r["missing_marker"]))
        chk("%s: tool_calls == 0 for all rows" % n, not r["bad_toolcalls"],
            "violations=%d" % len(r["bad_toolcalls"]))
        chk("%s: no value-bearing credential material (§3 definition)" % n,
            r["credential_hit_count"] == 0, "hits=%d" % r["credential_hit_count"])
        chk("%s: stored prompt matches the frozen set (credential-redaction aware)" % n,
            not r["prompt_mismatch"], "mismatches=%d" % len(r["prompt_mismatch"]))
        chk("%s: no foreign ids (all ids from prompts-7k)" % n, not r["foreign_ids"],
            "foreign=%d" % len(r["foreign_ids"]))
        chk("%s: schema complete on every row" % n, r["schema_violation_count"] == 0,
            "violations=%d" % r["schema_violation_count"])

    active = [n for n in results if n not in RETIRED and not results[n].get("fatal")]
    if len(active) > 1:
        a, b = active[0], active[1]
        chk("cross-teacher: identical available id sets",
            set(results[a]["missing_ids"]) == set(results[b]["missing_ids"]),
            "%s_missing=%d %s_missing=%d" % (a, len(results[a]["missing_ids"]),
                                             b, len(results[b]["missing_ids"])))
    else:
        chk("cross-teacher comparison", True,
            "n/a — one admitted teacher (%s); Muse is retired and not admitted"
            % (active[0] if active else "none"))

    # Admission companions: A7 content audit and the §3 contamination gate.
    audit_path = os.path.join(BASE, "CONTENT-QUALITY-AUDIT.json")
    if os.path.exists(audit_path):
        try:
            au = json.load(open(audit_path))
            chk("A7: teacher-content quality audit", au.get("verdict") == "PASS",
                "verdict=%s sample=%s" % (au.get("verdict"), au.get("sample_n")))
        except Exception as e:
            chk("A7: teacher-content quality audit", False, "unreadable: %s" % e)
    else:
        chk("A7: teacher-content quality audit", False,
            "CONTENT-QUALITY-AUDIT.json absent — A7 not yet measured, block not admittable")

    gate_path = os.path.join(BASE, "ADMISSION-GATE-RECEIPT.json")
    if os.path.exists(gate_path):
        try:
            g = json.load(open(gate_path))
            chk("§3 admission gate (13-gram Jaccard + verbatim containment)", g.get("hits") == 0,
                "hits=%s rows_checked=%s jaccard_max=%s" % (g.get("hits"), g.get("rows_checked"),
                                                            g.get("jaccard_max")))
        except Exception as e:
            chk("§3 admission gate", False, "unreadable: %s" % e)
    else:
        chk("§3 admission gate", False, "ADMISSION-GATE-RECEIPT.json absent — gate not yet run")

    chk("base SFT row counts match SFT_MANIFEST.md (127,767)",
        sft["_total"]["match"] and all(v["match"] for k, v in sft.items() if not k.startswith("_")),
        "total=%d expected=%d | %s" % (sft["_total"]["rows"], SFT_TOTAL,
                                       ", ".join("%s=%d/%d" % (k, v["rows"], v["expected"])
                                                 for k, v in sft.items() if not k.startswith("_"))))

    overall = all(ok for _, ok, _ in checks)

    lines = []
    lines.append("# VALIDATION-REPORT — CyberGuard v3 teacher trails + base SFT")
    lines.append("")
    lines.append("**Generated:** %s (by `tools/validate_trails.py`)" % __import__("time").strftime("%Y-%m-%d %H:%M:%S %Z"))
    lines.append("**Overall verdict:** %s" % ("**PASS**" if overall else "**FAIL**"))
    lines.append("")
    lines.append("## Check results")
    lines.append("")
    lines.append("| # | check | result | detail |")
    lines.append("|---|---|---|---|")
    for i, (label, ok, detail) in enumerate(checks, 1):
        lines.append("| %d | %s | %s | %s |" % (i, label, "PASS" if ok else "FAIL", detail))
    lines.append("")
    lines.append("## Exact counts")
    lines.append("")
    lines.append("| teacher | records | unique ids | duplicate ids | missing ids | missing `</think>` | tool_calls≠0 | prompt mismatches | credential hits | mean trail chars | sha256 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for n, r in results.items():
        if r.get("fatal"):
            lines.append("| %s | — | — | — | — | — | — | — | — | — | — |" % n)
            continue
        lines.append("| %s | %d | %d | %d | %d | %d | %d | %d | %d | %s | `%s` |" % (
            n, r["records"], r["unique_ids"], len(r["duplicate_ids"]), len(r["missing_ids"]),
            len(r["missing_marker"]), len(r["bad_toolcalls"]), len(r["prompt_mismatch"]),
            r["credential_hit_count"], r["mean_trail_chars"], r["sha256"][:16]))
    lines.append("")
    lines.append("Model ids returned by the providers:")
    for n, r in results.items():
        if not r.get("fatal"):
            lines.append("- %s: %s" % (n, r["models"]))
    lines.append("")
    lines.append("## Base SFT")
    lines.append("")
    lines.append("| file | rows | expected (SFT_MANIFEST.md) | match |")
    lines.append("|---|---|---|---|")
    for k, v in sft.items():
        if k.startswith("_"):
            continue
        lines.append("| %s | %d | %d | %s |" % (k, v["rows"], v["expected"], "yes" if v["match"] else "NO"))
    lines.append("| **total** | **%d** | **%d** | **%s** |" % (sft["_total"]["rows"], SFT_TOTAL,
                                                                 "yes" if sft["_total"]["match"] else "NO"))
    lines.append("")
    lines.append("## Repair targets")
    lines.append("")
    for n, r in results.items():
        if not r.get("fatal"):
            lines.append("- %s: %d ids need (re)generation — `supervisor/repair-targets-%s.txt` "
                         "(missing %d, marker-absent %d)"
                         % (n, r["repair_target_count"], n, len(r["missing_ids"]),
                            len(r["missing_marker"])))
    lines.append("")
    lines.append("## Method notes")
    lines.append("")
    lines.append("- `prompt` identity is checked against `prompts-7k.jsonl` (the frozen **generation-time** prompt set),")
    lines.append("  after applying the same credential-redaction function to the canonical text: the frozen set records what")
    lines.append("  the teacher was shown, while the training artifact is credential-redacted (§3).")
    lines.append("- Muse rows are retained on disk but are **not admitted** (retired by owner decision 2026-09-30);")
    lines.append("  their checks are reported for the record and do not gate admission.")
    lines.append("- Admission also requires A7 (content-quality audit) and the §3 contamination gate; both are")
    lines.append("  listed as checks above and are read from their receipts.")
    lines.append("- Credential scan uses generic key/token patterns only; no credential value is read or written.")
    lines.append("- Files are validated in place; no row is modified by this script.")
    lines.append("")
    with open(REPORT, "w") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
