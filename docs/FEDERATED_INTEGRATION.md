# Federated integration: Reaper, OPlague, Pytyliki and VentuSample

Reaper owns language execution and orchestration. It consumes versioned JSON artifacts from OPlague and VentuSample, and can route selected numerical operations through Pytyliki's native C ABI v1. All product boundaries remain independent.

## OPlague device snapshot contract

- Producer: OPlague.
- Consumer: Reaper.
- Contract: oplage.device-snapshot.v1.
- Transport: caller-selected UTF-8 JSON file.
- Report: reaper.oplage-comparison.v1.

Reaper checks the full snapshot envelope, read-only source declaration, identity-protection metadata, device/package record shapes, derived counters, normalized finite metric dimensions and canonical SHA-256 fingerprint. Reference and candidate dimensions must match exactly. The fingerprint detects content drift; it does not authenticate a publisher.

JSON reads reject duplicate object keys, NaN/Infinity, symbolic-link inputs, non-UTF-8 data and files above 16 MiB. JSON writes reject non-finite/non-JSON values, enforce the same limit and atomically replace only the explicitly named output file.

## Pytyliki C ABI v1

Native numerical calls load only from a caller-supplied explicit absolute library path. Reaper verifies pytyliki_abi_version() == 1 and the exported pytyliki_v1_* metric functions. Float64 vectors are finite, bounded to 1..4096 items, contiguous and synchronously passed through caller-owned buffers.

Available operations include norm, dot product, Euclidean distance and orthogonality. The Python metric backend remains the default. Selecting a native library executes trusted native code with Reaper's process permissions; it is not a sandbox.

## VentuSample pack v1

- Producer: VentuSample.
- Consumer: Reaper.
- Contract: ventusample.pack.v1.
- Transport: JSON manifest plus WAV assets retained in the export folder.
- Comparison report: reaper.ventusample-comparison.v1.

The consumer schema is pinned at schemas/ventusample.pack.v1.schema.json. The validator enforces the exact v1 field set, supported style/target/key/scale/sampler/timbre values, BPM and DSP parameter ranges, Nyquist-safe filter bounds, expected output count, per-variation coverage, unique safe WAV filenames and finite peak/RMS/crest measurements.

Reaper provides these built-ins to .rpr programs:

| Built-in | Signature | Result |
|---|---|---|
| ventusample_metrics | ventusample_metrics(pack) | Validated map of 22 normalized musical, processing and audio-measurement descriptors |
| ventusample_compare | ventusample_compare(reference, candidate[, library_path]) | Read-only comparison report with per-field deltas, distance backend and deterministic report hash |

The report describes descriptor shift, not whether one pack sounds better. The numerical distance is computed by Reaper's Python metric engine by default. A third argument may select a trusted Pytyliki ABI v1 library by explicit absolute path for the distance calculation.

Only the manifest is read. Reaper does not open, rewrite, execute, copy or upload WAV assets; it does not send generation commands to VentuSample and it does not act as a DAW or plugin host.

### Example workflow

1. Export two sample packs from VentuSample into separate folders.
2. Copy or reference their ventusample_manifest.json files from the Reaper script directory.
3. Run examples/ventusample_pack_audit.rpr.
4. Inspect ventusample-comparison-report.json; provide an explicit Pytyliki DLL/SO path only when a native metric cross-check is intended.

Example script:

~~~reaper
make reference := read_json("packs/reference/ventusample_manifest.json")
make candidate := read_json("packs/candidate/ventusample_manifest.json")
make report := ventusample_compare(reference, candidate)
write_json("ventusample-comparison-report.json", report)
~~~

The optional native form is:

~~~reaper
make report := ventusample_compare(
    reference,
    candidate,
    "C:/trusted/Pytyliki/build/Release/pytyliki_ffi.dll"
)
~~~

## Shared OCTA-8 topology

The shared four-project federation matrix and OCTA-8 contract define four projects, twelve directed peer links, four self-loops and eight protocol facets. The apex is metadata-only.

VentuSample → Reaper pack exchange is implemented. Reaper → VentuSample render requests and direct VentuSample ↔ Pytyliki native calls remain planned. VentuSample ↔ OPlague is explicitly not applicable.

## Cross-repository references

- [OPlague repository](https://github.com/Ivan-VHS/OPlague) · [federation contract](https://github.com/Ivan-VHS/OPlague/blob/main/docs/FEDERATED_INTEGRATION.md)
- [Pytyliki repository](https://github.com/Ivan-VHS/Pytyliki) · [public ABI header](https://github.com/Ivan-VHS/Pytyliki/blob/main/src/interop.h)
- [VentuSample repository](https://github.com/Ivan-VHS/VentuSample) · [pack schema](https://github.com/Ivan-VHS/VentuSample/blob/main/schemas/ventusample.pack.v1.schema.json) · [Reaper pack audit](https://github.com/Ivan-VHS/VentuSample/blob/main/docs/REAPER_PACK_AUDIT.md)
- [Shared project contracts](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md)
