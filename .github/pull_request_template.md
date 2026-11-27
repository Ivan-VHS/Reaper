This PR describes one coherent change to Reaper and the language or tooling behavior it affects.

## What changed
Explain the result in plain language, then name the relevant syntax, module, compiler pass, runtime path or developer workflow.

## Why
Describe the problem or missing capability this change addresses.

## Language and compiler impact
- [ ] Syntax, typing and diagnostics are documented where they change.
- [ ] Canonical IR, Span and SourceMap information remain consistent where affected.
- [ ] Public APIs, ABI behavior and source compatibility are preserved or explicitly versioned.
- [ ] Resource bounds, ownership and FFI boundaries are clear.
- [ ] Reference-runtime and native-AOT capabilities are distinguished accurately.

## Verification
List the exact Reaper conformance, runtime, native build and CI commands that were run. State clearly what is pending or unsupported.

- [ ] Positive, negative and boundary cases are covered.
- [ ] Examples use the current Reaper syntax.
- [ ] Documentation and feature status match the implementation.

## Compatibility and safety
Explain affected module contracts, target platforms, host capabilities and any limitations. Do not claim native-AOT parity when only the reference runtime was checked.

## Dependencies
Link stacked PRs and related repository changes. State the required merge order.
