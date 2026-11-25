# Reaper declarative file formats and extension registry

**Document ID:** REAPER-FORMATS-STD-001  
**Version:** 1.0  
**Status:** Format roles and invariants specified; parsers, validators and runtime handlers planned  
**Machine-readable planning registry:** ../reaper-file-extensions.v1.json  
**Registry schema:** ../schemas/reaper-file-extensions.v1.schema.json

## 1. Purpose and implementation boundary

This document consolidates the stream, memory, I/O, event, storage, routing and self-host file formats proposed in OS(2).txt. It turns their purpose and invariants into a versioned planning contract.

The registry is an inventory for architecture and review. It is **not** consumed by the current Reaper compiler, interpreter, VM, Studio, LSP or DAP. No parser, formatter, syntax highlighter, module loader or runtime support is claimed for these new formats.

The code fragments in OS(2).txt are conceptual sketches. They must be reworked against the actual Reaper grammar, canonical IR, Span/SourceMap, module system, diagnostics and compiler subset before they can be used as executable examples. In particular, a snippet containing unfamiliar declarations or host calls is not valid Reaper merely because it uses a .rpr-looking filename.

The new format definitions must preserve explicit effects, bounded resources, deterministic behavior, clear user/kernel boundaries and stable ABI contracts. External I/O, file access, clocks, device access, process operations and network access remain explicit capability-gated effects.

## 2. Namespace decision

The buffer description in OS(2).txt assigned .bav to **Buffer Allocation & Validation**, while the same document also assigns .bav to BAV antivirus/security bundles.

One suffix cannot identify two unrelated formats. The namespace is fixed as follows:

| Suffix | Owner | Meaning | Current status |
|---|---|---|---|
| .bav | DuckOS BAV Security | Signed declarative BAV detection-policy bundle | External DuckOS contract; not parsed by Reaper |
| .bufspec | Reaper | Buffer Allocation & Validation specification | Specified; parser not implemented |

Reaper already uses the policy identifier duckos.bav.defense-context.v1 and the file security/defense-context.v1.tsv. The policy identifier is a namespace, not a file extension. The TSV is a descriptive context vocabulary, not a malware-signature list.

The context taxonomy MUST remain informational. A topic match cannot increase malware confidence, create a malicious verdict, block a build or execution, quarantine/delete a file or revoke a capability.

The Reaper repository's Beelzebul 66-rule scanner remains a read-only repository-assurance tool. It inspects tracked repository content and CI/security metadata; it is not an endpoint scanner and does not provide process-memory or on-access protection.

## 3. Proposed Reaper formats

All ten Reaper-owned format entries below plus .bufspec are contract specifications only. The registry records their boundaries and intended dependencies; those dependencies are not yet executable module imports.

### 3.1 .tpr — Topology / Thread Pipeline Registry

Declares a stream graph: nodes, directed producer-to-consumer edges, channels, element types, capacities and backpressure policies.

Required invariants:
- Every channel declares an element type and finite capacity. Unbounded queues are prohibited.
- Every node declares its full-channel behavior: block, drop-newest, drop-oldest or explicitly configured spill-to-swap.
- The graph checker rejects invalid references, incompatible edge types and unmanaged cycles before execution.
- Queue size, memory budget and overflow behavior are explicit.

Acceptance evidence: valid/invalid topology fixtures, cycle detection, type mismatch, queue-capacity bounds, deterministic diagnostics and stable source spans.

### 3.2 .bufspec — Buffer Allocation & Validation

Declares buffer alignment, header and payload sizes, minimum/maximum frame sizes, high-/low-water marks and boundary/integrity rules.

Required invariants:
- Sizes and alignments are explicit and checked for overflow and target compatibility.
- Low-water is less than high-water; all values fit the declared buffer capacity.
- Frame headers and payload extents are validated before access.
- Hot paths declare allocation behavior and cannot hide unbounded allocation.

Acceptance evidence: alignment/bounds fixtures, overflow and zero-size cases, malformed frame headers, watermark ordering, target-width checks and property tests for range arithmetic.

### 3.3 .aio — Asynchronous Input / Output

Declares non-blocking I/O channels, readiness behavior, timeout, cancellation, outstanding-operation limits and partial read/write semantics.

Required invariants:
- Every operation has a timeout or a cancellable wait state.
- Partial transfers are represented explicitly; a stream descriptor is never assumed to complete an entire frame in one read/write.
- Pending operations and queue depth have finite limits.
- Cancellation and completion cannot both commit the same operation.

Acceptance evidence: partial read/write fixtures, timeout/cancellation race tests, saturation/backpressure, completion ordering and resource-release checks.

### 3.4 .oie — Output Ingress Engine / Event

Declares outgoing event frames, telemetry/metrics, sequence/timestamp semantics and output sinks.

Required invariants:
- Every event has a versioned schema and monotonic sequence or time-ordering contract.
- Sink failure cannot crash the producer's main processing path.
- Queue capacity, sampling, drop/coalescing and error accounting are explicit.
- Diagnostic output is bounded and must not leak secrets.

Acceptance evidence: schema evolution fixtures, ordering checks, sink-failure isolation, bounded queue tests and secret-redaction cases.

### 3.5 .eio — Egress / External Input Output

Declares boundaries with devices, files, sockets, external processes and federation protocols.

Required invariants:
- Every external input is validated for format, size, identity and granted capability at the boundary.
- External dependencies and protocol versions are listed explicitly.
- Timeouts, cancellation, partial transfer and disconnect behavior are defined.
- No ambient filesystem, network, device or subprocess permission is implied.

Acceptance evidence: malformed input, length overflow, path traversal, peer/version mismatch, permission denial, timeout and disconnect tests.

### 3.6 .sor — Stream Ordering & Reduction

Declares ordering keys, monotonic timestamps, watermarks, aggregation windows, allowed lateness and deterministic reduction behavior.

Required invariants:
- Ordering and window definitions are explicit and versioned.
- Reduction is deterministic for identical inputs and declared conflict/duplicate resolution.
- Late-frame behavior is explicit: accept-late, side-output or counted drop.
- Timestamp units, source clock, precision and tie-breaking are specified.

Acceptance evidence: out-of-order, duplicate, late, equal-timestamp, clock-boundary and replay fixtures; deterministic output comparison.

### 3.7 .col — Collection / Coalescing Layout

Declares frame batching/coalescing, size/count thresholds, linger time and field/memory layout.

Required invariants:
- Batch count and byte thresholds are finite.
- A maximum linger/flush deadline is explicit.
- Layout and alignment are declared and checked.
- Batching cannot silently violate downstream latency or memory budgets.

Acceptance evidence: max count/size boundaries, flush timeout, cancellation, allocation-failure and throughput-vs-tail-latency measurements.

### 3.8 .wal — Write-Ahead Log

Declares write-ahead records for state mutations, graph changes, snapshots and recovery.

Required invariants:
- Intent is journaled before the corresponding durable state mutation.
- Records have monotonic sequence and integrity markers/checksums.
- Torn or truncated tails have deterministic recovery behavior.
- Flush/fsync semantics and durability boundaries are explicit.
- Replay is idempotent or detects duplicate application.

Acceptance evidence: interrupted write, torn header/payload, checksum mismatch, duplicate replay, ordering and power-loss/fault-injection tests.

### 3.9 .swap — State Swap / Staging Page

Declares cold-state eviction and restore behavior under memory pressure or bounded backpressure.

Required invariants:
- Evicted state has a versioned serialization contract and integrity check.
- Restore validates schema, ownership and content identity before activation.
- Swapping is prohibited on a hard real-time path unless the owning contract explicitly permits it.
- Limits cover bytes, concurrency, retries and failure recovery.

Acceptance evidence: round-trip tests, corrupted snapshot, version mismatch, partial write, low-memory, interrupted restore and real-time exclusion tests.

### 3.10 .sw — Stream Wire / Switch

Declares conditional routing, filters, fan-out/fan-in and fallback paths between graph nodes.

Required invariants:
- Every input frame has a defined route, counted drop or declared fallback.
- Routing conditions are typed and deterministic.
- Unmanaged feedback loops are rejected.
- Queue capacity and overload behavior are inherited explicitly from the relevant channel contract.

Acceptance evidence: route priority, missing route, overlapping condition, cycle detection, fan-out bounds and replay determinism.

### 3.11 .svpr — Selfhost Verified Pipeline Rewrite

Declares controlled rewrite passes for Reaper modules, pipeline nodes and compiler transformations.

Required invariants:
- Rewriting follows verify → stage → compile/check → commit, with an explicit rollback point.
- Preconditions include source/IR identity and the contract versions being preserved.
- Core security, ABI and repeatability invariants cannot be weakened implicitly.
- Rewrites cannot invoke arbitrary shell commands or execute embedded payloads.
- Every rewrite emits deterministic diagnostics and an audit record.

Acceptance evidence: valid rewrite, rejected precondition, compile failure rollback, conflicting rewrite, malformed plan, deterministic output and preservation of source spans/contracts.

## 4. Cross-format conflict checks

The compiler/validator must check relationships, not merely parse each document independently.

| Conflict | Required behavior |
|---|---|
| .tpr capacity exceeds .bufspec memory budget | Reject with a bounded-memory diagnostic |
| .col batch/linger exceeds .aio or .oie latency budget | Reject or require an explicit reviewed override |
| .swap evicts state needed by an active hard-deadline path | Reject unless explicitly permitted by the timing contract |
| .wal durability mode conflicts with storage capabilities | Reject before state mutation |
| .sw routes create an unmanaged cycle | Reject with the exact cycle and source spans |
| .svpr weakens a security, ABI or repeatability invariant | Reject unless a versioned migration is explicitly approved |
| .eio requests ungranted file/network/device/process effects | Deny at the effect/capability boundary |

Every conflict must have a stable diagnostic code, primary Span, related spans and a deterministic remediation message. No validator may silently rewrite an input file to make it pass.

## 5. Implementation sequence

1. **F0 — Namespace and registry:** reserve .bav for DuckOS BAV, rename the buffer format to .bufspec and validate the planning registry.
2. **F1 — Shared contract foundations:** define primitive types, version negotiation, units, integer widths, error codes, source spans and deterministic serialization.
3. **F2 — .bufspec:** implement bounded buffer arithmetic and compile-time checks before any stream graph depends on it.
4. **F3 — .tpr:** implement topology parsing, typed edges, finite queues and deterministic cycle/type diagnostics.
5. **F4 — .aio and .eio:** define the I/O effect model, timeout/cancellation state machine and explicit host adapters.
6. **F5 — .oie and .sor:** version event schemas, ordering, watermarks and deterministic reduction.
7. **F6 — .col and .sw:** add batching and routing only with cross-format latency, capacity and cycle checks.
8. **F7 — .wal and .swap:** implement durable journal/restore behavior with fault injection and explicit storage semantics.
9. **F8 — .svpr:** implement verified transactional rewrites only after IR/source-map stability and rollback are established.

Each stage needs its own grammar/schema, parser, canonical typed IR representation, Span/SourceMap diagnostics, negative/property/fuzz tests, compatibility fixtures and CI. The implementation must use Reaper's actual supported language syntax; the source's conceptual examples are not copied as compilable code.

## 6. Registry and status rules

The machine-readable registry is deliberately called a planning registry. Its presence does not imply runtime discovery or parsing. For each format, future implementation evidence must name:
- grammar and schema version;
- parser and validator source paths;
- canonical IR node mapping;
- source-span and diagnostic behavior;
- runtime/compiler consumer, if any;
- resource and effect budgets;
- test fixtures and CI jobs;
- compatibility and migration policy.

A format remains Planned until parser, validator, fixtures and the actual owning workflow exist. It becomes Verified only for the tested compiler/runtime and declared target.

## 7. Related BAV boundary

The BAV security bundle is specified by DuckOS, not Reaper. Reaper's Beelzebul repository scanner and defense-context TSV remain separate tools/data contracts. They cannot be treated as an endpoint antivirus engine or as malware signatures. See [Defensive security doctrine and BAV context taxonomy](DEFENSIVE_SECURITY_DOCTRINE.md).
