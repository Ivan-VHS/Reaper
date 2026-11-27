# Reaper

Reaper is a systems-programming language and local development workbench for compiler tooling, embedded software and hardware-adjacent programs.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg"><img src="assets/readme/dashboard-light.svg" alt="Reaper language and developer tools" width="100%"></picture>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square)](LICENSE)

**Status:** the Python reference runtime, CLI/REPL, Windows Studio foundation, stdio LSP/DAP services and a partial native C17 track are present. Native compiler parity and privileged hardware services are not complete.

## HARVEST creative-research framework pack

HARVEST adds sixteen versioned Reaper capability modules for voice-feature profiles, creative cycles, chronology, language metrics, conflict ledgers, cultural context, evidence tracking, audio annotations, rhyme/flow metrics, album structure, collaboration/influence graphs and composite research output. Each module publishes a diagnostic surface and a typed domain IR contract. Shared core modules provide contract validation, diagnostics, snapshot storage, transaction transitions and a synchronous dependency DAG. See [HARVEST Reaper integration](docs/HARVEST_REAPER_INTEGRATION.md) for the pack contract, storage limits, Jora integration and verification status. The source pack is bundled by Jora, but remains `authored_unverified` until Reaper runtime and CI evidence establish conformance.

## What is included

- Processor Engineering Platform v1: project/target manifests, Typed Registry checks, read-only Pytyliki CPU/ISA evidence and the current scalar-C17 host AOT workbench slice. Target-specific code generation and privileged processor operations are not claimed.
- Processor Fabric import v1: local-only Pytyliki evidence import with digest/generation/byte-span checks and a Reaper-verified typed SemanticGraph sidecar. This does not emit legacy stack VM bytecode or perform hardware effects.
- Processor backends v1: five independently tested bounded C17 prototypes — a structured RV32I encoder, flat-image linker, subset emulator, combinational SystemVerilog emitter and Boolean equivalence checker. They are not full target-qualified toolchains.
- Reaper source language, lexer/parser, reference runtime and diagnostics.
- CLI, REPL, Windows Studio foundation, LSP and DAP services.
- Experimental native C17 implementation; it is not yet feature-equivalent to the reference runtime.
- NOO TAH delegates JavaScript execution to the official Node.js runtime.
- Jora application scaffolding and capability composition; catalog packs remain specifications, not installable editors.

See [Processor Engineering Platform](docs/PROCESSOR_ENGINEERING_PLATFORM.md), [Features](docs/FEATURES.md), [Architecture](docs/ARCHITECTURE.md), [Hardware Language](docs/HARDWARE_LANGUAGE.md), [Jora factory](docs/JORA_APPLICATION_FACTORY.md), [Studio and IDE](docs/REAPER_IDE.md) and [NOO TAH](docs/NOO_TAH.md).

## Quick start

Requirements: Python 3.10–3.12 for the reference runtime; Node.js 22/24 for optional compatibility tests; Tkinter for Windows Studio; CMake 3.16+ and a C17 compiler for the native track.

```sh
python -m venv .venv
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
```

Open Studio or the REPL:

```sh
python reaper_desktop.py
python -m reaper --repl
```

Run reference-runtime tests:

```sh
python -m unittest discover -s tests -v
```

## Architecture and status

The .rpr reference runtime, partial native C17 work, developer tools and external runtime adapters are separate tracks. A catalogue entry or planned capability is not proof of implementation.

- [Implementation roadmap](docs/IMPLEMENTATION_ROADMAP.md)
- [Kora standard-library helpers](docs/KORA.md)
- [Documentation index](docs/README.md)
- [Shared ecosystem standards](https://github.com/Ivan-VHS/DAK/blob/main/docs/SHARED_STANDARDS.md)

[Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md) · [Apache-2.0](LICENSE)
