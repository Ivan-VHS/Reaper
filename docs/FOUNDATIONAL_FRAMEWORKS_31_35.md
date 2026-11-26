# Reaper foundational frameworks 31–35

**Status:** executable Reaper reference contracts; live middleware, IPC, sandboxing and host dispatch remain partial or adapter-dependent.  
**Source:** `frameworks/foundation_31_35.rpr`  
**Dependency:** `frameworks/foundation_26_30.rpr`  
**Schema:** `reaper.foundation.seventh.v1`

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 31 | `foundation.layer.v1` | Layer | Intermediate subsystem boundary contracts | Partial |
| 32 | `foundation.middleware.v1` | Middleware | Ordered hooks, unique positions and failure policy | Partial |
| 33 | `foundation.integration-software.v1` | Integration Software | Versioned project envelopes and explicit adapter policy | Partial |
| 34 | `foundation.container.v1` | Container | Bounded hosted/simulator runtime profiles | Partial |
| 35 | `foundation.host.v1` | Host | Embedding lifecycle, capability and payload boundaries | Partial |

## 31. Layer — intermediate subsystem contracts

A layer contract is a fixed tuple:

`[id, from_layer, to_layer, interface_id, maturity]`

The catalogue links parser-to-semantic analysis, typed lowering, canonical IR execution, host dispatch and target lowering. Chain validation requires adjacent endpoints to connect without silently skipping a boundary.

Public functions: `layer_catalog()`, `layer_validate_contract(contract)`, `layer_validate_chain(chain)`.

## 32. Middleware — ordered extension hooks

A middleware hook is:

`[hook_id, phase, order, failure_mode]`

Phases are before-lex, after-parse, before-execute, after-execute, on-error and shutdown. Failure behavior is abort, skip or recover. Hook IDs and phase/order positions must be unique. The module validates a pipeline declaration; it does not call callbacks or inject code into the interpreter.

Public functions: `middleware_phases()`, `middleware_failure_modes()`, `middleware_validate_hook(hook)`, `middleware_validate_pipeline(pipeline)`, `middleware_order(pipeline)`.

## 33. Integration Software — cross-project adapters

The envelope is:

`[contract_id, major, minor, direction, payload_bytes, opt_in_enabled]`

The catalogue records the existing OPlague snapshot, Reaper comparison report, optional Pytyliki C ABI and OCTA-8 shared contract. Direction and version must match the contract; payload is bounded to one MiB. An opt-in contract is rejected unless its final boolean flag is explicitly true; ordinary contracts require false. The `not-applicable.v1` entry is kept visible as topology metadata but cannot be used for a transfer.

This is a schema gate, not a network client, authenticated transport or producer/consumer implementation. The native FFI remains opt-in.

Public functions: `integration_contracts()`, `integration_validate_envelope(envelope)`, `integration_validate_opt_in(id, enabled)`, `integration_transfer_policy()`.

## 34. Container — bounded execution profile

Profiles distinguish the current reference runtime quotas from simulator-only constraints and a planned explicit-network profile. Memory numbers are accounting targets, not hard process-RSS isolation. Reaper itself does not claim to provide an OS container, namespace isolation, seccomp, filesystem jail or network sandbox.

Public functions: `container_profiles()`, `container_validate_profile(profile)`, `container_validate_selection(id)`, `container_boundary_rules()`.

## 35. Host — embedding and authority

A host descriptor is:

`[host_id, abi_version, runtime_engine, capabilities, max_payload_bytes]`

Only ABI v1 and the existing tree-walk/canonical-VM engines are accepted. Payloads are bounded to one MiB. Granted capabilities must be a subset of the requested set and must be known to System Runtime ABI v1. This validator never grants capabilities; a trusted host remains the authority.

The lifecycle is construct → initialize → serve → drain → close → destroy.

Public functions: `host_lifecycle()`, `host_validate_lifecycle(trace)`, `host_contract_fields()`, `host_validate_descriptor(host)`, `host_validate_grant_policy(requested, granted)`, `host_boundary_rules()`.

## Unified catalogue

The module exposes `foundation_all_frameworks_35()` and `foundation_validate_catalog_35()`, extending all prior groups to thirty-five unique framework IDs.

## Usage

```reaper
import "../frameworks/foundation_31_35.rpr" as host

emit host["foundation_validate_catalog_35"]()
emit host["middleware_validate_pipeline"]([["audit", "before-execute", 10, "abort"], ["report", "after-execute", 20, "skip"]])
emit host["integration_validate_envelope"](["oplage.device-snapshot.v1", 1, 0, "consumes", 4096, false])
emit host["container_validate_selection"]("reference-bounded")
emit host["host_validate_descriptor"](["reaper-host", 1, "canonical-vm", ["FS_READ"], 65536])
emit host["host_validate_grant_policy"](["FS_READ", "CLOCK"], ["FS_READ"])
```

## Verification and safety

Tests cover valid/invalid layer chains, middleware positions, integration envelopes, container maturity and host capability subset rules. All functions are pure validators. No middleware callback, transport, container, host dispatch or privileged operation is actually started by this module.
