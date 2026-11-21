# OCTA-8 — Four-Project Horizontal Peer Product

**Status:** shared four-project topology with twelve directed peer links, four independent self-loops and eight octagonal-pyramid facets.

## Geometry and mesh

The base is a complete directed mesh of four independent products:

- Reaper — language and orchestration.
- Pytyliki — processor, memory, metric and DSP systems core.
- OPlague — read-only Windows device and driver-package diagnostics.
- VentuSample — offline procedural audio and sample-pack generation.

For n=4, the mesh contains n(n-1)=12 directed links. Each project retains its own local self-loop. The apex octa-hub carries protocol metadata only; it is non-executable, is not a runtime gateway and is not a single point of failure.

## Pairwise feature product

| Pair | Interface | State |
|---|---|---|
| Reaper ↔ OPlague | oplage.device-snapshot.v1, reaper.oplage-comparison.v1 | Implemented, bounded JSON, read-only |
| Reaper ↔ Pytyliki | pytyliki.c-abi.v1 | Optional explicit-path native metric calls |
| OPlague ↔ Pytyliki | pytyliki.c-abi.v1 | Optional explicit-path numerical cross-check |
| VentuSample → Reaper | ventusample.pack.v1 | Implemented pack-manifest audit and comparison |
| Reaper → VentuSample | ventusample.render-request.v1 | Planned |
| VentuSample ↔ Pytyliki | pytyliki.c-abi.v1 | Planned direct native adapter |
| VentuSample ↔ OPlague | not-applicable.v1 | Not applicable; no driver/audio coupling |

The Reaper pack consumer validates v1 metadata, derives 22 normalized descriptors, and produces a read-only comparison report. It does not inspect waveform data or alter generated files. Its default metric engine is Reaper Python; an explicit Pytyliki library path enables a native distance cross-check.

## Eight facets

1. **Identity:** stable project and interface identifiers.
2. **Contracts:** versioned schemas and compatibility rules.
3. **Transport:** bounded JSON artifacts and explicit synchronous native calls.
4. **Provenance:** source lineage and content fingerprints.
5. **Validation:** strict types, dimensions, units, value ranges and finite numbers.
6. **Privacy:** no unnecessary personal/device identity in sample-pack artifacts.
7. **Safety:** read-only hardware flow and explicit native-loading boundaries.
8. **Audit:** deterministic outputs, testable invariants and visible implementation status.

## Protocol rules

- No shared monolithic runtime and no central executable gateway.
- Native libraries are caller-selected by explicit trusted path; no implicit DLL/SO discovery.
- Device and driver evidence stays read-only across the mesh.
- Audio generation and sample asset storage remain owned by VentuSample.
- Manifest comparisons use declared settings and stored measurements, not waveform-level listening or quality judgments.
- Planned and not-applicable edges remain explicit and are never described as implemented.

## Validation

Each repository contains the same topology JSON/schema and a local validator:

~~~bash
python tools/validate_octa_pyramid.py
python -m unittest tests.test_octa_pyramid -v
~~~

The validator checks all twelve directed edges, unique facet identifiers, four self-loops, declared project membership and the non-executable apex. Project-specific contracts validate implementation evidence independently.

## Change policy

A shared topology change must update the topology, schema, validator, tests and each affected project contract together. Interface changes must also update producer/consumer documentation. New edges remain planned until working code and tests exist.
