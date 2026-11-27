# Expressive Precision: Reaper Syntax Design Rules v1

**Status:** normative design contract for future syntax and standard-library evolution.  
**Implementation boundary:** this document does not add keywords, operators, parser behavior or runtime capabilities. Existing source syntax and executable behavior remain authoritative.

## Purpose

The supplied text demonstrates several useful forms of expression: compact phrases, repeated hooks, internal sound patterns, layered vocabulary, ordered sequences, sharp transitions and movement between local details and larger systems. Reaper can learn from those structures without copying their words or importing ambiguity into a programming language.

The resulting design principle is **Expressive Precision**:

> Make common intent concise and memorable while keeping parsing, evaluation, memory, effects and failure behavior explicit.

Artistic ambiguity belongs in names, domain vocabulary and program output. The grammar and runtime must remain deterministic.

## Source-language baseline

The current reference grammar uses Reaper's established vocabulary: `craft`, `make`, `vary`, `change`, `yield`, `emit`, `when`, `otherwise`, `each`, `in`, `loop while`, and the data-flow operator `::`. Collection examples use calls such as `map`, `keep` and `sum`.

The canonical pipeline form is:

```reaper
value :: operation(arguments)
```

The left-hand value is passed as the first argument to the operation. `::` is a data-flow operator in the current language contract; it is not silently reinterpreted as namespace access. Do not introduce `->`, `|>` or another spelling as a competing pipeline operator without a separately reviewed grammar and migration decision.

## Design rules

### 1. Keep a strong grammatical spine

The core grammar must stay small, regular and teachable. A new keyword is justified only when it represents a recurring language-level operation that cannot be expressed clearly as a function, type, trait or module.

Prefer one canonical spelling per semantic operation. Avoid decorative syntax, implicit context switching, invisible state changes and token overloading that makes code harder to parse or review.

### 2. Give data flow a readable cadence

A pipeline should read from source to result. Every stage must have a defined input, output, evaluation order and effect boundary. Each stage is evaluated exactly once unless its documented contract explicitly states otherwise.

Use `::` for the established first-argument flow form. Keep intermediate transformations small and name a stage when its purpose is not obvious. Do not hide allocation, I/O, mutation, error suppression or capability acquisition inside a visually innocent pipeline step.

### 3. Treat reusable logic as the refrain

Repeated behavior belongs in a named `craft` function or a reusable library contract. Repetition should not require copying code, but reuse must not introduce a hidden macro system or implicit textual substitution.

A reusable operation must have stable semantics, documented inputs and outputs, predictable effects, and tests for edge cases. Combinators such as `map`, `keep` and `sum` should compose without changing the meaning of the functions passed to them.

### 4. Build meaning in layers

Keep the language core vocabulary small. Put domain-specific concepts in ordinary identifiers, modules, types, traits and library functions rather than promoting every useful noun into a reserved word.

A domain-specific language (DSL) must have a bounded grammar, an explicit owner, a contract, compatibility rules and a clear lowering path into the canonical language model. A DSL must not become a second parser hidden inside an ordinary string or comment.

### 5. Make names expressive, not magical

Prefer pronounceable, consistent names that reveal intent. A family of related APIs should use a coherent naming pattern; near-synonyms should not accidentally describe different operations.

Localized aliases must map through an explicit, versioned alias table to one canonical token. Matching is exact: no fuzzy spelling, phonetic guessing, stemming, transliteration or automatic synonym resolution. Unicode identifiers need documented character rules; mixed-script and confusable-name checks may warn, but must not silently rename identifiers.

### 6. Make sequences and numbers exact

Numeric syntax must communicate width, signedness, bounds, overflow behavior and units where relevant. Any range or repetition construct must define endpoint inclusion, direction, empty-range behavior, iteration limits and overflow handling.

Do not infer arithmetic meaning from repeated digits, words or visual patterns. A compact sequence form is acceptable only when its mathematical meaning is unambiguous and its resource cost is bounded.

### 7. Keep transitions visible

Branching, state changes, early exits and failure paths must remain visible in source. The language may offer concise forms, but they must preserve explicit control-flow semantics.

Future pattern matching must define exhaustiveness, unreachable cases, binding scope and behavior for unknown or non-exhaustive input. Future error-composition helpers must preserve the original error unless the program explicitly transforms or handles it. No silent fallback from an error to a plausible value.

### 8. Preserve the thin seams

High-level syntax must lower to a transparent representation. Types, ownership, lifetimes, resource cleanup, ABI layout, host effects and hardware access must have explicit rules at module and platform boundaries.

A short expression is not permission to allocate without bounds, borrow unsafely, access the filesystem, open a socket, call FFI or touch a device. The compiler and diagnostics must expose relevant overflow, conversion, lifetime, effect and resource risks.

### 9. Separate signal from diagnostic noise

Normal program logic should not be crowded with tracing scaffolding. Prefer structured, opt-in logging, tracing and event APIs with stable fields, filters, severity, correlation identifiers and bounded storage.

Observability must not change program semantics, bypass quotas or introduce hidden network or filesystem access. Developer tools may present a filtered view while retaining access to the complete authorized trace.

### 10. Keep the first useful task light

A new user should be able to read, check and run a small `.rpr` program through the documented reference workflow without first adopting a large framework or a mandatory package ecosystem.

The standard library should cover frequent local tasks with small, composable APIs. Optional integrations remain optional; simple programs should not inherit dependencies, permissions or setup ceremony they do not use.

### 11. Make one source portable across the toolchain

The reference frontend, VM, native frontend, formatter, LSP, DAP and documentation must share one canonical grammar and semantic contract. A feature is not complete merely because one parser accepts it.

High-level convenience syntax must have a defined AST/IR form and a predictable lower-level implementation. Native support and performance claims require parity fixtures and measurements on declared targets; they must not be inferred from reference-runtime behavior.

### 12. Evolve by evidence, not by ornament

Every syntax or standard-library extension must include:

1. A language-design rationale and a versioned grammar/semantic decision.
2. Positive and negative parser fixtures, including malformed and boundary inputs.
3. Stable source spans, diagnostics and source-map behavior.
4. Defined type, evaluation-order, resource and effect rules.
5. Canonical AST/IR representation and verifier coverage.
6. Reference-runtime and VM conformance; native parity where the target claims support.
7. Formatter, LSP, DAP and localized-alias alignment where applicable.
8. Migration notes, runnable examples, documentation and CI evidence.

A reserved token is not an implemented feature. A design page is not proof of runtime support. Keep maturity labels honest.

## Current-syntax example

This example uses the existing Reaper surface and demonstrates the intended compact, reusable flow. It does not require new syntax:

```reaper
craft double(value) {
    yield value * 2
}

craft is_large(value) {
    yield value >= 6
}

make values := [1, 2, 3, 4, 5]
make total := values :: map(double) :: keep(is_large) :: sum()

emit "flow result = " ++ text(total)
```

The named functions act as reusable hooks; the pipeline expresses the route; the result remains inspectable. Each operation retains its own documented contract.

## Competitiveness criteria

Reaper's syntax should be judged against practical work rather than visual novelty:

- **Readability:** a developer can identify data flow, mutation, effects and failure paths from the source.
- **Composability:** small functions and standard-library operations can be combined without special-case syntax.
- **Predictability:** the same source has stable parsing and defined behavior across supported execution paths.
- **Systems depth:** high-level code can be traced to types, IR, ABI and resource behavior.
- **Low entry cost:** the first useful utility does not require a heavyweight framework.
- **Tooling quality:** diagnostics, formatting, completion, navigation and debugging use the same language contracts.
- **Measured efficiency:** compile time, runtime cost, allocations and memory use are benchmarked rather than advertised by intuition.
- **Ecosystem compatibility:** modules and public APIs have versioned contracts and explicit compatibility boundaries.

## Non-goals

This design does not call for lyric-like keywords, phonetic parsing, fuzzy aliases, implicit macros, hidden control flow, several equivalent pipeline operators, or importing another language's syntax wholesale. Reaper's character should come from a coherent vocabulary and dependable composition, not from novelty tokens.

## Immediate adoption order

1. Apply these rules to all new grammar and standard-library proposals.
2. Keep the existing `::` flow operator and current `craft/make/vary/change/yield/emit` vocabulary as the compatibility baseline.
3. Prefer named reusable functions and documented combinators over syntax expansion for repeated patterns.
4. Close Unicode, source-span, parser and toolchain parity gaps before accepting further lexical sugar.
5. Evaluate each proposed extension with real utilities and measured cost, not showcase snippets alone.
