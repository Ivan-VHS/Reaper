# Reaper Framework Federation v1

**Schema:** `reaper.framework-registry/v1`  
**C ABI:** `reaper.framework-cabi.v1`  
**Implementation:** C17 registry plus twenty Reaper source modules  
**Maturity:** native registry and signature validation implemented; Reaper reference-runtime handlers are defined in the v1.1 handler increment; native C17 domain handlers remain contract-only

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
- `reaper_framework_invoke()` validates a framework/function key and arity, enforces 1 MiB request/response ceilings, and calls an explicit host-owned callback. Callback failures are normalized; output-size over-reporting is rejected.

The shared library exports a platform C ABI for compatible foreign-language hosts. `reaper_framework_invoke()` is a callback-based inter-language call gate: a caller supplies the payload encoding and a trusted host callback. The registry validates the operation signature and buffer sizes, but does not load code, grant capabilities, or provide domain handlers. The host callback remains responsible for typed marshalling, authorization, ownership and operation behavior. Dedicated Rust, Zig, Go, Swift, JVM, .NET or other SDK wrappers are not included in this increment.

## Reaper source modules

Each namespace has an importable `.rpr` module under `examples/frameworks/modules/`. Each module exports metadata helpers and six named Reaper source operations matching its stable function keys. The shared helper module is `examples/frameworks/federation_common.rpr`. The complete operation list and semantics are documented in [Framework Federation Reaper handlers v1.1](FRAMEWORK_FEDERATION_HANDLERS_V1.md).

`examples/frameworks/manifest_client.rpr` checks metadata; `examples/frameworks/federation_handlers_smoke.rpr` exercises all 120 source operations through the Reaper reference interpreter. These are reference-runtime handlers, not built-in handlers in the native C17 registry. Binding Reaper expressions to `reaper_framework_invoke()` remains a separate compiler/FFI milestone.

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
| Native registry API functions | 8 |
| Reaper reference-runtime source handlers | 120 |
| Executable native C17 domain operation handlers | 0 |
| Reaper source-level native bindings | 0 |

The native zeroes are intentional and important: a Reaper reference handler is not a native C17 built-in handler, and neither implies a source-level C ABI binding. No live usage analytics, personal data or network telemetry is collected.

## Cross-language boundary

The shared library provides a versioned C ABI for registry inspection and explicit host callback dispatch. The dispatcher accepts caller-defined, versioned payload bytes and enforces 1 MiB request/response limits; it is not a wire protocol. The host callback must perform typed marshalling, capability/authorization checks, handle ownership and structured error mapping. No ambient library loading or automatic privilege grant is performed. Reaper source-level calls are not yet connected to this bridge.

## Verification

The native C test verifies registry cardinality, stable IDs, function keys, case-insensitive lookup, arity rejection, callback dispatch, payload bounds and public statistics. The CMake target also installs the shared library and public header.
