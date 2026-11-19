# Concatenation and composition architecture

## Design rule

Reaper is flow-first: data and transformations are combined explicitly, in a declared order, under resource limits. The supplied 666-term vocabulary is used as a six-domain design crosswalk; it is not a claim that every listed database, network, UI, multimedia or distributed-system mechanism exists in the language runtime.

## Implemented public Python API

`reaper.composition` adds five pure operations:

- `concat(*parts, max_items=...)` — eager, ordered concatenation of iterables into an immutable tuple.
- `concat_text(*parts, separator=..., max_length=...)` — validates types and total output length before joining text.
- `merge_mappings(*mappings, on_conflict=..., max_keys=...)` — combines mappings with explicit `error`, `first` or `last` conflict semantics.
- `compose(f, g)(x)` — conventional right-to-left composition, equivalent to `f(g(x))`.
- `pipe(value, f, g)` — left-to-right data flow, matching Reaper's `|>` direction.

All operations are opt-in Python library functions exported from `reaper`; they do not silently add language syntax or host effects.

## Example

```python
from reaper import concat, concat_text, compose, merge_mappings, pipe

items = concat([1, 2], (3, 4))
label = concat_text("Harlem", "Metal", separator=" ")
settings = merge_mappings({"mode": "safe"}, {"theme": "dark"})
transform = compose(lambda n: n * 2, lambda n: n + 3)
flow_result = pipe(4, lambda n: n + 3, lambda n: n * 2)
```

## Six-domain crosswalk

| Domain | Reaper mapping | Status |
|---|---|---|
| 1. Strings, parsing, serialization | `concat_text` supplies bounded text joining; the parser's existing text quota remains authoritative at runtime | Implemented |
| 2. Streams and functional pipelines | `concat`, `compose` and `pipe` preserve part/function order | Implemented |
| 3. Relational and structured data | `merge_mappings` provides explicit duplicate-key policy; no SQL/database engine is claimed | Partial |
| 4. Modules, build and integration | Python package exports and unit tests integrate the API; native-backend parity is not claimed | Implemented |
| 5. UI and multimedia composition | Reaper is a language workbench, not an audio/video compositor | Not applicable |
| 6. Algebra and semantics | Identity behavior, ordered composition and explicit conflict handling are tested | Implemented |

## Resource and determinism contract

Defaults cap collection concatenation and mapping merges at 100,000 elements/keys and text at 1,000,000 characters. Callers may choose smaller positive limits. Boolean values are rejected where integer limits are expected. Input sequences and mappings are not mutated. Mapping insertion order follows first appearance; conflict replacement changes a value, not its original position.

Composition executes in a stable declared order and propagates exceptions from the supplied functions. The helpers do not catch arbitrary application errors, perform I/O, invoke subprocesses, access networks or alter interpreter permissions. They are bounded convenience primitives, not a sandbox.
