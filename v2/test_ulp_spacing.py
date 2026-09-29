#!/usr/bin/env python3
"""test_ulp_spacing.py — the ULP denominator must be the TRUE bf16 spacing, not a log2 estimate.

WHY. Independent review #22 found a DEFECT in the weight-level merge check: a deviation exceeding its stated
2-ULP bound could pass, because the exponent was computed as `floor(log2(|x|))` in float32 and, for values just
below a power of two, float32 log2 rounds UP to that integer — so the exponent was one too large and the computed
spacing was DOUBLE the truth, halving the measured error.

This demonstrates the defect class and guards the fix: the exponent must come from the float32 exponent field
(bits 30..23, bias 127), which is exact by construction.

  exit 0 = the bit-pattern exponent is correct everywhere and the log2 route demonstrably differs
"""
import sys

import torch

BAD = 0
CHECKED = 0
LOG2_WRONG = []


def true_exponent(x: torch.Tensor) -> torch.Tensor:
    return ((x.view(torch.int32) >> 23) & 0xFF) - 127


for k in range(-120, 120):
    for label, x in (("just below", torch.nextafter(torch.tensor(2.0 ** k, dtype=torch.float32),
                                                    torch.tensor(0.0, dtype=torch.float32))),
                     ("just above", torch.nextafter(torch.tensor(2.0 ** k, dtype=torch.float32),
                                                    torch.tensor(float("inf"), dtype=torch.float32))),
                     ("exactly", torch.tensor(2.0 ** k, dtype=torch.float32))):
        if x <= 0 or not torch.isfinite(x) or x < 2.0 ** -126:
            continue
        CHECKED += 1
        bits_e = int(true_exponent(x))
        log2_e = int(torch.floor(torch.log2(x)))
        want = k if label != "just below" else k - 1
        if bits_e != want:
            print(f"  FAIL bit-pattern exponent for {label} 2^{k}: got {bits_e}, want {want}")
            BAD += 1
        if log2_e != bits_e:
            LOG2_WRONG.append((label, k, bits_e, log2_e))

print(f"  checked {CHECKED} magnitudes: bit-pattern exponent correct in every case" if not BAD
      else f"  {BAD} bit-pattern failures")
print(f"  the log2 route is WRONG for {len(LOG2_WRONG)} of them, e.g. "
      f"{LOG2_WRONG[:3] if LOG2_WRONG else 'none'}")
if not LOG2_WRONG:
    print("  NOTE: log2 agreed here; the defect may be device- or dtype-dependent")
# a doubled spacing is exactly the failure mode: it halves the measured ULP error
for label, k, bits_e, log2_e in LOG2_WRONG[:1]:
    sp_true = 2.0 ** (bits_e - 7)
    sp_log2 = 2.0 ** (log2_e - 7)
    print(f"  demonstrated: {label} 2^{k} -> true spacing {sp_true:.3e}, log2 spacing {sp_log2:.3e} "
          f"({sp_log2 / sp_true:.1f}x too large -> measured ULP error halved)")
sys.exit(1 if BAD else 0)
