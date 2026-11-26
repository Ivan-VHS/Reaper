# Reaper foundational frameworks 11–15

**Status:** executable Reaper reference contracts; full compiler/runtime adoption remains partial.  
**Source:** `frameworks/foundation_11_15.rpr`  
**Dependency:** `frameworks/foundation_6_10.rpr`  
**Schema:** `reaper.foundation.third.v1`

This group adds typed aggregate descriptors, deterministic construction plans, project federation metadata, extension contracts and an explicit host shell boundary.

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 11 | `foundation.structure.v1` | Structure | Typed field descriptors and bounded scalar value validation | Partial |
| 12 | `foundation.construction.v1` | Construction | Dependency-first composition plans and deterministic order | Implemented |
| 13 | `foundation.ecosystem.v1` | Ecosystem | Peer inventory and versioned integration relationships | Partial |
| 14 | `foundation.extension.v1` | Extension | Capability-declared extension manifests and lifecycle transitions | Partial |
| 15 | `foundation.shell.v1` | Shell | Host/session envelope, request bounds and lifecycle ordering | Partial |

## 11. Structure — typed aggregates

A schema uses the positional form:

`[schema_id, schema_version, fields]`

Each field uses:

`[field_name, field_type, mutability]`

The v1 validator recognizes `bool`, `text`, `bytes`, fixed-width signed integers `i8`–`i128` and unsigned integers `u8`–`u128`. Field mutability is either `immutable` or `mutable`.

`structure_validate_instance(schema, values)` checks field count, value kind and integer range. The `bytes` type accepts text or a list whose every element is validated as an integer in the unsigned 8-bit range. Pointer/reference/slice/target-sized types are intentionally absent because the current runtime does not provide their ownership and target-layout semantics. This is a descriptor/runtime validation layer, not source-level `struct` syntax or compiler layout.

Public functions: `structure_type_bounds()`, `structure_supported_types()`, `structure_mutability_modes()`, `structure_validate_field(field)`, `structure_validate_schema(schema)`, `structure_value_matches(type, value)`, `structure_validate_instance(schema, values)`, `structure_field_layout(schema)`.

## 12. Construction — deterministic composition

A build plan is:

`[builder_id, ordered_steps]`

Each step is:

`[step_id, dependencies]`

A dependency must appear earlier in the plan. Duplicate IDs, missing/forward dependencies and self-cycles are rejected. This defines deterministic dependency ordering and cycle prevention by requiring a topological order; it does not launch builds or execute commands.

Public functions: `construction_plan_fields()`, `construction_validate_plan(plan)`, `construction_build_order(plan)`, `construction_rules()`.

## 13. Ecosystem — peer federation

The peer inventory reflects the existing Reaper federation roles for Reaper, Pytyliki, OPlague and VentuSample. Its validator requires the canonical peer inventory, and its link catalogue contains all twelve directed relationships from `federation/octa-pyramid.v1.json`. It preserves all twelve directed OCTA-8 links, including the two OPlague/Reaper artifact flows, the four implemented Pytyliki C ABI directions, the planned VentuSample/Pytyliki directions and the not-applicable Reaper/VentuSample and OPlague/VentuSample directions. The Pytyliki ABI remains opt-in even where the federation relationship is implemented. No network client or cross-repository runtime dependency is introduced.

Public functions: `ecosystem_peers()`, `ecosystem_links()`, `ecosystem_validate_peers(peers)`, `ecosystem_find_peer(id)`, `ecosystem_validate_link(link)`.

## 14. Extension — controlled add-ons

An extension manifest uses:

`[extension_id, major_version, host_contract, requested_capabilities, entry_point]`

The host contract must pass the previous group's version validator and identify `reaper.host-service.v1`. Capability names are checked against the symbolic constants in `include/reaper/system.h` (including `FS_READ`, `NETWORK`, `PROCESS_CONTROL` and desktop capability families). These are requests, not grants: only a trusted host can authorize or dispatch them.

The lifecycle allows declared → validated → enabled, enabled → disabled, disabled → enabled, and enabled/disabled → revoked. No code is loaded or enabled by this module.

Public functions: `extension_capabilities()`, `extension_lifecycle_states()`, `extension_valid_transitions()`, `extension_validate_capabilities(values)`, `extension_validate_manifest(manifest)`, `extension_validate_transition(from, to)`, `extension_policy()`.

## 15. Shell — host boundary

The shell context is:

`[host_id, session_id, entry_module, requested_capabilities]`

A request envelope is:

`[operation, capability, payload_bytes]`

Operations are `start`, `stop`, `query`, and `notify`; payload size is bounded to 65,536 bytes. Lifecycle order is bootstrap → validate → start → run → drain → shutdown → cleanup.

The host must derive identity and capabilities from trusted state. This layer validates declarative request metadata; it does not execute syscalls, open IPC channels, spawn processes, grant capabilities or provide a real shell service.

Public functions: `shell_context_fields()`, `shell_operations()`, `shell_lifecycle()`, `shell_validate_context(context)`, `shell_validate_lifecycle(steps)`, `shell_validate_request(request)`, `shell_boundary_rules()`.

## Unified catalogue

The module imports the second group, which itself imports the first group, then exposes `foundation_all_frameworks_15()` and `foundation_validate_catalog_15()`. The combined catalogue must contain fifteen unique framework IDs. The original groups remain independently owned in their own modules.

## Usage

```reaper
import "../frameworks/foundation_11_15.rpr" as systems

make gpio_schema := ["gpio.pin.v1", 1, [["pin", "u8", "immutable"], ["enabled", "bool", "mutable"]]]
emit systems["structure_validate_schema"](gpio_schema)
emit systems["structure_validate_instance"](gpio_schema, [13, true])
emit systems["construction_validate_plan"](["application", [["compile", []], ["test", ["compile"]]]])
emit systems["extension_validate_transition"]("enabled", "disabled")
emit systems["shell_validate_lifecycle"](systems["shell_lifecycle"]())
emit systems["foundation_validate_catalog_15"]()
```

## Verification and safety

Tests use the Reaper interpreter to validate field schemas, integer bounds, dependency ordering, peer inventories, extension manifests, lifecycle transitions, shell envelopes and the integrated fifteen-item catalogue.

The implementation is pure. It does not construct binary layouts, allocate pointer-backed memory, link modules, access the network, spawn processes, load extensions, grant privileges, open IPC channels or access physical devices.
