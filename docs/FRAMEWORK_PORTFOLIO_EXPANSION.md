# Reaper Framework Portfolio and Expansion Programme

**Portfolio schema:** reaper.framework-portfolio.v1  
**Implementation language target:** Reaper (.rpr)  
**Scale target:** 50,000 qualified production Reaper LOC per independently owned framework module  
**Truth rule:** proposals, manifests, operation signatures, generated catalogues and documentation are not executable handlers.

## 1. Portfolio topology

All first-party Reaper frameworks belong to one ecosystem, but not all are peers in the runtime architecture.

1. ДОМ is the single foundational application/system runtime.
2. Its eight subsystems own lifecycle, resources, contracts, communication, reactive state, composition and development control.
3. The eight Reaper framework modules provide focused domain algorithms and language/workbench facilities.
4. The twenty Framework Federation namespaces are separately versioned domain extension contracts. Their operation handlers must be implemented before their status can be promoted.
5. Native Framework Core is a host-side extension registry/activation mechanism. It is not a second application runtime and must not compete with ДОМ.
6. Jora is an application composition/scaffolding service, not a runtime.
7. Kora is a separate utility/plugin host surface with a Python runtime and Lua ReaScript integrations; it is not a Reaper-native ДОМ subsystem.
8. The Native Capability Suite and System Runtime ABI are distinct native host surfaces. Reaper source-level bindings and host providers remain separate gates.
9. Java Capability Adoption, Engineering Evolution and Quality/Commercial Readiness are engineering programmes and policy frameworks, not application runtimes.

## 2. ДОМ — canonical runtime foundation

| Subsystem | Normative owner | Responsibility | Initial implementation status |
|---|---|---|---|
| Uu | ДОМ Core | Identifiers, collections, bounded primitives and common values | Initial Reaper source slice |
| Nonconcrete | Contract layer | Contracts, adapters, versions, capability requirements and compatibility | Initial Reaper source slice |
| poooVERTY | Resource authority | Memory/task/queue/handle budgets, admission and backpressure | Initial Reaper source slice |
| JLOM | Execution authority | Object lifecycle, task scopes, cancellation and supervision | Initial Reaper source slice |
| System Carriere | Communication authority | Service registry, envelopes, commands, queries, events and IPC adapters | Envelope and endpoint-validation slice |
| JennyFlash | Reactive authority | Signals, derived state, dependencies, transactions and propagation | Versioned-signal/update-batch slice |
| Jenny Flashing Boy | Development control plane | Inspection, live preview, safe reload, snapshots and rollback | Reload-plan authorization slice |
| Establish | Composition root | Manifest, module resolution, capability and profile validation, startup/shutdown | Initial manifest/dependency resolver |
| ДОМ Core | Runtime product | Runtime identity, instance assembly, public API and host boundary | Initial runtime composition slice |

Establish is the sole composition root. The other subsystems must not create competing global registries, task schedulers, resource ledgers, message buses or reactive graphs. Jenny Flashing Boy is development-profile-only and must not be a production dependency.

## 3. Eight standalone Reaper framework modules

| Framework | Canonical owner/integration | Primary responsibility |
|---|---|---|
| GalHero | Establish adapter | Deterministic dependency graph validation and topological ordering |
| Call-and-Back | System Carriere adapter | Synchronous callback registration, priority dispatch and one-shot handlers |
| Stacked Options | Establish configuration adapter | Layered configuration resolution and validation |
| PerenosiMOST | Reaper language tooling | Exact Russian MOST alias mapping and support-state classification |
| MOST | Reaper language tooling | Stable public facade over the same canonical alias table; not a second grammar |
| Blau | JennyFlash adapter | Immutable versioned snapshots, compare-and-set and value diffs |
| Shashio | JLOM/application domain adapter | Finite-state transitions and atomic event sequences |
| Showel Fleppery CODE | Jenny Flashing Boy/tooling adapter | Validated in-memory source transformation pipelines and deterministic templates |

The module set and the ДОМ runtime have separate ownership. An application may use these modules through explicit adapters; ДОМ must not copy their implementations into its core.

## 4. Twenty Framework Federation namespaces

| ID | Namespace | Domain | Initial integration owner |
|---:|---|---|---|
| 001 | CodexNo | Compiler and language feature catalog | Reaper compiler/tooling |
| 002 | Joint Baby | Cross-language composition and ABI binding | Nonconcrete |
| 003 | Correpse | Contracts, consistency and reconciliation | Establish / Nonconcrete |
| 004 | Allocate Purpose | Memory, allocation and resource budgets | poooVERTY |
| 005 | Collillioi | Collections and deterministic algorithms | Uu |
| 006 | Aspdoi | Asynchronous tasks and structured scheduling | JLOM |
| 007 | ASJIOP | ABI, serialization and binary layouts | Nonconcrete / host ABI |
| 008 | ALLLLL | Language feature registry and compatibility | Reaper compiler/tooling |
| 009 | Zabor | Capability grants and policy scopes | Nonconcrete |
| 010 | Vjinz | Source maps, diagnostics and tracing | Reaper compiler / ДОМ diagnostics |
| 011 | SupremeBoy | Quality gates and release evidence | Engineering/CI |
| 012 | CheeNow | Channels, concurrency and back-pressure | JLOM / System Carriere |
| 013 | HumbleBumble | Result values, error taxonomy and recovery | Uu / JLOM |
| 014 | Hub2 | Service discovery and event distribution | System Carriere |
| 015 | Kloz | Modules, packages and dependency lifecycle | Establish |
| 016 | CO | Core primitives and deterministic identity | Uu |
| 017 | CrippleBO | Fault records and resilience policies | JLOM |
| 018 | RippleCripple | Reactive streams and flow control | JennyFlash |
| 019 | Secator | Security policy and secret references | Nonconcrete / host security adapter |
| 020 | PollATIA | Public statistics and privacy-aware metrics | ДОМ observability |

The 120 function entries in the registry are operation contracts. A metadata helper or signature is not a domain handler. Each operation needs a typed Reaper implementation, source diagnostics, capability/effect checks, negative tests and target-runtime evidence.

## 5. Native Framework Core profiles

The separate C17 Framework Core proposal defines five declarative profiles: CodexNo, Joint Baby, Correpse, Allocate Purpose and Collillio. They are metadata/extension contracts, not complete domain implementations. The API currently accepts trusted in-process callbacks and does not load arbitrary packages or provide an OS sandbox.

The Framework Core must be treated as a host registry and activation adapter. ДОМ remains the canonical runtime for applications and services. If both APIs are retained, a documented adapter must map typed manifests and lifecycle operations without creating two authorities for the same instance.

## 6. Adjacent Reaper programmes and host surfaces

| Programme | Purpose | Boundary |
|---|---|---|
| Jora | Deterministic application composition and Reaper project scaffolding | Generates scaffolds; catalog packs are not completed editors or installable applications |
| Kora | 66 utility functions, plugin facades and Cockos REAPER Lua scripts | Separate Python utility runtime and Lua ReaScript host; not Reaper-native ДОМ |
| Native Capability Suite | 18 module descriptors and 108 operation contracts plus selected numeric primitives | C17 native registry; registered signatures do not mean every handler exists |
| System Runtime ABI | 42 capability-gated host-operation descriptors | C17 host dispatch boundary; per-OS adapters and .rpr bindings are separate |
| DAK System Services | SysCore, NeuroLink and VirtHost system-service contracts | Contract-only until compiler bindings, DAK providers and target tests exist |
| Java Capability Adoption | Clean-room adaptation of useful type, runtime, concurrency, tooling and package practices | Reaper remains its own language/runtime; no JVM or copied Java source |
| Engineering Evolution | 20 engineering domains and 40 practices | Governance and acceptance policy, not product runtime |
| Quality / Commercial Readiness | 60 quality, execution and commercial controls | Evidence framework; it does not certify runtime behavior or profitability |

## 7. Fifty-thousand-line growth standard

The requested scale is a target for independently owned implementation modules, not a reason to inflate source files.

- Target per first-party framework module: 50,000 qualified production Reaper LOC.
- The 8 ДОМ subsystems each receive their own target.
- The 8 standalone Reaper framework modules each receive their own target.
- The 20 Federation namespaces each receive their own target after their public operation contracts and domain boundaries are reviewed.
- The 14 canonical language/compiler/runtime subsystems are separately governed by the existing 700,000-line programme in NATIVE_REAPER_EXPANSION_50000.md.
- Five Native Framework Core profiles are not counted as five additional runtime implementations; they are descriptors for domain extension surfaces.
- Adjacent programmes such as Jora, Kora and governance matrices are not counted as Reaper-native runtime implementation unless their own Reaper source module is explicitly established.

A line qualifies only when it is first-party executable Reaper code, owned by one subsystem, reachable from its public API, non-duplicated, non-generated and covered by positive, negative, boundary and regression tests. Exclude comments, blank lines, docs, fixtures, generated registries, templates, copied code, host-language implementation and unreachable placeholders.

Do not report a module as complete when it reaches 50,000 LOC. Completion also requires stable contract/versioning, diagnostics with Span/SourceMap, compatibility tests, resource bounds, security review, CI, native compiler/runtime evidence and integration.

## 8. Delivery order

1. ДОМ Foundation: Uu, Nonconcrete and runtime contract primitives.
2. ДОМ Composition: Establish and profile/manifest resolution.
3. ДОМ Execution: poooVERTY and JLOM.
4. ДОМ Communication: System Carriere.
5. ДОМ Reactive: JennyFlash.
6. ДОМ Development: Jenny Flashing Boy.
7. Standalone eight-framework hardening and explicit ДОМ adapters.
8. Federation namespaces implemented by owning subsystem, six or more operations at a time with end-to-end evidence.
9. Native Framework Core adapter review; resolve duplicate lifecycle ownership before adoption.
10. Migrate one real Reaper application, one editor workflow and one system service through ДОМ.
11. DAK host adapter and cross-repository conformance.
12. Continue the 14-subsystem language expansion without mixing framework LOC into language frontend/compiler totals.

Every step is a separate reviewable PR. Preserve protected main, Conventional Commits, required CI, compatibility and evidence-based maturity. A stacked PR is not shipped until its base PR is merged and its own checks pass.
