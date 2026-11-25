# Contributing to Reaper

Reaper is a flow-first programming language with a Python reference runtime and native tooling. Keep the grammar, interpreter, native implementation, LSP and DAP contracts aligned.

## Before opening a pull request

1. File a focused issue with a minimal `.rpr` example and the exact command or editor action.
2. Treat source files as untrusted input. Preserve parser, instruction, collection, text, heap and open-resource limits.
3. Do not describe a reserved token or roadmap entry as executable until parsing, runtime behaviour and tests all exist.
4. Keep diagnostic codes stable. Add a new code instead of repurposing an old one, and update `docs/errors/DIAGNOSTICS.md`.
5. Keep FFI disabled unless a user explicitly opts in.

## Local verification

```sh
python -m unittest discover -s tests -v
python -m reaper --explain RPR-E0013
```

If native components change, also configure and run the repository's CMake test targets.

## Pull request expectations

Explain grammar and compatibility impact, resource bounds, diagnostics and test coverage. Include a short source example when syntax changes. Do not use issue-closing keywords in PR descriptions; maintainers close issues after review.

## Psychoporter 666 review gate

Use [Psychoporter 666](docs/PSYCHOPORTER_666.md) as Reaper's normative code-style and engineering doctrine.

For each change:
1. Select only the rules that apply to the changed language layer, target and risk.
2. Check current grammar and feature maturity before using proposed syntax or claiming compiler support.
3. Review naming, data contracts, source spans, resource bounds, effects/capabilities, failure paths and tests.
4. Keep the PR focused; record justified exceptions and compatibility impact.
5. Run python tools/validate_psychoporter.py to verify the constitution/profile structure.

The validator checks document integrity only. A passing result does not certify implementation quality or replace code review, unit/integration tests, native parity checks or hardware qualification. Do not force every rule onto every module.

When principles conflict, use this order: correctness and safety → public contract and compatibility → clarity → aesthetics.

## Shared report format

To wrap an existing JSON result in the common report metadata contract, run python tools/report_envelope.py --tool reaper --version VERSION < result.json. Keep the tool-specific result unchanged. Tests live in tests/test_report_envelope.py.
