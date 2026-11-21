# Vertical Self-Product

REAPER interprets vertical self-multiplication as repeated self-composition of
an explicit transformation pipeline.

Let F be the ordered pipeline supplied by the caller. At each level the same
pipeline is applied twice to the previous result:

- level 1 produces F²(x);
- level 2 produces F⁴(x);
- level d produces F^(2^d)(x).

This is useful for compiler passes, canonicalization experiments and data-flow
transformations whose repeated application is meaningful. The function does
not guess which passes should be combined.

## Runtime contract

- API: vertical_self_product in reaper/self_product.py.
- Pipeline size: 1–64 callables; depth: 1–12.
- The order of transformations is the same as REAPER pipe(): left to right.
- The result includes each level, total pipeline applications and total
  function calls.
- Caller-supplied transformations should be deterministic and side-effect-free.
  The API executes them; it does not sandbox or roll back their side effects.
- Inputs are not copied. A transformation that mutates a mutable input remains
  responsible for that mutation.

## Verification

tests/test_self_product.py checks exact F²/F⁴ values, pipeline order, application
counts, and rejected bounds and invalid transformations.
