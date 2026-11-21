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
