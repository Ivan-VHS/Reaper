# Industrial backend and systems-language profile

**Status:** architecture profile with an implemented first slice in the Python reference runtime. This document separates live behavior from staged systems work.

Reaper is intended to evolve as one inspectable pipeline: source → lexer/parser → semantic checks → canonical IR → execution engine or native backend → explicit host adapters → Studio/LSP/DAP. Domain state belongs to runtime services. The visual layer presents that state and submits commands through typed contracts; a widget or plugin does not receive OS privilege merely because it can display a control.

## Implemented foundations

| Domain | Existing implementation | Boundary |
|---|---|---|
| Language core | expression-oriented `.rpr`, functions, immutable/mutable bindings and pipelines | deliberately small grammar |
| Execution | bounded tree-walk reference runtime and bytecode VM | Python is the compatibility oracle |
| Type analysis | conservative inference for primitives, collections, calls and Result/Context contracts | not yet a sound ownership/effect system |
| Resource lifecycle | heap ledger, lexical regions, bounded file handles and interpreter cleanup | Python host allocator remains authoritative |
| Module system | canonical relative paths, UTF-8/size limits, export isolation, dependency graph and cycle detection | no package registry or remote fetch |
| Transaction state | optimistic generations, checksums, rollback, schema migration and bounded JSON snapshots | in-memory host API, not firmware flashing |
| Authorization | host-injected scoped consent grants, HMAC verification and revocation | host must protect the signing key |
| FFI | explicit opt-in C ABI bridge | trusted native code runs with process privileges |
| Audit | append-only local hash chain and verification | tamper-evident, not a signature or remote attestation |
| Native route | scalar AOT through generated C17 plus partial native lexer/parser/IR | no general object backend or full-runtime parity |
| Hardware | QCS validation, MCU profiles/linker helpers and checked MMIO adapter contract | no physical mapping, IRQ or DMA service |
| Visual tooling | desktop Studio foundation, diagnostics, stdio LSP/DAP, formatter and command palette | no GPU compositor or complete systems workbench |

## Typed results and explicit request context

The reference runtime now supports typed result values and explicit correlation context.

| Built-in | Contract |
|---|---|
| `ok(value, context?)` | Construct a successful `Result[T]` |
| `err(code, message, details?, context?)` | Construct a bounded structured failure |
| `is_ok(result)` / `is_err(result)` | Inspect the result branch |
| `result_value(result)` | Extract success or raise a source-located runtime error |
| `result_error(result)` | Return the structured error map, or `nothing` on success |
| `result_context(result)` | Return attached context, if present |
| `result_map(result, craft)` | Transform success and preserve failure |
| `result_and_then(result, craft)` | Compose a Result-returning operation; short-circuit failures |
| `result_recover(result, craft)` | Recover a failure through another Result-returning operation |
| `result_or(result, fallback)` | Select a fallback without throwing |
| `request_context(id, trace?, parent?, metadata?)` | Create explicit request/trace IDs and bounded JSON metadata |
| `context_with(context, key, value)` | Return a new context with one metadata field |
| `context_get(context, key)` | Read request IDs or metadata |
| `context_to_map(context)` | Produce a JSON-compatible context snapshot, or an empty map when context is absent |
| `runtime_stats()` | Read current step, call-depth, resource and heap counters/limits |

Result transformations preserve context unless a callback explicitly supplies a replacement. Failure branches are not passed to success callbacks. Error codes/messages are validated; structured details and context metadata must be finite JSON-compatible maps within 16 KiB. IDs are supplied explicitly: the runtime does not fabricate request identifiers or read a clock.

These values are synchronous. They do not implement task scheduling, retries, circuit breakers, deadline enforcement, network transport or asynchronous cancellation. A timeout or upstream failure must be returned by a real host adapter as an `err(...)` value; Reaper does not pretend to have called a service.

### Example

~~~reaper
craft validate_port(value) {
    when value < 1 {
        yield err("NET-EPORT", "port below range")
    } otherwise {
        when value > 65535 {
            yield err("NET-EPORT", "port above range")
        } otherwise {
            yield ok(value)
        }
    }
}

craft reserve_port(value) { yield ok(value) }
craft recover_port(error) { yield ok(8080) }

make context := request_context("req-42", "trace-42")
make candidate := ok(443, context)
make validated := candidate :: result_and_then(validate_port)
make reserved := validated :: result_and_then(reserve_port)
make recovered := reserved :: result_recover(recover_port)

when is_ok(reserved) {
    emit result_value(reserved)
} otherwise {
    emit result_error(reserved)
}
~~~

Run the checked-in example:

~~~sh
python -m reaper --check examples/backend_pipeline.rpr
python -m reaper examples/backend_pipeline.rpr
python -m reaper --engine vm examples/backend_pipeline.rpr
python -m unittest tests.test_result_runtime tests.test_duck_profile -v
~~~

## Industrial architecture rules

### 1. Core and host boundary

Pure parsing, type analysis, value transformations and result composition remain independent of the window system, network and device drivers. File, FFI, process and hardware operations enter through explicit host APIs/adapters. A plugin, native library or device bridge cannot grant itself a capability.

### 2. Contracts and state

Public adapters need versioned input/output schemas, validation before side effects, stable error codes, explicit partial-success semantics and idempotency keys for retryable mutations. State changes use a single owner, concurrency control, bounded transactions, monotonic generations and rollback. The existing transaction service supplies the in-memory foundation; durable storage and a migration runner need separate backend and recovery tests.

### 3. Memory and lifecycle

The language defaults to immutable bindings, tracks managed collections, bounds heap accounting and open resources, supports explicit regions, and closes managed files/FFI libraries on interpreter exit. The Python heap ledger is an estimate, not process RSS, a borrow checker or a memory-safety guarantee. Native ownership, borrows, deterministic drops and ABI layout remain compiler milestones.

### 4. Process and concurrency

Long-running process adapters must use argument vectors rather than shell concatenation, define working-directory/environment policy, bound output, apply deadlines, distinguish launch/exit/timeout/cancel states and reap children on shutdown. NOO TAH delegates JavaScript execution to official Node.js. A general process API, thread scheduler, actor/mailbox runtime and async cancellation model are not yet language features.

### 5. Network and resilience

A future network adapter must use explicit DNS/connect/read/write deadlines, TLS policy, response-size limits, per-host connection pools, bounded queues and backpressure. Retries require idempotency and bounded exponential delay with jitter. Circuit breakers, duplicate suppression, readiness/liveness and partial results need defined state machines and tests. Reaper currently does not expose a general TCP/IP or HTTP stack to `.rpr` programs.

### 6. Files and virtual storage

Managed file handles already have a bounded lifecycle and deterministic cleanup. A production VFS still needs mount namespaces, path authorization, symlink policy, atomic replacement, quota accounting, snapshot consistency, archive-bomb protection, recovery journaling and explicit filesystem adapters. The current file API is not a sandbox or virtual filesystem.

### 7. Observability

Use stable diagnostic codes for compiler/runtime failures, explicit request/trace context for service flows, bounded structured details and measured runtime counters. Logs must avoid secrets and payloads by default. Latency percentiles, distributed tracing exporters, metric aggregation, alert delivery and process/device health collectors require real sampling and retention policies; they are not inferred from UI animation.

### 8. Native compiler and hardware

New syntax is accepted only when lexer, parser, semantic/type rules, canonical IR, diagnostics, reference runtime, native backend and differential tests agree. The scalar C17 subset does not yet compile Result, Context, collection pipelines or managed resources. Device access remains behind a checked host-supplied bus adapter; physical MMIO, IRQ, DMA and privileged operations require an OS/driver implementation and hardware qualification.

### 9. Studio and native visual shell

Studio is a client of language/runtime services. It should render real model state, keep window/focus/input handling separate from domain work, submit commands through explicit requests, and represent pending/success/failure/stale/unavailable states distinctly. GPU rendering, blur, glass panels and animation are optional; opaque high-contrast fallbacks, keyboard access, immediate input acknowledgement, reduced motion and bounded UI-thread work are mandatory. A renderer must never run in compiler, device, file or timing-critical callbacks.

### 10. Gaming and system tuning

The compiler/runtime can provide workload metadata and bounded profiling, but cannot safely change OS scheduler priorities, pin CPU cores, modify GPU clocks, suppress notifications or reserve physical memory without a signed platform service and user policy. Any game profile must be opt-in, reversible, temperature/power-aware and validated on actual OS/hardware. No automatic game optimizer is claimed by this change.

## Migration gates

1. **Semantic contract:** Result/Context behavior, error codes, source positions, limits and Tree-walk/VM parity pass tests.
2. **Compiler parity:** versioned IR instructions and C17/native tests precede any native-parity claim.
3. **Host adapter:** each process, filesystem, network and device capability has explicit grants, deadlines, cancellation, resource budgets and cleanup.
4. **Reliability:** concurrency, fault injection, saturation, rollback, fuzzing and p50/p95/p99 measurements are reproducible.
5. **Studio:** CLI, LSP/DAP and Studio share the same contracts; UI updates remain non-blocking and accessible.
6. **Release:** security review, supply-chain controls, reproducible builds, migration/rollback and platform qualification are complete.

The XP SP3 era is a compatibility and operational history lesson only. Reaper should retain compatibility discipline without inheriting 32-bit address-space limits, weak privilege separation, obsolete driver assumptions or unsafe automatic process manipulation.
