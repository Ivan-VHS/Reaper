# Reaper expressive constructs — 66-item implementation map

This map classifies the 66 ideas supplied for the Reaper language. Status describes the **Python reference runtime** on this branch. A keyword existing in the lexer or a reserved-token catalogue is not proof of executable support.

Status labels:
- **Implemented** — parser/runtime behavior plus acceptance coverage.
- **Partial** — a narrower related behavior exists; the full construct is not claimed.
- **Reserved only** — recognized by vocabulary/alias infrastructure but has no executable language semantics.
- **Planned** — not implemented in this slice.

## 1. Conditions, branching and pattern matching

| # | Construct | Status | Reaper behavior |
|---:|---|---|---|
| 1 | Pattern matching | Implemented | \`match value { case pattern { ... } }\`; supports literals, bindings, wildcard, fixed lists, maps and tagged variants |
| 2 | Guard clauses | Implemented | \`case pattern if condition { ... }\`; rejected guards fall through to the next arm |
| 3 | Ternary operator | Implemented | \`condition ? yes : no\`; branches are lazy |
| 4 | Null coalescing | Implemented | \`value ?? fallback\`; fallback is evaluated only when value is \`nothing\` |
| 5 | Null-coalescing assignment | Implemented | \`value ??= fallback\`; requires a mutable binding only when assignment is needed |
| 6 | Optional chaining | Implemented | \`map?.key\`, \`sequence?.length\`, \`sequence?.[index]\`; \`nothing\` and missing/out-of-range members propagate as \`nothing\` |
| 7 | Let-else | Implemented | \`let [a, b] := pair else { yield fallback }\`; the failure block must leave the current function or Reaper reports an error |
| 8 | Expression-bodied if | Partial | Ternary expressions are implemented; block-valued \`if\` expressions are not |
| 9 | Range-based if / in | Implemented | \`x in 1..5\` uses an exclusive end; \`1..=5\` is inclusive |
| 10 | Active patterns | Planned | Custom user-defined pattern extractors are not available |
| 11 | \`unless_ok\` | Partial | \`Ok\`, \`Err\`, \`try_result\` and \`or_else\` cover common result handling; no dedicated \`unless_ok { } fallback { }\` syntax |

## 2. Loops, streams and lazy evaluation

| # | Construct | Status | Reaper behavior |
|---:|---|---|---|
| 12 | Generators (\`yield\`) | Partial | \`yield\` returns from a \`craft\`; it is not a resumable generator |
| 13 | Generator delegation | Planned | \`yield from\` / \`yield*\` not implemented |
| 14 | Comprehensions | Implemented | Bounded list comprehension: \`[x * 2 for x in values if x > 0]\`; set/dict comprehensions are not included |
| 15 | Lazy sequences | Partial | Existing collection pipelines are eager; \`transduce\` offers a one-pass transformation pipeline without intermediate result lists |
| 16 | Async iterators | Planned | No \`for await\` execution |
| 17 | Zip / enumerate | Implemented | Bounded \`zip(...)\` and \`enumerate(sequence, start)\` built-ins |
| 18 | Labeled loops | Planned | No loop labels or labeled break/continue |
| 19 | Early guard / return | Partial | Pattern guards and let-else exits are available; there is no separate general-purpose guard statement |
| 20 | Infinite stream with take | Partial | \`take\` and bounded \`iterate(seed, steps, fn)\` exist; no unbounded lazy stream source |
| 21 | Transducers | Implemented | \`transduce(values, filtering(fn), mapping(fn), taking(n))\` performs a bounded single pass |
| 22 | \`retry_every\` | Planned | No timed retry/backoff scheduler |

## 3. Functions, composition and resource context

| # | Construct | Status | Reaper behavior |
|---:|---|---|---|
| 23 | Closures | Implemented | \`craft\` functions retain their lexical environment |
| 24 | Currying / partial application | Implemented | \`curry(fn, arity)\` and \`partial(fn, bound...)\` return callable adapters |
| 25 | Composition | Implemented | \`compose(f, g)\` runs right-to-left; \`pipe_fn(f, g)\` runs left-to-right |
| 26 | Pipe operator | Implemented | Reaper's native pipe spelling is \`::\`, e.g. \`items :: map(double) :: sum()\`; \`|>\` is not an alias |
| 27 | Decorators / wrappers | Partial | Function adapters exist for partial, composition and memoization; general declaration decorators are not implemented |
| 28 | Context managers | Partial | Managed resources are bounded and closed by the runtime; source-level \`with/using/defer\` blocks are not implemented |
| 29 | Memoization | Implemented | \`memoize(fn, max_entries)\` is bounded; \`memo_ttl(fn, ttl_ms, max_entries)\` uses a monotonic TTL clock |
| 30 | Higher-order functions | Implemented | User functions are accepted by \`map\`, \`keep/filter\`, \`fold/reduce\`, sorting and transducers |
| 31 | Tail-call optimization | Planned | Recursive calls remain subject to the call-depth limit |
| 32 | Algebraic effects / try-catch-finally | Partial | Runtime exceptions and Result values are explicit; source-level \`try/catch/finally\` syntax is not implemented |
| 33 | \`memo_ttl\` | Implemented | TTL cache is bounded and local to the returned function adapter |

## 4. Types, data and expressiveness

| # | Construct | Status | Reaper behavior |
|---:|---|---|---|
| 34 | Algebraic data types | Partial | Built-in tagged variants \`Ok(value)\`, \`Err(error)\`, \`Some(value)\`; user-defined product/sum type declarations are not active |
| 35 | Tagged unions | Implemented | Built-in variants carry a stable tag and fields and can be matched by constructor pattern |
| 36 | Destructuring | Implemented | Match and let-else destructure fixed list, map and variant patterns |
| 37 | Spread / rest operators | Planned | No general \`...\` expansion |
| 38 | Immutable updates | Partial | \`make\` bindings are immutable and functional helpers return new collections; there is no persistent immutable collection type |
| 39 | Newtype / opaque types | Planned | No distinct nominal wrapper type declarations |
| 40 | Generics / traits / typeclasses | Planned | No reference-runtime static type checker |
| 41 | Extension methods | Planned | No extension-method declaration syntax |
| 42 | Literal / phantom types | Planned | No compile-time literal or phantom type system |
| 43 | Typestate builder API | Planned | No compiler-enforced typestate protocol |
| 44 | Unit types | Planned | No dimensional unit checker; numeric operations remain ordinary number operations |

## 5. Async, concurrency and reactive behavior

| # | Construct | Status | Reaper behavior |
|---:|---|---|---|
| 45 | \`async/await\` | Reserved only | English/Russian vocabulary is recognized; no asynchronous execution semantics |
| 46 | Structured concurrency | Planned | No task-group runtime |
| 47 | Channels / actors | Planned | No message-passing scheduler |
| 48 | \`select\` | Planned | No multi-channel wait operation |
| 49 | Cancellation tokens | Planned | No cooperative task cancellation runtime |
| 50 | Future / Promise combinators | Planned | No Reaper Future type |
| 51 | Reactive signals | Planned | No dependency-tracked reactive state |
| 52 | Backpressure | Planned | No producer/consumer stream scheduler |
| 53 | Atomic / lock-free primitives | Planned | No shared-memory atomic API |
| 54 | Debounce / throttle | Planned | No event scheduler |
| 55 | Hedged request race | Planned | No network request runtime or hedging scheduler |

## 6. Metaprogramming, contracts and language tooling

| # | Construct | Status | Reaper behavior |
|---:|---|---|---|
| 56 | Macros | Planned | No AST macro expansion stage |
| 57 | \`comptime\` / \`constexpr\` | Reserved only | Vocabulary is reserved; compile-time evaluation is not implemented |
| 58 | Design by contract | Partial | Runtime \`requires\`, \`ensures\` and \`invariant_guard\` checks exist; function-signature pre/postconditions are not implemented |
| 59 | Tagged template literals | Planned | No tagged-template syntax |
| 60 | Derive / reflection macros | Planned | No generated type implementations |
| 61 | Declarative DSLs | Partial | Reaper supports expression and pipeline DSLs; no general user-defined embedded DSL declaration system |
| 62 | Property-based test generators | Planned | Unit acceptance tests exist; no property generator/shrinking framework |
| 63 | Result / Option handling | Implemented | \`Ok\`, \`Err\`, \`Some\`, \`is_ok\`, \`is_err\`, \`is_some\`, \`unwrap\`, \`or_else\`, \`try_result\`; no postfix \`?\` propagation operator |
| 64 | Hot reload / live coding | Partial | LSP supports incremental document changes; the running interpreter does not hot-reload code while preserving a live session |
| 65 | Sandbox / capability permissions | Partial | Execution quotas, managed resources and explicit native-FFI opt-in exist; this is not an OS process sandbox |
| 66 | \`invariant_guard\` | Implemented | Runtime invariant assertion with caller-supplied diagnostic text |

## Runtime examples

\`\`\`reaper
craft double(x) { yield x * 2 }
craft positive(x) { yield x > 0 }

make odds := [x for x in 1..10 if x % 2 == 1]
make result := transduce(odds, mapping(double), taking(3))
emit result

make profile := {name: "Reaper", icon: "bird"}
emit profile?.icon ?? "unknown"

match Ok(42) {
    case Ok(value) if value > 40 { emit "accepted" }
    case Err(error) { emit error }
    case _ { emit "not available" }
}
\`\`\`

## Compatibility boundary

These additions are implemented in the Python reference runtime and are tested through both
the tree-walk engine and the VM entry point. The VM currently delegates the new high-level
AST forms to the same reference evaluator to preserve semantics. This does **not** claim
native C17 parser/runtime parity. The native track remains a separate partial compiler until
its own parser, IR, code generation and conformance tests implement these features.

\`yield\` remains a function return, not a generator suspension. Async/concurrency words and
compile-time/type vocabulary that remain reserved are not executable features. Collection
comprehensions, maps, transducers and memoization all obey interpreter collection/execution
limits. Memoized functions should be pure; a cache does not invalidate itself when captured
mutable state changes.
