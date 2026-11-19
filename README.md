# Reaper — a flow-first programming language

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**Reaper is an expression-oriented language built around readable syntax and explicit data flow.** Its `~>` operator passes a value into the next operation. The repository currently contains a Python reference interpreter and a developing native C17 implementation.

## Example

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers ~> map(double) ~> sum()
emit "answer = " ++ text(answer)
```

## Implemented today

- **Python reference runtime:** Python 3.10+, tree-walking interpreter, lexer, parser, runtime, CLI and standard-library tests.
- **Language core:** Unicode identifiers, comments, strings, functions and closures, recursion, immutable `make`, mutable `vary` with explicit `change`, conditionals, iteration and flow composition.
- **Built-ins and diagnostics:** collection transforms, checked algebraic operations, vector/matrix helpers, sampled-data calculus, source-aware diagnostics and bounded combinatorial expansion.
- **Native C17 track:** lexer, expression parser and owned AST, verified integer Canonical IR, checked constant folding, a limited AST-to-IR lowering slice, CLI bring-up and C tests.
- **MOST language track:** documented language vocabulary and staged implementation contract.

The C implementation is not yet a full language interpreter. Full declarations/blocks, type checking, intent resolution, ownership analysis, native code generation and WASM are not complete. Python remains the compatibility reference until runtime and CLI parity is demonstrated.

## Screenshots

This is currently a language/runtime project, not a graphical application. No verified screenshot from a live terminal session is checked into the repository; illustrative terminal artwork has been removed rather than presented as a real capture. Use the runnable examples below to inspect actual output.

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

## Design and safety boundaries

Programs are tokenized, parsed into an AST and evaluated by a bounded interpreter. Console effects are explicit through operations such as `emit`, `say` and `ask`. Ordinary expressions do not silently gain filesystem, network, clock, process, shell or hardware access.

Default runtime quotas include 1,000,000 execution steps, 256 nested calls, 100,000 collection items and 1,000,000 characters from text concatenation. These are resource guardrails, **not a security sandbox**. Do not treat execution of untrusted programs as isolated from the host.

## Documentation

- [Language reference](LANGUAGE.md)
- [Unified REAPER/MOST architecture](docs/REAPER_UNIFIED_ARCHITECTURE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [MOST language specification](docs/MOST_LANGUAGE_SPEC.md)
- [C migration plan](docs/C_MIGRATION.md)
- [Examples](examples/) · [Tests](tests/) · [20-triad algebraic operator matrix](docs/ALGEBRAIC_OPERATOR_MATRIX.md) · [20-triad algebraic operator matrix](docs/ALGEBRAIC_OPERATOR_MATRIX.md)

## CI and license

GitHub Actions tests Python 3.10, 3.11 and 3.12, runs the unit suite, checks an example and executes the flow example. The native C core has its own CMake/CTest coverage.

[Apache License 2.0](LICENSE).

> 千里之行，始于足下。 — A journey of a thousand miles begins with a single step.
