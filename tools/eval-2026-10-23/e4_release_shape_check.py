#!/usr/bin/env python3
"""E-4 — the release-shape check: the decision names the shape, and its host facts are re-verified.

WHY THIS FILE EXISTS
--------------------
Ledger item **E-4** requires a written decision whose acceptance is: *"the decision names the shape
and the serving party, or records that the serving party is unresolved and says what that blocks"*.

`docs/RELEASE-SHAPE.md` takes the second branch: the **shape is decided**, the **serving party is
unresolved**, and the record names what that blocks.

WHAT THIS FILE MEASURES
-----------------------
Not "the document says the right words". Three things:

1. The decision **names the shape** — all six components, with the parameter that matters for each.
2. The decision **either names a serving party or records that it is unresolved**, and in the
   unresolved case it names **at least three specific things that are blocked** (a vague "this
   blocks deployment" would not pass).
3. **Every factual claim the decision makes about this host is re-verified against the filesystem
   and the network at check time.** A decision that says "that host is unreachable" must still be
   true when the check runs; a decision that says "`llama-quantize` is not built" must still be
   true. This is what stops the record from decaying into a stale story.

Output: eval-2026-10-23/e4-release-shape-check.json
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DOC = ROOT / "docs" / "RELEASE-SHAPE.md"
OUT = HERE / "e4-release-shape-check.json"

HOME = Path.home()
BASE_MODEL = HOME / "models" / "cyberguard-eval" / "Qwen3-4B-Instruct-2507"
ADAPTER = ROOT / "research-tmp" / "harvest-v3" / "adapters"
LLAMA_CPP = HOME / "llama.cpp"
LLAMA_BIN = LLAMA_CPP / "build" / "bin"
SERVE_SCRIPT = ROOT / "serve-cyberguard-local.sh"
MERGE_SCRIPT = ROOT / "cyberguard-merge-gguf.sh"
SERVE_HARDCODED_PATH = Path("<storage-mount>/gpu-work/build/llama.cpp/build/bin")
HOST = "<peer-host>"

SHAPE_COMPONENTS = ("merged weights", "GGUF bf16", "Q4_K_M GGUF",
                     "`generation_config.json`", "model card", "hash-frozen bundle")


def main():
    checks = []
    doc = DOC.read_text() if DOC.exists() else ""

    def ck(name, cond):
        checks.append((name, bool(cond)))

    # --- 1. the shape is named ----------------------------------------------------
    ck("the decision document exists", DOC.exists())
    ck("the decision names all six shape components",
       all(c in doc for c in SHAPE_COMPONENTS))
    ck("the decision states the pipeline order",
       "merge" in doc.lower() and "convert" in doc.lower()
       and "quantis" in doc.lower())
    ck("the decision names the serving parameter that matters (512 new tokens, not the default)",
       "512" in doc and "generation_config.json" in doc)
    ck("the decision states where the merge and the conversion happen",
       "on THIS host" in doc or "on this host" in doc.lower())

    # --- 2. the serving party is named OR recorded as unresolved ------------------
    unresolved = ("UNRESOLVED" in doc and "serving party" in doc.lower())
    ck("the decision either names a serving party or records it as unresolved",
       unresolved or "serving party is" in doc.lower())
    ck("the decision's status line states which branch it takes",
       re.search(r"\*\*Status:\*\*.*(UNRESOLVED|serving party)", doc) is not None)

    blocked = []
    if unresolved:
        # the "What the unresolved serving party blocks, precisely" list
        m = re.search(r"blocks, precisely:\*?\*(.*?)(?:\n---|\n## )", doc, re.S)
        if m:
            blocked = [l for l in m.group(1).split("\n")
                       if re.match(r"\s*\d+\.\s", l)]
    ck("the decision names at least three specific things the unresolved serving party blocks",
       len(blocked) >= 3)
    ck("the blocked list names the release decision (H-3) as blocked from ship-and-serve",
       any("H-3" in b for b in blocked))
    ck("the blocked list names the DSH registration as blocked",
       any("DSH" in b for b in blocked))

    # --- 3. every host fact the decision asserts is re-verified now ---------------
    ck("the base model the decision names is present at the path it names",
       BASE_MODEL.is_dir() and str(BASE_MODEL) in doc)
    ck("the adapter the decision names is present at the path it names",
       ADAPTER.is_dir() and str(ADAPTER) in doc)
    ck("the llama.cpp tree the decision names is present at the commit it names",
       LLAMA_CPP.is_dir() and re.search(r"[0-9a-f]{40}", doc) is not None)
    if LLAMA_CPP.is_dir():
        try:
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=LLAMA_CPP,
                                    capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception:
            commit = ""
        ck("the llama.cpp commit the decision names is the tree's current commit",
           bool(commit) and commit in doc)
    ck("the python `gguf` module is importable, as the decision states",
       subprocess.run(["python3", "-c", "import gguf"], capture_output=True).returncode == 0)

    ck("`llama-server` is built on this host, as the decision states",
       (LLAMA_BIN / "llama-server").exists())
    ck("`llama-quantize` is NOT built on this host, as the decision states",
       not (LLAMA_BIN / "llama-quantize").exists())
    ck("the decision states that `llama-quantize` is not built",
       "llama-quantize" in doc and "NOT built" in doc.replace("**NO**", "NOT built"))
    ck("the `llama-quantize` build target is nonetheless available locally, as the decision states",
       subprocess.run(["cmake", "--build", str(LLAMA_CPP / "build"), "--target", "help"],
                      capture_output=True, text=True).stdout.count("llama-quantize") > 0)

    ck("the path `serve-cyberguard-local.sh` hard-codes does not exist, as the decision states",
       not SERVE_HARDCODED_PATH.exists() and str(SERVE_HARDCODED_PATH) in doc)
    ck("`serve-cyberguard-local.sh` exists and does hard-code that path",
       SERVE_SCRIPT.exists()
       and str(SERVE_HARDCODED_PATH) in SERVE_SCRIPT.read_text())
    ck("`~/.cyberguard-env` does not exist, as the decision states",
       not (HOME / ".cyberguard-env").exists() and ".cyberguard-env" in doc)
    ck("`cyberguard-merge-gguf.sh` exists and does source `~/.cyberguard-env`",
       MERGE_SCRIPT.exists()
       and ".cyberguard-env" in MERGE_SCRIPT.read_text())

    gguf_dir = ROOT / "gguf"
    ck("the `gguf/` directory holds no GGUF, as the decision states",
       gguf_dir.is_dir() and not any(gguf_dir.glob("*.gguf")))

    # that host's reachability — a network fact, so it is checked and reported, and the
    # decision's claim must match what this check observes.
    host_rc = None
    host_out = ""
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", HOST,
                            "echo REACHABLE"], capture_output=True, text=True, timeout=20)
        host_rc = r.returncode
        host_out = (r.stdout + r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        host_out = f"ssh unavailable: {e}"
    ck("that host is not reachable from this host, as the decision states",
       host_rc != 0 and "REACHABLE" not in host_out)
    ck("the decision names that host as unreachable and quotes the observed failure",
       "<host-a>" in doc and "Host key verification failed" in doc)

    # --- 4. the record does not overclaim ----------------------------------------
    # A claim of shipping counts only when it is NOT inside a negation. The record's own
    # disclaimer ("does not claim the release ships") contains the phrase, so a bare
    # substring test would flag the disclaimer as the thing it forbids.
    NEG = ("does not claim", "cannot", "not ", "never", "no ")
    shipping_claims = []
    for i, l in enumerate(doc.splitlines(), 1):
        if re.search(r"\bthe release ships\b|\bwe ship\b|\bship it\b", l, re.I):
            if not any(n in l.lower() for n in NEG):
                shipping_claims.append((i, l.strip()[:120]))
    ck("the record makes no affirmative claim that the release ships",
       not shipping_claims)
    ck("the record says so explicitly", "does not claim the release ships" in doc)
    ck("the record does not claim any bar is met",
       "does not claim any bar is met" in doc)
    ck("the record names the untaken remedies as not launched",
       "NOT LAUNCHED" in doc)
    ck("the record names the corpus-receipt dependency (D-7) as blocking the manifest",
       "D-7" in doc and "manifest" in doc)

    out = {
        "status": "MEASUREMENT — the decision's structure and every host fact it asserts are "
                  "re-verified at check time.",
        "decision": str(DOC),
        "branch": "serving party UNRESOLVED" if unresolved else "serving party NAMED",
        "blocked_items_found": len(blocked),
        "host_facts_reverified": {
            "base_model_present": BASE_MODEL.is_dir(),
            "adapter_present": ADAPTER.is_dir(),
            "llama_cpp_present": LLAMA_CPP.is_dir(),
            "llama_server_built": (LLAMA_BIN / "llama-server").exists(),
            "llama_quantize_built": (LLAMA_BIN / "llama-quantize").exists(),
            "serve_script_hardcoded_path_exists": SERVE_HARDCODED_PATH.exists(),
            "cyberguard_env_exists": (HOME / ".cyberguard-env").exists(),
            "gguf_files_present": len(list(gguf_dir.glob("*.gguf"))) if gguf_dir.is_dir() else 0,
            "host_ssh_returncode": host_rc,
            "host_ssh_output": host_out[:200],
        },
        "checks": [{"check": c, "pass": bool(p)} for c, p in checks],
    }
    npass = sum(1 for _, p in checks if p)
    out["checks_passed"] = npass
    out["checks_total"] = len(checks)
    out["status_line"] = f"{npass}/{len(checks)} checks PASS"
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    print(f"e4_release_shape: {npass}/{len(checks)} checks PASS -> {OUT}")
    for c, p in checks:
        print(f"  [{'PASS' if p else 'FAIL'}] {c}")
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
