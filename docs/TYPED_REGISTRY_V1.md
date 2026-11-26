# Reaper Typed Registry v1

**Status:** native C17 registry engine implemented as an allocation-free library.  
**ABI:** `REAPER_TYPED_REGISTRY_ABI_VERSION = 1`.  
**Purpose:** register versioned operation contracts, validate typed inputs and outputs, enforce host-granted capability masks, and dispatch only explicitly supplied handlers.

## What it provides

Typed Registry is a reusable runtime contract layer. It is separate from the existing 18-module / 108-operation capability catalogue and the 84-operation System Runtime catalogue. Those catalogues remain source-compatible; they are not silently converted into typed executable handlers because their complete argument and result schemas are not yet declared.

The v1 value model includes:

| Kind | Validation |
|---|---|
| `bool` | Only `0` and `1` |
| `i64` / `u64` | Exact tag and optional inclusive minimum/maximum |
| `f64` | Exact tag, finite value and optional inclusive bounds |
| `utf8` | Valid UTF-8 byte sequence and optional byte-length limit |
| `bytes` | Pointer/length consistency and optional byte-length limit |
| `handle` | Nonzero ID and optional expected handle kind |
| `void` | Return type only |

Values are tagged. No implicit numeric widening, string conversion, parsing, or other coercion is performed. Null is represented explicitly and accepted only by nullable schemas. Optional arguments must form a trailing suffix; required arguments cannot appear after an optional argument.

Argument and return contracts can include scalar bounds, maximum byte lengths and handle-kind constraints. The handler's return value is validated against the registered result schema before it is copied to the caller. A failed result validation leaves the caller's output unchanged.

## Registration and lookup

A registry is backed by caller-owned arrays and arenas:

- operation-entry slots;
- an open-addressed bucket index;
- a string arena for copied domain and operation names;
- an argument-schema arena for copied parameter descriptors.

Initialization requires a power-of-two bucket count at least twice the entry capacity. This keeps the maximum load factor at or below 50%. Registration checks the complete operation contract, key, schema, entry capacity and arena capacity before modifying the registry. Duplicate `(domain, name, ABI major)` keys are rejected. Different major versions can coexist; minor versions are negotiated by the invocation's minimum-minor requirement.

Lookup uses a deterministic 64-bit FNV-1a key hash followed by linear probing and exact key comparison. The hash is an index, not an authentication primitive. Registrations and handler definitions must come from trusted application code; hostile public lookup endpoints should impose their own request and work quotas.

There is no hidden heap allocation, global singleton, dynamic library loading or network access. The registry does not own handler code or handler contexts; they must remain alive for as long as the registry can invoke them. Registration copies key strings and argument schemas, so the caller may release or change the source buffers after successful registration.

Each operation accepts at most `REAPER_TYPED_MAX_ARGUMENTS` (32) parameters. UTF-8 and byte payloads are borrowed views: the input buffers must remain valid and unchanged for the duration of the synchronous handler call, and handlers must not retain those pointers unless they copy or otherwise take ownership through a separate contract. Returned UTF-8/byte views are also borrowed; their backing storage must remain valid for as long as the caller uses the returned value. The registry copies the tagged value structure, not the payload bytes.

## Invocation boundary

Invocation is deliberately ordered:

1. Resolve the exact domain, operation and ABI major.
2. Require the registered minor version to satisfy the caller's minimum.
3. Check that every required capability bit is present in the host-granted mask.
4. Validate argument count, exact types, nullability, UTF-8, numeric bounds, byte lengths and handle kinds.
5. Reject declaration-only entries with no handler.
6. Invoke the handler and validate its result.

No handler is called for a missing operation, ABI mismatch, denied capability, arity mismatch or invalid argument. Capability bits are only an input from the trusted host; Typed Registry does not grant privileges, authenticate a caller, issue OS handles, enforce a process sandbox, or make a privileged syscall.

## Lifecycle and concurrency

Registration is supported during construction. `reaper_typed_registry_seal` closes the registry to further writes. A sealed registry is intended for read-only use after the application publishes it with the platform's normal thread/process synchronization. The library contains no internal locks or atomics: callers must serialize initialization and registration, and must not read a registry concurrently with mutation. The current API has no delete, replace or compaction operation; rebuild a fresh registry and publish it as a new snapshot when a new generation is required.

The entry count uses `size_t`, and the index and arenas scale with caller-provided memory. There is no compile-time fixed registry cardinality. A single in-memory registry is still bounded by its allocated arrays, address space and platform limits. Very large logical registries should be partitioned into independent bounded shards or backed by a separately implemented persistent index; v1 does not claim that tens of billions of records can reside in RAM at once.

## Example

```c
#include "reaper/typed_registry.h"

static ReaperTypedStatus sum_i64(
    void *context,
    const ReaperTypedValue *arguments,
    size_t argument_count,
    ReaperTypedValue *result) {
    (void)context;
    if (argument_count != 2U) return REAPER_TYPED_ARITY_MISMATCH;
    result->kind = REAPER_TYPED_I64;
    result->as.i64 = arguments[0].as.i64 + arguments[1].as.i64;
    return REAPER_TYPED_OK;
}

/* The host supplies entry, bucket, string and schema buffers. */
```

The handler above is illustrative: production arithmetic handlers must also define their overflow policy. A registry contract does not make an unchecked handler safe.

## Build and tests

```sh
cmake -S . -B build -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The native typed-registry test executable covers registry initialization, copied key/schema ownership, duplicate rejection, optional arity, version negotiation, capability denial before callback, exact type checks, numeric ranges, finite floating-point values, UTF-8 validation, byte limits, handle-kind checks, nullable values, output validation, handler error propagation, declaration-only entries, transactional storage exhaustion and sealing.

The module is built with strict C17 warnings. The focused test suite is also run under AddressSanitizer and UndefinedBehaviorSanitizer during development.

## Explicit non-goals and remaining gates

- No source-level Reaper declaration grammar, type checker, IR lowering or bytecode integration is added by this library alone.
- No implicit registration of existing capability or System Runtime operations occurs. Each adoption must add reviewed argument/result schemas and handler tests.
- No records, enums, generics, nested arrays, trait objects or user-defined ADTs are exposed as built-in value kinds in v1.
- No lock-free concurrent mutation, persistence engine, distributed consensus, replication protocol or cross-process transport is claimed.
- No handler is considered implemented merely because its metadata is registered.

The next compiler gate is to map source-level typed declarations and effects into these contracts with `Span`-backed diagnostics and canonical IR, then add differential tests for reference-runtime and native dispatch. A DAK host adapter must independently derive the caller identity and granted capabilities from trusted kernel state.
