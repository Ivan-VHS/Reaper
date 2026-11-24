
<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="Reaper systems language and developer studio" width="880"></picture></p>
<h1 align="center">Reaper — Systems Programming Language and Developer Studio</h1>
<p align="center"><strong>A flow-first language with a Python reference runtime, CLI, Windows Studio, stdio LSP/DAP services and a separately evolving native C17 track.</strong></p>
<p align="center"><a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="Python CI" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=Python%20CI"></a> <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml"><img alt="Windows Studio" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/desktop-build.yml?branch=main&style=flat-square&label=Windows%20Studio"></a> <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square"></a></p>

[Quick start](#quick-start) · [Revival](#documentation-revival) · [Visuals](#visual-overview) · [Architecture](#architecture) · [Docs](docs/README.md)

> **Implementation boundary:** the Python runtime is the executable compatibility reference. The native C17 lexer/parser/IR/lowering path is partial, not a complete compiler or general machine-code backend. Studio is Windows-only. LSP/DAP are local stdio services, not hosted APIs.

## Quick start

**Requirements:** Python 3.10+, Git. Tkinter is required for the Studio GUI. CMake 3.16+ and a C17 compiler are only needed for the partial native track. Node.js is optional for NOO TAH.

~~~sh
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

Open the Windows Studio with:

~~~sh
python reaper_desktop.py
~~~

Run the test suite:

~~~sh
python -m unittest discover -s tests -v
~~~

## Documentation revival

| Before | Revival documentation |
|---|---|
| Single static banner | Matching light/dark SVG hero with fallback alt text |
| Runtime and native compiler maturity easy to conflate | Explicit Python reference vs partial native C17 boundary |
| UI screenshot and data-flow drawing mixed together | Real Windows Studio capture plus a separately labelled workflow illustration |
| Broad feature descriptions | Concrete service, platform and language-service limits |
| Long navigation | Topic hubs, information map and publishing standard |

This is a documentation refresh, **not a new Reaper language version or release**. Verify feature maturity in source, tests and [FEATURES.md](docs/FEATURES.md).

## Current implementation

| Component | Available behavior | Boundary |
|---|---|---|
| Python reference runtime | Lexer, parser, interpreter, scopes, values, quotas and CLI/REPL | Compatibility reference |
| Static analysis | Conservative AST/type diagnostics in check, Studio and LSP | Static-only; does not execute source |
| Studio | Windows editor/debugger, command palette and MCU profile views | No live device inspector |
| LSP | stdio, UTF-16 positions, local diagnostics, completion, hover and symbols | Document-local; no cross-file type inference |
| DAP | Launch, line breakpoints, statement-boundary stepping, stack and locals | Documented runtime subset |
| Native C17 | Lexer, expression parser, owned AST, checked i64 IR and limited lowering | Partial; not full language parity |
| QCS / hardware contracts | Syntax validation and checked MMIO descriptor API | No physical mapping or complete device runtime |
| NOO TAH | Optional integration with official Node.js | Node.js is not required for .rpr execution |

## Visual overview

<table><tr><td width="50%"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Captured Reaper Studio window running on Windows" width="100%"></a><p><sub><strong>Real Studio capture</strong> — Windows desktop, 1920×1080.</sub></p></td><td width="50%"><img src="assets/readme/workflow.svg" alt="Reaper source, parser, Python runtime and developer services workflow" width="100%"><p><sub><strong>Architecture illustration</strong> — the implemented source-to-tooling path, not a UI screenshot.</sub></p></td></tr></table>

## Architecture

~~~mermaid
flowchart LR
  A[.rpr source] --> B[Lexer and parser]
  B --> C[AST and source spans]
  C --> D[Python reference runtime]
  D --> E[CLI / REPL]
  D --> F[Windows Studio]
  D --> G[stdio LSP / DAP]
  C -. partial track .-> H[Native C17 IR and limited lowering]
  I[Optional Node.js] --> J[NOO TAH adapter]
~~~

The native C17 path is deliberately shown as a separate partial branch. It is not treated as equivalent to the Python reference runtime.

## Configuration and trust

There is no hosted web service, account system or root .env contract. NOO TAH accepts these optional path overrides:

| Variable | Purpose |
|---|---|
| NOO_TAH_NODE | Explicit Node executable path |
| NOO_TAH_NPM_CLI | Explicit npm-cli.js path |
| NOO_TAH_NPX_CLI | Explicit npx-cli.js path |

Useful runtime switches include --check / --lint, --engine treewalk|vm, --allow-native-ffi and bounded resource options such as --steps, --items, --text-length, --heap-bytes and --open-resources. FFI is disabled unless explicitly allowed. The interpreter is not an OS sandbox; only run trusted programs and libraries.

## Repository map

| Path | Responsibility |
|---|---|
| reaper/ | Python language frontend, runtime and command services |
| native/ / src/ | Partial C17 implementation and native contracts |
| examples/ | Runnable .rpr programs |
| tests/ | Runtime, parser, diagnostics and integration tests |
| editors/vscode/ | Syntax-only VS Code support |
| docs/ | Language, compiler, runtime, IDE and hardware contracts |
| assets/readme/ | Theme-aware hero and workflow illustration |
| .github/workflows/ | Python CI, Windows Studio build and integrations |

## Verification and roadmap

~~~sh
python -m unittest discover -s tests -v
python -m reaper --check examples/flow.rpr
git diff --check
~~~

When changing the native track, also configure and run the repository's CMake/CTest targets. Read [Architecture](docs/ARCHITECTURE.md), [Features](docs/FEATURES.md), [Hardware Language](docs/HARDWARE_LANGUAGE.md), [IDE contract](docs/REAPER_IDE.md) and the [information architecture map](docs/INFORMATION_ARCHITECTURE.md) for current maturity and next milestones.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [README Visual Standard](docs/README_VISUAL_STANDARD.md) and [SECURITY.md](SECURITY.md). Changes to grammar, diagnostics, runtime quotas, LSP/DAP or native contracts should include focused regression tests.

## License

[Apache-2.0](LICENSE).
