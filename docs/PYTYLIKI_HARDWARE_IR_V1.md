# Pytyliki Hardware IR v1 interoperability

## Ownership

Pytyliki is the producer and semantic owner of processor/hardware-domain syntax, register descriptors, target-specific metadata, physical dimension vectors and Hardware IR v1.

Reaper is the consumer of the versioned interchange envelope and remains the owner of its general-language CanonicalIR, interpreter/VM and shared compiler contracts. The adapter does not redefine either language.

Producer schema: `pytyliki.hardware-ir.v1`.
Consumer schema: `reaper.typed-hardware-ir.v1`.
Type-system identity: `pytyliki.dimension-vector.v1`.

## Import and verification

`reaper.pytyliki_hardware_ir.import_hardware_ir(payload)` accepts a mapping, UTF-8 JSON text or bytes. It rejects oversized payloads, unsupported schema/producer IDs, unexpected fields, invalid dimension vectors, unknown types/opcodes, duplicate symbols, invalid source spans, forward HIR references, inconsistent arithmetic dimensions, malformed register operations, access-policy violations and effect summaries that do not match the actual HIR operations.

The importer returns immutable descriptors for:
- module and target identity;
- type IDs, fixed widths and eight-axis physical dimensions;
- HIR values, stable indices, operands and source spans;
- input/derived/register/operation symbols;
- declared and inferred effect sets.

The importer is inert. It does not inspect the host, resolve a physical address, load a device, invoke an MMIO callback or grant a capability.

## CanonicalIR lowering

`lower_pure(module)` returns a pair:

- `canonical_ir`: a verified Reaper `CanonicalIR` module for the pure numeric subset;
- `hardware`: the imported, typed hardware metadata retained alongside CanonicalIR.

Only the explicit `host` target, zero inferred effects and `f64`/physical-quantity values are eligible. The current scalar Reaper CanonicalIR does not encode dimension vectors, fixed-width integer overflow rules, register permissions, or hardware effects. The adapter therefore does not erase those semantics or pretend that `u32` is the same as an unbounded interpreter number.

The test fixture lowers the physical quantity example and executes the resulting pure code through Reaper's own bytecode VM. The derived result is emitted by the existing Reaper runtime. Dimension and source metadata remain available on the returned `hardware` sidecar.

## Effect and target boundary

MMIO read/write nodes can be imported and validated as declarations, including their register width/access contract and explicit effect allowlist. They are rejected by `lower_pure` before any CanonicalIR instruction is produced. The current Reaper VM is not a hardware execution engine.

Fixed-width integer HIR is also rejected by the v1 CanonicalIR adapter because the stack IR does not yet preserve the producer's overflow/width semantics. It remains inspectable as typed Hardware IR until a matching Reaper typed-IR path exists.

No physical MMIO, DMA, IRQ, clock/power operation, firmware write, driver installation, privilege change, or board control is implemented here.

## Verification

The Python conformance tests cover:
- strict import and eight-axis dimension preservation;
- arithmetic type/dimension invariants;
- source span and effect-summary rejection;
- fixed-width integer lowering rejection;
- MMIO register/access/effect checks and pure-runtime denial;
- pure lowering, CanonicalIR verification and execution with Reaper's VM;
- payload/schema and reference bounds.

The repository CI runs these tests across the supported Python matrix. No native C17 parity for this adapter is claimed.
