# DuckOS system services in Reaper

**Contract:** `ivan-vhs.duckos-system-services.v1`  
**Source language:** Reaper (`.rpr`)  
**Target:** DuckOS x86-64 first; other architectures use explicit target backends  
**Status:** contract integrated; executable system-service bindings are not yet implemented

## Scope and truth boundary

This specification integrates the requested operations 111–130 into the Reaper language and DuckOS architecture. It is the normative contract for the next implementation stages, not a claim that those functions already execute.

The current Reaper parser accepts the `craft`, `make`, `vary`, `change`, `yield` and `emit` language surface. The current native AOT backend accepts only a scalar subset and has no process, filesystem, device, NPU, container or hypervisor host-call ABI. Consequently, the C-like sample from the proposal is **not valid current Reaper source** and must not be checked in as a runnable `.rpr` example.

No Rust or C++ implementation is introduced by this integration. Existing Python reference-runtime and C17 compiler components are left unchanged. The planned system source surface remains Reaper; kernel and driver services are external DuckOS providers behind a versioned ABI.

## Architecture

The integration has four explicit boundaries:

1. **Reaper source contract.** A typed Reaper declaration names the operation, input/output types, error set, target and required effects. System operations are never implicit built-ins.
2. **Compiler and IR.** Type checking validates widths, ownership, lifetimes, effect grants and target compatibility. A versioned system-service IR operation lowers through a dedicated service-call boundary. DABI64 v1 is the user-entry/value/call-frame ABI; it is not itself a syscall dispatcher or the system-service ABI. The service contract in this document is versioned separately and will be connected only through an implemented DuckOS provider. An unsupported operation is a compile-time diagnostic, never a fallback to a host shell command.
3. **DuckOS ABI provider.** The kernel, service manager, filesystem, device manager, accelerator driver or hypervisor owns privileged work. User code receives bounded handles and explicit results, not raw kernel pointers.
4. **Capability policy.** The manifest requests named capabilities. The kernel/service manager grants the minimum set for the process. Revocation, audit identity and resource quotas are part of the provider contract.

A future typed declaration may look like this:

```reaper
craft sys_become_daemon(config: DaemonConfig) -> Result<DaemonHandle, SysError>
    effect process.control, process.fd
{
    // Reaper compiler intrinsic; lowered only for a DuckOS target.
    yield syscore.daemonize(config)
}
```

This is a **target-language proposal**, not syntax accepted by the current parser. It becomes supported only after grammar, type/effect rules, IR lowering, diagnostics and conformance fixtures are implemented together.

## Operation contracts

All twenty operations are currently **Planned** at the executable Reaper ABI level. The table specifies required behavior and dependencies; it does not register fake handlers.

### SysCore — process, service and device lifecycle

| ID | Operation | Required contract |
|---:|---|---|
| 111 | `sys_become_daemon` | Prefer supervisor-owned service launch. If detach is explicitly requested, create a new session, verify every descriptor operation, establish stdin/stdout/stderr deterministically, and return a structured error. No assumption that three `open` calls always yield descriptors 0, 1 and 2. |
| 112 | `svc_register` | Register an owned, versioned service descriptor. Validate name, callbacks, ABI version and lifetime; reject duplicate IDs; synchronize updates; unregister only after in-flight callbacks drain. |
| 113 | `cron_add_job` | Parse and validate the schedule before allocation; use a monotonic deadline derived from calendar/time-zone evaluation; define missed-run, daylight-saving, cancellation and duplicate-job behavior; return a stable job ID or error. |
| 114 | `log_emit` | Accept a bounded structured record with timestamp source, process identity, severity and payload length. Return an explicit full/closed/invalid status when the ring buffer cannot accept the record; never publish partially initialized packets. |
| 115 | `init_activate_unit` | Resolve the dependency graph, detect cycles, topologically activate dependencies, propagate failure, enforce start deadlines and make activation idempotent. A dependent unit cannot become active before all required dependencies are active. |
| 116 | `sys_shutdown_graceful` | Request a supervisor-managed staged shutdown: stop admission, notify services, wait with bounded deadlines, sync filesystems, unmount only after users release them, then request power-off. Record failures and support a defined forced-shutdown policy. |
| 117 | `sys_enter_emergency` | Enter a kernel-defined emergency state with a reason code and restricted diagnostics. Do not disable interrupts and then try to spawn an interactive shell. Console recovery is a separately authorized transition. |
| 118 | `udev_process_event` | Validate event version, device identity and path; serialize add/remove transitions; bind drivers through the device manager; create/remove nodes transactionally; reject stale or duplicate events. |
| 119 | `fw_load` | Read a bounded firmware object, verify its signature and device/firmware compatibility, acquire an authorized device handle, stream or map through the driver, check transfer completion and release all resources on every path. |
| 120 | `acpi_bootstrap` | Validate RSDP revision, checksums, lengths and address ranges; select XSDT/RSDT safely; validate every table before parsing; follow FADT references to DSDT; bound AML parsing and reject malformed tables without unchecked dereferences. |

### NeuroLink — accelerator and inference

| ID | Operation | Required contract |
|---:|---|---|
| 121 | `npu_ctx_create` | Discover an accelerator through the device registry, verify requested features and memory limits, acquire a scoped device capability, allocate DMA buffers through the driver and unwind partial initialization on error. No fixed 2 GiB allocation. |
| 122 | `tensor_mul` | Validate tensor rank, shape, dtype, strides, alignment and overflow-safe byte sizes; validate context/device ownership; synchronize DMA according to the driver contract; submit a bounded command and wait on a fence with timeout/cancellation. |
| 123 | `ai_run_inference` | Validate graph and operator versions before execution; validate input/output shape and buffer capacity; use an explicit allocator/arena; propagate operator errors; bound work and temporary memory; release intermediates deterministically. |
| 124 | `model_load_onnx` | Parse ONNX under file, nesting, tensor-count and allocation limits; validate operators/opsets and tensor metadata; retain backing storage for zero-copy weights or copy them into model-owned memory; reject external-data paths outside the model root. |
| 125 | `ai_secure_infer` | Bind a named, reviewed homomorphic-encryption scheme and parameter set; validate ciphertext/context compatibility and evaluation-key requirements; return encrypted output and explicit noise/budget status. A public key alone is not a generic evaluation key. |

### VirtHost — isolation, virtualization and build tools

| ID | Operation | Required contract |
|---:|---|---|
| 126 | `container_spawn` | Use DuckOS process, namespace, mount, network and resource-control APIs—not Linux `clone` flags as an assumed ABI. Validate image metadata and root filesystem, establish isolation before untrusted execution, and supervise/reap the container process tree. |
| 127 | `kvm_vm_create` | Expose a target-neutral hypervisor interface. Linux KVM is an optional host adapter only; DuckOS uses its own hypervisor backend. Validate CPU virtualization support, RAM budget, guest memory layout, vCPU lifecycle and disk/image ownership. |
| 128 | `flatpak_install` | Treat Flatpak as an optional Linux compatibility/import format, not DuckOS's native package format. Verify repository trust and signatures, validate bundle metadata, extract transactionally and install under a sandbox policy. |
| 129 | `pkg_install` | Resolve a package through DuckOS's native package service, verify repository metadata, package signature, dependencies and version constraints, then perform an atomic install/rollback. Never concatenate a package name into a shell command or invoke apt/dnf as the DuckOS package manager. |
| 130 | `build_cross` | Resolve an explicit target triple, ABI, CPU feature set and pinned toolchain manifest; validate source/output paths; pass arguments without a shell; isolate build environment; record reproducible inputs and artifacts; return structured diagnostics and exit status. |

## Shared ABI rules

- **Versioning:** the DABI64 v1 calling/value contract and this system-service contract have separate version identities. Every service request carries service ABI major/minor and structure size. Unknown major versions fail closed; additive minor extensions are explicitly negotiated. Do not overload DABI64 register conventions with undocumented syscall numbers.
- **Types:** fixed-width integers, checked size arithmetic, explicit byte order and alignment. Pointers do not cross privilege boundaries; use typed handles and bounded buffers.
- **Errors:** every fallible operation returns `Result<T, SysError>`; partial success and cleanup failures are represented explicitly.
- **Ownership:** handles, mappings, DMA buffers, fences, registrations and model storage have a single documented owner and deterministic release. No borrowed pointer may outlive its provider.
- **Concurrency:** callbacks and ring buffers specify ordering, reentrancy and cancellation. IRQ context cannot allocate, block, parse or invoke a general service callback.
- **Security:** deny by default, least privilege, signature verification for executable/firmware artifacts, bounded parsing, audit events and resource quotas.
- **Portability:** no Linux syscall numbers, Linux-only flags, KVM descriptors, apt/dnf commands or POSIX daemon assumptions appear in the DuckOS ABI. Host adapters may implement compatible behavior behind separate contracts.
- **Failure:** initialization is transactional; on error, release resources in reverse acquisition order. Timeouts, queue saturation and device removal are normal typed outcomes.

## Implementation gates

| Gate | Scope | Exit evidence |
|---|---|---|
| S0 — language boundary | Typed system declarations, effects, handle/result types, system-call IR and source-located diagnostics | Grammar and type/effect fixtures; compiler rejects an ungranted effect and unsupported target |
| S1 — SysCore process | Service registry, process handles, scheduler hooks, logging, unit graph and shutdown state machine | DuckOS provider plus lifecycle, race, cycle, timeout and fault-injection tests |
| S2 — devices | Hotplug, firmware verification, ACPI table validation and driver capability grants | Emulator/device-provider tests, malformed-table corpus and signature rejection tests |
| S3 — NeuroLink | Accelerator discovery, DMA lifecycle, tensor metadata, graph execution and ONNX loading | Fake NPU provider, shape/overflow tests, timeout tests and model-lifetime tests |
| S4 — VirtHost | Process isolation, hypervisor provider, package service and cross-toolchain orchestration | Isolation tests, privilege-boundary tests, package rollback and reproducible-build checks |

No gate is complete because its API is named. Each gate requires the Reaper front end, native lowering, DuckOS provider and tests to agree on the same versioned contract.

## Known implementation boundary

This integration adds the specification and machine-readable inventory only. DuckOS DABI64 v1 is being developed as a call-frame/value ABI, while the DuckOS kernel syscall dispatcher and service providers are not yet present on the current mainline; see the separate [DuckOS DABI64 draft](https://github.com/Ivan-VHS/DuckOS/pull/14). Reaper's native DuckOS compiler work is also tracked separately and is not yet a general system-call frontend; see [Reaper native compiler draft](https://github.com/Ivan-VHS/Reaper/pull/225). Neither draft is treated as proof of an implemented OS service. This integration does not add runtime stubs, pretend syscalls, unsafe FFI shortcuts, Linux compatibility shims or non-compiling `.rpr` examples. The next code change must begin at S0 and add one vertical slice end to end before marking any operation Partial or Delivered.
