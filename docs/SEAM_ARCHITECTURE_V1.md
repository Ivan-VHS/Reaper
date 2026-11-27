# SEAM Architecture v1

**Status:** implemented as a Reaper-source standard-library module for the Python reference runtime. Native C17 compiler parity, self-hosted compiler parity, cryptographic checkpoint authentication and host-enforced effect authorization are not claimed.

SEAM is a compositional reliability layer for Reaper programs. It gives ordinary .rpr modules stable record contracts for state transitions, immutable root identity, preflight effect declarations, bridge compatibility, checkpoint structure and bounded event coalescing. It does not create a second runtime or introduce magic global operations.

## Canonical source form

Use existing Reaper syntax. Scenario Flow v1 is the current executable spelling:

```rpr
scenario operanda(num; seed; bounds) {
    reg total := seed
    each step in bounds {
        when step == 0 {
            continue
        }
        change total := total + step
    }
    yield total + num
}
```

The following fragments are design notation, not additional grammar:

- **Scenario::operanda(...)** maps to a **scenario operanda(...)** declaration and an ordinary call.
- **reg it regit** maps to explicit declarations such as **reg it := num**.
- **Concrete scenario(...)** maps to a call with concrete arguments.
- **::** remains the existing Reaper first-argument data-flow operator: **value :: transform(...)**. It is not namespace qualification.
- **past**, **serenity**, **call stand portable** and **scene -- pawn-global** are ordinary names or compositions unless an explicitly imported function defines their behavior.
- **private+ privilege** is not an operator. A module cannot mint, widen, transfer or self-approve host capabilities.

## Module

Import the implementation explicitly:

```rpr
import "../stdlib/seam.rpr" as seam
```

All public functions return a tagged result:

- Success: **["ok", value]**
- Failure: **["err", diagnostic_code, message]**

A caller must inspect the tag before indexing the value. SEAM never silently turns a failed validation into a successful state.

## Versioned record contracts

### State

**["reaper.seam.state.v1", revision, root, integrity, payload]**

- **revision**: integer in U64 range.
- **root**: non-empty text identity, immutable across transitions.
- **integrity**: finite numeric value in inclusive range **0...1**.
- **payload**: caller-owned Reaper value; SEAM does not claim to serialize it.

**state_make(revision, root, integrity, payload)** validates a new state. **state_validate(state)** checks its shape and invariants. **state_transition(current, expected_revision, next_integrity, payload, minimum_integrity)** performs compare-and-advance semantics: the expected revision must match, the new revision is exactly +1, the root is copied unchanged and integrity must satisfy the floor. Revision overflow, stale writes and weak candidates fail without producing a new state.

### Checkpoint

**["reaper.seam.checkpoint.v1", revision, root, state]**

**checkpoint_make(state)** captures a structural checkpoint. **checkpoint_recover(checkpoint, expected_root, minimum_revision, minimum_integrity)** checks the embedded state, duplicated revision/root metadata, caller-supplied root identity, minimum revision and integrity floor.

**Trust boundary:** this is structural consistency checking, not a digital signature. A caller must authenticate checkpoint origin and storage integrity through a trusted host before treating a checkpoint as trusted. The library does not write files, roll back an OS, or claim atomic persistence.

### Module contracts and bridges

Contract record:

**["reaper.seam.contract.v1", name, version, inputs, outputs, effects, invariants]**

Input/output lists contain unique non-empty type names. Effects are unique values from:

**pure, io.read, io.write, process, network, native.ffi, device.read, device.write, unsafe**

**pure** is exclusive and cannot be combined with effectful declarations.

**contract_make(...)** creates a checked contract; **contract_validate(...)** validates an existing one. **bridge_validate(producer, consumer, granted_effects)** requires exact producer-output / consumer-input type-list equality and checks the union of effectful declarations against an explicit caller-supplied grant list. A pure contract is neutral when composed with an effectful contract; an all-pure bridge remains pure.

**Trust boundary:** **granted_effects** is evidence supplied by the caller for preflight, not an authority token. This function does not grant, enforce or perform host effects. The actual host must independently enforce capabilities at the call boundary.

## Event folding

Event record:

**["reaper.seam.event.v1", category, severity, payload, count]**

Severity is an integer from 0 through 3:

| Level | Meaning |
|---:|---|
| 0 | trace |
| 1 | information |
| 2 | warning |
| 3 | error |

**event_make(category, severity, payload)** creates an event with count 1. **events_squash(events, minimum_severity, maximum_output)** applies severity filtering first, then coalesces only adjacent retained events with exactly equal category, severity and payload. It preserves order and aggregates multiplicity in the count field. It never sorts events or silently truncates output: invalid records, U64 count overflow, input above 100,000 events, or output above the caller's maximum return an error.

This is deterministic event aggregation, not a logging sink. It performs no filesystem, network, telemetry upload or persistence operation.

## Public API

| Function | Contract |
|---|---|
| **state_make** | Construct and validate a versioned state |
| **state_validate** | Validate state shape and invariants |
| **state_transition** | Compare expected revision and create the next state |
| **checkpoint_make** | Create a structural checkpoint |
| **checkpoint_recover** | Validate checkpoint metadata and recovery floors |
| **contract_make** | Construct a versioned module contract |
| **contract_validate** | Validate a module contract |
| **effect_authorize** | Structural effect/grant preflight |
| **bridge_validate** | Check type seam and combined effect declarations |
| **event_make** | Construct a bounded-severity event |
| **event_validate** | Validate an event record |
| **events_squash** | Filter and coalesce bounded adjacent events |

## Verification

- **examples/seam_recovery.rpr** demonstrates Scenario Flow, revision changes, checkpoint validation, bridges, explicit effect preflight and event coalescing.
- **selfhost/seam_conformance.rpr** is executed by the repository's existing Reaper reference-runtime test harness.
- The fixture covers stale revisions, integrity floors, root mismatch, metadata mismatch, incompatible bridge types, duplicate effects, mixed pure/effectful declarations, missing grants, severity filtering, event-count overflow and output bounds.

The SEAM module is reference-runtime-only until the native compiler and a genuine self-hosted frontend implement and pass equivalent parsing, lowering, execution and differential conformance tests. Do not infer native support from the Reaper-source implementation.
