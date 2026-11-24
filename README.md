# Reaper

Reaper is a systems-programming language and local development workbench for engineers exploring embedded software, compiler tooling, hardware-adjacent programs and a flow-oriented source language.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg">
  <img src="assets/readme/dashboard-light.svg" alt="Reaper overview: source language, compiler front end, reference runtime and developer tools" width="100%">
</picture>

[![Python CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=Python%20CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Last commit](https://img.shields.io/github/last-commit/Ivan-VHS/Reaper?style=flat-square)](https://github.com/Ivan-VHS/Reaper/commits/main) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square)](LICENSE)

[Quick Start](#quick-start) · [Screenshots](#screenshots) · [Architecture](#architecture) · [Roadmap](#roadmap) · [Docs](docs/README.md) · [Commits](https://github.com/Ivan-VHS/Reaper/commits/main)

> **Status:** Active development. The Python reference runtime, CLI/REPL, Windows Studio foundation, stdio LSP/DAP services and a partial native C17 track are present. Native compiler parity and privileged hardware services are not complete.
>
> **Platforms:** Python runtime tests cover Python 3.10–3.12. The optional Node.js compatibility workflow tests Node 22/24 on Windows, Linux and macOS. Windows Studio requires Tkinter. Native C17 requires CMake 3.16+ and a C17 compiler.


### Jora application factory

[DuckOS Jora](https://github.com/Ivan-VHS/DuckOS) is being integrated as the Jora platform and application store. Each generated application receives its own independent product name; application names must not contain Jora. It composes capability packs such as Text Editor + Audio Editor + Translator into a separately named application such as Sonaris, then generates a Reaper project scaffold and EN/RU/UK/MOST interface dictionaries. Name suggestions are derived from application capabilities and never reuse the platform brand. Graph variants can optimize for balance, latency, modularity, extensibility or minimum complexity, and are exported as JSON plus Mermaid diagrams. See [Jora application factory](docs/JORA_APPLICATION_FACTORY.md). Current packs are specifications rather than functioning editors; the generated project is statically checked but is not installable. Reaper is the only integrated source generator in this increment; additional compiler targets remain pending.

## Quick Start

Create an environment and install the Python reference runtime:

~~~sh
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

Open the Studio or interactive prompt:

~~~sh
python reaper_desktop.py
python -m reaper --repl
~~~

Run the Python test suite:

~~~sh
python -m compileall -q reaper tests
python -m unittest discover -s tests -v
~~~

## What Reaper provides

| Component | Current behavior | Boundary |
|---|---|---|
| Python reference runtime | Lexer, parser, interpreter, modules, closures, resource quotas and audit log | Current executable language reference |
| Static checking | Primitive/list type inference, operator/index, mutability and call-arity diagnostics | Partial type system |
| Reaper Studio | Windows IDE foundation with project tree, editor, debugger and systems overview | Local GUI; hardware panels are not live device control |
| Language Server Protocol (LSP) | Stdio JSON-RPC diagnostics, completion, hover, symbols, lexical navigation and formatting | Per-open-document; no cross-file semantic inference |
| Debug Adapter Protocol (DAP) | Stdio debugging with line breakpoints, stepping, stack and locals | Statement-boundary subset |
| NOO TAH | Process integration with the official Node.js runtime, npm/npx and Inspector | Delegates JavaScript execution to upstream Node |
| Native C17 track | Lexer/parser, AST, checked i64 IR and limited lowering | Experimental partial track; not full language parity |
| QCS and embedded helpers | Hardware-description parsing, AST/diagnostics and bounded reference tools | Analysis/reference only; no physical hardware access |

A catalogue entry or reserved capability name is not automatically an implemented runtime feature. Current maturity and limits are documented in [Features](docs/FEATURES.md), [Hardware Language](docs/HARDWARE_LANGUAGE.md), [Reaper IDE](docs/REAPER_IDE.md), [NOO TAH](docs/NOO_TAH.md) and [Kora](docs/KORA.md).

## Why Reaper

- The `.rpr` reference runtime is executable today; the native compiler track is explicitly separated as partial.
- CLI, Studio, language services and tests share a single language implementation.
- Resource quotas and optional hash-chained audit logs make execution limits inspectable.
- Hardware-facing concepts are expressed as checked contracts and adapters, not claims of privileged device access.
- NOO TAH integrates upstream Node rather than pretending to reimplement V8 or libuv.

## Screenshots

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/workflow-dark.svg">
  <img src="assets/readme/workflow.svg" alt="Reaper workflow from .rpr source through lexer and parser into the reference runtime and developer tools" width="100%">
</picture>

<p align="center">
  <a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Real Windows capture of the Reaper Studio desktop application" width="100%"></a>
</p>
<sub>1920×1080 Windows Studio capture generated by the repository screenshot workflow. The SVG above is an architecture illustration.</sub>

## Architecture

~~~mermaid
flowchart LR
    A[.rpr source] --> B[Lexer and parser]
    B --> C[Python reference runtime]
    C --> D[CLI and REPL]
    C --> E[Studio]
    C --> F[LSP and DAP]
    G[Native C17 subset] -. separate partial track .-> B
    H[JavaScript project] --> I[NOO TAH]
    I --> J[Official Node.js]
~~~

| Path | Responsibility |
|---|---|
| `reaper/` | Python runtime, CLI, Studio, language/debug services and NOO TAH |
| `reaper/kora/` | Kora standard-library helpers |
| `src/`, `include/` | Partial native C17 implementation |
| `tests/`, `examples/` | Runtime/protocol tests and local `.rpr` programs |
| `docs/`, `editors/` | Language, IDE, architecture and editor support |
| `.github/workflows/` | CI, native/desktop build, screenshot and Node compatibility |

## Build matrix

| Target | Requirements | Status |
|---|---|---|
| Python reference runtime | Python 3.10+ | Executable reference; CI tests 3.10/3.11/3.12 |
| Windows Studio | Python with Tkinter | Desktop workflow target |
| Native C17 subset | CMake 3.16+, C17 compiler | Partial; separate test target |
| NOO TAH | Node.js 22 or 24 in current CI matrix | Optional integration; not needed for `.rpr` |
| macOS | Python path / Node compatibility job | Not a claim of native Reaper Studio support |

## Revival highlights

- The entry page distinguishes the executable Python reference from the partial native compiler.
- Build, check, run and test commands appear before deeper architecture.
- The real Windows Studio capture is separate from editable diagrams.
- The documentation states the exact scope of LSP, DAP, hardware adapters and Node integration.

| Legacy reading path | Revival reading path |
|---|---|
| Broad language promise | Capability and maturity table |
| Native compiler status easy to misread | Reference and partial tracks separated |
| Long setup discovery | Copy-ready commands near the top |
| General IDE claims | Document-local language-service boundaries |

## Roadmap

- [x] Python reference runtime, CLI/REPL and local examples.
- [x] Stdio LSP/DAP service foundations and Windows Studio foundation.
- [x] Partial native C17 lexer/parser/IR and test targets.
- [ ] Extend native type/ownership/effect analysis and code generation with matching tests.
- [ ] Add OS-backed MMIO/IRQ/DMA only through reviewed platform adapters and target-specific verification.

## Ecosystem

- [DuckOS](https://github.com/Ivan-VHS/DuckOS) — operating-system project and Mora desktop workspace.
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) — processor inspection and bounded systems utilities.
- [OPlague](https://github.com/Ivan-VHS/OPlague) — device and driver evidence workbench.
- [VentuSample](https://github.com/Ivan-VHS/VentuSample) — procedural sample generation and offline DSP.

See the [documentation index](docs/README.md), [architecture](docs/ARCHITECTURE.md), [contribution guide](CONTRIBUTING.md) and [VS Code syntax-support note](editors/vscode/README.md). License: [Apache-2.0](LICENSE).
