"""cap_scorers.py — pure scoring logic for the capability harness (no torch, unit-testable).

Every scorer is deterministic given (model_output, gold). Authority data (ATT&CK bundle,
NVD cache) is passed in as plain sets so this module runs anywhere.
"""
from __future__ import annotations
import json, re

CVE_RE = re.compile(r"\bCVE-(\d{4})-(\d{4,7})\b", re.IGNORECASE)
# review #4 MINOR: lowercase tid mentions ("t1059") must not be missed; canonicalize upper.
TID_RE = re.compile(r"\bT(\d{4})(\.\d{3})?\b", re.IGNORECASE)

def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    hw = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (round(max(0.0, c - hw), 4), round(min(1.0, c + hw), 4))

# ---------- authority loading (remote side) ----------
def load_tid_authority(stix_path: str):
    """Returns (valid_tids, deprecated_tids) from the MITRE attack-stix-data bundle."""
    valid, dep = set(), set()
    with open(stix_path) as f:
        bundle = json.load(f)
    for o in bundle.get("objects", []):
        if o.get("type") != "attack-pattern":
            continue
        for ref in o.get("external_references", []):
            if ref.get("source_name") == "mitre-attack" and ref.get("external_id"):
                tid = ref["external_id"]
                if o.get("deprecated"):
                    dep.add(tid)
                else:
                    valid.add(tid)
    return valid, dep

def norm_cve(s: str) -> str:
    m = CVE_RE.search(s)
    return f"CVE-{m.group(1)}-{m.group(2).lstrip('0').zfill(4)}" if m else ""

def extract_ids(text: str):
    cves = set()
    for m in CVE_RE.finditer(text or ""):
        # canonical form: digits int, min 4 (CVE-2021-0044 == CVE-2021-44); NVD cveId param
        # is exact-string, so all lookups must go through this normalization.
        cves.add(f"CVE-{m.group(1)}-{str(int(m.group(2))).zfill(4)}")
    tids = {f"T{m.group(1)}{(m.group(2) or '').upper()}".upper() for m in TID_RE.finditer(text or "")}
    return cves, tids

def factuality_score(gen: str, valid_tids, deprecated_tids, nvd_ok: set, nvd_checked: set):
    """Per-response ID facts. CVEs outside nvd_checked are 'unchecked' (API failed/limited),
    never counted as hallucinated — absence of evidence is not evidence of fabrication."""
    cves, tids = extract_ids(gen)
    tid_ok = {t for t in tids if t in valid_tids}
    tid_dep = {t for t in tids if t in deprecated_tids}
    tid_bad = {t for t in tids if t not in valid_tids and t not in deprecated_tids}
    cve_ok = {c for c in cves if c in nvd_ok}
    cve_bad = {c for c in cves if c in nvd_checked and c not in nvd_ok}
    cve_un = {c for c in cves if c not in nvd_checked}
    return {"cves": sorted(cves), "cve_ok": sorted(cve_ok), "cve_bad": sorted(cve_bad),
            "cve_unchecked": sorted(cve_un), "tids": sorted(tids), "tid_ok": sorted(tid_ok),
            "tid_deprecated": sorted(tid_dep), "tid_bad": sorted(tid_bad)}

# ---------- G1 triage ----------
def parse_triage(out: str):
    o = (out or "").strip().lower()
    m_bad = re.search(r"\b(malicious|phishing|spam|threat)\b", o[:60])
    m_ok = re.search(r"\bbenign\b|\bnot malicious\b|\bsafe\b|\blegitimate\b", o[:60])
    if m_bad and m_ok:
        return "malicious" if m_bad.start() <= m_ok.start() else "benign"
    if m_bad:
        return "malicious"
    if m_ok:
        return "benign"
    return "unparsed"

def triage_confusion(preds: list, golds: list):
    """gold in {malicious, benign}. Positive class = malicious.
    Review #4 MAJOR policy (declared): an unparsed output is a FAILURE of the task - counted as
    FP against benign gold and FN against malicious gold - while format_coverage is reported
    separately so the reader can see how much of the rate came from format vs label errors."""
    tp = fp = fn = tn = unp = 0
    for p, g in zip(preds, golds):
        if p == "unparsed":
            unp += 1
            if g == "malicious":
                fn += 1
            else:
                fp += 1
            continue
        if g == "malicious" and p == "malicious": tp += 1
        elif g == "benign" and p == "malicious": fp += 1
        elif g == "malicious" and p == "benign": fn += 1
        else: tn += 1
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    n = len(preds)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "unparsed": unp,
            "format_coverage": round((n - unp) / n, 4) if n else None,
            "precision": round(prec, 4), "recall": round(rec, 4), "fpr": round(fpr, 4),
            "precision_wilson95": wilson(tp, tp + fp)}

# ---------- G2 IOC extraction ----------
IOC_PATTERNS = {
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "domain": re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|io|ru|cn|xyz|top|info|biz|co|tk|ml|ga|cf|gq|local|internal|gov|edu)\b"),
    "url": re.compile(r"https?://[^\s\"'<>)}\]]+"),
    "email": re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b"),
    "hash": re.compile(r"\b(?:[a-f0-9]{32}|[a-f0-9]{64})\b"),
}
def extract_iocs(text: str) -> set:
    t = (text or "").lower()
    urls = {m.group(0).rstrip(".,;:") for m in IOC_PATTERNS["url"].finditer(t)}
    found = set()
    for kind, pat in IOC_PATTERNS.items():
        for m in pat.finditer(t):
            v = m.group(0).rstrip(".,;:")
            if kind == "ip" and any(int(x) > 255 for x in v.split(".")):
                continue
            # review #4 MAJOR: a URL also yields its host as a domain/ip prediction. Canonical
            # representation = the URL; drop the embedded host unless it ALSO appears outside
            # every URL in the text (then it is a genuine separate IOC).
            if kind in ("domain", "ip") and any(v in u for u in urls):
                stripped = t
                for u in urls:
                    stripped = stripped.replace(u, " ")
                if v not in stripped:
                    continue
            found.add(v)
    return found

def ioc_score(gen: str, gold: set, source_text: str):
    """predicted = IOCs in model output; fabricated = predicted IOC not present in the input
    report at all (invention); wrong-but-present = in text, not gold (mislabel)."""
    src = (source_text or "").lower()
    pred = extract_iocs(gen)
    gold = {g.lower() for g in gold}
    tp = pred & gold
    fabricated = {p for p in pred - gold if p not in src}
    mislabel = pred - gold - fabricated
    prec = len(tp) / len(pred) if pred else 0.0
    rec = len(tp) / len(gold) if gold else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"pred": len(pred), "gold": len(gold), "tp": len(tp),
            "fabricated": sorted(fabricated), "mislabel": sorted(mislabel)[:10],
            "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4)}

# ---------- G3 sigma ----------
SIGMA_REQUIRED = ("title", "logsource", "detection")
def sigma_validate(gen: str):
    """Returns (yaml_ok, schema_ok, detail). Review #4 MAJOR: evaluate ALL candidate blocks and
    keep the best rule (an invalid first block must not mask a valid later one); 'schema_ok'
    requires detection to be a MAPPING with a real 'condition' key, not the substring."""
    import yaml
    blocks = re.findall(r"```(?:yaml|yml)?\s*\n(.*?)```", gen or "", re.S)
    candidates = blocks + ([gen] if gen else [])
    yaml_ok = False
    best = (False, False, "no-parseable-yaml")
    for cand in candidates:
        try:
            doc = yaml.safe_load(cand)
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        yaml_ok = True
        missing = [k for k in SIGMA_REQUIRED if k not in doc]
        det = doc.get("detection")
        det_ok = isinstance(det, dict) and "condition" in det
        if not missing and det_ok:
            return True, True, "ok"
        if yaml_ok and not best[1]:
            best = (True, False, f"missing:{missing or 'condition'}")
    return best if not yaml_ok else (True, best[1], best[2])

def pysigma_compile(rule_dict) -> tuple[bool, str]:
    try:
        from sigma.collection import SigmaCollection
        sc = SigmaCollection.from_dict(rule_dict)
        sc.resolve_backend(None) if hasattr(sc, "resolve_backend") else None
        # parse-only validation (no backend execution): constructing + checking detection
        return True, "parsed"
    except Exception as e:
        return False, repr(e)[:120]

# ---------- G7 ----------
def gsm_extract(out: str):
    """Review #4 BLOCKER: strict LAST-LINE extraction. A number from truncated reasoning can no
    longer pass as the answer: with the answer-only prompt, a truncation yields no parseable
    last line -> None -> counted wrong (fail-closed)."""
    lines = [l.strip() for l in (out or "").splitlines() if l.strip()]
    if not lines:
        return None
    nums = re.findall(r"-?\d[\d,]*\.?\d*", lines[-1])
    if len(nums) != 1:  # ambiguous last line (0 numbers, or reasoning with several) -> reject
        return None
    n = nums[0].replace(",", "")
    try:
        f = float(n)
        return int(f) if f == int(f) else f
    except ValueError:
        return None

def gsm_gold(answer: str):
    m = re.search(r"####\s*(-?\d[\d,]*\.?\d*)", answer or "")
    if not m:
        return None
    n = m.group(1).replace(",", "")
    f = float(n)
    return int(f) if f == int(f) else f

# IFEval-lite: deterministic checkers over the raw response.
def ifeval_check(out: str, kind: str, param) -> bool:
    o = (out or "").strip()
    if not o:
        return False
    if kind == "start_with":
        return o.lower().startswith(str(param).lower())
    if kind == "end_with":
        return o.rstrip().lower().endswith(str(param).lower())
    if kind == "include_keyword":
        return str(param).lower() in o.lower()
    if kind == "forbid_keyword":
        return str(param).lower() not in o.lower()
    if kind == "n_words_range":
        n = len(o.split())
        return param[0] <= n <= param[1]
    if kind == "n_sentences":
        n = max(len(re.findall(r"[.!?]", o)), 1)
        return n == int(param)
    if kind == "line_count":
        return len([l for l in o.splitlines() if l.strip()]) == int(param)
    if kind == "uppercase":
        letters = [c for c in o if c.isalpha()]
        return bool(letters) and all(c.isupper() for c in letters)
    if kind == "json_object":
        try:
            m = re.search(r"\{.*\}", o, re.S)
            return bool(m) and isinstance(json.loads(m.group(0)), dict)
        except Exception:
            return False
    if kind == "json_keys":  # review #4: enforce the keys the instruction actually asked for
        try:
            m = re.search(r"\{.*\}", o, re.S)
            doc = json.loads(m.group(0)) if m else None
            return isinstance(doc, dict) and all(k in doc for k in param)
        except Exception:
            return False
    if kind == "bullet_list":  # exact count when param given (review #4: no free-pass 3+)
        lines = [l.strip() for l in o.splitlines() if l.strip()]
        bullets = [l for l in lines if l.startswith(("- ", "* ", "• "))]
        return len(bullets) == int(param) if param else len(bullets) >= 3
    return False
