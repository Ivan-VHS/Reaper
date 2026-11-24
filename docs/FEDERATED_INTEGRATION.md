# Federated integration

Reaper participates in two deliberately separate integration layers:

1. **OCTA-8 specialist peer mesh** — Reaper, Pytyliki, OPlague and VentuSample remain four independently versioned projects. The four-project topology in `federation/octa-pyramid.v1.json` is unchanged; DuckOS is not a fifth peer, mesh gateway or shared runtime.
2. **DuckOS host integration** — DuckOS may launch Reaper's developer tooling as a separate user-space process and may pass an explicit read-only hardware inventory artifact to Reaper for validation.

## Specialist peer contracts

| Peer | Format | Boundary |
|---|---|---|
| OPlague | versioned device snapshot JSON | read-only evidence; validate schema, bounds and provenance |
| Pytyliki | C ABI v1 | explicit trusted library path; opt-in native loading |
| VentuSample | no direct Reaper runtime coupling | separate product ownership; no implicit dependency |

The OCTA-8 validator remains authoritative for the four specialist peers, twelve directed links, eight facets and four self-loops. Do not insert host applications or orchestration products into that topology.

## DuckOS host contract

| Direction | Interface | Transport | Boundary |
|---|---|---|---|
| DuckOS → Reaper | `reaper.cli.static-check.v1` | bounded subprocess | explicit argv, `shell=False`, timeout and capped captured output |
| DuckOS → Reaper | `duckos.hardware-inventory.v1` | caller-selected JSON file | strict UTF-8 JSON, duplicate-key rejection, finite values, 16 MiB cap and digest validation |

DuckOS owns the native desktop panel and process discovery. Reaper owns its grammar, semantics, diagnostics, reference runtime and CLI. The host bridge does not import the Reaper interpreter into the DuckOS process, and static-check operations do not execute the selected Reaper source file.

The hardware inventory is produced by DuckOS in read-only mode and audited by Reaper through `reaper-duckos-audit`. Reaper validates the exact v1 field set, supported platform, per-device bounds, aggregate counts and canonical SHA-256 digest. The report is diagnostic only: it does not authorize driver downloads, installation, firmware changes or device mutation. See [DuckOS hardware inventory integration](DUCKOS_HARDWARE_AUDIT.md).

## Compatibility and security rules

- Keep the DuckOS host integration separate from the OCTA-8 peer topology and version its own interfaces.
- Prefer a versioned JSON artifact for offline exchange; use a subprocess for host tooling; use native FFI only through an explicit trusted library path.
- Bound input size, device count, text fields, process duration and captured output.
- Reject duplicate JSON object properties and non-finite numeric constants before schema/domain validation.
- Treat hashes as content-integrity checks, not proof of publisher identity or authenticity.
- Keep host operations least-privileged and explicit; native code is never loaded implicitly.
- Device/driver state is never mutated through federation.
- Update producer schemas, consumer validators, tests and documentation together when a shared contract changes.
