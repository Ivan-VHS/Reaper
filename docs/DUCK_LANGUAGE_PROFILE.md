# Duck language profile

**Status:** implemented in the Python reference runtime; native C17 parity is not claimed.

The Duck profile turns the useful engineering ideas behind duck typing and the Duck Inspector metaphor into small, bounded language operations. It is a standard-library/runtime profile, not a second grammar and not a claim that Reaper already has user-defined traits, generics or arbitrary method dispatch.

## Design contract

1. **Behavior over labels, within a defined boundary.** A Reaper map can satisfy a structural data contract when it contains the required field names. The current profile does not inspect arbitrary host-language objects or invoke unknown methods.
2. **Inspect shape, not secrets.** Inspection returns the value kind, supported capability names, size and (for string-keyed maps) field names. It never returns field values.
3. **Probe before requiring.** A canary-style probe returns a deterministic report without stopping the program. A strict requirement fails with a runtime diagnostic.
4. **Normalize without clobbering.** Adaptation copies a map and fills only absent fields from defaults. Caller-provided values always win; the source maps are not mutated.
5. **Keep the core dry.** These helpers are deterministic and have no file, network, clock, FFI or device effects. They do not grant host capabilities.
6. **Stay afloat under load.** Maps, field lists, collections, text, execution steps, heap use and open resources remain subject to the interpreter's configured limits.
7. **Prefer useful signals.** Inspection, probes and runtime statistics return data; they do not print, log or schedule background work.

## Language built-ins

| Built-in | Contract | Result |
|---|---|---|
| `duck_capabilities(value)` | Lists the known capabilities of the value's Reaper kind | `List[Text]` |
| `duck_supports(value, capability)` | Tests one capability name | `Bool` |
| `duck_has(map, field)` | Checks key presence, including a key whose value is `nothing` | `Bool` |
| `duck_inspect(value)` | Returns safe shape metadata, never payload values | `Map` |
| `duck_probe(value, fields)` | Non-throwing structural preflight for a map | `Map` |
| `duck_require(map, fields)` | Enforces required keys and returns the original map | same type as input |
| `duck_adapt(map, defaults)` | Returns a shallow copy with missing defaults added | `Map` |
| `runtime_stats()` | Returns current execution and open-resource counters | `Map` |

`fields` in `duck_probe` and `duck_require` may be one text key or a list of text keys. Duplicate names are checked once, in first-seen order. Map field names must be text when using `duck_adapt`.

### Capability vocabulary

| Value kind | Capabilities |
|---|---|
| `text` | `indexable`, `iterable`, `sized`, `text` |
| `list` / `range` | `indexable`, `iterable`, `sized` |
| `map` | `indexable`, `iterable`, `keyed`, `sized`, `structural` |
| `craft` | `callable` |
| `number` | `numeric` |
| `boolean` | `boolean` |
| `resource` | `resource` |
| `nothing` | `empty` |

The list is intentionally finite and versioned with the runtime implementation. An unknown capability returns `false`; it is not inferred from a spelling or host object attribute.

## Example

```reaper
make resources := resource_stats()
make preflight := duck_probe(resources, ["open_files", "limit"])

when preflight["ok"] {
    emit "resource contract: ready"
} otherwise {
    emit "resource contract: incomplete"
}

make checked := resources :: duck_require(["open_files", "limit"])
make report := duck_adapt(checked, heap_stats())

emit duck_inspect(report)
emit duck_supports(report, "keyed")
emit duck_has(report, "open_files")
emit duck_capabilities(range(0, 3))
emit runtime_stats()
```

Run it with:

```sh
python -m reaper --check examples/duck_profile.rpr
python -m reaper examples/duck_profile.rpr
python -m unittest tests.test_duck_profile -v
```

## How the 66 inspiration points map to code

| Source ideas | Reaper implementation |
|---|---|
| 1–14 · protection, stable center and efficient movement | bounded runtime, explicit effects, safe inspection, no implicit host access |
| 15–28 · feeding, grouping, adaptation and migration | expression pipelines, bounded collection helpers, structural probes and defaults |
| 29–38 · signals, silence and recognition | source-aware diagnostics, audit facilities, `runtime_stats()`, quiet result-returning probes |
| 39–50 · rubber-duck debugging and readable identity | `duck_inspect()`, deterministic reports, existing formatter, CLI, LSP and debugger |
| 51–66 · inspector, structural contracts, canaries and resilience | `duck_has`, `duck_supports`, `duck_require`, `duck_probe`, `duck_adapt`, resource quotas and runtime telemetry |

The biological details and toy symbolism are design metaphors, not literal runtime features. The language does not emulate animal physiology, play audio signals, or run a background observer.

## Boundaries and acceptance

- The current structural contract applies to Reaper maps. User-defined `trait`/interface declarations, method-based dynamic dispatch, generic constraints and cross-module structural inference remain outside this implementation.
- `duck_adapt` is a shallow map copy. It does not recursively merge nested values, coerce types or discard unknown fields.
- `duck_inspect` reports shape only and does not reveal map values or arbitrary Python attributes.
- `duck_probe` is a synchronous check, not a live monitor, scheduler or hardware canary.
- The new runtime built-ins are tested through both tree-walk and VM execution. Python remains the compatibility reference; the experimental C17 compiler does not claim parity for these operations.

Implementation evidence: `reaper/duck.py`, `reaper/runtime.py`, `reaper/typecheck.py` and `tests/test_duck_profile.py`.
