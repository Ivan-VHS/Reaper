# Reaper foundational frameworks 16–20

**Status:** executable Reaper reference contracts; native/host integration remains partial.  
**Source:** `frameworks/foundation_16_20.rpr`  
**Dependency:** `frameworks/foundation_11_15.rpr`  
**Schema:** `reaper.foundation.fourth.v1`

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 16 | `foundation.runtime.v1` | Runtime | Lifecycle transitions, terminal states and resource scopes | Partial |
| 17 | `foundation.execution-context.v1` | Execution Context | Engine/platform selection and bounded quotas | Partial |
| 18 | `foundation.engine.v1` | Engine | Tree-walk, canonical VM and scalar C17 route contracts | Partial |
| 19 | `foundation.kernel.v1` | Kernel | Trusted host ABI, capability and request validation | Partial |
| 20 | `foundation.library.v1` | Library | Versioned runtime-module descriptors and dependency compatibility | Partial |

## 16. Runtime — lifecycle ownership

Runtime lifecycle is represented as an explicit trace beginning at `created` and ending at `stopped` or `failed`. Transitions are closed and ordered; terminal states cannot be followed by more states. Resource scopes distinguish execution, module, function, region and host ownership. This contract does not implement a scheduler, task pre-emption, kernel process lifecycle or asynchronous cancellation.

Public functions: `runtime_lifecycle_states()`, `runtime_lifecycle_transitions()`, `runtime_resource_scopes()`, `runtime_validate_transition(from, to)`, `runtime_validate_scope(scope)`, `runtime_validate_lifecycle(trace)`, `runtime_lifecycle_contract()`.

## 17. Execution Context — bounded session profile

An execution context is:

`[engine, platform_profile, max_steps, max_call_depth, max_collection_items, max_text_length]`

The validator accepts the currently available hosted reference, native C17 host and simulator-adapter profiles. Engine status is checked: planned engines are rejected. All four quotas must be positive whole numbers.

Public functions: `execution_engines()`, `execution_context_fields()`, `execution_validate_context(context)`, `execution_default_context()`.

## 18. Engine — execution and compilation routes

The catalogue differentiates the tree-walk interpreter and canonical-IR VM (implemented), scalar C17 AOT (partial) and target object generation (planned). Route validation preserves the actual stage order and rejects planned output paths.

Public functions: `engine_catalog()`, `engine_routes()`, `engine_validate_selection(selection)`, `engine_validate_route(route)`.

## 19. Kernel — trusted host boundary

The capability vocabulary is aligned with the symbolic capability constants in `include/reaper/system.h`. Operation descriptors bind an operation to its required capability. Adapter descriptors accept only ABI v1 and an explicit trusted-host or simulator kind. Request payloads are bounded to one MiB.

This is a contract validator only. It does not enter kernel mode, issue syscalls, grant permissions, map physical memory, install drivers or authenticate caller-supplied process identity. The adapter/host remains authoritative.

Public functions: `kernel_domains()`, `kernel_capabilities()`, `kernel_operation_catalog()`, `kernel_validate_capabilities(values)`, `kernel_validate_adapter(adapter)`, `kernel_validate_request(request)`, `kernel_authority_rules()`.

## 20. Library — reusable module contracts

The module catalogue mirrors existing Reaper package modules and distinguishes implemented, partial and opt-in components. A dependency descriptor is:

`[module_id, major, minor]`

The public descriptor is:

`[module_id, major, minor, access]`

Access is `import`, `export` or `inspect`. Major versions must match and requested minor versions may not exceed the published minor version. Dependencies must be unique. This catalogue does not turn Python modules into importable `.rpr` modules and does not claim a complete source-level standard library.

Public functions: `library_modules()`, `library_validate_descriptor(descriptor)`, `library_validate_dependencies(dependencies)`.

## Unified catalogue

The module adds `foundation_all_frameworks_20()` and `foundation_validate_catalog_20()`, extending all prior groups to twenty unique framework IDs.

## Usage

```reaper
import "../frameworks/foundation_16_20.rpr" as runtime

emit runtime["runtime_validate_lifecycle"](["created", "initialized", "ready", "running", "draining", "stopped"])
emit runtime["execution_validate_context"](["treewalk", "hosted-reference", 1000000, 256, 100000, 1000000])
emit runtime["engine_validate_selection"](["canonical-vm", "canonical-ir", "runtime-value"])
emit runtime["kernel_validate_request"](["filesystem.read", "FS_READ", 4096])
emit runtime["library_validate_dependencies"]([["reaper.modules", 1, 0], ["reaper.resources", 1, 0]])
emit runtime["foundation_validate_catalog_20"]()
```

## Verification and safety

Tests cover valid/invalid lifecycle traces, execution quotas, engine routes, ABI capabilities, bounded host requests and library compatibility. The module has no process, syscall, filesystem, network, loader, privilege or device side effects.
