codex
**Verdict: do not scale this harness to 3 trillion tokens yet. The root failure is bypassable enforcement: consequential actions remain available without satisfying the checks intended to govern them.** More instructions cannot close that gap.

Evidence basis: T1–T4 are supplied incident evidence, not independently reproduced here. I verified the adapter declarations and inspected the local gate. The worker’s accounting was wrong twice; the corrected raw totals remain **UNVERIFIED** until reconciled against deduplicated request records and provider usage. Their arithmetic is correct: **29,532,513,003 / 3 trillion = 0.9844%**, almost ten times the stated 0.10%. That increases the urgency. Cache reads constitute 98.87% of the supplied total; token volume alone does not establish dollars spent or waste.

**1. Five missing properties**

| Property | Category | What it would have prevented or contained |
|---|---|---|
| **Mandatory mediation of consequential actions — ROOT** | Enforcement | Shell delegation bypassing adapters; training proceeding after a failed audit or missing human check. |
| Accurate, callable capability discovery | Discoverability | Being instructed to use governed adapters absent from the worker’s actual toolset. |
| Independent acceptance of complete artifacts | Verification | Accepting “no-trail” filenames as evidence, dropping label vectors, validating emptiness with the wrong quantity. |
| Reconciled usage with unknowns represented honestly | Accounting | Placeholder zeros and spending decisions based on duplicated or misinterpreted usage. |
| Failure and progress signals that trigger action | Feedback | Suppressed command failures, “success” with reconciliation outstanding, and an unattended 12.5-hour zombie. |

These controls prevent acceptance or continued spending; they do not guarantee that models never produce defective work.

**2. The ecosystem diagnosis is correct but incomplete.** Knowing an adapter exists does not make it callable. The [preset declares the adapters](/home/clawer-samurai-1/.dsh/.agent-presets/standard-agents/agent.cordis.yml:284); supplied T2 says the worker cannot reach them. **Cause: UNMEASURED.** Comparing that session’s selected preset, mounted providers, policy filtering, and final model-facing tool catalog settles it.

Capability awareness belongs in a compact description generated from the **effective runtime registry**, injected when a session starts and refreshed when capabilities change. Advertise callable tools and report unavailable required capabilities explicitly. A preset declares intent; a skill explains use. Neither proves availability. Prevent stale claims by deriving discovery and dispatch from the same runtime state.

**3. Enforcement must live outside the worker’s authority.** Authorization, budgets, and prerequisite checks must control actual process launches and provider access, including shell descendants. The worker cannot retain an unrestricted alternative using its own credentials or network access.

The inspected [Astra gate](/home/clawer-samurai-1/AgentHub/cyberguard/tools/astra_gate.py:1) explicitly checks and prints an action without executing it. **That file does not make checking mandatory.**

With unrestricted shell access and usable provider credentials, non-bypassability is unattainable. It becomes achievable only by restricting those authorities and mediating their use. Whether deployed DSH can enforce that boundary is **UNMEASURED**; controlled attempts through direct CLI, API, and child-process routes settle it. Any remaining accessible credential, remote execution route, or writable enforcement component remains a bypass.

**4. DONE requires independent acceptance.** Before work starts, define the requested output, complete population in scope, acceptance conditions, and required human decisions. A verifier outside the worker’s control checks the exact resulting artifacts against those conditions. Failed, missing, or unmeasured requirements block acceptance and dependent work.

The worker’s self-tests are useful diagnostics, not independent acceptance. A second model running the same flawed detector is not independent re-derivation. Objective claims need checks derived from raw artifacts; judgment claims need an accountable reviewer. The required human check cannot be replaced silently.

**5. Minimum action today, in order**

1. **Owner: pause new expensive workloads through controls the worker cannot override.** Cost: delayed throughput.
2. **Harness maintainer: restore reachable governed adapters and close alternate launch/access paths.** Exit: intended calls succeed with attribution; controlled bypass attempts fail. Cost: engineering effort and small test calls.
3. **Independent evaluator: replay the cited failure cases against acceptance checks.** Exit: defective artifacts and failed commands are rejected; corrected controls pass. Cost: artifact inspection and bounded reruns.
4. **Accounting owner: reconcile raw request usage and provider records; preserve missing usage as unknown.** Cost: reconciliation work, then measured verification overhead.
5. **Owner: resume bounded work only after those exits pass.** No unrestricted scale-up.

Engineering hours and dollar costs are **UNMEASURED**; deployment inspection, replay timings, and actual provider billing settle them. Supplying estimates now would repeat the accounting problem.

**6. Configuration cannot supply the missing trust boundary or truth oracle.** Wiring can expose adapters. It cannot make unrestricted worker authority non-bypassable, make self-certification independent, or guarantee that an acceptance test captures the owner’s intent. Those require architectural separation and accountable acceptance.

**The evidence warrants changing the harness before scaling it. It does not establish that DSH must be discarded; it establishes that the current operating arrangement has not earned authority over a 3-trillion-token budget.**
