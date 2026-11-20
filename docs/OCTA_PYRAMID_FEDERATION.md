# OCTA-8 — Horizontal Peer Product and Octagonal Pyramid

**Status:** shared, validated topology for Reaper, Pytyliki and OPlague. It maps explicit interfaces; it is not a central runtime bus.

## Geometry

OCTA-8 has an octagonal base, eight triangular side facets and one coordination apex. The base plane is the horizontal peer layer: all three projects remain independent and each keeps a local self-loop.

The apex `octa-hub` is protocol/topology metadata only. It is non-executable, not a runtime gateway and not a single point of failure. Peers communicate directly.

## Horizontal multiplication

For three projects, the complete directed pairwise product is `n × (n − 1) = 3 × 2 = 6` directed peer links, plus three self-loops.

| Direction | Transport | Contract | Behavior |
|---|---|---|---|
| OPlague → Reaper | bounded JSON | `oplage.device-snapshot.v1` | read-only snapshot consumed by Reaper |
| Reaper → OPlague | bounded JSON | `reaper.oplage-comparison.v1` | OPlague validates Reaper's report |
| Reaper → Pytyliki | explicit native FFI request | `pytyliki.c-abi.v1` | bounded float64 metric call |
| Pytyliki → Reaper | synchronous ABI response | `pytyliki.c-abi.v1` | status/result returned through the call |
| OPlague → Pytyliki | explicit native FFI request | `pytyliki.c-abi.v1` | optional native distance cross-check |
| Pytyliki → OPlague | synchronous ABI response | `pytyliki.c-abi.v1` | bounded numeric result returned through the call |

FFI responses are synchronous returns to caller-initiated requests, not autonomous callbacks or peer-launched processes.

## Eight pyramid facets

1. **Identity and namespaces** — stable project/interface IDs and opaque person/device references.
2. **Contracts and versioning** — explicit schemas and ABI versions; breaking changes require a new version.
3. **Transport and bounded envelopes** — bounded JSON or synchronous ABI; malformed and oversized input is rejected.
4. **Provenance and integrity** — source digests and artifact lineage; a hash does not authenticate a publisher.
5. **Validation and normalization** — exact dimensions, units, ranges and finite-number checks.
6. **Privacy and consent** — pseudonymous device references; explicit opt-in for native loading and exports.
7. **Execution and safety** — read-only hardware evidence flow; no driver mutation through the mesh.
8. **Audit and reproducibility** — deterministic fingerprints, inspectable results and discrepancy states.

Topology JSON and JSON Schema: `federation/octa-pyramid.v1.json`, `schemas/octa-pyramid.v1.schema.json`. Validate with `python tools/validate_octa_pyramid.py` and `python -m unittest tests.test_octa_pyramid -v`.

## Project boundaries

Reaper owns orchestration/reports; Pytyliki owns the C11 numerical core/ABI; OPlague owns PnP inventory, package inspection and driver evidence. Native libraries are explicitly selected. Driver installation, removal, enable/disable and privileged operations are not added. This is a federation contract, not a monolithic merge.

## Cross-repository references

- [Reaper](https://github.com/Ivan-VHS/Reaper)
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki)
- [OPlague](https://github.com/Ivan-VHS/OPlague)
- [Reaper federation matrix](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md)
