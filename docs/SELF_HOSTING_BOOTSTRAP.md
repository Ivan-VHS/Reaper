# Reaper Self-Hosting Bootstrap

## Objective

Move language implementation logic into Reaper source files. The finished compiler must be able to compile and rebuild its own source; merely renaming the Python or C implementation does not count as self-hosting.

## Current status — Stage 0 and partial Stage 1

### Stage 0: Reaper-written lexer (partial)

`selfhost/lexer.rpr` is the first executable frontend component implemented in Reaper itself. It performs scanning in Reaper functions and uses the language's existing string indexing, lists, comparisons, loops, control statements and collection operations. Python is only the bootstrap host that executes this source.

The lexer covers ASCII identifiers and digits, keywords, decimal/integer literals, strings and escapes, comments, newlines, punctuation, operators and source positions. It returns a structured error token for invalid characters and malformed strings. Unicode identifier parity with the Python reference lexer is not implemented yet.

### Stage 1: Reaper-written Pratt expression parser (partial)

`selfhost/parser.rpr` implements a Pratt parser in Reaper source. It consumes the reference token-array shape and builds a deterministic nested array tree for literals, identifiers, unary expressions, parenthesized expressions and infix operators. The precedence table covers flow composition, boolean operators, comparisons, concatenation, arithmetic and right-associative exponentiation. It reports malformed trailing input with source coordinates.

The parser deliberately remains a bounded expression slice. It does not yet parse function calls, indexing, list literals, declarations, function bodies, control-flow statements or the full reference AST schema. It is not a drop-in replacement for `reaper/parser.py` and Stage 1 is **not complete**.

### Bootstrap test contract

The Python unit suite executes both Reaper programs through the reference interpreter:
- `tests/test_self_hosting.py` runs `selfhost/lexer.rpr` and `selfhost/parser.rpr`.
- The tests validate embedded positive and negative assertions for tokens, positions, precedence, associativity, grouping and trailing-token diagnostics.
- The same test is registered with CTest when Python is available, in addition to the regular desktop unit-test workflow.

This proves that the lexer and expression-parser slices execute as Reaper code. It does **not** prove full frontend parity, a self-hosting compiler or native runtime equivalence.

## Bootstrap stages

| Stage | Reaper-written component | Current status | Acceptance gate |
|---|---|---|---|
| 0 | Lexer | Partial | Token-by-token parity for supported syntax, including Unicode and error locations |
| 1 | Parser and AST builder | Partial Pratt expression parser | Calls, indexes, literals, statements, AST parity and malformed-source diagnostics |
| 2 | Semantic analysis and runtime support | Planned | Differential conformance against the reference interpreter |
| 3 | Canonical IR construction and verifier | Native C17 slice exists; Reaper implementation planned | Deterministic IR plus rejection of malformed or unsafe IR |
| 4 | Optimizer passes | Native C17 slice exists; Reaper implementation planned | Differential semantics, fixed-point budget and reproducible output |
| 5 | Native code-generation frontend | Planned | Generated output builds and passes the complete conformance suite |
| 6 | Bootstrap closure | Planned | Stage-1 rebuilds Stage-1 reproducibly; clean-room bootstrap builds agree |

## Non-negotiable rules

1. Reaper implementation logic belongs in `.rpr` sources; host code is limited to bootstrap, platform primitives and test orchestration.
2. Keep the Python implementation as a compatibility oracle until full differential parity is demonstrated.
3. Keep the C17 runtime/compiler track as the native execution substrate during bootstrap; do not claim it is a complete runtime until the full suite passes.
4. Every stage has positive, negative, regression, resource-limit and source-location tests.
5. A stage is not complete because its source file exists. It must pass the stated acceptance gate on a clean checkout.
6. Bootstrap builds must be deterministic and record source hashes, compiler version, target and build inputs.
7. No stage may silently add filesystem, network, process, shell or hardware authority to ordinary Reaper programs.

## Immediate next work

- Close Unicode identifier parity in the self-hosted lexer and extend the token golden corpus.
- Extend the Reaper-written parser with calls, indexing, list literals and statement grammar.
- Define a canonical, versioned AST serialization format and compare parser output against the Python AST over a shared golden corpus.
- Add malformed-source, resource-limit and source-location tests before marking Stage 1 complete.
- Implement semantic analysis and ownership/type checks as Reaper modules before moving more compiler stages.
- Move the CLI, diagnostics and compiler pipeline into Reaper in dependency order.
