# Reaper foundational framework 66 — Software Framework

**Status:** executable umbrella contract; the overall platform/compiler/host ecosystem remains partial.  
**Source:** frameworks/foundation_66.rpr  
**Dependency:** frameworks/foundation_61_65.rpr  
**Schema:** reaper.software-framework.v1

## Purpose

Software Framework is the umbrella contract for the complete sixty-six-item Reaper foundation catalogue. It does not replace the earlier foundations or introduce another runtime. It imports the first sixty-five stable framework descriptors, appends its own canonical entry and validates catalogue uniqueness, composition order, framework version, implementation profile and extension surface.

## Canonical identity

| Field | Value |
|---|---|
| Framework ID | foundation.software-framework.v1 |
| Display name | Software Framework |
| Schema | reaper.software-framework.v1 |
| Major | 1 |
| Minor | 0 |
| Catalogue entries | 66 |
| Maturity | Partial |

## Integrated surfaces

The umbrella maps the foundational contracts onto actual Reaper components:

- Source and syntax: reaper/lexer.py and reaper/parser.py.
- Reference runtime and module loader: reaper/runtime.py and reaper/modules.py.
- Canonical IR: reaper/ir.py, with partial typed/native lowering.
- Native core and host ABI: src, include/reaper and System Runtime ABI v1.
- Hardware boundary: include/reaper/hardware.h and trusted host/driver adapters.
- Verification: repository tests and GitHub Actions.

The layer catalogue distinguishes implemented from partial. It does not claim a complete native compiler, privileged kernel, universal target backend or physical device access.

## Profiles

| Profile | Engine | Target | Maturity |
|---|---|---|---|
| reference-treewalk | treewalk | hosted-reference | Implemented |
| canonical-vm | canonical-vm | hosted-reference | Implemented |
| native-c17-host | scalar-c17-aot | native-c17-host | Partial |
| simulator | canonical-vm | simulator-adapter | Partial |
| freestanding | native-object | freestanding | Planned |

Planned profiles are rejected. A profile record is a compatibility declaration, not a claim that a compiler or cross-toolchain is installed.

## Manifest

The canonical manifest shape is:

~~~text
[schema, major, minor, framework_id, ordered_framework_ids, capabilities, maturity]
~~~

The 65 constituent IDs must match the prior catalogue in exact dependency order. The major version must match; requested minor versions may not exceed the supported minor version. The manifest declares the umbrella maturity as partial rather than overstating ecosystem completeness.

## Extension points

The framework exposes seven explicit extension points:

1. Language modules — versioned .rpr import/export contracts.
2. Compiler passes — canonical IR transformations with verification evidence.
3. Execution engines — reference interpreter, VM or qualified native route.
4. Host adapters — System Runtime ABI and least-privilege capability grants.
5. Target profiles — CPU, ABI, memory map, linker and toolchain metadata.
6. Interface contracts — versioned producer/consumer schemas.
7. Quality gates — tests, CI and acceptance evidence.

Extensions are validated as declarations only; no module is dynamically loaded or activated.

## Safety contract

The umbrella carries explicit boundaries for network, native FFI, hardware, privilege, workspace mutation and promotion evidence. It does not grant capabilities, perform syscalls, install drivers, flash firmware, open network connections, execute extensions or mutate source repositories.

## Public API

- software_framework_id(), software_framework_name()
- software_framework_ids_65(), software_framework_entry()
- foundation_all_frameworks_66(), foundation_validate_catalog_66()
- software_framework_profiles(), software_framework_validate_profile(profile), software_framework_select_profile(id)
- software_framework_extension_points(), software_framework_capabilities()
- software_framework_validate_extension(extension), software_framework_validate_extensions(extensions)
- software_framework_validate_load_order(ids)
- software_framework_manifest(), software_framework_validate_manifest(manifest)
- software_framework_validate_compatibility(major, minor)
- software_framework_integration_layers(), software_framework_validate_integration_layers()
- software_framework_safety_contract()

## Verification

The Reaper tests execute the module through the reference interpreter. They cover the sixty-six-entry catalogue, manifest shape and ordering, profile maturity, extension validation, compatibility gates and integration-layer inventory. CI results remain the authoritative merge evidence.
