# Automatic multiply and compute operations

Reaper implements the requested operation set as bounded arithmetic and sequence
built-ins in `reaper/arithmetic.py`, registered by the language interpreter.
They are available directly in `.rpr` programs.

| Requested capability | Reaper operation |
|---|---|
| Multiply / Product | `multiply(a, b)`, `product(values)` |
| Compute / Calculate | `compute(a, b, operation)`, `calculate(a, b, operation)` |
| Scale / Amplify | `scale_values(values, factor)`, `amplify(value, factor)` |
| Compound | `compound(left, right)` (element-wise product) |
| Expand | `expand(values, repetitions)` |
| Accumulate / Iterate | `accumulate(values)`, `iterate(seed, steps, function)` |
| Cross-multiply | `cross_multiply(left, right)` (outer product) |
| Exponentiate / Factor | `exponentiate(base, power)`, `factorize(integer)` |
| Combine / Fuse | `combine(left, right)`, `fuse(left, right)` |
| Aggregate | `aggregate(values)` (count, sum, product, mean, min, max) |
| Pair / Couple | `pair(a, b)`, `couple(left, right)` |
| Convolve | `convolve(signal, kernel)` |
| Cartesianize | `cartesianize(left, right)` |

Sequence operations enforce the interpreter collection limit. Numeric operations
reject booleans, non-finite values, invalid domains and results exceeding the
runtime's bounded integer size. `iterate` counts each callback against the
interpreter's normal execution budget and returns the seed plus every step.
