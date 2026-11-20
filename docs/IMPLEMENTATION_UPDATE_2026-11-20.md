# Reaper implementation update — 20 November 2026

This note records the executable additions made to the Python reference runtime and CLI. It does not imply that the developing C17 implementation has reached interpreter parity.

## Language and collection standard library

The existing `craft`, lexical closure, and `::` semantics remain unchanged. The reference runtime now provides:

- `filter(values, predicate)` as the readable alias of `keep`, and `reduce(values, initial, function)` as the alias of `fold`.
- Stable `sorted(values[, key_function][, "asc"|"desc"])` and `sort_by(values, key_function[, "asc"|"desc"])`.
- `chunk`, `take`, `drop`, one-level `flatten`, `reverse`, and stable `unique`.
- UTF-8-aware string operations: `split`, `join`, `trim`, `lower`, `upper`, `replace`, `contains`, `starts_with`, and `ends_with`.

All collection-producing operations continue to observe the interpreter's configured collection limit. `join` and `replace` enforce the configured text-length limit. Invalid directions, widths, counts, empty split separators, incompatible values, and callback failures surface as Reaper runtime diagnostics.

## Metric standard library

`vector_norm(values[, kind])` supports `l1`, `l2` (default), and `linf`. New operations are `vector_normalize` (`normalize_vector` alias), `manhattan_distance`, `chebyshev_distance`, `squared_euclidean_distance`, `cosine_similarity`, `angle_between`, `vector_projection`, and `vector_centroid`.

Vector dimensions, finite real-number inputs, overflow, dimension mismatch, and undefined zero-vector cases are validated. Normalizing a zero vector, projecting onto a zero vector, or asking for cosine similarity with a zero vector is an explicit error.

## CLI

- `--lint` is an alias for `--check`.
- `--repl` starts a persistent line-oriented REPL. Each submitted line must be a complete Reaper program; multiline editing remains a `.rpr`/Studio workflow.
- `--json` emits structured success and error records, buffering program output so stdout remains one JSON document.
- `--profile` reports elapsed wall time and interpreter step count. With `--json`, profile metrics are included in the result object.

Examples:

~~~sh
reaper --lint examples/flow.rpr
reaper --repl
reaper --profile examples/flow.rpr
reaper --json --profile examples/flow.rpr
~~~

## Runtime platform additions

The Python reference runtime now includes .rpr imports/exports, dependency graph scanning and cycle detection; a tracked heap with nested-container accounting, mark/sweep roots and explicit LIFO regions; owned file handles and automatic cleanup; opt-in generic C ABI calls and a typed adapter for Pytyliki's pl_* core API; Canonical IR lowering, bytecode assembly and a selectable stack VM; and Reaper Studio statement breakpoints, stepping, variable inspection and call stack display.

The precise contracts and limits are in [RUNTIME_PLATFORM.md](RUNTIME_PLATFORM.md). These capabilities currently belong to the Python reference runtime. The heap is an accounting/collection layer over Python's allocator, native FFI executes in-process, and ctypes cannot promise portable physical library unloading. The C17 implementation remains a separate bring-up and is not claimed to have full runtime/VM parity.

## Regression coverage

`tests/test_extended_runtime.py` covers the new collection/string APIs, limits, CLI JSON diagnostics, profiling, and persistent REPL state. Vector algorithms remain in the metric-space regression suite. The full unit suite and native C17/CTest suite are the release gates.
