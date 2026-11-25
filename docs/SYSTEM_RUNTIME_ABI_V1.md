# Reaper System Runtime ABI v1

**Status:** native C17 host-dispatch boundary and bounded Reaper source bridge implemented; per-platform syscall adapters and native compiler lowering remain separate gates.  
**Scope:** process and thread lifecycle, synchronization, filesystem, clocks, networking and cryptographic services.  
**Compatibility:** additive ABI; the existing Reaper FFI v1 symbols and the 18-module capability suite remain unchanged.

## Why this boundary exists

Reaper needs a stable way to ask a host operating system for services without pretending that a hosted program can safely perform kernel work by itself. The system ABI is therefore a capability-gated dispatch boundary. A trusted adapter may be supplied by DuckOS, another host OS, a simulator or a reviewed runtime. Reaper does not issue raw syscalls, map physical memory, load drivers, or elevate privilege through this API.

The ABI is implemented in include/reaper/system.h and src/system.c as the standalone C17 reaper_system library. It does not depend on the reference Python runtime or the partial scalar AOT frontend.

## Expansion measure

The existing native capability suite registers 18 modules with 6 operations each (108 registrations). System ABI v1 adds 7 domains with 6 operation IDs each (42 additional contracts). The declared operation surface therefore grows from 108 to 150 entries, a 38.9% increase. This is a registry/API-surface measurement, not a claim that every host service or language construct is implemented on every platform.

## Operation catalogue

| Domain | Operation IDs | Required capability |
|---|---|---|
| Process | process.spawn, process.wait, process.signal, process.exit, process.current_id, process.parent_id | PROCESS_CONTROL or PROCESS_INSPECT per operation |
| Thread | thread.spawn, thread.join, thread.detach, thread.yield, thread.sleep, thread.set_priority | THREAD_CONTROL |
| Synchronization | sync.mutex_create, sync.mutex_lock, sync.mutex_unlock, sync.semaphore_post, sync.semaphore_wait, sync.event_signal | SYNC |
| Filesystem | fs.open, fs.read, fs.write, fs.seek, fs.stat, fs.close | FS_HANDLE, FS_READ or FS_WRITE per operation |
| Clock and timers | clock.monotonic_ns, clock.realtime_ns, timer.create, timer.wait, clock.sleep_until, clock.deadline_after | CLOCK |
| Networking | net.socket_open, net.connect, net.send, net.receive, net.shutdown, net.resolve | NETWORK |
| Cryptography | crypto.random_fill, crypto.sha256, crypto.hmac_sha256, crypto.constant_time_equal, crypto.zeroize, crypto.key_import | CRYPTO |

reaper_system_operation_count, reaper_system_operation_at and reaper_system_operation_find expose the stable catalogue to native tools and adapters.

## Host contract

A ReaperSystemHost carries:

- abi_version and struct_size for forward-compatible validation;
- an explicit capability bitmask granted by the host;
- an opaque host context;
- one synchronous dispatch callback.

reaper_system_invoke validates the host ABI, operation ID, required capability, pointer/length pairs and one MiB input/output ceilings before calling the adapter. A missing grant is rejected before dispatch. The output length is reset on every failure. If the adapter reports more output than its declared capacity, Reaper returns host-contract-violation.

The adapter is trusted platform code. It must validate the operation-specific payload, validate all handles and path/name values, enforce cancellation and timeouts where relevant, and never retain the input/output pointers after the callback returns. Operation IDs are stable; payload layouts belong to a separately versioned host/platform contract and must not be guessed from an operation name.

## Effects and least authority

| Capability | Meaning |
|---|---|
| PROCESS_INSPECT | Inspect process identity and wait for an authorized child |
| PROCESS_CONTROL | Spawn, signal or terminate only processes in the adapter's permitted scope |
| THREAD_CONTROL | Create, join, detach or schedule threads within host policy |
| SYNC | Create and operate synchronization objects owned by the calling runtime |
| FS_HANDLE | Open, seek, inspect or close adapter-approved file handles |
| FS_READ | Read bytes from an already authorized file handle |
| FS_WRITE | Write bytes to an already authorized file handle |
| CLOCK | Read clocks and wait on adapter-managed timers/deadlines |
| NETWORK | Resolve names and open/use network endpoints allowed by host policy |
| CRYPTO | Use host entropy and cryptographic services |

A host should grant the smallest possible mask. A zero mask is valid. There is no implicit grant, global fallback, shell execution, environment-based library search or automatic privilege escalation.

## Safety rules

1. Process creation receives structured argument data from the platform adapter; it must not turn a string into an implicit shell command. process.exit must be scoped to the Reaper task/process, never the host desktop or supervisor.
2. Filesystem adapters should expose directory-rooted or handle-relative operations. They must reject path traversal, symlink escapes and access outside the granted root.
3. File handles, process IDs, thread IDs, sockets, mutexes and timers are opaque host-owned values. Adapters must reject stale, forged, cross-process or wrong-kind handles.
4. Network access is denied unless NETWORK is granted. The adapter applies endpoint policy, bounded DNS, connection and I/O timeouts, and maximum message sizes.
5. crypto.random_fill must use a cryptographically secure host source. It must fail closed; it must never silently substitute a time-seeded PRNG.
6. Key material must not be copied into logs or diagnostics. Adapters define key lifetime and zeroization guarantees. A successful crypto.zeroize is a host contract, not a guarantee made by ordinary C memset.
7. The system ABI does not grant MMIO, DMA, IRQ, port I/O, firmware flashing or driver installation. Those remain separate hardware/driver capabilities and trusted platform operations.
8. Callbacks are synchronous and must not retain caller-owned buffers. Long-running operations need adapter-defined cancellation/deadline payloads and bounded completion semantics.

## Language and compiler boundary

This release provides the native host ABI, operation catalogue and a bounded bridge callable from interpreted .rpr programs through the existing opt-in FFI. It does not claim that the .rpr parser, reference runtime or scalar AOT compiler can type-check or lower all 42 operations directly. Source-level effect, ownership, handle-lifetime and typed payload bindings remain compiler work. The bridge is not a DuckOS syscall provider; it only forwards requests to a trusted host adapter.

The intended language contract is:

- effects are explicit in function signatures and checked against manifest grants;
- OS handles are opaque, typed, non-copyable resources with deterministic close/drop;
- filesystem and network operations return explicit Result values;
- blocking calls declare deadlines/cancellation behavior;
- unsafe is local, explicit and cannot manufacture a host capability;
- the same operation IDs and effect names are shared by hosted, simulator and future DuckOS targets.

## Build and verification

    cmake -S . -B build -DREAPER_BUILD_TESTS=ON
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

The native-system-abi test covers catalogue cardinality and lookup, ABI/version/size checks, unknown capability rejection, denial before host dispatch, pointer/length validation, one MiB bounds, successful bounded dispatch, host failure and over-reported output lengths. Tests use a fake adapter; they do not invoke real processes, open files, access networks or manipulate devices.

## Adoption gates

- DuckOS: implement a policy-enforcing adapter over reviewed kernel services; keep process, filesystem and network rights off by default; preserve x86-64 Intel/AMD as the primary target and retain Elbrus as a separate supported backend.
- Pytyliki: consume only explicitly granted host services and keep its processor/hardware evidence APIs read-only; preserve the existing pytyliki.c-abi.v1 contract.
- OPlague: use only read-only filesystem/clock/crypto capabilities for package evidence workflows unless a separately reviewed capability is approved; never use this ABI to install, remove, enable, disable or flash drivers.

Each adopter must add its own adapter tests and cross-repository contract checks before describing an operation as available on that platform.


## Reaper source binding bridge

The shared `reaper_system_bridge` library exposes a narrow C surface that the current Reaper reference runtime can call through its existing explicit native FFI:

- `reaper_system_host_attach` copies a validated host descriptor into thread-local storage;
- `reaper_system_host_detach` removes the provider from the current thread;
- `reaper_system_call_json` resolves a registered operation name and forwards a bounded UTF-8 JSON request to the host dispatcher;
- `reaper_system_last_status` and `reaper_system_last_error` expose the result of the most recent bridge call on the current thread.

The bridge uses a 64 KiB request/response limit. Responses must be non-empty and contain no embedded NUL bytes. The provider is responsible for validating the operation-specific JSON schema, identifiers, handles, paths, endpoint policy and all other payload semantics. The bridge does not infer a schema from an operation name.

### Host attachment lifecycle

A trusted OS embedder must attach a host before running an .rpr program on each execution thread. Attachment is not inherited by newly created threads. The bridge copies the `ReaperSystemHost` descriptor, but the host-owned context and any state it references must remain valid until that thread detaches. Re-attaching on an already attached thread is rejected. The OS embedder must detach before destroying the provider context.

No host is attached by default. Calls without an attachment fail with `access-denied`. The bridge does not search for a provider, load a provider automatically, or grant capabilities. The embedder controls the capability mask and should begin with the minimum rights needed for the program.

### .rpr example

See [examples/system_runtime.rpr](../examples/system_runtime.rpr). It uses the existing `ffi_open` and `ffi_bind` functions, so it must be run with `--allow-native-ffi` and an explicit absolute library path. Loading a native library executes trusted native code; do not load an untrusted bridge.

The current scalar AOT compiler deliberately rejects FFI and does not lower this example to native code. This is an interpreted reference-runtime binding, not native compiler or DABI64 parity.

### Verification and limits

`tests/test_system_bridge.c` uses a fake host and verifies attachment, missing-capability denial before dispatch, unknown operation rejection, JSON forwarding, per-thread result handling, empty/embedded-NUL/oversized response rejection and the 64 KiB request bound. It does not launch a process, open a real file, create a socket or access a device.

The next platform milestone is a reviewed DuckOS host provider that translates these stable operation IDs into approved kernel services. Until that provider and its integration tests exist, process, filesystem, networking and other operations are available as contracts and dispatch points only—not as working DuckOS services.
