# Reaper punctuation operator system — 666 IDs

**Status:** canonical registry and lexical recognition are implemented. Five anchor operators have executable semantics in the Python reference runtime. The rest are reserved, not simulated.

## Alphabet and maximal-munch rule

The only glyph atoms in this family are `:`, `;`, `=` and `+`.

| Glyph | Base role |
|---|---|
| `:` | Declaration, access, type and binding |
| `;` | Statement boundary, sequence separator and step |
| `=` | Definition, comparison and contract |
| `+` | Increment, accumulation and forward composition |

A contiguous run is one token (maximal munch). Runs longer than five characters fail lexing. The 48 anchor forms and 618 generated forms are registered. Three historical spellings, `:=`, `==`, and `++`, remain compatibility aliases and are not separate IDs.

## Canonical pipeline

`::` is the single canonical data-flow operator and replaces the former `|>` spelling. It passes the left operand as the first argument to the operation on the right:

```reaper
craft double(value) {
    yield value * 2
}
make result ::= [1, 2, 3] :: map(double)
emit result
```

Namespace/member access is not overloaded onto `::`; that syntax remains a separate language-design decision.

## Deterministic ID layout

The registry has exactly 666 unique entries:

- 001–120: Memory, buffers, arenas and slices
- 121–240: Pipelines, control flow and synchronization
- 241–360: Bindings, contracts and types
- 361–480: Arithmetic, accumulation and shifts
- 481–580: Vectors, metrics and geometry
- 581–666: System hooks, diagnostics, tracing and metadata

IDs 001–048 are the named anchor table below. For ID `N >= 049`, encode `N - 49` as exactly five base-4 digits with digit alphabet `:`, `;`, `=`, `+` (in that order). Thus ID 049 is `:::::`; ID 666 encodes 617. Every code round-trips to one ID.

## Anchor table

| ID | Glyph | Name | State |
|---:|---|---|---|
| 001 | `;;:` | memory_commit | reserved |
| 002 | `::;` | buffer_view | reserved |
| 003 | `::=` | strict_define | implemented |
| 004 | `:++` | prefix_increment | implemented |
| 005 | `::` | pipeline | implemented |
| 006 | `:;` | expression_boundary | reserved |
| 007 | `=::` | contract_equal | implemented |
| 008 | `++:` | sequence_concat | implemented |
| 009 | `:;:` | debug_checkpoint | reserved |
| 010 | `;::` | aligned_buffer | reserved |
| 011 | `:::` | metric_context | reserved |
| 012 | `;;;` | frame_terminate | reserved |
| 013 | `:=:` | atomic_exchange | reserved |
| 014 | `:+:` | stride_step | reserved |
| 015 | `;+:` | capacity_reserve | reserved |
| 016 | `:+;` | buffer_clear | reserved |
| 017 | `=:=` | strict_identity | reserved |
| 018 | `:==` | compatible_rebind | reserved |
| 019 | `==:` | closure_capture | reserved |
| 020 | `++;` | stream_advance | reserved |
| 021 | `;++;` | batch_advance | reserved |
| 022 | `::+` | vector_projection | reserved |
| 023 | `+::` | vector_norm | reserved |
| 024 | `:;;` | metric_distance | reserved |
| 025 | `;:;` | sequence_filter | reserved |
| 026 | `;;=` | snapshot_freeze | reserved |
| 027 | `=;;` | snapshot_rollback | reserved |
| 028 | `:+=` | accumulate_assign | reserved |
| 029 | `++=` | structure_merge | reserved |
| 030 | `;=:` | destructure | reserved |
| 031 | `:=;` | binding_close | reserved |
| 032 | `::;;` | frame_open | reserved |
| 033 | `;;::` | frame_close | reserved |
| 034 | `:+++` | multi_advance | reserved |
| 035 | `+++:` | multi_concat | reserved |
| 036 | `;::;` | stream_partition | reserved |
| 037 | `::;:` | graph_node | reserved |
| 038 | `:;::` | graph_edge | reserved |
| 039 | `=::=` | structural_equivalence | reserved |
| 040 | `:==:` | epsilon_tolerance | reserved |
| 041 | `;;+:` | conditional_break | reserved |
| 042 | `+:;;` | bounded_repeat | reserved |
| 043 | `::=+` | metric_energy | reserved |
| 044 | `;=;` | orthogonality_test | reserved |
| 045 | `:==+` | approximate_compare | reserved |
| 046 | `;;=;` | critical_stop | reserved |
| 047 | `:;=:` | guard_check | reserved |
| 048 | `::=;` | buffer_checksum | reserved |

The initial sketch contained examples with `.`, `~`, `^`, `!`, `?` and `#`. Those characters are outside the chosen alphabet, so affected forms have been normalized to unique sequences made only from the four permitted glyphs. IDs and semantic intent retain their positions.

## Executable anchor semantics

| Operator | Runtime rule |
|---|---|
| `::=` (003) | Strict declaration/change introducer. Historical `:=` remains accepted. |
| `:++` (004) | Prefix increment of a mutable numeric name. Rejects immutable names, nonnumeric values and non-name operands. Returns the incremented value. |
| `::` (005) | Pipeline composition; `values :: map(f)` means `map(values, f)`. |
| `=::` (007) | Type-strict structural equality using Reaper's recursive equality semantics. |
| `++:` (008) | Concatenates two lists into a new list, enforcing the interpreter's collection limit. |

The prior `==` equality and `++` text-concatenation operators keep their original meanings. A single semicolon is a statement separator; multi-character semicolon sequences are separate registered operators.

All other anchor and generated forms are reserved. The lexer recognizes their IDs; the Python parser reports the reserved ID rather than guessing behavior. A registered ID is not evidence of an implemented operation.

## CLI

```sh
python -m reaper --operators
python -m reaper --operators-json
```

The Python registry is the reference catalogue. Native C17 exposes a matching lookup and ID/glyph round-trip API and validates glyph runs in its lexer. C17 parsing/runtime remains a partial implementation track; no C runtime parity is claimed.

## Compatibility and acceptance gate

Replace pipeline expressions `items |> map(transform)` with `items :: map(transform)`. New declarations may use `::=`; existing `:=` remains valid. `|>` is rejected.

A reserved operator becomes executable only after grammar position, precedence, operand/result types, evaluation order, errors, quotas, Python implementation, native frontend behavior and conformance tests are specified.
