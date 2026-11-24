# Source spans and canonical IR provenance

Reaper uses half-open source ranges throughout its Python reference frontend.

- Offsets are **UTF-8 byte offsets** into the exact original source buffer; the end offset is exclusive.
- Line and column coordinates are **1-based**; columns count Unicode code points, matching the lexer diagnostic convention.
- Every lexer token records its source name, byte range and ending line/column. `Span.to_dict()` provides a stable transport shape.
- AST nodes retain the token that introduced them. Lowered `IRInstruction` objects retain that token, expose its `Span`, and `CanonicalIR.source_map` returns a deterministic instruction-index mapping.
- `source_name` is inferred from the parsed source when the caller does not explicitly override it.

The native C17 frontend is extended in the same direction: tokens, AST nodes and IR nodes carry byte offsets in addition to line/column. The source identity remains a compilation-unit responsibility in that lower-level API; consumers pair offsets with the filename/source buffer used for compilation.

This contract is for provenance and diagnostics. It does not claim complete type checking, full language lowering, source-level effects, or Python/native semantic parity. Unsupported native syntax remains an explicit error rather than silently changing meaning.
