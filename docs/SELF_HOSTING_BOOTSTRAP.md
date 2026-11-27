# Reaper Self-Hosting Bootstrap

## Objective

Move language implementation logic into Reaper source files. The finished compiler must be able to compile and rebuild its own source; merely renaming the Python or C implementation does not count as self-hosting.

## Current status — Stage 0, partial Stage 1, partial Stage 2 and partial Stage 3

The self-hosting implementation lives in executable `.rpr` files. The Python reference interpreter currently acts only as the bootstrap host and test orchestrator for these sources. Running a Reaper-written module proves that the module's logic is Reaper code; it does **not** prove a self-hosting compiler or native-code parity.

### Stage 0: tokenizer

`selfhost/lexer.rpr` scans source text in Reaper itself. It covers ASCII identifiers and digits, keywords, decimal/integer literals, strings and escapes, comments, newlines, punctuation, operators and source positions. It returns a structured error token for an invalid character or malformed string.

The reference lexer accepts Unicode identifiers. The self-hosted lexer does not yet have parity for Unicode identifier classification, so Stage 0 remains open.

### Stage 1: Pratt expression parser (partial)

`selfhost/parser.rpr` consumes the bootstrap token-array shape and builds compact array-form expression nodes. Implemented forms are literals, names, unary expressions, grouping, list literals, function calls, indexing and infix operators. Its precedence table includes the actual `::` flow operator and right-associative `**`.

The parser does **not** yet parse declarations, function definitions, imports/exports, blocks, conditionals, iteration or loop statements. Its expression nodes are stage-local arrays, not the canonical whole-program AST contract. The Python parser remains the compatibility oracle.

### Stage 2: expression semantic analysis (partial)

`selfhost/semantic.rpr` implements deterministic symbol-table validation, duplicate-name rejection, name resolution, direct function/builtin call arity checks and conservative expression type inference. Its current primitive types are `number`, `text`, `boolean`, `list`, `nothing` and `unknown`. Numeric, text-concatenation, logical, comparison, indexing and flow-operator cases are handled explicitly. Diagnostics retain the expression's line and column where available.

The current pass is expression-scoped. It does not yet implement lexical scopes, declarations, parameter-type contracts, control-flow analysis, definite assignment, mutability checking or whole-program/module semantics. It must not be used as a replacement for the reference type/runtime checks.

### Stage 3: canonical expression IR and bytecode lowering (partial)

`selfhost/ir.rpr` lowers supported expression nodes into a versioned `RIR1` array representation. It recursively verifies node shapes, operator allowlists and source spans, then emits deterministic stack bytecode for constants, loads, unary/binary operations, calls, list construction and indexing. A separate bytecode verifier checks instruction shape, stack underflow, call/list arity consumption and the final single-value stack invariant. The verifier reports the maximum required stack depth.

This is an expression-only IR and bytecode frontend. It does **not** include a bytecode VM, control-flow blocks, whole-program IR, optimizer, object writer, linker, executable loader or native code generation. A verified bytecode sequence is not proof that it can execute or produce a native binary.

### Bootstrap stages

| Stage | Reaper-written component | Current state and acceptance gate |
|---|---|---|
| 0 | Lexer | Partial; token parity including Unicode identifiers, every keyword/operator, escapes and malformed-source positions |
| 1 | Pratt parser and statement parser | Expression subset exists; declarations, functions, imports/exports, blocks and control flow must match the canonical AST |
| 2 | Semantic analysis | Expression subset exists; scopes, function signatures, mutability, control flow and differential semantic fixtures remain |
| 3 | Canonical IR and verifier | Expression RIR1 and stack bytecode subset exists; whole-program IR, control-flow validation and cross-engine golden fixtures remain |
| 4 | Optimizer passes | Not implemented in the self-hosted frontend; requires semantics-preserving passes, fixed-point budgets and reproducible output |
| 5 | Native code-generation frontend | Not implemented in the self-hosted frontend; generated output must build and pass conformance |
| 6 | Bootstrap closure | Not implemented; the self-hosted compiler must rebuild itself reproducibly from a clean checkout |

## Non-negotiable rules

1. Reaper implementation logic belongs in `.rpr` sources; host code is limited to bootstrap, platform primitives and test orchestration.
2. Keep the Python implementation as a compatibility oracle until full differential parity is demonstrated.
3. Keep the C17 runtime/compiler track as the native execution substrate during bootstrap; do not claim it is a complete runtime until the full suite passes.
4. Every stage has positive, negative, regression, resource-limit and source-location tests.
5. A stage is not complete because its source file exists. It must pass the stated acceptance gate on a clean checkout.
6. Bootstrap builds must be deterministic and record source hashes, compiler version, target and build inputs.
7. No stage may silently add filesystem, network, process, shell or hardware authority to ordinary Reaper programs.

## Immediate next work

- Close Unicode identifier and numeric-character parity in the self-hosted lexer.
- Expand token conformance to every keyword, operator, escape, whitespace and malformed-source case.
- Add a Reaper-written statement parser for declarations, function definitions, imports/exports, blocks, conditionals, iteration and loops.
- Define a versioned whole-program AST and compare it with the reference parser over a shared golden corpus.
- Expand semantic analysis to lexical scopes, function parameter types, mutability, definite assignment and control-flow joins.
- Extend RIR1 to whole-program definitions and explicit control-flow blocks; add malformed-IR and resource-boundary fixtures.
- Implement an optimizer only after semantic and IR conformance gates exist.
- Move the CLI and compilation orchestration into Reaper in dependency order.
