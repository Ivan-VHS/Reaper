# Reaper — flow-first programming language

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper is an expression-oriented language built around readable syntax and explicit data flow.** Its `::` operator passes a value into the next operation. The repository contains a Python reference interpreter, a developing native C17 core, and Reaper Studio for Windows.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)
## Live Reaper Studio screenshot

<p align="center"><img src="assets/screenshots/reaper-studio.png" alt="Reaper Studio running desktop application" width="100%"></p>

<sub>Actual live Windows 11 capture from the Reaper Studio process, 1920×1080. The screenshot shows the default starter document and empty output pane; no user project data is included.</sub>


See [four-project federation](docs/PROJECT_FEDERATION_MATRIX.md), [OCTA-8 topology](docs/OCTA_PYRAMID_FEDERATION.md), [federated integration](docs/FEDERATED_INTEGRATION.md), and [consolidated project-thread ledger](docs/THREADS_AND_FEDERATION.md).

## Example

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Capabilities

- **Python reference runtime:** lexer, parser, interpreter, CLI, REPL, modules, closures, collections, resource tracking, quotas, optional bytecode VM, profiling and hash-chained audit. Host-injected consent grants add HMAC-authenticated scope checks, finite TTL and revocation.
- **Reaper Studio:** Windows editor with check/run/debug, breakpoints, variables and call-stack inspection.
- **Native C17:** lexer, expression parser, owned AST, checked integer IR operations and limited lowering. Not yet a complete interpreter; Python remains the compatibility reference.
- **МОСТ:** Russian-first source surface with 54 exact keyword aliases (21 executable in the REAPER 0.1 reference subset; 33 lexically reserved for future grammar work), UTF-8-aware source columns, and one canonical semantic core. See the [20-principle Russian-native profile](docs/MOST_RUSSIAN_NATIVE_PROFILE.md).
- **QCS 1.0:** independent hardware-domain frontend with source locations, frame parser, Pratt expressions and JSON AST. It does not replace `.rpr` or execute hardware operations. Run: `reaper-qcs check examples/qcs_irq.qcs`.
- **THESIS assertion graph:** versioned claims, typed evidence references, exact time/scope comparability, review states and append-only revisions. It never auto-verifies a claim ([design](docs/THESIS_ASSERTION_GRAPH.md)).
- **MOST Function Registry 666:** 666 traceable API contracts (147 existing specifications + 519 proposals), with a traceability index and validator. This is a specification catalogue, not 666 implemented functions.
- **Systems and interop:** Embedded C, MCU profiles and memory budgets; opt-in Pytyliki C ABI v1; 66 language/toolchain entries, 14 architecture profiles and the validated MOST 20×20 matrix.
- **VentuSample federation:** validates `ventusample.pack.v1`, derives 22 normalized pack descriptors and compares two manifests with `ventusample_metrics()` / `ventusample_compare()`; an explicit trusted Pytyliki ABI v1 path is optional for distance cross-checks. WAV assets remain untouched.

## Run

Requires Python 3.10+; no third-party runtime dependencies.

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m pip install -e .
python -m unittest discover -s tests -v
```

Run Studio on Windows with `python reaper_desktop.py`.

## Build C17

Requires CMake and a C17-capable compiler.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
```

## Architecture and boundaries

Python remains the executable compatibility reference until native parity is demonstrated. The managed heap is accounting over Python's allocator, not a physical allocator or RSS cap. Native FFI runs trusted ABI-compatible code in-process. Toolchain discovery checks `PATH`; it does not install compilers. MOST aliases resolve to canonical REAPER symbols; QCS parsing does not prove hardware contracts.

## Documentation

[THESIS assertion provenance graph](docs/THESIS_ASSERTION_GRAPH.md)

[Governance and consent controls](docs/HUMAN_FIRST_GOVERNANCE.md) · [Anatidae UI/UX](docs/UI_UX_SYSTEM.md) · [12-principle motion](docs/DISNEY_MOTION_SYSTEM.md) · [Language](LANGUAGE.md) · [QCS frontend](docs/QCS_FRONTEND.md) · [MOST 666 registry](docs/MOST_FUNCTIONS_666.md) · [МОСТ specification](docs/MOST_LANGUAGE_SPEC.md) · [Russian-native profile](docs/MOST_RUSSIAN_NATIVE_PROFILE.md) · [Runtime](docs/RUNTIME_PLATFORM.md) · [Engineering standard](docs/UNIFIED_ENGINEERING_STANDARD.md)


[Governance and consent](docs/HUMAN_FIRST_GOVERNANCE.md) · [Anatidae constitution](docs/ANATIDAE_CONSTITUTION.md) · [Desktop design system](docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) · [UI/UX architecture](docs/UI_UX_ARCHITECTURE.md) · [12 animation principles](docs/DISNEY_MOTION_SYSTEM.md) · [Clinical Systems Reliability CSR-120](docs/CLINICAL_SYSTEMS_CSR120.md) · [MOST implementation status](docs/MOST_IMPLEMENTATION_STATUS.md) · [Project contract](docs/UNIFIED_PROJECT_CONTRACT.md)
[Windows releases](https://github.com/Ivan-VHS/Reaper/releases) · [Desktop build](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## Anatidae doctrine and language guarantees

- **Consent and accountability:** host-injected grants are HMAC-authenticated, scope-checked, time-bounded and revocable; audit records make execution decisions inspectable.
- **Bounded execution:** quotas, resource accounting and input validation define runtime limits. Python remains the compatibility reference until native C17 parity is demonstrated.
- **One canonical language contract:** МОСТ aliases share canonical REAPER symbols, parser and runtime; QCS is a separate validation frontend, not a hardware executor.
- **Honest implementation status:** MOST 666 contains 147 existing specifications and 519 proposals; it does not mean 666 functions are implemented. Native C17 lowering remains partial.
- **Trusted-code boundary:** in-process native FFI executes trusted ABI-compatible code; it is not a sandbox for untrusted extensions.
- **Accessible tools and purposeful motion:** Studio/editor UX should have clear keyboard and focus behavior, readable diagnostics, localization and reduced-motion support. Animation clarifies feedback; it must not obscure state.

The doctrine guides engineering decisions; it does not turn roadmap items into implemented runtime features.

## Documentation governance

[Documentation control](docs/DOCUMENTATION_CONTROL.md) defines the normative rules for public claims, evidence, privacy and integrations.

## License

[Apache License 2.0](LICENSE)

## Anatidae design layer

The shared [Anatidae naming canon](federation/ANATIDAE_NAMING_CANON.md) governs friendly UI vocabulary across the four-project family. The [Reaper Studio desktop design contract](docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) defines its use without changing language syntax, commands or diagnostics.


## Improvement and conflict resolution

The [20-control improvement, dissonance, and conflict standard](docs/IMPROVEMENT_CONFLICT_STANDARD.md) turns inconsistencies into evidence-led, testable changes while preserving Reaper's Python-reference/native-C17 parity boundary and runtime controls. Run `python tools/improvement_conflict.py` to validate the machine-readable register. This validates the governance contract; it is not a source-code scanner and does not claim unassessed controls are resolved.
