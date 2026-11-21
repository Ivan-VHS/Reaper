# Reaper Language Reference 0.2

**Edition:** 0.2 reference-language slice  
**Executable reference:** Python 3.10+  
**Execution engines:** tree-walk interpreter and verified stack VM  
**Source extension:** `.rpr`

This document describes syntax that is parsed and executed by both reference engines. It deliberately separates executable behavior from lexical reservations, roadmap proposals and the partial C17 native track.

## 1. A complete runnable program

```reaper
import "math.rpr" as math

const limit = 10
let settings = {
    "name": "Reaper",
    "enabled": true,
    "limits": {"items": limit}
}

fn sum_until(values, stop) {
    mut total = 0
    for value in values {
        if value == stop {
            break
        }
        total = total + value
    }
    return total
}

fn label(config) {
    return config.name ?? "unnamed"
}

emit label(settings)
emit sum_until([1, 2, 3, 4, 5], 4)
emit "enabled" in settings
```

`::` remains the native flow operator: it passes a value to the next function or builtin. Existing `make`, `vary`, `change`, `craft`, `yield`, `emit`, `when`, `otherwise` and `each` syntax remains supported.

## 2. Declarations and assignment

| Form | Meaning |
|---|---|
| `let name = value` | Immutable binding |
| `const name = value` | Immutable binding; spelling alias for the same runtime contract |
| `mut name = value` | Mutable binding |
| `make name := value` | Existing immutable syntax |
| `vary name := value` | Existing mutable syntax |
| `name = value` | Assignment to an existing mutable binding |
| `change name := value` | Existing explicit assignment syntax |

A declaration cannot silently replace a name already defined in the same lexical scope. Assignment to an immutable binding is a runtime error. Reaper is dynamically typed in edition 0.2; the annotation and static type-system keywords in the reserved vocabulary are not yet a type checker.

## 3. Functions and return

```reaper
fn multiply(left, right) {
    return left * right
}

craft legacy(value) {
    yield value * 2
}

emit multiply(6, 7)
emit legacy(21)
```

`fn` and `craft` declare the same function type. `return` and `yield` have identical return semantics. Functions capture their lexical environment, require an exact argument count and are protected by the configured call-depth and execution-step limits. A return outside a function is rejected.

## 4. Conditions and loops

```reaper
mut total = 0
for item in [1, 2, 3, 4, 5] {
    if item == 2 {
        continue
    } else {
        total = total + item
    }
}

mut cursor = 0
while cursor < 10 {
    cursor = cursor + 1
    if cursor == 6 {
        break
    }
}
emit [total, cursor]
```

- `if / else` is equivalent to `when / otherwise`.
- `for value in collection` is equivalent to `each value in collection`.
- `while condition` is the direct loop form; legacy `loop while condition` remains accepted.
- `break` leaves the nearest enclosing loop.
- `continue` advances the nearest enclosing loop.
- Loop-control statements cannot cross a function boundary. Using them outside a loop is an error.

Lists, tuples, ranges, text and maps are valid iteration inputs. Map iteration visits keys in insertion order. Collection and step quotas remain enforced.

## 5. Maps, field access and membership

```reaper
let user = {
    "name": "Ada",
    "profile": {"active": true, "score": 42}
}

emit user.name
emit user.profile.score
emit user["name"]
emit "profile" in user
emit "missing" in user
```

Map keys must be hashable. Duplicate keys use the last value. Field access is shorthand for a string-key map lookup and reports a language error for a missing field or a non-map receiver. Index access continues to support lists and maps.

## 6. Null coalescing

```reaper
let optional_name = nothing
let display_name = optional_name ?? "anonymous"
emit display_name
```

`left ?? right` evaluates `right` only when `left` is `nothing` (the runtime null value). This is a short-circuit operator in both engines, not a truthiness fallback: `false`, `0` and empty text are preserved.

## 7. Execution engines and parity

The canonical pipeline is:

```text
.rpr source
  -> position-aware lexer
  -> recursive-descent / Pratt parser
  -> AST
      -> tree-walk reference interpreter
      -> canonical stack IR -> verifier -> bytecode VM
```

Both engines share runtime values, builtins, resource quotas, module loading, error formatting and memory accounting. The 0.2 conformance tests run new declarations, control flow, maps, membership and null coalescing through both engines.

The C17 track remains a separate partial native frontend/IR implementation. This release does not claim that C17 compiles or runs the full Python reference language.

## 8. Diagnostics and safety boundaries

- Source-aware lexer and parser errors retain filename, line and column.
- Execution-step, recursive call-depth, collection-size, text-size, heap and open-resource limits remain active.
- Module imports remain explicit `.rpr` imports with cycle and depth detection.
- Native FFI remains opt-in and consent-gated through the existing host boundary.
- Map field access and membership are deterministic and local; map literals do not perform implicit I/O.
- The VM rejects unsupported AST forms during lowering instead of silently executing a different program.

## 9. Explicitly not part of 0.2

The following vocabulary remains reserved or planned and must not be treated as implemented merely because the lexer recognizes it: user-defined `struct` / `enum` / `trait` / `impl`, static types and generics, pattern matching, async/await, compile-time evaluation, effect annotations, lexical memory regions, native C17 full-language parity, package manager and cross-project build toolchain.

The next language milestones should add these as vertical slices: grammar + semantic rules + tree-walk behavior + IR/VM parity + diagnostics + conformance tests + documentation. Feature count alone is not an acceptance criterion.

## 10. Conformance tests

```sh
python -m unittest discover -s tests -p "test_language_v2.py" -v
python -m unittest discover -s tests -p "test_language.py" -v
python -m unittest discover -s tests -p "test_extended_runtime.py" -v
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
```
