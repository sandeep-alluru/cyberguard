# ARTIFACT-MAP — where everything actually lives

Written because the canonical directories were empty while the real artifacts sat on a remote host,
which makes the repo look like nothing was produced. That ambiguity is now resolved here.

| canonical dir | state | where the content really is |
|---|---|---|
| `receipts/` | **populated** | copies of the harvested training receipts (`cyberguard-lora-v1.json`, corpus-safety audit) |
| `evals/` | **populated** | copies of the harvested eval + merge-equivalence receipts |
| `data/` | intentionally empty | the corpus (195 MB) lives on `spark-40ee:~/cyberguard/data`; admitted-v2 corpora will land here |
| `training/` | intentionally empty | training ran on `spark-40ee` (launcher + logs there) |
| `serving/` | intentionally empty | v1 is deliberately not served (`docs/SPEC-V2.md` §10) |
| `gguf/` | intentionally empty | no GGUF exists — v1 was never merged/converted because it is not served |
| `research-tmp/harvest-v1/` | populated | checksum-verified pull of the v1 adapter + receipts + evals + logs |
| `research-tmp/harvest-cap-v1/` | populated | checksum-verified pull of the capability-box receipts |
| `research-tmp/reviews/` | populated | the five Codex-Astra review transcripts + prompts |
| `research-tmp/trace/` | populated | toolcall-trace analysis receipts |

**Durable archive (outside any workspace):** `/mnt/purple4tb/AgentHub-archive/cyberguard/`
— a copy of both harvests, the docs set, the code set, and the independent remote re-hash record
(`remote-rehash-20260927.txt`). Remote `~/cyberguard` on `spark-40ee` is therefore preserved off-host.

**Remote re-hash of record (2026-09-27):** adapter `adapter_model.safetensors` =
`bead9235d5349965e320b68d7ef0368e7a9e53f3c5fc2d15bac857dd04c82976`, and all 15 comparable remote
artifacts matched the harvest manifest with **0 mismatches** (`research-tmp/hash-remote-now.txt`).

**Git:** this repo carries documents, code, and text receipts. Binaries (adapter, PDFs, session
transcripts) are ignored by `.gitignore` and preserved in the archive instead.
