# Reaper foundational frameworks 41–45

**Status:** executable Reaper reference contracts; complete governance automation and compiler-integrated module effects remain partial.  
**Source:** `frameworks/foundation_41_45.rpr`  
**Dependency:** `frameworks/foundation_36_40.rpr`  
**Schema:** `reaper.foundation.ninth.v1`

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 41 | `foundation.methodology.v1` | Methodology | Engineering lifecycle, gates and evidence rules | Partial |
| 42 | `foundation.approach.v1` | Approach | Compatibility-first, local-first, security and evidence strategies | Partial |
| 43 | `foundation.system.v1` | System | Project-level component and interface manifest | Partial |
| 44 | `foundation.subsystem.v1` | Subsystem | Owned subsystem input/output contracts | Partial |
| 45 | `foundation.module.v1` | Module | Versioned .rpr module, export, import and effect contract | Partial |

## 41. Methodology — evidence-led lifecycle

The canonical stages are inventory → specify → design → implement → verify → integrate → maintain. A plan may omit later optional stages, but it must begin with inventory, preserve order and reach at least verification. A gate carries a non-empty, unique list of evidence references.

This does not authorize autonomous approval or repository mutation. It is a validation contract for reviewable work.

Public functions: `methodology_stages()`, `methodology_validate_plan(stages)`, `methodology_validate_gate(gate)`, `methodology_rules()`.

## 42. Approach — engineering strategy profiles

Profiles publish principles for compatibility-first development, local-first operation, capability security, evidence-driven status and native conformance. Each profile is explicit; selection rejects unknown and duplicate IDs.

Public functions: `approach_profiles()`, `approach_validate_profile(profile)`, `approach_validate_selection(ids)`, `approach_principles(id)`.

## 43. System — project-level manifest

A system manifest is:

`[system_id, schema_version, components, required_contracts]`

Components are limited to language, compiler, runtime, host, toolchain, tests, documentation and integrations. IDs and contracts must be unique. This validates architecture inventory; it does not instantiate a running system.

Public functions: `system_component_catalog()`, `system_validate_manifest(manifest)`, `system_validate_dependency_order(components)`.

## 44. Subsystem — owned boundaries

Subsystem contracts publish:

`[subsystem_id, owner_component, input_contract, output_contract, maturity]`

The catalogue maps existing Reaper layers to their responsibilities: lexer, parser, semantic analysis, canonical IR, runtime, module loader, resource manager and host adapter. Flow validation checks that one subsystem's output matches the next subsystem's input.

Public functions: `subsystem_contracts()`, `subsystem_validate_contract(contract)`, `subsystem_validate_catalog()`, `subsystem_find(id)`, `subsystem_validate_flow(ids)`.

## 45. Module — .rpr package boundary

A module descriptor is:

`[module_id, relative_path, major, minor, exports, imports, effects]`

Paths must be relative `.rpr` files. Exports/imports are unique non-empty identifiers; imports cannot self-reference. Effects use a closed vocabulary, and `pure` is exclusive. Module graphs must be supplied in dependency-first order; missing dependencies and cycles are rejected.

The existing `reaper.modules.ModuleLoader` remains authoritative for actual file reads, UTF-8 decoding, canonical paths, import-depth limits, caching and cycle diagnostics. This contract does not replace or duplicate runtime loading.

Public functions: `module_effect_kinds()`, `module_validate_relative_path(path)`, `module_validate_contract(module)`, `module_validate_graph(modules)`, `module_graph_order(modules)`.

## Unified catalogue

The module exposes `foundation_all_frameworks_45()` and `foundation_validate_catalog_45()`, extending all earlier groups to forty-five unique framework IDs.

## Usage

```reaper
import "../frameworks/foundation_41_45.rpr" as engineering

emit engineering["foundation_validate_catalog_45"]()
emit engineering["methodology_validate_plan"](["inventory", "specify", "design", "implement", "verify"])
emit engineering["approach_validate_selection"](["compatibility-first", "evidence-driven"])
emit engineering["system_validate_manifest"](["reaper.system.v1", 1, ["language", "runtime", "tests"], ["reaper.foundation.v1"]])
emit engineering["subsystem_validate_flow"](["lexer", "parser"])
emit engineering["module_validate_graph"]([["app.math", "math.rpr", 1, 0, ["double"], [], ["pure"]], ["app.main", "main.rpr", 1, 0, ["run"], ["app.math"], ["console"]]])
```

## Verification and safety

Tests cover lifecycle order, evidence gates, profile selection, manifest components, subsystem flow and module dependency graphs. No module is loaded by this validator, and no tool, network service, repository mutation or privileged host operation is triggered.
