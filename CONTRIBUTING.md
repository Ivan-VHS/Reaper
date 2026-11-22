# Contributing to Reaper

Thank you for helping improve Reaper. Reaper is a flow-first programming language with a Python reference runtime, developer tooling, and a developing native C17 track.

## Preserve the language boundary

Treat the Python runtime as the executable compatibility reference unless a contract explicitly changes. Native C17 work must state which syntax and runtime behavior it supports; do not imply full parity where only a subset is implemented. Native FFI remains opt-in. Reaper's runtime limits are not an operating-system security sandbox.

## Before opening a pull request

1. Read README.md, LANGUAGE.md, and the relevant design documents under docs/.
2. Add lexer, parser, runtime, VM, LSP, DAP, or Studio tests at the layer where behavior changes.
3. When changing language semantics, add examples and tests that cover both normal and boundary inputs.
4. Update README.md, README.uk.md, README.ru.md, and README.zh-CN.md when user-visible behavior, syntax, limits, commands, or examples change.
5. Update the language specification, token catalogue, or JSON schemas when their contracts change.
6. Keep diagnostics source-aware and avoid automatic edits to user files.

## Local checks

    python -m compileall -q reaper tests
    python -m unittest discover -s tests -v
    python -m reaper --check examples/flow.rpr
    python .github/scripts/check_readme_links.py
    python .github/scripts/check_readme_parity.py

For native changes, run the CMake build and CTest targets documented by the native-C workflow. Run the feature and project-contract validators when related registries or schemas change.

## Pull request expectations

Explain the problem, the language or tooling behavior changed, compatibility implications, tests run, and known gaps between the reference and native tracks. Keep syntax changes explicit and provide before/after examples.

## Security and review

Do not describe execution quotas as a sandbox. Do not enable FFI implicitly. Avoid executing untrusted source outside the bounded runtime. Report security concerns through SECURITY.md and keep changes focused.
