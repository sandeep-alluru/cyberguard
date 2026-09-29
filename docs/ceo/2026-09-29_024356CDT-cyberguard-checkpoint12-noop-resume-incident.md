# CyberGuard v2 — checkpoint 12 (incident): the window was training nothing for three hours

**One line:** the 23:29 relaunch resumed both arms with `PeftModel.from_pretrained(...)` — whose default is
`is_trainable=False` — so every one of the 66,060,288 LoRA parameters was frozen; both arms reported
`trainable params: 0` and `grad_norm: 0` on all 99 logged lines while consuming **6.02 GPU-hours of the
owner's authorization for no learning at all**. It was found by reading a log, not by any gate. It is fixed,
verified, and now gated so it cannot recur silently.

## What the evidence says

| | arm A (`spark-40ee`) | arm B (`spark-8cf2`) |
|---|---|---|
| epoch 1 (10:24:28 → 21:26:14 / 21:25:20) | **11.03 h, genuinely trained** | **11.01 h, genuinely trained** |
| epoch 1 trainable params / grad_norm | 66,060,288 (1.6157 %) / ≈0.60–0.66 | 66,060,288 (1.6157 %) / ≈0.61–0.66 |
| 23:29 resume (23:29:36/45 → 02:30) | **3.01 h, `trainable params: 0`, grad_norm 0 × 99** | **3.01 h, `trainable params: 0`, grad_norm 0 × 99** |
| artifacts harmed | none — the epoch-1 adapters were untouched | none |

Two independent signals agreed throughout the frozen window: the parameter count was zero **and** the
gradient norm was zero on every logged step. Either alone would have been suspicious; the pair is decisive.
The learning-rate trace also restarted from warmup (`5.882e-06 → 1.000e-04`), confirming the optimizer and
scheduler were reset rather than continued — a weights-only continuation that was, in fact, no continuation.

The adapters produced by epoch 1 are real and are preserved with sha256 receipts
(arm A `e9d2f7b6…`, arm B `e567cb13…`, 264,308,896 bytes each), so the fallback artefact is a genuine
completed pass over the mixture rather than a loss.

## What was done

1. **Stopped** the frozen runs at 02:30–02:32 rather than let them finish their 9.5-hour box.
2. **Fixed** the resume path to `is_trainable=True`, and removed the redundant `get_peft_model` re-wrap that
   nested the adapters instead of unfreezing them.
3. **Guarded the class of failure, not the instance:** the trainer now refuses to start when the count of
   parameters with `requires_grad` is zero, and says why. The guard asserts on the *outcome*, which is the
   only reason this cannot recur silently.
4. **Relaunched** at 02:32:53 with a 570-minute box (ends 12:02:53) and re-verified immediately:
   both arms report `trainable params: 66,060,288 || trainable%: 1.6157` — identical to epoch 1, against
   `0` before.
5. **Made the three copies one artefact:** repo and both hosts are byte-identical
   (`train_cyberguard.py` sha256 `e4026df6…`), so the arms are reproducible from the repository.

## Why no gate caught it

The old contract could not have caught it either: it checked that an adapter *existed*, and a frozen run
writes a perfectly well-formed 264 MB adapter that is simply identical to its input. Two gates were added:

* **contract stage 00** — refuses to evaluate until both trainers have exited, so a half-written adapter can
  never be pulled (the contract was scheduled to pull four minutes before training ended);
* **contract stage 0d** — compares each adapter against the parent it resumed from and **fails closed** if the
  weights did not move. Its controls were tested three ways: identical weights fail, a genuinely different
  checkpoint passes, and a checkpoint older than the window under test is refused rather than counted.

## Independent review

Codex-Astra review #14 was run on the incident and the repair. It **cleared** the continuation artefact for
evaluation and returned no training-validity objection, with four required description changes and one
evidence gap:

* the reset changes the **optimization trajectory**, not merely the name — the result cannot substantiate a
  claim about *uninterrupted* training; the honest description is "one completed pass, followed by a partial
  second data pass with fresh optimizer state and a restarted LR schedule";
* exposure must be reported as **measured additional updates per saved artefact**, not as a projection;
* the frozen interval must be **excluded from learning exposure** (it stays in the cost accounting);
* "trainability restored" is supported, but **actual learning was unverified** — the reviewer asked for a
  nonzero optimizer-applied weight change against the preserved parent. That measurement is running now
  against the first step-500 checkpoint, and the same check gates the contract at 12:10.

## Cost to date (owner's authorization: 24 h × 2 = 48 GPU-hours)

| item | GPU-hours |
|---|---|
| epoch 1, both arms (real training) | 22.04 |
| frozen resume, both arms (**wasted**) | **6.02** |
| remaining under the 570-min cap, both arms | 19.00 |
| **worst-case total** | **47.06 of 48 authorized** |

All figures are cited from `v2/data/mixture/FACTS.json` and receipted in
`v2/data/mixture/noop-resume.receipt.json`. `refresh_facts.py` now carries these measured runtime facts
forward, because regenerating that file would otherwise have deleted the only machine-readable record of the
incident.

## What is open

* The learning proof against the first checkpoint (running), and the mandated checks at 12:10.
* The evaluated artefact will be a **continuation**, not one continuous schedule; the verdict must say so in
  exactly those terms, per review #14.
* The 24-hour window's second pass is partial by construction: the box stops it mid-epoch, so total exposure
  is one completed pass plus a partial second pass, per arm.
* `VERDICT-v2.md`, the checksummed harvest and the gate report still do not exist, so the objective is not
  complete.
