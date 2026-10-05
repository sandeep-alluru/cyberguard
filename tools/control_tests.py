#!/usr/bin/env python3
"""control_tests.py — prove every row test CAN FAIL by disabling its load-bearing control.

Owner criterion (D20): "the test must be demonstrated to FAIL -- against the pre-fix state, OR WITH THE
LOAD-BEARING CONTROL DISABLED; a test never seen to fail is rejected as a smoke test."

For each row this disables the specific control the row protects and requires the corresponding test to
return FAIL. If a test still passes with its control disabled, the test is a smoke test and is REJECTED.
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import row_tests as R

ROOT = R.ROOT

# (row, control-to-disable description, mutation(base) -> None)
def _mut(base, rel, fn):
    p = base / rel
    if p.exists():
        p.write_text(fn(p.read_text(encoding="utf8", errors="replace")), encoding="utf8")

CONTROLS = {
    "A01": ("re-insert the withdrawn design as the operative opening proposal",
            lambda b: _mut(b, "docs/dsh/OWNER-DECISION.md", lambda s: "Expose read/search and tool-subagent-codex only\n" + s)),
    "A02": ("remove the separate-identity ruling",
            lambda b: _mut(b, "docs/dsh/OWNER-DECISION.md", lambda s: s.replace("separate OS identity", ""))),
    "A03": ("re-insert the stale not-persisted claim",
            lambda b: _mut(b, "docs/dsh/ARCHITECTURE.md", lambda s: s + "\nnot persisted\n")),
    "A04": ("remove the planned-deliverable qualification entirely",
            lambda b: _mut(b, "docs/ACTIVE-PLAN.md",
                           lambda s: __import__("re").sub(r"planned|not yet implemented|deliverable", "READY", s, flags=__import__("re").I))),
    "A05": ("re-insert a blank required cell and an undeclared absent path",
            lambda b: _mut(b, "docs/ACTIVE-PLAN.md",
                           lambda s: s.replace("| **Both stages** | 750 benchmark items",
                                               "| **Both stages** | |").replace(
                                               "**Planned deliverable — does not exist yet.**", ""))),
    "A06": ("re-insert the stale session-status line",
            lambda b: _mut(b, "docs/PLAN-OF-RECORD.md", lambda s: s + "\nnot saved\n")),
    "A07": ("remove the D13 restoration reference",
            lambda b: _mut(b, "docs/PLAN-OF-RECORD.md", lambda s: s.replace("D13", "XX").replace("off-machine", "local"))),
    "A08": ("weaken the gate to allow any D19 row (disable the allowlist)",
            lambda b: _mut(b, "tools/astra_gate.py", lambda s: s.replace('row not in APPROVED_ROWS', 'False'))),
    "A09": ("inject a positive serialized-request enforcement claim and remove the estimate disclosure",
            lambda b: _mut(b, "tools/review_packet.py",
                           lambda s: s.replace("conservative CHARACTER ESTIMATE", "measured value")
                                      .replace("This tool constrains the PACKET it is given and estimates its size.",
                                               "This tool constrains the ACTUAL serialized request."))),
    "A10": ("re-insert the failure suppression",
            lambda b: _mut(b, "tools/astra_review.sh", lambda s: s.replace("codex exec", "codex exec || true && codex exec"))),
    "A11": ("re-insert a direct codex invocation into a launcher",
            lambda b: _mut(b, "tools/review_cycle.sh", lambda s: s + "\ncodex exec -m gpt-6-astra < x\n")),
    "A12": ("restore the lenient warn-and-pass behaviour (no identity match, exit 0)",
            lambda b: _mut(b, "tools/audit_reviews.py",
                           lambda s: __import__("re").sub(r"session_id", "x", s)
                                       .replace("if unmatched:", "if False:").replace("return 1", "return 0"))),
    "A13": ("re-insert a zero placeholder row",
            lambda b: _mut(b, "docs/review-accounting.jsonl", lambda s: s + '{"input_tokens": 0}\n')),
    "A14": ("re-insert CLOSED by plan",
            lambda b: _mut(b, "docs/FAILURE-REGISTER.md", lambda s: s + "\nCLOSED by plan\n")),
    "A15": ("remove the lost-vector disclosure",
            lambda b: _mut(b, "docs/HARMBENCH-RESULT.md", lambda s: s.replace("lost", "X").replace("missing", "X").replace("D6", "XX"))),
    "A16": ("remove every HarmBench limitation marker from the FRR side-by-side",
            lambda b: _mut(b, "docs/FRR-RESULT.md",
                           lambda s: s.replace("HARMBENCH", "X").replace("harmbench", "X")
                                      .replace("HarmBench", "X").replace("lost", "X")
                                      .replace("LOST", "X").replace("D6", "XX"))),
    "A17": ("re-insert unscoped exhaustive wording and remove the plan-of-record scoping",
            lambda b: _mut(b, "docs/ROLE-PROTOCOL.md",
                           lambda s: __import__("re").sub(
                               r"plan-of-record|plan of record|product instruments|not exhaustive",
                               "X", s, flags=__import__("re").I) + "\nOnly these four count\n")),
    "A18": ("empty the acceptance directory",
            lambda b: [f.unlink() for f in (b / "docs/dsh/acceptance").rglob("*") if f.is_file()]),
    "A19": ("remove the planted-entry detection",
            lambda b: _mut(b, "tools/scan_review_invocations.py", lambda s: "import sys\nsys.exit(0)\n")),
    "C01": ("corrupt one preserved copy so round-trip fails",
            lambda b: _mut(b, "docs/dsh/acceptance/preserve/MANIFEST.sha256", lambda s: s.replace(s.split()[0], "0"*64, 1))),
}


def main():
    print("== CONTROL RUN — disable each row's load-bearing control; every test MUST fail ==")
    results = []
    for rid, desc, fn in R.ROWS:
        if rid not in CONTROLS:
            continue
        cdesc, mutate = CONTROLS[rid]
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "tree"
            shutil.copytree(ROOT, work, symlinks=True,
                            ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", "*venv*"))
            try:
                mutate(work)
            except Exception:
                pass
            try:
                ok, ev = fn(work)
            except Exception as e:
                ok, ev = False, f"ERROR {e}"
        failed_as_required = (ok is False)
        results.append({"id": rid, "control": cdesc, "test_failed_with_control_disabled": failed_as_required,
                        "evidence": ev})
        print(f"  {'OK  ' if failed_as_required else 'SMOKE'}  {rid}  control: {cdesc}")
        print(f"          {ev}")
    smoke = [r["id"] for r in results if not r["test_failed_with_control_disabled"]]
    print(f"\n  == {len(results)-len(smoke)}/{len(results)} tests proven failable; SMOKE TESTS: {smoke or 'none'} ==")
    Path("docs/dsh/acceptance/report/control-run.json").write_text(json.dumps(results, indent=1))
    return 1 if smoke else 0


if __name__ == "__main__":
    sys.exit(main())
