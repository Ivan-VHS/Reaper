# RForge framework collection

**Contract:** `reaper.rforge.framework-catalog.v1`  
**Language:** Reaper `.rpr`  
**Current runtime:** Reaper reference runtime  
**Maturity:** source files present; runtime smoke execution pending  
**Native AOT:** not supported for these modules by the current backend

The collection contains twenty independently importable Reaper framework modules arranged in ten ordered mirror pairs. Each module exports a small, explicit API. The reverse member of a pair has a different composition emphasis; it is not an alias.

## Pair map

| Pair | Forward framework | Reverse framework | Distinction |
|---|---|---|---|
| 01 | Plague — Soft Frame | Outbreak — Frame Soft | Surface lifecycle kernel vs frame-first shell composition |
| 02 | Pestilence — Frame Saas | Malady — Saas Frame | Tenant-bound frames vs SaaS-first plan and route gates |
| 03 | Epidemic — Framework native | Miasma — native Framework | ABI and memory contracts vs native host lifecycle and extension admission |
| 04 | Pandemic — Program Summary | Fever — Summary Program | Execution accounting vs diagnostics-first summary aggregation |
| 05 | Scourge — System Control | Bane — Control System | System state machine vs control-rule and action-plan engine |
| 06 | Blight — Tunnel Justice | Curse — Justice Tunnel | Tunnel-first clearance routing vs justice-first evidence and release |
| 07 | Calamity — native Realisation | Menace — Realisation native | Native pipeline stages vs realization transaction and commit gates |
| 08 | Affliction — UI Unreal | Cataclysm — Unreal UI | UI-first event/geometry bridge vs Unreal-first widget lifecycle/batches |
| 09 | Infestation — Concrete Cosmos | Devastation — Cosmos Concrete | Entity-first scene graph vs space-first cell indexing/materialization |
| 10 | Contagion — base Space | Desolation — Space base | Coordinate geometry primitives vs coordinate basis authority/transforms |

## Implemented module APIs

### 01 — Plague / Outbreak

**Plague** provides `soft_frame_opacity_valid`, `soft_frame_phase_valid`, `soft_frame_transition_allowed`, `soft_frame_create` and `soft_frame_hit_test`. It owns the soft frame lifecycle and geometry constraints.

**Outbreak** provides `outbreak_slot_valid`, `outbreak_softness_valid`, `outbreak_shell_create`, `outbreak_attach_allowed` and `outbreak_surface_ready`. It composes a frame-first shell and prevents duplicate slot attachment.

### 02 — Pestilence / Malady

**Pestilence** provides tenant ID validation, tenant-bound frame descriptors, same-tenant access checks, quota validation and session transitions.

**Malady** provides plan-to-frame limits, feature entitlements, route validation, quota admission and a combined route decision. The starter plan limits are explicit policy defaults in source and should be changed only with a versioned product policy.

### 03 — Epidemic / Miasma

**Epidemic** provides scalar-width, ABI, alignment, region and aggregate native-contract validation. Its DABI64-v1 predicate is deliberately narrow: 64-bit little-endian.

**Miasma** provides native host/module ABI matching, lifecycle transitions, memory-budget admission, extension-grant checks and publish-readiness validation.

These modules describe and validate native boundaries. They do not provide a physical memory mapper, kernel loader, arbitrary FFI, driver or completed native AOT backend.

### 04 — Pandemic / Fever

**Pandemic** validates program counters and produces completion, remaining-work and outcome summaries.

**Fever** aggregates errors and warnings, classifies severity, validates report lines and provides a release gate that blocks on errors.

### 05 — Scourge / Bane

**Scourge** provides a system state machine and authorization-aware command admission. Inspection is available for known states; start and recovery require explicit guarded authorization.

**Bane** evaluates control rules and safe actions, produces proposed action plans and classifies enforcement level. It does not execute privileged system operations.

### 06 — Blight / Curse

**Blight** validates tunnel endpoints, clearance levels, audit reason presence, route admission and bounded leases.

**Curse** evaluates justice cases from evidence, supports appeal holds, requires signed release and emits structured audit records.

Both are policy frameworks only. They do not open network tunnels, grant OS permissions or enforce a remote service boundary by themselves.

### 07 — Calamity / Menace

**Calamity** models ordered native realization stages: source, parsed, typed, IR verified, lowered and linked. It gates emission on source, target, IR and ABI readiness.

**Menace** produces realization plans, controls artifact commit, bounds transient retries and validates stage ordering.

Neither claims a working native compiler or linker; they provide the build-governance contracts around one.

### 08 — Affliction / Cataclysm

**Affliction** validates UI widget dimensions, viewport layout and focused event routing. Its Unreal bridge check requires an exact engine/bridge major match and a minimum major of 5.

**Cataclysm** validates supported engine ranges, widget lifecycle transitions, draw/widget batch limits and frame commit readiness.

These are Reaper-side adapter contracts. An Unreal Engine runtime or plugin is not included.

### 09 — Infestation / Devastation

**Infestation** validates concrete entity identities, directed relationship kinds, parent attachment and nesting depth.

**Devastation** computes deterministic row-major 3D cell indices, validates region bounds and admits bounded entity materialization.

### 10 — Contagion / Desolation

**Contagion** supplies bounded 3D points, squared Euclidean distance, axis-aligned box checks and coordinate translation.

**Desolation** supplies basis validity and local/world transforms. Inverse transforms refuse a zero scale; the initial base profile is three-dimensional.

## Import and use

A Reaper program can import each framework directly:

```reaper
import "../../frameworks/rforge/plague_soft_frame.rpr" as plague

make frame := plague["soft_frame_create"](640, 480, 70)
assert(size(frame) == 5, "frame descriptor was not created")
```

Run the collection smoke suite from the repository root:

```sh
reaper --check tests/rforge/frameworks_smoke.rpr
reaper tests/rforge/frameworks_smoke.rpr
```

The smoke suite contains four positive/negative assertions for each framework plus four collection-level assertions (84 total). It has been authored but is not reported as passed until it runs in CI or on a Reaper runtime.

## Runtime and maturity boundaries

- The source modules use the existing Reaper `.rpr` module/import/export surface.
- The current native AOT backend does not support imports/exports or collection values. These source modules therefore target the reference runtime today.
- No framework currently claims `executable_capabilities`, installation, native compilation, network access, filesystem access or privileged OS effects.
- The SaaS, tunnel and Unreal names describe contract domains. They do not imply hosted SaaS infrastructure, network tunnel creation or an Unreal Engine dependency.
- The framework APIs are deterministic validation and composition primitives. Concrete storage, rendering, hosting, network transport, kernel and compiler backends remain explicit adapters or later implementation increments.

The aggregate module `frameworks/rforge/all.rpr` imports all twenty frameworks and exports inventory, profile, lookup and pair-membership helpers.

The machine-readable catalogue is `examples/rforge/frameworks.v1.json`; its schema is `schemas/rforge.framework-catalog.v1.schema.json`.
