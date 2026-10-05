# OWNER DECISION — DSH harness repair (CyberGuard scope)

Prepared by Astra (CTO) at the owner's request for **a solution he can approve**.
Nothing in this document has been executed. D9 freeze remains active.

---

codex
**1. THE PROPOSAL IN ONE PARAGRAPH**

Approve a CyberGuard-only repair that removes the worker’s unrestricted execution tools, exposes the existing Codex review adapter, and makes that adapter refuse requests unless authorization, evidence, privacy and budget checks pass. Reuse the D18 scripts and installed DSH adapter; test an isolated copy before switching one CyberGuard session. Leave the home patch untouched, keep project workloads frozen, and retain JEV as a mandatory factual checker with zero acceptance authority. This approval covers implementation, offline tests and a restricted canary with external sends disabled. The accepted limitation is that another process or person with the workstation account can still bypass these project restrictions.

**2. WHAT GETS BUILT — EXACT ARTIFACTS**

Relative paths are under `/home/clawer-samurai-1/AgentHub/cyberguard`. The worker implements; Astra accepts; the human operator installs. Every row below is a deliverable, including revisions of existing artifacts.

| Path | Existing/new; function and enforcement | Responsible party |
|---|---|---|
| docs/dsh/OWNER-DECISION.md; docs/ASTRA-DECISIONS.jsonl | New signed document; existing register receives its exact repair authorization. D9 remains active. | Owner signs; Astra specifies; operator records. |
| tools/astra_gate.py | Existing; repair required. Exact argument-vector authorization and dispatch in one protected operation; default deny. A decision ID alone grants nothing. | Worker. |
| tools/review_packet.py | Existing; repair required. One shared implementation of D18 evidence, exposure, budget and coverage checks, with persistent per-review accounting. | Worker. |
| tools/astra_review.sh; tools/review_cycle.sh; v2/dispatch_review.sh; v2/checkpoint_review.sh | Existing; wiring required. Remove direct Codex launches; route through the registered adapter. Outside the governed DSH context, refuse. | Worker. |
| docs/dsh/cyberguard.agent.cordis.yml | New restricted composition derived from standard-agents. Within its delegation group, retain tool-subagent-codex and ADD tool-subagent-claude-code, tool-subagent-grok and tool-subagent-kimi as governed **advisory reviewer** tools. Remove generic spawn/fork, subagent controls, workflows and other execution routes. Parent capability = local read/search + these four governed review tools; no unrestricted shell or mutation. Children receive packet-only context and NO tools. | Worker prepares; operator installs. |
| docs/dsh/codex-boundary.patch | New patch to the existing @deepseek-ai/dsh-subagent-codex/lib/index.js and affected serialization dependency. Record exact target paths/preimage hashes. Call shared checks before dispatch and enforce D18 before every serialized model request; no replacement adapter. | Worker prepares; Astra accepts; operator installs. |
| docs/dsh/check_enforcement.py | New integration-test entry point with the stage modes in §4. Exercises the installed loader, registry, dispatcher and serializer. Tests grant no authority. | Worker. |
| tools/audit_reviews.py; docs/review-accounting.jsonl | Existing; repair required. Reconcile actual project/session/request identities, reject unmatched records, deduplicate usage updates. Unknown usage is null plus UNMEASURED. Dispatcher consults reconciliation before each subsequent dispatch. | Worker. |
| docs/dsh/acceptance/ | New evidence directory: baseline bytes/hashes, test inputs, pre/post/control results, effective tool catalogs, request captures, rollback results, time records and acceptance verdict. | Worker records; operator preserves. |
| recovery/human/blocked-item-reviews.jsonl | D16-prescribed deliverable, populated only under applicable authorization. Human review and required-assessment completion remain separate states. | Cybersecurity reviewer; third adjudicator resolves disputes. |

Verified by inspection: the D18 scripts and all four adapter rows exist in `/home/clawer-samurai-1/.dsh/.agent-presets/standard-agents/agent.cordis.yml`. The three legacy launchers still contain direct Codex invocations. Those files settle these claims; stage 1 preserves their exact bytes and SHA-256 hashes. Claude, Grok and Kimi are included as governed **advisory reviewers** alongside Codex. Registration grants neither execution authority nor permission to substitute reviewers. Astra names the exact adapter/model and assigned claims in each authorized review; the worker cannot choose replacements or fallback routes. No adapter replaces mandatory JEV participation, D7/D11 reviewers or human acceptance.

Reuse `/home/clawer-samurai-1/.codex/skills/jev-decisions/references/jev_ask.py`. Its [skill instructions](/home/clawer-samurai-1/.codex/skills/jev-decisions/SKILL.md) inform §5; D14–D16 control wherever stricter.

**3. WHAT IT ENFORCES AND HOW**

The following are required acceptance conditions, not claims that the repair already works.

| Bypass | Exact control and acceptance test |
|---|---|
| Worker launches through shell, Python, copied binaries or alternate delegation | Effective registry permits only read/search and governed Codex review. Invoke every forbidden tool through the actual dispatch API, including remembered names and inherited/global tools: every attempt refused; zero child launches. |
| Approved child executes commands, reads the repository or delegates again | Fresh packet-only context; no execution, browsing, connectors, skills or delegation capabilities. Attempt each through the child runtime: refused. Filesystem read-only mode alone is insufficient. |
| Worker changes rules, code or accounting | No worker/child mutation capability. Attempt writes through every exposed capability, including symlinks: refused. Operator controls installation; implementation occurs in a separate operator-managed checkout. |
| Existing ruling ID launders an unauthorized command | Dispatcher matches exact action, argument vector, approved code hashes, packet hash and current D9 state. Unknown IDs, stale hashes, extra arguments, shell chains and D9 used as permission all refuse before execution. No shell-string dispatch. |
| Hidden context or retries exceed D18 | Count actual serialized input, including instructions/tool schemas, with the model tokenizer; atomically reserve budget before every send. Enforce **8,000 packet tokens, 20,000/request, 60,000/review and three requests including retries**. Test boundary values, restart, concurrent submission and a fourth request. Unknown input/accounting refuses. |
| Plausible evidence metadata passes without evidence | Recompute source hashes and extracted values from source bytes; verify population, denominator, missing/error counts and extractor identity. Independently alter each: refuse. Exclude whole historical documents/transcripts. |
| Failure or incomplete answer becomes approval | Transport failure, missing/duplicate/extra claim dispositions, unresolved claims or incomplete mandatory JEV coverage block dependent authorization. Inject each through the actual dispatcher: refuse advancement. |
| Unrecorded calls disappear from accounting | Match real request IDs and project/session identities; fail reconciliation on unmatched/unreadable records. A CyberGuard keyword mention is not attribution. Dispatcher refuses while reconciliation is unresolved. |

The inspected installed Codex provider configuration contains no D18 serialized-input limiter. Wiring alone therefore does not satisfy this proposal. Stage 2 must demonstrate interception of the actual final request. If input remains hidden or uncountable, external dispatch remains disabled; character estimates are prohibited substitutes.

**Residual bypass:** this restricts the CyberGuard session, not the workstation account. A human, unrestricted session or same-account process can launch Codex directly or modify controls. Auditing detects only activity covered by readable telemetry. Separate OS identities and machine-wide process/network containment are outside this approval. Missing telemetry cannot prove that no bypass occurred.

**4. THE STAGED ROLLOUT**

The commands below are implementation deliverables. They are not represented as existing or passing today. Every stage requires exit 0 plus Astra’s inspection of its evidence; missing measurements exit nonzero.

Definition of done:

| Stage | Actions, acceptance exit and rollback |
|---|---|
| **1 — Preserve** | Operator saves signed scope, installed versions, effective configuration, registered project identity and originals of every touched artifact. Worker builds the test entry point. Run `python3 docs/dsh/check_enforcement.py baseline`: exit 0 requires a full hash manifest and restorable originals. **Rollback:** discard candidate; no live change. |
| **2 — Repair** | Worker repairs checks/launchers and the existing adapter. Use the real dispatch/serialization paths with external egress blocked. Run `python3 docs/dsh/check_enforcement.py boundary`: exit 0 requires every §3 case, pre-fix failure, post-fix pass, failure again with each load-bearing control disabled, twin-path checks and full affected test suites. **Rollback:** discard candidate. |
| **3 — Isolate** | Operator uses a separate DSH_HOME inside the acceptance directory, copied installed bundles/configuration, no live credentials, blocked external egress and distinct local endpoints. Load web and headless compositions with the copied home patch; mount candidate; inspect effective tools; exercise forbidden calls, serialization, restart and restoration. Inject an unknown configuration key: startup must fail only in the isolated copy. Run `python3 docs/dsh/check_enforcement.py isolated`: all cases and restoration must pass. **Rollback:** remove isolated instance. |
| **4 — Canary** | Operator installs only the tested project composition/provider revision and binds one new CyberGuard session. Run `python3 docs/dsh/check_enforcement.py canary`, sends disabled: identical permissions, refusal behavior, reconciliation and unchanged home-patch hash required. **Rollback:** terminate canary, restore installation originals and leave CyberGuard stopped; never resume the unrestricted worker. |
| **5 — Accept** | Astra inspects all results and code/config diffs. Run `python3 docs/dsh/check_enforcement.py acceptance`: every preceding stage, complete inventories, tested rollback and unchanged model contract required. External-call status remains **DISABLED**. Offline tests cannot establish live provider success. |

**The home patch is not edited.** Its inspected SHA-256 is:

`1e82808792ad310cfbf019478428e20fe47f5bbf7c6c280f37aa2f7f4d49ba53`

Verify using `sha256sum /home/clawer-samurai-1/.dsh/cordis.patch.yml` at every stage. A need to change it blocks this rollout and requires a separate concrete proposal, not a worker-selected workaround.

New test runtimes follow `/home/clawer-samurai-1/AgentHub/2ndbrain/ops/PROJECT-ONBOARDING.md` and its existing launch wrappers. Stage 1 resolves registered identity; missing registration blocks launch. No invented IDs or unregistered service starts.

**5. JEV’S ROLE**

D14–D16 supply the binding contract:

- Apply existing Q1–Q10 verbatim to externally shareable training rows: empty answers, premise contradiction, thinking-control tokens, recorded truncation, unfinished content, unfilled templates, duplicates, explicit refusal and substantive response. Apply applicable factual questions to evaluated responses.
- Apply B1–B8 to Astra/worker reports: file existence, verbatim quotes, arithmetic, UTC ordering/duration, artifact-field identity, primary-source attribution, whether evidence measures the claimed quantity, and whether comparisons support the claimed change.
- Keep exact hashes, equality, token counts and arithmetic in code. Astra resolves contradictions against primary evidence. Missing/malformed/unavailable/abstaining required answers block dependent advancement and enter D16 supplemental human review; human review cannot manufacture JEV completion.

Only authorized public or synthetic material may leave the machine. Synthetic substitutes cannot certify private originals. This proposal makes **no JEV call** and claims no JEV endorsement: its assessment is **UNMEASURED**. D18 local repair checks remain permitted; dependent project advancement remains blocked by missing mandatory coverage.

JEV is load-bearing as a **coverage prerequisite**, never as an acceptance judge. Giving probabilities acceptance weight requires relevant public third-party benchmark calibration and a subsequent explicit Astra ruling defining the permitted use. Replacing human review additionally requires amending D7/D11. Calibration design/execution is outside this repair approval. JEV may not choose policy, bars, budgets, datasets, admission, repair, training or shipping.

**6. COST AND TIME**

| Resource | Authorized allocation or measured status |
|---|---|
| GPU-hours | **0 allocated to this repair.** Tests use CPU only; this is an allocation, not a past-consumption claim. Stage records check for unauthorized GPU processes. |
| Engineering hours | **UNMEASURED.** Record operator/worker start-stop intervals by artifact and sum actual hours. Charge within the existing **80 worker-hour ceiling**. |
| Human-review hours | **UNMEASURED** for this repair/supplemental review. Reviewer time records measure actual hours within the existing **800-hour ceiling**. The **25,500 initial reviews plus adjudication** remain unchanged. |
| Calendar | Completion duration **UNMEASURED**; UTC stage timestamps measure it. The first-24-hour report is a deadline, not a promise to finish all stages. D10’s **45-day target from activation** remains unchanged. |
| External spend | **$0 new rented GPU/API spend authorized; sends disabled.** Monetary cost and savings remain UNMEASURED pending billing records and reconciled telemetry. |

Established owner-supplied accounting: 29,532,513,003 / 3,000,000,000,000 × 100 = **0.9844171%**; cacheRead **98.87%**, supplied rather than remeasured here. Token totals do not establish monetary cost. Unknown remaining allowance blocks work requiring that allowance; this approval enlarges no ceiling.

**7. WHAT THE OWNER IS APPROVING**

- [ ] Local repair, offline tests and one restricted CyberGuard canary using **Codex/Astra as the active reviewer**; Claude, Grok and Kimi remain registered **placeholders**, uninvoked and untested in this approval; **ZERO external review/JEV sends**.
- [ ] All four adapters are **advisory reviewers only**. No child execution, repository access, mutation, browsing, connectors, skills, continuation or delegation.
- [ ] **One shared D18 allowance per authorized review** — 8,000 packet / 20,000 per request / 60,000 cumulative / **three requests including retries across ALL adapters**. No four-call panel, no per-adapter reset.
- [ ] Separate exact adapter bindings, authorization and final-request enforcement; every per-adapter and cross-adapter bypass test passes. Unknown measurement means refusal.
- [ ] **Astra specifies reviewer assignments.** No worker-selected substitution, fallback, extra reviewer or budget extension.
- [ ] Cross-family agreement has **ZERO acceptance weight**. Independence and incremental benefit remain **UNMEASURED**; calibration is outside this approval.
- [ ] Mandatory applicable JEV coverage, JEV's zero acceptance weight, and all D7/D11/D16 human-review obligations unchanged.
- [ ] Project-scoped only; **unchanged home-patch hash**; no permission expansion in unrelated sessions.
- [ ] Acceptance of the existing same-account/manual bypass limitation; **no claim of workstation containment**.
- [ ] Effort inside existing ceilings; **ZERO external-request allocation and $0 additional API spend.** Live review needs separately authorized aggregate limits.
- [ ] **D9 remains active** — no training, generation, rescoring, acquisition, model evaluation or release.
- [ ] Every rollout stage is required for acceptance **for the Codex path**. The four-adapter matrix (condition 5) and the cross-adapter matrix (condition 6) are **deferred to a later, separately authorized rollout** when the placeholders are activated. Offline acceptance grants no live-call authority.

**Signature:** ____________________ **UTC date/time:** ____________________

**8. WHAT DOES NOT CHANGE**

D1–D18 remain in force, with only the signed local repair deployment scope added. D9 remains active. The warm/fresh recovery pilot, parents, sources, mixture, rejection-only policy, registered metrics, bars, sample sizes, denominators, parsers, decoders and human-review obligations remain unchanged. Repair acceptance is not model qualification. D13 off-machine backup/restoration remains required before evidence restoration; configuration rollback does not substitute for it.

Controlling files inspected this session; verify with `sha256sum docs/ASTRA-DECISIONS.jsonl docs/ACTIVE-PLAN.md docs/PLAN-OF-RECORD.md`:

| Artifact | SHA-256 before approval |
|---|---|
| docs/ASTRA-DECISIONS.jsonl | `0e6b73bf5f2a3609885bbdb6409a9ed5a42c1d9bb0d236f4af4e0052816550f1` |
| docs/ACTIVE-PLAN.md | `45b9654bdeac8053838509c319223d4ba0e5482ab094309a6f0e086d82323cb4` |
| docs/PLAN-OF-RECORD.md | `fab5f18ccd7b11d5ff744059ff12591f6bd94b4c8b7c0cd5c49f310a7d87655d` |

Append signed authorization without rewriting existing register entries. The two plan files remain unchanged.

**9. THE FIRST 24 HOURS AFTER APPROVAL**

1. **Owner/operator:** sign and save this decision. **Astra:** specify its exact local-repair authorization for the register; retain D9.
2. **Operator:** stop the bypass-capable CyberGuard session; preserve touched-file originals and evidence, resolve registered identity, and record remaining allowance from actual accounting.
3. **Worker:** implement the acceptance entry point; run stage 1. Preserve failing pre-fix tests with external egress blocked.
4. **Worker:** repair gate, packet checks, accounting, legacy launchers and existing adapter; run stage 2, including isolated-control failures. No substitution or weakened check.
5. **Operator/worker:** run stage 3: both profile loads, unknown-key rejection, actual dispatch/serialization, restart and rollback. Proceed only on exit 0.
6. **Astra/operator:** inspect results; perform stage 4 only after stage 3 passes, then stage 5 only after the canary passes.
7. **Astra, by hour 24:** record measured hours, each stage’s PASS/FAIL/BLOCKED status, exact failure evidence, rollback status and external-call status in the acceptance verdict. Preserve unfinished work with its blocking condition; do not extend ceilings or resume project workloads.

### AMENDMENT — FOUR GOVERNED REVIEWER ADAPTERS (Astra, accepted with limits)

| row | provider / toolName | capability |
|---|---|---|
| `tool-subagent-codex` | `codex` / `subagent_codex` | advisory review within the standing model-training boundary |
| `tool-subagent-claude-code` | `claude-code` / `subagent_claude_code` | **PLACEHOLDER — registered, INACTIVE this rollout** |
| `tool-subagent-grok` | `grok` / `subagent_grok` | **PLACEHOLDER — registered, INACTIVE this rollout** |
| `tool-subagent-kimi` | `kimi` / `subagent_kimi` | **PLACEHOLDER — registered, INACTIVE this rollout** |

For **every** adapter: no repository access, shell, writes, browsing, connectors, skills, session
continuation, or further delegation.

**OWNER DIRECTION (recorded):** keep the three additional adapters as **registered placeholders**. The
current rollout uses **Codex/Astra only**. Claude, Grok and Kimi are **not invoked, not tested and not
budgeted** in this approval; they are wired later under the separate test matrix already specified in
condition 5. Their presence grants no permission to substitute reviewers, and no review may fall back to
them.

**Binding conditions**

1. All four share the **same immutable evidence packet** and fresh, **mutually isolated** contexts.
   Reviewers do not see one another's answers before recording their own. Packet must fit 8,000 tokens for
   **every** selected model's tokenizer.
2. **ONE SHARED D18 ALLOWANCE PER REVIEW: 8,000 packet / 20,000 per request / 60,000 cumulative input /
   THREE requests INCLUDING retries — across ALL adapters.** A fourth request is refused even with token
   allowance left. **No four-reviewer panel. No per-adapter reset. No automatic fan-out.** A missing
   selected reviewer blocks that review's completion.
3. Atomically reserve a request slot and its **measured** input before every send, including
   SDK/CLI-internal requests. Persist across restarts. Unknown usage stays unresolved and blocks dispatch;
   it is never refunded as zero. Changing adapter, session, packet hash or review ID cannot reset the
   allowance.
4. Dispatcher carries **four distinct exact-argument-vector bindings**, binding decision, authorized review,
   adapter, model, resolved executable, argument vector, code/config hashes and packet hash. No generic
   subagent command, no filename-substring matching, no user override of executable/args/endpoint/model/cwd/
   env/permission-mode/resume. **This approval authorizes offline test invocations only.**
5. For **each** adapter, the real loader, registry, dispatcher, child runtime and final serialization path
   must demonstrate identity resolution, blocked-transport delivery, refusal on every altered authorization
   field, absence of hidden context, refusal of all prohibited child capabilities, per-model boundaries,
   unknown-measurement refusal, and rollback restoration. **A provider-name match or mock adapter is
   insufficient.**
6. Test mixed-provider budget accumulation, retries, concurrency, restart, review-ID reset and a fourth
   request. The fourth must produce **zero additional provider sends.**

**Establishing configuration finding:** the installed web profile declares Grok and Kimi through ACP with
`permission: allow`. That declaration **does not** establish reviewer-only confinement. The real
child-capability tests settle confinement.

**Independence:** different provider names do **not** establish independent errors. Family diversity is
permitted; its incremental detection benefit and error dependence remain **UNMEASURED**. Substantiation
would need a separately authorized, preregistered, blinded assessment against an external reference
judgment. **Model agreement has ZERO acceptance weight** — it supplies leads for verification, never votes.

**All outputs are labelled "advisory review — zero acceptance weight."**

---

# ⚠ ARCHITECTURAL CORRECTION (Astra, after the owner challenged the path)

**Astra withdrew the restricted-composition proposal.** Its words:

> *"The direction is right; my proposed scope was wrong. Keep the worker's execution tools. Restrict its
> access to reviewer credentials and protected controls. **I withdraw the restricted composition as the
> CyberGuard worker architecture.**"*

The owner's objection was correct: the original proposal **removed shell and writes**, while the plan of
record **requires** them (dataset qualification, teacher generation, training, evaluation, packaging). A
worker without them cannot execute CyberGuard's plan at all.

## The corrected boundary

| | old proposal (WITHDRAWN) | corrected |
|---|---|---|
| worker shell / writes / compute | **removed** | **kept** — within an isolated execution environment |
| reviewer credentials | worker held them | **outside the worker's control**, held by a protected adapter |
| enforcement point | every tool call | **the resource and the transition it governs** |
| gate on every command | implied | **explicitly rejected** — *"Do not put a new approval gate on every command."* |

**Astra:** *"The worker can type `codex exec`. What must fail is the unauthorized model request, regardless of
whether it comes from that binary, Python, a copied executable, or a remote command. Removing a command from
the advertised tool list is insufficient."*

Required properties (**not** verified properties of today's installation):
- worker identity with writable project workspace + explicitly authorized execution resources
- separately protected review adapter holding provider credentials, enforcing the review contract, recording requests
- worker processes unable to read those credentials, modify adapter code/policy, or obtain unrestricted provider access
- the same boundary on remote destinations **including the GB10** — an unrestricted remote account reopens the route
- the trusted agent runtime keeps its own model credentials outside the shell environment
- controlled acquisition routes for approved data and dependencies (a provider-domain blacklist is **not** an acceptance criterion)

## What is a NECESSARY cost vs an OVER-RESTRICTION (Astra's ruling)

| gate | ruling |
|---|---|
| remove all worker shell/writes | **OVER-RESTRICTION — reject** |
| one shared config failure affecting every project | **OVER-RESTRICTION — avoid** |
| deny direct reviewer-provider access | **necessary**; add authorized access through the adapter |
| controlled acquisition access | **necessary maintenance cost**; no approval per download inside an approved scope |
| protect adapter credentials, policy, authoritative records | **necessary**; worker prepares, operator installs |
| D18 input/accounting limits | **necessary under the existing ruling** |
| missing required JEV assessment | **existing policy cost**; does not stop unrelated authorized work |
| D9 freeze | **necessary while D9 is active**; repair permission is not workload permission |

**Astra's candor on JEV:** *"the register makes its coverage mandatory while assigning its probabilities zero
acceptance weight and leaving incremental benefit unmeasured. That is an explicit availability cost. I will
not describe it as proven beneficial or silently waive it."*

**Reviewer containment is not workload containment:** preventing unauthorized GPU work needs control over
GPU access or workload admission. *"a shell-accessible check script alone does not provide that boundary."*

## Scope: reusable mechanism, CyberGuard-only deployment

**No fleet-wide configuration change.** Parameterize project identity, writable locations, execution
resources, acquisition destinations, reviewer/model assignments, credentials, budgets, required
assessments, approval authorities and freeze state. Keep CyberGuard's datasets, evaluation contract, D9 and
JEV obligations **out of shared defaults**. **One project's failure must not block another.** The other ~99
projects stay unchanged, and **no claim is made that this repair protects them.**

## Escape hatch

The owner may approve a **narrowly scoped operational exception**, applied by an operator outside worker
control. Recorded in a protected record: project, blocked operation, reason, authorizer, exact scope,
expiry/one-use limit, resource allowance, restoration check. **Exceptions expire automatically, cannot renew
themselves, and remain visible.** Repeated exceptions require fixing the policy, not extending again.

An exception grants permission to perform an operation. **It never converts missing evidence into a pass**,
and cannot quietly replace mandatory reviewers or change registered bars, sample sizes or metrics.

## The risk the owner is accepting

Astra: *"additional access maintenance and review-service availability dependence — **not a guarantee of
correct model judgments**."*
