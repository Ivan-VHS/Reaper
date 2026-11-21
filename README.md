# Reaper — Flow-First Programming Language

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="reference runtime" src="https://img.shields.io/badge/reference%20runtime-Python%203.10%2B-0039A6?style=flat-square">
  <img alt="native track" src="https://img.shields.io/badge/native%20track-C17-0A1E46?style=flat-square">
  <img alt="license" src="https://img.shields.io/badge/license-Apache--2.0-D52B1E?style=flat-square">
</p>

**Reaper is an expression-oriented programming language built around readable syntax and explicit data flow.** Its :: operator passes a value into the next operation. The repository includes the Python compatibility runtime, a developing native C17 core, and Reaper Studio for Windows.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Language example

~~~reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
~~~

## Product components

| Component | Current role |
|---|---|
| Python reference runtime | Lexer, parser, interpreter, CLI, REPL, modules, closures, collections, quotas, optional bytecode VM, profiling and hash-chained audit. |
| Reaper Studio | Windows editor with check/run/debug, breakpoints, variables and call-stack inspection. |
| Native C17 track | Lexer, expression parser, owned AST, checked integer IR operations and limited lowering. It is not yet a complete interpreter; Python remains the compatibility reference. |
| МОСТ | Russian-first source surface with 54 exact keyword aliases; 21 are executable in the REAPER 0.1 reference subset and 33 are lexically reserved for future grammar work. |
| QCS 1.0 | Separate hardware-domain validation frontend. It does not replace .rpr or execute hardware operations. |
| THESIS assertion graph | Versioned claims, typed evidence references, scope/time comparability and append-only revisions. Claims are not auto-verified. |
| Function registry | 666 traceable API contracts: 147 existing specifications and 519 proposals. This is a catalogue, not 666 implemented functions. |
| Systems and interop | Embedded C reference profiles, memory budgets, optional Pytyliki C ABI v1, language/toolchain and architecture catalogues. |
| VentuSample federation | Validates ventusample.pack.v1, derives normalized descriptors and compares stored pack metadata. The audit does not read or rewrite WAV assets. |

## Reaper Studio design

Studio adopts the **Duck Sovereign Canon** while retaining an editor-first layout: document and editing commands above the source workspace, with diagnostics, variables, call stack and execution state in distinct panes. The Tk/ttk theme uses the six approved color values, local system fonts, serif headings, compact geometry, visible keyboard focus and reduced-motion behavior.

The normative specification is [docs/DUCK_SOVEREIGN_CANON.md](docs/DUCK_SOVEREIGN_CANON.md). Existing language and interface contracts remain authoritative; the visual standard does not alter runtime semantics or imply native C17 parity.

## Run the reference runtime

Requires Python 3.10+. The reference runtime has no third-party runtime dependencies.

~~~sh
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m pip install -e .
python -m unittest discover -s tests -v
~~~

Run Reaper Studio on Windows:

~~~sh
python reaper_desktop.py
~~~

## Build the native C17 track

Requires CMake and a C17-capable compiler.

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
~~~

## Execution model and safety boundaries

- Python is the executable compatibility reference until native parity is demonstrated.
- Managed-heap figures are accounting over Python's allocator, not a physical allocator or RSS cap.
- Native FFI executes trusted ABI-compatible code in-process; it is not a sandbox for untrusted extensions.
- Consent grants are host-injected, HMAC-authenticated, scope-checked, time-bounded and revocable.
- Quotas and input validation define runtime limits.
- МОСТ aliases resolve to canonical REAPER symbols and share the semantic core.
- QCS is a separate validation frontend, not a hardware executor.

The parser, runtime and tests define the implemented feature boundary. Proposals and reserved syntax must remain explicitly distinguished from implemented behavior.

## Documentation

- [Language reference](LANGUAGE.md)
- [Runtime platform](docs/RUNTIME_PLATFORM.md)
- [Governance and consent](docs/HUMAN_FIRST_GOVERNANCE.md)
- [THESIS assertion provenance](docs/THESIS_ASSERTION_GRAPH.md)
- [Unified engineering standard](docs/UNIFIED_ENGINEERING_STANDARD.md)
- [Quality and commercial readiness](docs/QUALITY_COMMERCIAL_STANDARD.md)
- [Four-project federation](docs/PROJECT_FEDERATION_MATRIX.md)

## License

[Apache License 2.0](LICENSE)