# Reaper / Reapers Architecture — Engineering Specification

**Status:** experimental host-runtime reference implementation, added alongside Reaper 0.1.  
**Scope:** nine independently testable systems inspired by the Reapers mythology in *Mass Effect*. The mythology supplies names and design prompts; it is not evidence for performance or correctness claims.

## 1. Product and compatibility boundary

Reaper remains a flow-first language with its existing lexer, parser and Python tree-walking interpreter. This milestone adds 'reaper.reaper_systems', a standard-library-only host API for prototyping runtime mechanisms. It does **not** change '.rpr' grammar, inject hidden capabilities into language programs, or claim that Reaper is already a native compiler or distributed runtime.

The new module is deliberately opt-in. All operations that cross a trust boundary require an explicit capability or a caller-supplied handler. Snapshot payloads use JSON data rather than pickle. Mailboxes and snapshot sizes are bounded. The existing interpreter and its resource limits remain the reference execution path.

## 2. Nine systems and implemented contracts

| # | Reaper system | Reference implementation | Contract and current boundary |
|---:|---|---|---|
| 1 | **Citadel Relays** | 'RelayNetwork' | Named in-process routes, optional payload type checks, identity-preserving object handoff. No network transport, schema negotiation or remote zero-copy claim. |
| 2 | **Epochal Harvesting** | 'EpochArena' | Explicit allocations, selected-value promotion and bulk release of arena references at 'harvest()'. This is not a real-time allocator; Python finalizers and allocator behavior are outside the contract. |
| 3 | **Indoctrination Effects** | 'effect_scope', 'require_effect', 'requires_effects' | Nested context-local effect bindings using 'ContextVar'. Missing effects fail closed. This is scoped host context, not invisible compiler rewriting. |
| 4 | **Harbinger Tiering** | 'HotspotProfiler' | Records call counts and nanosecond durations, classifies hot sites and dispatches to an explicitly registered specialization. It does not emit machine code or perform JIT compilation. |
| 5 | **Synthesis** | 'IRNode', 'IRModule' | Immutable node topology, scalar literals, normalized attributes, versioned canonical JSON and SHA-256 digest. The IR is not yet generated from the parser AST or compiled to native code. |
| 6 | **Dragon's Teeth FFI** | 'ForeignFunctionSpec', 'ForeignFunction', 'FFIPermissions' | Explicit symbol grants, argument/result type checks and caller-provided callable adapters. No arbitrary library loading, pointer sanitization or automatic C/C++ conversion. |
| 7 | **Dark Space** | 'SnapshotCodec', 'StateSnapshot' | Size-bounded JSON serialization, SHA-256 integrity check and optional HMAC-SHA-256 authenticity. It stores data state only, not stacks, sockets or exact CPU execution position. |
| 8 | **Sovereign Units** | 'SovereignUnit' | Sequential local actor, FIFO bounded mailbox, JSON-only state and message envelope, state-preserving failure semantics, snapshot/awaken support. No distributed consensus or unbounded actor population guarantee. |
| 9 | **Vanguard Sentinel** | 'VanguardSentinel' | Named health probes and bounded recovery callbacks. Recovery is explicit and local; no embedded cloud agent or external service cloning. |

'architecture_summary()' and 'reaper --architecture' expose the current feature/boundary catalogue. The catalogue is documentation metadata, not a claim that future backends exist.

## 3. API sketches

### 3.1 Relays

~~~python
relay = RelayNetwork()
relay.register("metrics", consume, payload_type=dict)
result = relay.transmit("metrics", {"latency_ms": 12})
~~~

The relay resolves a local handler and passes the same object reference. A later network backend must define transport, framing, versioning, authentication, backpressure and failure semantics separately.

### 3.2 Epochs

~~~python
arena = EpochArena()
temporary = arena.allocate([1, 2, 3])
long_lived = arena.promote(arena.allocate({"id": "stable"}))
report = arena.harvest()
~~~

Promotion keeps selected references in the report; all arena-owned references are then released. The report's counts describe arena references, not bytes returned to the operating system. The current implementation cannot promise a universal O(1) harvest or deterministic destructors.

### 3.3 Effects

~~~python
@requires_effects("transaction", "trace")
def update_record(record):
    transaction = require_effect("transaction")
    trace = require_effect("trace")
    return transaction.write(record, trace=trace)

with effect_scope(transaction=db_transaction, trace=trace_context):
    update_record({"status": "ready"})
~~~

Scopes nest and are isolated by the Python context-variable model. Reaper source code does not gain file, network or process access from this API. A language-level effect checker/handler remains a later compiler milestone.

### 3.4 Profiled specialization

~~~python
profiler = HotspotProfiler(hot_threshold=500)
value = profiler.invoke("normalize", baseline_normalize, sample)
# A backend may register a tested specialization after the site is hot.
profiler.register_specialization("normalize", optimized_normalize)
~~~

The optimizer is intentionally an interface seam. A specialization must be supplied by a backend and must pass the same semantic tests as the baseline. Reported duration is wall-clock elapsed nanoseconds around the callable; it is not a CPU-cycle counter.

### 3.5 Semantic IR

~~~python
module = IRModule((
    IRNode("call", (IRNode("name", literal="sum"),), attributes=(("arity", 1),)),
))
print(module.digest)
~~~

Node identity is represented by a digest of canonical, versioned semantics. Consumers must compare canonical content when they need equality; a digest is an index, not a proof against hash collisions. Source maps, parser lowering and cache invalidation are future work.

### 3.6 FFI boundary

~~~python
sqrt = ForeignFunction(
    ForeignFunctionSpec("math.sqrt", (float,), float),
    math.sqrt,  # adapter supplied by the host application
)
with effect_scope(ffi=FFIPermissions({"math.sqrt"})):
    answer = sqrt(9.0)
~~~

A grant is exact-symbol by default; '*' is an explicit broad grant and should be avoided. The adapter is responsible for the underlying ABI, ownership, thread-safety and native error model. Type checks here do not make arbitrary native code memory-safe.

### 3.7 Snapshots and actor hibernation

~~~python
codec = SnapshotCodec(max_bytes=256_000)
snapshot = codec.freeze({"sequence": 41}, key=secret_key)
state = codec.restore(snapshot, key=secret_key)
~~~

HMAC is optional. Without a key, the digest detects accidental or unauthorized payload alteration only if the expected digest itself is trusted; it does not authenticate the producer. 'SovereignUnit.hibernate()' snapshots its state and queued JSON messages, clears its in-memory state and rejects further messages. 'SovereignUnit.awaken()' constructs a new unit from the snapshot and a caller-supplied handler.

### 3.8 Sovereign actors and Sentinel

~~~python
unit = SovereignUnit("inventory", {"count": 0}, handler, mailbox_capacity=128)
unit.send({"delta": 1})
unit.drain(max_messages=32)

sentinel = VanguardSentinel()
sentinel.watch("inventory", probe=unit_is_healthy, recover=restart_inventory, max_recoveries=2)
reports = sentinel.inspect()
~~~

Actors process messages sequentially. A handler returns '(new_state, result)'; if it raises, the message is consumed and the prior actor state remains unchanged. Recovery callbacks are application-defined and execute synchronously when inspection finds a failure.

## 4. Safety and resource rules

- **No implicit authority:** FFI requires an 'ffi' effect containing a matching 'FFIPermissions' grant.
- **No executable snapshots:** 'SnapshotCodec' accepts JSON-compatible scalar/list/map values only. It never unpickles code-bearing objects.
- **Integrity vs authenticity:** SHA-256 detects payload mismatch; HMAC authenticates snapshots only when the key is secret and correctly managed.
- **Bounded state:** snapshot byte length and actor mailbox capacity are checked before insertion or restoration.
- **Failure semantics:** route exceptions propagate; actor handler errors preserve the previous state and consume the failed message; sentinel recovery errors are returned in health reports.
- **No unmeasured claims:** no hard-real-time, zero-cost, microsecond wake-up, native JIT, memory-compaction or distributed fault-tolerance guarantee is made by this milestone.

## 5. Acceptance and test matrix

'tests/test_reaper_systems.py' covers all nine systems, including duplicate/missing routes, invalid promotion, effect denial and nesting, profiling thresholds and specialization, canonical IR stability, FFI permission/type failures, snapshot tampering and HMAC verification, bounded actor queues and hibernation restoration, plus bounded Sentinel recovery.

Run:

~~~sh
python -m unittest discover -s tests -v
python -m reaper --architecture
python examples/reaper_architecture.py
~~~

## 6. Next implementation gates

1. Lower the existing parser AST into the canonical IR while preserving source spans and proving deterministic output.
2. Add language-edition-aware type and effect checking before exposing effect syntax to '.rpr' programs.
3. Define a portable bytecode backend and differential tests against the tree-walking interpreter.
4. Only then consider a native optimizer, true region allocator, ABI-aware FFI generator or network relay transport.
5. Specify actor scheduling, mailbox backpressure, cancellation, persistence and distributed failure semantics before exposing remote execution.

A subsystem advances from prototype only when implementation, tests, supported-platform matrix and measurable acceptance evidence are present.
