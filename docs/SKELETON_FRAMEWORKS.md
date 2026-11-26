# Reaper Skeleton Frameworks — batch 01

**Domain:** Каркас (system-programming project and component skeletons)  
**Contract version:** `reaper.skeleton-frameworks/v1`  
**Implementation language:** Reaper (`.rpr`)  
**Execution model:** pure, deterministic validation functions; no ambient host effects.

This batch implements five separate frameworks. Each module has its own exported API and can be imported without importing the other four modules.

| Framework | Module | Contract | Main checks |
|---|---|---|---|
| FrameManifest | `manifest.rpr` | required component inventory | missing entries, duplicate names, empty or non-text names |
| FrameLayers | `layers.rpr` | ordered layer dependency graph | valid endpoints, forward-only dependencies, duplicate edges |
| FrameLifecycle | `lifecycle.rpr` | explicit component state transitions | transition record shape, duplicate transitions, undeclared steps |
| FrameCapabilities | `capabilities.rpr` | least-privilege component boundary | required grants, policy allowlist, duplicate and malformed capability names |
| FrameExtensions | `extensions.rpr` | extension identity and API compatibility | record shape, unique IDs, valid version interval, inclusive host compatibility |

## Common rules

- Every API is a pure Reaper function: it does not read files, access the network, start processes, load native libraries or touch hardware.
- Inputs are explicit lists and scalar values. Invalid shapes are rejected by a boolean result or an empty compatibility list, not by silently widening permissions.
- There is no shared mutable registry or implicit dependency between modules.
- Layer edges are ordered pairs `[source, target]`; only edges from a lower index to a higher index are accepted. This makes the declared layer relation acyclic by construction.
- Lifecycle transitions are explicit pairs `[from, to]`; a requested lifecycle must follow every declared transition in sequence.
- Extension records are `[id, minimum_api_level, maximum_api_level]`; compatibility bounds are inclusive.

## API

### FrameManifest

- `missing_components(required, present) -> list[text]`
- `valid_manifest(required, present) -> boolean`

### FrameLayers

- `valid_layer_graph(layer_count, edges) -> boolean`

### FrameLifecycle

- `valid_lifecycle(initial_state, steps, transitions) -> boolean`

### FrameCapabilities

- `missing_capabilities(required, granted) -> list[text]`
- `unexpected_capabilities(granted, policy) -> list[text]`
- `valid_capability_boundary(required, granted, policy) -> boolean`

### FrameExtensions

- `valid_extension_record(record) -> boolean`
- `compatible_extension(record, host_api_level) -> boolean`
- `valid_extension_registry(records) -> boolean`
- `compatible_extensions(records, host_api_level) -> list[record]`

## Verification

The repository regression suite exercises these modules through the Reaper interpreter, not through parallel Python implementations:

```sh
python -m unittest tests.test_skeleton_frameworks -v
```

The Python code in the test file is only the existing host-side test harness. Framework behavior remains implemented in Reaper source files.

## Maturity boundary

This batch implements five validation frameworks. It does not claim that the language has a general dependency scheduler, a process supervisor, a privilege broker, a plugin loader or a hardware runtime. Those require separate designs and executable evidence.
