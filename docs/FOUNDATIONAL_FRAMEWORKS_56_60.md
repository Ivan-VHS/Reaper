# Reaper foundational frameworks 56–60

**Status:** executable Reaper reference contracts; actual OS isolation and workspace mutation remain host-owned.  
**Source:** frameworks/foundation_56_60.rpr  
**Dependency:** frameworks/foundation_51_55.rpr  
**Schema:** reaper.foundation.twelfth.v1

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 56 | foundation.grid.v1 | Grid | Named axes, coordinates and cell coverage | Partial |
| 57 | foundation.contour.v1 | Contour | Subsystem boundary ports and invariants | Partial |
| 58 | foundation.perimeter.v1 | Perimeter | Trust zones, directional rules and default-deny decisions | Partial |
| 59 | foundation.working-environment.v1 | Working Environment | Reproducible host/build/test environment descriptors | Partial |
| 60 | foundation.workspace.v1 | Workspace | Logical roots, module membership and mutation state | Partial |

## 56. Grid — coordinate and coverage model

A grid descriptor is:

~~~text
[grid_id, axes, row_coordinates, column_coordinates]
~~~

Each axis is [axis_kind, axis_name, extent]. Row and column coordinates are explicit identifiers; cells use [row, column, value]. The validator requires complete unique coverage for the two coordinate dimensions.

Public functions: grid_axis_kinds(), grid_validate_axis(axis), grid_validate_descriptor(grid), grid_validate_cells(grid, cells), grid_validate_coordinate(grid, coordinate).

## 57. Contour — subsystem boundary

A contour descriptor is:

~~~text
[contour_id, owner, ports, invariants]
~~~

A port is [port_id, direction_kind, interface_id, contract_version]. Connections require matching interface/version and an input/output pair. Control, resource and trust ports remain named boundary types but require distinct policy checks before they are operational.

Public functions: contour_boundary_kinds(), contour_validate_port(port), contour_validate_descriptor(contour), contour_validate_connection(left, right).

## 58. Perimeter — trust-zone policy

Trust zones are untrusted-input, application, runtime, trusted-host and privileged-adapter. A rule uses:

~~~text
[source_zone, target_zone, direction, operation, decision]
~~~

Decisions are allow, deny and audit. Unknown paths default to deny; duplicate rule keys are rejected. This is a policy descriptor and decision helper, not a network firewall or OS security boundary.

Public functions: perimeter_trust_zones(), perimeter_directions(), perimeter_validate_rule(rule), perimeter_default_policy(), perimeter_validate_policy(policy), perimeter_decision(policy, source, target, direction, operation).

## 59. Working Environment — reproducible process context

Profiles cover the hosted developer runtime, native C17 build, test simulator and planned embedded cross-build environment. Planned profiles are not accepted. Variable names must be unique; secret-like variable names are rejected so secrets are not modeled as ordinary environment values.

Public functions: working_environment_profiles(), working_environment_validate_profile(profile), working_environment_validate_variables(variables), working_environment_requirements().

## 60. Workspace — project boundary and state

A workspace descriptor is:

~~~text
[workspace_id, project_root, source_root, build_root, state, module_paths]
~~~

Roots are logical relative paths, not filesystem operations. Source and build roots must remain beneath the project root. Module paths must be relative .rpr files and unique. Membership checks constrain a logical path beneath the project root. Mutation is allowed only for clean/modified states; read-only, locked and invalid workspaces reject mutation.

Public functions: workspace_states(), workspace_validate_root(root), workspace_validate_descriptor(workspace), workspace_validate_membership(workspace, path), workspace_mutation_allowed(workspace).

## Unified catalogue

The module exposes foundation_all_frameworks_60() and foundation_validate_catalog_60(), extending the first eleven groups to sixty unique framework IDs.

## Usage

~~~reaper
import "../frameworks/foundation_56_60.rpr" as workspace

emit workspace["foundation_validate_catalog_60"]()
emit workspace["perimeter_decision"](workspace["perimeter_default_policy"](), "application", "trusted-host", "egress", "capability-grant")
emit workspace["working_environment_validate_profile"](["developer-host", "hosted-reference", "local", "network-disabled-by-default", "implemented"])
emit workspace["workspace_validate_descriptor"](["reaper", "projects/reaper", "projects/reaper/src", "projects/reaper/build", "clean", ["modules/main.rpr"]])
emit workspace["workspace_mutation_allowed"](["reaper", "projects/reaper", "projects/reaper/src", "projects/reaper/build", "read-only", []])
~~~

## Verification and safety

Tests validate grid coverage, contour port compatibility, perimeter policy decisions, environment profiles/variables and workspace roots/membership/state. These are pure declarative checks: they do not create a filesystem workspace, change environment variables, isolate a process, install a sandbox or enforce OS access controls.
