# Architecture 66 — Reaper autonomy, independence and runtime contract

Status: normative requirements for the Reaper language project. A requirement marked as a future milestone is not a shipped feature.

## Architectural decision

Reaper is a standalone language implementation, not a service collection. Its logical monolith is the language product: CLI, lexer, parser, runtime, diagnostics, packaging, examples and tests work together as one installable unit while remaining separate implementation layers. The interpreter must stay small, deterministic, dependency-light and bounded.

### A. Product unity and modularity

1. Maintain one Reaper language identity, package and command-line entry point.
2. Keep the CLI as the single primary user-facing execution surface for the current milestone.
3. Keep lexer, parser, runtime, diagnostics and packaging in separate modules.
4. Treat tokens and AST nodes as explicit internal contracts between compiler stages.
5. Keep the runtime API callable independently of the CLI.
6. Centralize language version information and expose it consistently through package metadata and --version.
7. Keep platform-specific behavior out of language semantics.
8. Reject dependencies that duplicate existing standard-library capabilities without a measured need.

### B. Standalone operation

9. Keep the interpreter runnable locally without a network connection.
10. Keep runtime execution free of third-party dependencies.
11. Load source files explicitly from the CLI; the runtime API accepts source text directly.
12. Keep check-only mode free of program execution and console side effects.
13. Make UTF-8 source handling explicit and report decoding failures cleanly.
14. Do not require Pytyliki, a cloud service, database or external daemon to execute Reaper programs.
15. Keep installation reproducible through pyproject.toml and the documented editable-install path.
16. Make missing or invalid input fail with a clear exit code and diagnostic.
17. Keep examples runnable from a clean checkout.
18. Keep future package, plugin and registry features optional until they have their own integrity and lifecycle design.

### C. Language semantics and bounded automation

19. Preserve explicit data-flow composition through the :: operator.
20. Preserve immutability by default with make and explicit mutation through vary/change.
21. Keep console effects visible through explicit emit/say/ask operations.
22. Keep coercions explicit; do not silently convert booleans, numbers and text.
23. Keep expression precedence and associativity documented and regression-tested.
24. Keep lexical scope and closure behavior deterministic.
25. Bound every executing program by an instruction-step budget.
26. Bound recursive function calls with a configurable call-depth limit.
27. Bound collection sizes before large iteration or materialization.
28. Bound text growth from concatenation and report quota violations as language errors.

### D. Independent internal subsystems and future integrations

29. Keep each interpreter layer testable without starting a separate process.
30. Keep module imports acyclic and avoid hidden runtime singletons.
31. Use typed internal objects for tokens, AST nodes, bindings and callable values.
32. Keep public Python entry points small and stable.
33. Add foreign-function support only behind an explicit, narrow adapter.
34. Validate any future external package by identity, license, version, integrity and dependency graph.
35. Pin dependencies and record provenance before adding runtime packages.
36. Ensure a missing optional adapter cannot prevent core language execution.
37. Test each adapter with conformance tests and negative cases.
38. Do not claim native, GPU, distributed or self-hosted execution until a real backend and conformance suite exist.

### E. Resource governance

39. Validate all configurable limits as positive integers.
40. Check collection and text limits before allocating the expanded result where practical.
41. Avoid unbounded list materialization in built-ins.
42. Keep each/while loops subject to the shared instruction budget, including empty loop bodies.
43. Avoid background threads and unmanaged worker processes in the current interpreter.
44. Convert expected host-language failures into source-aware Reaper errors.
45. Keep cancellation and interruption responsive at statement/iteration boundaries.
46. Document the limits and their defaults in CLI help and language documentation.

### F. Safety and integrity

47. Treat Reaper source as executable input; do not describe the interpreter as a security sandbox.
48. Do not add implicit shell, filesystem, network, subprocess or hardware capabilities.
49. Validate built-in argument counts and value types before performing work.
50. Reject non-finite numeric results and invalid arithmetic.
51. Keep diagnostics free of secrets and avoid logging full source by default.
52. Keep future file-writing effects opt-in and scoped to an explicit capability.
53. Require an atomic-write/backup/rollback design before persistent destructive operations are introduced.
54. Fail closed when an optional capability, permission or resource limit is unavailable.

### G. Quality and evolution

55. Support the declared Python 3.10+ language baseline and test the supported CI matrix.
56. Keep standard-library unittest tests runnable from a clean checkout.
57. Run tests on every pull request and push to the default branch.
58. Include compile-time/import checks and executable example smoke tests in CI.
59. Review language changes for grammar ambiguity, compatibility and runtime cost.
60. Merge only after required CI and repository review policies pass; do not bypass branch protection.
61. Keep README, LANGUAGE.md, pyproject metadata and CLI help synchronized.
62. Make build, install, check and run commands reproducible.
63. Record design decisions and language changes in version control.
64. Add boundary and failure-path tests for every new quota or runtime capability.
65. Distinguish implemented semantics from roadmap items such as static types, bytecode, native code and self-hosting.
66. Re-evaluate this contract for every new language subsystem and keep each applicable rule backed by code, tests or an explicit non-implementation statement.

## Current conformance snapshot

| Area | Current evidence | State |
|---|---|---|
| Lexer, parser and tree-walk runtime | reaper/ modules | Implemented |
| CLI and check-only mode | reaper/cli.py | Implemented |
| Explicit console effects and lexical scope | runtime and language tests | Implemented |
| Step budget and call-depth limit | Interpreter | Implemented |
| Collection and text quotas | Interpreter and CLI | Added in this branch; CI must confirm |
| Standard-library runtime | pyproject.toml and imports | Implemented by design |
| Automated CI | .github/workflows/ci.yml | Added in this branch; CI must confirm |
| Static typing, bytecode, native backend | Roadmap only | Not implemented |
| Package registry, plugin host, FFI, network access | Roadmap only | Not implemented |
| Self-hosting compiler | Roadmap only | Not implemented |

## Acceptance gate

A language change is ready for review only when grammar and semantics are documented, limits and error behavior are explicit, tests cover normal and boundary cases, examples still run, supported Python CI passes, and documentation does not claim capabilities absent from the source.
