# Reaper foundational frameworks 61–65

**Status:** executable Reaper reference contracts; target deployment and privileged hardware access remain partial or planned.  
**Source:** frameworks/foundation_61_65.rpr  
**Dependency:** frameworks/foundation_56_60.rpr  
**Schema:** reaper.foundation.thirteenth.v1

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 61 | foundation.bridgehead.v1 | Bridgehead | Controlled handoff between source/runtime, host and target | Partial |
| 62 | foundation.anchor-point.v1 | Anchor Point | Stable IDs and versioned references | Partial |
| 63 | foundation.baseline.v1 | Baseline | Fingerprinted snapshots and compatible metric comparisons | Partial |
| 64 | foundation.supporting-structure.v1 | Supporting Structure | Primary/replica/fallback topology and recovery policy | Partial |
| 65 | foundation.hardware-software-base.v1 | Hardware/Software Base | CPU, ABI, memory-map and runtime compatibility descriptor | Partial |

## 61. Bridgehead — controlled handoff

Bridgehead profiles distinguish the hosted reference runtime, scalar C17 host path, simulator adapter, planned firmware staging and read-only device-snapshot inspection. A handoff uses:

~~~text
[bridge_id, protocol_id, payload_bytes, explicit_stage_authorization]
~~~

The protocol identifier and payload bound must match the bridge. Planned firmware staging is rejected. Handoff flags are explicit and do not cause a deployment, flash or device operation.

Public functions: bridgehead_modes(), bridgehead_catalog(), bridgehead_validate_descriptor(bridge), bridgehead_validate_selection(id), bridgehead_validate_handoff(handoff), bridgehead_rules().

## 62. Anchor Point — stable identifiers

Anchor descriptors use:

~~~text
[anchor_id, kind, owner, version, source_reference, stability]
~~~

Kinds include framework, capability, interface, module, diagnostic, target and requirement. Stability is canonical, stable, experimental or deprecated. References are descriptive identifiers and source paths, not dynamic links. Replacement validation requires a deprecated old anchor and canonical new anchor.

Public functions: anchor_kinds(), anchor_stability_levels(), anchor_catalog(), anchor_validate_descriptor(anchor), anchor_validate_reference(id, kind, minimum_version), anchor_validate_catalog(), anchor_validate_replacement(old, new).

## 63. Baseline — reproducible snapshot comparison

A baseline snapshot is:

~~~text
[baseline_id, source_revision, target_profile, fingerprint, metrics, evidence]
~~~

Each metric is [name, numeric_value, unit]. Fingerprints must be 64 characters; this shape check does not recompute or authenticate the digest. Comparisons require the same source revision and target profile, the same metric count and matching metric names/units. Output deltas are right minus left.

Public functions: baseline_metric_units(), baseline_validate_metric(metric), baseline_validate_snapshot(snapshot), baseline_compare(left, right), baseline_validate_pair(left, right).

## 64. Supporting Structure — resilience topology

A component is:

~~~text
[component_id, role, implementation_ref, required_or_optional]
~~~

Roles are primary, replica, fallback, observer and recovery. A structure is [structure_id, components, relations]. Exactly one primary is required. Relations use depends-on, replicates, backs-up, observes or recovers. Failure policies are fail-closed, retry-bounded, fallback, degrade and stop, with explicit retry and timeout bounds.

Public functions: supporting_failure_modes(), supporting_component_roles(), supporting_validate_component(component), supporting_validate_structure(structure), supporting_validate_policy(policy).

## 65. Hardware/Software Base — target and memory contract

Hardware profiles describe target architecture, word size, pointer model, endianness, ABI and runtime profile. Unqualified firmware profiles remain planned and are rejected by selection.

A memory region is [region_id, kind, start, size, permissions]. Region ranges must fit in the 64-bit address descriptor and may not overlap. ROM/Flash are read-only; MMIO uses the device permission. A base descriptor joins a known profile, memory map, firmware label and driver-policy label.

The module validates metadata only. It does not map physical addresses, read/write MMIO, allocate DMA, install drivers, register interrupts or flash firmware. Those actions require trusted OS/driver adapters and separate target qualification.

Public functions: hardware_word_sizes(), hardware_endianness(), hardware_memory_kinds(), hardware_memory_permissions(), hardware_profiles(), hardware_validate_profile(profile), hardware_validate_memory_region(region), hardware_validate_memory_map(regions), hardware_validate_base(base), hardware_safety_boundaries().

## Unified catalogue

The module exposes foundation_all_frameworks_65() and foundation_validate_catalog_65(), extending the previous twelve groups to sixty-five unique framework IDs.

## Usage

~~~reaper
import "../frameworks/foundation_61_65.rpr" as platform

emit platform["foundation_validate_catalog_65"]()
emit platform["bridgehead_validate_handoff"](["bridge.host-reference", "host-python-compat", 1024, false])
emit platform["anchor_validate_reference"]("anchor.reaper.system.abi", "interface", 1)
emit platform["baseline_validate_pair"](["before", "rev1", "host-x86_64", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", [["latency", 100, "milliseconds"]], ["tests/test_runtime_platform.py"]], ["after", "rev1", "host-x86_64", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", [["latency", 120, "milliseconds"]], ["tests/test_runtime_platform.py"]])
emit platform["hardware_validate_memory_map"]([["ram", "ram", 0, 4096, "read-write"], ["mmio", "mmio", 4096, 256, "device"]])
~~~

## Verification and safety

Tests cover bridge maturity and handoff shape, anchor stability, baseline comparability, resilience structure/policy, hardware profile maturity, memory overlap and permission rules. All functions are local validators; no host state or physical device is accessed.
