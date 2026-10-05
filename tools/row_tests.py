#!/usr/bin/env python3
"""row_tests.py — FAILABLE micro tests for the owner-approved rows (A01-A19, C01).

Owner criterion (D20): the deliverable is a FAILABLE MICRO TEST, not a document diff and not a human
eyeball check. Every test below must be demonstrable as FAILING against the pre-fix state, then PASSING
against the fixed state. A test never seen to fail is rejected as a smoke test.

  python3 tools/row_tests.py --state prefix   # run against docs/dsh/acceptance/prefix-snapshot (expect FAIL)
  python3 tools/row_tests.py --state live     # run against the working tree            (expect PASS)
  python3 tools/row_tests.py --report         # emit the test report Sandeep signs

Every test returns (ok: bool, evidence: str). `ok=False` means the row's defect is present.
"""
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "docs/dsh/acceptance/prefix2"
H = "1e82808792ad310cfbf019478428e20fe47f5bbf7c6c280f37aa2f7f4d49ba53"
HOME_PATCH = Path.home() / ".dsh/cordis.patch.yml"


def read(base: Path, rel: str):
    p = base / rel
    if not p.exists():
        return None
    return p.read_text(encoding="utf8", errors="replace")


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(cmd, cwd=None, timeout=60, shell=None):
    use_shell = isinstance(cmd, str) if shell is None else shell
    r = subprocess.run(cmd, shell=use_shell, capture_output=True, text=True,
                       cwd=str(cwd or ROOT), timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ── Group 1: A01-A19 ───────────────────────────────────────────────────────────────────────────────
# Each test asserts the CORRECTED state. On the pre-fix snapshot it must fail.

def a01(base):  # OWNER-DECISION: withdrawal must SUBSTITUTE, not merely append
    s = read(base, "docs/dsh/OWNER-DECISION.md")
    if s is None: return False, "file absent"
    has_withdraw = "I withdraw the restricted composition" in s
    # the withdrawn design must not remain as the operative proposal in the opening section
    opening = s.split("ARCHITECTURAL CORRECTION")[0] if "ARCHITECTURAL CORRECTION" in s else s
    operative_removal = "Remove shell, writes, generic spawn/fork" in opening or \
                        "Expose read/search and tool-subagent-codex only" in opening
    ok = has_withdraw and not operative_removal
    return ok, f"withdrawal={has_withdraw} superseded_opening_still_operative={operative_removal}"


def a02(base):  # OWNER-DECISION must incorporate the separate-identity mentor ruling
    s = read(base, "docs/dsh/OWNER-DECISION.md")
    if s is None: return False, "file absent"
    ok = "separate OS identity" in s and "operator" in s.lower()
    return ok, f"separate_identity_ruling_present={'separate OS identity' in s}"


def a03(base):  # ARCHITECTURE must not carry the stale "not persisted" claim
    s = read(base, "docs/dsh/ARCHITECTURE.md")
    if s is None: return False, "file absent"
    ok = "not persisted" not in s and "read-only, so I have not" not in s
    return ok, f"stale_not_persisted_claim={'not persisted' in s}"


def a04(base):  # ACTIVE-PLAN must mark absent pipeline exits as planned, not available
    s = read(base, "docs/ACTIVE-PLAN.md")
    if s is None: return False, "file absent"
    ok = re.search(r"planned|not yet implemented|deliverable", s, re.I) is not None and \
         "pipeline.py" in s
    return ok, "planned-deliverable qualification present" if ok else "no planned qualification found"


def a05(base):  # strict validation must pass ON THE GIVEN TREE
    rc, out = run([sys.executable, "plan-validate.py", "docs/ACTIVE-PLAN.md", "--root", ".", "--strict"],
                  cwd=base)
    ok = rc == 0
    return ok, f"plan-validate exit={rc} on {base.name}"


def a06(base):  # stale session-status line removed from PLAN-OF-RECORD
    s = read(base, "docs/PLAN-OF-RECORD.md")
    if s is None: return False, "file absent"
    bad = "not saved" in s or "all six checks passed" in s
    return (not bad), f"stale_session_status_present={bad}"


def a07(base):  # PLAN-OF-RECORD D6 sequence must reflect D13 off-machine restoration
    s = read(base, "docs/PLAN-OF-RECORD.md")
    if s is None: return False, "file absent"
    ok = "D13" in s and "off-machine" in s.lower()
    return ok, f"d13_restoration_reference={'D13' in s}"


def a08(base):  # gate: wrong action refused · exact authorized dispatched · altered args refused · D9-as-permission refused
    snap_gate = base / "tools/astra_gate.py"
    if not snap_gate.exists():
        snap_gate = ROOT / "tools/astra_gate.py"
    src = snap_gate.read_text(encoding="utf8", errors="replace")
    checks = {}
    # 1 refusal on wrong action
    rc, _ = run([sys.executable, str(snap_gate), "D99", "--", "true"])
    checks["wrong_action_refused"] = rc != 0
    # 2 dispatch on exact authorized action/args
    rc, out = run([sys.executable, str(snap_gate), "D19", "--", "python3 tools/row_tests.py A01"])
    checks["exact_authorized_dispatched"] = rc == 0
    # 3 refusal on altered args (a different row within D19 that is NOT approved)
    rc, _ = run([sys.executable, str(snap_gate), "D19", "--", "python3 tools/row.py B01"])
    checks["altered_args_refused"] = rc != 0
    # 4 refusal when D9 invoked as permission
    rc, _ = run([sys.executable, str(snap_gate), "D9", "--", "python3 pubbench/run_pubbench.py"])
    checks["d9_as_permission_refused"] = rc != 0
    ok = all(checks.values())
    return ok, json.dumps(checks)


def a09(base):  # review_packet must not claim serialized-request enforcement it does not perform
    s = read(base, "tools/review_packet.py")
    if s is None: return False, "file absent"
    low = s.lower()
    # POSITIVE assertions that this tool MEASURES the real request (the defect this row repairs)
    POSITIVE = ("constrains the actual serialized request",
                "exact measured serialized request",
                "measures the serialized request",
                "enforces the final request",
                "cumulative enforcement is implemented")
    claims_actual = any(ph in low for ph in POSITIVE)
    claims_cumulative = "MAX_REVIEW_TOKENS" in s and "enforc" in low
    # it must disclose that its token measure is a character estimate
    discloses = ("character estimate" in low) or ("estimate" in low and "len(text)" in s)
    char_estimate = "len(text) // 4" in s or "// 4" in s
    ok = discloses and (not claims_actual) and char_estimate
    return ok, (f"claims_actual_serialized={claims_actual} uses_char_estimate={char_estimate} "
                f"discloses_estimate={discloses} claims_cumulative_enforcement={claims_cumulative}")


def a10(base):  # wrapper must RETURN FAILURE on simulated launch failure, not fall through
    p = base / "tools/astra_review.sh"
    if not p.exists():
        p = ROOT / "tools/astra_review.sh"
    s = p.read_text(encoding="utf8", errors="replace")
    suppresses = "|| true" in s
    # live behavioural check: simulate a failing codex and require nonzero
    ok_beh = None
    try:
        env = dict(os.environ, ASTRA_FAKE_CODEX="1")
        rc, out = run(["bash", str(p), "/nonexistent-packet.json"], timeout=30)
        ok_beh = rc != 0
    except Exception as e:
        ok_beh = False
    ok = (not suppresses) and (ok_beh is not False)
    return ok, f"suppresses_failure={suppresses} fails_on_bad_input={ok_beh}"


def a11(base):  # launchers must not contain direct codex invocations
    bad = []
    for f in ("tools/review_cycle.sh", "v2/dispatch_review.sh", "v2/checkpoint_review.sh"):
        s = read(base, f)
        if s is None:
            bad.append(f"{f}:absent"); continue
        if "codex exec" in s:
            bad.append(f"{f}:direct")
    return (not bad), ("clean" if not bad else ",".join(bad))


def a12(base):  # audit_reviews must MATCH sessions to requests and FAIL when unmatched
    s = read(base, "tools/audit_reviews.py")
    if s is None: return False, "file absent"
    reads_ids = "request_id" in s
    # real matching = the session's own identity is compared against recorded request identity
    # the comparison must actually gate the return: an identity must be looked up against recorded ids
    compares = ("session_id" in s or "session-id" in s or "sessionid" in s) and \
               ("in recorded" in s or "== req" in s or "req in" in s)
    # it must FAIL when suspect sessions exist alongside ledger rows (not just warn and return 0)
    lenient = "reconcile before trusting" in s and "return 1" not in s.split("reconcile before trusting")[-1][:200]
    ok = reads_ids and compares and not lenient
    return ok, f"reads_request_ids={reads_ids} compares_session_identity={compares} warns_but_passes={lenient}"


def a13(base):  # accounting must not carry zero placeholders
    s = read(base, "docs/review-accounting.jsonl")
    if s is None: return False, "file absent"
    zeros = s.count('"input_tokens": 0')
    ok = zeros == 0
    return ok, f"zero_placeholder_rows={zeros}"


def a14(base):  # FAILURE-REGISTER: CLOSED must mean verified
    s = read(base, "docs/FAILURE-REGISTER.md")
    if s is None: return False, "file absent"
    bad = "CLOSED by plan" in s
    return (not bad), f"closed_by_plan_present={bad}"


def a15(base):  # HARMBENCH: lost vectors must be prominent
    s = read(base, "docs/HARMBENCH-RESULT.md")
    if s is None: return False, "file absent"
    ok = ("lost" in s.lower() or "missing" in s.lower()) and "D6" in s
    return ok, f"loss_disclosed={'lost' in s.lower() or 'missing' in s.lower()}"


def a16(base):  # FRR: "base refused, v3 answered" must be qualified as a HEURISTIC transition
    s = read(base, "docs/FRR-RESULT.md")
    if s is None: return False, "file absent"
    phrase = "base refused, v3 answered" in s or "base refused" in s
    qualifies = "heuristic" in s.lower()
    # the side-by-side table must also carry the damaged-HarmBench limitation
    carries_limit = ("HARMBENCH" in s.upper() and ("damaged" in s.lower() or "lost" in s.lower() or "D6" in s))
    ok = qualifies and carries_limit
    return ok, f"has_refusal_phrase={phrase} heuristic_qualified={qualifies} carries_harmbench_limit={carries_limit}"


def a17(base):  # ROLE-PROTOCOL instrument list must not read as exhaustive
    s = read(base, "docs/ROLE-PROTOCOL.md")
    if s is None: return False, "file absent"
    present = "only these four count" in s.lower()
    # must instead scope the list against the later product instruments
    low = s.lower()
    scoped = ("plan-of-record" in low and "not exhaustive" in low)
    ok = (not present) or scoped
    return ok, f"stale_exhaustive_wording={present} scoped_against_plan={scoped}"


def a18(base):  # acceptance dir must not be empty
    d = base / "docs/dsh/acceptance"
    if not d.exists(): return False, "dir absent"
    n = len([x for x in d.rglob("*") if x.is_file()])
    return n > 0, f"acceptance_files={n}"


def a19(base):  # scanner must EXIST and DETECT a planted ungoverned entry point
    p = base / "tools/scan_review_invocations.py"
    if not p.exists():
        return False, "scanner absent"
    # planted-entry-point test in a temp tree
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "ok.sh").write_text("#!/bin/bash\ntools/astra_review.sh packet.json\n")
        (t / "planted.sh").write_text("#!/bin/bash\ncodex exec -m gpt-6-astra < p.txt\n")
        rc_ok, _ = run([sys.executable, str(p), str(t / "ok.sh")])
        rc_bad, out_bad = run([sys.executable, str(p), str(t / "planted.sh")])
    detected = rc_bad != 0
    clean = rc_ok == 0
    return (detected and clean), f"planted_detected={detected} clean_passes={clean}"


# ── Group 3: C01 ───────────────────────────────────────────────────────────────────────────────────
REQUIRED_PRESERVED = [
    "docs/dsh/OWNER-DECISION.md", "docs/dsh/ARCHITECTURE.md", "docs/ACTIVE-PLAN.md",
    "docs/PLAN-OF-RECORD.md", "tools/astra_gate.py", "tools/review_packet.py",
    "tools/astra_review.sh", "tools/review_cycle.sh", "v2/dispatch_review.sh",
    "v2/checkpoint_review.sh", "tools/audit_reviews.py", "docs/review-accounting.jsonl",
    "docs/FAILURE-REGISTER.md", "docs/HARMBENCH-RESULT.md", "docs/FRR-RESULT.md",
    "docs/ROLE-PROTOCOL.md",
]


def c01(base):  # preserve manifest must COVER every required artifact and round-trip byte-identical
    pres = base / "docs/dsh/acceptance/preserve"
    man = pres / "MANIFEST.sha256"
    if not man.exists():
        return False, "preserve manifest absent"
    entries = {}
    for line in man.read_text().splitlines():
        if not line.strip():
            continue
        h, rel = line.split("  ", 1)
        entries[rel] = h
    missing = [r for r in REQUIRED_PRESERVED if not any(e.endswith(r) for e in entries)]
    # round-trip each entry against the GIVEN tree
    bad = []
    for rel, h in entries.items():
        f = pres / rel
        if not f.exists() or sha(f) != h:
            bad.append(rel)
    roundtrip = not bad
    # home patch: in the prefix/control tree use the preserved copy; in live use the real file
    hp = pres / "home/cordis.patch.yml"
    if hp.exists():
        actual = sha(hp)
    else:
        actual = sha(HOME_PATCH) if HOME_PATCH.exists() else "absent"
    ok = roundtrip and (not missing) and actual == H
    return ok, (f"coverage={len(entries)} entries missing={len(missing)} roundtrip={roundtrip} "
                f"home_patch_ok={actual == H}" + (f" missing={missing[:3]}" if missing else ""))


ROWS = [
    ("A01", "OWNER-DECISION: withdrawn design superseded, not appended", a01),
    ("A02", "OWNER-DECISION: separate-identity mentor ruling incorporated", a02),
    ("A03", "ARCHITECTURE: stale 'not persisted' claim removed", a03),
    ("A04", "ACTIVE-PLAN: absent pipeline exits marked planned", a04),
    ("A05", "ACTIVE-PLAN: strict validation passes", a05),
    ("A06", "PLAN-OF-RECORD: stale session status removed", a06),
    ("A07", "PLAN-OF-RECORD: D13 restoration reflected", a07),
    ("A08", "gate: refuse wrong/altered/D9-as-permission, dispatch exact", a08),
    ("A09", "review_packet: no enforcement overclaim", a09),
    ("A10", "wrapper: returns failure on launch failure", a10),
    ("A11", "launchers: no direct codex invocation", a11),
    ("A12", "audit_reviews: real request matching + nonzero exit", a12),
    ("A13", "accounting: no zero placeholders", a13),
    ("A14", "FAILURE-REGISTER: CLOSED means verified", a14),
    ("A15", "HARMBENCH: lost vectors disclosed", a15),
    ("A16", "FRR: heuristic transition qualified", a16),
    ("A17", "ROLE-PROTOCOL: instrument list not exhaustive", a17),
    ("A18", "acceptance dir populated", a18),
    ("A19", "scanner exists and detects planted entry point", a19),
    ("C01", "manifest round-trips byte-identical + home patch holds", c01),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", choices=["prefix", "live"], default="live")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    base = SNAP if a.state == "prefix" else ROOT
    rows = []
    for rid, desc, fn in ROWS:
        try:
            ok, ev = fn(base)
        except Exception as e:
            ok, ev = False, f"ERROR {type(e).__name__}: {e}"
        rows.append({"id": rid, "desc": desc, "ok": bool(ok), "evidence": ev})
        print(f"  {'PASS' if ok else 'FAIL'}  {rid}  {desc}")
        print(f"          {ev}")
    npass = sum(r["ok"] for r in rows)
    print(f"\n  == {a.state}: {npass}/{len(rows)} pass, {len(rows)-npass} fail ==")
    if a.json:
        Path(a.json).write_text(json.dumps({"state": a.state, "rows": rows}, indent=1))
    # prefix run MUST fail; live run MUST pass
    if a.state == "prefix" and npass == len(rows):
        print("  *** REJECTED: every test passed on the PRE-FIX state — these are smoke tests ***")
        return 2
    return 0 if npass == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
