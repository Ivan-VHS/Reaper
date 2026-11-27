# Processor Fabric Typed IR v1

**Status:** implemented as a bounded Reaper reference-runtime adapter over the existing Reaper SemanticGraph. This is not the legacy stack-machine bytecode IR and does not yet lower to complete HIR/MIR/LIR or emit a target executable.

## Flow

1. The local Node importer reads caller-selected source, topology, PPF graph, Hardware AST bridge and hardware-resource JSON files. It rejects symlinks, non-UTF-8 input, oversized files, schema/version mismatches, stale generations, duplicate IDs, missing references, cycles, region overlaps, invalid register ranges, untrusted effects, producer semantic claims and out-of-range spans.
2. The importer hashes the exact UTF-8 source bytes. The bridge SHA-256 and byte-length must match. Spans are kept as UTF-8 byte offsets; no text-character offset conversion is permitted.
3. Reaper's processor adapter accepts the import report plus independently resolved Reaper semantic/resource bindings produced by trusted Reaper semantic/type policy.
4. The adapter creates content-addressed SemanticNode values and connects resource/process values to exact typed input ports. SemanticGraph.validate(require_complete=True) verifies port types, effect structure and graph integrity.
5. Process depends-on edges are retained separately as control dependencies. They are not coerced into typed data edges.
6. The output contract is reaper.processor-fabric-typed-ir.v1. It records source digest, generation, semantic nodes/edges, AST spans, control dependencies, resource ownership and verification flags.

## Important distinction between IR layers

Reaper currently has a stack-oriented CanonicalIR used by its selectable bytecode VM. The Processor Fabric adapter does not serialize a fake stack program and does not claim VM bytecode emission. It builds a canonical typed semantic graph through Reaper's existing SemanticGraph/SemanticNode contracts. This typed graph is a processor IR sidecar until compiler-owned canonical HIR/MIR/LIR integration is implemented.

## Reaper-owned semantic bindings

Pytyliki can name a Hardware AST construct and link it to PPF process/resource IDs. It cannot choose the final operation type, input types, output type, effects, ownership interpretation or capability grant.

The Reaper binding provider supplies:

- operation name and fixed typed input/output signature;
- exact PPF resource/process IDs bound to input ports;
- operation effect set;
- resource value type, ownership owner, generation and optional DMA state/coherency.

The adapter requires every input port to be bound exactly once and type-equal. It rejects a source ref not listed by the validated construct graph, a resource with a stale generation, a missing semantic binding, a non-CPU-readable DMA ownership state, and any effect not in the explicit Reaper grant set.

The granted_effects input is an allowlist from Reaper project policy; merely finding an effect name in a producer report never grants it. No effect callback is invoked by this adapter.

## Local importer

Run the importer with explicit --source, --topology, --fabric, --bridge, --resources and --output path arguments. The output is created exclusively; an existing path is not overwritten. Input is local-only, regular-file-only and bounded. No network request, shell command, shared-library load, thread scheduling, MMIO map or DMA transaction occurs.

## Verification

The Node test suite covers source digests, UTF-8 spans, generation mismatches, forged producer semantic claims, graph parent cycles, missing resource references, overlapping memory regions and symlink rejection.

The Python adapter tests cover typed graph construction, source digest and generation admission, missing bindings, type mismatches, effect denial, DMA ownership denial and process dependency cycles.

A green CI run is required before promotion beyond partial. This adapter is not a native Reaper compiler pass and is not a backend qualification result.
