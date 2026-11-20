# Reaper — flow-first programming language

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper is an expression-oriented language built around readable syntax and explicit data flow.** Its `::` operator passes a value into the next operation. The repository contains a Python reference interpreter, a developing native C17 core, and Reaper Studio for Windows.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

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

- **Python reference runtime:** lexer, parser, interpreter, CLI, REPL, modules, closures, collections, resource tracking, quotas, optional bytecode VM, profiling and hash-chained audit.
- **Reaper Studio:** Windows editor with check/run/debug, breakpoints, variables and call-stack inspection.
- **Native C17:** lexer, expression parser, owned AST, checked integer IR operations and limited lowering. Not yet a complete interpreter; Python remains the compatibility reference.
- **МОСТ:** exact Russian keyword aliases over REAPER 0.1 and its shared parser/runtime; no separate semantics or runtime.
- **QCS 1.0:** independent hardware-domain frontend with source locations, frame parser, Pratt expressions and JSON AST. It does not replace `.rpr` or execute hardware operations. Run: `reaper-qcs check examples/qcs_irq.qcs`.
- **MOST Function Registry 666:** 666 traceable API contracts (147 existing specifications + 519 proposals), with source inventory and validator. This is a specification catalogue, not 666 implemented functions.
- **Systems and interop:** Embedded C, MCU profiles and memory budgets; opt-in Pytyliki C ABI v1; 66 language/toolchain entries, 14 architecture profiles and the validated MOST 20×20 matrix.

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

[Anatidae UI/UX](docs/UI_UX_SYSTEM.md) · [12-principle motion](docs/DISNEY_MOTION_SYSTEM.md) · [Language](LANGUAGE.md) · [QCS frontend](docs/QCS_FRONTEND.md) · [MOST 666 registry](docs/MOST_FUNCTIONS_666.md) · [МОСТ specification](docs/MOST_LANGUAGE_SPEC.md) · [Runtime](docs/RUNTIME_PLATFORM.md) · [Engineering standard](docs/UNIFIED_ENGINEERING_STANDARD.md)

[Windows releases](https://github.com/Ivan-VHS/Reaper/releases) · [Desktop build](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## License

[Apache License 2.0](LICENSE)
