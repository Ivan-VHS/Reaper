# Reaper Framework Federation v1

**Schema:** `reaper.framework-registry/v1`  
**C ABI:** `reaper.framework-cabi.v1`  
**Implementation:** C17 registry with importable Reaper metadata modules  
**Maturity:** registry and signature validation implemented; domain operation handlers remain contract-only

## What is delivered

This increment registers the twenty requested framework namespaces under one versioned Reaper registry. Each framework has one stable feature key and six stable operation keys, for **20 frameworks and 120 operation contracts**.

| Framework | Domain | Feature key |
|---|---|---|
| CodexNo (`codex-no`) | Compiler and language feature catalog | `RPR-FWK-001` |
| Joint Baby (`joint-baby`) | Cross-language composition and ABI binding | `RPR-FWK-002` |
| Correpse (`correpse`) | Contracts, consistency and reconciliation | `RPR-FWK-003` |
| Allocate Purpose (`allocate-purpose`) | Memory, allocation and resource budgets | `RPR-FWK-004` |
| Collillioi (`collillioi`) | Collections and deterministic algorithms | `RPR-FWK-005` |
| Aspdoi (`aspdoi`) | Asynchronous tasks and structured scheduling | `RPR-FWK-006` |
| ASJIOP (`asjiop`) | ABI, serialization and binary layouts | `RPR-FWK-007` |
| ALLLLL (`alllll`) | Language feature registry and compatibility | `RPR-FWK-008` |
| Zabor (`zabor`) | Capability grants and policy scopes | `RPR-FWK-009` |
| Vjinz (`vjinz`) | Source maps, diagnostics and tracing | `RPR-FWK-010` |
| SupremeBoy (`supreme-boy`) | Quality gates and release evidence | `RPR-FWK-011` |
| CheeNow (`chee-now`) | Channels, concurrency and back-pressure | `RPR-FWK-012` |
| HumbleBumble (`humble-bumble`) | Result values, error taxonomy and recovery | `RPR-FWK-013` |
| Hub2 (`hub2`) | Service discovery and event distribution | `RPR-FWK-014` |
| Kloz (`kloz`) | Modules, packages and dependency lifecycle | `RPR-FWK-015` |
| CO (`co`) | Core primitives and deterministic identity | `RPR-FWK-016` |
| CrippleBO (`cripplebo`) | Fault records and resilience policies | `RPR-FWK-017` |
| RippleCripple (`ripplecripple`) | Reactive streams and flow control | `RPR-FWK-018` |
| Secator (`secator`) | Security policy and secret references | `RPR-FWK-019` |
| PollATIA (`pollatia`) | Public statistics and privacy-aware metrics | `RPR-FWK-020` |

Every function entry has a stable key in the form `RPR-FWK-NNN-FNN`, a name, argument bounds and a description. Framework IDs and names are resolved case-insensitively.

## Native API

Include `reaper/framework_suite.h` and link `reaper_frameworks`.

- `reaper_framework_abi_version()` returns ABI version 1.
- `reaper_framework_count()` and `reaper_framework_at()` enumerate frameworks.
- `reaper_framework_find()` resolves an ID or display name.
- `reaper_framework_function_find()` resolves an operation descriptor.
- `reaper_framework_validate_arity()` validates a call shape before dispatch.
- `reaper_framework_registry_stats()` computes the public registry counters.

The shared library exports a platform C ABI for compatible foreign-language hosts. These exports cover registry metadata and arity validation only; they do **not** execute the framework operations. Dedicated Rust, Zig, Go, Swift, JVM, .NET or other SDK wrappers are not included in this increment.

## Reaper source modules

Each namespace has an importable `.rpr` metadata module under `examples/frameworks/modules/`. The modules expose the canonical ID, display name, feature key, operation keys and maturity state. `examples/frameworks/manifest_client.rpr` imports all twenty modules and exercises Reaper's existing module/export semantics.

These are metadata facades, not hidden host calls. Language-level dispatch from Reaper expressions into the C registry is a separate compiler/FFI milestone.

## Public statistics and maturity

Run the native tools:

```sh
reaper-c --frameworks
reaper-c --framework codex-no
reaper-c --framework-stats
```

The statistics are computed from the compiled registry and intentionally distinguish catalogued contracts from executable domain handlers:

| Metric | Current verified value |
|---|---:|
| Registered frameworks | 20 |
| Registered function contracts | 120 |
| Native registry API functions | 7 |
| Executable domain operation handlers | 0 |
| Reaper source-level native bindings | 0 |

The zeroes are intentional and important. A registered signature is not an implementation. No live usage analytics, personal data or network telemetry is collected.

## Cross-language boundary

The shared library provides a versioned C ABI metadata surface so a trusted host written in a C-ABI-compatible language can inspect the registry. It is not a wire protocol and does not authorize native execution. Any future invocation bridge must add typed values, ownership/lifetime rules, effect declarations, capability checks, structured errors and per-language conformance tests before operation handlers are marked implemented.

## Verification

The native C test verifies registry cardinality, stable IDs, function keys, case-insensitive lookup, arity rejection and public statistics. The CMake target also installs the shared library and public header.
