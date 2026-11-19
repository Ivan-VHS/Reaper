# Division & Decomposition Engine

The module `reaper.decomposition` provides exact, deterministic arithmetic and
ordered data decomposition as a separately importable library API.

## Public operations

- `euclidean_divmod(a, b)`: immutable result satisfying `a = q*b + r` and
  `0 <= r < abs(b)`; zero divisors are rejected.
- `divide_fraction(a, b)`: exact rational division using `fractions.Fraction`.
- `split_evenly(total, parts)`: conserves signed integer totals and assigns
  indivisible units to earlier buckets.
- `distribute_weighted(total, weights)`: largest-remainder allocation with
  exact rational comparisons and stable index tie-breaking.
- `decompose_sequence(items, chunk_size)` / `recombine(parts)`: ordered,
  lossless partitioning and reconstruction.
- `factor_pairs(n)`: positive factor-pair enumeration.

## Correctness and safety contract

All functions are deterministic and side-effect-free. They validate input
types and bounds, reject zero divisors and invalid weights, preserve element
order, and conserve integer totals. Floating weights are converted from their
decimal string representation before allocation. No function starts threads,
writes files, executes code, changes a project, or accesses the host.

## Auto-improvement integration

These primitives are suitable for future workload sharding, resource quotas,
dependency grouping, and compiler/runtime decomposition. An optimizer must
measure candidate plans, compare against a baseline, retain a rollback path,
and require explicit approval before applying changes outside an isolated
workspace. A proposed split is not an automatically verified speedup.
