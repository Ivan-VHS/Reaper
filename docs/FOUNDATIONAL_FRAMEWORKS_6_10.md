# Reaper foundational frameworks 6–10

**Status:** executable Reaper reference contracts; native type-system and backend integration remains partial.  
**Source:** `frameworks/foundation_6_10.rpr`  
**Dependency:** `frameworks/foundation.rpr`  
**Schema:** `reaper.foundation.next.v1`

This group extends the first five foundations without replacing them. It adds semantic rules, compatibility descriptors, project/module roots, application composition and the contracts that connect language layers.

## Framework set

| No. | ID | Framework | Owns | Maturity |
|---:|---|---|---|---|
| 6 | `foundation.basis.v1` | Basis | Value kinds, effects, ownership modes and semantic invariants | Partial |
| 7 | `foundation.contracts.v1` | Foundation | Versioned contract descriptors and compatibility validation | Partial |
| 8 | `foundation.root.v1` | Root | Project roots, relative import paths and module-boundary rules | Partial |
| 9 | `foundation.skeleton.v1` | Skeleton | Application component blueprint and composition validation | Implemented |
| 10 | `foundation.backbone.v1` | Backbone | Ordered data contracts between compiler, runtime and target layers | Partial |

## 6. Basis — semantic invariants

The executable registry exposes current runtime value kinds and the planned systems-language ownership/effect vocabulary. It validates effect sets and makes `pure` exclusive.

The contract separates current behavior from intended semantics:

- immutable-by-default bindings are implemented through `make`;
- runtime quotas and bounded resources exist;
- source-level effect declarations and a complete effect checker are partial;
- ownership/borrowing and deterministic drops are partial;
- typed source declarations and complete diagnostics/SourceMap coverage are not claimed complete.

Public functions: `basis_value_kinds()`, `basis_effect_kinds()`, `basis_ownership_modes()`, `basis_invariants()`, `basis_validate_value_kind(kind)`, `basis_validate_effects(effects)`, `basis_validate_ownership(mode)`, `basis_validate_invariants(rows)`.

An empty effect list denotes no declared host effect. A list containing `pure` is valid only when it contains that one item.

## 7. Foundation — contracts and compatibility

A contract descriptor uses this positional v1 shape:

`[contract_id, major, minor, direction]`

Direction is one of `provides`, `consumes`, or `both`. The catalogue currently accepts major version 1 and minor version 0 for its five published interface IDs. Unknown IDs, incompatible major versions, unsupported minor versions, non-integer versions and invalid directions are rejected.

The policy is additive: a future minor revision may widen accepted versions after its semantics are specified and tested. A major-version change requires a separate compatibility decision.

Public functions: `core_foundation_contracts()`, `core_foundation_validate_contract(descriptor)`, `core_foundation_validate_contract_catalog()`.

This is a source-level contract validator. It is not yet wired into every module import, linker operation or DABI64 host dispatch.

## 8. Root — project and module boundaries

The root context is a positional list:

`[project_id, source_root, module_root, build_root, target_profile]`

The three roots are logical relative paths. Absolute paths, drive-qualified paths and parent traversal are rejected. A module import edge is a two-item `[from, to]` pair and may not be empty or self-referential. Import specifiers must be relative `.rpr` paths.

The existing `reaper.modules.ModuleLoader` remains the implementation authority for actual file reads, import depth, UTF-8/source limits, canonical paths and cycle diagnostics. These new functions validate declarative descriptors; they do not replace the loader or resolve paths against the host filesystem.

Public functions: `root_context_fields()`, `root_validate_relative_path(path)`, `root_validate_context(context)`, `root_validate_import_edge(edge)`, `root_validate_import_specifier(specifier)`, `root_module_boundary_rules()`.

## 9. Skeleton — application composition

A project skeleton is distinct from the repository scaffold:

- required: `manifest`, `entry`, `modules`, `tests`;
- optional: `platform`, `resources`, `examples`, `docs`.

The validator rejects missing required components, duplicate entries and unknown component names. It does not generate directories, files or starter code.

Public functions: `skeleton_required_components()`, `skeleton_optional_components()`, `skeleton_composition_order()`, `skeleton_layout()`, `skeleton_validate_components(components)`.

## 10. Backbone — cross-layer flow contracts

The backbone connects the eight canonical architecture stages from the first group:

`source → lexer → parser → semantic-analysis → canonical-ir → execution-engine → host-adapters → target-backend`

Every adjacent pair has a named contract and a maturity label. The validator checks the complete edge inventory and confirms that the flow order matches the first group's canonical architecture order. It does not imply that partial semantic analysis, typed native IR or all target backends are finished.

Public functions: `backbone_edges()`, `backbone_flow_order()`, `backbone_validate_edges(edges)`, `backbone_find_edge(source, target)`.

## Unified catalogue

The module imports the first group and provides `foundation_all_frameworks()` and `foundation_validate_all_catalog()`. The combined catalogue is expected to contain ten unique IDs. The original five remain owned by `frameworks/foundation.rpr`; this module adds only entries 6–10.

## Usage

```reaper
import "../frameworks/foundation_6_10.rpr" as core

emit core["foundation_validate_all_catalog"]()
emit core["basis_validate_effects"](["filesystem", "clock"])
emit core["core_foundation_validate_contract"](["reaper.host-service.v1", 1, 0, "both"])
emit core["root_validate_import_specifier"]("modules/math.rpr")
emit core["skeleton_validate_components"](["manifest", "entry", "modules", "tests"])
emit core["backbone_validate_edges"](core["backbone_edges"]())
```

## Verification and safety

Tests run the new module through the Reaper interpreter and exercise valid and invalid contracts, effects, ownership modes, root paths, import edges, application components and backbone topology.

The module is pure and deterministic. It does not write files, inspect the host filesystem, access network/process/clock services, load native code, create OS processes, grant privileges, install drivers or access physical hardware.
