# Reaper — a flow-first programming language

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**Reaper is an expression-oriented language built around readable syntax and explicit data flow.** Its `|>` operator passes a value into the next operation. The repository currently contains a Python reference interpreter and a developing native C17 implementation.

## Example

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers |> map(double) |> sum()
emit "answer = " ++ text(answer)
```

## 66-language systems capability matrix

Reaper exposes a capability catalogue covering memory ownership, linear resources, regions, compile-time programming, C ABI/FFI, concurrency, formal verification, embedded targets, SIMD and GPU/shader toolchains. The duplicate Clay and Nimrod/early-Nim source entries remain explicit aliases. Compiler discovery is separate from native backend implementation.

```bash
reaper --systems-languages
reaper --systems-languages --language-profile reaper
reaper --available-languages --language-profile reaper
reaper --systems-json
```

Toolchain checks are PATH-only: they do not run or install compilers. The matrix is included in Python package data and its tests are registered with CTest.

## Implemented today

- **Python reference runtime:** Python 3.10+, tree-walking interpreter, lexer, parser, runtime, CLI and standard-library tests.
- **Language core:** Unicode identifiers, comments, strings, functions and closures, recursion, immutable `make`, mutable `vary` with explicit `change`, conditionals, iteration and flow composition.
- **Built-ins and diagnostics:** collection operations, explicit conversions, orthogonal metric mathematics (n-D distance, dot products, quadratic forms, Parseval energy and non-Euclidean models), source-aware errors and configurable execution limits.
- **Native C17 track:** lexer, expression parser and owned AST, verified integer Canonical IR, checked constant folding, a limited AST-to-IR lowering slice, CLI bring-up and C tests.
- **MOST language track:** documented language vocabulary and staged implementation contract.

The C implementation is not yet a full language interpreter. Full declarations/blocks, type checking, intent resolution, ownership analysis, native code generation and WASM are not complete. Python remains the compatibility reference until runtime and CLI parity is demonstrated.

## Desktop workbench

Reaper Studio provides a native Windows desktop editor and execution window for the Python reference runtime. It is a practical source workbench, not a claim that the developing C17 runtime has reached feature parity.

## Run the Python interpreter

Requirements: Python 3.10 or newer. No third-party runtime dependencies.

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m unittest discover -s tests -v
```

Editable CLI installation:

```bash
python -m pip install -e .
reaper examples/hello.rpr
```

## Build the native C17 core

Requirements: CMake and a C17-capable compiler.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
./build/reaper-c --evolution-status
```

The native executable currently exposes the implemented bring-up and analysis paths; it is not a drop-in replacement for the Python interpreter.


## Native desktop application

**Reaper Studio** adds a Windows x64 desktop workbench on top of the existing Python reference runtime: edit `.rpr` files, open/save source, parse-check a program, run it, and inspect output/errors. The C17 implementation remains a separate developing core; the desktop app does not claim full C-runtime parity.

- [Windows x64 Releases](https://github.com/Ivan-VHS/Reaper/releases)
- [Desktop build workflow and CI artifacts](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)
- [Latest workflow runs](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml?query=branch%3Amain)

A successful workflow run uploads `Reaper-Studio-windows-x64.zip`; a `v*` tag publishes the same archive as a GitHub Release. Run from source with Python 3.10+ using `python reaper_desktop.py`.


## Design and safety boundaries

Programs are tokenized, parsed into an AST and evaluated by a bounded interpreter. Console effects are explicit through operations such as `emit`, `say` and `ask`. Ordinary expressions do not silently gain filesystem, network, clock, process, shell or hardware access.

Default runtime quotas include 1,000,000 execution steps, 256 nested calls, 100,000 collection items and 1,000,000 characters from text concatenation. These are resource guardrails, **not a security sandbox**. Do not treat execution of untrusted programs as isolated from the host.

## Documentation

- [Language reference](LANGUAGE.md)
- [Unified REAPER/MOST architecture](docs/REAPER_UNIFIED_ARCHITECTURE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Concatenation and composition architecture](docs/CONCATENATION_ARCHITECTURE.md)
- [Orthogonal metric engine](docs/ORTHOGONAL_METRIC_ENGINE.md)
- [MOST language specification](docs/MOST_LANGUAGE_SPEC.md)
- [C migration plan](docs/C_MIGRATION.md)
- [Examples](examples/) · [Tests](tests/)

## CI and license

GitHub Actions tests Python 3.10, 3.11 and 3.12, runs the unit suite, checks an example and executes the flow example. The native C core has its own CMake/CTest coverage.

[Apache License 2.0](LICENSE).

> 千里之行，始于足下。 — A journey of a thousand miles begins with a single step.


## Execution audit trail

The optional audit mode writes a local hash-chained journal of source fingerprints and run lifecycle events without copying program output. Enable it with --audit-log PATH and verify it with --verify-audit-log PATH. The chain detects record edits but is not a digital signature or remote attestation; see docs/EXECUTION_AUDIT.md.
