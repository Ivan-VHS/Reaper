# Reaper — systems programming language and hardware development studio

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<p align="center"><img src="assets/readme/dashboard.svg" alt="Reaper project overview" width="100%"></p>

[Source](https://github.com/Ivan-VHS/Reaper) · [Python CI](.github/workflows/ci.yml) · [Windows Studio build](.github/workflows/desktop-build.yml) · [Node.js compatibility](.github/workflows/noo-tah.yml) · [Docs index](docs/README.md) · [Apache-2.0](LICENSE)

## Live Studio capture

<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Real Windows desktop capture of Reaper" width="100%"></a></p>
<p align="center"><sub>1920×1080 · Click the image to open the original PNG.</sub></p>

Genuine capture of the running Reaper Studio window on Windows, created by the repository's README screenshot workflow. The banner and flow diagram are original SVG illustrations, not screenshots.

### Architecture at a glance

<p align="center"><img src="assets/readme/workflow.svg" alt="Reaper implemented data flow" width="100%"></p>

Implemented path: `.rpr` source → lexer and parser → Python reference runtime → CLI, Studio, LSP and DAP.


[![Python CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=Python%20CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml)  [![Live Studio capture](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/readme-screenshots.yml?branch=main&label=Live%20Studio%20capture)](https://github.com/Ivan-VHS/Reaper/actions/workflows/readme-screenshots.yml)  [![License](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)


> **Scope:** Reaper is evolving into a low-level systems language and hardware development workbench while preserving the existing .rpr language and Python compatibility runtime. It is a local developer tool and Windows desktop IDE, not a hosted web service. Documentation was checked against the feature branch on **2026-11-23**.

## Purpose and implementation status

Reaper is being reoriented around systems programming: firmware, embedded software, platform components and hardware-adjacent development. Its expression-oriented `::` composition remains available, as do the Python reference runtime, CLI/REPL, Windows Studio, stdio LSP/DAP and optional NOO TAH integration.

**Available today:** a limited native scalar AOT path through C17, a partial C17 lexer/parser/IR core, a QCS hardware-description validation frontend, MCU profile/linker tooling, and a new checked MMIO descriptor API that dispatches only through a supplied host adapter.

**Still under development:** full native type/ownership/effect checking, a general machine-code/object backend, source-level hardware constructs, real OS-backed MMIO/IRQ/DMA services, and the complete hardware-focused Studio workspace. See [Hardware Language](docs/HARDWARE_LANGUAGE.md) for the staged migration and exact boundaries.

The intended audience is embedded and firmware developers, systems programmers, platform/driver engineers, compiler developers and educators.

### What is implemented

| Component | Current scope | Boundary |
|---|---|---|
| Python runtime | lexer, parser, interpreter, CLI, REPL, modules, closures, quotas and audit log | current executable reference |\n| Static type analysis | inferred primitive/list types, operator/index checks, mutability and call-arity diagnostics | partial; opt-in via `reaper typecheck` |
| Reaper Studio | Windows IDE foundation, project tree/editor/debugger, plus systems/hardware overview with MCU profiles and capability boundaries | local desktop application; no live device inspector |
| LSP | stdio JSON-RPC, diagnostics, completion, hover, symbols, lexical navigation, semantic tokens and document formatting | per-open-document; lexical highlighting, not cross-file type inference |
| Toolchain inventory | discovers compilers, builders, parsers, formatters, debuggers and WASM runtimes; pins binary hashes | PATH and SHA-256 only; discovered tools are never executed by inventory |
| DAP | stdio debug adapter, line breakpoints, stepping, stack and locals | statement-boundary debugging; trusted local programs only |
| NOO TAH | project/process management around the official Node.js runtime, npm/npx and Inspector | Node/V8/libuv are supplied by upstream Node |
| Native C17 + MMIO | lexer, expression parser, owned AST, checked i64 IR, limited lowering and checked MMIO adapter contract | experimental partial track; no physical mapping or Python-runtime parity |
| QCS / embedded tools | separate hardware-domain parser, JSON AST and bounded embedded helpers | reference/analysis tools, not hardware execution |
| Kora | optional standard-library helpers in seven manifest-backed modules | separate from the Reaper language runtime |

Catalogues and registries may contain proposed or reserved entries. An item in a catalogue is not automatically an implemented runtime feature. The capability pages record maturity and boundaries: [Features](docs/FEATURES.md), [Polyglot capability layer](docs/POLYGLOT_CAPABILITY_LAYER.md), [REAPER IDE](docs/REAPER_IDE.md), [NOO TAH](docs/NOO_TAH.md) and [Kora helpers](docs/KORA.md).

The image below is a capture of the Windows Studio application, not a browser-based playground.


## Related OS product: DuckOS

The seven-app **Mora** suite (Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify) is specified in the separate [DuckOS project](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/PREINSTALLED_APPLICATIONS.md). It is an operating-system application layer, not a component of Reaper. This repository does not claim to ship those applications or provide their OS services. Its own capabilities and interfaces remain independently defined by this repository's source, tests and versioned contracts.

## Quick Start

### Requirements

- Python **3.10 or newer**. CI currently tests Python 3.10, 3.11 and 3.12.
- Tkinter for the Studio GUI (normally included with standard Python distributions; some minimal Linux Python packages split it out).
- Git.
- CMake **3.16+** and a C17 compiler only if you want to build the partial native track.
- Node.js is optional for NOO TAH. The compatibility workflow tests Node.js **22 and 24**; it is not required to run Reaper `.rpr` programs.

The Python package declares `setuptools>=68` as its build-system requirement and has no third-party runtime dependency list in `pyproject.toml`.

### Install the Python reference runtime

```sh
python -m venv .venv
# Activate the environment:
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux / macOS:       source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

### Run a program and open Studio

```sh
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
python -m reaper --repl
python reaper_desktop.py
```

After editable installation, the equivalent entry points include `reaper`, `reaper-studio` and `reaper-toolchain`.

Inspect local tool availability without launching any of the discovered tools:

```sh
reaper-toolchain --output toolchain-inventory.json
```

Studio also advertises LSP `textDocument/formatting`; formatting normalizes indentation and whitespace without rewriting program tokens.

### Run the test suite

```sh
python -m compileall -q reaper tests
python -m unittest discover -s tests -v
```

The first install may retrieve the declared build backend from the package index; subsequent program execution is local. There is no application HTTP port, browser URL, database seed step or separate mock server.

### Optional native C17 track

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

This builds the current native compiler subset and its tests. It does not replace the Python runtime or establish full language parity.

### Optional NOO TAH / Node.js checks

Install Node.js from the official distribution and make `node` available on `PATH`, then run:

```sh
reaper-noo-tah version
reaper-noo-tah doctor
reaper-noo-tah check app.mjs
reaper-noo-tah run app.mjs
reaper-noo-tah npm run build
```

These commands operate on the selected local Node project. If the project starts its own HTTP server, its port is controlled by that project; Reaper itself does not expose a web preview URL.

## Reproducible workflows, examples and data

The checked-in examples are local source programs, not responses from a live API:

- `examples/flow.rpr` is the basic language smoke example.
- `examples/device_audit.rpr` demonstrates a read-only audit path and produces a versioned JSON report when run.
- `tests/` contains parser, runtime, language-service, debugger, registry and integration tests.
- The NOO TAH conformance suite tests Node built-ins, ESM/CommonJS, streams, workers, child processes and loopback HTTP/TCP. It does not rely on a public test service.

Try the core scenarios:

1. **Syntax only:** `python -m reaper --check examples/flow.rpr`; expect diagnostics or a successful parse without program execution.
2. **Run the example:** `python -m reaper examples/flow.rpr`; inspect the emitted result.
3. **Alternative execution engine:** `python -m reaper --engine vm examples/flow.rpr`; compare with the default tree-walk engine.
4. **Interactive prompt:** `python -m reaper --repl`; exit the prompt to end that in-memory session.
5. **LSP service:** `python -m reaper lsp`; it reads framed JSON-RPC from stdin and writes protocol messages to stdout.
6. **DAP service:** `python -m reaper dap`; use a trusted local program for launch and statement-boundary debugging.
7. **Node compatibility:** `node --test tests/noo_tah/conformance.test.mjs`; tests use local loopback networking and Node built-ins.

The CLI applies explicit resource limits: by default, one million execution steps, 100,000 collection items, one million characters of text, a 64 MiB managed heap and 64 simultaneously open managed files. The values can be changed through documented CLI options. A limit is an interpreter guardrail, not an OS-level sandbox.

Runtime state lives in the process and in files the operator chooses. An optional `--audit-log PATH` appends a local hash-chained execution journal; `--verify-audit-log PATH` checks it. Closing the process ends the active memory session but does not delete source files or journals. There is no browser localStorage, sessionStorage, IndexedDB or cookie state.

## Configuration, environment and trust

There is no root `.env.example`, Docker Compose web stack, hosted account system, demo login, CORS policy or application HTTPS setup. The Python runtime works without Node.js. NOO TAH has three documented environment overrides:

| Variable | Purpose | Default / behavior |
|---|---|---|
| `NOO_TAH_NODE` | path to the Node executable | otherwise discover `node` on `PATH` |
| `NOO_TAH_NPM_CLI` | explicit path to `npm-cli.js` | otherwise probe known paths beside the selected Node installation |
| `NOO_TAH_NPX_CLI` | explicit path to `npx-cli.js` | otherwise probe known paths beside the selected Node installation |

These values are executable paths, not secrets. Do not place credentials in source control. Missing Node produces a clear `Node.js not found` error; a missing npm/npx CLI reports the relevant override.

Other meaningful switches:

- `--check` / `--lint` parses without running a program.
- `--engine treewalk|vm` selects the runtime engine.
- `--allow-native-ffi` explicitly permits native C ABI loading; only use a library you trust.
- `--steps`, `--items`, `--text-length`, `--heap-bytes` and `--open-resources` set resource limits.

The language interpreter is not an OS sandbox. DAP launches trusted local files; enabling FFI permits native code; and npm package installation/lifecycle scripts execute third-party code with the permissions of the current user. Do not run unknown programs or packages merely because they appear in a demo.

LSP and DAP use Content-Length framed JSON-RPC over standard input/output, not a hosted HTTP API. Node Inspector can expose a local debugging endpoint when explicitly requested; that endpoint belongs to the selected Node process, not to a public Reaper web stand.

## Studio interaction and keyboard shortcuts

The Windows Studio editor uses the canonical language service for local source navigation:

| Shortcut / action | Behavior |
|---|---|
| `Ctrl+Space` | local completion for Reaper keywords, built-ins and current-document symbols |
| `F12` | navigate to a declaration in the current document |
| Find references | locate lexical identifier occurrences in the current document |
| `Ctrl+Shift+R` | rename lexical occurrences in the current document after confirmation |
| `Ctrl+K` | open the command palette |
| `Ctrl+Alt+K` | open the CODEX-66 capability browser |

These are document-local operations, not cross-file semantic refactoring. Conditional breakpoints, evaluate, step-out, complete type inference and a cloud AI assistant are not advertised as implemented.

## Architecture and repository map

```text
Reaper source (.rpr)
  -> Python lexer / parser / runtime
  -> CLI, REPL or Studio
  -> optional LSP / DAP stdio services

JavaScript project
  -> NOO TAH process manager
  -> official Node.js (V8, libuv, npm, Inspector)

Native C17 track
  -> lexer / parser / AST / IR / limited lowering
```

| Path | Contents |
|---|---|
| `reaper/` | Python reference runtime, CLI, Studio, language/debug services and NOO TAH |
| `reaper/kora/` | Kora standard-library helpers |
| `src/`, `include/` | partial native C17 track |
| `tests/` | Python, protocol, runtime and native tests |
| `examples/` | local `.rpr` sample programs |
| `docs/` | language, IDE, architecture and feature-boundary documentation |
| `editors/` | editor support and protocol notes |
| `.github/workflows/` | CI, native/desktop build and Node compatibility |

The project is not split into a deployed frontend, backend and mock API. Browser compatibility, browser storage, public ports, CORS and HTTPS are not applicable to the Reaper runtime itself.

## CI, desktop artifacts and rollback

- [Reaper CI](.github/workflows/ci.yml) runs Python 3.10/3.11/3.12 tests and validates examples and contracts.
- [NOO TAH compatibility](.github/workflows/noo-tah.yml) tests Node 22 and 24 across Windows, Linux and macOS.
- The native C17 track is built and tested separately.
- [Desktop build](.github/workflows/desktop-build.yml) packages the Windows Studio app as `Reaper-Studio-windows-x64.zip`. A tag matching `v*` triggers release publication.

Workflow artifacts are downloadable build outputs, not a live hosted IDE. To roll back a distributed desktop build, use the previous tagged GitHub Release. There is no running web service to roll back. Build logs and test diagnostics are in GitHub Actions.

## Troubleshooting

| Symptom | Check |
|---|---|
| `python -m reaper` is not found | activate the virtual environment or run from the repository root |
| Studio fails to open | check that the Python installation includes Tkinter |
| Node is not found | install Node.js or set `NOO_TAH_NODE` to the executable path |
| npm/npx cannot be found | set `NOO_TAH_NPM_CLI` or `NOO_TAH_NPX_CLI` to the matching CLI JavaScript file |
| A Node project build fails | run `reaper-noo-tah doctor`, then inspect the Node/npm output; lifecycle scripts may execute third-party code |
| Native C tests fail | verify CMake 3.16+, a C17 compiler and the complete CTest output |
| LSP/DAP output looks malformed | keep stdout reserved for protocol frames; send application logs to stderr |

## Known limitations, contribution and license

Python remains the executable compatibility reference. Native C17 parsing/lowering is partial. LSP symbol lookup, references and rename are lexical and document-local; DAP stepping is statement-granular; the IDE is not an OS sandbox. NOO TAH delegates JavaScript behavior to the official Node distribution rather than reimplementing V8.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the repository's contribution workflow and validation requirements. Propose changes through [GitHub Issues](https://github.com/Ivan-VHS/Reaper/issues) or a Pull Request. Include a reproducible `.rpr` example, Python/Node/compiler versions and the exact command/output. Run Python tests and, when touching the native track, CMake/CTest.

License: [Apache-2.0](LICENSE).

## Mapping to the 66 README rules

The web-stand rules are reflected according to the actual local developer-tooling product:

| Rules | README coverage |
|---|---|
| 1–11 · purpose and boundaries | explains language/IDE purpose, audience, executable vs partial tracks, local-only scope and absence of hosted demo |
| 12–22 · quick start | exact Python install, CLI, Studio, tests, native C17 and optional Node commands |
| 23–33 · configuration and access | documents the three actual NOO TAH path overrides, CLI flags and trust boundaries; no fake credentials or `.env` |
| 34–44 · data and behavior | local examples, test scenarios, execution quotas, audit-log lifetime, loopback-only conformance tests and debug limitations |
| 45–55 · architecture and build | maps packages, native sources, examples, tests, services and CI outputs |
| 56–66 · operations and support | links build/release workflows, explains artifact rollback, diagnostics, known limitations, contribution route and license |

**There is no public Reaper web-playground URL.** Studio screenshots and downloadable Windows artifacts are not a live web stand.

## Unified report envelope

Wrap JSON output in the shared ivan-vhs.report.v1 contract with: python tools/report_envelope.py --tool reaper --version VERSION < result.json. See docs/REPORT_ENVELOPE.md and schemas/ivan-vhs.report.v1.schema.json. The envelope preserves the tool-specific result and records limitations.


## Documentation map

Use the [documentation index](docs/README.md) as the entry point and the [information architecture map](docs/INFORMATION_ARCHITECTURE.md) for language, compiler, runtime, Studio and integration clusters. Topic hubs lead to detailed contracts; implementation status remains governed by source, tests and schemas.
