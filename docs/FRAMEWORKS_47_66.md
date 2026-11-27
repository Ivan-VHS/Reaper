# Reaper Frameworks — batches 47–66

**Scope:** 100 distinct Reaper-language modules across the final 20 domains.  
**Source:** `.rpr` modules in `reaper/frameworks/`.  
**Execution:** Reaper reference interpreter.  
**Effects:** explicit arguments only; no ambient host access.

| # | Domain | Frameworks and exported APIs |
|---:|---|---|
| 47 | Блок | Block Range `valid_block_ranges`; Capacity `admit_block_items`; Dependency `valid_block_dependencies`; Slot `missing_block_slots`; Lifecycle `valid_block_lifecycle` |
| 48 | Узел | Node Identity `valid_node_identity`; Ports `valid_node_ports`; Graph `valid_node_graph`; Requirements `missing_node_dependencies`; State `valid_node_state` |
| 49 | Интерфейс | Signature `valid_interface_signature`; Arity `interface_arity_compatible`; Binding `valid_interface_bindings`; Methods `missing_interface_methods`; Version `valid_interface_version_bounds` |
| 50 | Протокол | Frame `valid_protocol_frame`; Sequence `protocol_sequence_admissible`; Handshake `valid_protocol_handshake`; Features `missing_protocol_features`; Message Order `valid_protocol_message_order` |
| 51 | Стандарт | Rule `valid_standard_rule`; Compliance `standard_compliance_threshold`; Scope `standard_scope_applies`; Controls `missing_standard_controls`; Exceptions `valid_standard_exceptions` |
| 52 | Регламент | Policy `valid_regulation_policy`; Decision `regulation_decide`; Roles `valid_regulation_roles`; Controls `missing_regulation_controls`; Review `valid_regulation_review_window` |
| 53 | Спецификация | Parameter `valid_spec_parameter`; Constraints `valid_spec_constraints`; Requirements `missing_spec_requirements`; Traceability `valid_spec_traceability`; Version `valid_spec_version` |
| 54 | Схема | Definition `valid_schema_definition`; Record `schema_accepts_record`; References `valid_schema_references`; Required Fields `schema_missing_required_fields`; Migration `valid_schema_migration` |
| 55 | Матрица | Square `valid_square_numeric_matrix`; Multiplication `matrix_product_compatible`; Row Totals `matrix_row_totals`; Diagonal `matrix_diagonal`; Sparsity `matrix_nonzero_count` |
| 56 | Сетка | Shape `valid_grid_shape`; Cell `grid_cell_inside`; Neighbours `grid_neighbors4`; Occupancy `valid_grid_occupancy`; Distance `grid_manhattan_distance` |
| 57 | Контур | Graph `valid_circuit_graph`; Reachability `circuit_reachable`; Branches `valid_circuit_branch_count`; Redundancy `valid_circuit_redundancy`; State `valid_circuit_state_sequence` |
| 58 | Периметр | Zone `valid_perimeter_zone`; Action `perimeter_action_allowed`; Rules `valid_perimeter_rules`; Routes `missing_perimeter_routes`; Rate Limit `valid_perimeter_rate_limit` |
| 59 | Рабочая среда | Manifest `valid_work_environment_manifest`; Overlay `resolve_work_environment_value`; Tools `valid_work_environment_tools`; Locale `resolve_work_environment_locale`; Limits `valid_work_environment_limits` |
| 60 | Рабочая область | Layout `valid_workspace_layout`; Artifacts `valid_workspace_artifact_paths`; Directories `missing_workspace_directories`; Project `valid_workspace_project_selection`; Quota `valid_workspace_quota` |
| 61 | Плацдарм | Manifest `valid_staging_manifest`; Promotion `staging_promotion_allowed`; Rollback `staging_rollback_order`; Provenance `valid_staging_provenance`; Gate `valid_staging_gate` |
| 62 | Опорная точка | Identity `valid_anchor_identity`; Resolve `resolve_anchor_target`; Bindings `valid_anchor_bindings`; Version Pin `anchor_version_pinned`; References `missing_anchor_references` |
| 63 | Базовая линия | Snapshot `valid_baseline_snapshot`; Drift `baseline_drift_metrics`; Coverage `missing_baseline_metrics`; Profile `valid_baseline_profile`; Regression `baseline_regression_within_budget` |
| 64 | Несущая конструкция | Capacity Profile `valid_load_bearing_profile`; Distribution `balanced_load_distribution`; Margin `load_bearing_margin`; Redundancy `valid_load_redundancy`; Members `valid_load_bearing_members` |
| 65 | Аппаратно-программная база | Device Profile `valid_hardware_device_profile`; Memory Map `valid_hardware_memory_map`; Driver ABI `valid_hardware_driver_abi`; DMA Buffer `valid_dma_buffer_contract`; MMIO Register `valid_hardware_mmio_register` |
| 66 | Программный каркас | Application `valid_software_skeleton_manifest`; Composition `valid_software_skeleton_composition`; Modules `missing_software_skeleton_modules`; Entrypoint `valid_software_skeleton_entrypoint`; Lifecycle `valid_software_skeleton_lifecycle` |

## Contract details

The exact arguments and expected results for every operation live in the machine-readable [framework index](../reaper/frameworks/framework-index.v1.json). Tests load every module independently, execute the declared positive and negative fixtures through Reaper, and compare the result.

### Important boundaries

- Block ranges, circuit graphs and module compositions validate caller-supplied data; they do not allocate hardware or schedule live work.
- Interface and protocol modules validate shapes, compatibility and ordering; they do not open sockets or manage live sessions.
- Regulation decisions are local contract evaluation, not an OS authorization boundary or a replacement for the host consent/capability authority.
- Workspace and staging modules validate paths and metadata but do not write, publish, promote or roll back files.
- Baseline modules compare supplied measurement values; they do not benchmark the machine.
- Hardware modules validate metadata only. MMIO and DMA adapters do not map physical addresses or operate devices.
- Software-skeleton modules validate manifests and dependency graphs; they do not instantiate a process or supervisor.

No module claims native compiler parity or privileged runtime access that the current Reaper implementation does not provide.