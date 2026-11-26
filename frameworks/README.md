# Reaper Framework Family

Ten independent Reaper-source frameworks with one standard-library facade.

| Framework | Responsibility | Primary API |
|---|---|---|
| Lokaliza | Locale negotiation, plural rules, catalogs, fallback and message formatting | `locale.rpr` |
| Sealise | Project blueprints, public contracts, layering and migrations | `blueprint.rpr` |
| Blebby | Packages, semantic versions, constraints, lock snapshots and provenance | `package.rpr` |
| Centen | Resource ledgers, quotas, atomic reservation batches and lexical region models | `resource.rpr` |
| Kaso | Typed template contexts, escaping, conditionals and bounded rendering | `template.rpr` |
| Shinnn | Architecture graphs, deterministic topology, reachability and impact | `graph.rpr` |
| Porteo | Component lifecycle, readiness, launch plans, health and bounded restart policy | `lifecycle.rpr` |
| Portable Bortable | Target profiles, ABI compatibility and target matrices | `target.rpr` |
| SWO | Workflows, quality gates, retry schedules and release candidates | `pipeline.rpr` |
| ScoHOPE | Application profiles, typed configuration and service readiness | `application.rpr` |

## Reaper entry points

- `frameworks/family.rpr`: direct family import surface.
- `stdlib/frameworks.rpr`: standard-library facade for applications.
- `frameworks/smoke.rpr`: executable positive/negative integration coverage.
- `language/framework-adoption.v1.json`: traceability for all 666 catalogued API contracts and current feature records.

## Source budget

Each framework targets exactly **666,666 Unicode code points** of implementation source. Only tracked `.rpr` files under that framework's `src/` directory count. Whitespace and comments count; docs, tests, manifests and generated files do not. The manifest stores actual counts and remaining balances.

## Capability boundaries

These are executable Reaper-source libraries on the current reference runtime. The current native AOT backend does not yet support every list, module and dynamic-call construct used here. The source library therefore does not claim native-AOT parity.

Pure transformations do not grant filesystem, process, network, clock, device or privileged access. Any such capability must be explicitly supplied by a host adapter. Package provenance metadata is not signature verification; target compatibility checks are not cross-compilation; resource ledgers are not a process memory allocator.

ДОМ remains the shared runtime owner. The frameworks do not implement a competing scheduler, resource manager or application lifecycle.
