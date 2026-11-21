# Federated integration

| Peer | Format | Boundary |
|---|---|---|
| OPlague | versioned device snapshot JSON | read-only |
| Pytyliki | C ABI v1 | explicit trusted library path |
| VentuSample | pack v1 manifest | metadata-only |

Validate schema, version, bounds and provenance. Native code is never loaded implicitly. No audio waveform analysis or driver/device mutation is implied.
