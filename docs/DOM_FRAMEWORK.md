# ДОМ — Reaper Fundamental Framework

**Document ID:** `reaper.dom.framework`  
**Architecture version:** 0.1  
**Status:** Architecture baseline; implementation not yet claimed  
**Maturity:** Genesis  
**Target language:** Reaper  
**Target runtime:** Reaper-native ДОМ runtime  
**Primary consumers:** Reaper applications, editors, system services and DAK components

## 1. Purpose and architectural decision

ДОМ is a fundamental framework of Reaper. It is the canonical application and system runtime contract for building, composing, running, supervising and updating Reaper programs.

ДОМ is not a collection of optional helper libraries and is not a second programming language. It is the standard runtime layer above Reaper language semantics and below applications and system products.

The framework has one canonical implementation, one public API family, one module contract, one lifecycle model and one compatibility policy. Applications must not create private, incompatible replacements for task scheduling, resource accounting, service communication, reactive state, startup or recovery.

The word **one** describes architectural ownership and compatibility, not a shared mutable address space:

- each process or explicitly defined isolation domain owns a runtime instance;
- applications may share the same ДОМ runtime implementation and ABI without sharing heaps, mutable globals, handles or privileges;
- cross-process cooperation uses explicit host services and versioned IPC;
- a process boundary remains the default isolation boundary for mutually untrusted applications.

### 1.1 Responsibility split

| Layer | Owns | Must not own |
|---|---|---|
| Reaper language and compiler | Syntax, types, effects, source diagnostics, HIR/MIR/LIR, canonical IR and code generation | Product-specific lifecycle policy |
| ДОМ | Application runtime, module composition, tasks, scopes, budgets, messaging, reactive updates, lifecycle and recovery | Language syntax or unrestricted kernel access |
| Host adapter | Explicitly granted OS services, handles and platform transport | Application business logic or implicit privilege |
| Application | Product behavior and its own domain model | Private replacement runtime services |
| DAK | Kernel, process isolation, device and desktop authority | A forked, incompatible copy of ДОМ semantics |

The compiler may validate and lower framework operations, but the running ДОМ runtime must not require the compiler to be resident. Compiled applications target a versioned ДОМ API/ABI.

### 1.2 Reaper-native implementation rule

All framework policy, contracts, subsystem logic and public examples are authored in Reaper. Existing Python reference-runtime code in the repository is current compatibility infrastructure; it is not the implementation target for ДОМ and does not establish native ДОМ support. Native readiness requires Reaper source, compiler/IR evidence, target-runtime tests and CI.

A small platform adapter may use an explicitly supported low-level backend where a host boundary requires it. Such an adapter must remain narrow, capability-gated and replaceable. It must not move ДОМ policy or subsystem implementations into Python or turn a C host adapter into a second framework runtime.

## 2. Runtime product, not a library bundle

A conforming ДОМ distribution consists of:

1. **ДОМ Core** — runtime identity, instance context, module registry, capability checks, diagnostics, execution scopes and shared internal contracts.
2. **Eight integrated subsystems** — JLOM, poooVERTY, Uu, JennyFlash, Jenny Flashing Boy, System Carriere, Nonconcrete and Establish.
3. **Public API and ABI** — stable versioned entry points for applications, editors and system services.
4. **Host adapter contract** — explicit bindings to the host OS, simulator or DAK.
5. **Runtime profiles** — reproducible feature sets assembled from the same implementation.
6. **Conformance suite** — Reaper tests, IR/Span golden files, fault tests, compatibility tests and integration fixtures.

A consumer depends on the public ДОМ API, not on private paths inside individual subsystem implementations. The public surface is versioned independently from internal module layout.

### 2.1 Runtime topology

~~~mermaid
flowchart TB
    subgraph Consumers["Consumers"]
      APP["Reaper applications"]
      EDITOR["Editors and workbenches"]
      SERVICE["System services"]
      DAK["DAK components"]
    end

    subgraph DOM["ДОМ runtime instance"]
      CORE["ДОМ Core"]
      UU["Uu"]
      NC["Nonconcrete"]
      PV["poooVERTY"]
      JLOM["JLOM"]
      SC["System Carriere"]
      JF["JennyFlash"]
      EST["Establish"]
      JFB["Jenny Flashing Boy"]
      CORE --- UU
      CORE --- NC
      CORE --- PV
      CORE --- JLOM
      CORE --- SC
      CORE --- JF
      CORE --- EST
      JFB -. "development profile only" .-> CORE
    end

    HOST["Versioned Reaper Host API"]
    OS["Host OS / DAK adapter"]

    APP --> CORE
    EDITOR --> CORE
    SERVICE --> CORE
    DAK --> HOST
    CORE --> HOST
    HOST --> OS
~~~

The diagram describes ownership and call direction. It does not imply that all consumers share one process, address space or runtime instance.

## 3. The eight integrated subsystems

Each subsystem has a single primary responsibility, a public contract, private implementation, diagnostics, tests and an explicit dependency list.

### 3.1 Uu — universal foundational types and utilities

Uu is the lowest-level shared foundation. It owns only reusable, deterministic primitives:

- identifiers, versions and stable names;
- byte and text operations with explicit encoding;
- bounded collections and ranges;
- unit values, sizes and durations;
- canonical paths and validated path values;
- common option/result support where the language does not already provide it.

Uu must not import another ДОМ subsystem, perform host I/O, allocate unbounded storage or hide global mutable state. Domain-specific helpers belong to their owning subsystem.

### 3.2 Nonconcrete — contracts and abstraction

Nonconcrete defines the seams between implementations:

- typed subsystem and host contracts;
- provider and adapter contracts;
- contract and schema versioning;
- compatibility validation;
- capability declarations;
- dependency graph validation;
- explicit effect requirements.

It is not a global service locator. Dependencies must be declared and resolved during composition. A consumer receives the contract it needs; it does not search a mutable global registry at arbitrary points in execution.

### 3.3 poooVERTY — resource economy and budget control

poooVERTY is the authority for declared and measured runtime budgets:

- memory and allocation budgets;
- CPU time and task concurrency limits;
- queue, message and buffer bounds;
- file, socket and other host-handle quotas;
- I/O and deadline budgets;
- admission control and backpressure;
- pressure telemetry and bounded degradation policies.

A budget is not a security sandbox and an estimate is not a physical process limit. Host-enforced isolation remains the host's responsibility. Exceeded budgets return structured errors or apply a declared degradation policy; they must not silently disable safety checks.

### 3.4 JLOM — job, object and lifecycle management

JLOM owns the lifetime of runtime work:

- object and module instance registration;
- task creation, scheduling and joining;
- structured task scopes and ownership;
- cancellation propagation and deadlines;
- supervision and restart policy;
- dependency-aware start and stop ordering;
- cleanup and terminal-state accounting.

Every task belongs to an explicit scope and has an owner, resource budget, cancellation policy and failure policy. JLOM schedules work under poooVERTY admission decisions; it does not maintain a competing resource ledger.

Canonical lifecycle:

~~~text
Declared -> Resolved -> Prepared -> Running -> Ready
                                      |
                                      v
                               Quiescing -> Stopped
                                      |
                         failure ----+----> Failed
                                      |
                                Recovering
~~~

Invalid transitions are rejected. Recovery is explicit and bounded. A component is not reported as Ready until its declared dependencies and startup invariants hold.

### 3.5 System Carriere — service and communication fabric

System Carriere owns typed communication between modules and services:

- service registration and endpoint discovery within an application boundary;
- command, query and event dispatch;
- schema-checked message envelopes;
- correlation and trace propagation;
- local IPC adapters;
- delivery, retry, deadline and backpressure policy;
- sender/recipient authorization through capabilities.

Delivery semantics must be declared per channel or operation: best-effort, at-most-once or at-least-once. At-least-once consumers must be idempotent or deduplicate by a stable message identifier. The framework must not promise global exactly-once delivery or global ordering.

System Carriere does not become an implicit network stack. Network transport is unavailable unless a host capability and explicit adapter are supplied.

### 3.6 JennyFlash — reactive state engine

JennyFlash owns the reactive dependency graph:

- typed signals and derived values;
- dependency registration and invalidation;
- deterministic update batches;
- incremental recomputation;
- transactional state updates;
- snapshots and change records;
- bounded propagation and cycle detection.

JLOM supplies execution scopes and scheduling. poooVERTY limits propagation queues and computation. JennyFlash must not introduce a private scheduler or unbounded notification queues. Update ordering and snapshot consistency are part of the public contract.

### 3.7 Establish — composition and runtime bootstrap

Establish is the composition root of ДОМ. It turns a validated application manifest into a running runtime instance:

- manifest parsing and validation;
- module and version resolution;
- dependency graph construction and cycle rejection;
- profile and configuration resolution;
- capability request verification against host grants;
- resource budget admission;
- deterministic prepare/start ordering;
- readiness checks;
- coordinated quiesce, shutdown and recovery.

No other subsystem may depend on Establish. Establish depends on the public contracts of the subsystems and wires concrete implementations once. It does not contain application business logic.

### 3.8 Jenny Flashing Boy — development control plane

Jenny Flashing Boy is the development-only control plane for a running ДОМ instance:

- live preview and runtime inspection;
- source-to-runtime change tracking;
- incremental rebuild coordination;
- compatible hot reload;
- state migration and snapshot restoration;
- failed-reload rollback;
- debugger and editor bridges.

Jenny Flashing Boy is optional and excluded from production profiles. It may only use declared debug capabilities. Hot reload is allowed only when module ABI, active scopes, resource ownership and state migration checks pass. It must never replace live code underneath active unsafe operations or bypass lifecycle coordination.

## 4. Dependency direction and ownership

The dependency graph is deliberately acyclic:

~~~mermaid
flowchart TD
    U["Uu"]
    N["Nonconcrete"]
    P["poooVERTY"]
    J["JLOM"]
    S["System Carriere"]
    F["JennyFlash"]
    E["Establish"]
    B["Jenny Flashing Boy"]

    U --> N
    U --> P
    N --> P
    U --> J
    N --> J
    P --> J
    J --> S
    P --> S
    N --> S
    U --> S
    J --> F
    P --> F
    N --> F
    U --> F
    U --> E
    N --> E
    P --> E
    J --> E
    S --> E
    F --> E
    E -. "development control contract" .-> B
    J -. "debug and reload contracts" .-> B
    F -. "reactive inspection contract" .-> B
~~~

Arrows show dependency direction (the target depends on the source). Establish is the only composition root. Jenny Flashing Boy depends on narrow development contracts and is never a production dependency.

The following rules are normative:

1. Uu has no dependency on any other ДОМ subsystem.
2. No subsystem imports private implementation details from another subsystem.
3. No subsystem except Establish performs global composition or startup ordering.
4. No subsystem creates a competing scheduler, resource ledger, message bus or reactive graph.
5. Cross-subsystem calls use versioned contracts and typed results.
6. Optional features are represented as explicit capabilities or profile selections, never ambient runtime discovery.
7. A dependency cycle is a build-time architecture error.

## 5. Public contracts and compatibility

The initial public contract family is:

| Contract ID | Purpose |
|---|---|
| `reaper.dom.runtime.v1` | Runtime instance creation, identity, lifecycle and public API |
| `reaper.dom.module.v1` | Module metadata, dependencies, exports and lifecycle hooks |
| `reaper.dom.manifest.v1` | Application and runtime composition description |
| `reaper.dom.capability.v1` | Requested capability, host grant and scope |
| `reaper.dom.resource-budget.v1` | Resource ceilings, accounting units and admission rules |
| `reaper.dom.message.v1` | Typed message, correlation, deadline and delivery metadata |
| `reaper.dom.reactive.v1` | Signal, dependency and transactional update semantics |
| `reaper.dom.diagnostics.v1` | Stable diagnostic codes, source spans and runtime context |
| `reaper.dom.dev-control.v1` | Development-only inspection and reload boundary |

The identifiers are proposed initial contract names, not claims that these APIs already exist.

### 5.1 Compatibility rules

- Public contracts are versioned independently from internal implementation.
- Additive compatible changes may remain within a major version when semantics remain unchanged.
- Removing, renaming or changing the meaning of a public field, operation or invariant requires a new major contract version or a documented migration period.
- The runtime reports its ABI/API version and supported contract ranges.
- A consumer must validate compatibility before activation.
- Host-specific handles are opaque, typed, scoped and validated by the host.
- Unknown fields may be ignored only where the relevant schema explicitly permits it; unknown required operations fail closed.

### 5.2 Application manifest

The manifest is declarative input to Establish. The schema must be versioned and validated before any module is activated.

~~~json
{
  "schema": "reaper.dom.manifest.v1",
  "application": {
    "id": "example.application",
    "version": "0.1.0",
    "entry_module": "app.main"
  },
  "runtime": {
    "api": "reaper.dom.runtime.v1",
    "profile": "standard"
  },
  "modules": [
    {
      "id": "app.main",
      "version": "0.1.0",
      "requires": ["storage.read"]
    }
  ],
  "resources": {
    "memory_bytes": 16777216,
    "max_tasks": 32,
    "max_queue_items": 256,
    "max_open_handles": 16
  },
  "lifecycle": {
    "startup": "dependency_order",
    "shutdown": "reverse_dependency_order"
  }
}
~~~

Manifest declarations request capabilities; they do not grant them. The host independently supplies the effective capability set. The example is illustrative and is not yet a validated repository schema.

## 6. Runtime profiles

Profiles are configurations of the same ДОМ implementation, not forks.

| Profile | Intended use | Included surface |
|---|---|---|
| `core` | Minimal deterministic programs | Uu, Nonconcrete, Establish and the minimum execution contracts |
| `standard` | Ordinary applications and editors | Core plus JLOM, poooVERTY, System Carriere and JennyFlash |
| `system` | DAK/system services | Standard plus explicitly granted host-service adapters and stricter resource policy |
| `development` | Reaper Studio and debugging | Standard plus Jenny Flashing Boy and debug-only capabilities |
| `embedded` | Constrained targets | Bounded subset chosen at build time; no dynamic loading unless target support is proven |

A profile cannot silently add privileges. Feature absence is explicit and validated during Establish. Production builds must not include Jenny Flashing Boy unless the operator explicitly builds a development image.

## 7. Isolation, authority and DAK integration

ДОМ follows default-deny capability policy:

- the application manifest declares requested capabilities;
- the host decides what to grant;
- the runtime binds grants to an application, process, service or resource scope;
- a subsystem cannot elevate its own authority;
- capabilities are not inherited by unrelated tasks unless the contract explicitly permits scoped delegation;
- denied operations return diagnostics before dispatch.

The DAK integration boundary is a Reaper host adapter over versioned host contracts, including the existing Reaper System Runtime ABI and DABI64 Desktop Host specifications where applicable. ДОМ must not issue raw syscalls, access physical memory, load drivers or mutate privileged OS state directly. Kernel identity, handles and authorization are derived from trusted DAK host state, not from caller-supplied message fields.

DAK applications and services use the same public ДОМ API and compatibility rules. They do not each invent private lifecycle, scheduler, message or reactive subsystems. Isolation remains per process or trust domain; sharing the ДОМ implementation does not mean sharing mutable application state.

## 8. Failure, diagnostics and observability

Every failure has a structured diagnostic with:

- stable code and owning subsystem;
- severity and failure category;
- source `Span` and SourceMap reference where source-originated;
- runtime instance, application, module and task identifiers;
- correlation/trace identifier where applicable;
- bounded contextual fields that do not expose secrets;
- explicit retryability and recovery disposition.

Initial code families:

| Prefix | Owner |
|---|---|
| `DOM-E0xxx` | Core and composition |
| `DOM-E1xxx` | JLOM |
| `DOM-E2xxx` | poooVERTY |
| `DOM-E3xxx` | Uu |
| `DOM-E4xxx` | JennyFlash |
| `DOM-E5xxx` | Jenny Flashing Boy |
| `DOM-E6xxx` | System Carriere |
| `DOM-E7xxx` | Nonconcrete |
| `DOM-E8xxx` | Establish |

Subsystems emit structured events and bounded metrics through the core observability contract. Logs must not contain credentials, secret material or unrestricted payload dumps. Health, readiness and liveness are distinct signals. A component that has failed a critical invariant is not reported Ready.

## 9. Reaper compiler and language integration

The framework is implemented in Reaper and compiled through the canonical Reaper pipeline:

- source modules use `.rpr` and explicit import/export boundaries;
- compiler checks validate module contracts, effects, capabilities and resource declarations;
- diagnostics preserve `Span` and SourceMap provenance;
- HIR/MIR/LIR and canonical IR define the lowering boundary;
- runtime entry points use versioned ДОМ API/ABI contracts;
- host operations are lowered only through declared capability-gated bindings;
- ownership, borrow/region and no-allocation guarantees are required where the target profile needs them.

The final source syntax and exact function signatures must be validated against the current Reaper grammar and type system before they are published as executable examples. This document defines architecture and semantics, not new unimplemented language syntax.

The current repository describes Python as the compatibility reference and native compiler/runtime parity as incomplete. That status must remain accurate until native Reaper compilation, execution and conformance tests prove otherwise. ДОМ itself is not considered implemented merely because a Python reference host, C ABI catalogue or manifest document exists.

## 10. Conformance and verification

A ДОМ release must pass evidence-backed gates in the following areas:

| Area | Required evidence |
|---|---|
| Contract integrity | Schema validation, version compatibility and negative cases |
| Dependency graph | Deterministic resolution and cycle rejection |
| Lifecycle | Valid/invalid transition tests and ordered shutdown |
| Tasks | Scope ownership, cancellation, deadlines and supervision |
| Resources | Admission, quota boundaries, exhaustion and backpressure |
| Communication | Envelope validation, delivery semantics, deduplication and authorization |
| Reactive state | Deterministic ordering, batching, cycles and snapshot consistency |
| Security | Default-deny, scope isolation and host adapter denial tests |
| Recovery | Fault injection, bounded restart, rollback and clean shutdown |
| Compiler | Reaper source tests, IR/Span golden tests and diagnostics |
| Compatibility | API/ABI matrix across supported runtime versions |
| DAK integration | Adapter tests against a real or explicitly identified simulator host |

Required test classes are Reaper-native contract tests, compiler/IR/Span golden tests, target-runtime integration tests, fault-injection tests and cross-repository adapter tests. CTest may validate a narrow native host adapter; it does not replace Reaper-level framework tests. Python tests may continue to validate the repository's existing compatibility infrastructure, but they cannot be the proof of a Reaper-native ДОМ implementation.

## 11. Repository implementation layout

The target source layout is:

~~~text
dom/
  core/
    contracts/
    diagnostics/
    capabilities/
    runtime/
    observability/
  Uu/
  Nonconcrete/
  poooVERTY/
  JLOM/
  System-Carriere/
  JennyFlash/
  Establish/
  Jenny-Flashing-Boy/
  host/
    simulator/
    dak/
  profiles/
  manifests/
  tests/
    contracts/
    compiler/
    lifecycle/
    resources/
    messaging/
    reactive/
    recovery/
    compatibility/
  examples/
~~~

Runtime and subsystem policy source is Reaper. Generated artifacts, IR fixtures and narrow host adapters are kept in clearly separated directories. Development-only source is not linked into production profiles.

## 12. Delivery sequence and maturity gates

Implementation is delivered as separate reviewable changes with explicit dependencies. Each subsystem has its own contract, source, tests, documentation and CI evidence. Main remains protected; changes are reviewed and squash-merged sequentially.

1. **Genesis — architecture baseline.** Define contracts, dependency graph, threat boundaries, public API inventory and conformance plan. This document is the architecture baseline only.
2. **Foundation — executable core.** Implement Uu, diagnostics, capability primitives, Nonconcrete contracts and a minimal Reaper-native runtime instance.
3. **Evolution — composition.** Implement Establish, manifest validation, deterministic module resolution and profile assembly.
4. **Ascension — resources and lifecycle.** Implement poooVERTY and JLOM with task scopes, budgets, cancellation and supervision.
5. **Vanguard — communications.** Implement System Carriere local messaging, service registry and delivery policies.
6. **Frontier — reactive runtime.** Implement JennyFlash and prove deterministic state propagation.
7. **Dominion — development control plane.** Implement Jenny Flashing Boy with compatible reload, snapshots and rollback.
8. **Apex — product adoption.** Migrate a Reaper application and editor to the shared runtime without private runtime replacements.
9. **Zenith — DAK integration.** Validate host adapters, capability enforcement and process isolation on the DAK target.
10. **Singularity — ecosystem conformance.** Enforce the ДОМ contract across applications, editors and system services with compatibility, upgrade and recovery evidence.

A maturity name is not a marketing label. A stage is reached only when its exit criteria have source, tests, target-runtime evidence, CI and auditable artifacts. No stage beyond Genesis is claimed by this architecture document.

## 13. Non-goals

ДОМ does not:

- replace Reaper language, compiler or canonical IR;
- create a universal shared heap for unrelated applications;
- grant host capabilities merely because a manifest requests them;
- guarantee exactly-once distributed delivery;
- treat resource estimates as a security boundary;
- require a network service for local application execution;
- make hot reload available in production by default;
- claim full native support before the Reaper compiler and target runtime prove it;
- duplicate the DAK kernel, device manager or privileged service implementation.

## 14. Acceptance criteria for the architecture baseline

This baseline is ready for implementation planning when reviewers can verify that:

- the eight subsystems have distinct, non-overlapping ownership;
- the dependency graph is acyclic and Establish is the sole composition root;
- public runtime, module, manifest, capability, resource, message, reactive and diagnostic contracts are identified;
- runtime instances remain isolated while sharing one canonical implementation;
- DAK integration is capability-gated through explicit host adapters;
- development-only hot reload is separated from production runtime;
- Reaper is the implementation language and native readiness gates are explicit;
- current repository limitations are stated without presenting the framework as shipped.

**Implementation status:** no executable ДОМ subsystem is claimed by this document. The next implementation change must establish the Reaper-native foundation and executable contract tests before consumers are migrated.
