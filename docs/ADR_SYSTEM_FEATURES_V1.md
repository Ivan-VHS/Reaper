# ADR: Reaper System Features v1

**Status:** accepted for native system-contract implementation  
**Date:** 2026-11-26

## Context

The language needs a coherent systems layer for deterministic contract validation, bounded memory and task execution, reproducible state comparison, transient data handling, revision gates, expiry, observability, effect boundaries and reversible schema evolution.

The frontend and native C17 backend currently have different coverage. A capability catalogue entry is not evidence of executable language support, so the first delivery must make the native contracts executable while keeping language-level maturity explicit.

## Decision

1. Add one versioned C17 systems ABI with ten independently testable capability groups.
2. Use bounded caller-owned buffers for arenas, transient scopes, reconciliation plans and profiling histograms.
3. Make dependency ordering and aggregate reconciliation deterministic. Reject unsorted/ambiguous inputs instead of silently normalizing them.
4. Make task budgets cooperative and explicitly require host-level process/scheduler enforcement for hard preemption.
5. Keep reconciliation as a plan builder only. No persistence connector or automatic apply callback is included.
6. Require host-validated, revision-bound grants for manual authorization; do not copy opaque grant bytes into revision events.
7. Keep local-only effect validation free of network adapters. Transitive import effects must be supplied by the compiler.
8. Require tested forward and reverse migration steps.
9. Do not add syntax or promote language feature statuses until parser, type checker, canonical IR, reference runtime and supported backend behavior agree.

## Consequences

The C17 core exposes executable contracts that can be tested independently and called by a compiler/host integration. .rpr syntax, compile-time execution, IR lowering, runtime APIs, Studio completion and local metrics adapters remain follow-up integration gates. The registry therefore records these ten capabilities as specified at the language level.

The API is intentionally not a storage engine or a policy engine. Host integrations retain control over persistence, process isolation, local output channels and application-specific mutation semantics.
