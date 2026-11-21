# Four-project repository federation matrix

**Reference:** 2026-11-21  
**Scope:** Reaper × Pytyliki × OPlague × VentuSample. This is an evidence-based capability map, not a proposal to merge four independent products into one runtime.

## Product boundaries

| Project | Owns | Current implemented surface |
|---|---|---|
| [Reaper](https://github.com/Ivan-VHS/Reaper) | Programming language and execution/orchestration | Python reference interpreter, selectable Canonical IR VM, developing native C17 frontend, МОСТ alias surface, bounded resources, embedded reference workbench and opt-in FFI |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | Portable processor and numerical systems core | C11 processor discovery, bounded benchmarks, memory kernel, DSP, metric engine, TRACE provenance and C ABI v1 |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | Windows device and driver-package evidence | Read-only PnP inventory, bounded INF/ZIP/UDRV inspection, exact-ID candidate graph, DRIVE-LENS evidence, reports and snapshots |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | Hip-hop sample-pack generation | C++20 DSP renderer, 13 procedural styles, five output targets, PCM16 WAV chop import/export and deterministic manifests |

## Four-by-four product map

| From / To | Reaper | Pytyliki | OPlague | VentuSample |
|---|---|---|---|---|
| **Reaper** | Language/runtime/VM self-loop | **Implemented:** explicit Pytyliki ABI v1 calls | **Implemented:** exports comparison reports; consumes bounded OPlague snapshots | **Planned:** render-request adapter; pack consumer not yet implemented |
| **Pytyliki** | **Implemented:** ABI v1 provider side for synchronous calls | C11 processor/DSP/memory/metric self-loop | **Implemented:** ABI v1 provider for OPlague cross-checks | **Planned:** no VentuSample native adapter is shipped |
| **OPlague** | **Implemented:** versioned device snapshot provider and Reaper report validator | **Implemented:** optional native metric call through explicitly selected ABI v1 | Read-only PnP/INF/ZIP/UDRV inspection and evidence self-loop | **Not applicable:** no direct shared domain operation |
| **VentuSample** | **Partial:** exports `ventusample.pack.v1` JSON + WAV artifacts; Reaper consumer is not implemented | **Planned:** possible explicit ABI v1 use after differential tests | **Not applicable:** no direct shared domain operation | Offline seeded sample generation, sample slicing and WAV/manifest export self-loop |

The OCTA-8 topology contains **12 directed links** (four projects × three other projects) and **four independent self-loops**. See [the validated topology contract](OCTA_PYRAMID_FEDERATION.md).

## Shared engineering doctrine

- **Human-first governance:** operator intent, explicit consent, visible consequences and no silent privileged changes.
- **Hydrodynamic clarity:** calm white/blue/red semantic surfaces, accessible focus, readable errors and purposeful reduced motion.
- **Bounded execution:** size, range, frame, resource and time limits at data boundaries.
- **Provenance:** input identity, source digests, versioned contracts, deterministic manifests and audit trails.
- **Independent product ownership:** no hidden runtime gateway; each repository retains its own build, release and test lifecycle.
- **Honest implementation states:** design registries and roadmap proposals are not callable APIs; producer-side file export is not a consumer-side integration.

## Links

[Reaper](https://github.com/Ivan-VHS/Reaper) · [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) · [OPlague](https://github.com/Ivan-VHS/OPlague) · [VentuSample](https://github.com/Ivan-VHS/VentuSample)
