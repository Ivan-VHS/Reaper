# Rivet — Reaper-native framework and multitool assembly

**Request contract:** `reaper.rivet.request.v1`  
**Module contract:** `reaper.rivet.module.v1`  
**Product contract:** `reaper.rivet.product.v1`  
**Implementation language:** Reaper (`.rpr`)  
**Current scope:** dependency and contract planning engine  
**Current build state:** `plan_only`; source generation and package emission are not implemented

## 1. Purpose

Rivet is a Reaper-native composition system for assembling reusable frameworks, multitool suites and combined products from independently versioned capability modules.

The product formula is:

`Product = Foundation + Runtime + Contracts + Capabilities + Adapters + Workflows + Target Profile`

Rivet is complementary to Jora, not a replacement:

- **Jora** remains the application-oriented catalogue and application scaffold generator.
- **Rivet** composes reusable frameworks and multitool products, resolves their complete module graph and evaluates whether their declared contracts can work together.
- A future shared catalogue format may be consumed by both systems, but neither system may silently treat a specification-only catalogue entry as executable code.

Generated product names are independent product identities. The platform or factory name must not be inserted into those names.

## 2. Product profiles

| Profile | Composition goal | Required shape |
|---|---|---|
| `framework` | reusable foundation for other software | contracts, lifecycle, runtime services, extension points, adapters and tests |
| `multitool` | one coordinated product containing multiple useful tools | shared runtime, tool modules, common navigation/command surface and workflow orchestration |
| `hybrid` | a framework that also ships user-facing tools | framework contracts and services plus an explicit tool/workflow layer |

A profile is an architectural constraint, not a product label. Every selected module must explicitly declare that it supports the requested profile.

### Framework composition

A framework is not a pile of wrappers. It must have stable public contracts, clear ownership boundaries, lifecycle semantics, versioned extension points, deterministic error behavior and conformance tests. The framework profile should expose a small stable core and keep optional adapters outside that core.

### Multitool composition

A multitool shares one runtime and one permission model across its modules. It should reuse common search, storage, task, settings, localization, logging and update contracts rather than shipping duplicated implementations. Tools remain independently replaceable modules, with explicit workflow edges between them.

## 3. Reaper source layout

The first implementation increment lives in:

```text
rivet/
  catalog.rpr       # closed first-party catalogue
  engine.rpr        # dependency closure, validation and plan generation

schemas/
  rivet.request.v1.schema.json
  rivet.module.v1.schema.json
  rivet.product.v1.schema.json

examples/rivet/
  framework_plan.rpr
  multitool_plan.rpr
  planner_checks.rpr
  framework.request.json
  multitool.request.json
```

The Reaper API is imported from `rivet/engine.rpr`:

```rpr
import "../../rivet/engine.rpr" as rivet

make plan := rivet["compose"](
    "Northstar Service Framework",
    "framework",
    ["framework.http", "framework.plugin", "framework.config"]
)

assert(plan[0] == "ok", "composition must satisfy all module contracts")
emit rivet["describe"](plan)
```

The planner returns a bounded data record:

`[status, product_name, product_kind, ordered_modules, dependency_edges, requested_permissions, module_maturity, build_state]`

The initial engine implements:

1. closed-catalogue module lookup;
2. transitive dependency expansion with duplicate elimination and finite limits;
3. deterministic dependency-first topological ordering;
4. cycle detection;
5. product-profile compatibility checks;
6. required-capability provider checks;
7. declared module conflict checks;
8. aggregation of permissions for later review;
9. human-readable plan reporting.

The catalogue record layout is:

`[id, version, kind, profiles, dependencies, provides, requires, conflicts, maturity, permissions, summary]`

## 4. Assembly pipeline

The complete target pipeline is intentionally split into inspectable stages:

1. **Intent capture.** Accept a product name, product profile, module roots, target architecture, optimization objective and requested capabilities.
2. **Request validation.** Validate the versioned request schema, closed enums, unique roots, collection sizes, target support and path limits.
3. **Catalogue resolution.** Load only configured local catalogue snapshots by default. A remote registry is never contacted implicitly.
4. **Dependency closure.** Add transitive dependencies, pin exact module versions and reject unknown or unbounded dependency ranges.
5. **Graph validation.** Detect cycles, conflicting providers, incompatible profile declarations, missing capability providers and unsupported target edges.
6. **Architecture planning.** Produce a dependency-first graph and separate asynchronous event edges from startup dependencies. Synchronous startup/control edges must remain acyclic.
7. **Source composition.** Generate Reaper modules from typed templates or verified source units. Do not concatenate arbitrary source text or silently rewrite user code.
8. **Contract generation.** Emit public interfaces, error/result boundaries, API docs, configuration schemas and module ownership metadata.
9. **Verification.** Run static analysis, module conformance suites, integration tests, resource-limit checks and deterministic-output comparisons.
10. **Packaging.** Produce a lockfile, SBOM, license inventory, artifact hashes and provenance record.
11. **Promotion.** Sign and publish only after required evidence exists and a human approves the release.

The initial implementation covers the in-memory part of stages 1–6: a caller supplies the product identity, profile and root module IDs directly to the Reaper API; the planner expands dependencies, validates the graph and contracts, orders modules, aggregates requested permissions and renders a plan. It does not yet read the JSON request fixtures. The current source also does not emit project files, compile generated products, run module conformance suites, create packages or sign artifacts. Those are explicit follow-on increments, not implied by the planner.

## 5. Module contracts and catalogue policy

Every installable module must carry:

- immutable module ID and semantic version;
- module kind and supported product profiles;
- exact dependencies and compatibility ranges;
- provided and required capability IDs;
- declared conflicts and replacement rules;
- target/ABI compatibility;
- source files and public entry points;
- permission requirements and resource budgets;
- SPDX license identity and third-party inventory;
- conformance-suite identifiers and evidence references;
- content hashes, provenance and a verifiable signature.

A registry description is metadata, not implementation. A module may move through these maturity states:

| State | Meaning |
|---|---|
| `specification_only` | contract and intent exist; no executable implementation is claimed |
| `source_only` | source exists, but required tests/evidence are incomplete |
| `implemented` | declared behavior has code and focused tests |
| `verified` | conformance, compatibility, resource and provenance gates pass for named targets |
| `installable` | package integrity, signature, permissions, transaction and rollback gates pass |

Rivet's current first-party catalogue entries are `specification_only`. The planner may describe their intended graph, but must not promote them to executable frameworks or tools.

## 6. Security and local-first behavior

- Offline/local catalogue resolution is the default. Registry access must be explicit, pinned and auditable.
- Composition never executes a module, shell command, generated source file or build hook.
- Filesystem, network, process, audio and device permissions are collected as requested capabilities. They are not granted by the planner.
- Every external permission requires a separate consent and host-policy decision.
- Build output is written to a new staging directory, verified, then atomically promoted. Existing destinations and symlink escapes are rejected.
- Build tools, dependencies and generators are pinned; reproducible output and content hashes are recorded.
- Untrusted manifests, source archives and binary artifacts are size-bounded and validated before parsing.
- Third-party code is not copied or vendored without license review. Prefer clean-room Reaper implementations and documented adapters.

## 7. DОМ runtime integration

Frameworks and multitools should converge on the shared Reaper DОМ runtime contracts for lifecycle, tasks, resources, communication, reactive state, validation, startup and recovery. Rivet must not generate a private competing lifecycle or scheduler when a compatible DОМ service exists.

This integration is contract-gated: each DОМ interface must have a frozen version, ownership/effect rules, compatibility tests and a verified implementation before a generated product can depend on it. Until then, a DОМ dependency remains explicitly planned.

## 8. Target architecture and DAK integration

Reaper is the canonical source language and source generator. The initial supported target is Reaper source. An architecture label such as x86_64, aarch64 or Elbrus is a target declaration, not proof that a compiler backend or runtime adapter exists for it.

Future DAK integration may consume verified Rivet packages through the DAK package manager and update subsystem. The trust boundary remains outside the composer: signature verification, staged installation, least-privilege grants, rollback and recovery must be enforced by the package/runtime services. Rivet must not install or activate privileged components itself.

## 9. CLI direction

The planned command family is:

```sh
reaper rivet catalog --json
reaper rivet inspect --module framework.http
reaper rivet plan --request examples/rivet/framework.request.json
reaper rivet compose --request examples/rivet/multitool.request.json --output ./Workbench
reaper rivet verify ./Workbench
reaper rivet package ./Workbench --output ./dist
```

These commands describe the target CLI surface; they are not all available in the current increment. Run the Reaper examples with the installed Reaper CLI: `reaper examples/rivet/framework_plan.rpr`, `reaper examples/rivet/multitool_plan.rpr` and `reaper examples/rivet/planner_checks.rpr`.

## 10. Implementation milestones

| Milestone | Deliverable | Exit evidence |
|---|---|---|
| RIV-1 | Reaper-native catalogue and deterministic planning | dependency closure, ordering, cycle/conflict/profile/capability checks |
| RIV-2 | Manifest and local registry loader | schema validation, pinned versions, offline operation, malformed-input tests |
| RIV-3 | Reaper source generator | typed templates, deterministic project tree, no arbitrary text injection |
| RIV-4 | Framework and multitool runtime foundations | real lifecycle, task, resource, event and adapter implementations |
| RIV-5 | Contract and integration verification | conformance suites, negative tests, compatibility and resource evidence |
| RIV-6 | Reproducible package pipeline | lockfile, SBOM, license report, hashes, provenance and signature verification |
| RIV-7 | DAK package/update integration | staged transaction, trust checks, capability grants, rollback and recovery |

RIV-1 is the current partial increment. Do not mark later milestones delivered based on the existence of schemas, examples or catalogue records.
