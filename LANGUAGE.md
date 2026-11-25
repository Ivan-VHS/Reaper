# Reaper language — quick reference

**Normative specification:** [Reaper Language Canon v1](docs/LANGUAGE_CANON.md)  
**Machine-readable contract:** [language/language-canon.v1.json](language/language-canon.v1.json)

Reaper is one language with one semantic core. The canonical source extension is `.rpr`; the canonical flow operator is `::`. The Russian МОСТ layer supplies exact aliases for the same Reaper tokens and does not create a second grammar.

## Core syntax

| Syntax | Meaning |
|---|---|
| `craft name(args) { ... }` | Function |
| `make name := value` | Immutable binding |
| `vary name := value` | Mutable binding |
| `change name := value` | Reassignment |
| `yield value` | Function result |
| `emit value` | Explicit output |
| `when condition { ... } otherwise { ... }` | Conditional |
| `each item in values { ... }` | Iteration |
| `loop while condition { ... }` | Bounded loop |
| `value :: operation(args)` | Pass value as the first argument |

```reaper
craft double(x) {
    yield x * 2
}

make total := [1, 2, 3] :: map(double) :: sum()
emit "total = " ++ text(total)
```

## Operator order

From lowest to highest: `::`, `or`, `and`, comparisons, `++`, `+ -`, `* / // %`, `**`. Exponentiation is right-associative; the other binary operators are left-associative. The word forms `and` and `or` are canonical.

`|>` and `~>` are not pipeline aliases. `->` is not a pipeline operator. C17 lexer/parser recognition of additional spellings does not make those spellings part of the reference language.

## МОСТ

The alias registry contains 54 exact Russian mappings: 21 runtime-supported aliases and 33 lexically reserved aliases. Reserved aliases do not imply parser or runtime support. No stemming, inflection guessing or synonym resolution is performed. See [МОСТ implementation status](docs/MOST_IMPLEMENTATION_STATUS.md) and [alias registry](language/most_keyword_aliases.json).

## Implementation boundary

The Python reference runtime and its VM define the current broad compatibility behavior. The native C17 parser is an expression-level slice, and native AOT supports a bounded scalar subset emitted as C17 for a host toolchain. Full native parity, direct freestanding DuckOS code generation and self-hosting are not claimed.

Use [Features](docs/FEATURES.md), [Implementation roadmap](docs/IMPLEMENTATION_ROADMAP.md), [Native Compiler](docs/NATIVE_COMPILER.md) and [Hardware Language](docs/HARDWARE_LANGUAGE.md) for evidence-backed implementation status.
