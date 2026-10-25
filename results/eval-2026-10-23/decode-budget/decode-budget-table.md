### G-4 decode-budget sensitivity — v3 on CTI-MCQ, same population, only `max_new_tokens` varies

Population: CTI-MCQ, 2,500 items, identical at every budget.  
Comparator (CyberSecQwen-4B, same frozen surface): **0.5764**.  
Always-C baseline: **0.3712**.

| max_new_tokens | n | strict accuracy | unparseable rate | at/near cap (re-tokenized, instrument-dependent) | truncation signature (field-independent) | batch-labelled rate (upper bound) | vs comparator |
|---|---|---|---|---|---|---|---|
| 512 | 2500 | 0.4660 | 0.4116 | 0.4424 (1106/2500) | 0.3652 | 0.9744 | -11.04 pp |
| 1024 | 2500 | 0.6112 | 0.1684 | 0.1720 (430/2500) | 0.1492 | 0.7568 | +3.48 pp |
| 2048 | 2500 | 0.6404 | 0.1024 | 0.1032 (258/2500) | 0.0880 | 0.5680 | +6.40 pp |

**Reading.** A budget row is present only where the sweep produced that budget's `results-v3-public.json`; a missing budget is written MISSING and is never substituted with another budget's number.

**The two right-hand columns are evidence for a ruling, not a published rate.** The escalation `docs/ESCALATION-E2-T-TRUNCATION-FIELD-WITHDRAWAL.md` offers three treatments for the withdrawn decode-cap rate and states that **the worker does not choose** between them; under Treatment B the choice of instrument is explicitly a ruling's. So this table reports the ingredients and their provenance and selects no treatment. The *batch-labelled rate* is the runner's `termination` field, and it is the **batch** rate — *this item's batch contained at least one item that reached the cap* — because the runner computes the length from a rectangular tensor and records the batch's maximum; the project's own B6 withdrew the per-item figure that rested on it, so here it is only the upper bound. The *at/near cap* column re-tokenizes each response's own text with the model's tokenizer, and the *truncation signature* column is the project's existing tokenizer-independent instrument. Both are stated as instrument-dependent evidence, and the escalation's own caveat is carried: the text proxy under-counts by construction.

**The decision-relevant numbers in this table are the first two columns of figures — strict accuracy and the unparseable rate — because they are the sweep's own outputs and they settle the question the sweep was run to answer: whether a larger decode budget changes the score.**
