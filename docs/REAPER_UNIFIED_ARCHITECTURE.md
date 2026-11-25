# Reaper unified language architecture

**Normative language authority:** [Reaper Language Canon v1](LANGUAGE_CANON.md)  
**Machine-readable projection:** [language/language-canon.v1.json](../language/language-canon.v1.json)

This page summarizes the architecture. It does not define a competing grammar.

| Principle | Contract |
|---|---|
| One language | Reaper owns canonical syntax, semantics, value model and module contract |
| One semantic core | All supported surface profiles normalize to one canonical AST and semantic IR |
| МОСТ | Exact Russian keyword aliases only; no morphology, synonym inference or second grammar |
| Flow | `::` is the sole canonical pipeline operator |
| Mutability | Immutable by default; mutation is explicit |
| Effects | Host operations are explicit and capability-gated |
| Runtime | Resource and execution budgets are enforced by the selected runtime |
| Native target | C17 and future target backends must pass feature-by-feature conformance |

## Compiler boundary

`source → profile resolution → lexer → parser → canonical AST → semantic checks → canonical IR → verifier → runtime/backend`

A syntax profile may change spelling or provide a grammar adapter, but cannot change type rules, evaluation order, errors, module behavior, permissions, limits or ABI contracts. Profile selection is explicit; content-based grammar guessing is prohibited.

## Current implementation

- The Python reference lexer, parser, runtime and VM form the current broad compatibility baseline.
- МОСТ has 54 exact aliases: 21 runtime-supported and 33 lexically reserved.
- The native C17 lexer/parser is narrower than the full Reaper grammar; its current parser is expression-oriented.
- The native AOT path compiles a bounded scalar subset through generated C17 and a host compiler.
- QCS is a separate validation frontend, not a Reaper dialect.

The C17 frontend recognizes some spellings that the reference grammar does not currently accept. Those spellings are non-canonical until all language layers are updated and conformance tests prove the same meaning. In particular, a token catalog, lexer branch or architecture proposal is not evidence of an implemented language feature.

## Hardware boundary

The language may eventually express target-specific types and operations through versioned grammar, type/effect rules and target profiles. A source declaration cannot map physical memory, enter privilege, register an interrupt, allocate DMA memory or perform device I/O by itself. A trusted OS/driver/platform adapter owns those operations and validates the requested capabilities.

See [Hardware Language](HARDWARE_LANGUAGE.md), [Native Compiler](NATIVE_COMPILER.md), [Native IR execution](NATIVE_IR_EXECUTION.md) and [Implementation roadmap](IMPLEMENTATION_ROADMAP.md) for current evidence and remaining gates.
