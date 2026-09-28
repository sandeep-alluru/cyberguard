---
title: CyberGuard — DSH session audit, all 16 sessions: what happened, why every research session died, and what survived
issued_at: 2026-09-26T18:10:00-05:00
project: CyberGuard
status: current
kind: audit
---

# CyberGuard — DSH session audit · CEO brief

**Updated** 2026-09-26 18:10 CDT · **Scope** all 16 DSH sessions under the cyberguard workspace
(2026-09-26, 15:05–17:12 CDT), plus run logs, the research brief, and README.
**Method** decompressed every `session.v3.jsonl.zstd`, built per-session digests, cross-read
`logs/flash-session.*`, `logs/finish-chain.log`, and the brief on disk.

## 1 · The big picture

One day's work on **CyberGuard: a 4B defensive-security model** — a Qwen3-4B LoRA fine-tune on
the Trendyol cyber-defence dataset (host `spark-40ee`), plus a research effort to produce a
design brief. The research effort was launched against a **new local model endpoint
(`spark-local/qwen3.8-flash-next`) that was unhealthy**, and **every research session died
mid-flight from request timeouts**. Sixteen sessions, zero completed research objectives. Two
exceptions prove the rule: the two "Reply with the word OK" smoke tests — one answered, one
didn't — and this audit session.

The work itself was **good**; the plumbing killed it. What survived is genuinely valuable and
listed in §6.

## 2 · Session tree (16 sessions, depths 0–3)

```
session-37d5fec1  [headless run #1] "4B Cyber Defence Model Research Brief"  ── died 16:04 (rc=124)
├─ aadb5359  Research SLM cyber capability gap          ── died (LLM retry/timeout)
│  ├─ c00f6cb2  Cybench/CTF small-model scores          ── died
│  ├─ 7cbc70f8  Small cyber LLM papers (CyberPal…)      ── died
│  └─ efc0fa11  RAG vs fine-tuning & ensembles          ── died
│     ├─ 2a694eab  small models as RAG consumers        ── died
│     └─ 9f89167f  RAG vs FT deltas                     ── died
├─ fcc7f57c  Research cyber data strategy & refusal     ── died
│  ├─ 183aadf0  Refusal/alignment-tax evidence          ── died
│  ├─ cac25b83  Benchmark contamination evidence        ── died
│  └─ 4e270271  In-training misalignment detection      ── died
session-218f9953  interactive "plan a cyber model" (deepseek-flash, stalled after mid-session model switch)
session-3d50bed0 / session-fdd688f8  "Reply with the word OK" endpoint smoke tests (1 died, 1 OK after retries)
session-32a16e31  [headless run #2] incremental research brief ── died ~16:24, sections 1–2 landed
session-72afaf76  ← the session that produced this brief
```

## 3 · Root cause of the wipeout

All 12 research sessions end with `llm/retry` → `{"message": "Request timed out.",
"code": "TIMEOUT"}` against provider **`spark-local`** (24 retries logged; policy: 10 retries,
3 s→30 s backoff). Every session tail shows the same pattern: mid-step, waiting on a retry that
never resolves. Parents blocked on `job_output` of children that never returned — one flaky
endpoint, fanned out across a depth-3 tree, became 12 simultaneous failures.

The two "Reply with the word OK" sessions at 15:40–15:41 confirm the endpoint was already
failing on trivial requests: one never produced an assistant reply; the other needed retries.
Settings backups trace the whole arc: switched to `spark-local` at 15:14 CDT, again at 16:10,
restored to `deepseek-official/deepseek-flash` at 16:26.

## 4 · Timeline (CDT)

| time | event |
|---|---|
| 15:05 | `finish-cyberguard` chain starts, waiting on training run `cyberguard-lora-v1` |
| 15:14 | Flash run #1 (50-min timeout) → session-37d5fec1 + 10-agent research tree |
| 15:38–15:41 | Interactive planning session stalls after model switch; OK smoke tests: endpoint sick |
| 15:53–16:04 | `resume-flash-session.sh` tries to resume → **crashes: `$3: unbound variable`** + /proc races; run #1 ends rc=124, scraped "brief" = 177 bytes of the agent's last message |
| 16:10 | Flash run #2 (3 h budget, reasoning on) → session-32a16e31, writes brief incrementally |
| ~16:24 | Run #2 dies mid-Section 3 — well before budget; settings restored 16:26 (looks like a manual plug-pull) |
| 17:12 | Audit session begins |

## 5 · What the flash brief is (and why run #2 nearly worked)

Run #1 scraped the agent's *final message* as the brief — 177 bytes of garbage when the session
died mid-thought. Run #2 changed the contract: **the model writes the brief file incrementally,
rewriting the whole file after each section.** That design change is the only reason anything
survived: `logs/flash-research-brief.md` holds complete Sections 1–2 before the death.

## 6 · What survived (the valuable part)

- **`logs/flash-research-brief.md`** — Sections 1–2 written to disk, and they're good: honest
  capability-gap framing ("force multiplier for Tier-1 triage, not an analyst"), a concrete CPT
  mixture table with general-replay ratios, explicit uncertainty labeling. Sections 3–5 are
  still `(placeholder)`.
- **Sections 3–5 content is recoverable** — run #2's raw output stream in
  `logs/flash-session.err` contains drafted text (including the Section 5 falsification
  experiment: pilot ladder on 500M/1B bases, ~2–4 B tokens, ≥30 % frontier-gap-closure decision
  rule) that the model reasoned out but never wrote to the file.
- **~10 primary papers downloaded + extracted as text** in `research_tmp/`, `research-tmp/`,
  `resbench/` — CyberPal (arXiv 2510.14113), CyberLLMInstruct, Cybench, NYU CTF Bench,
  InterCode-CTF, CVE-bench, CyberSOCEval, Lost-in-the-Middle, NoLiMa, small-ensemble malware
  paper. Reusable without re-fetching.
- **Solid empirical findings made before the deaths**:
  - The Trendyol corpus has one system prompt on every row, templated boilerplate answers, and
    an escaping bug; Apache-2.0; 53,202 rows; created 2025-07-30 — *after* the base model's
    release window, a real data-timing concern.
  - 15+ unauthorized mirrors of the dataset exist on Hugging Face.
  - NYU CTF Bench: LLaMA-3-70B and Mixtral-8×7B solved **0 %** of challenges.
  - Negative findings correctly reported ("CyberSecInstruct" / "SecInstruct" do not exist on
    arXiv).
- **Training state**: `receipts/` and `evals/` are empty — no harvested artifact for
  `cyberguard-lora-v1` in this workspace. Its fate lives on `spark-40ee`, not in these logs.

## 7 · The agents behaved well

Prompts contained **wrong arXiv IDs** (Cybench was cited as …08918, actually **2408.08926**;
InterCode actually **2306.14898**) — agents caught and corrected these instead of citing
garbage. One agent detected a corrupted tool result and explicitly discarded it. Search quality
was poor, so agents fell back to direct arXiv fetch + `pdftotext` — the right call. The
incremental-write contract in run #2 paid for itself immediately (§5).

## 8 · Friction observed (harness-level, fixable)

1. **`/tmp` is not shared between bash calls** — at least three agents (and the audit session)
   wasted turns discovering this. State it in headless prompts: "work in the workspace."
2. `resume-flash-session.sh` has a **`$3: unbound variable` bug** (line 24) and races on
   `/proc/<pid>/cmdline`.
3. A 10-retry / 30 s-backoff policy inside a 50-minute headless budget means one flaky endpoint
   can silently eat the entire run.
4. Reasoning mode leaked the model's internal monologue (meta-commentary about tool budgets)
   into `flash-session.err` — noisy, though in this case lucky (§6, recoverable sections).
5. Fan-out of 12 sessions across a depth-3 tree on an **unverified** endpoint amplified one
   point of failure into a total wipeout. Smoke-test first, cap depth until stable.

## 9 · Recommended next steps

1. **Finish the brief** — assemble Sections 3–5 from the recoverable content in
   `logs/flash-session.err` + the extracted papers, in a session on a healthy model. ~30 minutes
   of work, not a research run.
2. **Check `spark-40ee` for `cyberguard-lora-v1`** and harvest or relaunch with receipts.
3. Fix the resume script (`$3` binding, /proc guards) and add an **endpoint health gate** in
   `run-flash-session.sh` before any launch.
4. Decide whether `spark-local/qwen3.8-flash-next` is stable enough to run on: it is answering
   now (the audit session runs on it), but the evidence from 15:14–16:24 says it was not.

**Needs your decision:** (a) finish-the-brief now vs. relaunch the full research fan-out on a
verified endpoint; (b) status check on `cyberguard-lora-v1` (harvest vs. restart).

---
*Sources: 16 × `session.v3.jsonl.zstd` under the cyberguard workspace's DSH session store;
`logs/flash-session.log`, `.err`, `-resume.log`, `.stdout`; `logs/flash-research-brief.md` (+
archived 177-byte `.failed` predecessor); `logs/finish-chain.log`; `README.md`; settings backups
`~/.dsh/settings.yaml.bak-*`. Digest artifacts under `research-tmp/dsh-digest/`.*
