# Reaper — Systems Language & Workbench

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Native C17](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/native-c.yml?branch=main&label=Native%20C17)](https://github.com/Ivan-VHS/Reaper/actions/workflows/native-c.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)

> **Flow-first syntax. Explicit contracts. Diagnostics that retain source context.**

**Project record:** Alpha · Python reference runtime available · native C17 compiler track partial · Python package 0.1.0 · CMake track 0.2.0 · Apache-2.0 · **Documentation reviewed:** 2026-11-27 UTC

<p align="center"><img src="assets/reaper-hero.svg" alt="Reaper systems language and workbench overview" width="100%"></p>
<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Reaper Studio screenshot" width="100%"></a></p>

## Purpose and scope

Reaper is a systems-programming language and local development workbench. Its current implementation has two distinct compiler/runtime tracks: the Python reference runtime and an experimental native C17 implementation. The native track is not yet feature-equivalent to the reference runtime. Windows Studio, LSP/DAP services and external adapters are separate tooling surfaces.

## Language example

The `.rpr` language uses flow-first expressions and the `::` operator to pass the left-hand value as the first argument:

~~~reaper
craft double(value) {
    yield value * 2
}

make values := [1, 2, 3]
make result := values :: map(double) :: sum()
emit "result = " ++ text(result)
~~~

Run a checked-in example with the reference runtime after installation:

~~~sh
python -m venv .venv
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

## What is implemented

- **Reference language runtime:** lexer, parser, AST interpreter, CLI/REPL, structured diagnostics and bounded execution.
- **Canonical IR and VM:** selectable Python bytecode VM over Canonical IR; tree-walk execution remains the compatibility default.
- **Modules:** versioned `.rpr` imports/exports, isolated scopes, cached exports, dependency graph checks and cycle diagnostics.
- **Static analysis:** conservative type inference for supported AST constructs. Unknown module/host boundary values remain `Any`; this is not a complete sound type system.
- **Resource accounting:** heap/open-file quotas, execution bounds and deterministic cleanup. These are runtime guardrails, not a security sandbox for hostile programs.
- **Native C17 track:** a partial lexer/parser, owned AST, checked IR, optimizer and limited lowering. The scalar AOT subset emits C17 for a host GCC/Clang-compatible toolchain; it does not provide reference-runtime parity.
- **Architecture registry:** 66 stable architecture concepts across nine layers, with exact lookup and bounded dependency-graph validation.
- **Developer tools:** Windows Studio foundation, stdio LSP/DAP services, Kora helpers and optional NOO TAH integration. NOO TAH delegates JavaScript execution to the official Node.js runtime.
- **Product composition:** 18 in-process product services are exposed by the reference runtime. Jora catalogue packs and framework descriptions are not automatically installable applications.

The embedded workbench creates and inspects reference MCU projects and can invoke user-installed toolchains. It does not include built-in firmware flashing or live hardware debugging. MMIO descriptors are validated through a host-supplied bus; they do not map physical memory.

## Build and test

Requirements: Python 3.10+ for the reference runtime; CMake 3.16+ and a C17 compiler for the native track; Node.js 22/24 for optional compatibility checks; Tkinter for the Windows Studio GUI.

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

The CMake test suite runs native C tests and, when a Python interpreter is found, additional reference-runtime and repository validation tests.

Launch the REPL or installed Studio entry point:

~~~sh
python -m reaper --repl
reaper-studio
~~~

## Integrations and trust boundaries

- OPlague device snapshots are imported as versioned JSON and compared offline.
- Pytyliki C ABI calls require an explicit opt-in and a caller-selected trusted, ABI-compatible library.
- VentuSample pack exchange is manifest-based; Reaper reads declared metadata and does not alter WAV assets.
- The OCTA-8 federation records peer contracts; it does not create a central runtime or grant privileges.

Filesystem, process, network, clock, shell and native-library effects must remain explicit or opt-in. Native FFI executes in-process code and must only load trusted libraries.

## Documentation

- [Features](docs/FEATURES.md) · [Architecture](docs/ARCHITECTURE.md)
- [Native compiler](docs/NATIVE_COMPILER.md) · [Hardware language](docs/HARDWARE_LANGUAGE.md)
- [Runtime limits](docs/RUNTIME_PLATFORM.md) · [Kora helpers](docs/KORA.md)
- [Studio and IDE](docs/REAPER_IDE.md) · [Jora factory](docs/JORA_APPLICATION_FACTORY.md)
- [Implementation roadmap](docs/IMPLEMENTATION_ROADMAP.md) · [Documentation index](docs/README.md)
- [NOO TAH JavaScript boundary](docs/NOO_TAH.md)
- [Shared ecosystem standards](https://github.com/Ivan-VHS/DAK/blob/main/docs/SHARED_STANDARDS.md)

## Contributing and license

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing language semantics, compiler stages or public contracts. Keep changes reviewable and add deterministic tests. Security reports belong under [SECURITY.md](SECURITY.md).

Licensed under [Apache-2.0](LICENSE). External project names and trademarks remain with their respective owners.

---
<p align="center"><sub>Reaper · README review 2026-11-27 UTC</sub></p>
