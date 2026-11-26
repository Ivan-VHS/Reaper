# Construction, Ecosystem, Overlay, Shell and Runtime Frameworks — batches 12–16

## Construction (12)

- `valid_construction_manifest`: unique build artifacts, types and size limits.
- `construction_select_variant`: first variant compatible with the available feature set.
- `construction_merge_flags`: inherited flags merged with local overrides.
- `construction_build_cost`: bounded build-step cost sum.
- `valid_construction_artifact_graph`: acyclic transformation dependencies.

## Ecosystem (13)

- `valid_ecosystem_peer_mesh`: peer link integrity, no self-links, every peer participates in both directions.
- `ecosystem_missing_peers`: required/active peer difference.
- `valid_ecosystem_version_matrix`: unique peer versions on one major compatibility line.
- `ecosystem_peer_quorum`: minimum healthy-peer threshold.
- `ecosystem_capability_owner`: first explicitly declared peer that owns a capability.

## Overlay (14)

- `overlay_merge_layers`: later configuration layers replace earlier keys.
- `overlay_conflicting_keys`: reports keys assigned different values in distinct layers.
- `overlay_apply_patch`: applies a key/value patch while preserving order.
- `overlay_remove_tombstones`: removes explicitly deleted records.
- `overlay_highest_priority`: deterministic highest-priority selection.

## Shell (15)

- `valid_shell_command_request`: validate a command request structure, but never launch it.
- `shell_command_allowed`: exact executable allowlist check.
- `valid_shell_pipeline`: check producer/consumer hand-off compatibility.
- `valid_shell_argument_vector`: explicit argument vector validation without implicit splitting.
- `shell_exit_status_class`: classify an observed exit code; no process is started.

## Runtime (16)

- `valid_runtime_quotas`: validate step/depth/heap/collection quotas.
- `runtime_step_admission`: bounded step reservation.
- `runtime_resource_total`: named resource ledger total.
- `valid_runtime_cancellation_transition`: cooperative cancellation state machine.
- `runtime_budget_remaining`: remaining budget after reservation.

All modules are pure Reaper code. Shell frameworks validate requests only; they do not execute shell commands. Ecosystem frameworks consume supplied peer manifests and do not establish network connections. Runtime frameworks calculate policy and quota state; they do not replace Reaper's actual interpreter resource manager.
