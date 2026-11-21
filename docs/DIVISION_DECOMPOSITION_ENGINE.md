# Division and decomposition engine

| API | Contract |
|---|---|
| `euclidean_divmod(a,b)` | exact quotient/remainder; zero divisor rejected |
| `divide_fraction(a,b)` | exact rational division |
| `split_evenly(total,parts)` | conserves signed integer total |
| `distribute_weighted(total,weights)` | largest-remainder allocation |
| `decompose_sequence/recombine` | ordered, lossless partition |
| `factor_pairs(n)` | positive factor pairs |

Deterministic, side-effect-free and bounded. Does not create threads or modify project state.
