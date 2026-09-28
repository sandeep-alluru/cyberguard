# CRAFT 05 — The session toolcall trace: what the instrument actually did

The operation's own postmortem (`docs/muse-1.3-…-postmortem.md` §9/§10b) named exactly one analysis
gap it could not close: **"DSH session bodies (toolcall-level trace) not re-read here"** — the
narrative in `LEDGER.md` was mined, the session that produced it was not. This file closes that gap
with counts instead of impressions.

**Method.** `analyze_toolcalls.py` (repo root) reads a `session.v3.jsonl[.zstd]` from the DSH session
store and reports tool mix, harness-level errors, shell exit codes, normalized error signatures and
event timing. Two sessions of this working directory have traces:

| trace | session | window (CDT) | what it covers |
|---|---|---|---|
| `research-tmp/trace/trace-main.json` | `session-72afaf76…` | 09-26 17:12 → 09-27 20:21 | the whole operation: corpus audit, contract build, v1 training watch, eval chain, capability box, corpus writing, handover |
| `research-tmp/trace/trace-2.json` | `session-218f9953…` | 09-26 15:38 → 09-27 20:20 | the flash-serving investigation that produced `RUNBOOK-qwen-flash-serving.md` |

Reproduce exactly:

```bash
D=~/.dsh/sessions/--home-clawer-samurai-1-AgentHub-cyberguard--
zstd -dc "$D/session-72afaf76-03b8-4f79-ba9c-a7e8b026b903/session.v3.jsonl.zstd" \
  > research-tmp/session-main.jsonl
python3 analyze_toolcalls.py research-tmp/session-main.jsonl \
  --json research-tmp/trace/trace-main.json --top 20
```

---

## 1. The operation in numbers (main trace)

| quantity | value |
|---|---|
| turns / steps | **40 / 425** |
| context compactions | **5** (the operation outlived its own context window five times) |
| LLM retries / failed attempts | **18 / 22** (the endpoint was demonstrably unhealthy) |
| tool calls / harness errors | **517 / 11** (2.1 %) |
| bash calls / non-zero exits marked | **257 / 13** (5.1 %) |
| `[exit code]` markers: 1, 2, 124 | 10, 2, 1 |

**Tool mix** (top 10 of 20): `bash` 257 · `edit` 111 · `read` 41 · `write` 23 · `job_output` 18 ·
`memory` 9 · `list_agents` 8 · `job_list` 7 · `plur_learn` 7 · `todo_write` 6 · `web_search` 6.
Review delegation in the mix: `subagent_codex` 5, `subagent_grok` 2, `subagent` 3 (the three
own-model mining agents the owner later ordered abandoned — the tool mix makes that visible).

**Shell categories** (main): `ssh-remote` 92 · `curl-probe` 31 · `process-scan` 30 · `scp-transfer` 28
· `sed-rewrite` 24 · `gpu-probe` 16 · `systemctl` 1. Two thirds of all shell work was remote
orchestration — the operation was an *instrument-build* project, not a training script.

**Second trace for contrast:** 202 tool calls, 135 bash, and a completely different profile —
`ssh-remote` 72, `curl-probe` 55, `systemctl` 36, `gpu-probe` 6 — i.e. a serving-diagnosis session,
with 0 LLM retries and 1 harness error, against the main session's 18 retries. The two traces
separate cleanly: **one session measured the model, the other debugged the server.**

## 2. Failure taxonomy (11 harness + 13 shell = 24 recorded failures, 2.1 % + 5.1 %)

**Harness-level (11):** `edit` 8 — `FS_EDIT_NOT_FOUND` ×3, `FS_NOT_OBSERVED` ×3,
`FS_STALE_VERSION` ×2; `read` 2 — `FS_NOT_FOUND`, `FS_NOT_OBSERVED`; `update_goal` 1 —
`GOAL_STALE_REVISION`. These are *file-observation* discipline errors, not tooling bugs: each code is
an instruction (read first / re-read then retry / re-read the goal revision).

**Shell-level (13 non-zero exits):**

| class | count | evidence |
|---|---|---|
| **designed** self-test failures (scorer/contract fixtures rejecting bad input, 11:10–11:49) | 4 | `AssertionError` tracebacks in `cap_scorers`/`cap_probes` smoke runs |
| scratch-directory misuse (`cd /tmp/cgdigest` before it existed) | 1 | `bash: cd: /tmp/cgdigest: No such file or directory` |
| path typo against a file the command had just been told to list | 1 | `head: cannot open 'docs/…'` |
| schema assumption in a throwaway analysis script | 1 | `AttributeError: 'str' object has no attribute 'get'` |
| detached-launch status (the ssh-124 class) | 1 | `exit 124` with stderr `REPLAY-STARTED` |
| stderr-noise-only non-zero exits (deprecation warnings in the chain) | 2 | `[transformers] torch_dtype is deprecated…` |
| remaining short assertion exits in dev loops | 3 | `exit 1`/`exit 2` inside py_compile + smoke chains |

**Text-level scan (the channel the marker misses):** within the main trace's bash results,
`No such file` appears in 9, `Traceback` in 9, `command not found` in 1. In the **second** trace:
**135 bash calls, zero exit markers**, while 3 results contain `No such file` and 3 contain
`Permission denied`. A marker-only failure count for that session reads **0**; the truth is not 0.
That single observation is CRAFT-O-22.

## 3. What the trace says worked

- **Nothing was lost to the 5 compactions**: every collapsed turn resumed from the ledger and the
  research-tmp receipts rather than from memory — the compaction boundary is where a project without
  durable artifacts dies, and this one had them.
- **Detached work survived 18 retries and 22 failed attempts** on an endpoint that was measurably
  sick; the main session's own liveness checks (log growth + `/proc`) rather than log tails are what
  kept the sleep-watching honest.
- **Review delegation happened on the record**, not in prose: 5 `subagent_codex` calls and 2
  `subagent_grok` calls, each landing a disposition table in `LEDGER.md`.
- **Only 24 failures in 517 calls, and zero data loss**: every incident preserved its evidence
  (`*.stray-*`, `*.batch1-slow-*`, `logs/acknowledged/`, `…aborted-wrongmask-20260927`).

## 4. Caveats (what this trace cannot show)

- The trace is the **local orchestration** only; the training/eval/capability boxes ran remotely, and
  their evidence is the remote logs and receipts, not these events. A remote-side failure is visible
  here only when a local command observed it.
- `tool/result` carries no `callId` at the top level in this harness version (it lives under
  `message.source.callId`) and `arguments` is a JSON-encoded **string**; a parser that assumes either
  shape silently reports every result as unattributed. This cost one debugging round in `analyze_toolcalls.py`
  and is why the script is kept with the corpus.
- Failure text is normalized (`<path>`, `<hex>`, `<n>`) before grouping; two genuinely different
  failures sharing a signature are counted together by design, so the counts are a floor, not a census.

## 5. Lessons this produced

`CRAFT-O-22` (a trace is a lossy instrument: count text too) · `CRAFT-O-23` (separate designed test
failures from misfires before computing a failure rate) · `CRAFT-O-24` (exit code says *that*, text
says *what*) · `CRAFT-O-25` (`mkdir -p` scratch before `cd`; never `/tmp`) · `CRAFT-O-26` (harness
error codes are a second channel; read them as instructions) — all in `03-pod-ops-code.md`.
