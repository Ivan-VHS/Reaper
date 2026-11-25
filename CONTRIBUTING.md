# Contributing to Reaper

Reaper is a flow-first programming language with a Python reference runtime and native tooling. Keep the grammar, interpreter, native implementation, LSP and DAP contracts aligned.

## Before opening a pull request

1. File a focused issue with a minimal `.rpr` example and the exact command or editor action.
2. Treat source files as untrusted input. Preserve parser, instruction, collection, text, heap and open-resource limits.
3. Do not describe a reserved token or roadmap entry as executable until parsing, runtime behaviour and tests all exist.
4. Keep diagnostic codes stable. Add a new code instead of repurposing an old one, and update `docs/errors/DIAGNOSTICS.md`.
5. Keep FFI disabled unless a user explicitly opts in.
6. Apply [Ivan-VHS Code Style](docs/IVAN_VHS_CODE_STYLE.md) and the shared [Psychoporter profile](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/PSYCHOPORTER_CODE_STYLE.md). Preserve Reaper syntax, C/C++ idioms and the owning subsystem's established naming and formatting conventions.

## Local verification

```sh
python -m unittest discover -s tests -v
python -m reaper --explain RPR-E0013
```

If native components change, also configure and run the repository's CMake test targets.

## Pull request expectations

Explain grammar and compatibility impact, resource bounds, diagnostics and test coverage. Include a short source example when syntax changes. Do not use issue-closing keywords in PR descriptions; maintainers close issues after review.

## Shared report format

To wrap an existing JSON result in the common report metadata contract, run python tools/report_envelope.py --tool reaper --version VERSION < result.json. Keep the tool-specific result unchanged. Tests live in tests/test_report_envelope.py.
