# Reaper foundational frameworks 26–30

**Status:** executable Reaper reference contracts; full target build, source generation and typed-native integration remain partial.  
**Source:** `frameworks/foundation_26_30.rpr`  
**Dependency:** `frameworks/foundation_21_25.rpr`  
**Schema:** `reaper.foundation.sixth.v1`

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 26 | `foundation.technology-stack.v1` | Technology Stack | Compiler/ABI/linker/runtime target profile | Partial |
| 27 | `foundation.template.v1` | Template | Validated project/module template requests | Partial |
| 28 | `foundation.skeleton.alias.v1` | Skeleton | Canonical alias to the existing Skeleton implementation | Implemented |
| 29 | `foundation.boilerplate.v1` | Boilerplate | Reusable Reaper starter source fragments | Implemented |
| 30 | `foundation.base-layer.v1` | Base Layer | Evidence-backed minimum language-core inventory | Partial |

## 26. Technology Stack — target composition

Profiles distinguish hosted C17 host development, Windows MSVC-compatible host builds and planned ARM/RISC-V firmware targets. A stack records target, ABI, compiler family and maturity. A profile being catalogued does not imply the named compiler is installed or that target code generation is qualified.

Public functions: `technology_stack_profiles()`, `technology_stack_validate_profile(profile)`, `technology_stack_validate_selection(id)`, `technology_stack_requirements()`.

## 27. Template — validated project inputs

Templates define required string bindings for CLI tools, library modules, test suites and embedded workspaces. Requests use:

`[template_id, [[field_name, field_value], ...]]`

Unknown, duplicate, missing or empty fields are rejected. The validator produces a plan only; it does not write files or substitute content into the repository.

Public functions: `template_catalog()`, `template_validate_request(request)`, `template_plan(request)`.

## 28. Skeleton — canonical alias

The original Skeleton framework remains authoritative at `foundation.skeleton.v1` from group 6–10. This group registers the repeated term as `foundation.skeleton.alias.v1` and resolves it to the existing implementation. There is no duplicate skeleton runtime or conflicting component schema.

Public functions: `skeleton_alias_catalog()`, `skeleton_alias_resolve(name)`, `skeleton_alias_validate(alias)`.

## 29. Boilerplate — starter source fragments

The registry supplies small Reaper source fragments for an entry point, identity function, exported constant and bounded list flow. A caller can inspect a fragment by ID or validate a unique selection. This is not a code generator, does not create files and does not claim the fragments fit every application or target profile.

Public functions: `boilerplate_catalog()`, `boilerplate_validate_selection(ids)`, `boilerplate_source(id)`.

## 30. Base Layer — minimum language core

The base-layer inventory identifies source-backed features and their maturity: syntax, bindings/scopes, module loading, reference runtime and resource limits are implemented; canonical IR, static type analysis, ownership/effects and native target lowering remain partial.

A base profile must include the five required working-core features and may add only known catalogue IDs. This stops a profile from being described as a working Reaper base if it omits module loading or runtime/resource semantics.

Public functions: `base_layer_catalog()`, `base_layer_required_features()`, `base_layer_validate_profile(features)`, `base_layer_status(id)`.

## Unified catalogue

The module exposes `foundation_all_frameworks_30()` and `foundation_validate_catalog_30()`, extending all prior groups to thirty unique framework IDs. The Skeleton alias is separately identified and points back to the original canonical contract.

## Usage

```reaper
import "../frameworks/foundation_26_30.rpr" as base

emit base["foundation_validate_catalog_30"]()
emit base["technology_stack_validate_selection"]("hosted-c17-x86_64")
emit base["template_validate_request"](["cli-tool", [["project_name", "sample"], ["entry_module", "main.rpr"]]])
emit base["skeleton_alias_resolve"]("Skeleton")
emit base["boilerplate_source"]("identity-function")
emit base["base_layer_validate_profile"](["core-syntax", "scopes-and-bindings", "module-loading", "reference-runtime", "resource-limits"])
```

## Verification and safety

Tests verify target profile maturity, template bindings, alias stability, boilerplate lookup and base-layer completeness. This module performs no target compilation, filesystem writes, code execution, installation, network access or privileged operation.
