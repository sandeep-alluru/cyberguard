# LAUNCH PACKET — CyberGuard VulnTriage (evaluation programme)

> **INTERNAL.** Not for publication, not for the repository's public face, and not for a
> prospective reader. This packet states the state of the record, what was deliberately left out
> and why, how ready each part is, and the decisions that only the owner can take. It sits in the
> repository because the repository is where the programme's record lives — **it is marked internal
> because it contains judgements and open questions that the evaluation itself does not.**

**Prepared:** 2026-10-25 · **Repository:** `sandeep-alluru/cyberguard` (private) ·
**Scope:** the evaluation programme repository, as rebuilt on 2026-10-25.

---

## 1. Current state

### 1.1 The repository

| | |
|---|---|
| **Name** | `sandeep-alluru/cyberguard` |
| **Visibility** | **private** (verified with `gh` after the push) |
| **Action taken** | **updated in place**, not duplicated — the name was already taken by the owner's own v3-era workspace repository, so the brief's "update it, never duplicate" branch applied |
| **Default branch** | `master` |
| **Contents now** | 132 files: methodology and governance, public-benchmark results with their receipts, corpus-qualification and gate discipline, the eval tooling, the boundary charter, the inventory, and this packet |
| **Before** | 430 files: the v3-era build workspace, including training candidates, the held-out set, the internal probe sets, session archives and host-specific scripts |

The previous contents remain in the git history. The replacement is deliberate, and the reasons are
recorded in `INVENTORY.md` §2.

### 1.2 The product

**CyberGuard VulnTriage** — CVE → CWE, plus CVSS, impact and prioritisation. Release artefact
name `CyberGuard-Vuln-4B`. LoRA **r = 32** on **`Qwen3-4B-Instruct-2507`**, evaluated on **public
third-party benchmarks only**.

### 1.3 The state of the record — the honest version

| | state | source |
|---|---|---|
| **The arm of record (v3)** | **NO-SHIP** on the registered criteria. 10 rows decided — 4 PASS, 6 FAIL. Two measured regressions: the defensive-behaviour gate `G-A2` (the tuned model emitted a complete, copy-pasteable attack command inside an otherwise defensive answer, and refused a legitimate defensive VPN request). | `docs/V3-EVAL-FINAL-RESULTS.md`; `docs/V3-OWNER-DECISIONS.md` `OWNER-D13` (2026-10-01) |
| **Is v3 a release candidate?** | **No.** The release table does not carry it forward; it is retained as the arm of record, the baseline the next arm is measured against. | `docs/BAR-SHEET.md` §1.1 |
| **The corpus Data Gate** | **BLOCKED — NOT PASS.** All three registered limits (unsafe < 1 %, off-topic < 2 %, shallow < 5 %) are **NOT MEASURED**; the §6 confirmation draw has not been executed; the non-statistical criterion **cross-row leakage FAILED**. | `qualification/data/v4/DATA-GATE.json` |
| **The held-out leak (F-8)** | **604 rows** carrying a held-out identity, covering **499 of the 500** held-out rows. Prompts byte-identical; 499 of the 604 also carry the held-out row's own answer content. Present in v3's SFT file and mixture, and in the corpus/mixture lineage through v4. | `docs/ESCALATION-F8-HELDOUT-CONTAMINATION.md`; `qualification/.../f8c-holdout-leak-trace.json` |
| **The corpus candidate** | `corpus-v7-f8clean.jsonl`, 108,536 rows, sha256 `066937a3913596f9…`. `ASTRA-D30`: remove nothing from the corpus; restore v7 as the candidate. | `docs/ASTRA-DECISIONS.jsonl` `D30` |
| **The training arm** | `mixture-v7-f8clean.jsonl`, 366,755 rows, sha256 `f2485d853400c482…`, refusal share exactly 4.9098 %. **Trained from BASE**, `RESUME_ADAPTER` unset. | `docs/ASTRA-DECISIONS.jsonl` `D32`; `OWNER-D1` `W-5`/`W-6` |
| **Training run state (2026-10-25, ~09:54 CDT)** | A **30-step throughput pilot** completed: 219.9 s wall, 191.5 s train, **2.506 samples/s** measured on the local GPUs, **epoch 0.024** over a 20,000-row subset, from base, no warm start. It is a **measurement of the machine**, not a release arm. **No release v4 adapter exists.** The pilot's adapter is deliberately not published; its receipt is. | `results/receipts/cyberguard-lora-v4-PILOT.json` |
| **The release shape** | **Six artefacts, none built**: merged bf16 weights → GGUF bf16 → Q4_K_M → `generation_config.json` (512 new tokens) → model card → hash-frozen bundle. | `docs/RELEASE-SHAPE.md` §1 |
| **The serving party** | **UNRESOLVED.** Until it is named, a release can be shipped as an artefact bundle but cannot honestly claim to be served. | `docs/RELEASE-SHAPE.md` §2 |

### 1.4 One correction the record itself makes

The false-refusal ceiling is **≤ 5.13 %**, not ≤ 5.27 %. The 5.27 % rendering was built on the
pre-repair 4.27 % base figure; the base was re-measured at **4.13 %** (31/750) and the bar is
*base + 1.0 pp*. The change was recorded as a **correction, not a decision**
(`docs/PRODUCT-CONTRACT.md` §9; `PLAN-LEDGER.md` `E-1`). The operative form — *no worse than the
untrained base* — is unchanged, and v3 fails either way (29.07 %, 5.67× the 5.13 % ceiling).

---

## 2. Exclusions, and why each one is excluded

The repository's boundary is set out in `EVALUATION.md` §4 and enforced by `verify_repo.py`. What
follows is the exclusion list as a decision record, not a summary.

| excluded | why | when it may change |
|---|---|---|
| **Model weights, LoRA adapters, GGUF, merged checkpoints** | They are the release artefact, not the evaluation record. There is no shippable model: v3 is a NO-SHIP. Publishing an adapter would publish a claim the record has withdrawn. | after H-3, with the artefacts |
| **Training data, corpora, mixtures, SFT files** | Corpus qualification turns on data separation; publishing the rows destroys the instrument being qualified. The lineage survives as receipts with counts, hashes and verdicts. | never for the training rows; receipts are enough |
| **The 500-row held-out set** | Held-out data is explicitly out of bounds — and it is exactly what the F-8 leak was about. | never |
| **The internal probe sets** | The standing boundary is that internal instruments are diagnostic and decide nothing. Publishing them as results would misdescribe them. | publishable as *method* later, if wanted; not as evidence |
| **A model card** | Its content *is* the bar sheet's numbers and their limits. It cannot exist before the new arm's H-2 row does. | after H-2 |
| **A dataset card for the training corpus** | It would assert a qualification that has not happened. | after the Data Gate reads PASS |
| **Any claim that v3 ships** | The release table does not carry it forward; `OWNER-D13` records NO-SHIP. | only via a new arm that clears the bars |
| **Credentials, tokens, environment files, host configuration** | Never. | never |
| **Internal hostnames, IP addresses, absolute internal paths** | The repository outlives the machines. The setup is described generically, the way the other launch repositories were scrubbed. | never, for this repository |
| **Session transcripts, harness archives, chat logs, downloaded papers** | The working record and reference material, not the programme's product. | never |
| **The pilot adapter** | A pilot adapter is not a release candidate — its receipt records epoch 0.024. The *receipt* is published, because it sizes the real run. | never; the receipt is the artefact |

### 2.1 One residual exposure, stated plainly

**The repository's git history still contains the pre-rebuild tree**, including
`v2/holdout500.jsonl` (the 500-row held-out set, 1.85 MB) and the `v2/data/probe-set-*.jsonl`
internal probe sets. They were tracked and pushed on 2026-10-05, before this rebuild, and they are
absent from the current tree.

- The repository is **private**, so the exposure is limited to the owner and anyone the owner grants
  access to.
- The held-out set is derived from a public dataset.
- Removing it from history means rewriting the branch, which **destroys the provenance** of every
  commit the repository has ever carried — including the v3 build record the programme's own
  argument depends on.

**This is an owner decision, not a build decision.** It is listed in §5. It was not acted on.

---

## 3. Readiness

| asset | ready? | notes |
|---|---|---|
| **The evaluation programme repository** | ✅ **ready** | private, pushed, boundary-checked, self-verifying (`verify_repo.py` exits 0) |
| **The boundary charter** (`EVALUATION.md`) | ✅ ready | options considered, the boundary, and the seven-step path to a shippable model repository |
| **The inventory** (`INVENTORY.md`) | ✅ ready | generated from the build manifest; 125 imported files with source path and source sha256 |
| **The demo video** | ✅ ready | see §6 |
| **A shippable model** | ❌ **not ready** | v3 is a NO-SHIP; no release arm exists |
| **A qualified corpus** | ❌ not ready | the Data Gate is BLOCKED; the §6 confirmation draw has not been run |
| **The release artefacts** | ❌ not ready | none of the six is built |
| **A serving path** | ❌ not ready | the serving party is unresolved; the local quantiser is buildable but not launched |
| **A public launch** | ❌ out of scope | the repository is private and licensing is deferred by the owner |

---

## 4. What is in flight, and what it is waiting on

| work | state | waiting on |
|---|---|---|
| **The clean arm (H-1)** | OWNER GO (`ASTRA-D25`, `ASTRA-D26`); the arm, mixture and base are fixed; the throughput is measured | the run itself — and the §6 confirmation draw, which is the measurement the Data Gate repair preregisters |
| **The Data Gate repair** | `ASTRA-D30`: fix the measurement first; the re-measurement is to be preregistered with a named reviewer pair and a decision rule | a reviewer pair that did not see the development rows |
| **The evaluation of the new arm (H-2)** | open | the arm |
| **The release ruling (H-3)** | open | H-2 |

---

## 5. Owner-only decisions

None of these is a technical question, and none of them was taken here.

1. **The git-history exposure in §2.1.** Rewrite the branch to purge the held-out set and the
   internal probe sets from history, and lose the commit provenance — or keep the history and accept
   a private repository whose past contains data the present boundary forbids. *Recommendation:
   keep the history. The repository is private, the data is derived from a public dataset, and the
   provenance of the v3 build is itself evidence the programme's argument leans on.*
2. **The serving party.** Who serves the model, and under what terms. Until this is named, the
   release is an artefact bundle and not a served model, and the model card's *how to run it*
   section would be an untested claim. `RELEASE-SHAPE.md` §2 lists the two options it saw.
3. **The local quantiser.** Buildable on this host, and **not launched** without a ruling.
4. **Whether the H-1 run proceeds before the §6 confirmation draw completes.** `OWNER-D3` and
   `ASTRA-D25` say the run is GO; `ASTRA-D30` says the gate measurement is repaired first and the
   re-measurement preregistered. These can be read as sequential or as parallel — only the owner can
   settle the reading, and it matters, because a run against an unqualified corpus is exactly the
   failure the Data Gate exists to prevent.
5. **Licensing.** Explicitly deferred. No licence file is in the repository, and none is discussed in
   `EVALUATION.md`.
6. **Public vs private.** The repository is private. Whether the evaluation programme should ever be
   made public — and if so, in what redaction — is an owner decision. The boundary already answers
   the technical half of it: everything that identifies the machines or the data stays out.

---

## 6. Launch assets

| asset | file | duration | coverage |
|---|---|---|---|
| **Demo video** | `cyberguard-evaluation-demo.mp4` (in the launch workdir — **not** in the repository) | **16 min 13 s** (973 s), 1920×1080, 25 fps, H.264 + AAC, 27.5 MB | the evaluation story end to end, in the order below |

**What it covers**, and where:

| # | segment | what is on screen |
|---|---|---|
| 1 | what VulnTriage is, and what this repository holds | title card; the four contents and the four exclusions |
| 2 | the shape of the repository | live terminal: the tree, the file counts, the commit log |
| 3 | the rule everything follows | card: *public third-party benchmarks only* |
| 4 | the pre-registered bars | live terminal: `docs/BAR-SHEET.md` §2, all eight bars with their n, their bar and their status |
| 5 | the release table | live terminal: which arms are carried forward, and why |
| 6 | v3's verdict | live terminal: the gate table — 4 PASS, 6 FAIL, and the row that carries the weight |
| 7 | v3's public-benchmark numbers | live terminal: B4 HarmBench per arm, B1 CTI-RCM per arm, B5 CTI-MCQ per arm, B3 false-refusal per arm, B3b refusal integrity per arm |
| 8 | the corpus gate | card, then live terminal: the Data Gate receipt, verdict and all three registered limits |
| 9 | the held-out leak | live terminal: the F-8 trace, stage by stage — 604 rows, 499 of 500 |
| 10 | why the next arm trains from base | card, then live terminal: the pilot receipt — 2.506 samples/s, epoch 0.024 |
| 11 | the seven steps to a shippable model repository | card, building one step at a time |
| 12 | the boundary, enforced | live terminal: `verify_repo.py` running to PASS |
| 13 | what was deliberately left out | live terminal: `INVENTORY.md` §2 |
| 14 | where to read it, and the whole story | card |

The video was produced from the same scrubbed repository copies that are published here, by screen
capture of the tooling and the records, plus title and structure cards. **Nothing on screen is a
model weight or adapter, training or held-out data, a credential, or an internal hostname or
path** — the on-screen commands are all relative-path reads of this repository's own published
files. It has **not** been uploaded anywhere; publication is the owner's to do.

The build is reproducible from the launch workdir: `demo_content.py` holds the narration and the
on-screen material, `make_demo.py` renders the cards, drives the screen capture through tmux and
assembles the file, and `make_demo.py --reuse-audio` re-uses the existing narration clips.

---

## 7. How to verify this packet

| claim | the check |
|---|---|
| the repository is private | `gh repo view sandeep-alluru/cyberguard --json visibility,isPrivate` |
| the boundary holds | `python3 verify_repo.py` — exits 0 only when identifiers, credentials and off-allow-list row files are all absent |
| what is in the repository and where it came from | `INVENTORY.md` |
| the boundary, and why it is where it is | `EVALUATION.md` |
| the v3 verdict | `docs/V3-EVAL-FINAL-RESULTS.md` |
| the corpus gate | `qualification/data/v4/DATA-GATE.json` |
| the held-out leak | `docs/ESCALATION-F8-HELDOUT-CONTAMINATION.md` |
| the release shape and the six artefacts | `docs/RELEASE-SHAPE.md` |
| the current rulings | `docs/ASTRA-DECISIONS.jsonl`, `docs/OWNER-DECISIONS.md`, `docs/V3-OWNER-DECISIONS.md` |
| the demo video's content and length | `ffprobe -show_entries format=duration cyberguard-evaluation-demo.mp4` |

---

*Internal. Prepared from the programme record; the programme tree was read, not written.*
