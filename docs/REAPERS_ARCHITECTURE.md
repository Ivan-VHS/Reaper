# Reaper Cyclic Runtime Architecture

**Status:** first executable host-runtime slice; language syntax and native backend remain future milestones.  
**Baseline:** Reaper 0.1.x, Python 3.10+, standard library only.

This document turns the Reaper cyclic-runtime concept into testable subsystem contracts. The implementation preserves the existing lexer → parser → AST → bounded interpreter path. New mechanisms are initially exposed as Python host APIs; they do not silently grant Reaper source programs filesystem, network, process, or native-code access.

## 1. Architectural principles

1. **Evolution without a rewrite.** The tree-walking interpreter remains the semantic reference while experimental runtime services mature independently.
2. **Explicit capability boundaries.** Context propagation does not manufacture permissions. A capability must be supplied by the host.
3. **Bounded resources.** Every queue, registry, arena, profile table, and execution path has an explicit limit or lifecycle.
4. **Deterministic core first.** Local routing, mailbox order, snapshots, counters, and policy decisions have reproducible behavior.
5. **No imaginary zero-cost claims.** In-process dispatch avoids wire serialization; it is not mathematically free. Python reference cleanup is not a native O(1) arena reset.
6. **Backend parity.** A future bytecode or native backend must pass the interpreter's language conformance suite before it becomes a supported execution mode.

## 2. Subsystem map

| Concept | Reaper subsystem | Current evidence | Boundary |
|---|---|---|---|
| Citadel / mass relays | **reaper.relays.RelayBus** | Typed local endpoint registry and direct synchronous dispatch | In-process only; no network, serialization, retries, or delivery guarantees |
| Epochal harvest | **reaper.epoch.EpochArena** | Bounded reference groups, promotion, harvest, close | Python references are released in O(n); no custom allocator or hard real-time guarantee |
| Indoctrination / context | **reaper.effects.effect_scope** | Nested task-local context with immutable views | Host-side context API; no compiler effect inference or source rewriting |
| Harbinger / direct control | **reaper.profiling.HotPathProfiler** | Bounded call counters and ranked hot-path candidates | Advisory only; no JIT, machine-code generation, or CPU-specific specialization |
| Synthesis | Semantic IR roadmap | Design contract in this document | AST, values, and executable code are not yet one representation |
| Dragon's Teeth / FFI | Capability-gated FFI roadmap | Safety requirements below | No dynamic library loading or automatic C/C++ wrapper generation |
| Dark Space | **SovereignUnit.hibernate() / wake()** | JSON-safe state + mailbox snapshot with SHA-256 integrity check | State snapshot only; no stack, open descriptor, thread, or instruction-pointer freeze |
| “We are a nation” | **reaper.actors.SovereignUnit** | Single-threaded FIFO actor with bounded mailbox | No millions-of-actors scheduler, distributed consensus, or parallel execution |
| Vanguard | **reaper.sentinel.VanguardSentinel** | Validated health samples and advisory decisions | No process restart, cloud wake-up, traffic shifting, or external orchestration |

## 3. Executable contracts

### 3.1 RelayBus — typed local topology

**RelayBus.register(address, handler, payload_type=...)** installs one named endpoint. **send(address, payload)** validates the payload type and invokes the handler synchronously. Duplicate registrations, unknown addresses, invalid handlers, and endpoint-budget overflow fail explicitly.

~~~python
from reaper.relays import RelayBus

relays = RelayBus(max_endpoints=128)
relays.register("orders.validate", lambda order: order["id"], payload_type=dict)
order_id = relays.send("orders.validate", {"id": "R-17"})
~~~

This is a local call-dispatch table, not a transparent replacement for REST or gRPC. A future remote relay must declare a transport, wire format, trust model, timeout policy, back-pressure behavior, and delivery semantics.

### 3.2 EpochArena — bounded lifetime groups

An arena retains object references until **harvest()** or **close()**. A child arena can **promote(value)** into its parent. **max_objects** bounds retained references. Operations on a closed arena fail.

~~~python
from reaper.epoch import EpochArena

long_lived = EpochArena(max_objects=1000)
with EpochArena(parent=long_lived, max_objects=100) as request_epoch:
    result = request_epoch.retain({"request": 17})
    request_epoch.promote(result)
# request_epoch has released its remaining references
~~~

The Python implementation groups lifetimes but cannot promise O(1) destruction: clearing a list releases O(n) references, and Python's garbage collector controls actual reclamation. A native region allocator may later provide constant-time region reset when its ownership and destructor rules are proven.

### 3.3 Effect context — implicit propagation, explicit authority

**effect_scope()** overlays named values on the current **contextvars** context. Nested scopes shadow outer values and restore them on exit. The mapping exposed to callers is immutable. **get_effect()** raises **EffectUnavailableError** when a requested binding is absent.

~~~python
from reaper.effects import effect_scope, get_effect

with effect_scope(trace_id="req-17", transaction="tx-42"):
    with effect_scope(trace_id="child-18"):
        trace = get_effect("trace_id")  # child-18
        transaction = get_effect("transaction")  # tx-42
~~~

The mechanism propagates supplied objects; it does not grant access on its own. It does not yet infer algebraic effects, rewrite function bodies, or alter Reaper source semantics.

### 3.4 HotPathProfiler — candidate discovery

**HotPathProfiler** counts named execution sites under a bounded registry and returns deterministic candidates after a configurable threshold. Candidate order is descending call count, then name. The profiler never compiles or replaces code.

A future Harbinger backend must add statistically sound sampling, warm-up policy, de-optimization, code-cache limits, CPU-feature detection, and interpreter-equivalence tests before enabling JIT execution.

### 3.5 SovereignUnit — deterministic actors

A **SovereignUnit** owns JSON-compatible state, a FIFO mailbox, a handler, and a maximum mailbox size. **drain(max_messages=...)** processes messages in order. The handler receives copies of state and message; the next state is committed only after a successful return and JSON validation.

~~~python
from reaper.actors import SovereignUnit

def update(state, message):
    return {"balance": state["balance"] + message["delta"]}

ledger = SovereignUnit("ledger-1", {"balance": 100}, update, max_mailbox=500)
ledger.send({"delta": 25})
ledger.drain()
assert ledger.state == {"balance": 125}
~~~

The actor is deliberately single-threaded and deterministic. Handlers should avoid external side effects because a host callback cannot roll those side effects back if it raises.

### 3.6 Dark Space — integrity-checked hibernation

**hibernate()** serializes actor identity, JSON-compatible state, and pending mailbox contents into canonical UTF-8 JSON, then adds a SHA-256 digest. The actor becomes unavailable until **wake(snapshot)** verifies the digest, snapshot version, actor identity, and mailbox bounds.

This is a portable state snapshot, not a frozen process. It does not preserve a Python call stack, open files, sockets, thread state, timers, or an exact CPU instruction boundary. The integrity digest detects accidental or unauthorized modification; it is not an authenticated signature and does not establish trust in an untrusted snapshot producer.

### 3.7 VanguardSentinel — observe, classify, recommend

**VanguardSentinel.observe(HealthSample(...))** validates CPU, memory, error-rate, latency, and mailbox metrics. It returns a monotonically sequenced report with **healthy**, **warning**, or **critical** severity and an advisory action. Critical recommendations escalate only after the configured number of consecutive critical samples.

The sentinel does not collect metrics itself and does not restart, clone, or route services. A future supervisor requires a separately permissioned actuator, authenticated control plane, audit log, rate limits, and safe rollback behavior.

## 4. Deferred architecture contracts

### 4.1 Unified semantic representation

The long-term synthesis model should use a versioned, typed semantic graph shared by:
- parsed syntax and source locations;
- normalized expressions and control-flow blocks;
- type and effect metadata;
- interpreter instructions;
- future bytecode and native-code artifacts.

Runtime mutation must produce a new validated graph revision, not mutate arbitrary live AST objects behind the interpreter's back. Compilation must be bounded, cache keys must include target and semantic version, and generated code must pass the same semantic conformance suite as interpreted code.

### 4.2 Safe foreign-function boundary

FFI must be capability-gated and manifest-driven. A future manifest must declare library identity, ABI, symbol name, argument and result layouts, ownership, lifetime, thread-safety, error conversion, and allowed effects. Raw pointers remain unsafe handles; they must not be presented as automatically safe merely because a wrapper was generated.

Initial support should target a narrow C ABI and explicitly annotated functions. C++ templates, exceptions, arbitrary headers, callback lifetimes, and ownership inference require separate designs. WebAssembly can be a safer isolation boundary, but still needs resource quotas and explicit imports.

### 4.3 Adaptive execution

The interpreter remains the reference backend. A future tiered engine may use:
1. baseline interpreter execution;
2. bounded profiling;
3. candidate selection with warm-up and cooldown;
4. verified bytecode or native compilation;
5. guarded optimized execution;
6. de-optimization when assumptions fail.

No JIT status is reported as complete until generated code is actually executed and tested on supported targets.

### 4.4 Distributed relays and actor placement

Remote actors require versioned schemas, explicit serialization, authentication, authorization, replay protection, back-pressure, timeout and retry semantics, idempotency rules, and observability. A network address is not equivalent to an in-process endpoint. The local **RelayBus** API is not a distributed transport abstraction yet.

## 5. Failure and resource policy

- Exceeding an arena or endpoint limit raises an explicit exception.
- Missing effects fail closed.
- Unknown relay addresses and type mismatches fail before handler execution.
- Actor mailbox overflow rejects the new message; it does not silently drop an older message.
- Actor handler failure leaves the current message queued and does not commit the returned state.
- A malformed, modified, wrong-version, wrong-identity, or oversized actor snapshot is rejected.
- Sentinel input rejects non-finite metrics and out-of-range ratios.
- Profiling storage is bounded; candidates are advisory.
- These host APIs are not a security sandbox. Do not execute untrusted Python callbacks under the assumption that Reaper isolates them.

## 6. Acceptance gates and roadmap

| Phase | Deliverable | Acceptance gate |
|---|---|---|
| **I — Runtime primitives** | Epochs, effect context, local relays, deterministic actors, snapshots, sentinel, hot-path counters | Standard-library unit tests cover success, limits, lifecycle, malformed input, and failure rollback |
| **II — Language surface** | Versioned syntax for effect scopes, actor declarations, relays, and epoch scopes | Grammar, diagnostics, capability semantics, and interpreter tests; no implicit host privileges |
| **III — Semantic IR** | Versioned typed IR shared by validation and execution | Round-trip and interpreter conformance tests; bounded transformation |
| **IV — Bytecode / JIT** | Baseline bytecode and guarded optimization tiers | Differential tests, de-optimization, code-cache bounds, reproducible benchmarks |
| **V — FFI** | Manifest-based C ABI adapter and optional WASM adapter | Ownership, ABI, failure, and adversarial-input tests |
| **VI — Distributed runtime** | Remote relay transport, actor placement, supervisor actuators | Threat model, authn/authz, delivery semantics, failure injection, auditability |

**Release rule:** an item is “implemented” only when executable code and conformance tests exist. A design, type stub, example, benchmark target, or roadmap entry is not evidence of a working backend.
