# Reaper foundational frameworks 6–10

**Status:** executable Reaper reference contracts; full native type/effect integration remains partial.  
**Source:** `frameworks/foundation_6_10.rpr`  
**Dependency:** `frameworks/foundation.rpr`  
**Schema:** `reaper.foundation.next.v1`  
**Canonical vocabulary:** native C17 architecture catalog, IDs 6–10.

This group is aligned with the repository's stable 66-concept catalog. It does not create a second naming system: the Reaper module uses matching concept names in matching order, while publishing executable contracts for the parts that can be validated today.

## Framework set

| No. | Native concept key | Framework | Owns | Maturity |
|---:|---|---|---|---|
| 6 | `basis` | Basis | Agreed semantic primitives, value kinds, effect and ownership vocabulary | Partial |
| 7 | `base` | Base | Stable shared implementation primitives required by dependent capabilities | Partial |
| 8 | `foundation` | Foundation | Mandatory invariants and versioned compatibility contracts | Partial |
| 9 | `skeleton` | Skeleton | Minimal mandatory shape of a complete application | Implemented |
| 10 | `backbone` | Backbone | Essential contracts preserving the source-to-target flow | Partial |

The native registry keys and IDs are authoritative: `basis` (6), `base` (7), `foundation` (8), `skeleton` (9), and `backbone` (10). The Reaper-level IDs are namespaced as `architecture.<key>.v1`. The first group remains independently owned by `frameworks/foundation.rpr`.

## 6. Basis — agreed semantic primitives

Basis publishes the value-kind, effect and ownership vocabularies used to describe Reaper's execution model. It also publishes a list of core invariants with an evidence-backed maturity for each one.

Implemented today: immutable `make` bindings, runtime quotas and bounded resource accounting. Partial: source-level effect declarations, complete effect checking, ownership/borrowing, deterministic drops, and full source-coordinate coverage.

An empty effect list means no declared host effect. `pure` is exclusive: it cannot appear beside filesystem, network, clock, MMIO or any other effect. Duplicate effect names and unknown values are rejected.

Public API:

- `basis_value_kinds()`
- `basis_effect_kinds()`
- `basis_ownership_modes()`
- `basis_invariants()`
- `basis_validate_value_kind(kind)`
- `basis_validate_effects(effects)`
- `basis_validate_ownership(mode)`
- `basis_validate_invariants(rows)`

The vocabulary is a contract catalogue, not proof that every listed type or effect is accepted by the current parser or native compiler.

## 7. Base — stable shared primitives

Base inventories shared implementations on which other Reaper capabilities depend:

| Primitive | Evidence | Maturity |
|---|---|---|
| Module loader | `reaper.modules` | Implemented |
| Canonical IR and VM | `reaper.ir`, `reaper.vm` | Implemented |
| Resource ledger | `reaper.resources` | Implemented |
| Memory manager | `reaper.memory` | Implemented |
| Diagnostic catalog | `reaper.diagnostic_catalog` | Implemented |
| System host dispatch | `include/reaper/system.h` | Partial |
| Native scalar backend | `reaper.native_compiler` | Partial |

`base_required_primitives()` names the five implemented shared primitives. `base_validate_selection(selected)` rejects unknown or duplicated entries and requires the complete minimum set. Optional/partial primitives may be selected, but their status remains visible. This is an inventory and selection check; it does not load or enable a service.

Public API: `base_primitives()`, `base_required_primitives()`, `base_validate_primitive(row)`, `base_validate_selection(ids)`.

## 8. Foundation — invariants and compatibility contracts

Foundation describes conditions that must be explicitly declared before dependent extensions are introduced.

The invariant inventory names the required Basis rules. `foundation_validate_invariants(ids)` verifies that a supplied set contains the required unique, known invariant IDs. It does **not** prove that a partial compiler/runtime feature already enforces those rules.

A contract descriptor has this positional shape:

`[contract_id, major, minor, direction]`

Direction is one of `provides`, `consumes`, or `both`. The v1 catalog accepts five named contract IDs at major 1, minor 0. Unknown IDs, incompatible versions, fractional/negative version numbers and invalid directions are rejected. A future minor version must be added deliberately with a compatibility decision and tests; this validator does not assume arbitrary forward compatibility.

Public API: `foundation_required_invariants()`, `foundation_contracts()`, `foundation_validate_contract(descriptor)`, `foundation_validate_contract_catalog()`, `foundation_validate_invariants(ids)`.

The validator is not yet wired into every module import, linker operation or DABI64 host dispatch.

## 9. Skeleton — minimum application form

A complete application skeleton is distinct from the repository-level scaffold in group 1.

Required components: `manifest`, `entry`, `modules`, `tests`.  
Optional components: `platform`, `resources`, `examples`, `docs`.

The validator rejects missing required components, duplicates and unknown component names. It does not create project files or generate starter code.

Public API: `skeleton_required_components()`, `skeleton_optional_components()`, `skeleton_composition_order()`, `skeleton_layout()`, `skeleton_validate_components(components)`.

## 10. Backbone — essential cross-layer flow

Backbone binds the eight canonical architecture stages declared by group 1:

`source → lexer → parser → semantic-analysis → canonical-ir → execution-engine → host-adapters → target-backend`

Every adjacent pair carries a contract identifier and a maturity marker. The validator checks the declared edge inventory and confirms that its layer order matches the first group's architecture contract. Partial semantic analysis, native typed IR, host adapters and target backends remain partial; the graph is not evidence of complete end-to-end native compilation.

Public API: `backbone_edges()`, `backbone_flow_order()`, `backbone_validate_edges(edges)`, `backbone_find_edge(source, target)`.

## Unified catalogue and usage

`foundation_all_frameworks()` composes the first group's five entries with this group's five entries. `foundation_validate_all_catalog()` checks all ten rows and unique identifiers without copying or redefining group 1.

```reaper
import "../frameworks/foundation_6_10.rpr" as core

emit core["foundation_validate_all_catalog"]()
emit core["basis_validate_effects"](["filesystem", "clock"])
emit core["base_validate_selection"]([
    "module-loader",
    "canonical-ir",
    "resource-ledger",
    "memory-manager",
    "diagnostic-catalog"
])
emit core["foundation_validate_contract"]([
    "reaper.host-service.v1", 1, 0, "both"
])
emit core["skeleton_validate_components"]([
    "manifest", "entry", "modules", "tests"
])
emit core["backbone_validate_edges"](core["backbone_edges"]())
```

## Verification and safety

Tests execute the module through the Reaper interpreter and cover the combined catalog, value/effect/ownership vocabularies, duplicate rejection, shared primitive selection, contract versions, invariant inventory, application skeleton and backbone topology.

The module is pure and deterministic. It does not write files, inspect the host filesystem, access network/process/clock services, load native code, create OS processes, grant privileges, install drivers or access physical hardware.
