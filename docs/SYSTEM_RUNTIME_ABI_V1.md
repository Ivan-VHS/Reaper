# Reaper System Runtime ABI v1

**Status:** native C17 host-dispatch boundary implemented; DABI64 Desktop Host request/response framing and validators are added as a separate library. Platform syscall adapters, privileged kernel dispatch and Reaper source-level bindings remain separate gates.
**Scope:** process/thread lifecycle, synchronization, filesystem, clock, networking, cryptography and desktop services.
**Compatibility:** additive operation catalogue. Existing Reaper FFI v1 symbols and capability-suite registrations are unchanged.

## Purpose

Reaper exposes a capability-gated host dispatch boundary. A trusted adapter may be supplied by DAK, another host OS, a simulator or a reviewed runtime. Reaper does not issue raw syscalls, map physical memory, load drivers or elevate privilege through this API. The C17 implementation lives in include/reaper/system.h and src/system.c.

## Operation catalogue

The native capability suite has 108 registrations. System Runtime API v1 now declares 84 host operations in 14 domains. The combined declared surface is 192 registry entries. This is an API-surface count, not evidence that kernel services, drivers or source bindings exist for every operation.

| Domain | Operations | Capability |
|---|---|---|
| Process | spawn, wait, signal, exit, current_id, parent_id | PROCESS_CONTROL / PROCESS_INSPECT |
| Thread | spawn, join, detach, yield, sleep, set_priority | THREAD_CONTROL |
| Synchronization | mutex_create, mutex_lock, mutex_unlock, semaphore_post, semaphore_wait, event_signal | SYNC |
| Filesystem | open, read, write, seek, stat, close | FS_HANDLE / FS_READ / FS_WRITE |
| Clock | monotonic_ns, realtime_ns, timer_create, timer_wait, sleep_until, deadline_after | CLOCK |
| Network | socket_open, connect, send, receive, shutdown, resolve | NETWORK |
| Cryptography | random_fill, sha256, hmac_sha256, constant_time_equal, zeroize, key_import | CRYPTO |
| Window manager | create, destroy, set_geometry, set_state, focus, query | DESKTOP_WINDOW |
| Display | enumerate, query, set_mode, set_scale, set_primary, subscribe | DESKTOP_DISPLAY / DESKTOP_DISPLAY_ADMIN |
| Input | subscribe, unsubscribe, next_event, pointer_capture, release_capture, query_state | DESKTOP_INPUT |
| Session | profile_read, profile_write, snapshot_save, snapshot_restore, lock, request_unlock | DESKTOP_SESSION / DESKTOP_SESSION_ADMIN |
| Framebuffer compositor | surface_create, surface_destroy, surface_attach_buffer, surface_detach_buffer, submit_frame, frame_state | DESKTOP_COMPOSITOR |
| GPU | device_query, buffer_allocate, buffer_release, submit, fence_wait, reset | DESKTOP_GPU / DESKTOP_GPU_ADMIN |
| Native shell | launcher_query, launcher_open, menu_open, notification_post, notification_clear, settings_query | DESKTOP_SHELL |

Existing operation IDs remain stable. Desktop operations use additive ID ranges. The exported catalogue functions enumerate all 84 operations.

## Host contract and authority

ReaperSystemHost contains ABI version, structure size, an explicit host-granted capability mask, an opaque context and a dispatch callback. Invocation checks the ABI, known operation, required capability, pointer/length consistency and one MiB I/O ceilings before dispatch. The output length is reset on failure, and over-reported output sizes are rejected.

Desktop capabilities are split by trust boundary. Display topology reads do not imply permission to change display mode. Ordinary GPU operations do not imply GPU reset. Session profile access does not authenticate a user or unlock a session. Input grants are scoped to events routed to an authorized focused surface; they do not grant global input capture. All window, surface, display and GPU handles are host-issued and must be validated against the calling process.

A host should grant the smallest possible mask. Zero grants are valid. There is no implicit grant, global fallback, shell execution, environment-based library search or automatic privilege escalation.

## DABI64 Desktop wire framing

DABI64 Desktop Host v1 has a fixed 40-byte request header and 32-byte response header. Multi-byte fields are little-endian; payloads are limited to 65,536 bytes and must exactly match the frame length. The wire header contains no native pointer, sender PID or caller-supplied capability mask. The kernel transport must derive identity from trusted task state. Structural validation is not authentication, IPC delivery, authorization or syscall entry. See DABI64_DESKTOP_HOST_V1.md.

## Safety rules

1. Process creation uses structured arguments, never implicit shell text; exit is scoped to the caller.
2. Filesystem adapters use authorized roots or handles and reject path traversal and symlink escapes.
3. Handles are opaque, owned by the host and rejected when stale, forged, cross-process or wrong-kind.
4. Network access is denied unless explicitly granted and bounded by endpoint policy and timeouts.
5. Cryptographic entropy must come from a secure host source and fail closed; secrets never enter logs.
6. Input is routed only to focused authorized surfaces. Applications never receive unrestricted physical framebuffer or GPU register access.
7. Framebuffer/GPU adapters validate dimensions, pitch, format, ownership, quotas and fences.
8. Session restore and unlock remain subject to identity, authentication and crash-safe recovery.
9. Async adapters copy or pin request data before use and must not retain caller buffers after a synchronous callback.

## Language and compiler boundary

This release provides the host operation catalogue and DABI64 desktop message validators. It does not claim the current parser, reference runtime or scalar AOT compiler can type-check or lower all operations directly. Source-level effect, ownership, handle-lifetime and typed payload bindings remain a separate compiler gate.

## Build and verification

    cmake -S . -B build -DREAPER_BUILD_TESTS=ON
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Native System Runtime tests cover catalogue lookup, ABI/version/size checks, capability denial before dispatch, pointer/length validation, buffer limits and host contract violations. DABI64 tests cover fixed header sizes and offsets, version/operation checks, request and sequence identifiers, reserved flags, payload bounds, exact frame length and response validation. The tests use local fake data; they do not invoke a kernel, create windows, read devices, persist sessions, render pixels or submit GPU work.

## Adoption gates

- DAK: implement IPC and policy-enforcing adapters over real kernel services; derive sender identity from kernel task state; keep display administration, global input, session administration and GPU reset off by default.
- Pytyliki and OPlague: request only window/shell capabilities needed by their native utility panels; keep hardware inventory, driver and package evidence read-only.
- VentuSample: use window, compositor-surface and focused-input services only; audio-device access is separate.

Each adopter needs adapter tests and cross-repository checks before describing a service as available on its platform.
