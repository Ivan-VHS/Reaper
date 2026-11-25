# Reaper ↔ DuckOS system-service contracts

**Contract:** `reaper.duckos-system-services/v1`  
**Status:** contract-only; all 20 entries are Planned  
**Ownership:** Reaper defines the language/host-call boundary; DuckOS implements the OS services and privileged adapters.

## Purpose

This contract translates the proposed operations 111–130 into a versioned boundary between Reaper programs and DuckOS. It is not a claim that the current Reaper parser, reference runtime or native C17 track can execute these operations.

The machine-readable registry is [`language/duckos_system_services.v1.json`](../language/duckos_system_services.v1.json). The existing `language/functions_666.json` MOST registry is deliberately unchanged: its `MOST-FN-111` through `MOST-FN-130` identifiers already have separate meanings.

## Ownership and execution layers

| Layer | Responsibility | Examples |
|---|---|---|
| Reaper language and compiler | Typed operation signatures, effects, capability requests, ABI validation and source diagnostics | Host-call declarations; target/effect checking |
| DuckOS kernel and HAL | Privileged state transitions, address-space and DMA primitives, interrupt control, ACPI table discovery, isolation primitives | ACPI, device mappings, power-state handoff |
| DuckOS system services | User-mode lifecycle orchestration, policy, persistence, scheduling and audit | Init, logging, device events, firmware broker, package transactions |
| DuckOS compute runtime | Model loading, tensor execution, NPU sessions and inference budgets | ONNX loader, NPU dispatch, encrypted inference |
| Build and compatibility tools | Reproducible target builds and optional format adapters | Cross-compilation, Flatpak import bridge |

A user-mode service must not disable interrupts, map arbitrary physical memory or perform privileged device operations directly. A kernel driver must not become a general-purpose package manager, container supervisor or model runtime. These boundaries are part of the API, not implementation details.

## Contract map

| Proposed operation | Canonical host-call symbol | Owning layer |
|---|---|---|
| 111. Daemon creation | `service.detach` | DuckOS service manager |
| 112. Service lifecycle hooks | `service.register_lifecycle` | DuckOS service manager |
| 113. Cron scheduler | `scheduler.register_calendar_job` | DuckOS scheduler |
| 114. Log daemon | `log.append` | DuckOS logging service |
| 115. Init system | `service.start_unit` | DuckOS init/service manager |
| 116. Graceful shutdown | `system.request_shutdown` | DuckOS power coordinator |
| 117. Emergency mode | `system.enter_recovery` | DuckOS recovery coordinator |
| 118. Device events | `device.apply_event` | DuckOS device manager |
| 119. Firmware loading | `firmware.stage_image` | Firmware broker and device driver |
| 120. ACPI parsing | `acpi.enumerate_tables` | DuckOS boot/HAL subsystem |
| 121. NPU session | `npu.open_session` | NPU driver and compute runtime |
| 122. Tensor multiplication | `tensor.matmul` | Tensor runtime/NPU backend |
| 123. AI inference | `model.infer` | Inference runtime |
| 124. ONNX model loading | `model.load_onnx` | Model loader |
| 125. Encrypted inference | `model.infer_encrypted` | Privacy compute runtime |
| 126. Container creation | `container.create` | DuckOS container service |
| 127. Virtual machine creation | `vm.create` | Hypervisor service/backend |
| 128. Flatpak compatibility | `package.import_flatpak` | Optional compatibility adapter |
| 129. Package installation | `package.install` | DuckOS package manager |
| 130. Cross-compilation | `build.cross_compile` | Reaper/DuckOS build orchestrator |

The full contract IDs, effects, capabilities, safety invariants and acceptance criteria live in the JSON registry. All entries currently have `status: planned`.

## Required host-call shape

Every operation must be described before it is exposed to Reaper code:

1. A stable, versioned symbol and typed argument/result layout.
2. An explicit effect set, such as `process`, `clock`, `log`, `device`, `dma`, `crypto`, `power` or `build`.
3. One or more capabilities scoped to the resource and action. Possessing a function name must not grant the capability.
4. Defined ownership and lifetime rules for handles, buffers, mappings, callbacks and sessions.
5. A closed error model covering denial, invalid state, unsupported target, resource exhaustion, timeout, device removal and partial completion where applicable.
6. Target and ABI identity, including architecture, calling convention, layout and supported feature set.
7. Deterministic tests for success, denial, malformed inputs, limits and teardown.

The host kernel or service decides whether to grant each capability. Reaper code cannot self-elevate by importing a module or invoking a syscall name. Ordinary code receives typed handles; raw pointers and privileged instructions remain inside audited, target-specific adapters.

## Corrections required before implementing the original snippets

- **Daemonization:** do not expose a generic `fork/setsid/close` recipe. DuckOS service creation belongs to its service manager, which controls inherited handles and restart policy.
- **Lifecycle and init:** validate the complete dependency graph, reject cycles, make state transitions idempotent and avoid invoking callbacks under registry locks.
- **Scheduling:** calendar time and monotonic deadlines are different clock domains. Timezone changes and daylight-saving transitions need explicit rules.
- **Logging:** bounded queues need a documented drop/overwrite policy, loss accounting and a non-blocking producer path where required.
- **Shutdown and recovery:** use state machines and deadlines. A fixed sleep followed by a global `SIGKILL` is not a shutdown protocol. Disabling interrupts is kernel-only and must never be performed by a user-mode recovery process.
- **Device and firmware handling:** hotplug events are untrusted and repeatable. Device identity, driver signatures, firmware digest, board revision, authorization and rollback must be verified before mutation.
- **ACPI:** validate all firmware-supplied lengths, checksums, alignment and address ranges. Table discovery is distinct from AML parsing and AML interpretation.
- **NPU and tensors:** discover devices instead of assuming `/dev/npu0`; do not hard-code a 2 GiB allocation. Validate shapes, dtypes, layout, overflow, DMA ownership, cache synchronization, fences and timeouts.
- **Inference and ONNX:** reject unsupported graph operators rather than silently skipping them. Bound protobuf parsing, graph size, external tensor paths, scratch memory and execution time.
- **Encrypted inference:** specify the cryptographic scheme, parameters, supported operations and threat model. A generic `he_matmul` call is not a privacy guarantee.
- **Containers and VMs:** Linux `clone`, `chroot` and KVM are backend-specific mechanisms, not portable Reaper primitives. DuckOS requires its own versioned isolation and hypervisor adapters.
- **Packages:** Flatpak is an optional compatibility import, not the DuckOS-native package format. Native installation requires trusted signatures, dependency resolution, a transaction journal and rollback; never fall back to arbitrary `apt`/`dnf` commands.
- **Cross-compilation:** never concatenate untrusted strings into shell commands. Use an allowlisted toolchain profile and an argument vector, then record the target ABI, toolchain digest and artifact hashes.

## Integration sequence

1. Freeze this host-call manifest and review the ABI, effects, capability names and ownership rules.
2. Implement DuckOS kernel/HAL adapters for the privileged primitives; keep orchestration in user-mode services.
3. Add Reaper compiler diagnostics for unknown effects, missing capabilities, wrong target, invalid ABI layout and unsafe handle use.
4. Add a host-call dispatch table with version negotiation and fail-closed behavior. Do not add built-ins to the reference runtime until semantics and quotas are specified.
5. Implement one vertical slice at a time, beginning with read-only discovery and bounded logging before device mutation, firmware updates, power control or hypervisor operations.
6. Add target-specific tests and integration evidence. Only then change a contract from Planned to Experimental or Delivered.

## Acceptance rule

A registry row or design document is not an implementation. No operation in this file is callable from current Reaper merely because its symbol is listed. Mark an operation Delivered only when the owning DuckOS source, Reaper host-call contract, negative tests, target qualification and CI evidence are all linked to the same reviewed revision.
