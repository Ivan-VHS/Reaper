# Unified Engineering Standard

**Profile:** flow-first language, Python reference runtime and developing native C17 implementation.

This standard turns the shared quality vocabulary into rules that can be implemented, tested and reviewed. It guides new work and consolidation; it does not claim native implementation parity with the reference runtime.

## Product boundary

Reaper owns source syntax, lexing, parsing, AST/IR, evaluation, module loading, diagnostics, runtime resources and language tooling. Pytyliki owns processor-oriented numerical primitives and its stable C ABI. OPlague owns Windows device inventory, driver-package inspection and device snapshots.

## Twenty quality groups, expressed as engineering rules

| Quality vocabulary | Enforceable meaning |
|---|---|
| Unified · Consolidated · Centralized | Maintain one language specification and one canonical semantic definition for each implemented operation. |
| Unique · Distinctive · Original | Preserve Reaper's flow-first syntax and language identity; do not become a wrapper around another project's runtime. |
| Universal · Cross-platform · Compatible | Keep the language core portable and isolate OS-specific process, filesystem and desktop integrations behind adapters. |
| Standardized · Normalized · Systematized | Version module metadata and machine-readable output; keep diagnostics, token definitions and semantic terminology consistent. |
| Versatile · Multifunctional · Multipurpose | Support CLI, REPL, linting, module graphs, reference execution and native development without forking language semantics. |
| Integrated · Interoperable · Interconnected | Use versioned JSON and explicit FFI boundaries for external systems; do not share private AST or runtime layouts. |
| Harmonized · Synchronized · Aligned | Keep grammar, Python frontend, C17 frontend, built-ins, examples and conformance tests aligned as coverage grows. |
| Adaptive · Flexible · Modular | Keep lexer, parser, AST, lowering, IR, optimizer, runtime and toolchain adapters independently testable. |
| Extensible · Scalable · Bounded | Bound recursion, execution steps, file sizes, collection growth and runtime resources; reject unsafe or unrepresentable operations. |
| Comprehensive · Holistic · Multidisciplinary | Verify syntax, semantics, execution, resource lifetime, interoperability, diagnostics and packaging as one lifecycle. |
| Exceptional · Unparalleled · Evidence-led | Do not label a native feature complete until its contract, tests and CI support the claim. |
| Singular · Coherent · Consistent | Keep one source of truth for operator precedence, token meanings, error categories and built-in behavior. |
| Exclusive · Explicit · Opt-in | Native FFI, external compiler discovery and execution of external tools require explicit opt-in and clear trust boundaries. |
| Coordinated · Combined · Composable | Compose language features through stable values and explicit data flow; avoid hidden global state and implicit module mutation. |
| Cross-language · Stable · Interoperable | Keep Python authoritative for implemented semantics until a C17 feature passes matching conformance vectors. |
| All-purpose · Generalized · Hybrid | Generalize reusable language primitives without weakening type, ownership, error or execution guarantees. |
| Remarkable · Auditable · Reproducible | Make parser, lowering and runtime behavior inspectable through fixtures, structured diagnostics and deterministic tests. |
| Rare · One-of-a-kind · Purposeful | Reserve syntax and token-catalog entries deliberately; catalogue membership alone never means executable behavior. |
| Unmatched · Unrivaled · Reliable | Reject malformed source, invalid module graphs, resource exhaustion and unsupported native operations predictably. |
| Integrated · Maintainable · Independent | Keep Reaper independently buildable; optional Pytyliki and OPlague adapters must not become mandatory runtime dependencies. |

## Existing integration contracts

- **OPlague snapshots:** Reaper consumes the versioned `oplage.device-snapshot.v1` data contract through federation tooling.
- **Pytyliki ABI v1:** optional numerical cross-checks require an explicit trusted library path. Loading a shared library executes native code and remains opt-in.
- **Native C17 track:** the C implementation is a developing subset. Python/C parity is established feature by feature through shared conformance tests, not inferred from matching names.

## Required review gates for new language features

1. Specify syntax, precedence, evaluation order, value semantics, errors and resource limits before implementation.
2. Add Python reference tests and parser/runtime fixtures; add native C17 tests only for the implemented subset.
3. Where both engines support a feature, run the same semantic vectors against both and compare results and failure classes.
4. Make module imports explicit; detect cycles and preserve deterministic dependency diagnostics.
5. Bound recursion, execution steps, memory growth and file access; release resources on success and failure.
6. Keep native FFI disabled by default, validate explicit paths and ABI versions, and never treat PATH discovery as permission to execute a toolchain.
7. Update language docs, feature registry, CLI help and implementation status together.

## Non-goals and truth rules

A reserved token is not an executable language feature. A discovered compiler is not a native backend. A partial parser or lowering path is not a complete compiler. The C17 track must not be advertised as a full interpreter until implementation and conformance establish that status.

## Related contracts

- [Unified Reaper architecture](REAPER_UNIFIED_ARCHITECTURE.md)
- [Federated integration](FEDERATED_INTEGRATION.md)
- [Token catalogue](TOKEN_CATALOG.md)
- [Runtime platform contract](RUNTIME_PLATFORM.md)
