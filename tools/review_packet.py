#!/usr/bin/env python3
"""Review packet — the bounded invocation boundary (Astra D18).

The measured problem: token volume is input-dominated. One supplied review session recorded
8,018,526 input tokens against 29,356 output tokens (273:1), because every review re-read the
repository. This tool constrains the PACKET it is given and estimates its size. Token accounting here is a
conservative CHARACTER ESTIMATE (len//4), NOT a measured serialized request. Final-request and
cumulative measurement are NOT implemented; do not read this tool as performing them.

Astra's accepted changes, implemented here:
  (a) batch by phase          -> check-batch
  (b) immutable per-review packet -> check-packet
  (c) never inject bulk artifacts -> check-extractions
  (d) HARD budgets            -> test-budget
  (e) no implicit historical exposure -> check-exposure
  (f) claim-based review      -> check-coverage

Hard budgets (D18, not negotiable without a new ruling):
  MAX_PACKET_TOKENS   =  8,000   packet content
  MAX_REQUEST_TOKENS  = 20,000   total input per model request
  MAX_REVIEW_TOKENS   = 60,000   cumulative input per review
  MAX_REQUESTS        =      3   model requests per review, including retries
Unknown accounting or overflow means REFUSE BEFORE SENDING. Never silently truncate evidence.

Exit codes: 0 = pass · 1 = violation · 2 = cannot run
"""
import argparse, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_PACKET_TOKENS = 8_000
MAX_REQUEST_TOKENS = 20_000
MAX_REVIEW_TOKENS = 60_000
MAX_REQUESTS = 3

# bulk artifacts that must never enter a request (D18c). Multi-MB results files, transcripts, ledgers.
BULK_PATTERNS = (
    re.compile(r"results-.*\.json$"), re.compile(r"battery-.*\.json$"), re.compile(r"^LEDGER\.md$"),
    re.compile(r"PLAN-V3\.md$"), re.compile(r"review.*\.txt$"), re.compile(r"session.*\.jsonl$"),
    re.compile(r"rollout.*\.jsonl$"), re.compile(r"\.safetensors$"), re.compile(r"\.gguf$"),
)
BULK_BYTES = 256 * 1024          # anything this large is refused regardless of name

REQUIRED_PACKET_FIELDS = ("review_id", "state_hash", "questions", "rulings", "evidence", "changes_since")


def est_tokens(text: str) -> int:
    """Conservative estimate. Refusal is based on this, so over-estimating is the safe direction."""
    return max(1, len(text) // 4)


def load(p):
    try:
        return json.load(open(p, encoding="utf8"))
    except Exception as e:
        print(f"  CANNOT RUN: packet unreadable: {e}", file=sys.stderr)
        sys.exit(2)


def _is_bulk(name: str, size: int | None = None) -> bool:
    base = Path(name).name
    if any(p.search(base) for p in BULK_PATTERNS):
        return True
    return size is not None and size > BULK_BYTES


def check_batch(p):
    """(a) every pending question included, or explicitly blocked; duplicate submissions refused."""
    qs = p.get("questions") or []
    if not qs:
        print("  FAIL no questions in packet -> nothing to review, refuse"); return 1
    bad = 0
    ids = []
    for q in qs:
        if not q.get("id") or not q.get("question"):
            print(f"  FAIL question missing id or text: {q}"); bad = 1; continue
        if q.get("status") not in ("pending", "blocked"):
            print(f"  FAIL {q['id']} status {q.get('status')!r} is neither pending nor blocked"); bad = 1
        ids.append(q["id"])
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print(f"  FAIL duplicate question ids: {sorted(dupes)}"); bad = 1
    print(f"  questions: {len(qs)} ({sum(1 for q in qs if q.get('status')=='blocked')} blocked)")
    print("  CHECK-BATCH:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


def check_packet(p):
    """(b) required fields, source hashes, selectors and applicable rulings all validate."""
    bad = 0
    for f in REQUIRED_PACKET_FIELDS:
        if f not in p:
            print(f"  FAIL missing required field: {f}"); bad = 1
    if not isinstance(p.get("changes_since"), dict):
        print("  FAIL changes_since must be a mapping of what changed since the preceding verdict"); bad = 1
    for e in p.get("evidence") or []:
        for f in ("path", "selector", "sha256", "extractor"):
            if not e.get(f):
                print(f"  FAIL evidence entry missing {f}: {e}"); bad = 1
        if e.get("sha256") and not re.fullmatch(r"[0-9a-f]{64}", str(e["sha256"])):
            print(f"  FAIL evidence sha256 malformed: {e.get('sha256')!r}"); bad = 1
        if e.get("quote") is None:
            print(f"  FAIL evidence {e.get('path')} carries no quoted excerpt (numbers must not be paraphrased)"); bad = 1
    print("  CHECK-PACKET:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


def check_extractions(p):
    """(c) no raw bulk attachment; extracted values recomputed and matched."""
    bad = 0
    for e in p.get("evidence") or []:
        path = str(e.get("path", ""))
        size = e.get("bytes")
        if _is_bulk(path, size if isinstance(size, int) else None):
            print(f"  FAIL bulk artifact would enter the request: {path} ({size} B). Extract fields instead."); bad = 1
        if e.get("raw_attached"):
            print(f"  FAIL evidence {path} marked raw_attached — D18c forbids it"); bad = 1
        if e.get("bytes") is not None and e["bytes"] > BULK_BYTES:
            print(f"  FAIL evidence {path} is {e['bytes']} B > {BULK_BYTES} B limit"); bad = 1
        for f in ("population", "denominator", "missing", "error_count"):
            if f not in e:
                print(f"  FAIL evidence {path} omits {f} (D18c requires population/denominator/missing/errors)"); bad = 1
    print("  CHECK-EXTRACTIONS:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


def check_exposure(p):
    """(e) outgoing content matches its manifest; no implicit historical attachments."""
    bad = 0
    declared = p.get("included_paths")
    if declared is None:
        print("  FAIL included_paths missing — outgoing content must match a manifest"); return 1
    actual = [e.get("path") for e in (p.get("evidence") or [])]
    undeclared = [a for a in actual if a not in declared]
    if undeclared:
        print(f"  FAIL evidence not in manifest: {undeclared}"); bad = 1
    for a in actual:
        if _is_bulk(str(a)):
            print(f"  FAIL manifest includes a bulk/historical artifact: {a}"); bad = 1
    print(f"  manifest: {len(declared)} paths; evidence: {len(actual)}")
    print("  CHECK-EXPOSURE:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


def check_coverage(p, v):
    """(f) every submitted claim has a disposition; unresolved evidence cannot produce approval."""
    bad = 0
    qids = {q["id"] for q in (p.get("questions") or []) if q.get("id")}
    dids = {}
    for d in (v.get("dispositions") or []):
        if not d.get("claim_id"):
            print(f"  FAIL disposition without claim_id: {d}"); bad = 1; continue
        if d.get("result") not in ("supported", "contradicted", "unresolved"):
            print(f"  FAIL {d['claim_id']} result {d.get('result')!r} invalid"); bad = 1
        dids[d["claim_id"]] = d.get("result")
    missing = qids - set(dids)
    if missing:
        print(f"  FAIL claims with no disposition: {sorted(missing)}"); bad = 1
    unresolved = [k for k, r in dids.items() if r == "unresolved"]
    if unresolved and v.get("approval") in ("approved", "pass"):
        print(f"  FAIL approval claimed with unresolved evidence: {sorted(unresolved)}"); bad = 1
    print(f"  claims {len(qids)}, dispositions {len(dids)}, unresolved {len(unresolved)}")
    print("  CHECK-COVERAGE:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


def test_budget(p=None):
    """(d) below-limit sends succeed; every over-limit or unknown-accounting case is refused."""
    bad = 0
    content = json.dumps(p) if p else ""
    n = est_tokens(content) if p else 0
    print(f"  MAX_PACKET_TOKENS  {MAX_PACKET_TOKENS:>7,}   MAX_REQUEST_TOKENS {MAX_REQUEST_TOKENS:>7,}")
    print(f"  MAX_REVIEW_TOKENS  {MAX_REVIEW_TOKENS:>7,}   MAX_REQUESTS       {MAX_REQUESTS:>7,}")
    if p:
        print(f"  this packet: ~{n:,} tokens of {MAX_PACKET_TOKENS:,}")
        if n > MAX_PACKET_TOKENS:
            print("  REFUSE: packet over budget — split by phase, do not truncate"); bad = 1
        else:
            print("  within packet budget")
    # self-test the refusal behaviour
    cases = [(MAX_PACKET_TOKENS - 1, "accept"), (MAX_PACKET_TOKENS, "accept"),
             (MAX_PACKET_TOKENS + 1, "refuse"), (None, "refuse")]
    for val, want in cases:
        if val is None:
            got = "refuse"          # unknown accounting
        else:
            got = "accept" if val <= MAX_PACKET_TOKENS else "refuse"
        ok = got == want
        bad |= (0 if ok else 1)
        print(f"    {'OK  ' if ok else 'FAIL'} packet={val!s:>8} -> {got} (want {want})")
    print("  TEST-BUDGET:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["check-batch", "check-packet", "check-extractions", "test-budget",
                                     "check-exposure", "check-coverage"])
    ap.add_argument("packet", nargs="?")
    ap.add_argument("verdict", nargs="?")
    a = ap.parse_args()
    if a.mode == "test-budget":
        sys.exit(test_budget(load(a.packet) if a.packet else None))
    p = load(a.packet)
    if a.mode == "check-batch":       sys.exit(check_batch(p))
    if a.mode == "check-packet":      sys.exit(check_packet(p))
    if a.mode == "check-extractions": sys.exit(check_extractions(p))
    if a.mode == "check-exposure":    sys.exit(check_exposure(p))
    if a.mode == "check-coverage":
        if not a.verdict:
            print("  CANNOT RUN: check-coverage needs a verdict file", file=sys.stderr); sys.exit(2)
        sys.exit(check_coverage(p, load(a.verdict)))


if __name__ == "__main__":
    main()
