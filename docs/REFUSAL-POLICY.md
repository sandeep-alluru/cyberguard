# REFUSAL-POLICY — the v4 corpus's refusal-stream weight

**Programme item C-5. Status: EXECUTED, and the target weight is one parameter away from being changed.**

**The target:** the refusal stream's share of the rebuilt corpus is **4.91 %** — **5,314
presentations** from the **1,198 distinct refusal rows**, in a final corpus of **108,238 rows**
(measured: **4.9096 %**).

**The corpus this produces:** `data/v4/corpus-v4-r2.jsonl` (sha256 and every check in
`data/v4/receipt-v4-r2.json`).

---

## 1. The evidence this rests on

The refusal stream is the only dial the programme has measured on **both ends at once** — the
false-refusal rate on benign security requests (MITRE-FRR, 750 prompts) and harmful compliance
(HarmBench, 159 valid behaviours).

| arm | refusal share of the mixture | false-refusal rate | harmful compliance |
|---|---|---|---|
| base model — **no refusal training at all** | — | **4.13 %** | 1 / 159 |
| **v2 arm B** | **4.91 %** | **17.47 %** | 5 / 159 |
| v3 | 6.82 % | 29.07 % | 0 / 159 |
| v2 arm A | 11.82 % | 35.33 % | 2 / 159 |
| public comparator (CyberSecQwen-4B) | — | 1.07 % | 3 / 159 |

**The controlled pair.** v2 arm A and arm B are the same 81,074-row mixtures with one stream
swapped. That single comparison moves the false-refusal rate by **−17.87 pp at exact McNemar
p = 5.1 × 10⁻²²**, while the harmful-side movement on the **same pair** (2/159 → 5/159, +1.89 pp)
is **not statistically significant** (p = 0.375).

> **The limit of that pair, stated.** One swapped stream is not one changed property. Inside the
> 5,600 substituted rows the content type, the prompt diversity and the answer length all move
> together, and the programme's own SPEC-V2 D2 gate for a matched control reads **NOT MET**
> (the evaluation record §5.3.6/§5.3.9). The pair identifies the refusal **slot's content** as causal;
> it does not separately identify the refusal behaviour inside that slot, and the sign of the
> diversity/length confound is not determined by these artefacts. That does not weaken the
> direction of the effect — 17.87 pp at p = 5.1 × 10⁻²² is not a small effect — but it is the
> reason the policy below claims a **slot**, not a mechanism.

## 2. Why 4.91 %, and not something else

**It is the lowest share for which the programme has a MEASURED false-refusal rate and a MEASURED
harmful-compliance count on the same arms, the same prompts and the same instrument.** Below it
the dose-response is an extrapolation, and the record calls that extrapolation UNMEASURED: *"there
is no arm in the family with a smaller refusal stream than arm B, so 'reweight the stream and the
gap closes' is a hypothesis with a measured direction, not a result."*

**It buys the certain gain.** Across the one controlled pair the false-refusal movement is large
and certain, while the harmful-side movement on the same pair is not statistically significant.
The corpus-only floor is the untrained base model's own **4.13 %**, and **17.47 %** is the lowest
false-refusal rate any *trained* arm in this family has achieved.

**It is not chosen to dodge a bar.** At this target the expected harmful-compliance count is
**5 / 159**, whose two-sided 95 % Wilson upper bound is **0.0554** — **above** the programme's
release bar of "at most 1/159 harmful, Wilson upper at most 3.5 %". The policy states that rather
than picking a share that would pretend to pass. **The public comparator fails that bar too**
(3 / 159, Wilson upper 0.0540), so the bar as written excludes the market comparator. That is
the evaluation record §8 Q11 and it is an open product decision — this policy cannot settle it, and
it does not pretend to.

## 3. The arithmetic that had to be got right

The removal of the two contaminated sources shrank the corpus from **140,545** to **112,508** rows while the refusal stream
stayed at **9,584** presentations. A share is a ratio, so the refusal share **rose from 6.82 % to
8.52 %** — an *increase* — purely as a side effect of removing two contaminated sources. Left
alone, the rebuilt corpus would have been *more* refusal-loaded than v3, and the dose-response
would have predicted a false-refusal rate near **33 %**, worse than the model the rebuild is meant
to improve.

So the reweight is solved against the **final** denominator, not applied to the old one:

```
R / (non_refusal_mass + R) = target_share
102,924 = 112,508 - 9,584   (the non-refusal mass, which the reweight does not touch)
R = 0.0491 x 102,924 / (1 - 0.0491) = 5,314      ->  final corpus = 108,238 rows
```

**Measured on the written file: 5,314 / 108,238 = 4.9096 %.** Stated as a **share**: 4.91 %.
Stated as a **row count**: 5,314 presentations. Weight over the distinct rows: 4.4357
(4–5 presentations each).

**Which presentations are kept.** All **1,198 distinct refusal rows survive** — the cut removes
presentations, never content. The remaining presentations are spread evenly over the distinct rows
in a deterministic round-robin, so no refusal family is over-represented by the cut. This follows
the record's own guidance for the v4 working corpus ("the same 1,198 rows, fewer
presentations").

## 4. What this policy is accountable to

- **The named release gate is met:** *"Zero stock preambles or thinking-control tokens across the
  release battery"* — the rebuilt corpus carries **0** of each (`data/v4/class-stock-preamble.json`,
  `data/v4/class-thinking-control-tokens.json`).
- **The pilot-spec bar is met:** ≤ 1 % of knowledge responses — the training-target rate for
  stock preambles is **0.00 %**.
- **The composition is inspectable:** every row of `data/v4/corpus-v4-r2.jsonl` is accounted for,
  and the 102,924 non-refusal rows are **byte-identical** to `data/v4/corpus-v4-r1.jsonl`.

## 5. Reversal path — and the alternatives, already computed

The target is **one parameter** in `eval-2026-10-23/c5_refusal_policy.py`. Changing it and
re-running re-emits the corpus in one command; no other step is re-measured, because nothing else
changes. The alternatives' row counts are already computed:

| target | refusal presentations | final corpus rows | measured share | expected FRR | expected harmful | basis |
|---|---|---|---|---|---|---|
| **4.91 % (this policy)** | **5,314** | **108,238** | **4.9096 %** | **17.47 %** | 5 / 159 | **measured** (arm B) |
| 6.82 % (v3's dose) | 7,533 | 110,457 | 6.8200 % | 29.07 % | 0 / 159 | **measured** (v3) |
| 11.82 % (arm A's dose) | 13,796 | 116,720 | 11.8200 % | 35.33 % | 2 / 159 | **measured** (arm A) |
| no refusal stream | 0 | 102,924 | 0.00 % | 4.13 % | 1 / 159 | **measured**, but on a model with no adapter — an inference for any trained model |

¹ The **share** is solved against the final denominator, so the *presentation count* that lands on
a target share differs from the original arm's count: arm A's 9,584 presentations were 11.82 % of
a **140,545**-row corpus, while the same share of the rebuilt 102,924-row non-refusal mass needs
**13,796**. **The share is the causal currency, not the presentation count** — the record
established that the arms' doses differ only in the denominator.

## 6. What would falsify this policy

The next checkpoint's **measured** false-refusal rate and harmful-compliance count at this share.
If the measured false-refusal rate lands materially above **17.47 %**, then the share→rate mapping
has moved with the corpus's other changes (the removal of the two contaminated sources, the new triage streams) and the target
must be re-derived from the new measurement rather than carried over from arm B. If the measured
harmful-compliance count lands materially above **5 / 159**, the controlled pair's "not significant"
reading does not hold at this share and the trade has to be re-priced.

## 7. How the target was set — stated plainly

The next-steps record (§2) noted that *"the refusal stream's weight is already cut from ×8.0 to
×4.08 …"*, that the target weight is a release decision, and the open-decision list asked *"what
FRR does the release target, knowing that every point of it is paid for on the HarmBench side?"*
The safety-posture choice sits with the release decision (the evaluation record §8 Q12; P2-1,
P2-2).

**A correction to the premise that question rested on, and it changes what the target means.**
That question rested on a **weight**. The measured variable is the **share** — the dose-response
curve in the evaluation record §5.3.9b is plotted against the refusal share of the training
mixture, not the presentation weight, and the two do not move together. Measured: the v4 working
corpus's weight was indeed halved (×8.0 → ×4.08) while its **share** sat at only **3.6066 %** —
*below* every point on the curve — and executing the removal of the two contaminated sources
**raised** the share from **6.8192 %** to **8.5185 %**. So a weight-based target would have been
chosen against the wrong number. **This policy therefore fixes the share** (4.91 %, arm B's
measured dose point), and the rebuilt corpus measures **4.9092 %**. Evidence:
`eval-2026-10-23/refusal-weight-audit.json` (**7/7** checks); the evaluation record §5.3.13.

**This policy is therefore executed under the approved 2026-10-23 direction** (**W-3**), recorded
with its reversal path, because the approved plan lists C-5 as *"decide and execute"* and the
standing instruction is to keep going without waiting. **It is not presented as settled.** The
target, the evidence, the two-sided cost and the alternatives are all above, and §5 makes changing
it one command.
