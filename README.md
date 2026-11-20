# Reaper — flow-first programming language

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper is an expression-oriented language built around readable syntax and explicit data flow.** Its `::` operator passes a value into the next operation. The repository contains a Python reference interpreter, a developing native C17 core, and Reaper Studio for Windows.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Language example

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Studio preview

<p align="center"><img src="assets/reaper-terminal-preview.svg" alt="Illustrative Reaper command-line session preview" width="100%"></p>
<sub>Expected output rendered from committed examples, not a live terminal or desktop screenshot. A captured Reaper Studio session is not yet committed.</sub>

## Implemented capabilities

- **Reference runtime:** Python 3.10+, lexer, parser, tree-walking interpreter, CLI, REPL and standard-library tests.
- **Language core:** Unicode identifiers, functions/closures, recursion, immutable `make`, mutable `vary` with explicit `change`, conditionals, iteration and flow composition.
- **Collections and metrics:** map/filter/fold/reduce, sorting, slicing, flattening, UTF-8 helpers, vector norms/distances, projections, quadratic forms and geometry.
- **Modules and resources:** `.rpr` imports/exports, dependency graphs, cycle diagnostics, managed-resource ledger, LIFO regions, bounded file handles and deterministic cleanup.
- **Execution and audit:** selectable Python bytecode VM, execution quotas, JSON output, profiling and hash-chained audit logs.
- **Reaper Studio:** Windows editor for open/save/check/run, breakpoints, step/continue/stop, variable inspection and call stack.
- **Embedded C and interop:** project scaffolding, MCU profile inspection, memory budgets and opt-in C ABI access to trusted libraries, including Pytyliki ABI v1.
- **Additional systems:** local-first Polyglot; 666 reserved lexemes; 66 language/toolchain entries; 14 architecture profiles; MOST 20×20 matrix with 400 specified projections and an implemented integrity validator (not 400 executable compiler features).
- **МОСТ:** exact Russian keyword aliases over REAPER 0.1. The Python reference executes a limited subset through the existing parser/runtime; the C17 lexer exposes canonical REAPER spellings. No separate parser, AST, type system, morphology engine or runtime is introduced.

The native C17 track has a lexer, expression parser, owned AST, checked integer IR operations, limited lowering, optimizer tests and CLI bring-up. It is **not a complete interpreter**. The self-hosting lexer/parser is a staged bootstrap, not a replacement for the Python frontend.

## Run the reference interpreter

Requirements: Python 3.10+. No third-party runtime dependencies.

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m unittest discover -s tests -v
```

Install the CLI with `python -m pip install -e .`. Run Reaper Studio on Windows with `python reaper_desktop.py`.

## Build the native C17 core

Requirements: CMake and a C17-capable compiler.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
```

## Evolution and boundaries

Started 17 Nov 2026 with lexer, parser, interpreter and CLI. Main added modules, quotas, VM, Studio debugger, Polyglot, Embedded C, partial C17/self-hosting tracks and the validated MOST 20×20 architecture matrix.

The managed heap is accounting over Python's allocator, not a physical allocator or process-RSS cap. Native FFI is opt-in and executes loaded code in-process; use trusted ABI-compatible libraries only. Toolchain discovery checks `PATH` and does not install compilers. Python remains the compatibility reference until native parity is demonstrated.

## Documentation and downloads

[UI/UX architecture](docs/UI_UX_ARCHITECTURE.md) · [Language](LANGUAGE.md) · [Runtime platform](docs/RUNTIME_PLATFORM.md) · [Self-hosting plan](docs/SELF_HOSTING_BOOTSTRAP.md) · [Token catalogue](docs/TOKEN_CATALOG.md) · [Embedded C](docs/EMBEDDED_C_WORKBENCH.md) · [MOST matrix](docs/MOST_400_COMBINATORIAL_MATRIX.md) · [Engineering standard](docs/UNIFIED_ENGINEERING_STANDARD.md) · [МОСТ aliases](docs/MOST_LANGUAGE_SPEC.md) · [66 Russian readability rules](docs/MOST_RUSSIAN_66_RULES.md)

[Windows releases](https://github.com/Ivan-VHS/Reaper/releases) · [Desktop build workflow](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## License

[Apache License 2.0](LICENSE)