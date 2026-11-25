# DABI64 Desktop Host v1

**Status:** fixed-width request/response wire format and local validators implemented in Reaper. Kernel syscall entry, IPC transport, process authentication, desktop service implementations and hardware backends are not part of this milestone.

## Purpose

DABI64 Desktop Host v1 is the message boundary between a Reaper native client and a trusted desktop host. The System Runtime catalogue declares operations and required capabilities; DABI64 defines pointer-free request and response frames for a future DuckOS transport.

The wire header contains no native pointer, sender PID or caller-supplied capability mask. The receiver must derive sender identity from the current kernel execution context and resolve object handles against the sender's own handle table. A client cannot claim system identity or mint its own grant.

## Wire encoding

All multi-byte fields are little-endian. Version 1 targets the x86-64 DABI64 ABI. Reserved flags must be zero. Incompatible future layouts require a new ABI version.

### Request frame v1

The request header is exactly 40 bytes:

| Offset | Width | Field | Rule |
|---:|---:|---|---|
| 0 | 4 | struct_size | Exactly 40 |
| 4 | 2 | abi_version | Exactly 1 |
| 6 | 2 | operation | Registered Reaper System operation ID |
| 8 | 4 | flags | Zero in v1 |
| 12 | 4 | payload_size | 0–65,536 bytes |
| 16 | 8 | request_id | Non-zero correlation identifier |
| 24 | 8 | object_handle | Opaque host-issued handle; zero only where operation permits |
| 32 | 8 | sequence | Non-zero per-client sequence number |

Payload bytes immediately follow the header. Frame length must equal 40 + payload_size. Truncated frames, trailing bytes, unknown operations, unsupported versions, non-zero flags and oversized payloads are rejected.

### Response frame v1

The response header is exactly 32 bytes:

| Offset | Width | Field | Rule |
|---:|---:|---|---|
| 0 | 4 | struct_size | Exactly 32 |
| 4 | 2 | abi_version | Exactly 1 |
| 6 | 2 | status | Known DABI64 status |
| 8 | 4 | flags | Zero in v1 |
| 12 | 4 | payload_size | 0–65,536 bytes |
| 16 | 8 | request_id | Must match the completed request |
| 24 | 8 | object_handle | Opaque host-issued handle or zero |

Response payload bytes immediately follow the header and obey the same exact-size rule. The caller compares request_id with its pending request table; a structural validator cannot do this for it.

## Operation and authority model

The System Runtime catalogue defines seven desktop domains: window manager, display topology, focused input routing, session/profile, framebuffer compositor, GPU broker and native shell.

Each operation maps to a capability bit. This is only an admission precheck. The trusted host must additionally validate sender identity, object ownership, session state, quotas, focus, sequence freshness and operation-specific payloads. A grant does not authorize access to another process's window or buffer.

Administrative operations have distinct capability bits for display-mode changes, session unlock requests and GPU reset. Authentication and final policy decisions remain host-owned.

## Handle and payload rules

- Handles are opaque unsigned 64-bit values and are never interpreted as memory addresses.
- A zero handle is valid only where an operation contract allows create or discovery.
- Payload structs are separately versioned and use fixed-width integers, reserved fields and explicit bounds.
- Variable-length strings carry byte lengths and encoding; NUL termination is not assumed.
- The receiver copies or pins untrusted payload bytes before asynchronous use.
- Sequence freshness is tracked per authenticated endpoint by the kernel transport, not by trusting a client claim.

## Validation library

The Reaper C17 library exposes request validation, response validation and status-name lookup. Validators are side-effect-free and check header layout, version, known operations/statuses, non-zero identifiers, zero flags, payload ceiling and exact frame length.

They do not authenticate callers, validate handle ownership, deliver IPC, dispatch operations or grant capabilities.

## Ordered implementation gates

1. DuckOS syscall entry saves the x86-64 user register frame, validates user ranges and copies the request into kernel-owned memory.
2. IPC derives sender PID and capability grants from kernel-owned task state, then applies operation and per-object authorization.
3. Native desktop service owns the window registry, process/window lifecycle, display leases, focused input subscriptions and session transactions.
4. Software framebuffer compositor owns scanout and presentation; applications submit owned surfaces, never physical framebuffer addresses.
5. GPU broker adds device buffers, submissions and fences only after software composition is stable.
6. Shell service consumes launcher/catalogue and settings APIs without executing arbitrary manifest command strings.

The current DuckOS stage-1 kernel still halts after firmware/memory handoff. None of these kernel gates should be marked complete until source, tests and QEMU or hardware evidence exist.
