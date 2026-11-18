# Reaper Systems — nine-part runtime architecture

**Status:** additive host-runtime architecture built on the compiler/runtime foundations in this branch. The nine concepts are design inspiration; implementation status and performance guarantees are defined by code and tests, not by their names.

## Product boundary

Reaper remains an independent, flow-first language. The current product contains a Python 3.10+ interpreter, a conservative static checker, a source-mapped portable IR frontend, bounded host-runtime APIs and a CLI. The systems in this document are Python host APIs unless a later language edition explicitly adds grammar, type-system and runtime support.

They do not silently grant `.rpr` programs filesystem, network, process or native-library access. Host capabilities must be granted explicitly. Nothing in this architecture is an operating-system sandbox.

## The nine systems

| # | Architecture concept | Current implementation | Verified contract | Not claimed |
|---:|---|---|---|---|
| 1 | **Citadel / Mass Relays** | `CitadelRouter` in `reaper.citadel` | Thread-safe named local routes, optional payload checks, counters, bounded route registry | Remote transport, network zero-copy, serialization-free cross-process calls |
| 2 | **Harvest / Epochs** | `Region`, `RegionRef`, `EpochManager` in `reaper.resources` | Bounded logical regions, move-invalidated handles, scoped borrows and epoch-delayed reclamation | Physical-memory return guarantees, universal O(1) reclamation, hard real-time latency |
| 3 | **Indoctrination / Effects** | `CapabilityAuthority`, `capability_scope`, `require_capability` in `reaper.security` | HMAC-authenticated process-local tokens, revocation and context-local permission checks | Invisible compiler rewriting, static effect types, OS sandboxing |
| 4 | **Harbinger / Direct Control** | `RuntimeProfiler`, optimizer in `reaper.profiling` and `reaper.compiler` | Call counts, wall-clock samples, hot-site ranking and safe literal constant folding | JIT/AOT machine code, SIMD specialization, deoptimization or guaranteed speedups |
| 5 | **Synthesis / Code and Data** | `CompilationUnit`, `IRNode`, `compile_source`, `optimize` in `reaper.compiler` | Immutable source-mapped IR, conservative type diagnostics, deterministic JSON and digests | Arbitrary runtime self-mutation, native execution or unrestricted compile-time evaluation |
| 6 | **Dragon's Teeth / FFI** | `parse_c_header`, `NativeLibrary`, `ForeignHandle` in `reaper.interop` | Limited scalar C prototype parsing, explicit capability-gated `ctypes` loading and managed handle release | Full C/C++ parsing, preprocessing, automatic ownership proofs, safe conversion of arbitrary pointers |
| 7 | **Dark Space / Hibernation** | `SnapshotStore`, `TransactionalStore` in `reaper.checkpoint` | Checksummed, schema-versioned JSON application-state snapshots, atomic replacement and copy-on-write transactions | Live process/stack capture, exact CPU continuation, transparent actor migration or microsecond wake-up |
| 8 | **Sovereign / Nation Actors** | `ActorSystem`, `ActorRef`, `TypedChannel` in `reaper.concurrency` | Cooperative asyncio actors, typed bounded queues, backpressure, handler restart hooks and structured shutdown | Millions of OS threads, distributed consensus, durable delivery or deterministic scheduling |
| 9 | **Vanguard / Sentinel** | `VanguardSentinel` in `reaper.vanguard` | Explicit health probes, actor-status inspection, bounded local recovery callbacks and immutable reports | Background self-management, cloud cloning, external orchestration or an unkillable supervisor |

## Integration sketch

The systems compose through explicit host APIs. This example uses only local capabilities and callbacks:

~~~python
from reaper.citadel import CitadelRouter
from reaper.vanguard import VanguardSentinel

routes = CitadelRouter(max_routes=32)
routes.register("metrics", consume_metrics, payload_type=dict)
routes.dispatch("metrics", {"queue_depth": 3})

sentinel = VanguardSentinel()
sentinel.watch(
    "metrics-consumer",
    probe=metrics_consumer_is_healthy,
    recovery=restart_metrics_consumer,
    max_recoveries=2,
)
report = sentinel.inspect()
if not report.healthy:
    sentinel.recover("metrics-consumer")  # explicit, budgeted action
~~~

The executable end-to-end example is [`examples/reaper_architecture.py`](../examples/reaper_architecture.py). Run it with:

~~~sh
python examples/reaper_architecture.py
python -m unittest discover -s tests -v
~~~

## Engineering decisions

### Local relay first, transport later

A process-local route can pass an object reference without serialization. This is useful for modularity and testing, but it remains a Python function call with lookup, locking and callback costs. A future remote relay must specify framing, schema versioning, authentication, backpressure, retries, ordering, cancellation and failure semantics before exposing a network API.

### Logical memory epochs, not magical reclamation

The current region API makes lifetimes observable and invalidates stale handles. Python owns the underlying objects, so clearing a region releases references; it does not guarantee that the allocator returns pages to the operating system. Epoch advancement is a safety policy, not an O(1) performance guarantee.

### Explicit effects and least privilege

Capabilities are granted by the host, scoped to an execution context and revocable. Reaper source does not acquire hidden effects. Native loading remains especially sensitive because loaded code executes in the host process; only trusted libraries should be used, and capabilities do not replace OS permissions.

### Profiling before specialization

The profiler records measurements. The current optimizer folds bounded, side-effect-free literal expressions in portable IR. These are distinct from a JIT. A future executable backend must define code-cache ownership, invalidation, deoptimization, CPU-feature detection and interpreter conformance before any JIT claim.

### Data snapshots are not process checkpoints

Snapshots store JSON-compatible application state with a checksum and schema version. They do not capture Python frames, open files, sockets, thread stacks or CPU registers. Restoring data is not resuming an instruction pointer.

## Acceptance gates for future language integration

| Future capability | Required evidence before calling it implemented |
|---|---|
| Language-level effect syntax | Grammar, static effect rules, handler semantics, capability-flow tests and compatibility tests |
| Native epoch allocator | Backend-owned memory, borrow/lifetime proofs, concurrent reclamation tests and allocator benchmarks |
| JIT/AOT/SIMD | Executable target backend, deoptimization or fallback policy, architecture tests and reproducible benchmarks |
| Distributed relays and actors | Versioned wire protocol, authenticated transport, bounded queues, cancellation, retry and fault-injection tests |
| Full C/C++ FFI | Parser/preprocessor strategy, ABI/layout validation, ownership model, panic/exception boundary and sanitizer-backed tests |
| Live process hibernation | OS/runtime checkpoint integration, descriptor policy, compatibility checks and measured restore benchmarks |
| Autonomous recovery | Explicit operator policy, idempotent recovery, retry budgets, audit trail and chaos tests |

## Compatibility and quality bar

- Keep existing `.rpr` syntax and interpreter behavior unchanged in this milestone.
- Keep the runtime standard-library-only and Python 3.10+ compatible.
- Validate limits before work or allocation where practical.
- Keep external effects explicit and fail closed when a capability is absent.
- Test healthy, failure, quota, stale-handle, restart, corruption and recovery-budget paths.
- Update all four README editions and the language/architecture references together.
