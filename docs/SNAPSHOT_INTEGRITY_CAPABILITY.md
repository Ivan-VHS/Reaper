# Snapshot integrity audit capability

**Status:** native C17 core implemented; direct .rpr standard-library binding remains pending  
**ABI:** REAPER_SNAPSHOT_AUDIT_ABI_VERSION = 1  
**Mode:** deterministic, bounded, read-only metadata audit

## Purpose

Reaper provides a native core for validating snapshot manifests and comparing aggregate shard metadata. The operation is suitable for reproducibility checks, schema-drift detection, inventory consistency and offline validation of synthetic fixtures.

The first increment deliberately compares **logical shard aggregates only**. It does not read, hydrate, join, identify or mutate individual records.

## Native API

The public contract is include/reaper/snapshot_audit.h and the implementation is src/snapshot_audit.c.

- **reaper_snapshot_manifest_validate** checks a non-zero generation, the validity window, the shard-count limit, ASCII-safe logical shard IDs, non-zero schema versions and strict deterministic ordering.
- **reaper_snapshot_compare** merges two sorted manifest sequences and emits unchanged, content-changed, schema-changed, added or removed aggregate states.
- **reaper_snapshot_transient_equal** compares caller-owned transient byte buffers without allocation, copying, logging or retention.
- **reaper_snapshot_audit_status_name** and **reaper_snapshot_delta_kind_name** expose stable status names.

A delta contains only a logical shard ID, schema versions and aggregate item counts. It never contains a record key, field value or digest. Delta IDs borrow storage from the input manifest; callers must keep the manifests alive while using the result.

## Time and bounds

created_day_utc, valid_until_day_utc and current_day_utc are UTC day numbers counted from 1970-01-01. The expiry boundary is exclusive: a snapshot is invalid when current_day_utc is greater than or equal to valid_until_day_utc. A manifest validity window must be between 1 and 120 calendar-day boundaries.

The implementation caps a manifest at 4,096 shards and each shard ID at 96 ASCII characters. Shard IDs are restricted to letters, digits, dot, underscore and hyphen. Entries must be strictly sorted by bytewise ID order; duplicates and unsorted input are rejected instead of being silently normalized.

The comparison requires a newer generation and a non-decreasing creation day. It validates output capacity before writing any delta. A capacity or validation failure leaves the output array untouched and sets written to zero.

## Transient and no-persist data

reaper_snapshot_transient_equal is the only transient comparison primitive in this increment. It uses caller-owned buffers, performs a fixed-length comparison, allocates no memory and returns only a Boolean. The API has no persistence sink and no logging callback.

A host must not pass no-persist values, derived identifiers or their digests into a manifest, delta, trace, cache, crash report or persistent log. The caller remains responsible for limiting buffer lifetime and zeroizing sensitive buffers after the comparison. A comparison result must not be used to reconstruct or identify a person.

## Explicit boundaries

This capability does not provide:

- person-level or household-level linkage, identity resolution or demographic filtering;
- bulk hydration of personal data or joins across citizen, personnel or conscription records;
- live API, DBMS, shard or external service connectors;
- row-level diff, upsert, delete, commit, override or hotfix execution;
- an automated decision, ranking, eligibility or enforcement workflow.

Host I/O remains explicit and separately permissioned. The native core is read-only and offline; it cannot connect to a data source or persist mutations.

## Language integration and maturity

No new keyword is introduced. The existing Reaper keyword and operator surface stays unchanged. This avoids claiming parser, type-checker, VM or AOT support that does not exist yet.

The C17 core is built into reaper_core and has native conformance tests. The .rpr standard-library facade, typed SnapshotManifest/SnapshotDelta declarations, canonical IR representation and Studio/LSP completion are subsequent integration work. The feature registry therefore records the language-level capability as specified, not implemented or verified.

Promotion to a language-level implemented state requires all of the following:

1. Reaper-owned source-level types and a stable standard-library contract.
2. Explicit effect/capability declarations for host reads and transient operations.
3. Runtime and canonical IR parity, including deterministic ordering and error behavior.
4. Negative tests for expiry, invalid manifests, bounds, duplicate IDs and transient-data escape.
5. Differential tests across the reference runtime and native backends.
6. Confirmation that transient buffers and their derived values do not cross a persistence boundary.

Build and run the focused native test through CMake's native-snapshot-audit target.
