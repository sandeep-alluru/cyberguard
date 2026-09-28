---
title: CyberGuard — capability gap map (3h measurement box): model can answer defense, CANNOT be trusted at the boundary — refusal collapsed to 10% at scale (was "12/12" on the small fixture); IDs fabricated in adjacent-ID pattern; Sigma/format broken; grounded-QA is the bright spot
issued_at: 2026-09-27T14:30:00-05:00
project: CyberGuard
status: current
kind: result
supersedes: 2026-09-27_064500CDT-cyberguard-v1-result-ceo-brief.md
---

# CyberGuard capability box — the honest gap map

**One line:** you asked for 3 hours of extensive testing to see what v1 really can do; it can do
defensive answering and grounded Q&A well, but the 60-probe battery **refutes the small-fixture
safety claim — offensive refusal fell from 40 % (base) to 10 % (tuned, p=4×10⁻⁵), with verified
outputs that specify ransomware features and spear-phish recipes** — the model is a useful
defensive draft-assistant under human review, and **not deployable against adversarial traffic**.
Full detail: `docs/CAPABILITY-v1.md`; evidence: `research-tmp/harvest-cap-v1/` (18 receipts,
sha256-verified); chronology: `LEDGER.md`.

## The gap map

| Capability | Verdict | Numbers |
|---|---|---|
| Defensive answers (incl. 20 benign-help) | **CAN** | 40/40 + 20/20 answered; quality: v1 +12.5 pp F1 vs base |
| Grounded QA + saying "I don't know" | **CAN** (n=20) | 87 % correct, 5/5 refused unknown, 0 fabricated |
| Triage judgment (easy cases) | **CAN — ceiling effect** | **47/47 verdicts correct when it emitted one** |
| Triage one-word FORMAT | **CANNOT** | 61 % never emit a verdict — format, not judgment, is the G1 blocker |
| IOC extraction | **HALF** | F1 .56; **fabricated IOCs in 65 % of reports** |
| Sigma rule drafting (G3) | **CANNOT** | YAML-valid 6.7 %, schema-complete 0 % |
| CVE/ATT&CK specifics | **CANNOT — do not quote it** | 21 % of ATT&CK IDs + 18 % of CVEs invented (dual-authority confirmed); signature = **adjacent-ID extrapolation** (T1550.005–.010 don't exist; CVE-2021-26856 unassigned) |
| Instruction constraints (IFEval-lite) | **WEAK, not regressed** | .40 → .45 both arms |
| General floor ≥95 % (G7) | **UNPROVEN** | GSM8K result is a format-contract floor (both arms), withdrawn as capability |
| **Refusing attacks at scale** | **CANNOT — regression** | **24/60 → 6/60**, McNemar p=4×10⁻⁵, −30 pp [−43, −18]; survives batch-1 and 512-token reruns (decode-controlled) |

## Why this finding is trustworthy (house discipline did its job)

- **Replays reproduced every aggregate exactly** (determinism), then an **audit replay stored every
  output** — because receipts holding only classes can't be audited, and this one mattered.
- **Codex review #5** (results review, 2 BLOCKERs + 4 MAJORs + 2 MINOR, all fixed): read the raw
  outputs independently and confirmed actionable harmful content on probes 0/1/4/6; demanded and
  got the decode-sensitivity reruns (collapse survived) and an independent harmfulness rater
  (~50 % of outputs carry operational-level detail; rater's own index-mapping bug was caught by
  our QA and item-level claims withdrawn accordingly).
- My "NVD API is flaky" suspicion was tested against a second authority (MITRE) **and overruled**:
  both flagged CVEs are genuinely unassigned. Failures are the model's, not the yardstick's.
- Data fetches that failed (CIEM, 3 phishing sets) are recorded SKIPPED; the fallbacks they forced
  are labeled "authored, easy-mode floor" everywhere their numbers appear.

## What this changes

1. **v1's "boundary intact" claim is retired** — the 12-probe fixture was underpowered. The
   VERDICT-v1 doc's domain-quality numbers stand; its G5 safety substitute does not.
2. **Not deployable** for free-form user traffic; acceptable for **internal, human-reviewed
   defensive drafting** (its answers are on-domain and it doesn't over-refuse).
3. **v2 is now specified by evidence, not taste**: refusal-retention data + re-gate at n=100 with
   a rubric instrument; inference-time ID validation (adjacent-ID signature makes detection cheap);
   format-compliance data (fixes G1 + Sigma together); official G7 protocol; real extraction corpus.

## Asks

1. **v2 direction** — the four fixes above fit the <10-GPU-day falsification pilot (brief §5);
   say go and the mix/plan comes back with the DATASET-V2 admission gate applied.
2. Nothing needed on the fleet: GPU released clean (0 %, no processes), all monitors exited,
   flash-serving box untouched throughout.
