# Native capability suite

**Schema:** `reaper.native-capabilities.v1`  
**Implementation language:** C17  
**Registry:** 18 modules, 6 operation contracts per module (108 total)

This catalog adds the requested domain APIs to the native Reaper track without replacing the existing Python reference product registry or the older Kora utility namespaces. IDs are stable and case-insensitive; function names are resolved within their owning module.

## Inspect the native registry

After building Reaper:

```sh
./build/reaper-c --capabilities
./build/reaper-c --capability operandu
./build/reaper-c --capability keel-koh
```

The first command prints all modules and operation signatures. The second and third print the selected module and its six operation contracts.

## Module map

| ID | Display name | Domain | Operation contracts |
|---|---|---|---:|
| `operandu` | Operandu | Expressions, operands and transformations | 6 |
| `dropaul` | Dropaul | Payload routing, queues and staging | 6 |
| `zdoro` | Zdoro | Wellness check-ins and recovery | 6 |
| `pyemont` | Pyemont | Analytics, reports and forecasts | 6 |
| `dilly` | Dilly | Deferred tasks and reminders | 6 |
| `baplap` | Baplap | Iterations, retries and lap timing | 6 |
| `sretuo` | Sretuo | Reversal, rollback and mirroring | 6 |
| `kali` | Kali | Security, isolation and access control | 6 |
| `zalam` | Zalam | Segmentation, clipping and stitching | 6 |
| `liur` | Liur | Entity links and dependency graphs | 6 |
| `keel-koh` | Keel Koh | Anchors, stabilization and drift control | 6 |
| `vorof` | Vorof | Source collection and consolidation | 6 |
| `vprof` | Vprof | Profiling, telemetry and allocations | 6 |
| `profe` | Profe | Profiles, roles and competencies | 6 |
| `prossee` | Prossee | Process lifecycles and transitions | 6 |
| `vprossee` | Vprossee | Surveys, responses and branching | 6 |
| `professiya` | Professiya | Profession and career tracks | 6 |
| `profevo` | Profevo | Evolution and growth planning | 6 |

## Native C API

Include `reaper/capability_suite.h`.

- `reaper_capability_module_count()`, `reaper_capability_module_at()` enumerate the registry.
- `reaper_capability_module_find()` resolves a module ID or display name.
- `reaper_capability_function_find()` resolves an operation in its module.
- `reaper_capability_validate_arity()` checks the operation's declared argument bounds.
- The allocation-free primitives below are callable native implementations, not placeholder entries.

| Primitive | Behavior |
|---|---|
| `reaper_capability_fold_i64` | Callback-based i64 reduction |
| `reaper_capability_map_i64` | Callback-based i64 mapping into caller-owned output |
| `reaper_capability_reverse_i64` | Copy or in-place reversal |
| `reaper_capability_clip_f64` | Finite-value range clipping |
| `reaper_capability_chunk_count` | Overflow-safe chunk count |
| `reaper_capability_calc_delta_f64` | Absolute and relative delta (zero baseline rejected) |
| `reaper_capability_detect_anomalies_f64` | Mean/variance sensitivity flags |
| `reaper_capability_forecast_trend_f64` | Least-squares linear trend projection |
| `reaper_capability_check_drift_f64` | Absolute drift check against a tolerance |
| `reaper_capability_retry_delay_ms` | Saturating exponential retry delay |

All caller-owned output buffers must have sufficient capacity. Invalid pointers, invalid ranges, non-finite data and invalid arities return explicit status values. The mapper and reducer execute caller-supplied native callbacks; callers remain responsible for callback safety and overflow policy.

## Maturity and boundaries

The **18 modules / 108 operations are registered API contracts**. They are discoverable from the C17 binary and have stable names, descriptions and arity metadata. Only the shared primitives listed in the preceding table are implemented as executable native routines in this change. Higher-level business handlers (for example, persistent queue draining, wellness storage, process orchestration, arbitrary sandbox execution, secret rotation, profile persistence and survey branching) are not represented as complete merely because their signatures are registered.

In particular:

- `Kali.sandbox_exec` is an API contract, not an operating-system sandbox. The native runtime does not execute arbitrary commands through this catalog.
- `Zdoro` is a non-clinical wellness domain. No health records are uploaded or persisted by this native catalog.
- `Dropaul`, `Dilly` and `Prossee` do not run queued tasks or processes through catalog lookup alone.
- Registry arity validation is not a substitute for typed argument validation, authorization or input validation in a future handler.
- Existing Kora utility functions and the Python product host remain compatible; this native catalog is a separate API surface.

## Tests

The CMake target `reaper-capability-tests` checks module cardinality, all 108 registrations, lookups, arity rejection, buffer boundaries, non-mutating map behavior, alias-safe reversal, numeric validation, analytics and retry saturation.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```
