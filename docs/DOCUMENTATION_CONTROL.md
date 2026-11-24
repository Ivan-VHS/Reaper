# Documentation control

**Scope:** Reaper README family, technical documentation, diagrams, screenshots and public language/runtime contracts.

## Acceptance gates

| Gate | Requirement |
|---|---|
| Evidence | Implemented claims link to source, tests, schemas or CI |
| Maturity | Separate implemented, partial, specified, planned and verified |
| Runtime parity | Python reference and native C17 status are never conflated |
| Platform | State Windows-only Studio and local stdio service boundaries |
| Trust | Document FFI opt-in, interpreter limitations and optional Node integration |
| Localization | English, Ukrainian, Russian and Chinese entry points match in meaning and commands |
| Visual provenance | Screenshots are real captures; workflow art is an illustration |
| Adaptive hero | Light/dark SVGs share dimensions and have accessible fallback text |
| Navigation | Important pages are reachable from the index and information map |
| Review | Verify links, examples, Mermaid and git diff --check |

## Maturity vocabulary

- **Implemented:** behavior exists in current source.
- **Partial:** only a subset exists.
- **Specified:** contract/design exists, implementation is not complete.
- **Planned:** future work without an available implementation.
- **Verified:** a named test/check passed on a stated revision and environment.

## Publication checklist

Update the README and the owning language/runtime contract together when behavior changes. A catalog or design document does not prove compiler conformance. A passing Python test suite does not prove native C17 parity.
