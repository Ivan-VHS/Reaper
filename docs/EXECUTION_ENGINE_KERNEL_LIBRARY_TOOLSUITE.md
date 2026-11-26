# Execution, Engine, Kernel, Library and Tool Suite Frameworks — batches 17–21

## Execution Environment (17)
- `valid_execution_profile`: coherent runtime mode / allocator / threads / host-I/O profile.
- `valid_execution_phase_order`: canonical load → initialize → run → shutdown sequence.
- `valid_execution_scheduler_weights`: unique positive bounded scheduler weights.
- `valid_execution_resource_lifetimes`: acquisition/release intervals and unique IDs.
- `valid_execution_host_effect_policy`: requested effects must be granted and allowlisted, and not denied.

## Engine (18)
- `valid_engine_pipeline`: type continuity across compiler/engine stages.
- `valid_engine_optimization_passes`: unique passes ordered by phase.
- `engine_missing_backend_features`: backend feature gap report.
- `engine_cache_key`: deterministic key from explicit text components.
- `engine_within_optimization_budget`: bounded work × iteration admission.

## Kernel (19)
- `valid_kernel_interrupt_vectors`: bounded unique IRQ vectors/handlers.
- `valid_kernel_privilege_transition`: explicit user/kernel transition reasons.
- `valid_kernel_memory_protection_map`: non-overlapping regions with W^X policy.
- `valid_kernel_syscall_contracts`: stable syscall numbers/names/arity.
- `valid_kernel_handle_table`: validated object handles, generations and owners.

## Library (20)
- `valid_library_dependency_constraint`: inclusive semantic version range.
- `valid_library_export_table`: unique exported symbols and signatures.
- `valid_library_module_visibility`: unique module IDs and visibility.
- `valid_library_dependency_graph`: acyclic import/dependency graph.
- `library_select_highest_version`: highest offered version on selected major.

## Tool Suite (21)
- `valid_tool_suite_manifest`: unique tool names with version and target.
- `valid_tool_suite_command`: explicit bounded command structure; not executed.
- `tool_suite_capability_owner`: resolve declared tool capability.
- `valid_tool_suite_output_record`: validate exit code and output-size record.
- `tool_suite_target_supported`: verify a target triple in a tool's declaration.

Kernel and shell/tool-suite APIs remain data-level contracts. They do not access physical memory, install drivers, execute commands, or create processes.
