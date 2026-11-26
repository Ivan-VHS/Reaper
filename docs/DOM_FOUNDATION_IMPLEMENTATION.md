# ДОМ Foundation — first executable Reaper-native slice

**Contract family:** reaper.dom.*.v1  
**Implementation language:** Reaper (.rpr)  
**Status:** initial reference-runtime vertical slice; native compiler parity is not claimed  
**Architecture parent:** https://github.com/Ivan-VHS/Reaper/pull/350

## What this increment implements

This change moves the ДОМ proposal from architecture diagrams into executable Reaper source for a cohesive first slice.

| Subsystem | Reaper source | Executable responsibility |
|---|---|---|
| Uu | dom/Uu/core.rpr | Stable list primitives, uniqueness, bounded pair operations, name and numeric checks |
| Nonconcrete | dom/Nonconcrete/contracts.rpr | Contract shape validation, major/minor compatibility, dependency and capability checks |
| poooVERTY | dom/poooVERTY/budgets.rpr | Four-dimensional resource vectors, admission, remaining budget, release and weighted split |
| JLOM | dom/JLOM/lifecycle.rpr | Explicit lifecycle transitions, managed instance records and task scopes |
| Establish | dom/Establish/manifest.rpr | Manifest validation, module dependency ordering, cycle rejection and host-grant checks |
| System Carriere | dom/System-Carriere/envelope.rpr | Versioned message-envelope validation, delivery policy and recipient resolution |
| JennyFlash | dom/JennyFlash/signals.rpr | Versioned signals, subscriptions, compare-and-set and atomic update batches |
| Jenny Flashing Boy | dom/Jenny-Flashing-Boy/reload.rpr | Development-only reload plans, ABI compatibility checks, quiescence gates and rollback selection |
| ДОМ Core | dom/core/runtime.rpr | Composition of manifest, host grants and lifecycle into one runtime instance |

All framework policy in this slice is authored in Reaper. The Python test module is only an adapter to the repository's existing reference-interpreter test harness; it is not a subsystem implementation.

The standalone modules are consumed through dom/adapters/framework_modules.rpr. The adapter calls only their public Reaper contracts; their algorithms remain in their owning modules.

## Canonical data contracts

The current Reaper grammar supports crafts, lists, module imports/exports and explicit result tuples. Until typed public record declarations and a stable aggregate ABI are available, this first vertical slice uses documented positional list contracts.

- Resource vector: [memory_units, task_slots, queue_items, open_handles].
- Contract descriptor: [id, major, minor, fields, effects, capabilities].
- Manifest: [schema, app_id, app_version, profile, modules, requested_capabilities, budget].
- Module descriptor: [module_id, version, dependencies].
- Runtime instance: [runtime_id, app_id, app_version, profile, state, generation, ordered_modules, granted_capabilities, budget].
- Message envelope: [message_id, correlation_id, schema_id, schema_version, sender, recipient, deadline, delivery_mode, payload].
- Signal: [signal_id, version, value, dependencies, subscribers].

A schema row is not a privilege grant. Establish validates requested capabilities against host-supplied grants. A valid manifest cannot elevate itself.

## Dependency and lifecycle rules

The initial source dependency direction is:

    Uu
      -> Nonconcrete
      -> poooVERTY
      -> JLOM
      -> System Carriere
      -> JennyFlash
      -> Establish
      -> ДОМ Core
      -> Applications and editors

This is an ownership sketch, not a requirement that each subsystem imports every preceding subsystem. Establish is the composition point; its resolver rejects missing dependencies and cycles before activation.

Lifecycle transitions are explicit:

    Declared -> Resolved -> Prepared -> Running -> Ready
                                          |          |
                                          +------> Quiescing -> Stopped

    Failed -> Recovering -> Prepared

Stopped is terminal for the current instance. Recovery is explicit; it does not silently restart a stopped object.

## Safety boundaries

- The current slice is deterministic and local. It does not open files, sockets, processes or devices.
- poooVERTY performs logical budget admission. A host OS must enforce physical memory, CPU and handle limits.
- System Carriere validates messages and resolves declared endpoints; it is not yet a network stack or cross-process transport.
- JennyFlash provides versioned values and atomic list-level batches; it is not yet a concurrent shared-memory engine.
- Jenny Flashing Boy authorizes a reload candidate only. It does not patch live machine code or bypass JLOM.
- No ambient capability, raw syscall, kernel pointer, driver load or firmware operation is introduced.
- Python remains the current compatibility oracle. Passing the Reaper source smoke test proves behavior only on the reference runtime.

## Verification

Run the Reaper source integration example through the current reference runtime:

    python -m reaper examples/dom_foundation_smoke.rpr
    python -m unittest tests.test_dom_foundation -v

The test entry point executes the .rpr program. It must not reimplement a subsystem in Python.

## Next implementation gates

1. Add Reaper-native positive, negative and boundary fixtures for every public operation.
2. Replace positional contracts with typed Reaper record declarations when the canonical type/IR contract supports them.
3. Add canonical IR and Span/SourceMap fixtures for ДОМ calls and diagnostics.
4. Add target-side allocation and task enforcement through an explicit Reaper host adapter.
5. Implement service-message transport and delivery/deduplication semantics.
6. Implement reactive graph ordering, incremental propagation and cycle handling.
7. Connect reload authorization to a real JLOM quiesce/snapshot/restore transaction.
8. Verify behavior through the future native Reaper compiler/runtime before promoting maturity.

## Scale target

The long-term engineering target is 50,000 qualified production Reaper LOC per separately owned framework subsystem. Qualified lines exclude comments, blank lines, docs, generated output, tests and duplicate/template code. This vertical slice is a small, inspectable foundation and is not represented as satisfying any 50,000-line target.
