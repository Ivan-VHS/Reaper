# Reaper framework portfolio

This folder is the fast entry point for the Reaper-native framework collection.
The canonical, machine-readable inventory is
[portfolio.v1.json](portfolio.v1.json); its schema is
[framework-portfolio.v1.schema.json](../schemas/framework-portfolio.v1.schema.json).
The portfolio is deliberately broader than this folder: it also indexes ДОМ,
the Framework Federation contracts, the 14 language/runtime subsystems and
adjacent Reaper integration surfaces.

## Standalone Reaper modules

All eighteen modules below are ordinary .rpr source modules using Reaper's
existing parser, module loader and reference runtime. They do not create a
second language or silently acquire host permissions.

| Framework | Main responsibility | Public API examples |
|---|---|---|
| GalHero | deterministic dependency planning | validate, topological_order, transitive_dependencies |
| Call-and-Back | synchronous callback/event dispatch | subscribe, dispatch, call_chain |
| Stacked Options | layered configuration | put, merge, resolve, validate |
| PerenosiMOST | exact Russian MOST alias mapping | canonical, support, normalize_words |
| MOST | facade over the existing alias profile | classify, runtime_aliases, reserved_aliases |
| Blau | immutable versioned snapshots | empty, read, write, compare_and_set, diff |
| Shashio | finite-state transitions and atomic event batches | validate, transition, run, apply_atomic |
| Showel Fleppery CODE | validated in-memory source transforms | add_step, render, run |
| Vorke | application manifests and declarative launch phases | validate_manifest, phase_plan, shutdown_plan |
| Jellymeat | schema-first record validation and projection | validate_schema, validate_record, project |
| LejjyFish | bounded ordered streams and backpressure | stream_valid, append, take_batch, fanout |
| Lejjy | explicit service bindings and lifetime scopes | bind, resolve, resolve_many, validate_dependencies |
| Oplos | transport-neutral routes and message envelopes | validate_routes, resolve_route, validate_envelope_pair |
| Holmosaptimu | local metric contracts and summaries | validate_samples, summarize, health_grade |
| Sentan | deny-by-default policy evaluation | validate_rules, evaluate, explain, least_privilege |
| Cellene | component manifests and ABI compatibility | validate_manifests, host_compatible, validate_composition |
| Kolir | declarative UI-tree and accessibility structure | validate_tree, focus_order, viewport_admit |
| SOMO | deterministic scenarios and replay comparisons | validate_scenario, evaluate, replay_equal, release_gate |

## Run the smoke programs

From the repository root, browse the unified catalogue without opening source files:

    python -m reaper --frameworks
    python -m reaper --framework-info Vorke
    python -m reaper --framework-search federation

Run the source-level smoke programs:

    python -m reaper examples/frameworks_smoke.rpr
    python -m reaper examples/frameworks_portfolio_smoke.rpr
    python -m unittest tests.test_frameworks -v
    python -m unittest tests.test_frameworks_portfolio -v

The smoke programs execute Reaper source through the current reference runtime.
The tests do not assert native C17 or native AOT parity.

## Other framework collections and integration surfaces

The machine-readable portfolio also indexes:
- ДОМ's canonical runtime foundation and its eight initial subsystem slices;
- twenty Framework Federation namespaces, with registry contracts and a
  separate stacked Reaper-handler proposal;
- fourteen language/compiler/runtime subsystems;
- Native Framework Core, RForge, Rivet, PLAGUE and Aesthetica;
- Kora, the eighteen internal products, the Native Capability Suite, System
  Runtime ABI, DABI64, Jora, self-hosting, MOST/QCS and NEXUS/OCTA.

Each entry records its source path or PR/branch and current maturity. Open or
draft PRs are not presented as merged features.

## Runtime and safety boundaries

- Framework calls operate on explicit caller-owned values unless an explicit
  adapter is supplied.
- No module in this collection grants filesystem, process, network, FFI,
  hardware or kernel authority.
- Vorke creates a plan; Establish and JLOM remain ДОМ lifecycle authorities.
- Jellymeat validates records; durable storage and transactions remain explicit
  adapters.
- LejjyFish models bounded stream state; it is not a live message bus.
- Lejjy resolves declared providers; it does not construct or execute them.
- Oplos validates transport contracts; it does not open sockets or send requests.
- Holmosaptimu summarizes supplied values; it does not collect or export telemetry.
- Sentan returns policy decisions; the trusted host performs enforcement.
- Cellene validates metadata; Native Framework Core owns trusted native
  registration and activation.
- Kolir validates declarative UI structure; Studio and platform hosts render it.
- SOMO evaluates supplied results; it does not launch subprocesses or devices.

Every module is an initial reference-runtime implementation slice. Native
bindings, persistent services, concurrency, platform integration and the
50,000-qualified-LOC goals are separate evidence gates.
