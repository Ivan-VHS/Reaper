# Mora archive contracts

**Status:** executable Reaper reference-runtime module  
**Module:** `mora/archive_contracts.rpr`  
**Fixture:** `examples/mora_archive_contracts.rpr`

Mora archive validation is implemented as ordinary Reaper `.rpr` source. The module is intentionally pure: it validates supplied values and returns diagnostics. It does not start a desktop shell, perform audio playback, access files, read the clock, use the network, collect telemetry or modify user data.

The current Reaper grammar does not yet parse typed `contract` declarations or the `Shell` host API shown in early design sketches. This module therefore uses the supported `export craft`, list, control-flow and function-call syntax. It is executable with the current reference runtime; it does not claim native C17 compiler parity.

## Run

From the repository root:

```sh
python -m reaper examples/mora_archive_contracts.rpr
```

The fixture runs the successful archive checks and negative regression cases. It exits with an error when an assertion fails. CI executes this fixture on the supported reference-runtime matrix.

## Record layouts

The current expression grammar has list literals and indexed access, but no parsed named-record declarations. To keep the boundary explicit, each record has a fixed positional layout.

| Record | Field order |
|---|---|
| Performance budget | target frame ms, measured frame p95 ms, target input p95 ms, measured input p95 ms, RAM limit MiB, measured RAM MiB, idle CPU limit %, measured idle CPU % |
| Permission rule | subject, resource, scope, lifetime, granted, silent allowed |
| Snapshot delta | snapshot id, timestamp, parameter, before value, after value, preserves user files |
| Archive metadata | record id, edition, release timestamp, studio, lead producer, mix engineer, distributor, track count, duration seconds, visual reference, offline verified, provenance state, evidence reference |
| Timeline segment | segment id, title, start second, end second, workspace, color token, notes |
| Track marker | track index, position second, code name, category, theme tag, verified, evidence reference |
| Diagnostic | component, passed, error code, message |

All row shape and field-type checks happen before later indexed fields are read. Unsigned 32-bit fields are checked for whole-number values and the inclusive `0..4294967295` range. Numeric performance values reject non-numbers, NaN and values outside their explicit bounds.

## Validation invariants

### Performance

- Targets must be finite, positive and bounded.
- Measurements must be finite, non-negative and no greater than their targets.
- RAM values must be whole-number u32 MiB values.
- CPU values must be percentages in the inclusive `0..100` range.

A passing budget means only that the supplied measurements are internally consistent. It does not prove that the values came from a benchmark or represent a real machine. The checked-in sample numbers are fixtures, not performance claims.

### Permissions

- Every rule has a unique subject/resource pair and explicit scope and lifetime.
- Silent grants are rejected, including on denied rules.
- A denied rule must use `scope = "none"` and `lifetime = "permanent_deny"`.
- A granted rule must use a supported finite lifetime.
- When local-only mode is enabled, a granted `network.outbound` capability is rejected.

The validator does not grant, revoke or persist a permission. It only checks the policy data passed by its caller.

### Snapshots

- Snapshot identifiers, timestamps and parameter names are required.
- A delta must actually change its value.
- The same parameter may appear only once per snapshot.
- Every delta must explicitly confirm that user files are preserved.

The contract verifies the declared preservation flag; it cannot prove the behavior of an external rollback implementation.

### Timeline and markers

- Timeline segments start at zero, are ordered, gap-free and non-overlapping.
- Empty, duplicate, out-of-range and duration-mismatched segments are rejected.
- Marker track indexes and positions are strictly increasing and remain within archive bounds.
- Partial marker sets are allowed. Missing track names or positions are never fabricated.
- A marker marked verified must carry an evidence reference.

### Archive provenance

The metadata validator distinguishes structural consistency from historical verification. `offline_verified` may be true only when the provenance state is `verified` and an evidence reference is supplied.

The fixture preserves the supplied archive description but sets provenance to `unverified`, because no evidence references were included with the source fragment. Its release, studio, credits, chart and other historical statements remain user-supplied assertions; passing the contract does not authenticate them.

## Public module API

- `diagnostic(component, passed, error_code, message)`
- `check_performance_budget(budget)`
- `check_permission_policy(rules, local_only)`
- `verify_snapshot_safety(deltas)`
- `check_archive_metadata(metadata)`
- `verify_segments(segments, total_duration)`
- `verify_track_markers(markers, total_tracks, total_duration)`
- `validate_archive(metadata, budget, acl_rules, snapshot_deltas, segments, markers, local_only)`

Each validator returns a four-field diagnostic list. `validate_archive` returns `[all_passed, diagnostics, supplied_marker_count, declared_track_count]`.

The module deliberately does not expose the original pseudo-`Shell` calls. A future Studio/DAK host adapter must be a separate capability boundary with explicit permission, snapshot and marker-registration contracts; this pure archive module must remain usable offline and without host privileges.
