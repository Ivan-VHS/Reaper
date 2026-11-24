# Reaper Semantic IR

## Purpose and compatibility boundary

Reaper now has two deliberately separate intermediate representations:

- reaper.ir.CanonicalIR remains the verified stack instruction stream used by the existing VM.
- reaper.semantic_ir.SemanticIR is a versioned expression graph for semantic analysis, contract checking, diagnostics and future optimization passes.

The semantic graph does not replace the VM format and does not claim native-backend parity. Both representations can coexist while compiler work proceeds incrementally.

## Pipeline normalization

The existing :: operator remains canonical and backward compatible. -> is accepted as a readable flow-first alias and is normalized by the parser to the same AST operator. Both forms lower using one rule:

value :: function(extra) and value -> function(extra) become function(value, extra).

The piped input is always argument zero. This is a language-wide contract for semantic analysis and future runtime/backend adapters.

## Node and provenance contract

Each semantic IR node has:

- a deterministic module-local node_id;
- a typed node kind (IRVar, IRLiteral, IRList, IRIndex, IRIntrinsic or IRCall);
- a primary SourceSpan;
- a NodeOrigin with the primary range, related source ranges and optional transformation name;
- an optional inferred type, populated by later immutable analysis results rather than mutating the source AST.

Spans use half-open UTF-8 byte ranges and 1-based line/code-point columns. The lexer records byte offsets directly; it does not reconstruct them from Unicode character indices. Pipeline calls point primarily at the stage function name, while the original pipe operator and call delimiter remain related spans. Operator expressions normalize to intrinsic calls such as ge, with the operator token as their primary location.

## Type contracts

IRTypeChecker accepts explicit variable types and registered FunctionSignature contracts. This keeps external, imported and host-provided functions honest: the checker does not invent signatures for unknown functions. It checks argument count, assignability, comparison operand compatibility, named map/filter callbacks and common collection operations.

Type errors are structured IRDiagnostic values with stable codes, the originating node ID, stage and original-source span. format_diagnostic renders the same source excerpt and caret regardless of whether the expression used :: or ->.

## Current scope

The current Reaper parser supports named calls, variables, literals, lists, indexing, unary/binary operators and collection pipes. It does not yet parse anonymous fn lambdas, record literals or field access such as entry.code; those require separate grammar, AST, runtime and conformance work. The semantic IR intentionally does not fabricate those capabilities.

## Integration sequence

Lexer -> Parser/AST -> SemanticIR -> name/type/contract analysis -> optimization -> execution-IR lowering -> VM/backend

The existing bytecode lowering remains available independently. A future pass can translate verified semantic IR into the stack IR once node coverage, effects, ownership and runtime contracts have conformance tests.
