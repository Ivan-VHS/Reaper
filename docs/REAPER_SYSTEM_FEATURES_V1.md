# Reaper System Features v1

**Scope:** ten orthogonal systems-language capability contracts  
**ABI:** REAPER_SYSTEM_FEATURES_ABI_VERSION = 1  
**Native implementation:** include/reaper/system_features.h and src/system_features.c  
**Language maturity:** native API implemented in this change set; .rpr syntax, compiler-pipeline bindings, reference-runtime bindings and backend parity remain pending.

These capabilities are general-purpose building blocks for deterministic software, local-first applications, bounded runtimes, schema evolution and reproducible data processing. They contain no domain-specific identity selection or enforcement policy.

## 1. Deterministic comptime contract graph

**API:** reaper_contract_graph_validate, reaper_contract_graph_order

The compiler-facing verifier accepts immutable contract descriptors, field names/type IDs/flags, versioned dependencies and required dependency fields. It rejects duplicate names, missing dependencies, old versions, incompatible field shapes and cycles. A successful order is dependency-first and deterministic: ties are resolved by lexical contract ID.

Limits: 256 contracts, 64 fields per contract and 1,024 dependency edges. The C17 API is ready for a pre-emission compiler hook; that hook is not yet connected to the .rpr compilation pipeline.

## 2. Zero-allocation arena slots

**API:** reaper_arena_slot_begin, reaper_arena_slot_alloc, reaper_arena_slot_end

A slot owns no storage: the caller supplies a fixed buffer. Allocation performs checked power-of-two alignment and bounds checks without calling an allocator. End-of-frame resets the cursor and can zeroize every byte touched by that frame.

The slot descriptor must be initialized to zero before its first begin. A frame cannot be begun twice while active. Maximum supported alignment is 4,096 bytes.

## 3. Budgeted micro-workers

**API:** reaper_worker_budget_begin, reaper_worker_budget_checkpoint, reaper_worker_budget_dump

Each worker receives a monotonic CPU-time budget and an accounted-memory budget. The host calls checkpoint at explicit yield/safe points. An overrun moves the budget to a halted state and returns a compact state dump.

This is cooperative accounting, not an operating-system sandbox: it cannot preempt arbitrary non-cooperative code or impose a process RSS cap by itself. Hard isolation requires a host process/scheduler that enforces CPU and memory limits.

## 4. Diff/reconcile plan

**API:** reaper_reconcile_plan_build

Two sorted sets of aggregate resource states produce a deterministic union plan containing noop, upsert and drop. An optional invariant callback validates every candidate aggregate before output is written. Output capacity is checked before materialization; invalid input, invariant failure or insufficient capacity leaves the plan untouched and reports zero written items.

The API works on non-personal aggregate resource descriptors only. It does not apply the plan, write records, open databases or connect to remote systems. A separate host adapter must own any application-specific side effects.

## 5. Ephemeral match scopes

**API:** reaper_ephemeral_scope_begin, reaper_ephemeral_match, reaper_ephemeral_scope_end

The caller supplies scratch storage. The match operation compares fixed-size 32-byte digests with a constant-time byte comparison. Ending the scope overwrites the complete caller buffer through volatile writes, invalidates the scope and retains no pointer.

The API has no serializer, logger, cache or persistence callback. Callers must not export transient values or derived digests into persistent records, metrics, crash dumps or audit details. Initialize the scope descriptor to zero before its first begin.

## 6. Automatic/manual mutation authorization

**API:** reaper_mutation_authorize

Automatic mode requires a passing validator. Manual mode requires an opaque grant validated by the host, tied to the current revision, and bounded to 256 bytes. Both modes require an exact expected-revision match and return a revision event.

The native API authorizes and describes an operation; it does not apply it or write a journal. Host code must separately perform the operation and durably record the revision event. The token is never copied into the event.

## 7. Typed lease windows

**API:** reaper_lease_window_open, reaper_lease_window_check

The ReaperLeaseWindowDays value and REAPER_LEASE_DAYS(n) macro provide a compile-time check for literal durations from 1 to 120 days. A window uses UTC day numbers with an exclusive expiry boundary and can return lease-warning before expiry.

The generic .rpr type form lease_window<days> is not yet parsed or type-checked by the language frontend; the native value contract is implemented.

## 8. Runtime latency profiler

**API:** reaper_latency_profiler_init, reaper_latency_record, reaper_latency_summary

A fixed 28-bucket histogram records phase latencies without allocation. Up to 16 phases are supported. Summary reports sample count, integer mean, bucketed p95/p99 upper bounds and maximum latency.

The profiler is caller-owned and thread-confined. It does not create a local socket or log sink. A local-only read adapter may export summaries through an explicitly granted host effect; no network listener is introduced by this core.

## 9. Local-only effect boundary

**API:** reaper_module_effects_validate

The caller provides declared, inferred and transitively imported effect bitmasks. The checker rejects undeclared effects. When local_only is true, declared or observed network/remote-I/O effects are rejected, including effects from imports.

The compiler must aggregate transitive import effects and call this validator before code generation. The .rpr module-header parser and compiler binding remain pending.

## 10. Typed migration and rollback plan

**API:** reaper_rollback_plan_validate

Each plan names a migration, a strictly increasing source/target schema version, and distinct forward and reverse steps. Both steps must have passing test evidence. Missing rollback tests fail closed.

This API validates a plan; it does not execute migration callbacks or modify stored data.

## Integration and acceptance

The C17 module is part of reaper_core. The focused CTest target is native-system-features and contains ten independent test groups: graph order/cycles/field compatibility; arena alignment/bounds/zeroization; budget halt/dump; reconcile plan/invariants/atomic capacity; ephemeral match/wipe; mutation gates/revisions; lease warning/expiry; p95/p99; local-only transitive effects; and paired migration tests.

The capability registry lists all ten as specified at the language level until their syntax/AST/type-checker/IR/runtime/backend bindings have equivalent positive and negative coverage. No lexer keyword or parser production is claimed by this increment.
