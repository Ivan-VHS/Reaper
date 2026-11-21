# Four-project federation matrix

**Reference:** 21 November 2026  
**Topology:** OCTA-8 · four independent products · 12 directed peer links · four local self-loops

This matrix is an evidence-backed feature cross-product. It combines useful capabilities through explicit contracts; it does not merge four product runtimes or imply that planned links already execute.

## Product responsibilities

| Project | Owns | Reusable strength |
|---|---|---|
| [Reaper](https://github.com/Ivan-VHS/Reaper) | Programming language, automation and orchestration | Validated JSON workflows, comparison reports, modules, bounded execution and explicit native adapters |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | Portable processor, memory, metric and DSP systems core | C11 ABI v1 metrics, memory kernels, numerical comparison, PCM16 DSP and TRACE provenance |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | Windows hardware inventory and driver-package diagnostics | Read-only PnP snapshots, bounded INF/ZIP/UDRV inspection, exact-ID dry-run and evidence ledgers |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | Procedural hip-hop audio and sample-pack generation | Seeded C++20 rendering, PCM16 WAV assets, musical controls and ventusample.pack.v1 manifests |

## Six useful pairings

| Pair | Useful combination | Current state |
|---|---|---|
| Reaper × OPlague | Reaper consumes bounded device snapshots, computes read-only comparisons and emits reports; OPlague validates those reports | **Implemented** |
| Reaper × Pytyliki | Reaper routes selected float64 norm/dot/distance/orthogonality calculations through the explicitly selected Pytyliki C ABI v1 | **Optional, implemented** |
| OPlague × Pytyliki | OPlague cross-checks selected metric calculations against Pytyliki's native Euclidean-distance implementation | **Optional, implemented** |
| VentuSample × Reaper | VentuSample exports pack v1; Reaper validates manifests, produces 22 normalized descriptor/measurement metrics and compares two packs | **Implemented: VentuSample → Reaper** |
| VentuSample × Pytyliki | Future direct native metric/DSP adapter; current Reaper comparison can optionally use Pytyliki for the numerical distance stage | **Direct VentuSample ABI link planned** |
| VentuSample × OPlague | Driver inventory and package diagnostics have no useful role in offline sample-pack generation | **Not applicable by design** |

The Reaper-to-VentuSample render-request contract is recorded as planned. Reaper currently audits exported packs; it does not dispatch generation jobs into the VentuSample desktop application.

## Complete directed mesh

| Direction | Transport | Contract | State |
|---|---|---|---|
| OPlague → Reaper | Bounded JSON | oplage.device-snapshot.v1 | Implemented |
| Reaper → OPlague | Bounded JSON | reaper.oplage-comparison.v1 | Implemented |
| Reaper → Pytyliki | Explicit native FFI | pytyliki.c-abi.v1 | Implemented |
| Pytyliki → Reaper | Explicit native FFI | pytyliki.c-abi.v1 | Implemented |
| OPlague → Pytyliki | Explicit native FFI | pytyliki.c-abi.v1 | Implemented |
| Pytyliki → OPlague | Explicit native FFI | pytyliki.c-abi.v1 | Implemented |
| VentuSample → Reaper | JSON + local WAV assets | ventusample.pack.v1 | Implemented |
| Reaper → VentuSample | JSON artifact | ventusample.render-request.v1 | Planned |
| VentuSample → Pytyliki | Native FFI | pytyliki.c-abi.v1 | Planned |
| Pytyliki → VentuSample | Native FFI | pytyliki.c-abi.v1 | Planned |
| VentuSample → OPlague | None | not-applicable.v1 | Not applicable |
| OPlague → VentuSample | None | not-applicable.v1 | Not applicable |

For n=4, the directed peer product is n(n-1)=12 links. Four additional self-loops preserve each product's independent responsibility.

## Reaper's VentuSample pack audit

Reaper exposes two language built-ins:

- ventusample_metrics(pack) validates a complete ventusample.pack.v1 object and returns 22 finite, normalized descriptor/measurement values.
- ventusample_compare(reference, candidate[, library_path]) compares two validated manifests and writes a reaper.ventusample-comparison.v1 report with per-component deltas and a deterministic SHA-256 fingerprint.

The comparison uses musical settings and generator-supplied peak/RMS/crest metadata. It does **not** read WAV sample data, judge musical quality, rank styles or change packs. Supplying an explicit absolute Pytyliki library path opts into a native distance cross-check; otherwise Reaper's Python metric implementation is used.

Example: [examples/ventusample_pack_audit.rpr](https://github.com/Ivan-VHS/Reaper/blob/main/examples/ventusample_pack_audit.rpr). Contract: [docs/FEDERATED_INTEGRATION.md](https://github.com/Ivan-VHS/Reaper/blob/main/docs/FEDERATED_INTEGRATION.md).

## OCTA-8 protocol facets

All peer links share eight invariants: identity, contracts, transport, provenance, validation, privacy, safety and audit. The octa-hub apex is coordination metadata only; it is non-executable and is not a central runtime gateway.

## Safety and ownership

- Hardware discovery, device snapshots and package evidence remain read-only. No driver install/remove/enable/disable or firmware action is transported through the mesh.
- Native library loading is never implicit. A caller must provide an explicit trusted ABI-compatible library path; loading native code executes it with the caller's process permissions.
- JSON and audio assets are treated as untrusted input. Schemas, dimensions, paths, finite values and resource bounds are checked before use.
- A hash or content fingerprint identifies bytes; it does not prove publisher authenticity, source trust or audio quality.
- Planned and not-applicable edges remain visible but are not counted as implemented capabilities.

## Change rule

When changing a shared interface, update the provider and consumer contracts, the relevant tests, the topology/schema/validator and affected federation docs in the same PR. Keep the four project manifests truthful about implemented, partial, optional, planned and not_applicable states. A catalogue entry or topology edge is not implementation evidence by itself.


Publication and privacy requirements follow [Documentation Control](DOCUMENTATION_CONTROL.md).
