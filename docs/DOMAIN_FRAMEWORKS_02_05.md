# Reaper Domain Frameworks — batches 02–05

**Scope:** 20 standalone Reaper modules across four domains.  
**Source language:** Reaper `.rpr`.  
**Execution:** existing Reaper reference interpreter.  
**Effects:** pure and deterministic; no ambient host access.

## Platform (02)

| Framework | API | Contract |
|---|---|---|
| Target Profile | `valid_platform_target_profile(profile)` | Coherent architecture, OS, ABI, pointer width and byte order |
| ABI Contract | `valid_platform_abi_contract(contract)` | Calling convention, pointer width, stack alignment and return mode |
| Feature Gate | `platform_missing_features(required, available)` | Missing CPU/target features without implicit grants |
| Cross-Build | `valid_platform_cross_build_plan(plan)` | Host, target and explicitly supported compiler targets |
| Memory Map | `valid_platform_memory_map(regions)` | Typed, positive-size, non-overlapping regions |

## Environment (03)

| Framework | API | Contract |
|---|---|---|
| Manifest | `valid_environment_manifest(entries)` | Unique uppercase environment keys and text values |
| Config Overlay | `resolve_environment_config(layers, key, fallback)` | Last matching key across ordered layers wins |
| Working Root | `safe_environment_path(path)` | Reject absolute, empty and parent-traversal paths |
| Profile Chain | `valid_environment_profile_chain(profiles)` | Unique inheritance chain rooted at `base` |
| Locale Fallback | `resolve_environment_locale(requested, supported, fallback)` | Requested → fallback → English resolution |

## Infrastructure (04)

| Framework | API | Contract |
|---|---|---|
| Service Graph | `valid_infrastructure_service_graph(count, edges)` | Forward-only acyclic service dependencies |
| Resource Allocator | `allocate_infrastructure_resources(demands, capacities)` | Residual capacity after all-or-nothing admission |
| Readiness Gate | `infrastructure_readiness_gate(states, minimum_ready)` | Minimum-ready quorum over explicit service states |
| Failure Domain | `resilient_infrastructure_placement(placements, minimum_domains)` | Unique replicas spread across enough failure domains |
| Health Reducer | `reduce_infrastructure_health(states)` | Worst-state reduction across healthy/degraded/unhealthy |

## Architecture (05)

| Framework | API | Contract |
|---|---|---|
| Layer Architecture | `valid_architecture_layers(count, edges)` | Forward-only layer dependency graph |
| Impact Cone | `architecture_impact_cone(start, count, edges)` | Transitive downstream impact closure |
| Coupling Matrix | `architecture_matrix_profile(matrix)` | Square non-negative matrix; returns nodes and nonzero links |
| Module Boundary | `valid_architecture_module_boundary(count, edges, boundaries)` | Prevent direct dependency edges from skipping protected boundaries |
| Contract Compatibility | `architecture_contract_compatible(required, offered)` | Same-major semantic version, no minor/patch regression |

## Importing

Each module can be imported by itself:

```reaper
import "target_profile.rpr" as target

emit target["valid_platform_target_profile"](["x86_64", "linux", "sysv", 64, "little"])
```

The relative import path is resolved from the importing `.rpr` source file. No module depends on another new module in this batch.

## Verification

```sh
python -m unittest tests.test_framework_programme -v
```

The tests invoke each module through Reaper. They cover one positive and one negative contract fixture per module. The full repository test and native CTest suites remain required.

## Boundaries

- Platform memory maps are metadata validation, not physical memory mapping.
- Cross-build validation checks declared toolchain target support; it does not launch a compiler.
- Environment resolvers operate on explicit lists, not the caller's actual process environment or filesystem.
- Infrastructure health/readiness functions process supplied state values; they do not probe live services or orchestrate them.
- Architecture impact and coupling functions operate on supplied graphs/matrices; they do not inspect source repositories automatically.
