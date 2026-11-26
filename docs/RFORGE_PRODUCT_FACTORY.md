# RForge — Reaper product composition factory

**Contract:** `reaper.rforge.product-factory.v1`  
**Status:** architecture proposal; executable RForge implementation is not present yet  
**Relationship:** general composition engine for Reaper; Jora remains the application-catalogue and application-generation experience

## 1. Purpose

RForge is a Reaper-first factory for designing and assembling complete software products from versioned capabilities and contracts. It generalises the existing Jora application-composition model without replacing or duplicating it.

RForge must be able to plan seven product families:

| Product kind | Contract meaning | Required composition shape |
|---|---|---|
| `framework` | Reusable framework or runtime foundation | Stable APIs, lifecycle, extension points, compatibility contract |
| `multitool` | A coordinated suite of tools | Independent tool identities, shared shell, typed tool routing and permission boundaries |
| `multiapp` | Multiple independent applications | Separate application roots and lifecycles connected only through declared contracts |
| `framework_bundle` | **Фреймворложения**: a framework-oriented application kit | One or more frameworks plus compatible application foundations, adapters and extension packs |
| `multiframe` | A composition of UI/workspace frames | Frame tree, navigation, state ownership, layout and lifecycle contracts |
| `multiwork` | A coordinated work system | Workspace, applications, tools, workflows, data contracts and explicit failure handling |
| `frame_app_tool_suite` | **Фреймприлотуллы**: a full frame/application/tool composition | Framework layer, application roots, tool suite and frame/workflow graphs in one product |

The labels `framework_bundle` and `frame_app_tool_suite` are the canonical machine identifiers for the two user-defined product families. Display labels remain localizable.

## 2. Relationship to Jora

The current Jora increment already provides deterministic application requests, a closed capability catalogue, dependency closure, conflict checks, topology alternatives, stable graph scoring, localization generation and staged scaffold output. Its first-party application packs are explicitly specification-only; generated scaffolds are not executable editors.

RForge builds on those concepts:

- Jora remains the application-focused catalogue, naming, composition and store-facing workflow.
- RForge becomes the general product-graph model and composition engine.
- Jora's existing `reaper.jora.request.v1` and `reaper.jora.application.v1` contracts remain valid. A Jora adapter maps an application request into the general RForge model; no silent schema replacement is permitted.
- Existing graph limits and deterministic tie-break rules are the initial compatibility profile. Any limit increase requires boundedness tests and a versioned contract change.
- The existing Jora CLI remains compatible. New generic operations use `reaper forge`; Jora may delegate to the shared engine after conformance tests pass.

RForge must not create a second catalogue, second dependency solver or competing graph implementation beside Jora. Shared algorithms should be extracted behind stable contracts, then consumed by both surfaces.

## 3. Core product model

RForge composes a typed graph. It does not concatenate arbitrary source files or executable binaries.

### 3.1 Component kinds

Every catalogue entry has an immutable identifier, semantic version, component kind, maturity, capability declarations and a versioned contract.

Initial component kinds:

- `framework` — runtime, library, framework or reusable foundation;
- `tool` — an independently addressable operation or tool;
- `application` — a separately named application root;
- `frame` — a UI, window, scene, panel or workspace frame;
- `workflow` — a deterministic process or orchestration definition;
- `adapter` — an explicit boundary to a host, service or external ABI;
- `asset` — a typed resource required by a component.

A component contract records:

- stable ID, version and compatibility range;
- provided and consumed capabilities;
- required, optional and conflicting dependencies;
- public interfaces and schema versions;
- lifecycle, state ownership and failure semantics;
- resource budgets and declared effects;
- filesystem, network, device and process permissions;
- implementation maturity, supported targets and provenance.

A catalogue record is not proof of implementation. Maturity must distinguish at least `specification_only`, `contract_only`, `source_generated`, `compiled`, `tested`, `installable` and `released`. Each transition requires evidence.

### 3.2 Graph node and edge types

Nodes carry stable identity, kind, version, maturity, target and contract hash.

Typed edges include:

- `requires` — hard dependency;
- `provides_to` — capability connection;
- `hosts` — framework or runtime hosting;
- `workflow_step` — ordered work step;
- `frame_child` — frame composition;
- `mounts` — application/tool registration;
- `event` — asynchronous message delivery;
- `extends` — a declared extension point;
- `validates` — a quality or policy gate.

Synchronous control and data dependencies must be acyclic. Feedback is allowed only through an explicitly asynchronous event boundary with bounded queues, delivery semantics and failure policy. Event edges must not be used to conceal a synchronous dependency cycle.

### 3.3 Product-specific invariants

**Frameworks**
- expose versioned public interfaces and explicit extension points;
- declare supported runtime/target combinations;
- define lifecycle, resource ownership and compatibility policy;
- do not absorb application-specific state into the framework core.

**Multitools**
- preserve a stable identity and permission scope for every tool;
- route calls through typed contracts;
- prevent a tool from inheriting another tool's privileges implicitly;
- support independent enablement, replacement and version pinning.

**Multiapplications**
- retain independent product identities, configuration and lifecycles;
- share data only through declared schemas and access policy;
- allow a composition to contain independently buildable applications.

**Фреймворложения**
- define framework dependency order and compatibility intersections;
- bind application foundations to explicit extension points;
- produce a reusable kit rather than one opaque application binary.

**Мультифреймы**
- separate frame structure from application business logic;
- define parent/child ownership, focus, navigation and state lifetime;
- validate layout constraints and accessibility metadata;
- support frame reuse without duplicating application state.

**Мультиворки**
- model workspaces, workflows, triggers, steps and outputs explicitly;
- define retries, cancellation, compensation and restart checkpoints;
- preserve deterministic execution order where the workflow requires it;
- never grant a workflow undeclared filesystem, network or device access.

**Фреймприлотуллы**
- compose framework, application, tool and frame graphs through contracts;
- keep every application and tool independently addressable;
- emit a root manifest plus per-component manifests and a single lock graph.

## 4. Factory architecture

The engine is divided into narrow, reviewable services. Their final implementation belongs to Reaper; JSON manifests are interchange and audit artefacts, not the implementation language.

| Service | Responsibility |
|---|---|
| `rforge::request` | Parse and validate a bounded product request |
| `rforge::catalog` | Read immutable, versioned component manifests |
| `rforge::capability` | Index providers and resolve capability contracts |
| `rforge::resolver` | Compute dependency closure, versions and conflicts |
| `rforge::graph` | Construct, normalize, sign and validate typed graphs |
| `rforge::planner` | Produce deterministic candidate assembly plans |
| `rforge::composer` | Lower a selected plan into canonical Product IR |
| `rforge::codegen` | Emit Reaper source and generated contracts |
| `rforge::integrator` | Bind APIs, events, data models and adapters |
| `rforge::verify` | Run contract, static, integration and resource gates |
| `rforge::build` | Compile through the supported Reaper toolchain |
| `rforge::package` | Create manifests, lock files, hashes and provenance |
| `rforge::evolve` | Propose bounded repairs and extension plans |
| `rforge::runtime` | Connect generated products to the shared runtime |

The shared ДОМ runtime is the lifecycle and orchestration foundation. RForge must use its common lifecycle, task, resource, communication, reactive-state, contract, launch and recovery mechanisms rather than introducing a parallel runtime.

## 5. Composition pipeline

1. **Describe** — accept the product kind, independent product name, target, desired capabilities, limits and explicit permissions.
2. **Normalize** — convert the request to a versioned typed request model; reject unknown fields and unsupported product shapes.
3. **Discover** — inspect the local catalogue and explicitly selected repository sources. No hidden network discovery.
4. **Resolve** — compute dependency closure, compatible versions, conflicts and missing capabilities.
5. **Plan** — produce bounded graph candidates for the selected optimization objective.
6. **Explain** — report why each component and edge is present, what is reused, what is missing and which constraints affected the plan.
7. **Fill gaps** — when enabled, propose missing component contracts and generate new Reaper modules in an isolated staging workspace.
8. **Compose** — lower the selected graph into canonical Product IR with source provenance.
9. **Generate** — emit Reaper source from typed structures/AST nodes, not by unsafe string concatenation.
10. **Integrate** — generate adapters only where an explicit interface contract exists.
11. **Verify** — run parser/type/IR checks, contract conformance, dependency checks, integration tests, resource limits and deterministic-build checks.
12. **Package** — emit a reproducible package only when the maturity and permission gates pass.
13. **Promote** — require explicit approval for installation, publishing, privileged operations or changes to protected repositories.

A failed gate returns structured diagnostics with source spans, component IDs, contract versions and remediation options. A failed candidate must never be reported as a successful product.

## 6. Deterministic planning

Planning must be explainable and repeatable.

Candidate ranking is lexicographic, with hard constraints applied before quality scoring:

1. required capability coverage;
2. version and contract compatibility;
3. absence of prohibited permissions and conflicts;
4. fewer unresolved requirements;
5. reuse of already verified components;
6. selected optimization objective;
7. stable canonical graph signature as the final tie-break.

Supported objectives initially mirror Jora: `balanced`, `low_latency`, `modularity`, `extensibility` and `minimal_complexity`. Resource efficiency may be added as a separately versioned objective.

The same normalized request, catalogue snapshot and seed must produce the same graph signature, dependency order, lock file and generated source. Nondeterministic inputs must be explicit and recorded.

The initial bounded profile inherits the existing Jora ceilings: 24 selected components, 128 graph nodes, 512 graph edges and at most 6 graph alternatives. These are ceilings, not targets. A larger product must use deterministic clustering and bounded provider lookup; it must not silently turn into an all-pairs graph search.

## 7. Product IR and Reaper code generation

Product IR is a Reaper-owned, versioned intermediate representation. It records:

- product kind and product identity;
- component identities and locked versions;
- typed graph nodes and edges;
- public contracts and capability bindings;
- runtime/lifecycle wiring;
- permission and resource declarations;
- source provenance and diagnostic mapping;
- build targets and maturity evidence.

The generator must preserve source locations and diagnostics through `Span` and `SourceMap`. The Reaper compiler remains authoritative for parsing, typing, canonical IR validation and code generation. When available, lowering follows the canonical typed IR and the supported HIR/MIR/LIR and VM/AOT routes. DABI64 is selected only for declared native boundaries.

RForge's implementation is Reaper-first. It must not introduce a new Python generator or Python test runner as the implementation path. The current repository still has a Python reference host and a partial native C17 track; neither fact is evidence that an RForge-native runtime or a full native compiler backend already exists. RForge source generation and execution must be marked pending until Reaper-native support and conformance tests exist.

## 8. Generated product layout

A generated product should use a stable, inspectable structure:

```text
<product>/
  README.md
  rforge.product.json
  rforge.lock.json
  rforge.graph.json
  rforge.provenance.json
  contracts/
    components/
    interfaces/
    events/
  src/
    reaper/
      main.rpr
      frameworks/
      tools/
      applications/
      frames/
      workflows/
      adapters/
  locales/
  tests/
  reports/
```

Empty directories and specification-only source stubs do not count as implemented functionality. The root manifest records every component's maturity and the product's effective maturity. The lock file pins versions, hashes, graph signature and generator version. Provenance records the source revision of each component and all generation inputs.

## 9. Autonomy and safety

RForge may autonomously inspect, plan, compose in staging, generate source, run permitted checks and propose bounded repairs. It must not:

- execute newly generated code outside an isolated, resource-limited test environment;
- install packages, elevate privileges or grant filesystem/network/device permissions;
- overwrite an existing output directory;
- modify protected branches or publish packages without approval;
- rewrite its own policy, verifier or trust roots;
- convert missing evidence into a successful maturity state.

Repairs are limited to a configured number of attempts and must produce a diff, a failing test reference, a changed graph/lock signature and an explanation. Repeated repair loops stop with a diagnostic. Network access is off by default; imported packages require pinned versions, hashes, licence metadata and signature verification.

Cross-repository integrations use versioned contracts and separate reviewable changes. RForge can propose coordinated changes, but it cannot claim that another repository has been updated until that change is reviewed and merged.

## 10. CLI surface

The proposed command surface is:

```text
reaper forge catalog
reaper forge inspect --request <request>
reaper forge plan --request <request> --explain
reaper forge generate --request <request> --output <directory>
reaper forge verify --product <directory>
reaper forge build --product <directory>
reaper forge package --product <directory>
reaper forge diff --left <product-a> --right <product-b>
reaper jora compose --request <request>
```

These commands are a design contract, not a claim that the CLI commands are implemented today.

## 11. Implementation increments

| Increment | Deliverable | Exit evidence |
|---|---|---|
| 0 — Contract | Product-kind enum, request schema, product manifest and migration rules | Schema fixtures, negative cases, docs |
| 1 — Shared model | Extract Jora-compatible catalogue, resolver and graph contracts | Differential Jora fixtures and stable graph signatures |
| 2 — Reaper core | Reaper-native Product IR, resolver and planner | Reaper parser/type/IR tests and deterministic fixtures |
| 3 — Seven composers | Framework, multitool, multiapp, framework bundle, multiframe, multiwork and frame-app-tool composers | Per-kind contract and negative tests |
| 4 — Native generation | Reaper source emitter and generated project layouts | Parse/typecheck generated programs; source-map checks |
| 5 — Real components | First executable framework, tools and applications | Functional, integration, resource and permission tests |
| 6 — Runtime & packages | ДОМ integration, package format, signature and rollback adapters | Isolated runtime and package lifecycle evidence |
| 7 — Evolution | Bounded repair proposals and cross-component compatibility planning | Replayable repair traces and human-review gates |

A product family is not complete when its enum or generator stub exists. It is complete only when it has working components, successful target-runtime evidence, tests, permission policy, packaging/provenance and documented limitations.

## 12. Initial acceptance criteria

- All seven product kinds have distinct validation rules and graph invariants.
- Jora's current request and output contracts remain backward-compatible.
- Unknown IDs, dependency cycles, incompatible versions, conflicts and unsupported targets fail closed.
- Every generated source file maps to a Product IR node and source provenance record.
- Repeated generation from the same inputs is byte-for-byte reproducible.
- Specification-only packs never produce `installable=true` or executable capability claims.
- A failed verification gate prevents packaging and promotion.
- Every external effect is declared, permission-checked and auditable.
- Reaper-native implementation status is reported separately from the existing Python reference host and partial C17 track.
