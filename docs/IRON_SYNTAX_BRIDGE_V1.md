# Reaper Iron Syntax AST bridge v1

**Canonical syntax owner:** Pytyliki  
**Consumer:** Reaper compiler/tooling  
**Status:** immutable AST envelope validation; no execution or lowering

Reaper accepts the versioned `pytyliki.iron-syntax-ast.v1` interchange document produced by Pytyliki. It verifies the exact twenty-record catalogue, schema/version, canonical owner, record identifiers, field spellings, order and source locations. The adapter returns immutable `IronSyntaxAst` and `IronRecord` values so later compiler work can retain source provenance.

This is deliberately not a second Iron lexer. Reaper does not normalize spelling, correct the user-provided `brachpass` or `verison` forms, interpret the records as runtime commands, or lower them into executable IR. `execution_performed` must be exactly `false`; unknown fields and unsupported versions are rejected rather than silently accepted.

The bridge does not authorize MMIO/DMA, device access, driver installation, privilege changes, instruction emission or firmware writes. Semantic mappings require a separate versioned language design and conformance review.

```python
from reaper.iron_syntax import decode_iron_ast

ast = decode_iron_ast(json_payload)
for record in ast.records:
    print(record.kind, record.line, record.column)
```
