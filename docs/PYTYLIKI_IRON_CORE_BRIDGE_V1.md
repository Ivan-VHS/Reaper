# Pytyliki Iron Core → Reaper bridge v1

**Status:** native metadata adapter and stable marker catalogue  
**Upstream source:** Pytyliki pytyliki.iron-core-ast.v1  
**Reaper role:** canonical language semantics, typed IR, source-map and ABI owner  
**Maturity:** structural metadata import only; no Iron Core statement lowering

## Boundary

Pytyliki owns the exact twenty marker spellings, source framing and processor/hardware AST. Reaper consumes a schema-validated block projection through a small native C17 adapter. The adapter maps stable semantic IDs to coarse semantic classes and preserves byte offsets, body ranges and line numbers.

Reaper's current scalar IR is not yet a suitable representation for hardware plans, interrupt contexts, MMIO, DMA, scheduling or target-specific operations. The bridge therefore does not invent IR opcodes or imply that the scalar VM can execute these constructs.

## Import contract

- Accept only schema version 1 and source documents up to one MiB.
- Accept at most 64 block records.
- Require a version label, consistency policy declaration and source verification claim.
- Resolve each semantic_id against the closed twenty-entry catalogue.
- Reject unknown IDs, delimiter/metadata IDs used as blocks, unclosed blocks and invalid source ranges.
- Preserve source byte offsets and line numbers exactly. AST v1 has no columns, so the bridge does not fabricate them.
- Treat verificated as an untrusted source claim. It is not a CI status, signature or approval.

## Semantic classes

| Class | Markers | Reaper responsibility |
|---|---|---|
| framing | module root, block close | Source document boundaries; not imported as executable nodes |
| context | core, system, level | Typed contexts and target-capability checks |
| plan | selective, operation, massive, start, new-work, concrete, utility, unify, brachpass, tournament, jump, connective | Future typed plan nodes with explicit effects and resource budgets |
| policy | CC based rules | Versioned policy evidence and consistency gates |
| source-metadata | version, verification claim | Provenance only; no authority or privilege |

## Source maps and IR

The bridge returns a ReaperIronSourceAnchor with exact source byte range and source line. This is an anchor, not a substitute for Reaper's complete Span/SourceMap; columns and token-level spans must be recovered from the source document by a future Reaper parser adapter.

No typed lowering, optimization, VM execution, machine-code generation, ABI call, processor access, MMIO/DMA, driver operation or firmware write is performed. Future lowering work must add typed IR nodes, effect/capability checks, target contracts, diagnostics and conformance tests before executable support is claimed.

## Validation

The C17 library exposes reaper_iron_import, marker lookup and the full marker catalogue. CTest covers catalog completeness, preserved byte/line anchors, invalid schema versions, unknown markers, open blocks, invalid source ranges and mandatory metadata. Schema: schemas/reaper.pytyliki-iron-core-bridge.v1.schema.json.
