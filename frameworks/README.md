# Reaper framework modules

These modules are written in Reaper source files (.rpr) and use the existing
reference runtime, module loader, callback model and collection built-ins. They
do not introduce a second parser or a parallel runtime.

| Module | Responsibility | Main operations |
|---|---|---|
| GalHero | deterministic dependency planning | validate, topological_order, transitive_dependencies |
| Call-and-Back | synchronous callback/event dispatch | subscribe, dispatch, call_chain |
| Stacked Options | layered option resolution and validation | put, merge, resolve, validate |
| PerenosiMOST | exact alias migration to canonical Reaper names | canonical, support, normalize_words |
| MOST | stable facade over the existing МОСТ profile | classify, runtime_aliases, reserved_aliases |
| Blau | immutable versioned local state snapshots | empty, read, write, compare_and_set, diff |
| Shashio | finite-state transitions and atomic event batches | validate, transition, run, apply_atomic |
| Showel Fleppery CODE | deterministic in-memory code transformation | add_step, render, run |

## Execute the integration example

From the repository root:

    python -m reaper examples/frameworks_smoke.rpr

The example exercises all eight modules and uses Reaper assertions. It is a
reference-runtime integration example, not a claim of native C17 parity.

## Contracts

- Inputs are explicit values; no module silently reads or writes files.
- No framework grants filesystem, process, network, FFI or hardware authority.
- Callback execution is synchronous and follows stable registration/priority order.
- GalHero rejects unknown dependencies and cycles rather than guessing.
- Stacked Options uses right-most-wins precedence: defaults, profile, workspace,
  then request.
- PerenosiMOST performs exact spelling lookup only. It does not stem, guess
  inflections, translate identifiers or rewrite source text.
- MOST remains an alias profile over the single Reaper grammar and runtime.
- Blau returns new snapshots; a version conflict never overwrites newer state.
- Shashio applies event batches atomically from the caller's point of view.
- Showel Fleppery CODE transforms source text in memory and rolls back the
  reported result when a stage validator rejects the output.

These APIs are a first executable slice. They do not imply asynchronous
execution, parallel scheduling, durable storage, a complete code generator,
or native compiler conformance.
