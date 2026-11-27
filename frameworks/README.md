# Reaper Framework Family

Ten independent Reaper-source frameworks with a single family entry point and an application-facing standard-library facade.

| Framework | Responsibility | Main capabilities |
|---|---|---|
| Lokaliza | Locale and language infrastructure | Locale negotiation, plural rules, catalog coverage/validation, regional fallback, message formatting and terminology |
| Sealise | Project blueprints and contracts | Project profiles, public contract compatibility, layering, migration planning and baseline validation |
| Blebby | Package and library infrastructure | Semantic versions, dependency closure, version selection, lock snapshots/diffs and provenance metadata |
| Centen | Fundamental resource primitives | Bounded ledgers, quotas, staged multi-resource transactions, usage policies and lexical regions |
| Kaso | Template and construction engine | Typed contexts, nested lookup, safe interpolation, conditionals, schema checks and bounded rendering |
| Shinnn | Architecture and structural graphs | DAG validation, dependency-first ordering, reachability, graph metrics, component boundaries and impact analysis |
| Porteo | Component integration and orchestration | Lifecycle transitions, dependency readiness, health reports, capability checks, event journals and restart policies |
| Portable Bortable | Target and ABI portability | Target profiles, ABI validation, capability matrices and memory-region layout validation |
| SWO | Engineering and release tooling | Workflow validation, quality gates, retry schedules, evidence tracking, waivers and release manifests |
| ScoHOPE | Application foundation | App profiles, typed configuration scopes, environment compatibility, service readiness and extension contracts |

## Reaper entry points

- `frameworks/family.rpr`: exports all ten framework namespaces.
- `stdlib/frameworks.rpr`: Reaper-source facade for applications that want to discover and import a framework by name.
- `frameworks/smoke.rpr`: positive and negative source-level integration checks; CI invokes it with the current reference runtime.
- `language/framework-adoption.v1.json`: traceability for all 666 API contracts in the existing registry and the current 22 language feature records.

## Source budget

Each framework has a target of exactly **666,666 Unicode code points** of implementation source. Current measured counts in this branch total **101,528 characters** across the ten `src/` directories. The exact count and remaining balance for each framework are recorded in `frameworks/manifest.json`.

Only tracked `.rpr` files under each framework's `src/` directory count toward the target. Whitespace and comments count; docs, tests, manifests and generated files do not.

## Compatibility and safety

These modules are Reaper source programs that use the existing language surface and reference runtime. The current native AOT compiler still lacks complete support for list-heavy module programs; native-AOT parity is not claimed.

The 666-entry function registry is a catalogue of contracts, not a claim that every entry is implemented. The adoption map records the intended Reaper layer for each contract and preserves its current status. Compiler syntax, typed IR, ownership/effects, memory model, concurrency and native code generation require work in the language/compiler. Filesystem, process, network, clock, device and privileged operations require explicit host adapters and capabilities.

Package provenance metadata is not signature verification. Target/ABI validation does not perform cross-compilation. Resource ledgers are policy models, not a physical memory allocator. These boundaries remain explicit.

ДОМ remains the shared runtime owner. The framework family does not introduce a competing scheduler, resource manager or application lifecycle runtime.
