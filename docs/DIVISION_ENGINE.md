# Division and Partitioning Engine

## Scope

The division subsystem gives the Python reference runtime and native C support
library a consistent, checked foundation for arithmetic division, exactness,
balanced splitting, and proportional allocation. It is deterministic and
bounded by the interpreter's collection quota or the native partition limit.

## Arithmetic contract

- The / operator remains real-number division.
- The // and % operators retain their existing language semantics for backward
  compatibility.
- divmod_euclidean(a, b) and its alias euclidean_divmod(a, b) return [q, r]
  such that a = q*b + r and 0 <= r < abs(b).
- quotient(a, b), remainder(a, b), and is_divisible(a, b) expose the
  corresponding result and exactness test.
- A zero divisor, boolean operand, or non-integer operand is rejected with a
  runtime diagnostic. The native signed-i64 API also rejects INT64_MIN / -1
  rather than invoking signed-overflow undefined behavior.

## Collection and allocation operations

- partition(values, count) and split(values, count) create count contiguous
  groups. Group sizes differ by at most one; earlier groups receive any
  remainder. Text input produces text chunks, other sequence input produces
  list chunks.
- distribute(total, count) splits a signed integer total into near-equal
  integer shares while preserving the exact sum.
- proportional_split(total, weights) uses the largest-remainder method.
  Integer weights are non-negative, at least one must be positive, ties are
  resolved by input order, and the returned allocations sum exactly to total.

All Python collection outputs obey max_collection_items. Native partition
planning validates non-zero counts and has a fixed upper bound.

## Native C support

The include/reaper/division.h header exposes checked Euclidean division,
divisibility, balanced range planning, and a worker-count recommendation based
on available workers and a minimum work grain. The recommendation is advisory;
it does not set CPU affinity, spawn threads, or mutate machine state.

The native C17 compiler track is not yet a complete language interpreter.
These helpers are reusable native primitives, not a claim that all Python
built-ins are already callable from native Reaper programs.

## Automatic improvement loop

A caller can compare several minimum-grain settings, benchmark the resulting
workloads, and select the best measured plan. Reaper does not rewrite source
code or silently change runtime behavior: recommendations remain explicit and
testable. Any future optimizer integration must preserve the identity
dividend = quotient * divisor + remainder, deterministic allocation, and
resource quotas.

## Validation

The Python tests cover sign combinations, zero division, balanced splitting,
negative totals, exact proportional allocation, and collection limits.
The native C tests cover Euclidean signed division, overflow rejection,
contiguous partition ranges, empty ranges, and bounded worker recommendations.
