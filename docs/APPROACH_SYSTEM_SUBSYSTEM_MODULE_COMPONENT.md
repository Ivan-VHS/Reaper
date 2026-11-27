# Approach, System, Subsystem, Module and Component Frameworks — batches 42–46

## Approach (42)
- `valid_approach_strategy`: explicit strategy, trade-offs, phases and review cadence.
- `approach_select_strategy`: highest-score strategy satisfying mandatory requirements.
- `valid_approach_sequence`: task permutation respecting prerequisite edges.
- `valid_approach_risk_register`: unique bounded probability/impact risks and mitigations.
- `valid_approach_acceptance`: evidence reference for every objective.

## System (43)
- `valid_system_manifest`: named versioned system and unique services.
- `valid_system_composition`: acyclic service composition.
- `reduce_system_health`: worst state across system services.
- `valid_system_configuration`: unique text configuration.
- `valid_system_resource_budget`: allocations within declared resource ceilings.

## Subsystem (44)
- `valid_subsystem_boundary`: provided/consumed contract lists.
- `valid_subsystem_ownership`: unique resource ownership assignments.
- `valid_subsystem_lifecycle`: explicit lifecycle transitions.
- `valid_subsystem_dependencies`: acyclic subsystem dependency graph.
- `valid_subsystem_isolation`: required isolation flags.

## Module (45)
- `valid_module_import_contract`: unique imports, version and visibility.
- `valid_module_export_contract`: unique exported symbols and signatures.
- `valid_module_dependency_graph`: acyclic import graph.
- `module_version_compatible`: same-major, non-regressing minor.
- `valid_module_interface`: stable interface identifier and unique methods.

## Component (46)
- `valid_component_contract`: identity, semver, lifecycle profile and entrypoint.
- `valid_component_ports`: unique typed input/output ports.
- `valid_component_wiring`: type-compatible component port connections.
- `valid_component_lifecycle`: explicit component state transitions.
- `component_contract_compatible`: offered version in inclusive compatibility bounds.

These are data/contract modules. System/subsystem lifecycle and health models do not start or supervise real services; component wiring does not instantiate components.
