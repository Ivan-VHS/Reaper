# Federated integration

| Peer | Format | Boundary |
|---|---|---|
| OPlague | versioned device snapshot JSON | read-only |
| Pytyliki | C ABI v1 | explicit trusted library path |

Validate schema, version, bounds and provenance. Native code is never loaded implicitly. Device/driver state is never mutated through federation.
