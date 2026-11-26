# Reaper 325 Frameworks — implementation plan

**Spec:** [325 Frameworks design](../specs/2026-11-26-reaper-325-frameworks-design.md)

## Global constraints

- Reaper `.rpr` is the implementation language for framework behavior.
- Every framework gets a separate module and a stable ID.
- No ambient host effects, hardware access, implicit FFI, networking or subprocesses.
- Preserve first batch APIs and existing Reaper module-loader behavior.
- Keep `main` untouched; work only on `feat/frameworks-skeleton-batch-01`.

## Tasks

1. Add a machine-readable 65-domain / 325-module index and interpreter-driven positive/negative tests. Run the tests before implementation and record the expected missing-module failure.
2. Implement all 325 standalone modules using the five common contract roles, with domain-scoped API identifiers and input validation.
3. Add package discovery and recursive Reaper source package data; include the full suite in the CTest path.
4. Add architecture, API, constraints and maturity documentation; update the 66 × 5 roadmap without claiming privileged capabilities.
5. Run focused framework tests, full unittest discovery, Python packaging validation, CMake build and CTest.
6. Inspect the exact PR head and all required Actions results. Keep the PR in Draft until the review/CI gates are satisfied.

## Verification commands

- `python -m unittest tests.test_framework_programme -v`
- `python -m unittest discover -s tests -v`
- `python -m build --wheel` (when the build frontend is available)
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --parallel`
- `ctest --test-dir build --output-on-failure`
