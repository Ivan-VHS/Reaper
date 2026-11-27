# Reaper Self-Hosting Bootstrap

## Objective

Move language implementation logic into Reaper source files. The finished compiler must be able to compile and rebuild its own source; merely renaming the Python or C implementation does not count as self-hosting.

## Current status — Stage 0 and partial Stage 1

`selfhost/lexer.rpr` is the first executable frontend component implemented in Reaper itself. It performs scanning in Reaper functions and uses only the language's existing string indexing, lists, comparisons, loops, flow-independent control statements and standard collection operations. The Python interpreter is only the bootstrap host that executes this Reaper program.

The stage-0 lexer currently covers ASCII identifiers and digits, keywords, decimal/integer literals, strings and escapes, comments, newlines, punctuation, operators and source positions. It returns a structured error token for an invalid character or malformed string. The Python lexer accepts Unicode identifiers; that compatibility gap is deliberate and must be closed before the self-hosted frontend can replace the reference lexer.

The Python test suite executes the Reaper source and checks its internal assertions. This proves that the lexer logic is running as Reaper code; it does **not** prove a self-hosting compiler or complete frontend parity.

### Stage 1: Pratt expression parser (partial)

`selfhost/parser.rpr` now implements a Pratt parser in Reaper source. It consumes the same token-array shape emitted by the bootstrap lexer and builds compact array-form expression nodes. Implemented forms are literals, names, unary expressions, grouping, list literals, function calls, indexing and infix operators. The precedence table matches the reference parser, including the actual `::` flow operator and right-associative `**`.

The bootstrap assertions cover arithmetic precedence, exponentiation associativity, source-located unary nodes, flow composition, nested call/list/index expressions, missing delimiters and trailing-token errors. The reference-runtime test suite executes `selfhost/lexer.rpr`, `selfhost/parser.rpr`, and `selfhost/scalar_stack.rpr`; the same tests are registered with CTest when the reference-runtime test host is available. The tests exercise Reaper source; the host is orchestration, not the implementation of these algorithms.

This is deliberately **not** a complete parser replacement: declarations, function definitions, control-flow statements, block grammar and parity with the reference AST are not yet implemented. The parser output is a stage-local representation, not the canonical AST contract. The reference parser remains the compatibility frontend.

### Reaper-native scalar medium and stack synthesis

`selfhost/scalar_stack.rpr` is an executable Reaper module for two bounded algorithms:

- scalar-field relaxation on a cyclic one-dimensional topology, with Q16 interpolation, per-cell completed-half-life decay, scalar-gradient measurement and checked flux aggregation;
- deterministic stack planning over module/ABI descriptors, dependency edges, local-only/deprecation policy, memory/compute budgets, common-runtime deduplication and stable topological ordering.

The module validates positional record layouts at its boundary. It does not use the proposed `contract`, `comptime`, `budget` or `arena_slot` syntax because those constructs are not yet part of the implemented frontend. The array layouts are explicitly versioned in the feature documentation and tested through the Reaper reference runtime.

The criticality gate consumes runtime counters (`spawned_tasks / accepted_tasks`) in Q16. It rejects supercritical reproduction, a full queue, or active workers above the declared slot count. A near-critical balanced window is a policy threshold, not a claim that queue stability follows from a static module descriptor.

The stack synthesizer produces a deterministic integration plan; it does not merge source files into one unreviewable binary, download dependencies, rewrite code, or mutate repositories. Estimated memory savings count only declared shared-runtime allocations deduplicated under an identical key and ABI. They are not measured executable-size or latency improvements. The native AOT backend does not yet compile this full module.

## Bootstrap stages

| Stage | Reaper-written component | Acceptance gate |
|---|---|---|
| 0 | Lexer | Token-by-token parity for the supported language, Unicode and error locations included |
| 1 | Pratt expression parser (partial); statement parser and canonical AST still pending | Calls, indexes, lists and operators are covered; complete AST parity and statement grammar remain the acceptance gate |
| 2 | Semantic analysis and runtime support | Differential conformance against the reference interpreter |
| 3 | Canonical IR construction and verifier | Deterministic IR plus rejection of malformed or unsafe IR |
| 4 | Optimizer passes | Differential semantics, fixed-point budget and reproducible output |
| 5 | Native code-generation frontend | Generated output builds and passes the complete conformance suite |
| 6 | Bootstrap closure | Stage-1 rebuilds Stage-1 reproducibly; clean-room Stage-0/Stage-1/Stage-2 builds agree |

## Non-negotiable rules

1. Reaper implementation logic belongs in `.rpr` sources; host code is limited to bootstrap, platform primitives and test orchestration.
2. Keep the Python implementation as a compatibility oracle until full differential parity is demonstrated.
3. Keep the C17 runtime/compiler track as the native execution substrate during bootstrap; do not claim it is a complete runtime until the full suite passes.
4. Every stage has positive, negative, regression, resource-limit and source-location tests.
5. A stage is not complete because its source file exists. It must pass the stated acceptance gate on a clean checkout.
6. Bootstrap builds must be deterministic and record source hashes, compiler version, target and build inputs.
7. No stage may silently add filesystem, network, process, shell or hardware authority to ordinary Reaper programs.

## Immediate next work

- Close Unicode identifier parity in the self-hosted lexer.
- Expand token conformance to every keyword, operator, escape, whitespace and malformed-source case.
- Extend the Reaper-written frontend with declarations, function definitions, blocks, conditionals, iteration and loop statements.
- Define a versioned canonical AST representation and compare parser output with the Python AST over a shared golden corpus.
- Add differential tests for calls, indexes, list literals, operator precedence, nested blocks and malformed statements.
- Move the CLI, diagnostics, semantic analysis and compiler pipeline into Reaper in dependency order.
