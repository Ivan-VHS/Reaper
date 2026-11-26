# Reaper foundational frameworks 21–25

**Status:** executable Reaper reference contracts; package installation and external tool execution remain planned or adapter-dependent.  
**Source:** `frameworks/foundation_21_25.rpr`  
**Dependency:** `frameworks/foundation_16_20.rpr`  
**Schema:** `reaper.foundation.fifth.v1`

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 21 | `foundation.toolset.v1` | Toolset | Reaper tool inventory and ownership | Partial |
| 22 | `foundation.tooling.v1` | Tooling | PATH-only discovery and evidence policy | Partial |
| 23 | `foundation.toolkit.v1` | Toolkit | Composable tool bundles and deterministic resolution | Implemented |
| 24 | `foundation.package.v1` | Package | Versioned manifests and dependency-first package graph | Partial |
| 25 | `foundation.stack.v1` | Stack | Hosted, VM, native, simulator and freestanding layer profiles | Partial |

## 21. Toolset — developer tool inventory

The catalogue records actual Reaper services: CLI, formatter, type checker, scalar native compiler, LSP, DAP, embedded workbench and architecture matrix. It distinguishes implemented services from partial tracks and gives each a stable ID and command label. A registry row does not claim every subcommand or native backend is complete.

Public functions: `toolset_catalog()`, `toolset_find_tool(id)`, `toolset_validate_catalog()`, `toolset_validate_selection(ids)`.

## 22. Tooling — discovery and evidence

The tool catalogue contains compiler, build-system, embedded cross-compiler and language-tool candidates. Probe descriptors use:

`[command, path_state, probe_state]`

where probe state is `available`, `missing` or `not-probed`. This validates a report shape; the module does not itself inspect PATH or execute a compiler. Availability is not ABI certification. Installation and system mutation are explicitly outside the contract.

Public functions: `tooling_commands()`, `tooling_find_command(command)`, `tooling_validate_probe(probe)`, `tooling_probe_policy()`.

## 23. Toolkit — composable tool bundles

Bundles group the existing catalogue into language, native-build, editor, embedded and quality workflows. Selection requires known unique bundles; resolution returns the deduplicated tool IDs in deterministic bundle order. It produces a plan, not a process execution.

Public functions: `toolkit_bundles()`, `toolkit_validate_bundle(name)`, `toolkit_validate_selection(names)`, `toolkit_resolve_tools(names)`.

## 24. Package — manifest and dependency graph

A package manifest is:

`[package_id, major, minor, entry_module, dependencies]`

The entry module must be a `.rpr` path. Dependency IDs are unique and must already appear in the registry sequence, so the accepted registry is a topological order; missing nodes and cycles are rejected. This is not yet a complete package manager: semantic lockfiles, content digests, local cache, signed sources, atomic installation and rollback remain planned.

Public functions: `package_manifest_fields()`, `package_validate_manifest(manifest)`, `package_validate_registry(packages)`, `package_resolve_order(packages)`, `package_policy()`.

## 25. Stack — runtime and target composition

The stack catalogue contains the hosted reference interpreter, canonical VM, scalar C17 host and simulator profiles, plus a planned freestanding profile. Selection rejects planned profiles and requires exact layer order. The validator prevents a profile from quietly omitting a frontend, semantic-analysis or target boundary.

Public functions: `stack_profiles()`, `stack_validate_profile(profile)`, `stack_validate_selection(id)`, `stack_layer_catalog()`, `stack_validate_layers(layers)`.

## Unified catalogue

The module exposes `foundation_all_frameworks_25()` and `foundation_validate_catalog_25()`, extending the first four groups to twenty-five unique framework IDs.

## Usage

```reaper
import "../frameworks/foundation_21_25.rpr" as tools

emit tools["foundation_validate_catalog_25"]()
emit tools["toolset_validate_selection"](["reaper.cli", "reaper.formatter"])
emit tools["tooling_validate_probe"](["gcc", "C:/toolchain/bin/gcc.exe", "available"])
emit tools["toolkit_resolve_tools"](["language", "native-build"])
emit tools["package_resolve_order"]([["math", 1, 0, "math.rpr", []], ["app", 1, 0, "main.rpr", ["math"]]])
emit tools["stack_validate_selection"]("canonical-vm")
```

The probe example is illustrative of a caller-provided report. No filesystem lookup or compiler execution occurs.

## Verification and safety

Tests exercise inventories, discovery-state descriptors, bundle composition, package graph ordering and stack-profile selection. The framework is pure: it does not launch tools, install packages, modify PATH, access a network, create files or select a privileged runtime.
