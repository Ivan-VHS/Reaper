# Reaper Framework Core v1

**Implementation:** C17 host library  
**Header:** include/reaper/framework.h  
**Library:** reaper_framework  
**Public contract:** reaper.framework-manifest.v1  
**Host ABI:** 1.0

Framework Core is a bounded native host API for registering trusted Reaper extensions, validating their manifests, resolving a dependency graph and managing an explicit lifecycle. It complements, rather than replaces, the current Python reference runtime, Kora helpers, Jora composition graph, Capability Suite, System Runtime and DABI64 contracts.

## What is implemented

- Caller-owned registry with a fixed maximum of 32 registered manifests and no heap allocation inside the registry.
- Stable framework IDs, display names, descriptions, semantic versions and host ABI checks.
- Dependency constraints with inclusive minimum and optional exclusive maximum versions.
- Duplicate dependency rejection, declared conflict checks, missing-dependency and version-mismatch diagnostics.
- Deterministic topological resolution. When multiple nodes are ready, the lexicographically smallest stable ID is selected.
- Capability-mask validation against the existing System Runtime capability vocabulary. A framework receives only its manifest's required, already-granted capability bits.
- Explicit start and stop callbacks for executable, trusted host extensions.
- Reverse-order shutdown and rollback of already-started extensions if a later start callback fails.
- Stable entry-state inspection and registry counters for registrations, resolutions, activations, deactivations, failures and rollback stops.
- Five built-in declarative profiles and native CLI inspection commands.

The registry is intentionally allocation-free and does not provide hidden threads or locks. The host serializes registry operations. Manifest data, its strings and arrays, callback code and callback context must remain alive while registered. Registering a new item invalidates a prior resolution and requires a fresh resolve before activation.

## Lifecycle

~~~text
typed manifest
    -> manifest validation
    -> registration
    -> dependency and capability resolution
    -> deterministic topological order
    -> explicit activation callbacks
    -> reverse-order deactivation
~~~

A declarative-only manifest has no callbacks and is never reported as an active executable plugin. It can describe providers and extension points for later composition. An executable manifest must supply both start and stop callbacks. This API accepts trusted in-process host code; it does not discover dynamic libraries or execute untrusted binaries.

On activation failure, the failed extension becomes failed. Previously started extensions are stopped in reverse activation order. A successful rollback records stopped entries; a failed rollback stop is recorded as a failed entry and increments the callback failure counter. The caller receives a structured error containing the failing ID and a stable status code.

## Manifest shape

The C interface is the executable host contract. The JSON Schema and built-in JSON catalogue are versioned interchange/documentation contracts; v1 does not parse JSON files into executable callbacks and does not install them.

A manifest declares:

- ID, display name, version and host ABI version.
- Required dependencies with version intervals.
- Optional conflicts.
- Provided capability names and named extension points.
- Required Reaper System Runtime capability bits.
- Lifecycle mode and trusted host callbacks.

Version ranges use semantic-version numeric comparison: minimum is inclusive; a non-zero maximum is exclusive. A zero maximum means no upper bound. Prerelease/build metadata is not part of v1.

The stable JSON schema is at schemas/framework-manifest.v1.schema.json. The five built-in descriptors are mirrored in frameworks/catalog.v1.json. The host API currently registers the compiled C descriptors returned by reaper_framework_builtin_at().

## Built-in extension domains

| Profile | Responsibility | Initial extension points |
|---|---|---|
| CodexNo | Framework scaffolding, compiler/backend extensions and source metadata | compiler backend, source generator, workspace scaffold |
| Joint Baby | Cross-language adapters, serialization and host ABI bindings | language adapter, host ABI, serialization |
| Correpse | Composition graphs, dependency resolution and lifecycle policy | composition node, composition policy, framework lifecycle |
| Allocate Purpose | Resource budgets, allocation policy and bounded pools | resource allocator, resource budget, resource pool |
| Collillio | Public statistics, telemetry processing and observability export | telemetry exporter, telemetry processor, registry statistics |

All five are currently declarative-only. Their descriptors make extension contracts discoverable; they do not claim to provide a complete compiler generator, language bridge, workflow engine, allocator service or telemetry backend. Correpse depends on Allocate Purpose v1 or later, which demonstrates versioned dependency resolution in the built-in graph.

## Native commands

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure

build/reaper-c --frameworks
build/reaper-c --framework correpse
~~~

The CTest suite covers profile discovery, deterministic dependency ordering (including Allocate Purpose before Correpse), lifecycle callbacks, rollback, dependency errors, version constraints, conflicts, ABI mismatch, capability denial, invalid manifests and statistics. Statistics expose total registry size separately from mutually exclusive per-state counts.

## Capability and security model

Framework Core does not mint privileges. Its registry receives a capability grant mask from its trusted host, and every manifest is rejected if its required bits exceed that grant. The existing System Runtime remains responsible for actual host dispatch and per-operation checks. Framework registration does not open files, create processes, access the network, map MMIO, install drivers, or call privileged DuckOS services by itself.

The native callbacks are in-process trusted code, not a sandbox. A host must only register reviewed extensions built for the matching ABI. Dynamic-library loading, package signatures, publisher identity, key rotation and isolation are not included in v1. A JSON digest alone would not authenticate a publisher.

## Interoperability and 2026 direction

The extension model is designed to leave room for a Reaper-owned typed adapter layer. The WASI Component Model is a compatibility target to study for language-neutral component interfaces, versioned imports/exports and asynchronous calls; it is not a runtime dependency in this release. The OpenTelemetry semantic conventions are the naming reference for future metric, trace and log exporters; Collillio currently exposes only those extension contracts, not an exporter implementation.

The language front end must later add source-level declarations/imports and connect them to the same typed manifests, with canonical IR and Span/SourceMap diagnostics preserved. Do not add an alternate ad-hoc plugin syntax or expose native pointers in DABI64 wire frames. Direct .rpr framework declarations, native dynamic package loading, WASI component execution, asynchronous task orchestration and persistent registry storage are explicit future gates.

## Compatibility

- Existing Kora API and Python reference runtime are untouched.
- Existing 18-module / 108-operation Capability Suite is untouched.
- Existing System Runtime ABI v1 and DABI64 Desktop Host v1 remain the host-operation and wire-boundary contracts.
- No dependency on a cloud service, external registry, package server or dynamic loader is introduced.
- Native C17 code is compiled with the repository's warning policy and tested with CTest.
