# Federated integration: Reaper, OPlague and Pytyliki

Reaper remains the language and orchestration layer. It consumes versioned JSON
files from OPlague, applies Reaper-native operations, and may call the
Pytyliki C ABI v1 for selected numerical hot paths.

## Reaper standard-library contract

The following built-ins are available in .rpr programs:

| Built-in | Signature | Result |
|---|---|---|
| read_json | read_json(path) | JSON value (map/list/scalar) |
| write_json | write_json(path, value) | written path |
| oplage_metrics | oplage_metrics(snapshot) | validated metric map |
| oplage_compare | oplage_compare(reference, candidate[, library_path]) | read-only audit report |
| pytyliki_norm | pytyliki_norm(vector, library_path) | native float64 norm |
| pytyliki_dot | pytyliki_dot(left, right, library_path) | native float64 dot product |
| pytyliki_distance | pytyliki_distance(left, right, library_path) | native float64 distance |
| pytyliki_orthogonal | pytyliki_orthogonal(left, right, tolerance, library_path) | native boolean |

JSON reads reject duplicate object keys, NaN and Infinity, symbolic-link
inputs, non-UTF-8 data and files larger than 16 MiB. JSON writes reject
non-finite and non-JSON values, enforce the same size limit, and atomically
replace only the explicitly named output file. Parent directories are not
created implicitly.

OPlague snapshots must use the oplage.device-snapshot.v1 schema. Each metric
must be finite and normalized to [0, 1], higher meaning healthier/better.
Reference and candidate snapshots must expose identical metric dimensions.
A dimension change is an explicit error, not an implicit zero fill.

## Pytyliki FFI bridge

Native functions load only from an explicit absolute file path supplied by
the .rpr program. Reaper checks pytyliki_abi_version() == 1 and verifies all
required ABI v1 symbols before use. Inputs are contiguous float64 vectors with
1..4096 values. Buffers are owned by Reaper for the duration of the synchronous
call and are never retained by Pytyliki.

Examples of explicit native library paths:

- Windows: C:/path/to/Pytyliki/build/Release/pytyliki_ffi.dll
- Linux: /path/to/Pytyliki/build/libpytyliki_ffi.so
- macOS: /path/to/Pytyliki/build/libpytyliki_ffi.dylib

Loading a shared library executes native code with the permissions of Reaper.
Only use a library built from a trusted Pytyliki source tree. The bridge never
searches PATH, the current directory, environment variables or implicit DLL
locations and never loads an optional backend unless a script explicitly asks.

## End-to-end device audit

1. Run OPlague's read-only snapshot command on Windows:
   python -m tools.federation snapshot --output baseline.json
2. Capture a second snapshot later as current.json.
3. Run the .rpr script:
   reaper examples/device_audit.rpr
4. Inspect device-audit-report.json or use it as an automation artifact.

The included example uses Reaper's own numerical implementation by default.
To route the distance calculation through Pytyliki, change its comparison
call to include an explicit absolute DLL/SO path:

```reaper
make report := oplage_compare(baseline, current, "C:/trusted/Pytyliki/build/Release/pytyliki_ffi.dll")
```

The JSON and native bridge do not expose device mutation. Reaper cannot install,
remove, enable, disable or roll back drivers through these built-ins. OPlague's
driver-management safety gates remain independent.


## Cross-repository references

- **Shared 3 × 3 map:** [Project federation matrix](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md).
- **OPlague:** [repository](https://github.com/Ivan-VHS/OPlague), [federation contract](https://github.com/Ivan-VHS/OPlague/blob/main/docs/FEDERATED_INTEGRATION.md), [device snapshot producer](https://github.com/Ivan-VHS/OPlague/blob/main/tools/federation.py), [project manifest](https://github.com/Ivan-VHS/OPlague/blob/main/project-contract.json).
- **Pytyliki:** [repository](https://github.com/Ivan-VHS/Pytyliki), [federation contract](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/FEDERATED_INTEGRATION.md), [public ABI header](https://github.com/Ivan-VHS/Pytyliki/blob/main/src/interop.h), [project manifest](https://github.com/Ivan-VHS/Pytyliki/blob/main/project-contract.json).
- **Reaper evidence:** [snapshot and comparison bridge](../reaper/federation.py), [native FFI bridge](../reaper/ffi.py), [project manifest](../project-contract.json).


## OCTA-8 topology

The shared [OCTA-8 horizontal peer mesh](OCTA_PYRAMID_FEDERATION.md) records the full directed Reaper↔Pytyliki↔OPlague product, its three local self-loops and eight pyramid facets. Reaper remains the orchestration layer; the apex is only protocol metadata and does not route runtime traffic.
