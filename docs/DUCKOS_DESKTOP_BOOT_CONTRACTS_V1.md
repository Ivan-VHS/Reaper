# DuckOS desktop and boot policy contracts v1

**Status:** contract design; Reaper source modules and exports are not yet delivered.  
**Canonical system architecture:** [DuckOS native desktop and DuckBoot architecture v1](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/DESKTOP_AND_DUCKBOOT_ARCHITECTURE_V1.md).  
**Language owner:** Reaper owns deterministic policy, validation and service orchestration. DuckOS owns native privileged mechanisms and their enforcement.

## 1. Boundary

Reaper must not pretend to be a display server, firmware loader, kernel, device driver or cryptographic verifier. It supplies deterministic policy decisions over bounded descriptors. DuckOS native code independently validates all memory, handles, capabilities, firmware responses, signature evidence and privileged operations.

A successful Reaper contract result means only that the supplied descriptor satisfies the declared policy. It does not authorize a syscall, write to an EFI System Partition, modify firmware NVRAM, access a GPU, observe global input or capture a screen.

The current Reaper repository contains a Python reference runtime and a partial native C17 compiler track. The native compiler is not feature-equivalent to the reference runtime and is not yet a freestanding DuckOS service compiler. Therefore this document defines source-level ownership and acceptance contracts; it does not add guessed Reaper syntax or claim native integration.

## 2. Contract namespace

The following namespaces are reserved for the DuckOS platform integration.

| Namespace | Owned decisions | Must not perform |
|---|---|---|
| duckos.desktop.session | Profile validation, dependency resolution, switch plan and rollback decision | Spawn a process, kill an app or write arbitrary configuration |
| duckos.desktop.output | Output descriptor validation, geometry, scale and hotplug transition | Map MMIO or submit GPU commands |
| duckos.desktop.surface | Buffer dimensions, quotas, configure serials and lifecycle admission | Read arbitrary client memory or map pages |
| duckos.desktop.window | Geometry constraints, focus eligibility, state transitions and tiling decisions | Inject input or grant capture permissions |
| duckos.desktop.input | Event sequence validation and focused-client route decision | Read raw device registers or broadcast keystrokes |
| duckos.desktop.portal | Consent scope, lifetime, target identity and revocation policy | Capture screen, enumerate files or read clipboard itself |
| duckos.desktop.accessibility | Motion, contrast, scale, keyboard and assistive-profile validation | Claim screen-reader support without a native provider |
| duckos.boot.entry | Entry descriptor and cross-field validation | Read disk sectors or firmware variables |
| duckos.boot.adapter | Adapter capability negotiation and typed unsupported results | Install a loader or silently emulate unsupported features |
| duckos.boot.plan | Deterministic dry-run diff and affected-resource inventory | Perform writes or reboot |
| duckos.boot.trust | Trust-policy decision from native verification evidence | Verify signatures using a caller-supplied boolean |
| duckos.boot.recovery | Attempt budget, known-good target and rollback transition | Rewrite boot metadata or remove foreign files |

These are proposed policy modules. Until a module exists in Reaper source with tests and CI, its status is specified, not implemented.

## 3. Shared data invariants

All contracts use versioned records and fixed-width integer fields where data crosses a native boundary.

Required invariants:

- reject unknown mandatory versions and unsupported enum values;
- reject duplicate IDs, malformed identifiers and invalid state transitions;
- use half-open ranges and checked arithmetic for all offsets and lengths;
- enforce explicit maxima for arrays, strings, buffers, workspaces and event queues;
- distinguish absent, unknown, stale, denied and invalid values;
- never interpret profile text, app titles, file names or boot menu labels as executable instructions;
- return a deterministic result for identical valid input;
- preserve input state when a decision is denied or returns backpressure;
- include a stable diagnostic code and field/path context for invalid input;
- keep policy data separate from privileged side effects.

The Reaper tree-walk runtime and VM must execute the same contract fixtures and produce equivalent typed results. Native ABI integration is a later gate and must consume the same serialized contract fixtures.

## 4. Desktop contract shapes

### 4.1 Session profile

Required data: schema version, stable profile ID, base profile, layout mode, launcher mode, window policy, workspace policy, density, motion policy, required services and compatibility range.

Validation:

1. The profile ID is stable and unique.
2. Every enum is recognized by the target DuckOS session version.
3. Required services exist in the target capability profile.
4. Profile data contains no executable path, source body, URL action, driver name or privilege request.
5. Motion and accessibility preferences may be more restrictive than the system default, never less restrictive than a mandatory safety policy.
6. A profile is activated only when the full dependency plan is satisfiable.
7. Failure produces a rollback decision and leaves the previous session snapshot intact.

### 4.2 Output and surface

An output descriptor includes stable output ID, generation, physical and logical bounds, scale, transform and supported presentation modes. A surface descriptor includes client identity, surface ID, dimensions, pixel format, buffer quota, generation and lifecycle state.

Validation includes nonzero dimensions, configured maximum dimensions, checked pixel/byte multiplication, stride alignment, supported pixel formats, generation match and state-machine legality. A stale configure serial is rejected without changing the active surface.

### 4.3 Window and focus

A window record includes owning process identity, app ID, role, output ID, workspace ID, geometry, state and focus eligibility. A requested focus transition is evaluated against session policy and the caller's window ownership. Focus is not an authorization token and cannot grant capture, clipboard or input-device access.

Tiling calculations use bounded integer geometry. Every output rectangle must remain within the logical output after scale/transform conversion. Rounding must be deterministic and cumulative gaps may not push windows outside the usable region.

### 4.4 Input and portal

Input policy validates monotonically sequenced events, seat identity, target focus and event bounds. The default route is the focused client. System shortcuts are handled by a separate allowlisted path. Unknown events are rejected or ignored according to the protocol version; they are never reinterpreted as keystrokes.

Portal policy requires caller identity, purpose, requested scope, target identity, expiration and decision. A grant is short-lived, scoped and revocable. Denial, timeout or revocation leaves no residual capability. Native providers independently enforce the grant.

## 5. DuckBoot contract shapes

### 5.1 Boot entry

Required data: schema version, stable entry ID, source adapter, firmware class, architecture, loader path, kernel or image path, initramfs references, command-line source, filesystem identity, trust evidence, slot identity, fallback entry and version.

Validation rejects path traversal, duplicate IDs, unknown firmware/architecture, invalid path encoding, overlapping or overflowed image ranges, unsupported filesystem claims and unbounded command-line data. A menu label is display-only and never becomes a path or command.

### 5.2 Adapter capability negotiation

Each adapter advertises exact support for firmware, architecture, filesystem and operations. Supported operation names are discover, inspect, plan, verify, chainload, install, set-default, set-once, rollback and remove.

The contract returns one of: supported, unsupported, unavailable, requires-confirmation or blocked-by-policy. It must not infer install support from inspect support or infer set-once from set-default support. An adapter version mismatch fails closed.

### 5.3 Dry-run plan

A plan contains a stable plan ID, source entry, target adapter, ordered operations, affected paths, affected firmware variables, preconditions, backups required, recovery target, expiration and approval requirements.

The policy rejects a plan when any affected path is not owned or explicitly authorized, a target file is outside the declared ESP/vendor path, a required backup is missing, or a rollback path is not available. The planner never performs the operations.

### 5.4 Trust and anti-rollback

A trust decision consumes native verification evidence containing artifact digest, signature algorithm, signer identity, trust-root identity, verification result, revocation state, secure-boot mode and monotonic version. Reaper evaluates policy over that evidence; it does not create it.

A boolean such as signed=true is not acceptable evidence. Missing, stale, unverifiable or revoked evidence remains untrusted. An older version is rejected when it violates the configured anti-rollback floor.

### 5.5 Recovery

Recovery state contains the known-good entry, pending target, attempt count, maximum attempts, last boot result, health confirmation and rollback eligibility. The state machine must be deterministic and idempotent. Repeated recovery calls cannot increase the attempt budget or remove the known-good target.

A boot marker alone is not health confirmation. The final acceptance signal must come from the native startup supervisor after required services have passed their health checks.

## 6. Diagnostics

Suggested stable diagnostic families:

- RPR-DESK-001..099: profile and session decisions;
- RPR-DISP-001..099: outputs, surfaces and presentation admission;
- RPR-WIND-001..099: window, focus and geometry;
- RPR-INPT-001..099: input sequence and routing;
- RPR-PORT-001..099: portal grants and revocation;
- RPR-BOOT-001..099: boot-entry parsing and validation;
- RPR-ADPT-001..099: adapter capability and version;
- RPR-PLAN-001..099: plan precondition and resource diff;
- RPR-TRST-001..099: trust, revocation and anti-rollback;
- RPR-RECV-001..099: recovery and attempt-budget transitions.

Diagnostic messages must identify the failed field and expected invariant without exposing secrets, raw firmware variable contents or private paths unnecessarily.

## 7. Required Reaper tests

For every policy group, add:

- valid minimum and maximum descriptor fixtures;
- missing, unknown and duplicate field tests;
- overflow, underflow, alignment and range boundary tests;
- invalid enum and unsupported version tests;
- state transition and stale-generation tests;
- capability-denied and wrong-owner tests;
- resource exhaustion and bounded-queue tests;
- deterministic repeated-run fixtures;
- tree-walk and VM parity tests;
- integration fixtures consumed by DuckOS native host tests.

Boot tests additionally cover traversal paths, malformed configuration, unsupported operation negotiation, missing backup, expired plan, wrong ESP identity, invalid signature evidence, revocation and rollback loops.

Desktop tests additionally cover stale configure serials, zero/huge buffers, focus theft, input sequence gaps, revoked portal grants, client teardown and geometry rounding.

## 8. Integration order

1. Add Reaper data types and pure validators for profile and boot-entry descriptors.
2. Add session, surface, window and adapter policy state machines.
3. Add dry-run boot planner, trust-evidence evaluator and recovery policy.
4. Add shared fixtures and equivalent tree-walk/VM tests.
5. Export versioned data-only adapters for DuckOS host tests.
6. Connect the policy to native DuckOS only after the syscall, process, IPC, capability and memory contracts have enforceable implementations.
7. Add native DABI64 bindings only after compiler parity, calling convention, ownership, error mapping and freestanding runtime support pass their own gates.

Do not put guessed source syntax into this design document. The first implementation PR must follow the actual Reaper parser/runtime semantics and include executable tests. The second PR may bind the verified contracts to DuckOS native code. These are separate reviewable milestones.

## 9. Status vocabulary

- **specified:** schemas or architecture describe the intended behavior.
- **reference-tested:** Reaper source runs the policy tests on the reference runtime.
- **VM-tested:** the same fixtures pass through the Reaper VM with equivalent results.
- **native-host-tested:** native library and tests execute on the host.
- **freestanding-tested:** code is compiled and exercised in the target freestanding image/emulator.
- **privilege-enforced:** the kernel or firmware boundary independently enforces the operation.
- **hardware-qualified:** the declared physical hardware and firmware matrix has passed reproducible tests.

A status cannot skip a maturity level. Documentation, catalogs or a policy-only test never prove privilege enforcement or hardware qualification.
