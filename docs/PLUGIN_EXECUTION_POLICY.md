# Built-in plugin execution policy

Reaper's product plugins are in-process adapters over the approved product
registry. This change borrows operational practices from Spring Boot,
Quarkus/Micronaut and MicroProfile without introducing a second runtime or a
web server.

## Host-owned policy

`PluginExecutionPolicy` configures:

| Parameter | Default | Bound |
|---|---:|---:|
| `max_input_bytes` | 4 MiB | 1 B–64 MiB |
| `max_output_bytes` | 8 MiB | 1 B–128 MiB |
| `max_runtime_ms` | 30,000 ms | 1 ms–10 min |
| `max_concurrent_per_plugin` | 4 | 1–64 |

Arguments and results are checked as finite JSON-compatible data. Dispatch
uses per-plugin bounded admission. Every accepted invocation records a
correlation-independent local execution count, duration, result status,
failure and in-flight state.

`PluginManager.health()` returns `reaper.plugin-health.v1`, with readiness
based on the built-in product registry and a metrics snapshot per plugin.
It is a local registry/handler readiness report, not proof that every external
toolchain, database, network dependency or product integration is healthy.

## Deadline semantics

The Python product handlers are synchronous. The runtime budget is therefore
an *observed post-return deadline*: if a handler returns after the configured
budget, Reaper rejects its result and records the late execution. The manager
does not pretend it can safely terminate a Python call mid-operation.

A future hard deadline would require cooperative cancellation or isolated
worker processes with bounded IPC, cleanup and a cancellation contract.

## Framework capability crosswalk

| Java capability | Reaper adaptation |
|---|---|
| Spring IoC / DI | Explicit manager, registry, policy and product operation dispatch |
| Spring Boot Actuator | Plugin readiness and invocation health snapshot |
| Quarkus / Micronaut | Static product descriptors and validation before dispatch |
| MicroProfile Health / Config | Stable local health schema and explicit host policy values |
| Resilience4j bulkhead | Per-plugin bounded semaphores |
| Resilience4j timeout | Observed deadline; not forceful cancellation |
| OpenTelemetry | Local duration/status counters; no OTLP exporter or remote service is claimed |
| Hibernate / jOOQ / MyBatis | Not applicable to the current in-memory product dispatcher; no database added |
| Netty / Vert.x / Camel | Not applicable to this synchronous local plugin host |

This policy is orthogonal to the language front-end work in
[Mixed syntax and locale profiles](POLYGLOT_SOURCE_PROFILES.md): both use the
same Reaper repository and canonical product/runtime boundaries.

## Verification

```sh
python -m unittest tests.test_plugins -v
python -m unittest discover -s tests -v
```

The regression tests for byte limits, concurrency admission and metrics are
part of the adaptation branch and require CI before merge.
