# LAUNCH PACKET — CyberGuard VulnTriage

> **A CVE or advisory in → CWE + CVSS v3.1 vector and score + plain-English impact + a
> prioritisation call out — proven only on public benchmarks, with ship/no-ship bars fixed in
> advance.**

**INTERNAL.** Not for publication, not for the repository's public face, and not for a prospective
reader. This packet states the state of the record, what was deliberately left out and why, how
ready each part is, and **the decisions only the owner can take**. It sits in the repository because
the repository is where the programme's record lives — **it is marked internal because it contains
judgements and open questions that the evaluation itself does not.**

**Prepared:** 2026-10-25 · **Repository:** `sandeep-alluru/cyberguard` (private) ·
**Scope:** the evaluation programme repository, as rebuilt on 2026-10-25.

---

## 1. The product, in one line

**CyberGuard VulnTriage** — a vulnerability-triage scorer: **CVE → CWE**, plus **CVSS v3.1 vector
and score**, **plain-English impact**, and a **prioritisation call**. Release artefact name
`CyberGuard-Vuln-4B`: LoRA **r = 32** on **`Qwen3-4B-Instruct-2507`**, evaluated on **public
third-party benchmarks only**.

**This repository is the evaluation programme, not a model release.** The model does not ship today.
The arm of record — **v3** — is a **NO-SHIP** on its own criteria, the release table does not carry
it forward, and the corpus Data Gate is **BLOCKED**. The recorded path forward is a new arm trained
from the base checkpoint on a qualified corpus.

---

## 2. The benchmark table — four models, one scoreboard

Every bar was written down **before** the training run, and no bar may be restated once a new arm's
number is visible. A bar that fails is shown failing. A number we have not measured is shown as not
measured — never as a zero, never as a pass.

**Legend —** **P** = **PUBLISHED** (by that model's own authors; cited under *Sources*).
**F** = **FIRST-PARTY** (our own evaluation; the report and its receipt are in `results/`).

| model | CTI-RCM ↑<br>CVE→CWE | CTI-MCQ ↑<br>2,500 MCQs | CTI-VSP ↓<br>CVSS MAD | MITRE-FRR ↓<br>false refusal | HarmBench ↓<br>harmful / 159 | CyberMetric-500 ↑ | SecQA ↑ |
|---|---|---|---|---|---|---|---|
| **the bar** | **> 0.6780** | *report only* | **≤ 1.223** @ 2048 | **≤ 5.13 %** | **≤ 1/159** (Wilson ≤ 3.50 %) | *report only* | *report only* |
| Qwen3-4B-Instruct-2507<br>*(base, untrained)* | 0.4100 **F** | 0.4444 **F** | 1.32 **F** | 4.13 % **F** | 1/159 **F** | 0.4680 **F** | 0.6818 **F** |
| **CyberSecQwen-4B**<br>*(the direct twin)* | 0.6664 **P**<br>0.6780 **F** | 0.5868 **P**<br>0.5764 **F** | 1.223 **F** | 1.07 % **F** | 3/159 **F** | 0.4460 **F** | 0.4727 **F** |
| **Cisco Foundation-Sec-8B-Instruct**<br>*(the reference specialist)* | 0.692 **P** | 0.644 **P** | 0.802 **P** ⚠ | not measured | not comparable ⚠ | not measured | not measured |
| **CyberGuard VulnTriage v3**<br>*(arm of record — NO-SHIP)* | **0.6360 F** ✗ | 0.4648 **F** | not measured | **29.07 % F** ✗ | **0/159 F** ✓ | **0.8000 F** | **0.9364 F** |

**How to read v3's row.** v3 is the **best** of the four on CyberMetric-500 (0.8000) and SecQA
(0.9364), and it **clears** the HarmBench bar outright — 0 harmful completions in 159, the only
model in the table besides the untrained base to do so. It **fails** two bars: CTI-RCM, 4.2 pp
under a comparator measured against it on the same surface, and the false-refusal rate, where
29.07 % is **5.67×** a 5.13 % ceiling. That is why it is a NO-SHIP, and why the next arm is trained
from base rather than from v3.

**Four notes the table cannot carry in the cells.**

1. **B1's bar (0.6780) is our own re-measurement of CyberSecQwen-4B** on this programme's
   equal-terms surface — not its published 0.6664, which was measured on a different surface and a
   different protocol. Both are shown rather than one. The bar sheet withdrew the author-reported
   figure and fixed the bar on our own re-measurement (`docs/BAR-SHEET.md` §0, clause 3).
2. **The 5.13 % false-refusal ceiling** is *base + 1.0 pp*, with the base re-measured at 4.13 %
   (31/750). An earlier rendering of this bar read 5.27 %, built on a pre-repair base figure; it was
   recorded as a **correction, not a re-decision**. The operative form — *no worse than the
   untrained base* — is unchanged.
3. ⚠ **CTI-VSP is not comparable across that column.** CTI-Bench's metric for the task is mean
   absolute deviation in CVSS points, lower is better, and that is how we score it (comparator
   MAD **1.223**, base **1.32** at 2,048). Cisco's card describes CTI-VSP the same way but
   tabulates it alongside accuracy-style numbers and never states the direction, so its 0.802
   cannot be placed against a MAD. Shown, and not used as a bar.
4. ⚠ **Cisco's HarmBench figure is a different measure.** Cisco publishes a HarmBench *safety
   rate* (91.98 % for Foundation-Sec-8B-Instruct, 99.25 % with LlamaGuard) over the full suite.
   Our bar counts **harmful completions out of the 159 standard-test behaviours**. The two cannot
   be converted into one another, so Cisco's row is unmeasured here rather than guessed.

The full table with per-cell provenance, the bars of record, and the receipt path for every
figure is on the repository front page ([`README.md`](README.md)). The bars themselves are in
[`docs/BAR-SHEET.md`](docs/BAR-SHEET.md) §2, each with its population, its baseline and its status.

---

## 3. The differentiator

Most model cards tell you how good a model is. This programme tells you **how it knows**, and
publishes the parts that are unflattering. Four things, in plain language:

**1 · The bars are fixed before the run, and cannot be moved afterwards.** Every instrument's
population, baseline and threshold is written down in advance. The rule is not a convention — it is
binding: the harmful-compliance bar was fixed by supervisor ruling *before* the new arm's number
could be seen (`ASTRA-D27`), and it may not be restated afterwards.

**2 · Public third-party benchmarks only. Our own instruments decide nothing.** Every bar is a
published external suite with a public dataset and a protocol anyone can run. The programme's
self-made gates are diagnostic: they tell you where to look, and they never decide a release. This
is the direct fix for how this project failed once before — it spent a great deal of effort grading
itself with instruments it wrote.

**3 · Contamination is caught before it ships, not after.** The held-out set is 500 rows. **604
rows carrying a held-out identity were found inside a training file, covering 499 of those 500
rows**, with byte-identical prompts. It was caught by the programme's own gate — and it is the
reason the next arm trains from base instead of warm-starting from v3. A model card cannot show
you a contamination check that passed; this one shows you the check that *failed*, and what was
done about it.

**4 · We publish our own judge's agreement rate.** Where a human reviewer would normally stand in,
this is a one-person programme, so the model's own judgement stands in — and **every such judgement
is labelled *model-adjudicated* where it is cited, never as a human reference** (`OWNER-D3`). We
also publish how far our judge actually agrees with a benchmark's own human labels: on the
official HarmBench judge, our run agrees with the suite's published human column on
**227/300 = 75.67 %**, against the suite's own **78.33 %**. That number is unflattering and it is in
the record.

> **PROPOSED — name for the method: *Bar-First Evaluation*.** The claim it makes is narrow and
> checkable: *the ship/no-ship threshold for every public benchmark is published before the run,
> the benchmark is public and third-party, and the programme's own failures — contamination, judge
> disagreement — are published with the results.* A name is a proposal, not a finding; the finding
> is the record.

---

## 4. The path, plainly

**1 · Fix the gate measurement.** The corpus **Data Gate is BLOCKED — NOT PASS**. All three
registered limits — unsafe < 1 %, off-topic < 2 %, shallow < 5 % — are **NOT MEASURED**, because the
§6 confirmation draw has not been run; and the non-statistical criterion **cross-row leakage
FAILED**. The gate is being repaired before it is re-measured, and the re-measurement is to be
preregistered with a named reviewer pair and a decision rule.

**2 · Certify the corpus.** Run the confirmation draw; re-issue the gate. It must read **PASS**
with all three limits measured and the leakage criterion satisfied. No training is valid before it.

**3 · Train the new arm from base.** LoRA r = 32 on `Qwen3-4B-Instruct-2507`, **from the base
checkpoint, no warm start**, with the refusal-stream weight as the single controlled variable and
the epoch **never truncated** — an earlier run in this programme died at two tenths of an epoch
under a time cap, and that failure mode is excluded on the record. A 30-step throughput pilot has
already measured the machine at **2.506 samples/s**; the pilot's receipt is published, its adapter
is not, and it is not a release candidate.

**4 · Evaluate it on every bar.** Same frozen surface, same session, same instruments. B1–B4
decide; B5–B8 are reported with their parse rates.

**5 · Rule it.** Ship or do not ship — recorded either way, with the numbers.

Then, and only then, the six release artefacts: merged bf16 weights → GGUF bf16 → Q4_K_M →
`generation_config.json` → model card → hash-frozen bundle. Until a **serving party** is named, a
release can be shipped as an artefact bundle but cannot honestly claim to be served.

---

## 5. The state of the record — the honest version

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

### 5.1 One correction the record itself makes

The false-refusal ceiling is **≤ 5.13 %**, not ≤ 5.27 %. The 5.27 % rendering was built on the
pre-repair 4.27 % base figure; the base was re-measured at **4.13 %** (31/750) and the bar is
*base + 1.0 pp*. The change was recorded as a **correction, not a decision**
(`docs/PRODUCT-CONTRACT.md` §9; `PLAN-LEDGER.md` `E-1`). The operative form — *no worse than the
untrained base* — is unchanged, and v3 fails either way (29.07 %, 5.67× the 5.13 % ceiling).

### 5.2 The repository

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

---

## 6. OWNER DECISIONS — required, in priority order

**None of these is a technical question, and none of them was taken here.** Each one below is
written as a decision with its options and their consequences stated separately, so the choice is
never buried in prose. The three the owner named — **D1** the ship ruling, **D2** the serving
party, **D3** the public flip — are first. The **Recommendation on the record** line at the end of
each block is a recommendation, and it was **not** acted on; the decision itself remains the
owner's.

---

### D1 · The release ruling (H-3) — ship, or do not ship

**The decision.** When the new arm's row exists, whether the programme releases it, and on what
claim. The ruling is written either way, with the numbers.

**What the record has already fixed, and is therefore not yours to re-open:**

- the **decision rule** (`docs/BAR-SHEET.md` §0, `PLAN-LEDGER.md` `H-3`): **ship** if B1–B4 hold and
  B5–B7 are published with their parse rates and baselines; **do not ship** if B3 fails; if **B1
  fails but B3 passes**, the release is *the evidence stack plus a smaller claim*, not a benchmark
  claim;
- the **decision instruments** (B1 CTI-RCM, B2 CTI-VSP, B3 MITRE-FRR, B3b refusal integrity,
  B4 HarmBench) and the **report-only** instruments (B5–B8, which are never a pass or a fail);
- the **B4 bar was fixed before H-2** (`ASTRA-D27`) and may not be restated after the new arm's
  harmful-completion count is visible;
- **a bar met is not a ship decision** — it is one condition of one.

| option | what it means | what it commits you to |
|---|---|---|
| **A — ship the full claim** | B1–B4 all hold; release the model, the model card, the dataset card, and the benchmark claim | Six artefacts built, a serving party named (D2), and a public claim the numbers carry |
| **B — ship the evidence stack with a smaller claim** | B1 fails but B3 holds; release as a documented method-and-evidence package, not a benchmark-beaten model | The same artefacts minus a comparative claim; the evaluation programme becomes the product |
| **C — do not ship** | B3 fails, or the Data Gate never clears, or the corpus receipt cannot be completed | The record stays as it is — an evaluation programme with a NO-SHIP arm of record, and a named next step |

**Recommendation on the record.** *Not actionable today, and deliberately not taken.* H-3 has no
arm to rule on: H-2 has not run, the Data Gate is BLOCKED, and the corpus receipt the bundle's
manifest needs is itself blocked. **The useful owner decision today is not a ship/no-ship verdict
on v3 — it is whether the rule above stands as written when the new arm's numbers arrive.**

---

### D2 · The serving party — who serves the model, and on what terms

**The decision.** Name the party that operates the endpoint, and the licence and availability
terms the release ships under. `docs/RELEASE-SHAPE.md` §2 lists it as **R-4** and states plainly
that it is *the owner's call, not the worker's*.

**What the record has already measured** (so the decision is made on facts, not on preference):

- the v1-era peer host that was to produce the f16 GGUF is **unreachable** — SSH returns
  `Host key verification failed` and there is no `known_hosts` entry;
- the `llama-quantize` path the serve script hard-codes **does not exist** on this host; the
  target is **buildable here** but is **NOT LAUNCHED** (R-1);
- `~/.cyberguard-env` **does not exist**, and `gguf/` holds only a README — **no GGUF exists**;
- **four of the six artefacts do not depend on this decision at all**: merged weights, f16 GGUF,
  `generation_config.json`, and the model card's measurement sections.

| option | what it means | what it blocks / unblocks |
|---|---|---|
| **A — this workstation** | the endpoint runs where the artefacts are built | unblocks "ship **and serve**" and DSH registration; makes the model card's *how to run it* a verified instruction rather than a claim |
| **B — the peer host** | the endpoint runs on the original v1-era host | **currently blocked** — that host is unreachable; the chain has to be repaired first |
| **C — a hosted service** | the endpoint runs as a managed service | brings terms, cost and an external dependency; the licence and availability terms ship with it |
| **D — the customer's own hardware** | the release ships as artefacts only, and the customer serves it | H-3 can only ever be "ship the artefact bundle"; no served claim, ever |

**Recommendation on the record.** *A* — this workstation — is the option the measurements support,
because the merge and the conversion both live here and option B is currently unreachable. But
this is the owner's call and it was **not taken**: building the quantiser (R-1) still needs its own
ruling, and no build was launched.

---

### D3 · The public flip — does this repository ever go public

**The decision.** Whether the evaluation programme becomes a public repository, and if so, in what
redaction and under what licence.

**What the record has already fixed:**

- the repository is **private** today, by the owner's standing order;
- **licensing is explicitly deferred by the owner**, and this packet does not analyse it;
- the **boundary already answers the technical half**: everything that identifies the machines or
  the data stays out — enforced by `verify_repo.py`, not by good intentions;
- **two things would still have to be handled before a public flip**, and neither is a licence
  question:
  1. **the git history** contains the pre-rebuild tree, including the 500-row held-out set
     (`v2/holdout500.jsonl`) and the internal probe sets — see **D4**;
  2. **the published comparator's numbers are ours, not theirs.** The table in §2 prints
     CyberSecQwen-4B's first-party re-measurement; that is our evaluation of their model, and a
     public reader should be told that clearly, which is what the P/F legend does.

| option | what it means | what it costs |
|---|---|---|
| **A — stay private** | the programme stays an internal record | no external audience; the differentiator is unproven in public |
| **B — public, as it stands** | the tree becomes public as it is | the git history would carry the held-out set and the probe sets with it — **not available without D4** |
| **C — public, history rewritten** | the branch is rewritten, then the tree is published | loses the provenance of every commit the repository has carried, **including the v3 build record the programme's own argument leans on** |
| **D — public, redacted** | the tree is published with the residual items removed and the removals published too | the most work; and the removals must be *stated*, or the public repo would overclaim |

**Recommendation on the record.** *Not taken.* The owner deferred licensing and has not ruled on
visibility; the packet's technical input is that **D4 must be settled before any public flip**,
and that the P/F labelling is already the redaction mechanism for the numbers.

---

### D4 · The git-history exposure — rewrite the branch, or keep the provenance

**The decision.** The repository's history still contains the pre-rebuild tree, including
`v2/holdout500.jsonl` (the 500-row held-out set, 1.85 MB) and the `v2/data/probe-set-*.jsonl`
internal probe sets. They were tracked and pushed on 2026-10-05, before this rebuild, and they are
absent from the current tree.

**What the record has already fixed:**

- the repository is **private**, so the exposure is limited to the owner and anyone the owner grants
  access to;
- the held-out set is **derived from a public dataset**;
- removing it from history means **rewriting the branch**, which destroys the provenance of every
  commit the repository has ever carried — **including the v3 build record the programme's own
  argument depends on**.

| option | what it means | what it costs |
|---|---|---|
| **A — keep the history** | the repository stays private and the past stays intact | a private repository whose past contains data the present boundary forbids; the exposure ends only if the repo is ever made public |
| **B — rewrite the history** | the branch is rewritten to purge the two file groups | the provenance of the v3 build is destroyed — which is the evidence the programme's contamination story rests on |
| **C — archive and reset** | the history is moved to a private archive and the public-facing branch is rebuilt | preserves provenance off the published branch, at the cost of splitting the record in two |

**Recommendation on the record.** *A — keep the history.* The repository is private, the data is
derived from a public dataset, and the provenance of the v3 build is itself evidence the
programme's argument leans on. **This was not acted on**; the decision was not taken.

---

### D5 · Does the H-1 run proceed before the §6 confirmation draw completes

**The decision.** `OWNER-D3` and `ASTRA-D25` say the run is GO; `ASTRA-D30` says the gate
measurement is repaired first and the re-measurement preregistered. These can be read as
**sequential** or as **parallel**. Only the owner can settle the reading, and it matters: a run
against an unqualified corpus is exactly the failure the Data Gate exists to prevent.

| option | what it means | what it costs |
|---|---|---|
| **A — sequential** | the confirmation draw completes, the gate reads PASS, then the arm trains | the slowest route, and the only one where the corpus receipt in the bundle manifest can be completed |
| **B — parallel** | the arm trains while the draw runs | faster; but if the draw fails, the arm is trained on an unqualified corpus and the measurement is compromised before a single new row is seen |

**Recommendation on the record.** *A — sequential.* The Data Gate's own receipt requires the three
limits to be MEASURED and the leakage criterion satisfied, and the bundle manifest cannot be
completed before the corpus receipt clears. **Not taken.**

---

### D6 · The local quantiser build

**The decision.** R-1 in `docs/RELEASE-SHAPE.md` §3: build `llama-quantize` from the local
`llama.cpp` tree. It is a build of an existing source tree, not a port or a new implementation.

**Why it was not simply done.** It installs a new binary on a machine whose GPUs are running
long-lived measurement sweeps, and the standing worker rules require a ruling before installation
or build work is launched. **Recording the remedy with its exact command is the worker's job;
pressing it is not.** It is **NOT LAUNCHED**.

**Recommendation on the record.** *Launch R-1 and R-2 together, once the owner rules.* Not taken.

---

### D7 · Licensing

**The decision.** Deferred by the owner. **No licence file is in the repository, and no licence
analysis appears in this packet or in `EVALUATION.md`.** It becomes a live decision only if D3
takes the public flip.

---

## 7. Exclusions, and why each one is excluded

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

---

## 8. Readiness

| asset | ready? | notes |
|---|---|---|
| **The evaluation programme repository** | ✅ **ready** | private, pushed, boundary-checked, self-verifying (`verify_repo.py` exits 0) |
| **The front page** (`README.md`) | ✅ ready | product identity, headline, the apples-to-apples table, the differentiator, the path |
| **The boundary charter** (`EVALUATION.md`) | ✅ ready | options considered, the boundary, and the seven-step path to a shippable model repository |
| **The inventory** (`INVENTORY.md`) | ✅ ready | generated from the build manifest; 125 imported files with source path and source sha256 |
| **The demo video** | ✅ ready | see §10 |
| **A shippable model** | ❌ **not ready** | v3 is a NO-SHIP; no release arm exists |
| **A qualified corpus** | ❌ not ready | the Data Gate is BLOCKED; the §6 confirmation draw has not been run |
| **The release artefacts** | ❌ not ready | none of the six is built |
| **A serving path** | ❌ not ready | the serving party is unresolved; the local quantiser is buildable but not launched |
| **A public launch** | ❌ out of scope | the repository is private and licensing is deferred by the owner |

---

## 9. What is in flight, and what it is waiting on

| work | state | waiting on |
|---|---|---|
| **The clean arm (H-1)** | OWNER GO (`ASTRA-D25`, `ASTRA-D26`); the arm, mixture and base are fixed; the throughput is measured | the run itself — and the §6 confirmation draw, which is the measurement the Data Gate repair preregisters (**D5**) |
| **The Data Gate repair** | `ASTRA-D30`: fix the measurement first; the re-measurement is to be preregistered with a named reviewer pair and a decision rule | a reviewer pair that did not see the development rows |
| **The evaluation of the new arm (H-2)** | open | the arm |
| **The release ruling (H-3)** | open | H-2, and the owner's ruling (**D1**) |

---

## 10. Launch assets

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

## 11. How to verify this packet

| claim | the check |
|---|---|
| the repository is private | `gh repo view sandeep-alluru/cyberguard --json visibility,isPrivate` |
| the boundary holds | `python3 verify_repo.py` — exits 0 only when identifiers, credentials and off-allow-list row files are all absent |
| what is in the repository and where it came from | `INVENTORY.md` |
| the boundary, and why it is where it is | `EVALUATION.md` |
| every number in §2 | `docs/BAR-SHEET.md` §2 and §5 for the first-party figures and their receipts; the *Sources* section of `README.md` for the published ones |
| the release rule behind D1 | `docs/BAR-SHEET.md` §0; `docs/PLAN-LEDGER.md` `H-3` |
| the serving-party facts behind D2 | `docs/RELEASE-SHAPE.md` §2–§3 |
| the v3 verdict | `docs/V3-EVAL-FINAL-RESULTS.md` |
| the corpus gate | `qualification/data/v4/DATA-GATE.json` |
| the held-out leak | `docs/ESCALATION-F8-HELDOUT-CONTAMINATION.md` |
| the release shape and the six artefacts | `docs/RELEASE-SHAPE.md` |
| the current rulings | `docs/ASTRA-DECISIONS.jsonl`, `docs/OWNER-DECISIONS.md`, `docs/V3-OWNER-DECISIONS.md` |
| the demo video's content and length | `ffprobe -show_entries format=duration cyberguard-evaluation-demo.mp4` |

---

*Internal. Prepared from the programme record; the programme tree was read, not written.*
