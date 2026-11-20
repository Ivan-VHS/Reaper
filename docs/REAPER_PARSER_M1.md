# REAPER parser M1 — expression AST foundation

**Status:** implemented slice; not a complete language parser.

## Included

- C17 Pratt parser for one complete expression.
- Flat, owned AST node storage with stable 32-bit node indices.
- Source line/column retained on every node.
- Integer/decimal/string/boolean/null literals and Unicode identifiers.
- Prefix arithmetic/logical operators; binary arithmetic, comparison, equality, boolean, null-coalescing and flow operators.
- Explicit precedence and right-associative exponentiation.
- Parentheses and bounded nesting depth (256).
- Rejects trailing tokens and malformed grouping; no silent recovery.

## Deliberate limits

This increment does not parse declarations, functions, blocks, types, patterns, imports or contracts. It does not resolve names, infer types, lower expressions to IR, execute expressions or generate native code. String and number payloads remain lexical text; numeric range and escape semantics are validated by later semantic stages.

The parser consumes only the REAPER token stream. МОСТ is an exact keyword-alias table: Russian keywords are canonicalized to existing REAPER tokens before parsing. There is no MOST morphology stage, domain resolver or second parser. Ordinary Russian identifiers are passed through unchanged.

## Build

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

## Next gate

M1 continuation: complete REAPER declaration/block grammar, recoverable diagnostics and complete source spans. The exact Russian keyword aliases must enter the same parser. No MOST Intent AST or scoped dictionary resolver is planned.
