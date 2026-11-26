# ADR: bounded snapshot integrity audit

**Status:** accepted for the first native-core increment  
**Date:** 2026-11-26

## Context

Reaper needs a reusable capability for checking whether versioned snapshot metadata is structurally consistent across logical shards. The first slice must remain deterministic, bounded, portable and independent of external services.

A source request also described high-sensitivity personal-data aggregation and record mutation. That application-specific workflow is outside this decision. This ADR adopts only the general snapshot-integrity problem and intentionally excludes individual-level personal-record linkage, sensitive-attribute selection, bulk data hydration and database mutation.

## Decision

1. Add a read-only C17 core API for snapshot-manifest validation and aggregate-only shard comparison.
2. Use sorted, ASCII-safe logical shard IDs and deterministic merge comparison. Reject malformed or unsorted inputs rather than silently repairing them.
3. Bound manifests to 4,096 shards and validity windows to 120 UTC calendar-day boundaries.
4. Provide a transient byte-equality helper that does not allocate, copy, log or retain its input.
5. Keep all host I/O outside the core API. No network, DBMS, persistence, record update or mutation hook is introduced.
6. Do not add lexer keywords or grammar productions in this increment. The .rpr type/stdlib facade is a separate compiler integration stage.
7. Mark the language capability specified until source-level types, runtime bindings, IR parity and .rpr tests exist.

## Consequences

The native core can be built and tested independently and can support offline integrity audits on synthetic or non-personal aggregate manifests. It does not constitute a full language-level implementation, an external connector or a data mutation pipeline.

The next language integration must define typed source values, explicit host effects, lifetime and escape rules for transient data, diagnostics with Span/SourceMap, and backend conformance before the feature can be promoted.
