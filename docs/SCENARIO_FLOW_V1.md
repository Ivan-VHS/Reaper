# Scenario Flow v1

**Status:** implemented in the Python reference frontend, tree-walk runtime, canonical IR and bytecode VM. The native C17 compiler does not yet claim parity.

Scenario Flow is a small, explicit control-flow layer for bounded computational scenarios. It reuses Reaper's existing function, lexical-scope, pipeline, quota and capability contracts instead of introducing a second execution model.

## Canonical syntax

```rpr
scenario operanda(num; seed; bounds) {
    reg total := seed
    reg offset := num

    each value in bounds {
        when value == 0 {
            continue
        }
        change total := total + value
    }

    yield total + offset
}

make result := operanda(2; 10; 0...3)
emit result
```

The example produces `18`: the inclusive range is `0, 1, 2, 3`, the loop continues past zero, the numeric register accumulates the remaining values, and the scenario returns the result.

## Language rules

| Construct | Rule |
|---|---|
| `scenario name(parameters) { ... }` | Declares a callable scenario using exactly the same lexical closure, call-depth limit, return, and error semantics as `craft`. It is not a privileged task or a separate scheduler. |
| `reg name := expression` | Creates a mutable, function/block-local numeric binding. Initial and assigned values must be integers or finite runtime numbers; booleans and text are rejected. It is a language-level register, not a physical CPU register, MMIO mapping, or device handle. |
| `continue` | Continues the nearest enclosing `each` or `loop while`. The parser rejects it outside a loop, including inside a nested function that merely appears within a loop. |
| `start...end` / `start..end` | Creates an inclusive integer range. Ascending and descending endpoints are supported. The item count is checked against the interpreter's collection quota before iteration. |
| `;` | May separate parameters, call arguments, list elements, and statements. Commas and newline statement boundaries remain supported. |
| `value :: function(arguments)` | Retains the existing Reaper data-flow call: `value` is passed as the first argument. The operator is not reinterpreted as namespace access. |

The type checker models inclusive ranges as `Range[Int]` and numeric registers as mutable numeric bindings. Unknown function parameter types remain `Any`; they are not guessed. Runtime guards remain mandatory.

## Mapping the supplied sketch

- `Scenario::operanda(num)` becomes a declaration such as `scenario operanda(num; seed; bounds) { ... }`, followed by an ordinary call to `operanda(...)`. `::` remains the pipeline operator, not a namespace delimiter.
- `Concrete scenario(num;sum;0...1)` becomes a concrete call with explicit arguments, for example `operanda(num; sum; 0...1)`.
- `reg it regit` becomes explicit numeric register declarations such as `reg it := num` and `reg regit := sum`.
- `continue` is executable loop control with matching behavior in tree-walk and VM execution.
- `Join::connecting(option)` can be written as `option :: connecting()` when `connecting` is an explicitly declared function.
- `adopt :: call`, `serenity`, and `stand_portable` remain ordinary user-defined functions or values. Reaper does not invent a host action from an identifier's spelling.
- A scene is an explicit value passed to or returned from a scenario. Shared/global scene state must be passed explicitly; a scenario does not receive an implicit global mutable scene.
- A `past` phase should be represented by explicit history data or a separately called function. It does not imply time travel, rollback, or an implicit snapshot service.

## Capability and privilege boundary

The fragment `private+ privilege` is not executable Reaper syntax and is intentionally not introduced as a privilege-escalation operator. Scenario declarations do not acquire permissions. File, process, network, native FFI, device, MMIO and other host effects continue to use the existing explicit host grants, consent checks, quotas and opt-in boundaries. A scenario can use only capabilities already granted by the host; it cannot mint, widen, or transfer them by calling `adopt`, `join`, or another user-defined function.

## Maturity boundary

The parser, type checker, tree-walk runtime, canonical IR, verifier and bytecode VM are extended together. The native C17 expression compiler remains a separate, partial implementation; this feature must not be described as native-compiled until its grammar, lowering, diagnostics and differential fixtures are implemented and pass.


## Related reference-runtime library

[SEAM Architecture v1](SEAM_ARCHITECTURE_V1.md) builds on the existing Scenario Flow, module and capability contracts. It does not change the grammar or reinterpret `::`.
