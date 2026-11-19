# Algebraic and structural operator matrix

## Purpose

This module makes the supplied 20-triad algebraic model usable in ordinary Reaper
programs. It is not an audio feature pack. The same operations can be used for
numeric computation, collection processing, vectors, matrices, sampled data,
text sequences, and deterministic program pipelines.

The source document mixes formal operators with semantic contrasts and growth
metaphors. Reaper therefore implements the mathematically defined operations and
gives each extension an explicit executable contract; terms such as "antonym",
"opposition", or "proliferation" are not treated as machine instructions by
themselves.

## Implemented language operations

| Triad | Reaper API | Executable meaning |
|---|---|---|
| 1. Addition / multiplication | `+`, `sum(values)`, `multiply(a, b)` | Additive aggregation and scalar multiplication |
| 2. Subtraction / replication | `-`, `opposite(value)`, `replicate(value, count)` | Additive inverse and bounded copying |
| 3. Multiplication / growth | `multiply(a, b)`, `scale(vector, factor)` | Scalar product and vector scaling |
| 4. Division / ratio | `/`, `divide(a, b)` | Checked division with zero rejection |
| 5. Powers | `**`, `power(base, exponent)` | Real-valued exponentiation |
| 6. Roots / branching | `root(value, degree)`, `proliferate(choices)` | Real roots and bounded Cartesian expansion |
| 7. Logarithms | `logarithm(value, base)` | Logarithm with explicit domain checks |
| 8. Exponential growth | `exponential(value, base)` | Exponential mapping with overflow rejection |
| 9. Differentiation | `differentiate(samples, step)` | Forward finite differences over ordered samples |
| 10. Integration | `integrate(samples, step)` | Cumulative trapezoidal integration |
| 11. Reversal / accumulation | `reverse(values)`, `accumulate(values, initial)` | Reverse order and prefix sums |
| 12. Branching | `branch(value, functions)` | Apply each supplied Reaper function to one value |
| 13. Quantization | `quantize(value, step)` | Round to a positive grid interval (ties to even) |
| 14. Normalization | `normalize(values, mode)`, `distance(a, b)` | Min-max or Euclidean unit normalization; vector distance |
| 15. Factorization | `factorize(integer)` | Prime factors of a positive integer with a work ceiling |
| 16. Decomposition | `flatten(value)`, `transpose(matrix)`, `matrix_multiply(a, b)` | Nested-list flattening and bounded matrix operations |
| 17. Reduction / increments | `fold(values, initial, fn)`, `differences(values)` | General reduction and adjacent finite differences |
| 18. Simplification / deduplication | `unique(values)` | Stable scalar deduplication without coercing types |
| 19. Transformation / composition | `transform(values, fn)`, `~>` | Function application and left-to-right flow composition |
| 20. Proliferation | `cartesian(a, b)`, `proliferate(choices)` | Controlled combinatorial expansion |

## Contracts and limits

- All numeric helpers reject booleans and non-finite floating-point inputs.
- Numeric results must remain finite and real; invalid roots, logarithms,
  division by zero, and overflow become source-aware Reaper runtime errors.
- `differentiate` returns adjacent forward differences divided by the sample
  interval. It is a discrete approximation, not symbolic differentiation.
- `integrate` returns cumulative trapezoidal areas, starting at zero. It is
  numerical integration, not an exact symbolic antiderivative.
- `normalize(values)` uses min-max scaling by default. The optional `"unit"`
  mode uses the Euclidean norm. Constant and zero vectors map to zero vectors.
- `factorize` has a deterministic trial-division work ceiling; it rejects
  inputs that exceed the budget instead of running without bound.
- Matrix multiplication checks output size and the estimated number of scalar
  multiply-accumulate operations before doing the work.
- Replication, flattening, transposition, branching, Cartesian products, and
  general proliferation respect the interpreter's collection-item limit.
- Branching accepts only Reaper `craft` functions or registered pure built-ins.
  It does not create processes, threads, network calls, or background tasks.

These operations do not grant filesystem, network, clock, process, shell,
hardware, audio-device, or plugin access. Such host effects remain explicit,
capability-gated future work.

## Example

```reaper
craft plus_one(value) {
    yield value + 1
}
craft square(value) {
    yield value * value
}

make samples := [1, 2, 3, 4]
emit samples ~> differentiate()
emit samples ~> integrate(0.5)
emit normalize([10, 20, 30])
emit 4 ~> branch([plus_one, square])
emit proliferate([[1, 2], ["left", "right"]])
```

## Status

This document describes the implemented Python reference-runtime slice. The
native C17 runtime must not claim parity until equivalent operations, validation,
resource accounting, and conformance tests are implemented in C and pass CI.
