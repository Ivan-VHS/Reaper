# RFS-01 — Rhythm-Field Syntax and BlockPulse Architecture

**Status:** executable Reaper-source reference model in `stdlib/rfs01.rpr`. The symbolic operator spellings in the original RFS sketch are documented mappings, not additions to Reaper's lexer or parser. Native C17, self-hosted frontend parity and physical/network effects are not claimed.

## Purpose

RFS-01 models a bounded network of spatial nodes and directed links. It treats pressure, integrity, noise, signal quality, root identity and synchronization as explicit data. The implementation is a Reaper library that composes with the existing Scenario Flow and module system; it does not introduce a second interpreter.

## Canonical executable grammar

Use the current Reaper grammar and explicitly imported functions:

```rpr
import "../stdlib/rfs01.rpr" as rfs

make root := rfs["rfs_node_make"](
    "block-a", "Basement", 10, 0.40, 0.80,
    "root-seed-a", ["old-wire"], true, [], "Dormant"
)

make edge := rfs["rfs_link_make"](
    "gate-a-b", "block-a", "block-b", "Wire", true, 0.80,
    ["rfs.key.v1", "root-seed-a", ["old-wire"]]
)

make mesh := rfs["rfs_awaken_grid"]([root[1], peer[1]], [edge[1]], 5)
```

Every exported function (except the exported constant lists and limits) returns a tagged result: `["ok", value]` or `["err", diagnostic_code, message]`. Callers must check the tag before reading the value.

## Symbolic notation and compatibility

| RFS sketch | Meaning in the RFS model | Current executable Reaper form | Parser status |
|---|---|---|---|
| `::` as a state/node separator | Node construction or transition boundary | `rfs_node_make(...)`, `rfs_shift(...)` | `::` remains Reaper's first-argument data-flow operator; never redefined |
| `<>` | Explicit boundary between states | `rfs_phase_gate(...)` or a versioned record | Not added |
| `~>` | Directed pressure/signal transfer | `rfs_shift(source, target, pressure)` | Not added |
| `>>` | Forward field transition | `rfs_shift(source, target, pressure)` | Not added |
| `<<` | Reverse field transition | `rfs_shift(target, source, pressure)` | Not added |
| `[phase : threshold]` | A named phase gate with an observed value and threshold | `rfs_phase_gate(phase, observed, threshold)` | Not added as a bracket grammar |
| `||` | Contrast in the sketch | `rfs_contrast(left, right)` | `||` retains its existing logical-OR meaning |
| `^^` | Contrast composition notation | `rfs_contrast(left, right)` | Not added |
| `<-root` | Validate and reclaim the mesh root from a pulse | `rfs_reclaim_root(mesh, pulse)` | Not added |
| `^core` | Derive a bounded spark from the root node | `rfs_ignite_from_core(mesh)` | Not added |

These spellings must not be pasted into ordinary `.rpr` source as if they were implemented operators. A future surface-grammar proposal requires token-collision analysis, grammar and precedence rules, parser diagnostics, Canonical IR lowering, VM parity, native-C acceptance fixtures and editor/LSP support.

## Data contracts

### Node

`["rfs.node.v1", id, layer, pressure, integrity, noise, core_seed, history, awake, route, state]`

- Layers: `Basement`, `Corridor`, `Gate`, `Skyline`, `Horizon`.
- `id` and `core_seed` are non-empty text identifiers. They are not cryptographic hashes or secrets.
- `pressure` and `noise` are finite, non-negative numbers bounded by the supported U64 numeric range.
- `integrity` is in the inclusive interval `0...1`.
- `history` and `route` are lists; `awake` is boolean.
- State is one of `Dormant`, `Active`, `Dissonant`.

`rfs_node_make(...)` creates and validates a node. `rfs_node_validate(node)` returns a stable diagnostic when a field or invariant is invalid.

### Link

`["rfs.link.v1", id, origin_id, target_id, channel, blocked, weight, required_key]`

Channels: `Wire`, `Rail`, `Beat`, `Current`, `Bridge`. Link weight is in `0...1`. A required key is `nothing` or a record.

`rfs_link_make(...)` validates the record. `rfs_awaken_grid(nodes, links, high_load)` validates endpoints and duplicate identities before returning a mesh.

**Unlock boundary:** the sample key is a structural tuple derived from a node's `core_seed` and `history`. It demonstrates deterministic salvage matching only. It is not cryptographic authentication, an access-control token, a physical gate unlock or a device permission. Real host actions require independent host authorization.

### Mesh

`["rfs.mesh.v1", nodes, links, root_id, cycle, status, metrics]`

The mesh must have at least one node. Node and link IDs must be unique; all link endpoints must exist; `root_id` must name a node. Limits are 4,096 nodes, 8,192 links, and 108 synchronization cycles.

The root is selected from the first supplied node at mesh construction. Synchronization never rewrites it. `rfs_reclaim_root(mesh, pulse)` verifies that the pulse carries that root and that the root still exists.

### Signal and scoreboard

Frame: `["rfs.frame.v1", has_origin_truth, is_manufactured_hype, payload, resonance]`.

Stream: `["rfs.stream.v1", frames]`; scoreboard: `["rfs.scoreboard.v1", score]`; clean signal: `["rfs.signal.v1", verified_frames, coherence]`.

`rfs_filter_static_and_score(stream, scoreboard)` resets the returned scoreboard to zero, retains only frames with `has_origin_truth == true` and `is_manufactured_hype == false`, projects accepted payloads onto `CoreIntent`, and computes coherence as the arithmetic mean of accepted frame resonance. An empty accepted set has coherence zero. The original input values are not mutated.

Frame input is bounded by 100,000 items. Resonance and resulting coherence are in `0...1`.

## Transition semantics

### Pressure-to-axis

`rfs_pressure_rule(node, threshold)` emits `backbone_holds` only when `node.pressure > threshold` and `node.integrity > 0`. The returned transition contains a `bone_load` to `backbone_lock` shift and a contrast record for `external_noise` versus `inner_calm`.

`rfs_phase_gate(phase, observed, threshold)` returns a phase record with an explicit boolean indicating whether the observed value meets or exceeds the threshold.

Basement reinforcement in `rfs_awaken_grid` applies:

`integrity' = clamp(integrity + pressure * 0.15, 0, 1)`

`noise' = clamp(noise * 0.6, 0, U64_MAX)`

Other node layers retain their original integrity and noise. Inputs are validated before this transformation.

### Gate salvage and bridge rerouting

For a blocked link, the library derives `["rfs.key.v1", origin.core_seed, origin.history]`. The link is switched to channel `Bridge` and unblocked only when this value exactly matches `required_key`. A mismatch leaves it blocked and preserves its channel.

### Collective loop

`rfs_run_collective_loop(mesh, signal, max_cycles)`:

1. Validates the mesh, signal and cycle budget.
2. Derives a spark from root integrity and noise.
3. Forms a bounded intent value from signal coherence plus spark energy.
4. Creates a pulse carrying the immutable root ID and verified frames.
5. Validates the root in the pulse.
6. Synchronizes nodes by setting `awake = true`, state to `Active`, and appending the root to each route without duplicates. This models `allow_late_join = true`.
7. Detects dissonance when integrity is below `0.5`, noise is above `0.5`, or a link remains blocked.
8. When dissonance is present, moves each unblocked, non-Bridge link weight halfway toward the average of that same class. Bridge weights are preserved.
9. Stops when all nodes are active or the explicit cycle limit is reached.

The current reference model normally synchronizes eligible records in one pass. The 108-cycle maximum is a safety bound, not a target or a claim of parallel distributed execution.

## Public API

| Function | Responsibility |
|---|---|
| `rfs_node_make`, `rfs_node_validate` | Node construction and public validation |
| `rfs_link_make`, `rfs_link_validate` | Link construction and public validation |
| `rfs_mesh_make`, `rfs_mesh_validate` | Mesh identity, endpoint and bound validation |
| `rfs_awaken_grid` | Basement pressure transformation and gate salvage |
| `rfs_frame_make`, `rfs_frame_validate` | Signal-frame construction and validation |
| `rfs_signal_validate` | Public clean-signal shape and coherence validation |
| `rfs_filter_static_and_score` | Noise/hype filtering, coherence and scoreboard reset |
| `rfs_phase_gate` | Explicit phase threshold evaluation |
| `rfs_contrast`, `rfs_shift` | Tagged contrast and directed transition values |
| `rfs_pressure_rule` | Pressure-to-backbone transition |
| `rfs_ignite_from_core` | Validated bounded spark derived from the root node |
| `rfs_reclaim_root` | Verify root identity in a pulse |
| `rfs_run_collective_loop` | Bounded node synchronization and tension rebalance |
| `rfs_main_block_engine` | Compose grid, signal and collective phases into one result |

`rfs_main_block_engine(environment)` accepts `["rfs.environment.v1", blocks, gates, stream, scoreboard, high_load, max_cycles]` and returns a result record containing the mesh snapshot, reset scoreboard and a telemetry descriptor. The telemetry descriptor is data only; no telemetry is sent or persisted.

## Failure and safety model

- Stable diagnostics use the `RPR-RFS-*` namespace.
- Invalid schemas, unknown layers/channels, duplicate IDs, missing endpoints, invalid numeric ranges, bad root pulses and over-limit collections fail with an error result.
- The implementation is deterministic and local. It opens no files, sockets, processes, device handles or native libraries.
- `core_seed`, `history` and `required_key` are illustrative structural data. Do not use them as authentication material.
- Integrity and coherence are model metrics, not proofs, cryptographic digests or hardware measurements.
- The library does not schedule threads, perform distributed consensus, establish transport channels, access MMIO/DMA/IRQ, or emit external telemetry.
- C17 and self-hosted parity remain open acceptance gates.

## Verification

- `examples/rfs01_blockpulse.rpr` demonstrates the complete BlockPulse pipeline.
- `selfhost/rfs01_conformance.rpr` is executed by the existing Reaper reference-runtime self-hosting harness.
- The fixture covers node/link validation, pressure saturation, attenuation, valid/invalid gate keys, source-truth filtering, hype rejection, phase thresholds, root preservation, late-join synchronization, cycle limits and duplicate-ID rejection.

The RFS-01 Reaper-source model is implemented for the reference runtime only. Do not mark the feature native or fully self-hosted until the equivalent compiler/frontend paths and differential tests exist.
