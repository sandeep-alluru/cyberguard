#!/usr/bin/env python3
"""Mine a DSH session trace for tool-call behaviour: what the instrument actually did.

Reads a `session.v3.jsonl[.zstd]` from the DSH session store and reports, per session:
  * tool calls by name, with failure counts and failure rate
  * normalized error signatures (grouped, with first/last occurrence and an example)
  * turn/step counts, LLM retries and failed attempts (endpoint health)
  * the shell/ops failure classes that CRAFT 03 documents, counted rather than asserted

This exists because the operation's own postmortem flagged the toolcall-level trace as the one
analysis gap: `docs/CRAFT/*` was mined from LEDGER.md, which is a *narrative* of the session, not
the session. This script closes that gap with counts.

Usage:
  python3 analyze_toolcalls.py <session.v3.jsonl[.zstd]> [--json OUT.json] [--top N]
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys


def read_events(path: str):
    opener = subprocess.run if path.endswith(".zstd") else None
    if opener:
        proc = subprocess.run(["zstd", "-dc", path], capture_output=True, check=True)
        lines = proc.stdout.decode("utf-8", "replace").splitlines()
    else:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


NUM = re.compile(r"\b\d+\b")
HEX = re.compile(r"\b[0-9a-f]{7,}\b")
PATHISH = re.compile(r"(/[\w.\-]+){2,}")


def signature(text: str) -> str:
    """Collapse an error string to a comparable signature."""
    s = str(text).strip().splitlines()[0] if str(text).strip() else ""
    s = HEX.sub("<hex>", s)
    s = PATHISH.sub("<path>", s)
    s = NUM.sub("<n>", s)
    return s[:180]


def iso(ms) -> str:
    import datetime
    if not ms:
        return "-"
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%m-%d %H:%M:%S")


def result_text(d: dict) -> str:
    """Flatten a tool/result message to plain text."""
    msg = d.get("message")
    if not isinstance(msg, dict):
        return str(msg or "")
    out = []
    for block in msg.get("content", []) or []:
        for inner in block.get("content", []) or []:
            if isinstance(inner, dict) and inner.get("type") == "text":
                out.append(inner.get("text", ""))
    return "\n".join(out)


EXIT_RE = re.compile(r"\[exit code: (\d+)\]")
STDERR_RE = re.compile(r"\[stderr\]\n(.*)", re.S)


def bash_failure_signature(text: str) -> str:
    m = STDERR_RE.search(text)
    raw = m.group(1) if m else text
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    lines = [ln for ln in lines if not ln.startswith("[exit code")]
    if not lines:
        return "(no stderr)"
    if "Traceback" in raw:
        tail = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        for ln in reversed(tail):
            if "Error" in ln or "Exception" in ln:
                return "Traceback: " + signature(ln)
        return "Traceback: (unparsed)"
    return signature(lines[0])


def analyze(path: str, top: int) -> dict:
    counts = collections.Counter()
    tool_calls = collections.Counter()
    tool_fail = collections.Counter()
    sigs = collections.Counter()
    sig_first, sig_last, sig_example = {}, {}, {}
    sig_tool = collections.defaultdict(collections.Counter)
    first_ms = last_ms = None
    turns = 0
    retries = 0
    attempts = 0
    shellish = collections.Counter()

    pending = {}
    exit_codes = collections.Counter()
    bash_fail = collections.Counter()
    bash_fail_meta = {}
    bash_calls = bash_marked = 0
    for ev in read_events(path):
        t = ev.get("type", "?")
        counts[t] += 1
        ms = ev.get("time")
        if ms:
            first_ms = ms if first_ms is None else min(first_ms, ms)
            last_ms = ms if last_ms is None else max(last_ms, ms)
        d = ev.get("data") or {}

        if t == "turn/start":
            turns += 1
        elif t == "llm/retry":
            retries += 1
        elif t == "assistant/attempt":
            attempts += 1
        elif t == "tool/call":
            name = d.get("name", "?")
            tool_calls[name] += 1
            args = d.get("arguments")
            if isinstance(args, str):            # this harness stores arguments as a JSON string
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            if not isinstance(args, dict):
                args = {}
            cmd = str(args.get("command", ""))
            pending[d.get("callId")] = (name, cmd)
            if name in ("bash", "shell", "run_command"):
                bash_calls += 1
                for pat, label in (
                    (r"\bpgrep\b|\bps aux\b|/proc/", "process-scan"),
                    (r"\bscp\b", "scp-transfer"),
                    (r"\bssh\b", "ssh-remote"),
                    (r"\bsed\b", "sed-rewrite"),
                    (r"\bcurl\b", "curl-probe"),
                    (r"systemctl", "systemctl"),
                    (r"nvidia-smi", "gpu-probe"),
                ):
                    if re.search(pat, cmd):
                        shellish[label] += 1
        elif t == "tool/result":
            # the call id lives inside message.source, not at the top level of `data`
            msg = d.get("message") if isinstance(d.get("message"), dict) else {}
            cid = d.get("callId") or (msg.get("source") or {}).get("callId")
            name, cmd = pending.pop(cid, ("?", ""))
            err = d.get("error")
            if not err:
                for block in msg.get("content", []) or []:
                    if isinstance(block, dict) and block.get("isError"):
                        err = block.get("error") or "isError=true"
            if err:
                tool_fail[name] += 1
                s = signature(err if isinstance(err, str) else json.dumps(err))
                sigs[s] += 1
                sig_tool[s][name] += 1
                sig_first.setdefault(s, ms)
                sig_last[s] = ms
                sig_example.setdefault(s, err if isinstance(err, str) else json.dumps(err)[:300])
            elif name in ("bash", "shell", "run_command"):
                text = result_text(d)
                m = EXIT_RE.search(text)
                if m:
                    bash_marked += 1
                    code = int(m.group(1))
                    exit_codes[code] += 1
                    if code != 0:
                        s = f"exit {code}: " + bash_failure_signature(text)
                        bash_fail[s] += 1
                        meta = bash_fail_meta.setdefault(
                            s, {"first": iso(ms), "last": iso(ms), "example_cmd": cmd[:220]})
                        meta["last"] = iso(ms)

    return {
        "session_file": os.path.basename(path),
        "window": {"first": iso(first_ms), "last": iso(last_ms)},
        "turns": turns,
        "steps_started": counts.get("step/start", 0),
        "tool_calls_total": sum(tool_calls.values()),
        "tool_calls": dict(tool_calls.most_common()),
        "tool_failures": dict(tool_fail.most_common()),
        "failure_rate": round(sum(tool_fail.values()) / max(1, sum(tool_calls.values())), 4),
        "llm_retries": retries,
        "assistant_attempts": attempts,
        "compactions": counts.get("compaction/summary", 0),
        "bash_calls": bash_calls,
        "bash_results_with_exit_marker": bash_marked,
        "bash_exit_codes": dict(exit_codes.most_common()),
        "bash_failures": [
            {"signature": s, "count": c, **bash_fail_meta.get(s, {})}
            for s, c in bash_fail.most_common(top)
        ],
        "shell_categories": dict(shellish.most_common()),
        "error_signatures": [
            {"signature": s, "count": c, "tools": dict(sig_tool[s]), "first": iso(sig_first.get(s)),
             "last": iso(sig_last.get(s)), "example": sig_example.get(s, "")[:300]}
            for s, c in sigs.most_common(top)
        ],
        "event_types": dict(counts.most_common()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Mine a DSH session trace for tool-call behaviour")
    ap.add_argument("session")
    ap.add_argument("--json", metavar="OUT")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    rep = analyze(args.session, args.top)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=2)

    print(f"SESSION {rep['session_file']}  {rep['window']['first']} -> {rep['window']['last']}")
    print(f"  turns={rep['turns']} steps={rep['steps_started']} compactions={rep['compactions']} "
          f"llm_retries={rep['llm_retries']} attempts={rep['assistant_attempts']}")
    print(f"  tool calls={rep['tool_calls_total']} failures={sum(rep['tool_failures'].values())} "
          f"rate={rep['failure_rate']:.1%}")
    print("\nTOOL CALLS")
    for name, c in rep["tool_calls"].items():
        f = rep["tool_failures"].get(name, 0)
        print(f"  {c:5d}  {name:<22} failures={f}")
    if rep["shell_categories"]:
        print("\nSHELL CATEGORIES")
        for k, c in rep["shell_categories"].items():
            print(f"  {c:5d}  {k}")
    print(f"\nBASH EXIT CODES (marked results: {rep['bash_results_with_exit_marker']}"
          f"/{rep['bash_calls']})")
    for code, c in rep["bash_exit_codes"].items():
        print(f"  exit {code:<5} {c}")
    if rep["bash_failures"]:
        print(f"\nTOP {args.top} BASH FAILURES")
        for b in rep["bash_failures"]:
            print(f"  x{b['count']:<4} {b.get('first')} -> {b.get('last')}")
            print(f"        {b['signature']}")
            print(f"        cmd: {b.get('example_cmd','')}")
    print(f"\nTOP {args.top} ERROR SIGNATURES")
    for s in rep["error_signatures"]:
        print(f"  x{s['count']:<4} {s['first']} -> {s['last']}  [{','.join(s['tools'])}]")
        print(f"        {s['signature']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
