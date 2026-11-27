# Middleware, Integration, Container, Host and Context Frameworks — batches 32–36

## Middleware (32)
- `valid_middleware_chain`: typed stage continuity and ordered phases.
- `middleware_missing_requirements`: pipeline capability gap report.
- `valid_middleware_effect_policy`: explicit grant/allow/deny effect policy.
- `middleware_short_circuited`: detect a terminating stage.
- `middleware_within_budget`: summed stage latency budget gate.

## Integration Software (33)
- `valid_integration_map`: versioned project/interface endpoint mapping.
- `integration_missing_endpoints`: disconnected endpoint report.
- `integration_version_compatible`: same-major protocol compatibility.
- `valid_integration_federation_graph`: acyclic project federation graph.
- `valid_integration_data_contract`: versioned field/type schema.

## Container (34)
- `valid_container_manifest`: declarative image and privilege profile.
- `valid_container_mounts`: unique safe mount targets with explicit read-only policy.
- `valid_container_namespaces`: PID/network/mount/user namespace declaration.
- `valid_container_quotas`: CPU/memory/process limits.
- `valid_container_lifecycle_transition`: explicit container lifecycle state machine.

## Host (35)
- `valid_host_abi`: host architecture, ABI, word size and byte order.
- `host_missing_features`: missing host capability report.
- `valid_host_call_contract`: named host call with signature and explicit effects.
- `valid_host_capabilities`: unique declared host capability set.
- `host_supports_target`: host target support lookup.

## Context (36)
- `valid_context_entries`: unique typed context values.
- `valid_context_scope_tree`: rooted scope hierarchy and reachability.
- `valid_context_snapshot`: snapshot identity/revision/digest metadata.
- `context_merge_values`: local-over-base shadowing.
- `context_within_budget`: aggregate context text budget.

These modules validate supplied metadata only. Container/host contexts are not actual OS isolation boundaries; they do not create namespaces, mount filesystems, or invoke host calls.
