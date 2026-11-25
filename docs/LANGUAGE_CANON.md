# Reaper Language Canon v1

**Status:** normative language contract  
**Contract:** `reaper.language-canon.v1`  
**Edition:** Reaper 0.1 compatibility surface  
**Scope:** source syntax, semantics, profiles, compiler boundaries, runtime guarantees and conformance

This document establishes one language authority for Reaper. It consolidates the rules already supported by the reference implementation and sets the conditions under which future syntax or native compiler work may be promoted. It does not claim that every target feature described in architecture documents is already executable.

The normative words **MUST**, **MUST NOT**, **SHOULD** and **MAY** are used in their ordinary standards sense.

## 1. Authority and document hierarchy

There is one Reaper language and one semantic contract.

1. **This document** is the normative human-readable language specification.
2. **`language/language-canon.v1.json`** is the versioned machine-readable projection of this contract. It records identifiers, current profiles, operator precedence, implementation boundaries and conformance gates. It is not a replacement parser or a source of unimplemented syntax.
3. **`LANGUAGE.md`** is the short syntax reference. It MUST link here and MUST NOT define conflicting rules.
4. **`docs/PSYCHOPORTER_666.md`** governs code quality, naming, safety and engineering conduct. It does not create additional grammar.
5. **`language/features.json`** records feature maturity. A registry row does not make a feature executable.
6. **`language/token_catalog.json`** reserves symbolic lexemes only. A reserved lexeme is not an operator until grammar, semantics, diagnostics and tests exist.
7. **`language/most_keyword_aliases.json`** is the exact МОСТ alias registry. It maps spellings to existing Reaper words; it does not define another language.
8. The reference lexer, parser, runtime, tests and CI provide implementation evidence. A mismatch between this contract and an implementation is a conformance defect, not permission to create another interpretation.

Architecture, hardware, IDE, marketing and roadmap documents are subordinate to this authority for language syntax and meaning. They may describe future work, but MUST label it as specified, partial or planned.

## 2. Language identity

- The language name is **Reaper**.
- The canonical source extension is **`.rpr`**.
- Source text is UTF-8. Line and column information is retained for diagnostics.
- Canonical keyword spellings are lowercase English words.
- Identifiers preserve their source spelling. An alias is normalized only by an exact registered mapping.
- A source file has one selected Reaper grammar/profile. The compiler MUST NOT guess a grammar from arbitrary source text.
- Comments use `#`. Text literals use double quotes and the documented escapes: `\\n`, `\\r`, `\\t`, `\\"` and `\\\\`.

A future source edition or grammar change MUST be versioned and accompanied by an explicit compatibility or migration rule.

## 3. Canonical surface syntax

The current reference grammar uses the following executable keyword set:

`make`, `vary`, `change`, `craft`, `yield`, `emit`, `when`, `otherwise`, `each`, `in`, `loop`, `while`, `true`, `false`, `nothing`, `and`, `or`, `not`, `import`, `export`, `as`.

The established declaration and control-flow forms are:

| Form | Meaning |
|---|---|
| `make name := value` | Declare an immutable binding |
| `vary name := value` | Declare a mutable binding |
| `change name := value` | Assign to an existing mutable binding |
| `craft name(args) { ... }` | Declare a function |
| `yield value` | Return a value from a function |
| `emit value` | Write an explicit output value |
| `when condition { ... } otherwise { ... }` | Conditional execution |
| `each item in values { ... }` | Collection iteration |
| `loop while condition { ... }` | Bounded while loop |
| `import "module.rpr" as alias` | Import a Reaper module |
| `export name` | Export a declared name |

A function may use `yield` without an expression where the current runtime permits a unit-like result. Blocks use braces. Statements are separated by newlines; semicolons are not a substitute for the canonical layout.

### 3.1 Binding and mutation

- `make` is immutable by default.
- `vary` explicitly opts into mutation.
- `change` MUST target an existing mutable binding.
- A compiler MUST reject writes to immutable or unknown bindings before executing the affected program.
- Implicit mutation through an alias, hidden global state or an undocumented host callback is not part of the language contract.

### 3.2 Canonical flow operator

The sole canonical flow/pipeline operator is **`::`**.

`value :: operation(args)` passes `value` as the first argument to `operation`. Chained expressions are evaluated left to right according to the published precedence and associativity rules.

`|>` and `~>` are not aliases for `::`. `->` is not a pipeline operator. A future type-signature or control-flow use of another token requires its own versioned grammar rule and MUST NOT silently redefine pipeline behavior.

### 3.3 Reference expression precedence

The reference parser defines the following binary precedence, from lowest to highest. Operators at the same level associate left to right, except exponentiation, which associates right to left.

| Precedence | Operators | Contract |
|---:|---|---|
| 1 | `::` | Flow: insert the left value as the first argument of the right call |
| 2 | `or` | Boolean disjunction |
| 3 | `and` | Boolean conjunction |
| 4 | `== != < <= > >=` | Equality and comparison |
| 5 | `++` | Text concatenation |
| 6 | `+ -` | Addition and subtraction |
| 7 | `* / // %` | Multiplication, division, floor division and remainder |
| 8 | `**` | Exponentiation; right associative |

Prefix `not` and unary `-` are part of the reference expression grammar. The canonical word operators are `and` and `or`; symbolic spellings such as `&&` and `||` are not interchangeable aliases.

This table describes the reference grammar. Native frontend support is a separate implementation-maturity question and MUST be tested against the same fixtures.

## 4. One semantic core, not competing dialects

Reaper has one semantic core:

`source → profile resolution → lexing → parsing → canonical AST → semantic checks → canonical IR → IR verification → runtime/backend`

A syntax profile MAY alter exact spelling or provide a grammar adapter. It MUST normalize into the same canonical AST and semantic IR. After normalization, profile identity may be retained as source provenance, but MUST NOT create different:

- value or type semantics;
- evaluation order or error behavior;
- module, scope or symbol rules;
- ownership or resource-lifetime rules;
- runtime limits;
- filesystem, process, network, clock, FFI or hardware permissions;
- ABI or calling-convention rules.

A profile MUST be selected explicitly through a registered profile, file extension or project configuration. The compiler MUST NOT infer it from source content. An unregistered alias, operator or grammar is an error, not an implicit compatibility mode.

### 4.1 Current profiles

| Profile | Status | Contract |
|---|---|---|
| Reaper canonical | Current | The `.rpr` language and canonical English keyword set |
| МОСТ Russian | Partial | Exact Russian aliases normalized to canonical Reaper tokens |
| Ukrainian aliases, Classic aliases, alternate flow grammars | Not promoted in the current mainline contract | Require a versioned profile, explicit selection and full conformance evidence before becoming supported profiles |

МОСТ currently records 54 exact aliases: 21 have reference-runtime support and 33 are lexically reserved. Reserved aliases do not imply parser, type-checker, IR, VM or native-backend support. No stemming, inflection guessing, transliteration or synonym inference is permitted.

A foreign language frontend such as QCS, or a polyglot adapter for another language, is a separate frontend/tool integration. It is not automatically a Reaper dialect. Embedded languages require explicit delimiters, a pinned adapter and a canonical interchange boundary.

## 5. Semantic and runtime invariants

All implementations and profiles MUST preserve these invariants:

1. **Explicit meaning.** No silent type conversion, ambiguous overload or profile-dependent runtime behavior.
2. **Explicit effects.** Filesystem, console, process, network, clock, FFI and hardware operations are explicit host/runtime capabilities. No ambient shell, network or privileged hardware access is implied by an expression.
3. **Bounded execution.** Source size, token count, nesting, steps, call depth, text, collections and managed resources have documented limits. Limits are enforced by the selected runtime rather than assumed from syntax.
4. **Predictable failure.** Invalid syntax, unsupported constructs, arithmetic failures, quota exhaustion and denied capabilities produce explicit diagnostics or runtime errors. A backend MUST reject unsupported source before code generation; it MUST NOT silently fall back to another runtime.
5. **Deterministic interfaces.** Public module, serialization, FFI and target contracts are versioned. Ownership, lifetime, mutation and cleanup responsibilities are explicit at each boundary.
6. **Least authority.** A source program cannot grant itself operating-system privilege. Hardware access is mediated by a trusted OS/driver/platform adapter and an explicit capability.
7. **Observable provenance.** Diagnostics and generated code preserve source attribution sufficiently to identify the responsible source construct. Expanded source maps and end-to-end span parity remain compiler conformance work until proven.

## 6. Canonical compiler and backend boundaries

Every backend implements the same language contract; no backend owns a separate language meaning.

- The Python reference lexer/parser/runtime is the current compatibility baseline for the broad `.rpr` surface.
- The bytecode VM is an execution path over the reference semantic/IR model and MUST remain behaviorally aligned with the reference interpreter.
- The native C17 lexer/parser currently covers a narrower expression/AST slice. It is not a complete Reaper frontend.
- The native C17 AOT path supports a bounded scalar subset and emits C17 for a host compiler. It is not full native parity, a freestanding DuckOS compiler, a complete linker/loader or a self-hosting compiler.
- QCS is a separate validation frontend, not a second spelling of Reaper.

The native C17 lexer/parser currently recognizes some operator spellings that are not in the reference grammar (including `??`, `&&`, `||`, `+%` and `+|`). Recognition by a lexer or a partial parser does not promote a spelling into Reaper. Such tokens MUST remain reserved/non-canonical until the reference grammar, semantics, diagnostics, IR, runtime and conformance tests are updated together.

Likewise, fixed-width type syntax, `Result`, ownership/borrowing, regions, async, IRQ, DMA, MMIO and other systems constructs are not current language features merely because they appear in a target architecture or design example. Each construct requires a versioned syntax rule, type/effect rule, IR representation, runtime/backend behavior and positive/negative tests.

## 7. Naming, formatting and localization

- Use the canonical English keyword set in public `.rpr` examples unless the example explicitly demonstrates a supported МОСТ alias.
- Use descriptive `lower_snake_case` identifiers for ordinary variables, functions and module-level names, consistent with the Reaper code constitution.
- Keep type, ABI, target and diagnostic names stable and versioned.
- Keep user-facing translations separate from source-language keywords. Translation of documentation or UI does not silently translate the grammar.
- Preserve each repository and product's identity; language standardization does not rename Reaper, its modules or its applications.

See [Psychoporter 666](PSYCHOPORTER_666.md) for the full code-quality, safety and review constitution.

## 8. Feature maturity and promotion

Use the existing feature maturity terms consistently:

| Status | Meaning |
|---|---|
| `planned` | Intended work; no complete normative or executable implementation is claimed |
| `specified` | A contract exists, but executable support is not established |
| `partial` | A bounded implementation exists with explicit exclusions |
| `implemented` | The declared scope exists in source and has relevant regression tests |
| `deprecated` | Retained only for a documented compatibility window; new code must not adopt it |

A feature is not **verified** merely because a document, registry entry, generated scaffold or single backend accepts its spelling. Verification is an evidence gate: the relevant CI checks, positive and negative tests, reference/VM parity, and native conformance for any backend that claims support must pass.

A language change is eligible for promotion only when it has:

- a precise grammar and precedence/associativity rule;
- positive, negative, boundary and malformed-input tests;
- deterministic canonical AST/IR fixtures;
- explicit type, effect, error, ownership and resource behavior where applicable;
- source-location and diagnostic coverage;
- reference-interpreter and VM parity;
- native-backend parity for every backend that claims the feature;
- documentation, migration notes and a versioning decision.

A reserved token or a catalogue count is never implementation evidence.

## 9. Change control

A change to syntax, semantics, a profile or an ABI MUST update the canonical human spec and machine projection in the same reviewable change. It MUST also update the relevant lexer/parser, feature registry, tests, examples, IDE/LSP metadata and backend conformance fixtures where affected.

Changes that only propose future capability MUST remain marked `specified` or `planned`. Do not rewrite existing source files or rename public syntax as incidental cleanup. Compatibility changes require an explicit migration path and deprecation window.

The acceptance objective is simple: **one Reaper language, one meaning, one canonical semantic contract, multiple implementations only where conformance is proven.**
