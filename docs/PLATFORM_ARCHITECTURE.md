# Reaper platform architecture

Status: additive runtime foundations for the existing Python-hosted language. This document distinguishes executable behavior from later backend goals.

## Original subsystem vocabulary

The implementation uses project-specific names rather than character, faction, organization or technology names from third-party fictional universes.

| Subsystem | Responsibility | Current evidence |
|---|---|---|
| Quarry IR | Source-mapped intermediate representation and deterministic serialization | compiler.py, IR verifier and digest tests |
| Morrow Types | Conservative static checking for the implemented language slice | TypeChecker, negative type tests and compiler CLI |
| Glassforge | Pure constant-folding transformations | Optimizer and division-by-zero preservation tests |
| Epoch Basin | Bounded logical regions, move semantics, borrows and epoch reclamation | resources.py and lifetime tests |
| Cairn Actors | Isolated asynchronous message handlers and supervision | concurrency.py and actor tests |
| Conduit Channels | Typed bounded queues with producer backpressure | TypedChannel and capacity tests |
| Keyguard | Explicit, revocable, process-local capabilities | security.py and permission tests |
| Waystone | Checksummed application-state snapshots | checkpoint.py, corruption and round-trip tests |
| LedgerStore | Copy-on-write transactions persisted through atomic replacement | TransactionalStore and rollback tests |
| Pulse Metrics | Execution timing, counters and hot-function detection | profiling.py and threshold tests |
| Portico FFI | Scalar C ABI declaration parsing and capability-gated loading | interop.py and parser tests |
| Mosaic Bridge | Explicit foreign adapter registration and owned handles | AdapterRegistry, PythonAdapter and release tests |
| Orbit Scope | Parent-owned actor task lifetime and bounded shutdown | ActorSystem context-manager tests |
| Adaptive Tuner | Measured hot-spot ranking and conservative IR optimization | profiler and optimizer APIs; no machine-code specialization |

These labels are identifiers for this repository's design. They do not imply that every planned subsystem is complete or that a name is legally cleared in every territory.

## Implementation sequence and status

### Stage 1 — Compiler front end

**Implemented in this change:** lexer and parser reuse; source-mapped immutable IR nodes; conservative static diagnostics; deterministic source and IR digests; structural IR verification; JSON compiler CLI; optional constant folding.

**Not implemented:** typed syntax annotations, full generic inference, algebraic data types, pattern exhaustiveness, hygienic macros, self-hosting or executable machine code.

### Stage 2 — Resource lifetimes

**Implemented in this change:** a bounded logical region, handles that become invalid after move, scoped borrow guards, and an epoch manager that delays reclamation until a later epoch.

**Boundary:** Python retains ownership of the actual objects. The API can invalidate handles and clear region references, but it cannot promise deterministic native memory reclamation, a zero-copy allocator or hard real-time latency.

### Stage 3 — Concurrency

**Implemented in this change:** asynchronous actors, typed mailboxes, bounded channels, backpressure, handler-factory restart supervision and structured shutdown when an ActorSystem scope exits.

**Not implemented:** distributed actors, deterministic replay, lock-free scheduling, work stealing, real-time deadlines or a static effect system. A supervisor restart reconstructs the handler from its factory; it does not restore arbitrary external state.

### Stage 4 — Adaptive execution

**Implemented in this change:** call/time metrics, hot-function ranking and a deterministic constant-folding IR pass.

**Not implemented:** AOT machine-code generation, a JIT compiler, code caches, deoptimization, SIMD lowering or claims of speedup. These require a verified executable backend and reproducible target benchmarks.

### Stage 5 — Metaprogramming

**Implemented in this change:** typed IR data structures and an optimizer interface over immutable nodes.

**Not implemented:** source-level macro syntax, hygienic expansion, runtime code generation or compile-time execution of arbitrary program code.

### Stage 6 — Native integration

**Implemented in this change:** a narrow reader for scalar C function prototypes, explicit ctypes binding, capability-gated library loading, and revocable foreign handles.

**Not implemented:** general C preprocessing, struct/union layout inference, variadic calls, generated ownership proofs, arbitrary C++ bindings or a WebAssembly engine. Only trusted native libraries should ever be loaded.

### Stage 7 — State continuity

**Implemented in this change:** checksummed JSON snapshots, schema versioning, atomic file replacement and copy-on-write key/value transactions.

**Not implemented:** process checkpointing, stack capture, live actor continuation capture, transparent crash recovery or online snapshot migration. The stored state must be explicitly JSON-serializable application data.

### Stage 8 — Language adapters

**Implemented in this change:** a host-controlled adapter registry and a Python identity adapter.

**Not implemented:** JavaScript, JVM, .NET or WebAssembly bridges, shared-memory ABI negotiation, garbage-collector coordination or foreign-thread attachment.

### Stage 9 — Production assurance

**Implemented in this change:** standard-library tests for successful paths, negative paths, boundaries, quotas, stale handles, channel capacity, restart behavior, snapshot corruption, capability revocation and C declaration limits.

**Remaining:** security audit, debugger, package manager, signed artifact/release pipeline, deterministic cross-platform builds, fuzz/property suites, native-target conformance and operational incident runbooks.

## Compiler command

After installing the package:

~~~sh
reaperc examples/hello.rpr
reaperc examples/flow.rpr --optimize
~~~

The command emits JSON IR. A successful compilation proves front-end parsing, the current conservative checker and IR verification only. It does not prove that the program can be lowered to native machine code.

## Security and effect boundary

The current interpreter still exposes only its documented language operations. Capabilities added here are host APIs; they are not automatically injected into Reaper programs. A capability token is process-local and revocable, but does not replace OS permissions, sandboxing, code signing or a security review.

Native loading executes code in the host process. It is therefore gated by an explicit capability and must be limited to libraries obtained from a trusted source. The C declaration reader supports a deliberately narrow set of scalar types to avoid pretending to understand arbitrary C headers.

## Independent naming and rights hygiene

This change uses independently authored subsystem labels and original implementation text. It does not include third-party character names, fictional terminology, logos, artwork, quotations or copied source code from a media franchise. Keep source provenance, contributor authorship and third-party dependency notices with future changes.

Renaming architectural labels is not a legal guarantee and cannot prevent every copyright, trademark, patent or unfair-competition claim. No trademark clearance search or legal opinion is performed by this repository change. Before public branding or commercial distribution, check relevant registries in target markets and obtain qualified legal review. The repository's existing Apache-2.0 license remains unchanged; no relicensing or patent covenant is implied.
