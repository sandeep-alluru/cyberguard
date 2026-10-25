# The release shape — decision record

**Raised:** 2026-10-23 · **Ledger item:** E-4 (P2-5, from `EVALUATION.md` step 2-5) · **Status:** the **shape is decided**; the **serving party is UNRESOLVED**
**Checked by:** `eval-2026-10-23/e4_release_shape_check.py` → `eval-2026-10-23/e4-release-shape-check.json`

> **This record decides what it is allowed to decide and says plainly what it did not decide.** The
> shape of the release is a technical decision, and it is decided here. **Who operates the
> endpoint is an owner/operator decision, and it is recorded as unresolved** — with exactly what
> that blocks, because a decision that names a blocker is useful and a decision that hides one is
> not.

---

## 1. The shape — DECIDED

The release artefact set is six things. The order is the pipeline order.

| # | artefact | what it is | how it is produced | the number that matters |
|---|---|---|---|---|
| 1 | **merged weights** | the LoRA merged into the base, bf16, `safe_serialization=True` | `PeftModel.from_pretrained(base, adapter).merge_and_unload()` then `save_pretrained` | ~7.6 GB for a 4B at bf16 |
| 2 | **GGUF bf16** | the merged weights as GGUF, unquantised | `convert_hf_to_gguf.py --outtype bf16` from `llama.cpp` | ~7.5 GB |
| 3 | **Q4_K_M GGUF** | the quantised model that is actually served | `llama-quantize <f16> <out> Q4_K_M` | ~2.4 GB (the v1 smoke run measured 2,375.91 MiB, 165 s) |
| 4 | **`generation_config.json`** | the serving parameters, named | written by hand from the **frozen surface** | **512 new tokens** — not the framework default of ~20 (B15) |
| 5 | **model card** | the public numbers and their limits | written from `docs/BAR-SHEET.md` and its §4 | every bar, its n, its baseline, and what the sheet does not measure |
| 6 | **hash-frozen bundle** | a manifest that pins every artefact | sha256 of each artefact + the base model's config sha256 + the adapter's sha256 + the corpus receipt + the `llama.cpp` commit | the bundle is reproducible or it is not shipped |

**Why these six and not fewer.** The v1-era chain is **validated end to end** — a throwaway
adapter was merged, converted, quantised and served before the real adapter existed, producing a
coherent defensive answer (`README.md`, "Serving path — validated end to end"). That validation
was real, and it is the reason the shape is not an open question: the pipeline works, and what is
missing is the **artefacts**, not the **design**. The two additions since v1 are `generation_config.json`
(B15 — a downloader gets the framework's ~20-token default, not 512, and every measurement in this
programme was taken at 512) and the **hash-frozen bundle** (the record's own blocking fact: *"a
future run cannot bind to repository HEAD alone; it needs a manifest of every executed file and
data/model hash"* — `SESSION-ARCHIVE/board/EVALUATION.md`).

**The merge and the conversion happen on THIS host.** The v1-era split put the merge on
`<host-a>` and the quantise + serve on a workstation. **That split is forced by what is built
where, and on this host the facts have changed:**

| input | present on this host | where |
|---|---|---|
| base model | **yes** | `<model-cache>/cyberguard-eval/Qwen3-4B-Instruct-2507` |
| adapter | **yes** | `<programme-tree>/research-tmp/harvest-v3/adapters` |
| python `gguf` module | **yes** | `<venv>/lib/python3.11/site-packages/gguf` |
| `llama.cpp` source | **yes** | `<llama.cpp-tree>`, commit `94256114c229674ef96e76eb2dea596e65b43818`, Release, `GGML_CUDA=ON` |
| `llama-server` binary | **yes** | `<llama.cpp-tree>/build/bin/` |
| `llama-quantize` binary | **NO** | not built — but the target **exists and is buildable here** (§3) |

Both halves of the merge live on this host, so the f16 GGUF can be produced here without the
handoff. **The quantise step can also be produced here** — the target exists — but building it is
a new capability on this host and the standing rules require a ruling before that is launched
(§3).

---

## 2. The serving party — UNRESOLVED, and here is what it blocks

**No serving party is named, because none can be named on the facts.** The two candidate hosts
are both unavailable to this one, for reasons that are measured rather than assumed:

| what the v1-era chain needs | state on this host, 2026-10-23 |
|---|---|
| the f16 GGUF from `<peer-host>` over scp | **that host is not reachable** — SSH returns `Host key verification failed` and `~/.ssh/known_hosts` has no entry for it |
| `llama-quantize` at `<storage-mount>/gpu-work/build/llama.cpp/build/bin/` (the path `serve-cyberguard-local.sh` hard-codes) | **that path does not exist** |
| `~/.cyberguard-env` (which `cyberguard-merge-gguf.sh` sources for `$CYBERGUARD_ROOT` and `$CYBERGUARD_VENV`) | **does not exist** — the script fails on its first line, before any work |
| a GGUF to serve | **`gguf/` holds only a README** — *"No GGUF exists: v1 was never merged/converted because it is not served"* |

**What the unresolved serving party blocks, precisely:**

1. **The release decision (ledger **H-3**) cannot be "ship and serve".** It can only be **"ship
   the artefact bundle"**. No arm can be served on this host, so no bar can be evaluated against a
   served model, and the model card's *how to run it* section cannot be written as a **verified**
   instruction — it would be an untested claim in a document whose whole purpose is to publish
   only what was measured.
2. **The Q4_K_M artefact cannot be produced by the scripted chain.** Both halves of the v1-era
   split are broken here: that host that was to produce the f16 GGUF is unreachable, and the
   local quantiser is unbuilt at the path the serve script hard-codes.
3. **DSH registration cannot happen.** The record is explicit: *"The model is not registered in
   DSH yet — registering happens once the real GGUF exists, because pointing the harness at a
   dead endpoint would be untidy."* Registering now would create exactly the dead endpoint the
   record warns against, and the harness would point at it.
4. **What is NOT blocked, and can proceed on this host without resolving the serving party:** the
   merged weights, the f16 GGUF, `generation_config.json`, the model card's measurement sections,
   and the hash manifest. **Four of the six artefacts do not depend on the serving party at all.**

**The dependency that is genuinely open, and is not this record's to close:** the hash-frozen
bundle's manifest must include the **corpus receipt**, and that receipt is ledger **D-7** — which
is **BLOCKED on human reviewers** that do not exist for this programme (D-3, D-6, A-6). **So the
bundle's manifest cannot be completed before the human adjudication clears, no matter what
happens with the serving party.**

---

## 3. The identified remedy, and its authorisation status — NOT LAUNCHED

| # | remedy | status | who must authorise |
|---|---|---|---|
| R-1 | **Build the quantiser on this host:** `cmake --build build --target llama-quantize` in `<llama.cpp-tree>`. The target is listed by the local build system, so this is a build of an existing source tree, not a port or a new implementation. | **NOT LAUNCHED** | **A ruling.** This is a build action on this host that creates a new capability, and the standing worker rules require a ruling before installation or build work is launched. |
| R-2 | **Point the serving script at the local binary** (`<llama.cpp-tree>/build/bin`) instead of the hard-coded `<storage-mount>/...` path, or copy the binary there. | **NOT LAUNCHED** | with R-1 |
| R-3 | **Write `~/.cyberguard-env`** with the real `$CYBERGUARD_ROOT` and `$CYBERGUARD_VENV` for this host, so `cyberguard-merge-gguf.sh` runs; or run the merge steps directly against the paths in §1. | **NOT LAUNCHED** | with R-1 |
| R-4 | **Name the serving party** — this workstation, that host, a hosted service, or the customer's own hardware — and the licence and availability terms it ships under. | **OPEN — the owner's call** | **the owner.** Not a worker decision. |
| R-5 | **Register in DSH** once a real GGUF exists and an endpoint answers. | blocked on R-1/R-4 | after R-1 and R-4 |

**Why the worker did not simply do R-1.** It is the obvious next move and it is one command. It
is also a build that installs a new binary on a machine whose GPU is currently running two
long-lived measurement sweeps, and the standing rules are explicit that the worker does not
launch installation or build work without a ruling. **Recording the remedy with its exact command
is the worker's job; pressing it is not.**

---

## 4. What this record does and does not settle

**Settles:** the artefact set, the pipeline order, the parameters, the measurement sources for the
model card, the manifest contents, and where the merge and the conversion happen.

**Does not settle, and says so:** who operates the endpoint (R-4), whether the quantiser is built
on this host (R-1, a ruling), and whether the bundle's manifest can be completed at all (D-7, human
reviewers).

**Does not claim.** This record does not claim the release ships, does not claim the endpoint
works, and does not claim any bar is met. The bar sheet's standing is the bar sheet's, and the
ship/no-ship decision is ledger **H-3**'s.
