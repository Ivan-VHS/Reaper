# Native Reaper runtime and selfhood/autonomy model

## Runtime direction

Reaper is being moved toward an implementation that can execute its own language core without starting Python. The native C17 path is a real compiler/runtime slice:

`source → lexer → Pratt expression parser → owned AST → checked IR lowering → fixed-point optimizer → checked i64 execution`.

The native command is built by CMake and has no Python startup or interpreter dependency:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
./build/reaper-c --eval "1 + 2 * 3"
./build/reaper-c --run examples/native_expression.rpr
ctest --test-dir build --output-on-failure
```

The current native execution contract is deliberately bounded:

- Integer literals, parentheses, unary `+` and `-`, and binary `+`, `-`, `*`, `/` are executable.
- Arithmetic is signed 64-bit integer arithmetic. Overflow and division by zero fail explicitly; output values are not changed on failure.
- Identifiers, calls, collection values, declarations, control flow, floating-point execution and external effects are not part of this native slice yet.
- The lexer and parser can recognize a wider syntax than the native lowering/execution path. Recognition is not a claim of executable semantics.

## Stable C ABI v1

`include/reaper/ffi.h` defines the versioned interface exposed by `reaper_ffi`:

- `reaper_abi_version()`
- `reaper_v1_eval_i64(source, source_length, output, error, error_capacity)`
- `reaper_v1_selfhood_count(count)`
- `reaper_v1_selfhood_lookup(identity, ordinal)`

Calls are synchronous. The engine does not retain caller pointers. Source is capped at 1 MiB, must not contain embedded NUL bytes, and must represent one expression supported by the native slice. Loading a shared library executes native code: consumers must use an explicit, trusted library path and check the ABI version before calling it.

The API uses stable status codes and does not grant filesystem, network, process, hardware or plugin permissions. Reaper expression evaluation is not an OS sandbox.

## Python's remaining role and self-hosting boundary

Python remains the compatibility reference for the complete language, IDE services, debugger, extended runtime and tooling. The C17 engine is now independently executable for the documented integer-expression slice, but it is not yet a replacement for the full Python runtime.

The Reaper-written lexer and Pratt parser in `selfhost/` remain bootstrap components. Their current conformance harness still runs through the Python reference runtime. A full self-hosting claim requires the Reaper compiler to parse, compile and reproducibly rebuild the required Reaper compiler sources without Python. That acceptance gate remains open.

The transition rule is therefore:

1. Implement semantics in the versioned native core where parity and safety can be proven.
2. Keep Python as a compatibility oracle for language features not yet supported natively.
3. Differential-test native and reference behavior before promoting a feature.
4. Remove a Python dependency only after a native implementation and clean-checkout acceptance tests exist.

## Selfhood and autonomy vocabulary

The canonical data file is `language/selfhood.v1.json`, validated by `schemas/selfhood-autonomy.v1.schema.json`. The native immutable lookup table is exposed through `include/reaper/selfhood.h` and the C ABI.

Each record is an ordered semantic mapping:

`identity → transformation → autonomy outcome`.

The 20 records preserve the supplied Russian wording. Exact lookup is intentional: this catalogue is a stable vocabulary, not a fuzzy synonym engine, and a matching word does not authorize a source or system mutation.

Inspect it with:

```sh
./build/reaper-c --selfhood
./build/reaper-c --selfhood-token "Сам"
```

The C test suite verifies order, uniqueness, exact wording and the 20-entry count.

## Federation adapters

Reaper is the shared expression engine, not a reason to replace each repository's specialist implementation:

- Pytyliki may link the Reaper C ABI when `REAPER_SOURCE_DIR` points to a sibling Reaper checkout. Its existing C11 compute/DSP implementation remains the host.
- OPlague can load a caller-selected Reaper ABI library through an explicit-path Python bridge. Its Python product logic and existing Pytyliki bridge remain independent.
- VentuSample may link the same ABI from its C++20 DSP/plugin host. Audio rendering, Qt and real-time DSP stay in C++; Reaper is an optional deterministic control-expression engine.

No repository downloads or loads a native library implicitly. The default builds remain usable without a sibling Reaper checkout.
