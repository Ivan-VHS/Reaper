# Reaper repository adoption standard

**Scope:** the five Ivan-VHS repositories currently connected to this workspace.
**Rule:** Reaper is the shared language and policy toolchain; specialist runtimes remain authoritative for their own domains.

## Canonical language contract

- Reaper owns its grammar, keyword semantics, reference runtime, compiler and diagnostics.
- The executable flow operator in the current reference language is `::`. Integrations must not silently substitute an unimplemented pipeline spelling.
- МОСТ is an exact lexical alias profile. An alias normalizes to the same canonical token; no stemming, synonym guessing or parallel semantics are allowed.
- The frontend pipeline is source → tokens → AST → checks → canonical IR → supported execution backend. Source provenance must survive every transformation.
- Source offsets are half-open UTF-8 byte ranges. Line/column coordinates are 1-based and count Unicode code points. The source name is carried by the Python token/IR path; lower-level C callers pair byte ranges with their compilation-unit source identity.
- `ok/err`, exhaustive `match`, structural typing, ownership/effect checking, general async execution and general machine-code generation must be labelled by their actual feature status. A catalogue entry or reserved token is not an implementation.

## Repository roles

| Repository | Reaper role | Boundary that must remain explicit |
|---|---|---|
| **Reaper** | Authoritative language, Python reference runtime, Studio/LSP/DAP, canonical IR and limited native C17 expression/AOT slices | Native C17 coverage is partial; Python remains authoritative outside proven subsets |
| **DuckOS** | User-space source checker and separate-process Studio launcher; `.rpr` policy/contract programs | No implicit shell, kernel privilege, driver loading or inherited device access |
| **Pytyliki** | CI-only Reaper policy checks for bounded reference-profile invariants | C11 processor core and C ABI remain the application runtime; Reaper is not a required runtime dependency |
| **OPlague** | Optional native C17 integer-expression ABI for a validated ordinal aggregation | Explicit trusted absolute library path; no driver writes, device control or compatibility verdicts |
| **VentuSample** | Optional native C17 integer-expression ABI for deterministic control/preset calculations | Offline control only; never in the real-time DSP path or arbitrary plugin loading |

## Integration requirements

1. Keep source parsing and policy evaluation deterministic and bounded. Define input, token, nesting, instruction, output and timeout limits at the boundary.
2. Keep I/O and host effects outside pure Reaper expressions unless a separately reviewed capability contract explicitly authorizes them.
3. Prefer a process boundary for CLI/Studio integration. Use a fixed argument vector, `shell=False`, explicit working directory, bounded timeout and bounded captured output.
4. Use the C ABI only when its version is checked and the operator selects the exact library path. Do not search `PATH`, the current directory or implicit plugin locations.
5. Validate source files with Reaper's own checker. Do not reimplement the grammar in each specialist application.
6. Keep domain-specific engines native to their repositories: processor inspection stays in Pytyliki, read-only device/package analysis stays in OPlague, audio rendering/DSP stays in VentuSample, and OS orchestration stays in DuckOS.
7. Test both success and failure paths: invalid source, unsupported syntax, overflow, resource limits, missing runtime, ABI mismatch, invalid path and timeout.
8. Pin cross-repository source dependencies to immutable commit SHAs in CI and submodule records. Update those pins deliberately with a reviewed change.
9. Report capabilities as implemented, partial, experimental or planned. Never infer implementation from a design document, token catalogue, feature registry or screenshot.
10. Preserve `Span` provenance through lowering, optimization and diagnostics. An optimization that changes instruction shape must keep the original source range that explains the resulting operation.

## Verification matrix

| Contract | Required evidence |
|---|---|
| Language correctness | Reaper lexer/parser/runtime/IR tests and differential tests for supported backends |
| Source provenance | UTF-8 offset tests, Unicode column tests and IR source-map tests |
| Host integration | subprocess argument/timeout/source-validation tests |
| Native integration | ABI version tests, explicit library-path tests and real shared-library CI build |
| Domain integrity | specialist project's own unit, native build, sanitizer and product-contract suites |

This standard is a cross-repository architecture contract. It does not claim that every feature listed in the language roadmap is already available in every backend.
