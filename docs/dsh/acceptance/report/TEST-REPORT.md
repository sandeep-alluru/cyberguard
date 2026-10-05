# TEST REPORT — Framework Fix Ledger, approved scope

**Generated 2026-10-05 08:07:51Z · the single artifact Sandeep signs (per D20).**

**D9 REMAINS ACTIVE. Group 2 (B01–B27) and C02–C05 untouched.**

## Criteria applied

Owner criterion D20: the deliverable is a **FAILABLE MICRO TEST**, not a document diff and not a human eyeball check.

1. The test must be **demonstrated to FAIL** — against the pre-fix state, or with the load-bearing control disabled. **A test never seen to fail is rejected as a smoke test.**
2. The test must then **PASS** against the fixed state.
3. The **full suite runs TWICE** — fail-pass cycle, then a clean repeat pass.

## Summary

| check | result |
|---|---|
| rows in approved scope | **20** (A01–A19, C01) |
| failed against pre-fix state | **17/20** |
| proven failable with control disabled | **20/20** |
| **smoke tests** | **0** — NONE |
| pass after fix (run 1) | **20/20** |
| pass after fix (run 2, clean repeat) | **20/20** |
| home-patch H holds | **YES** |


## Per-row evidence

### A01 — OWNER-DECISION: withdrawn design superseded, not appended

- **Fail-before:** passed pre-fix; failability shown by CONTROL
  - pre-fix evidence: `withdrawal=True superseded_opening_still_operative=False`
- **Control (load-bearing control disabled):** re-insert the withdrawn design as the operative opening proposal
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `withdrawal=True superseded_opening_still_operative=False`

### A02 — OWNER-DECISION: separate-identity mentor ruling incorporated

- **Fail-before:** FAIL
  - pre-fix evidence: `separate_identity_ruling_present=False`
- **Control (load-bearing control disabled):** remove the separate-identity ruling
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `separate_identity_ruling_present=True`

### A03 — ARCHITECTURE: stale 'not persisted' claim removed

- **Fail-before:** FAIL
  - pre-fix evidence: `stale_not_persisted_claim=False`
- **Control (load-bearing control disabled):** re-insert the stale not-persisted claim
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `stale_not_persisted_claim=False`

### A04 — ACTIVE-PLAN: absent pipeline exits marked planned

- **Fail-before:** passed pre-fix; failability shown by CONTROL
  - pre-fix evidence: `planned-deliverable qualification present`
- **Control (load-bearing control disabled):** remove the planned-deliverable qualification entirely
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `planned-deliverable qualification present`

### A05 — ACTIVE-PLAN: strict validation passes

- **Fail-before:** FAIL
  - pre-fix evidence: `plan-validate exit=2`
- **Control (load-bearing control disabled):** re-insert a blank required cell and an undeclared absent path
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `plan-validate exit=0 on cyberguard`

### A06 — PLAN-OF-RECORD: stale session status removed

- **Fail-before:** passed pre-fix; failability shown by CONTROL
  - pre-fix evidence: `stale_session_status_present=False`
- **Control (load-bearing control disabled):** re-insert the stale session-status line
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `stale_session_status_present=False`

### A07 — PLAN-OF-RECORD: D13 restoration reflected

- **Fail-before:** FAIL
  - pre-fix evidence: `d13_restoration_reference=False`
- **Control (load-bearing control disabled):** remove the D13 restoration reference
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `d13_restoration_reference=True`

### A08 — gate: refuse wrong/altered/D9-as-permission, dispatch exact

- **Fail-before:** FAIL
  - pre-fix evidence: `{"wrong_action_refused": true, "exact_authorized_dispatched": false, "altered_args_refused": true, "d9_as_permission_refused": true}`
- **Control (load-bearing control disabled):** weaken the gate to allow any D19 row (disable the allowlist)
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `{"wrong_action_refused": true, "exact_authorized_dispatched": true, "altered_args_refused": true, "d9_as_permission_refused": true}`

### A09 — review_packet: no enforcement overclaim

- **Fail-before:** FAIL
  - pre-fix evidence: `claims_actual_serialized=True uses_char_estimate=True claims_cumulative_enforcement=False`
- **Control (load-bearing control disabled):** inject a positive serialized-request enforcement claim and remove the estimate disclosure
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `claims_actual_serialized=False uses_char_estimate=True discloses_estimate=True claims_cumulative_enforcement=False`

### A10 — wrapper: returns failure on launch failure

- **Fail-before:** FAIL
  - pre-fix evidence: `suppresses_failure=True fails_on_bad_input=True`
- **Control (load-bearing control disabled):** re-insert the failure suppression
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `suppresses_failure=False fails_on_bad_input=True`

### A11 — launchers: no direct codex invocation

- **Fail-before:** FAIL
  - pre-fix evidence: `tools/review_cycle.sh:direct,v2/dispatch_review.sh:direct,v2/checkpoint_review.sh:direct`
- **Control (load-bearing control disabled):** re-insert a direct codex invocation into a launcher
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `clean`

### A12 — audit_reviews: real request matching + nonzero exit

- **Fail-before:** FAIL
  - pre-fix evidence: `reads_request_ids=True compares_session_identity=False warns_but_passes=True`
- **Control (load-bearing control disabled):** restore the lenient warn-and-pass behaviour (no identity match, exit 0)
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `reads_request_ids=True compares_session_identity=True warns_but_passes=False`

### A13 — accounting: no zero placeholders

- **Fail-before:** FAIL
  - pre-fix evidence: `zero_placeholder_rows=2`
- **Control (load-bearing control disabled):** re-insert a zero placeholder row
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `zero_placeholder_rows=0`

### A14 — FAILURE-REGISTER: CLOSED means verified

- **Fail-before:** FAIL
  - pre-fix evidence: `closed_by_plan_present=True`
- **Control (load-bearing control disabled):** re-insert CLOSED by plan
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `closed_by_plan_present=False`

### A15 — HARMBENCH: lost vectors disclosed

- **Fail-before:** FAIL
  - pre-fix evidence: `loss_disclosed=False`
- **Control (load-bearing control disabled):** remove the lost-vector disclosure
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `loss_disclosed=True`

### A16 — FRR: heuristic transition qualified

- **Fail-before:** FAIL
  - pre-fix evidence: `has_refusal_phrase=True heuristic_qualified=True carries_harmbench_limit=False`
- **Control (load-bearing control disabled):** remove every HarmBench limitation marker from the FRR side-by-side
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `has_refusal_phrase=True heuristic_qualified=True carries_harmbench_limit=True`

### A17 — ROLE-PROTOCOL: instrument list not exhaustive

- **Fail-before:** FAIL
  - pre-fix evidence: `stale_exhaustive_wording=True scoped_against_plan=False`
- **Control (load-bearing control disabled):** re-insert unscoped exhaustive wording and remove the plan-of-record scoping
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `stale_exhaustive_wording=False scoped_against_plan=True`

### A18 — acceptance dir populated

- **Fail-before:** FAIL
  - pre-fix evidence: `dir absent`
- **Control (load-bearing control disabled):** empty the acceptance directory
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `acceptance_files=57`

### A19 — scanner exists and detects planted entry point

- **Fail-before:** FAIL
  - pre-fix evidence: `scanner absent`
- **Control (load-bearing control disabled):** remove the planted-entry detection
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `planted_detected=True clean_passes=True`

### C01 — manifest round-trips byte-identical + home patch holds

- **Fail-before:** FAIL
  - pre-fix evidence: `preserve manifest absent`
- **Control (load-bearing control disabled):** corrupt one preserved copy so round-trip fails
  - test fails with control disabled: **YES**
- **Pass-after:** PASS (both runs)
  - live evidence: `coverage=17 entries missing=0 roundtrip=True home_patch_ok=True`


## Invariants

- **H — home patch unchanged:** `1e82808792ad310cfbf019478428e20fe47f5bbf7c6c280f37aa2f7f4d49ba53`
- Expected: `1e82808792ad310cfbf019478428e20fe47f5bbf7c6c280f37aa2f7f4d49ba53`
- **HOLDS**


## What this report does NOT establish

Failability and passage of these tests is **not** model qualification, not proof the corrected framework enforces anything at runtime, and not completion of mandatory factual assessment. Group 2 (B01–B27) and C02–C05 remain **BLOCKED** and are not covered here. Live provider success, boundary effectiveness and cost remain **UNMEASURED**.


## Sign-off

**Sandeep — do you accept this test report as the evidence of completion for A01–A19 and C01?**

```
Accept TEST REPORT for A01-A19 + C01; smoke tests 0/N; H holds; O2 D9 ACTIVE; signed [name] [UTC timestamp]
```
