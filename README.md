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
| Division/allocation | checked Euclidean division, balanced partition and proportional allocation |
| Reaper Studio | Windows editor: check/run/debug, breakpoints, variables, call stack |
| Native C17 | lexer, expression parser, owned AST, checked IR and limited lowering |
| МОСТ | 54 exact aliases: 21 executable in reference subset, 33 lexically reserved |
| QCS 1.0 | separate hardware-domain parser and JSON AST; no hardware execution |
| THESIS | typed evidence graph; claims are not auto-verified |
| Registries | 813 feature proposals; 666 API contracts; 666 reserved token lexemes |
| Internal products | 18 in-process services; Operandu + Dropaul workflow/data layer; Python reference only |
| Federation | OPlague snapshots, VentuSample pack v1, optional Pytyliki C ABI |

## IDE language and debug services

- `python -m reaper.lsp` — versioned UTF-16 LSP workbench with background indexing, completion, navigation and rename.
- `python -m reaper.dap` — DAP launch, line breakpoints, statement stepping, stack and local-variable inspection.
- Installed entry points: `reaper-lsp` and `reaper-dap`.

See [Experimental Language Workbench](docs/EXPERIMENTAL_LANGUAGE_WORKBENCH.md) for the current implementation boundary.

## Run and test

```sh
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m unittest discover -s tests -v
```

Studio: `python reaper_desktop.py` (Windows). Native: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`, then `cmake --build build --parallel` and `ctest --test-dir build --output-on-failure`.

```reaper
craft double(value) { yield value * 2 }
make result := [1, 2, 3] :: map(double) :: sum()
emit "result = " ++ text(result)
```

[Internal products](docs/INTERNAL_PRODUCTS.md) · [Features](docs/FEATURES.md) · [Language](LANGUAGE.md) · [Division](docs/DIVISION_ENGINE.md) · [Architecture](docs/ARCHITECTURE.md) · [813 registry](docs/REAPER_813_FEATURE_ARCHITECTURE.md) · [Federation](docs/PROJECT_FEDERATION_MATRIX.md) · [Docs index](docs/README.md)

[Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Releases](https://github.com/Ivan-VHS/Reaper/releases) · [Apache-2.0](LICENSE)
