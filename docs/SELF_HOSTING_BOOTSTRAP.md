# Reaper Self-Hosting Bootstrap

## Objective

Move language implementation logic into Reaper source files. The finished compiler must be able to compile and rebuild its own source; merely renaming the Python or C implementation does not count as self-hosting.

## Current status — Stage 0, partial Stage 1, and compiler-core slices

**selfhost/lexer.rpr** is the first executable frontend component implemented in Reaper itself. It performs scanning in Reaper functions and uses only the language's existing string indexing, lists, comparisons, loops, flow-independent control statements and standard collection operations. The Python interpreter is only the bootstrap host that executes this Reaper program.

The stage-0 lexer currently covers ASCII identifiers and digits, keywords, decimal/integer literals, strings and escapes, comments, newlines, punctuation, operators and source positions. It returns a structured error token for an invalid character or malformed string. The Python lexer accepts Unicode identifiers; that compatibility gap is deliberate and must be closed before the self-hosted frontend can replace the reference lexer.

The bootstrap tests execute Reaper source and check its internal assertions. This proves that the tested logic runs as Reaper code under the reference interpreter; it does **not** prove a self-hosting compiler, full frontend parity, or native execution.

### Stage 1: Pratt expression parser (partial)

**selfhost/parser.rpr** implements a Pratt parser in Reaper source. It consumes the same token-array shape emitted by the bootstrap lexer and builds compact array-form expression nodes. Implemented forms are literals, names, unary expressions, grouping, list literals, function calls, indexing and infix operators. The precedence table matches the reference parser, including the **::** operator and right-associative **.

The bootstrap assertions cover arithmetic precedence, exponentiation associativity, source-located unary nodes, flow composition, nested call/list/index expressions, missing delimiters and trailing-token errors.

This is deliberately **not** a complete parser replacement: declarations, function definitions, control-flow statements, block grammar and parity with the reference AST are not yet implemented. The parser output is a stage-local representation, not the canonical AST contract. The reference frontend remains the compatibility oracle.

### Reaper-written compiler foundations

The following executable Reaper source modules extend the bootstrap beyond tokenization and expression parsing:

| Source | Implemented contract | Explicit boundary |
|---|---|---|
| selfhost/source_map.rpr | Code-point-based line starts, offset lookup, half-open spans, containment and span merging | Offsets are not UTF-8 byte offsets; backend conversion and full Unicode normalization remain separate |
| selfhost/diagnostics.rpr | Versioned diagnostic records, stable RPR- codes, severities and source-located notes | Host rendering, localization and fix-it application are not implemented here |
| selfhost/module_graph.rpr | Bounded local manifest validation and deterministic topological ordering; unknown, duplicate and cyclic dependencies are rejected | No file discovery, package registry, semantic-version solver or network access |
| selfhost/ir.rpr | Expression-subset lowering into canonical IR v1 and a verifier for register definitions, operand reads and block termination | One entry block only; complete typed AST lowering, CFG, effects, ownership and serialized IR remain pending |
| selfhost/bytecode.rpr | Expression-subset lowering into stack bytecode v1 and a verifier that simulates stack depth and validates termination | Structural verifier only; bytecode serialization, VM execution, type verification and native parity remain pending |

IR registers are function-local non-negative integer identifiers. The current IR slice rejects duplicate definitions, undefined reads, malformed operands, unknown instructions and unterminated blocks. Bytecode verification rejects stack underflow, bad argument indices and instructions after RETURN. Unsupported AST forms fail with explicit RPR-E diagnostic identifiers rather than being silently discarded.

These modules are intentionally small executable building blocks. They are not yet wired through a source-level import system, and their independent assertions do not substitute for a full end-to-end compile test.

## Bootstrap stages

| Stage | Reaper-written component | Acceptance gate |
|---|---|---|
| 0 | Lexer | Token-by-token parity for the supported language, Unicode and error locations included |
| 1 | Pratt expression parser (partial) | Complete declaration/block grammar, canonical AST parity and shared golden corpus |
| 2 | Source-map, diagnostic and local module-graph contracts (partial) | Semantic analysis, name/type resolution and differential runtime conformance |
| 3 | Expression-subset canonical IR and stack-bytecode construction/verifiers | Full AST lowering, CFG/effects/ownership verification, serialization and malformed-input coverage |
| 4 | Optimizer passes | Differential semantics, bounded fixed-point behavior and reproducible output |
| 5 | Native code-generation frontend | Generated output builds and passes the complete conformance suite |
| 6 | Bootstrap closure | Reaper compiler rebuilds itself reproducibly from a clean Stage-0 toolchain |

## Non-negotiable rules

1. Reaper implementation logic belongs in .rpr sources; host code is limited to bootstrap, platform primitives and test orchestration.
2. Keep the reference implementation as a compatibility oracle until full differential parity is demonstrated.
3. Keep the native C17 runtime/compiler track as an execution substrate during bootstrap; do not claim it is a complete runtime until the full suite passes.
4. Every stage has positive, negative, regression, resource-limit and source-location tests.
5. A stage is not complete because its source file exists. It must pass the stated acceptance gate on a clean checkout.
6. Bootstrap builds must be deterministic and record source hashes, compiler version, target and build inputs.
7. No stage may silently add filesystem, network, process, shell or hardware authority to ordinary Reaper programs.

## Immediate next work

- Close Unicode identifier and normalization parity in the self-hosted lexer.
- Expand token conformance to every keyword, operator, escape, whitespace and malformed-source case.
- Complete Reaper-written declaration, function, block and control-flow parsing.
- Define a canonical AST shared by the lexer/parser, IR lowerer and all hosts.
- Add end-to-end lexer → parser → semantic analysis → IR → bytecode tests using a single Reaper program as the fixture.
- Extend IR to multiple blocks, explicit control-flow edges, effects, regions and ownership verification.
- Add typed bytecode verification, serialization, execution and differential tests.
- Move name/type resolution, optimizer passes and compiler driver logic into Reaper in dependency order.
