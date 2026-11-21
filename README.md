# Reaper — flow-first programming language

[CI](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) · Python 3.10+ reference runtime · C17 native track · Windows Studio · Apache-2.0

Reaper is an expression-oriented language: `::` passes a value into the next operation. Python remains the executable compatibility reference; C17 is a developing native track, not yet a full replacement.

## Live Studio

<p align="center"><img src="assets/screenshots/reaper-studio.png" alt="Reaper Studio running on Windows" width="100%"></p>
<sub>Live Windows 11 capture, 1920×1080.</sub>

## Capability matrix

| Area | Scope / state |
|---|---|
| Python runtime | lexer, parser, interpreter, CLI, REPL, modules, closures, quotas and audit |
| NOO TAH | Node.js bridge: V8/libuv-backed execution via official Node, ESM/CJS, npm forwarding, syntax check and inspector launch |
| Division/allocation | checked Euclidean division, balanced partition and proportional allocation |
| Reaper Studio | Windows editor: check/run/debug, breakpoints, variables, call stack |
| Native C17 | lexer, expression parser, owned AST, checked IR and limited lowering |
| МОСТ | 54 exact aliases: 21 executable in reference subset, 33 lexically reserved |
| QCS 1.0 | separate hardware-domain parser and JSON AST; no hardware execution |
| THESIS | typed evidence graph; claims are not auto-verified |
| Registries | 813 feature proposals; 666 API contracts; 666 reserved token lexemes |
| Internal products | 18 in-process services; Operandu + Dropaul workflow/data layer; Python reference only |
| Federation | OPlague snapshots, VentuSample pack v1, optional Pytyliki C ABI |

## Run and test

```sh
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m unittest discover -s tests -v
```

NOO TAH integrates the official cross-platform Node.js runtime: V8, libuv, core APIs, ESM/CommonJS, streams, workers, child processes, npm/npx, N-API and Inspector. Reaper Studio includes JavaScript run/check/stop and runtime diagnostics. Commands: `reaper-noo-tah doctor`, `reaper-noo-tah run app.mjs`, `reaper-noo-tah npm run build`. See [NOO TAH architecture](docs/NOO_TAH.md).

Studio: `python reaper_desktop.py` (Windows). Native: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`, then `cmake --build build --parallel` and `ctest --test-dir build --output-on-failure`.

```reaper
craft double(value) { yield value * 2 }
make result := [1, 2, 3] :: map(double) :: sum()
emit "result = " ++ text(result)
```

[Features](docs/FEATURES.md) · [Language](LANGUAGE.md) · [Division](docs/DIVISION_ENGINE.md) · [Architecture](docs/ARCHITECTURE.md) · [813 registry](docs/REAPER_813_FEATURE_ARCHITECTURE.md) · [Federation](docs/PROJECT_FEDERATION_MATRIX.md) · [Docs index](docs/README.md)

[Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Releases](https://github.com/Ivan-VHS/Reaper/releases) · [Apache-2.0](LICENSE)
