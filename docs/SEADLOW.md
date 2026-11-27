# Seadlow — bit-parallel execution

**Status:** Experimental native C17 foundation. This page describes implemented scope, not infinite speed or completed hardware acceleration.

Seadlow is Reaper's bit-oriented execution subsystem. Its objective is to increase useful bit throughput by processing machine-word batches, reducing per-bit control overhead, bounding working sets and making tail bits explicit.

## Implemented scope

### Language and IR surface

The native expression frontend accepts and lowers these operators:

| Reaper expression | Native IR operation | Semantics |
|---|---|---|
| `a & b` | `bit.and.i64` | bitwise AND |
| `a | b` | `bit.or.i64` | bitwise OR |
| `a ^ b` | `bit.xor.i64` | bitwise XOR |
| `~a` | `bit.not.i64` | bitwise NOT |
| `a << n` | `shift.left.i64` | logical bit-pattern shift left |
| `a >> n` | `shift.right.logical.i64` | logical right shift |

Bitwise operations work on the 64-bit representation carried by the existing `i64` value type. Shift counts must be in the range 0–63; invalid counts fail explicitly. Right shift is logical, not sign-extending. The constant folder uses unsigned bit patterns so signed-shift undefined behavior is avoided.

Precedence is ordered as logical operators, comparison operators, bitwise OR, XOR, AND, shifts, addition and multiplication. Parentheses remain available to make intent explicit.

### Bulk bitset API

`include/reaper/seadlow.h` exposes host-side operations over exactly `bit_count` bits:

- AND, OR, XOR and NOT transforms;
- portable 64-bit word processing in bounded 256-word tiles;
- unaligned buffers via `memcpy` loads/stores;
- exact in-place operation when output equals an input;
- rejection of partial output/input overlap;
- deterministic clearing of unused high bits in a final partial byte;
- popcount over the requested bit range;
- fused transform-plus-popcount, which computes the population count while writing each transformed word/byte instead of rereading the completed output;
- counters for processed bits, words, tail bytes/bits and tiles.

The API does not spawn worker threads or assume SIMD support. The fixed-size word loop gives optimizing compilers a simple vectorization target while retaining a portable C17 implementation. Actual SIMD, multicore scheduling and device offload require target-specific implementations and benchmark evidence.

## Algebraic model and fused reduction

For a bit-vector \(x \in \mathbb{B}^n\), where \(\mathbb{B}=\{0,1\}\), define the
wordwise transform \(z=T_\circ(x,y)\). Its population count is

\[
\operatorname{wt}(z)=\sum_{i=0}^{n-1}z_i
=\lVert z\rVert_1,
\qquad
d_H(x,y)=\operatorname{wt}(x\oplus y).
\]

For NOT, the finite-width complement is taken only over the declared domain:
\[
\operatorname{wt}(\neg_n x)=n-\operatorname{wt}(x).
\]
Unused high bits in the final byte are therefore excluded from both the output
and the reduction.

The new function reaper_seadlow_transform_popcount fuses the map and reduction:
\[
(c,z)\leftarrow(c+\operatorname{wt}(T_\circ(x_j,y_j)),
               T_\circ(x_j,y_j))
\]
for each 64-bit word \(j\), followed by the exact byte/bit tail. The count is
published only after the operation succeeds. Its result is identical to
\[
z\leftarrow T_\circ(x,y);
\qquad c\leftarrow\operatorname{popcount}(z),
\]
but avoids the second full read of the transformed buffer. Both paths remain
\(O(\lceil n/64\rceil)\) in word operations; the fused path reduces memory
traffic rather than changing the asymptotic complexity. No speedup percentage
is claimed without a reproducible benchmark on named hardware.

The test suite exhaustively checks all 8-bit operand pairs for AND/OR/XOR,
checks finite-width complement and Hamming-weight identities, compares fused
results against the two-pass reference at byte, word and 256-word tile
boundaries, and verifies that invalid requests do not commit the count output.

## Example

```reaper
((85 & 255) ^ 15) << 1
```

Build the `reaper-c` target and run:

```sh
reaper-c --eval-i64 examples/seadlow_bits.rpr
```

Expected output: `180`.

## Current boundary

The native expression parser, verified IR, constant folder and evaluator in this change cover scalar bitwise expressions. The bulk transform and popcount functions are exported by the native C17 core. Reaper does not yet expose those bulk functions as callable `.rpr` standard-library functions: that requires a stable native-call/FFI lowering contract, ownership rules for slices, and cross-runtime conformance tests. This host API must not be described as an already callable source-level builtin.

Seadlow does not change memory permissions, access physical addresses, install drivers, create threads or offload work to a GPU. Hardware-aware scheduling, explicit SIMD backends, parallel worker pools, and language-level slice/stream integration remain future work.

## Acceptance evidence

The native Seadlow test target covers source-to-IR evaluation, unary and binary bitwise operations, shift bounds, multi-tile transforms, non-byte-aligned tails, popcount, unaligned buffers, exact in-place writes, partial-overlap rejection and zero-length behavior. CI results are the release evidence; no speedup ratio is claimed without a reproducible benchmark suite on named hardware.
