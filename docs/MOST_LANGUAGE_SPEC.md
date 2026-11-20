# MOST — language architecture and implementation contract

**Status:** MOST is specified as the Russian-first source language frontend; the native C17 lexer is being extended with Russian reserved words. The complete Russian grammar, resolver, type checker and backend are not yet implemented.

MOST is the systems-and-web language track of REAPER. It targets deterministic native code and WebAssembly from one statically typed source language. The C17 implementation is the bootstrap host; it is not the language's permanent runtime requirement.

## Design invariants

1. No subject-oriented receiver keywords. `@` denotes the current lexical receiver/context.
2. No implicit allocation, conversion, thread creation, exception unwinding, or ambient global state.
3. Static types, immutable bindings by default, explicit mutation, explicit effects.
4. No tracing garbage collector. Region/arena allocation and linear resource ownership are checked statically.
5. A single source model lowers to verified typed IR, then to native or WASM backends.
6. The Python interpreter remains a compatibility oracle until the native implementation passes differential conformance; it is not a MOST backend.
7. Every capability has an implementation state and executable acceptance tests. Roadmap text never counts as implementation.
8. Russian is the primary source-language vocabulary of MOST; compatible REAPER syntax remains available and shares the same semantics.
9. Morphology and synonyms are explicit, scoped lookup tables. The compiler never guesses a program meaning from unrestricted natural-language text.
10. Unicode normalization and source mapping are compiler contracts; spoken prosody and voice recognition are separate host tools.

## Canonical surface syntax

MOST is Russian-first. The following is the target spelling for the Russian frontend:

~~~most
модуль счётчик

структура Состояние {
    значение: целое32 = 0
}

функция увеличить(значение: целое32, шаг: целое32) -> целое32 {
    вернуть значение +| шаг
}

пусть шаг: целое32 = 2
переменная итог: целое32 = увеличить(40, шаг)

если итог > 0 {
    вывести "готово"
} иначе {
    вывести "пусто"
}
~~~

This example documents the planned grammar; it is not yet a promise that the whole program parses or executes. The native C17 lexer recognizes the Russian keyword vocabulary, while declaration grammar, MOST intent resolution, type checking and backend support remain later gates.

The compatibility REAPER surface keeps its existing forms and semantics:

~~~reaper
module counter

struct State {
    value: signal<i32> = 0
}

fn increment(value: i32, step: i32) -> i32 {
    value +| step
}
~~~

Both source forms must lower to equivalent typed AST/Canonical IR. Source spelling, canonical symbol and source range remain available for diagnostics and tooling.

### Russian lexical vocabulary

The initial reserved-word set includes module/access words (модуль, импорт, как, публичный, экспорт), declarations (функция, структура, перечисление, типаж, реализация, тип, константа), bindings (пусть, переменная, изменить), control flow (вернуть, если, иначе, выбор, для, в, пока, прервать, продолжить, отложить), memory and resource words (область, сырой, арена, уничтожить), task/reactivity words (сигнал, асинхронно, ожидать), contracts (тест, вычислить_при_сборке, требует, гарантирует), system boundaries (небезопасно, внешний, где), values and logic (истина, ложь, ничего, и, или, не), and interaction words (вывести, сказать, спросить).

Names such as счётчик, состояние, файл and целое32 remain identifiers. Built-in type aliases are registered in the type table, not treated as control keywords. The lexer retains the original spelling; exact NFC validation and code-point source columns are separate conformance work.

Russian case forms and synonyms are not accepted by free-form stemming. They will be resolved by explicit per-module dictionaries after lexing, with unknown-name and ambiguity diagnostics. No probabilistic or network lookup may silently select a symbol.

## Compiler pipeline

`UTF-8 source → tokens → CST/AST → name resolution → type/effect checking → ownership & region analysis → typed MOST IR → verification/optimization → native or WASM backend`.

The IR must be immutable, source-mapped, deterministic and independently verifiable. Frontends must not emit machine code directly. Backend selection must not change source semantics.

## Memory and safety model

- **Regions:** lexical region scopes own bulk allocations; escape analysis prevents references outliving a region.
- **Borrows:** shared immutable borrows may alias; mutable borrows are exclusive. The compiler rejects overlapping mutable access.
- **Linear resources:** file/socket/lock handles are consumed by close, transfer, or a verified scope destructor exactly once.
- **Raw operations:** pointer arithmetic, inline assembly and hardware access require an explicit unsafe function/block and are excluded from safe proofs.
- **Slices:** pointer-plus-length values carry bounds; safe indexing checks bounds or is proven safe.
- **Drop:** deterministic reverse declaration order; cleanup paths are inserted on every control-flow exit.
- **Arithmetic:** checked by default; wrapping and saturating operators are distinct semantics.
- **Optionals:** tagged option types; pointer niche optimization is permitted only when ABI and validity rules prove it sound.

A region allocator is not a substitute for borrow checking. Runtime tests alone cannot establish memory safety.

## Types and language semantics

The type system includes fixed-width integers, floats, booleans, UTF-8 strings/slices, arrays, tuples, structs, enums with payloads, option/result types, function types, traits, and explicit pointer/ABI types. Exhaustive matching is a compile-time property. Generic monomorphization and compile-time evaluation must be bounded and deterministic.

`::` passes the left expression as the first argument. `??` unwraps an optional with a fallback. `+%` is wrapping addition; `+|` is saturating addition. More than two call arguments require labels in canonical source mode. Effects (I/O, allocation, mutation, unsafe, async) are explicit in function signatures or verified effect declarations.

## Web and WASM boundary

The web layer is a typed host binding, not a second dynamic language. DOM nodes, events, Canvas, WebGL, WebGPU, Fetch and AudioContext are represented by capability-bearing handles. Signals compile to direct dependency updates; no Virtual DOM is required. UI syntax lowers through the same AST and typed IR. Strings are escaped by default; trusted HTML requires a distinct unsafe-capability type.

The browser still supplies Web APIs and a JavaScript host boundary where the platform requires it. MOST removes application-framework dependence; it cannot make browser APIs cease to exist. Server rendering, hydration, routing and CSS scoping are separate milestones.

## Native and C interoperability

C ABI declarations must specify layout, alignment, calling convention, ownership and error mapping. Header ingestion begins with a constrained declarator parser; full preprocessing and arbitrary macro evaluation are not assumed. SIMD abstractions lower per target with scalar fallbacks. Endian wrappers and bit-width integers have explicit serialization rules. Bare-metal targets require a documented target description and linker/runtime contract.

## 66-rule language-formation ledger

The 66 sociolinguistic, phonetic, semantic and grammatical principles are mapped to concrete language design decisions in [MOST_RUSSIAN_66_RULES.md](MOST_RUSSIAN_66_RULES.md). The ledger is normative input for design and acceptance planning, not a claim that every capability already exists.

| Rules | MOST interpretation | Acceptance owner |
|---|---|---|
| 1–11 | Clear commands, functions, scopes, explicit results, quantities, capabilities and teachable examples | Grammar, symbols, types, effects, docs |
| 12–22 | Namespaced domain vocabularies, imports, dialect isolation, editioning and stable public conventions | Modules, resolver, package/version manager |
| 23–33 | Contrastive spelling, Unicode identifiers, formatter rules and strict separation of written syntax from speech | Lexer, Unicode validator, formatter, optional host adapter |
| 34–44 | Explicit canonical names, composition, aliases, imports, semantic specialization and deterministic macros | Resolver, type checker, standard library |
| 45–55 | Formal grammar, fixed declaration order, explicit morphology, typing, provenance and grammar versioning | Parser, resolver, type/effect checker |
| 56–66 | Learnability, stable core, composition, bounded recursion, introspection, documentation and governed evolution | Runtime, tooling, CI, edition policy |

The human-language mechanisms do not become hidden execution behavior: intonation does not change syntax, tone does not change values, social prestige does not select overloads, and natural-language ambiguity is a compile error. See the linked document for the complete rule-by-rule mapping and delivery stages.

## Delivery phases and truthful status

- **M0 — Native lexical base:** C17 scanner, source locations, MOST keywords/operators. This branch implements this phase.
- **M1 — Grammar:** declarations, expressions, blocks, functions, structs/enums, Pratt expressions, parser diagnostics.
- **M2 — Semantic core:** symbol tables, static types, inference, ADTs, exhaustive match, contracts and typed IR.
- **M3 — Safe memory:** regions, borrows, move/linear checking, slices, drop elaboration and allocator interfaces.
- **M4 — Native executable:** portable object/ELF first, then PE and Mach-O; C ABI and target-specific codegen.
- **M5 — WASM:** WASI and browser WASM targets, host bindings, UI and signals.
- **M6 — Toolchain:** tests, fuzzing, docs tests, profiler, reproducible builds, package hashes and self-hosting.

No claim of sub-5-MB self-hosting, full C-header parsing, 15-KB universal web bundles, constant-time cryptography, all-platform cross-compilation, or 30-year ABI stability is made until independently measured and tested.

## Compatibility policy

The 1.0 core grammar and semantics are frozen. Additions after 1.0 use versioned standard-library modules or explicitly versioned language editions; security fixes and compiler bug fixes must not silently change valid program meaning. Binary ABI stability is a separate promise from source compatibility.


## 147-feature architecture extension

The extended architecture backlog, including all 147 proposed capabilities, semantic constraints, platform caveats, duplicate resolution, implementation waves and truthful status ledger, is maintained in [MOST_147_FEATURE_REGISTRY.md](MOST_147_FEATURE_REGISTRY.md). The registry extends the 66 foundational rules; it does not imply that the listed features are already implemented. The canonical numbering is normalized to seven non-overlapping groups (1–21 through 127–147).
