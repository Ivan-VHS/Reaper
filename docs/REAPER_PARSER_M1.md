# Native parser M1

**Status:** implemented slice, not a complete language parser.

| Included | Excluded |
|---|---|
| C17 Pratt parser for one expression | declaration/block grammar |
| owned flat AST, 32-bit node indices | name/type resolution |
| source line/column per node | runtime execution |
| literals, Unicode identifiers, operators | native code generation |
| bounded nesting depth 256 | complete language implementation |

Malformed grouping and trailing tokens fail explicitly. MOST exact aliases canonicalize to REAPER tokens before this parser. CMake/CTest verifies the supported slice.

The parser itself still accepts one expression, not a complete program. A separate, limited backend now lowers signed i64 expressions (integer literals, unary signs and binary `+`, `-`, `*`, `/`) through verified IR to x86-64 System V ELF assembly. This does not expand the parser grammar to declarations or blocks. See [Native compiler](NATIVE_COMPILER.md) for the backend contract and target limits.
