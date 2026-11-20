# Three-project federation matrix

**Reference snapshot:** 2026-11-20  
**Scope:** Reaper × OPlague × Pytyliki. This is an evidence-based integration map, not a proposal to merge three independent products into one runtime.

## Product boundaries

| Project | Owns | Main implemented surface |
|---|---|---|
| [Reaper](https://github.com/Ivan-VHS/Reaper) | Programming language, execution and workflow orchestration | Python reference runtime, Canonical IR VM, module graph, bounded resources, opt-in native FFI and MOST language track |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | Windows device inventory and driver-package inspection | Read-only PnP snapshots, INF/ZIP/UDRV inspection, deterministic report composition and hardware-profile analysis |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | Portable processor, memory and numerical systems core | C11 processor inventory, bounded workloads, memory kernel, metric engine, DSP and public C ABI v1 |

## The 3 × 3 cross-product

Each cell describes the real interaction between a project and itself or one of its peers. **Implemented** means code and/or a versioned contract exists; **optional** means the caller must explicitly enable or select it; **not connected** means no such runtime integration is claimed.

| Project × project | Reaper | OPlague | Pytyliki |
|---|---|---|---|
| **Reaper** | **Reaper × Reaper — implemented.** Language frontend, Python reference runtime, selectable Canonical IR VM, `.rpr` module graph, diagnostics and resource limits compose internally. | **Reaper × OPlague — implemented.** Reaper validates the full `oplage.device-snapshot.v1` envelope, derived counters and canonical SHA-256 fingerprint before extracting metrics and creating a `reaper.oplage-comparison.v1` report. It does not mutate devices or drivers. | **Reaper × Pytyliki — optional, implemented.** Reaper validates ABI v1 and calls the current `pytyliki_v1_*` numerical functions through an explicit trusted native-library path, both directly and through a typed handle. |
| **OPlague** | **OPlague × Reaper — implemented producer side.** OPlague exports bounded, versioned device snapshots for Reaper. OPlague does not embed or execute the Reaper runtime; orchestration remains on the Reaper side. | **OPlague × OPlague — implemented.** Read-only PnP inventory, INF/ZIP/UDRV inspection, exact-ID candidate graph, metric analysis and ordered `oplage.inspection-bundle.v1` report composition. | **OPlague × Pytyliki — optional, implemented.** OPlague can compare its Python metric result with Pytyliki's native Euclidean-distance implementation via ABI v1. A caller-supplied absolute path to a trusted library is required. |
| **Pytyliki** | **Pytyliki × Reaper — implemented provider side.** Pytyliki supplies a narrow C ABI v1 for bounded float64 metric operations. Pytyliki does not depend on Reaper or call its runtime. | **Pytyliki × OPlague — implemented provider side.** The same ABI v1 supplies an optional numerical cross-check. It does not inspect driver packages or perform device operations. | **Pytyliki × Pytyliki — implemented.** Portable C11 processor, memory, metric, embedded-reference and DSP modules are independently built and verified. |

## Actual data and call paths

```text
OPlague
  └─ oplage.device-snapshot.v1 (bounded JSON file)
       └─> Reaper
             └─ reaper.oplage-comparison.v1 (JSON audit report)

Pytyliki
  └─ pytyliki.c-abi.v1 (explicit trusted shared-library path)
       ├─> Reaper (opt-in metric calls)
       └─> OPlague (opt-in metric cross-check)
```

| Interface | Provider | Consumer | Transport and constraint |
|---|---|---|---|
| `oplage.device-snapshot.v1` | OPlague | Reaper | UTF-8 JSON; full v1 envelope and derived-counter validation; canonical SHA-256 verification; bounded finite metrics |
| `reaper.oplage-comparison.v1` | Reaper | User / downstream tooling | JSON comparison report; dimension mismatches are errors, not silently filled |
| `oplage.inspection-bundle.v1` | OPlague | User / downstream tooling | Canonical ordered JSON summary with a deterministic SHA-256 fingerprint |
| `pytyliki.c-abi.v1` | Pytyliki | Reaper, OPlague | Synchronous C ABI; explicit absolute path to a trusted shared library; caller-owned contiguous buffers |

## Integration boundaries

- **No monolithic merge:** the projects keep their own source trees, build systems, release cycles and domain ownership.
- **Read-only device boundary:** the OPlague-to-Reaper flow transports evidence and reports only. Reaper's federation built-ins do not install, remove, enable, disable or roll back drivers.
- **No implicit native loading:** Reaper and OPlague load Pytyliki only when a caller explicitly supplies a trusted library path. Loading a shared library executes native code with the caller's permissions.
- **Stable ABI:** Pytyliki ABI v1 uses fixed-width counts, contiguous float64 vectors, synchronous calls and caller-owned buffers. Consumers verify the ABI version and reject invalid dimensions or non-finite values.
- **Bounded interchange:** JSON consumers reject oversized, malformed or non-finite input. OPlague's PnP snapshot omits raw PnP instance IDs and uses HMAC-SHA-256 pseudonyms; ephemeral keys prevent correlation by default, while caller-managed keys enable deliberate linkability. Pseudonyms are not anonymization.
- **No reverse integrations claimed:** Pytyliki does not itself consume OPlague snapshots; OPlague does not execute Reaper programs; the projects do not exchange private in-memory structures.

## Useful cross-references

| Project | Integration contract | Project contract | Implementation evidence |
|---|---|---|---|
| Reaper | [Federated integration](https://github.com/Ivan-VHS/Reaper/blob/main/docs/FEDERATED_INTEGRATION.md) | [project-contract.json](https://github.com/Ivan-VHS/Reaper/blob/main/project-contract.json) | [federation.py](https://github.com/Ivan-VHS/Reaper/blob/main/reaper/federation.py) · [ffi.py](https://github.com/Ivan-VHS/Reaper/blob/main/reaper/ffi.py) |
| OPlague | [Federated integration](https://github.com/Ivan-VHS/OPlague/blob/main/docs/FEDERATED_INTEGRATION.md) | [project-contract.json](https://github.com/Ivan-VHS/OPlague/blob/main/project-contract.json) | [federation.py](https://github.com/Ivan-VHS/OPlague/blob/main/tools/federation.py) · [pytyliki_ffi.py](https://github.com/Ivan-VHS/OPlague/blob/main/tools/pytyliki_ffi.py) · [report_composer.py](https://github.com/Ivan-VHS/OPlague/blob/main/tools/report_composer.py) |
| Pytyliki | [Federated integration](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/FEDERATED_INTEGRATION.md) | [project-contract.json](https://github.com/Ivan-VHS/Pytyliki/blob/main/project-contract.json) | [interop.h](https://github.com/Ivan-VHS/Pytyliki/blob/main/src/interop.h) · [interop.c](https://github.com/Ivan-VHS/Pytyliki/blob/main/src/interop.c) |

## Change rule

When an interface changes, update its provider contract, every affected consumer contract, the relevant tests and all three `docs/FEDERATED_INTEGRATION.md` files in the same change. Preserve existing interface versions for compatible extensions; introduce a new versioned identifier for breaking changes. Keep this matrix synchronized with the three `project-contract.json` manifests.

This matrix is an inventory of current repository evidence. A roadmap item, language/toolchain catalogue entry or architecture idea must not be presented as an implemented cross-project feature until code, tests and contract evidence exist.
