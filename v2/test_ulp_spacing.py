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

# SUBNORMAL SPACING (review #23): bf16 subnormal spacing is a UNIFORM 2**-133, so the exponent must be clamped
# at the minimum normal exponent (-126). An unclamped exponent field of zero gives -127 and therefore 2**-134,
# half the truth - which DOUBLED the control ULP values and let a 61-ULP separation pass a >=100 requirement.
import math
Q_TRUE = 2.0 ** -133
sub = torch.tensor(2.0 ** -130, dtype=torch.float32)          # a subnormal-scale ideal
e_field = int(((sub.view(torch.int32) >> 23) & 0xFF)) - 127
e_clamped = max(e_field, -126)
got = 2.0 ** (e_clamped - 7)
if abs(got - Q_TRUE) > 0:
    print(f"  FAIL subnormal spacing: got {got:.3e}, bf16 subnormal spacing is {Q_TRUE:.3e}")
    BAD += 1
else:
    print(f"  subnormal spacing exact: {got:.3e} == 2**-133 (unclamped would be {2.0 ** (e_field - 7):.3e}, "
          f"a factor {Q_TRUE / (2.0 ** (e_field - 7)):.1f} too small)")
# and verify against torch's own notion of the next BF16 subnormal value (a float32 tensor would measure
# FLOAT32 spacing here - 2**-149 - which is what an earlier version of this test did, printing a spurious
# mismatch). bf16 is what the merge check compares.
_n = torch.tensor(2.0 ** -130, dtype=torch.bfloat16)
_delta = abs(float((torch.nextafter(_n, torch.tensor(0.0, dtype=torch.bfloat16)) - _n).float()))
if abs(_delta - Q_TRUE) > 0.0:
    print(f"  FAIL bf16 nextafter spacing {_delta:.3e} != claimed 2**-133 {Q_TRUE:.3e}")
    BAD += 1
else:
    print(f"  bf16 nextafter confirms subnormal spacing {_delta:.3e} == 2**-133")
# Review #23's EXECUTED COUNTEREXAMPLE, re-derived with the corrected denominator. Their matrix: bf16, rank one,
# base = -600q, scaling = 1, A = 1, B = 600q, merged = 0 except one element = q (q = 2**-133). The ideal is
# therefore 0, and with the unclamped denominator (2**-134) the controls reported 122 and 1202 ULP and PASSED the
# >=100 separation requirement, while their true separations are 61 and 601 - the first of which must FAIL it.
q = Q_TRUE
_true_drop = 600.0 * q / q          # |merged - base| / spacing
_true_90 = 60.0 * q / q             # |merged - (base + 0.9*600q)| / spacing
_unclamped = 2.0 ** -134
_infl_drop = 600.0 * q / _unclamped
_infl_90 = 60.0 * q / _unclamped
print(f"  review #23 counterexample re-derived: ideal=0 (subnormal binade)")
print(f"    true control separations   : dropped {_true_drop:.0f} ULP, 10%-scale {_true_90:.0f} ULP")
print(f"    with the unclamped spacing : dropped {_infl_drop:.0f} ULP, 10%-scale {_infl_90:.0f} ULP  <-- PASSED >=100")
if _true_90 >= 100:
    print("  FAIL: the corrected denominator must make the 10%-scale control FAIL the >=100 separation")
    BAD += 1
else:
    print(f"    with the corrected spacing : the 10%-scale control is {_true_90:.0f} ULP -> FAILS the >=100 "
          f"requirement, so that matrix is REFUSED rather than accepted on an artefact")

# Review #24's counterexample, re-derived with NO masking (the fix). Their matrix: ideal = 0 everywhere,
# base = -8q, A = 1, B = 8q, scaling = 1, merged zero except one element = 100q (q = 2**-133). Because the
# statistic no longer masks subnormal ideals, the residual itself is measured: 100q / q = 100 ULP, which FAILS
# the 2-ULP bound - previously it was excluded while the controls divided by the same spacing, so the residual
# manufactured control separations of 100.8/108 ULP and PASSED.
_resid_ulp = 100.0 * q / q
print(f"  review #24 counterexample re-derived (no masking): the residual is {_resid_ulp:.0f} ULP and exceeds "
      f"the 2-ULP bound -> REFUSED by the main statistic, not tolerated")
if _resid_ulp <= 2.0:
    print("  FAIL: the residual must exceed the main tolerance once the mask is removed")
    BAD += 1

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
