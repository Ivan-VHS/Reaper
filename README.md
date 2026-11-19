# Reaper — a flow-first programming language

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="Python and native CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Reaper 0.1" src="https://img.shields.io/badge/Reaper-0.1.0-2563EB?style=flat-square">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/runtime-Python%203.10%2B-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-111827?style=flat-square">
</p>

<p align="center"><img src="assets/reaper-hero.svg" alt="Reaper flow-first language" width="100%"></p>

Reaper is an independent, flow-first language with a readable syntax and a bounded interpreter. The current engineering tree also contains a portable compiler front end, opt-in host-runtime APIs and an experimental native C17 workstream. The interpreter remains the semantic reference.

**Read this in:** [English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

## Visual tour

<p align="center"><img src="assets/reaper-toolchain-preview.svg" alt="Source-aligned preview of the Reaper compiler front end and Quarry IR path" width="100%"></p>
<p align="center"><img src="assets/reaper-nine-systems.svg" alt="Reaper bounded host-runtime systems architecture" width="100%"></p>

<sub>These are source-aligned SVG previews and an architecture diagram, not screenshots captured from a live terminal session. Terminal text and example values in the preview are illustrative.</sub>

## Language and runtime

- **Flow-first syntax:** the established ~> operator composes transformations while preserving Reaper's existing grammar.
- **Interpreter:** lexer, parser, AST and bounded tree-walking execution remain the compatibility baseline.
- **Compiler front end:** conservative static diagnostics, deterministic source-mapped Quarry IR, structural verification and safe literal folding. The front end does not emit native machine code.
- **Host runtime APIs:** bounded resource regions, asynchronous channels and actors, scoped capabilities, checksummed application-state snapshots, in-process routing, profiling, capability-gated C ABI interop and health-policy observation.
- **Host target reporting:** the --target-info command reports host metadata, including E2K identification. It does not imply an MCST native backend.
- **Native C17 track:** portable compiler/runtime foundations and tests are maintained separately from the Python interpreter; full language parity is not claimed.

## Try the checked-in examples

Requirements: Python 3.10 or newer. The runtime uses the Python standard library.

    git clone https://github.com/Ivan-VHS/Reaper.git
    cd Reaper
    python -m reaper --check examples/flow.rpr
    python -m reaper examples/flow.rpr
    python -m reaper --target-info
    python -m reaper.compiler_cli examples/flow.rpr --optimize

## Build and verify

Run the Python suite:

    python -m compileall -q reaper tests
    python -m unittest discover -s tests -v

Build and test the native C17 targets:

    cmake -S . -B build -DBUILD_TESTING=ON
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

GitHub Actions validates Python 3.10, 3.11 and 3.12, runs the interpreter examples, exercises the compiler CLI and runtime architecture example, and tests the native C17 targets. A separate HMGA audit workflow checks the repository contract.

## Consolidated engineering updates

The integration branch curates compatible work from the open development history:

- **Compiler front end:** source-mapped Quarry IR, deterministic digests, conservative static checks, structural validation and safe constant folding.
- **Runtime foundations:** bounded resources, asynchronous channels/actors, scoped host capabilities, durable application-state snapshots, local routing, profiling, limited C ABI interop and health policy.
- **E2K profile:** host identification and explicit capability reporting only; native MCST code generation is not implemented.
- **MOST architecture:** staged system design mapped to the existing language and C17 migration without changing Reaper syntax.
- **HMGA v2/v3:** read-only repository audit and a deterministic 20-axiom / 400-operator native C17 catalogue with a finite 64-round planning limit.
- **Engineering gates:** signature-aware composition tests, cross-version Python checks, native C17 tests and a documented review/merge process.

Historical prototypes with overlapping actor, effect, resource, relay and health APIs were reviewed and deduplicated instead of being installed side-by-side. The current module-per-contract implementation remains the canonical host-runtime path. See the [integration audit](docs/INTEGRATION_AUDIT_2026-11-19.md) for the source-by-source record.

## Architecture and documentation

- [Language reference](LANGUAGE.md)
- [Platform architecture](docs/PLATFORM_ARCHITECTURE.md)
- [Nine-system runtime reference](docs/REAPER_SYSTEMS.md)
- [Cyclic runtime architecture](docs/REAPERS_ARCHITECTURE.md)
- [MOST systems architecture](docs/MOST_SYSTEMS_ARCHITECTURE.md)
- [Engineering standard](docs/ENGINEERING_STANDARD.md)
- [HMGA v2.0 contract](docs/HMGA_V2.0.md)
- [HMGA v3.0 operator matrix](docs/HMGA_V3.md)
- [E2K host profile](docs/ELBRUS_E2K.md)
- [Integration audit](docs/INTEGRATION_AUDIT_2026-11-19.md)

## Current boundaries

Reaper 0.1 remains an interpreter-first language. The compiler front end emits portable IR, not machine code. Host APIs are opt-in Python integrations and do not silently become language built-ins or an operating-system sandbox. Native code generation, JIT, distributed actors, network transport, cloud orchestration and full MCST E2K support are not claimed.

## License

Released under the [Apache License 2.0](LICENSE).
