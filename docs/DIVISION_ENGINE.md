# Division and partitioning

The Python runtime and C17 support library expose deterministic, checked arithmetic and bounded allocation.

## Numeric operations

| Built-in | Contract |
|---|---|
| `divmod_euclidean(a,b)` / `euclidean_divmod` | `a=q*b+r`, `0≤r<|b|` |
| `quotient(a,b)` | Euclidean quotient |
| `remainder(a,b)` | non-negative Euclidean remainder |
| `is_divisible(a,b)` | exact divisibility check |

`/`, `//` and `%` retain existing language semantics. Zero divisors, booleans and non-integers are rejected; native `INT64_MIN / -1` is checked for overflow.

## Collection allocation

| Built-in | Contract |
|---|---|
| `partition(values,count)` / `split` | contiguous groups; size delta ≤1 |
| `distribute(total,count)` | signed integer shares; sum preserved |
| `proportional_split(total,weights)` | largest remainder; stable tie order |

Weights must be non-negative with at least one positive value. Outputs obey collection quotas. Native range/worker planning is advisory: it does not spawn threads or set CPU affinity.

**Invariant:** `dividend = quotient × divisor + remainder`. Tests cover sign combinations, zero division, overflow, balanced splits, allocation sums and bounds.
