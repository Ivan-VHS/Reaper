# OCTA-8 — four-project peer federation

**Status:** shared, validated topology for Reaper, Pytyliki, OPlague and VentuSample. The apex is protocol metadata only; it is not a central runtime bus.

## Geometry and multiplication

The topology has an octagonal base, eight triangular facets and a non-executable coordination apex. The four independent products form a complete directed peer mesh:

`n × (n − 1) = 4 × 3 = 12`

That means **12 directed links and four independent self-loops**. It does not mean every pair has a runtime adapter. Each link records its transport, interface, direction and honest implementation status.

## Verified peer links

| Direction | Transport | Contract | Status | Meaning |
|---|---|---|---|---|
| OPlague → Reaper | Bounded JSON | `oplage.device-snapshot.v1` | Implemented | Reaper validates and compares read-only device snapshots |
| Reaper → OPlague | Bounded JSON | `reaper.oplage-comparison.v1` | Implemented | OPlague validates the generated report |
| Reaper → Pytyliki | Explicit native FFI | `pytyliki.c-abi.v1` | Implemented | Caller-requested synchronous metric call |
| Pytyliki → Reaper | Synchronous ABI response | `pytyliki.c-abi.v1` | Implemented | Result returned inside caller's invocation |
| OPlague → Pytyliki | Explicit native FFI | `pytyliki.c-abi.v1` | Implemented | Optional native metric cross-check |
| Pytyliki → OPlague | Synchronous ABI response | `pytyliki.c-abi.v1` | Implemented | Result returned inside caller's invocation |
| VentuSample → Reaper | JSON artifact | `ventusample.pack.v1` | Partial | WAV + manifest export exists; Reaper consumer is not implemented |
| Reaper → VentuSample | JSON artifact | `ventusample.render-request.v1` | Planned | Future validated render-request adapter |
| VentuSample → Pytyliki | Explicit native FFI | `pytyliki.c-abi.v1` | Planned | VentuSample does not load the Pytyliki library yet |
| Pytyliki → VentuSample | Synchronous ABI response | `pytyliki.c-abi.v1` | Planned | Future result path after explicit ABI adoption |
| VentuSample → OPlague | None | `not-applicable.v1` | Not applicable | No shared domain operation |
| OPlague → VentuSample | None | `not-applicable.v1` | Not applicable | No shared domain operation |

An exported file is not evidence that the receiving application consumes it. Planned interfaces are not implemented features.

## Eight facets

1. **Identity and namespaces** — stable project/interface IDs; no personal or host identity required in interchange.
2. **Contracts and versioning** — versioned schemas and ABI contracts.
3. **Transport and bounded envelopes** — bounded JSON or explicit synchronous calls.
4. **Provenance and integrity** — byte digests and artifact lineage; hashes do not authenticate publishers.
5. **Validation and normalization** — explicit units, dimensions, ranges and finite-number checks.
6. **Privacy and consent** — explicit export/native-load operations and data minimization.
7. **Execution and safety** — read-only hardware work; offline audio processing; no privileged operations through the mesh.
8. **Audit and reproducibility** — deterministic outputs, inspectable manifests and discrepancy states.

## Independent self-loops

| Project | Internal contract | Owns |
|---|---|---|
| Reaper | `reaper.internal-runtime.v1` | Language frontend, reference runtime, VM, modules, resources and audit |
| Pytyliki | `pytyliki.internal-core.v1` | C11 processor systems, memory, DSP, metrics, TRACE and ABI |
| OPlague | `oplage.internal-workbench.v1` | Read-only PnP inventory, package inspection, evidence and reports |
| VentuSample | `ventusample.internal-audio.v1` | Hip-hop pattern engine, sampler DSP, WAV I/O and sample-pack generation |

## Validation

```bash
python tools/validate_octa_pyramid.py
python -m unittest tests.test_octa_pyramid -v
```

## Safety boundary

Native libraries are never loaded implicitly. Reaper and OPlague require an explicit trusted Pytyliki library path. OPlague remains read-only. VentuSample remains offline and does not control system audio. OCTA-8 is a versioned peer map, not a privileged executor or monolithic application.

## Repositories

[Reaper](https://github.com/Ivan-VHS/Reaper) · [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) · [OPlague](https://github.com/Ivan-VHS/OPlague) · [VentuSample](https://github.com/Ivan-VHS/VentuSample)
