# The release shape

**Raised:** 2026-10-23 · **Programme item:** E-4 (P2-5, from the evaluation programme's step 2-5) · **Status:** the **shape is set**; the **serving party is named as part of the release**
**Checked by:** `eval-2026-10-23/e4_release_shape_check.py` → `eval-2026-10-23/e4-release-shape-check.json`

> **This record sets the shape of the release.** The artefact set, the pipeline order and the
> parameters are decided here. **Who operates the endpoint is a deployment decision, and it is taken
> as a step of the release** — named in the pipeline below, with what it gates stated exactly, so the
> release reads as one ordered chain rather than a set of open questions.

---

## 1. The shape — six artefacts, in pipeline order

The release artefact set is six things. The order is the pipeline order.

| # | artefact | what it is | how it is produced | the number that matters |
|---|---|---|---|---|
| 1 | **merged weights** | the LoRA merged into the base, bf16, `safe_serialization=True` | `PeftModel.from_pretrained(base, adapter).merge_and_unload()` then `save_pretrained` | ~7.6 GB for a 4B at bf16 |
| 2 | **GGUF bf16** | the merged weights as GGUF, unquantised | `convert_hf_to_gguf.py --outtype bf16` from `llama.cpp` | ~7.5 GB |
| 3 | **Q4_K_M GGUF** | the quantised model that is actually served | `llama-quantize <f16> <out> Q4_K_M` | ~2.4 GB (the v1 smoke run measured 2,375.91 MiB, 165 s) |
| 4 | **`generation_config.json`** | the serving parameters, named | written by hand from the **frozen surface** | **512 new tokens** — not the framework default of ~20 (B15) |
| 5 | **model card** | the public numbers and their limits | written from `docs/BAR-SHEET.md` and its §4 | every bar, its n, its baseline, and what the sheet does not measure |
| 6 | **hash-frozen bundle** | a manifest that pins every artefact | sha256 of each artefact + the base model's config sha256 + the adapter's sha256 + the corpus receipt + the `llama.cpp` commit | the bundle is reproducible — the release depends on it |

**Why these six and not fewer.** The v1-era chain is **validated end to end** — a throwaway
adapter was merged, converted, quantised and served before the real adapter existed, producing a
coherent defensive answer (`README.md`, "Serving path — validated end to end"). That validation
was real, and it is the reason the shape is not an open question: the pipeline works, and what comes
next is the **artefacts**, not the **design**. The two additions since v1 are `generation_config.json`
(B15 — a downloader gets the framework's ~20-token default, not 512, and every measurement in this
programme was taken at 512) and the **hash-frozen bundle** (the fact that decides it: *"a future run
cannot bind to repository HEAD alone; it needs a manifest of every executed file and data/model
hash"*).

**The merge and the conversion happen on THIS host.** The v1-era split put the merge on
`<host-a>` and the quantise + serve on a workstation. **That split is forced by what is built
where, and on this host the facts have changed:**

| input | present on this host | where |
|---|---|---|
| base model | **yes** | `<model-cache>/cyberguard-eval/Qwen3-4B-Instruct-2507` |
| adapter | **yes** | `research-tmp/harvest-v3/adapters` |
| python `gguf` module | **yes** | `<venv>/lib/python3.11/site-packages/gguf` |
| `llama.cpp` source | **yes** | `<llama.cpp-tree>`, commit `94256114c229674ef96e76eb2dea596e65b43818`, Release, `GGML_CUDA=ON` |
| `llama-server` binary | **yes** | `<llama.cpp-tree>/build/bin/` |
| `llama-quantize` binary | **NO** | not built — but the target **exists and is buildable here** (§3) |

Both halves of the merge live on this host, so the f16 GGUF can be produced here without the
handoff. **The quantise step is produced here too** — the target exists — and the build that
produces it is one command away (§3).

---

## 2. The serving party — a step of the release

**The serving party is named as part of the release.** The two candidate hosts
are both unavailable to this one, for reasons that are measured rather than assumed:

| what the v1-era chain needs | state on this host, 2026-10-23 |
|---|---|
| the f16 GGUF from `<peer-host>` over scp | **that host is not reachable** — SSH returns `Host key verification failed` and `~/.ssh/known_hosts` has no entry for it |
| the `llama-quantize` binary at the path `serve-cyberguard-local.sh` hard-codes | **that path does not exist** |
| `~/.cyberguard-env` (which `cyberguard-merge-gguf.sh` sources for `$CYBERGUARD_ROOT` and `$CYBERGUARD_VENV`) | **does not exist** — the script fails on its first line, before any work |
| a GGUF to serve | **`gguf/` holds only a README** — *"No GGUF exists: v1 was never merged/converted because it is not served"* |

**What the serving party is needed for:**

1. **The release milestone H-3 closes on the artefact bundle.** The served model follows the serving
   party: no arm can be served on this host, so no bar can be evaluated against a
   served model, and the model card's *how to run it* section becomes a **verified**
   instruction once an endpoint answers — a document whose whole purpose is to publish
   only what was measured carries no untested instruction.
2. **The Q4_K_M artefact follows the quantiser build.** Both halves of the v1-era
   split are ready here: that host that was to produce the f16 GGUF is unreachable, and the
   local quantiser is unbuilt at the path the serve script hard-codes.
3. **DSH registration is the step after the endpoint answers.** The record is explicit: *"The model is not registered in
   DSH yet — registering happens once the real GGUF exists, because pointing the harness at a
   dead endpoint would be untidy."* Registering before a real GGUF exists would create exactly the dead endpoint the
   record warns against, and the harness would point at it.
4. **What the serving party does not gate:** the
   merged weights, the f16 GGUF, `generation_config.json`, the model card's measurement sections,
   and the hash manifest. **Four of the six artefacts do not depend on the serving party at all.**

**The dependency that runs in its own track, and is not this record's to close:** the hash-frozen
bundle's manifest must include the **corpus receipt**, and that receipt is programme item **D-7** — which
closes on the human assessment (D-3, D-6, A-6), itself outside this record's scope. **So the
bundle's manifest closes when the human adjudication clears, whatever happens with the serving party.**

---

## 3. The steps from the artefacts to a served endpoint

| # | step | state | what it depends on |
|---|---|---|---|
| R-1 | **Build the quantiser on this host:** `cmake --build build --target llama-quantize` in `<llama.cpp-tree>`. The target is listed by the local build system, so this is a build of an existing source tree, not a port or a new implementation. | **the next build** | **A decision of its own.** This is a build action on this host that creates a new capability, and the standing rules require that decision before installation or build work starts. |
| R-2 | **Point the serving script at the local binary** (`<llama.cpp-tree>/build/bin`) instead of the hard-coded workstation path, or copy the binary there. | **queued** | with R-1 |
| R-3 | **Write `~/.cyberguard-env`** with the real `$CYBERGUARD_ROOT` and `$CYBERGUARD_VENV` for this host, so `cyberguard-merge-gguf.sh` runs; or run the merge steps directly against the paths in §1. | **queued** | with R-1 |
| R-4 | **Name the serving party** — this workstation, that host, a hosted service, or the customer's own hardware — and the licence and availability terms it ships under. | **a step of the release** | **the deployment.** Not a build decision. |
| R-5 | **Register in DSH** once a real GGUF exists and an endpoint answers. | **after R-1 and R-4** | after R-1 and R-4 |

**Why R-1 is a decision of its own.** It is the obvious next move and it is one command. It
is also a build that installs a new binary on a machine whose GPU is currently running two
long-lived measurement sweeps, and the standing rules are explicit that installation or build
work does not start without a decision of its own. **The step is recorded with its exact
command; running it is the next move.**

---

## 4. What this record settles, and what comes next

**Settles:** the artefact set, the pipeline order, the parameters, the measurement sources for the
model card, the manifest contents, and where the merge and the conversion happen.

**Next, in the pipeline:** who operates the endpoint (R-4 — named as a step of the release), whether
the quantiser is built on this host (R-1, a decision of its own), and the bundle manifest's corpus
receipt (D-7, human assessment).

**Scope.** This record describes the release's shape: the artefact set, the pipeline order and the
serving-party step. The bar sheet's standing is the bar sheet's, and the release decision is
programme milestone **H-3**'s.
