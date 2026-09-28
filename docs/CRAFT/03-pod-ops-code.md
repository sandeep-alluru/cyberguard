# CRAFT 03 — Fleet ops, shell discipline and code idioms (28 lessons)

Mined from the CyberGuard operation's ops incidents (`LEDGER.md` rounds 1–7 and the capability box),
the harness/launcher/monitor scripts in the repo root, `RUNBOOK-qwen-flash-serving.md`, and — for
lessons 22–26 — the **DSH session traces themselves** (`analyze_toolcalls.py` over
`research-tmp/trace/`; see `05-toolcall-trace.md`). Every entry here is a *code idiom*, not an
attitude: the rule is written so it can be pasted.

Grades: **GOLD** / **STANDARD** / **ANTI** (a mistake we actually made). **Ancestor** = the pod-ops
corpus entry that already covered it (`00-crossref-podops.md`): an ANTI with an ancestor is a
**process failure**, not a new discovery.

---

**CRAFT-O-01 | Derive liveness from `/proc` and log *growth*, never from the log tail**
- Situation: the crash scan in `monitor-cyberguard.sh` read `tail -200` of a run-name log that
  yesterday's crashed attempt had already written to.
- Action: on relaunch the monitor false-fired `CRASH` 22 s in, reporting an old traceback; it now
  reads **only bytes appended after monitor start**.
- Rule: liveness = a `/proc` entry for the exact pid **plus** monotonic log growth between cycles.
  Any "crash" conclusion from log text must be scoped to text written after the current start epoch.
- Evidence: LEDGER review-#1 window. Grade: GOLD.

**CRAFT-O-02 | A process scan can match its own pattern string — five distinct forms (ANTI)**
- Situation: `/proc` scans and `pgrep -f` guards are used to prove "no process is running" and
  "training is alive".
- Outcome: five separate self-match incidents in one operation:
  1. `pgrep -f` matching the scanner's own command line (the classic);
  2. the monitor-arming scan matching its **own launcher cmdline**;
  3. the final **GPU-clean scan printing `BUSY`** because it matched its own `run-cap` pattern string;
  4. a bracketed pattern (`[t]rain`) that failed because the same text appeared **elsewhere** in the
     same cmdline;
  5. a **pattern-language mismatch** (`grep` glob vs regex — see O-03) reading as "process gone".
- Rule: scan `/proc/<pid>/cmdline` in a loop with a **shell `case` glob** and never echo the bare
  pattern into any command line that the scanner itself will read:
  ```bash
  for p in /proc/[0-9]*; do
    cmd=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$cmd" in *train_cyberguard.py*) echo "ALIVE pid=${p#/proc/}";; esac
  done
  ```
  A self-matching probe can never support a claim about absence.
- **Sixth form (observed live, 2026-09-27 20:3x, while this corpus was being written):** a *waiter*
  built as `for p in $(pgrep -f "codex exec"); do while kill -0 "$p"; do sleep 15; done; done` — the
  `pgrep` ran inside a `bash -c` whose own command line contained `codex exec`, so the waiter captured
  **its own pid** and waited on itself **forever**, holding a job slot after the work it was waiting
  for had finished.
- **Seventh form (observed live, 2026-09-27 21:0x, same session):** a *kill* built as
  `for p in $(pgrep -f "codex-linux-x64.*codex exec"); do kill "$p"; done` — the pattern matched the
  kill command's own cmdline, so it **killed the shell it was running in**, terminating the script
  mid-way (the prompt-file edit it was performing never completed). The recovery is the same idiom as
  above: scan `/proc` with a **bracketed** pattern and skip `$$`:
  ```bash
  for p in /proc/[0-9]*; do
    [ "$p" = "/proc/$$" ] && continue
    cmd=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$cmd" in *code[x]-linux-x64*) kill "${p#/proc/}";; esac
  done
  ```
  Both forms share one root cause: **the pattern text lives in the command line that the scan reads**.
- Evidence: `watch-cap.sh`, `monitor-cap.sh`; LEDGER capability-box close (R25 lesson #6) and the
  2026-09-27 review-loop entry; `00-crossref-podops.md` Class 1. Grade: ANTI. **Ancestor: A14 + A10 —
  known rule, re-paid seven times.**

**CRAFT-O-03 | A glob handed to `grep` is not a regex — and `grep -q` fails *silently***
- Situation: `run-eval-chain.sh` armed its wait-loop with `grep -q "*train_cyberguard[.]py*"`.
- Outcome: a leading `*` is a literal in BRE, so the pattern **never matched**; the chain concluded
  the GPU was free, launched `merge_equiv` (died: adapter not saved) and then launched the evaluator
  **during training**. The trainer slowed to ~27 s/it for ~5 minutes; no corruption. Orphan killed by
  `/proc` case-scan, the misleading base-only partial receipt removed, stray logs preserved
  (`*.stray-*`).
- Rule: liveness checks use shell `case` globs (O-02). If you must `grep`, pass an explicit regex
  (`grep -qE 'train_cyberguard[.]py'`) and assert the negative case in a test:
  `printf 'x train_cyberguard.py\n' | grep -qE 'train_cyberguard[.]py' || echo BUG`.
- Evidence: LEDGER 04:10–04:17 incident; `run-eval-chain.sh` (`alive()` rewrite). Grade: ANTI.
  **Ancestor: A06 class ("a command that succeeds can still be wrong") + F5 pattern-language form.**

**CRAFT-O-04 | `sed ... && next-step` chains hide non-matching patterns**
- Situation: a mid-run log-rename used `sed -i 's/…cap-replay.log$/…/'`, but the pattern was not at
  end-of-line.
- Outcome: `sed` exited 0 with **no substitution**; because the edit was chained with `&&`, the
  following step ran against the **old** path. Caught by `grep -c` before it consumed the file.
- Rule: after any `sed` rewrite, assert the change landed before using the artifact:
  `sed -i 's|old|new|' f && grep -q 'new' f || { echo "EDIT-DID-NOT-LAND"; exit 1; }`
- Evidence: LEDGER capability-box staging. Grade: ANTI.
  **Ancestor: EXT-3 (`00-crossref-podops.md`).**

**CRAFT-O-05 | One file per transfer, then verify every hash — a multi-path `scp` can fetch nothing**
- Situation: `scp host:'a b c' .` with several remote paths inside one quoted string.
- Outcome: it succeeded (exit 0) and fetched **nothing**. Fix: one `scp` per file plus a manifest
  loop that verifies `sha256sum` per file and exits non-zero on the first mismatch.
- Rule: transfers are per-file with `set -e`, and the harvest ends with a printed
  `HARVEST-COMPLETE` only after every hash matches the remote manifest.
- Evidence: `harvest-v1.sh`, `harvest-cap.sh`; LEDGER capability-box harvest. Grade: ANTI.
  **Ancestor: A05/A06 class — known rule, re-paid.**

**CRAFT-O-06 | Exit codes from backgrounded/detached remote commands are advisory**
- Situation: launching a long job over `ssh` in the background returned **exit 124** while the job
  was running perfectly.
- Outcome: an exit-124 "failure" was nearly acted on; `/proc` inspection showed the job alive and
  writing.
- Rule: for detached work, the exit code of the launcher is not the status of the job. Verify with a
  `/proc` scan for the pid/path and a log-growth check, then record *that* as the evidence.
- Evidence: LEDGER rounds; `watch-eval.sh`. Grade: ANTI. **Ancestor: A05 class.**

**CRAFT-O-07 | Watchdog alerts need an `acknowledged/` directory and a one-line cause**
- Situation: two `ALERT-EVAL` files fired from the *old* monitor's last cycle racing the new chain's
  arming 11 s later, and one from the chain that had written its done-line into a log that was then
  renamed.
- Action: each ALERT was acknowledged, **moved to `logs/acknowledged/`**, and given a ledger line
  stating the mechanism.
- Rule: never delete an alert and never leave it ambiguous — move it aside with a cause. A monitor
  whose alerts can be dismissed silently is worse than no monitor, because it manufactures a false
  all-clear.
- Evidence: `logs/acknowledged/`; LEDGER 05:12, 05:17:26. Grade: GOLD.

**CRAFT-O-08 | Detach durably, and refuse to start twice**
- Situation: an 8-hour operation with two crashes had to lose **zero** log evidence.
- Action: launch with `setsid nohup … > logfile 2>&1 &` to a durable path, plus a `/proc`
  refuse-to-start-twice gate before launch.
- Outcome: no lost logs across the whole operation; the aborted wrong-mask run's evidence was
  preserved by **renaming rather than deleting** (`…log.wrong-mask-20260927`,
  `adapters/…aborted-wrongmask-20260927`).
- Rule: detach from the shell, log to a durable path, gate the start, and move aborted artifacts
  aside instead of removing them — a wrong run is evidence about the instrument.
- Evidence: `run-cyberguard-train.sh`, `run-cap.sh`; LEDGER 00:46, 01:29. Grade: GOLD.

**CRAFT-O-09 | No pipes in the launch or receipt path**
- Situation: a pipeline's exit status is the **last** command's status, so a failed first command can
  vanish inside a "successful" pipeline.
- Action: the launch path and every receipt-producing command run without pipes; failures propagate
  as non-zero exits that the chain can see.
- Rule: `set -euo pipefail` at the top of every script, and keep the *recorded* commands pipe-free.
  When a pipe is unavoidable, use `PIPESTATUS` and record it.
- Evidence: corpus R26/F54; `run-cap.sh`, `harvest-cap.sh`. Grade: GOLD.
  **Ancestor: F54/R26 — known rule.**

**CRAFT-O-10 | Sync discipline: md5 the whole path before launch, re-verify after every fix**
- Situation: code lives on the workstation and runs on `spark-40ee`; silent drift would mean the
  receipt describes code that never ran.
- Action: before launch, md5-compare **every** file on the training path local↔remote (zero drift);
  after any mid-run fix, redeploy and require `REMOTE-TEST-PASS` before continuing.
- Outcome: every receipt in the operation is attributable to a known revision; the tests ran on the
  remote too, not just locally.
- Rule: a run owns a revision set. Hash it before launch, record it in the receipt, and re-hash after
  any edit. Running tests locally is not evidence about the remote host.
- Evidence: LEDGER 00:25, 01:45–01:55 (`REMOTE-TEST-PASS`). Grade: GOLD.

**CRAFT-O-11 | Isolate by file, not by memory**
- Situation: the flash-serving box had to remain untouched during an 8-hour training/eval operation.
- Action: `~/.cyberguard-env` exports root/venv/GPU for the project; every script sources it instead
  of relying on a remembered convention.
- Outcome: `spark-8cf2` was never touched, across two trainer crashes on the other host.
- Rule: isolation is a file that the scripts read, not a rule the operator remembers. Encode the
  blast radius in the environment.
- Evidence: `~/.cyberguard-env`; `00-crossref-podops.md` Class 3 item 10. Grade: GOLD.

**CRAFT-O-12 | Put remote commands in script files, never inline in quoted `ssh` strings**
- Situation: an inline `ssh host '…complex quoting…'` watchdog command produced a **false
  `CHAIN-DIED`**.
- Action: the waiter became a file (`watch-eval.sh`, `watch-cap.sh`) copied to the host and executed.
- Rule: quoting across `ssh` is a lossy channel. Ship a file, run the file, and keep the same file
  under version control — then the command you debugged is the command that runs.
- Evidence: LEDGER 05:17; `watch-eval.sh`. Grade: GOLD.

**CRAFT-O-13 | Make long evals survive their own death: per-phase receipts, resume, self-budget, timeout backstop**
- Situation: a 7-phase capability box on a borrowed 3-hour window, where a crash at phase 6 would
  have cost every earlier phase.
- Action: `cap_harness.py` writes a durable receipt **per phase**, can resume from them, tracks a
  180-minute self-budget, and carries a hard timeout backstop; generation phases checkpoint
  `.partial.json` every 25 items with an ETA.
- Outcome: the box finished in **16.8 min** with all 7 receipts; the earlier 500-row eval similarly
  survived a deliberate kill mid-run (`*.batch1-slow-20260927` preserved, `exit=137` recorded).
- Rule: the unit of durable work is the phase, not the run. Write the receipt as you go; assume the
  process dies at the worst moment.
- Evidence: `cap_harness.py`, `eval_cyberguard.py`; LEDGER round 6. Grade: GOLD.

**CRAFT-O-14 | The serving invariant: per-slot context = `-c` / `--parallel`**
- Situation: a llama-server slot was silently halved: `--parallel 1 → 2` while `-c` stayed 262144.
- Outcome: per-slot context fell to 131,072 and the client's `contextWindow` had been set **equal**
  to it — zero headroom — which is how a long session met a poisoned/collapsed state.
- Rule: never raise `--parallel` without raising `-c` by the same factor, and never set the client's
  `contextWindow` equal to the per-slot context; keep it strictly below. Assert the invariant in the
  unit file's comment and in the runbook.
- Evidence: `RUNBOOK-qwen-flash-serving.md` §5. Grade: GOLD.

**CRAFT-O-15 | `curl -o /dev/null -w '%{http_code}'` without `-f` returns 0 for HTTP 4xx/5xx**
- Situation: a "is the model ready?" check that only inspected curl's exit status.
- Outcome: it passed while the model was still loading; a 400 was invisible.
- Rule: readiness = HTTP **200** *and* a semantic probe (`/slots` returns the expected shape; a real
  completion returns non-empty content). Status codes are the contract; exit codes are not.
- Evidence: `RUNBOOK-qwen-flash-serving.md` §6. Grade: GOLD.

**CRAFT-O-16 | Inside the DSH sandbox you cannot see host processes — use `systemctl --user` or `ssh`**
- Situation: `ss -tlnp` / `ps` run under `bwrap --unshare-pid`, so they show a private pid namespace.
- Outcome: two "clean" conclusions were artifacts of looking at the wrong process table.
- Rule: host-level facts come from `systemctl --user`, a real `ssh` to the host, or files the host
  writes. Record which of those the evidence came from.
- Evidence: `RUNBOOK-qwen-flash-serving.md` §6. Grade: GOLD.

**CRAFT-O-17 | A client disconnect does not cancel server generation**
- Situation: killing a local `curl`/`ssh` left the server generating and holding the slot.
- Rule: after abandoning a request, kill the **remote** client/generation too; and check `/slots`
  before concluding the server is idle.
- Evidence: `RUNBOOK-qwen-flash-serving.md` §6. Grade: STANDARD.

**CRAFT-O-18 | Check `input_tokens` on every probe — a 4-token prompt means your history vanished**
- Situation: `in=4` for a long conversation revealed llama-server had dropped the whole history (it
  cannot render `tool_result` blocks when no tools are declared).
- Outcome: two investigation results were invalidated by an empty prompt they had not noticed.
- Rule: a probe result is only meaningful with the prompt size that produced it. Log and read
  `input_tokens` alongside every probe reply.
- Evidence: `RUNBOOK-qwen-flash-serving.md` §6. Grade: GOLD.

**CRAFT-O-19 | Release the GPU cleanly and verify it with two independent readings**
- Situation: closing claim "GPU released, nothing running" — the kind of claim that is usually noise.
- Action: `nvidia-smi` utilisation/memory **and** a `/proc` scan for the project's processes, after
  killing every monitor and watcher.
- Outcome: 0 %, no processes, all monitors exited, the serving box untouched — and the last scan's
  first `BUSY` print was the scanner matching itself (O-02 form 3), corrected by reading the two
  sources separately.
- Rule: a clean-release claim cites both readings and names the monitors that were stopped. One
  reading is a guess.
- Evidence: LEDGER capability-box close; D-16. Grade: GOLD.

**CRAFT-O-20 | Catalogue the disk state before you trust a path**
- Situation: a wrapper wrote checkpoints into a directory nobody had inventoried, and the canonical
  local dirs (`data/`, `evals/`, `gguf/`, `receipts/`, `training/`, `serving/`) sat **empty** while
  every real artifact lived on the remote host.
- Outcome: a fresh agent reading the repo would conclude nothing had been produced; the postmortem
  had to flag the ambiguity.
- Rule: either populate a canonical directory or document it as intentionally remote — an empty
  directory is a lie of omission. `du -sh` + `ls` the tree you will hand over, and put the inventory
  in the ledger.
- Evidence: `docs/muse-1.3-…-postmortem.md` §8; LEDGER housekeeping. Grade: STANDARD.

**CRAFT-O-21 | Keep a runbook for the failure you had to debug at 3 a.m.**
- Situation: the flash-serving box emitted a wall of `/` for hours and every theory (sampling, tool
  schema, reasoning budget, oversized request) was tested and ruled out before the real cause
  (poisoned slot/KV state, sticky until restart) was found.
- Action: `RUNBOOK-qwen-flash-serving.md` records the signature, the ruled-out table, the one-command
  recovery, the installed 5-minute self-healing watchdog, the serving invariant, the diagnostics that
  discriminate, and the config-backup history.
- Outcome: the next agent's diagnosis is one sentence ("the first token was `/`") instead of a
  re-investigation.
- Rule: every multi-hour debugging session ends with a runbook containing (a) the signature, (b) the
  ruled-out table **with the tests that ruled them out**, (c) the recovery command and its expected
  reload time, (d) the invariant that was broken.
- Evidence: `RUNBOOK-qwen-flash-serving.md`. Grade: GOLD.

---

## Mined from the session traces (lessons 22–26)

`analyze_toolcalls.py` reads a `session.v3.jsonl[.zstd]` from the DSH session store and counts what
the instrument actually did — tool mix, harness errors, shell exit codes, normalized error
signatures. Numbers, method and the two-session comparison: `05-toolcall-trace.md`.

**CRAFT-O-22 | A tool trace is a lossy instrument — count failures from the result text, not the exit marker**
- Situation: we mined the two session traces for the operation's failure record.
- Outcome: the **main** session logged 13 `[exit code: N]` markers across 257 bash results
  (exit 1 ×10, 2 ×2, 124 ×1) and 9 results containing `No such file`, 9 `Traceback`,
  1 `command not found`. The **second** session ran **135 bash calls with ZERO exit markers** while
  3 results contained `No such file` and 3 `Permission denied`.
- Rule: the marker is emitted only sometimes. Scan **both** channels (marker and failure text),
  report both counts, and never read "no marker" as "no failure".
- Evidence: `research-tmp/trace/trace-main.json`, `trace-2.json`. Grade: GOLD.

**CRAFT-O-23 | Separate designed test failures from ops misfires before computing a failure rate**
- Situation: 4 of the main session's 13 non-zero exits are `AssertionError` tracebacks raised by the
  `cap_scorers` / `cap_probes` self-test runs (11:10–11:49) while the judges were being built.
- Outcome: counting them as ops failures inflates the shell failure rate from ~3.5 % to 5.1 % and
  points the investigation at tooling that was working exactly as designed.
- Rule: classify each non-zero exit by *who wanted it to fail* — a test rejecting a bad input is the
  test succeeding. Publish the designed-failure rate and the misfire rate separately.
- Evidence: `trace-main.json` `bash_failures`. Grade: GOLD.

**CRAFT-O-24 | The exit code tells you *that* something failed; the text tells you *what* — read both**
- Situation: a detached replay launch over `ssh` recorded `exit 124` while its own stderr read
  `REPLAY-STARTED`.
- Outcome: read alone the marker says "timeout, lost job"; read with the text it says "the remote
  process started and the launcher's session ended" — healthy work, misleading status.
- Rule: pair every non-zero exit with its first stderr line in the record. When they disagree, the
  text wins and the launch mechanism is the suspect, not the job.
- Evidence: `trace-main.json` (09-27 12:41:43); CRAFT-O-06. Grade: GOLD.

**CRAFT-O-25 | `mkdir -p` the scratch directory before you `cd` into it — and keep scratch out of `/tmp`**
- Situation: a mining step opened with `cd /tmp/cgdigest && python3 …`; the directory did not exist.
- Outcome: `exit 1` — `bash: cd: /tmp/cgdigest: No such file or directory` — losing the whole
  analysis step; the retry then had to establish that `/tmp` was the wrong home for scratch anyway.
- Rule: `mkdir -p <workspace-scratch> && cd <workspace-scratch>`. Never a bare `cd` into a path you
  have not created, and nothing you may need to cite later lives in `/tmp`.
- Evidence: `trace-main.json` 09-26 17:17:06. Grade: STANDARD.

**CRAFT-O-26 | Harness error codes are a second failure channel — read them as instructions**
- Situation: 11 harness-level errors (2.1 % of 517 calls) sat alongside the 13 shell failures:
  `edit` 8 — `FS_EDIT_NOT_FOUND` ×3 (the literal had already changed, or whitespace drifted),
  `FS_NOT_OBSERVED` ×3 (editing a file not read in this session), `FS_STALE_VERSION` ×2 (concurrent
  write); `read` 2 (`FS_NOT_FOUND`); `update_goal` 1 (`GOAL_STALE_REVISION`).
- Rule: `FS_NOT_OBSERVED` ⇒ read first; `FS_STALE_VERSION` ⇒ re-read then retry;
  `GOAL_STALE_REVISION` ⇒ call `get_goal` immediately before every `update_goal` and use the
  returned revision. Report harness errors and command failures as **two** rates — each is invisible
  to the other's scan.
- Evidence: `trace-main.json` `error_signatures`; `analyze_toolcalls.py`. Grade: GOLD.

**CRAFT-O-27 | Freeze the artifact you handed to a reviewer — and record dispositions in the ledger, not in the artifact**
- Situation: an adversarial reviewer is asked to verify a **sha256** of the document under review and to
  stop if it does not match. Revisions happened while review rounds were in flight.
- Outcome: **twice in one session** a review had to be aborted and re-dispatched because a disposition
  table was appended to the document *after* its hash was captured for the prompt — the reviewer would
  have stopped on the mismatch, and one wasted dispatch actually happened. The better architecture
  surfaced by accident: the **reviewed artifact stays frozen** while dispositions accumulate in the
  append-only ledger.
- Rule: hash the artifact, freeze it, hand over that hash, and put findings/dispositions in the ledger
  (or a separate changelog), never back into the frozen file. If a fix *must* change the artifact, that
  is a **new revision with a new hash and a new review** — never a silent edit to a document someone is
  reading.
- Evidence: `research-tmp/reviews/codex-review-{6..10}.md`; `LEDGER.md` review-loop entries; the parallel
  rule that "a reviewed artifact that is not the shipped artifact is not a reviewed artifact".
  Grade: GOLD.

**CRAFT-O-28 | The pattern you scan for lives in your own command line — including the kill command (ANTI)**
- Situation: dozens of process scans and watchers across the operation used `pgrep -f <pattern>` to find
  or *stop* a job.
- Outcome: seven distinct self-match incidents (CRAFT-O-02); the last two observed live in one session —
  a waiter that captured its own pid and waited on itself forever, and a **kill loop that matched its own
  cmdline and killed the shell running it**, silently truncating the script mid-edit.
- Rule: never `pgrep -f` a pattern that appears in the command doing the scanning; scan `/proc` with a
  **bracketed** `case` glob (`*code[x]-linux-x64*`) and skip `$$`. Prefer waiting on an **artifact** (a
  file appearing) to waiting on a process at all.
- Evidence: `analyze_toolcalls.py` trace counts; LEDGER review-loop entry. Grade: ANTI.
  **Ancestor: A14/A10.**
