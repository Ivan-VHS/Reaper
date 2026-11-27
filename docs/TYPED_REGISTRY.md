# Typed Registry v1

**Status:** implemented as a Reaper .rpr library and executable conformance example. First-class aggregate grammar and native-code lowering are separate compiler milestones.

The Typed Registry is the shared, versioned contract for data layouts, target platforms and host bindings. It is written in Reaper itself: constructors, layout computation, graph checks and diagnostics live in stdlib/typed_registry.rpr.

## Run it

With the Reaper CLI installed:

~~~sh
reaper --check examples/typed_registry.rpr
reaper examples/typed_registry.rpr
~~~

The conformance program must finish with REAPER_TYPED_REGISTRY_OK. CI runs both the static check and the program.

## Reaper declaration style

Declarations are ordinary immutable Reaper values. The API stays composable with make, craft, lists and the :: flow operator; it does not require a second configuration language.

~~~reaper
make u32 := typed["scalar"]("u32", 32, false, 4)

make GpioRegisters := typed["struct"]("GpioRegisters", [
    typed["field"]("mode", "u32", 0, "read_write", ["mmio.read", "mmio.write"]),
    typed["field"]("input", "u32", 16, "read_only", ["mmio.read"]),
    typed["field"]("output", "u32", 20, "write_one_to_set", ["mmio.write"])
], "c", 0, 0)

make DAK_X86_64 := typed["platform"](
    "DAK-x86_64", "x86_64-unknown-dak", "x86_64", "dak",
    "DABI64", 64, "little", "dabi64", "kernel",
    ["sse2"], ["mmio.read", "mmio.write", "irq"]
)
~~~

The field offset is either an explicit non-negative byte offset or -1 for ABI-computed placement. Struct representation is native, c or packed; packing and explicit alignment are independently checked.

## Type constructors

| Constructor | Contract |
|---|---|
| scalar(name, bits, signed, alignment) | Fixed-width 8/16/32/64/128-bit scalar and explicit alignment |
| pointer(name, target, address_space, mutable) | Typed pointer with target type and generic/stack/heap/static/mmio/io address space |
| array(name, element, count) | Fixed-size array; count is bounded to 1..1,048,576 |
| field(name, type, offset, access, capabilities) | Named field, placement, access policy and required capabilities |
| struct(name, fields, representation, packing, explicit_alignment) | Aggregate descriptor with deterministic ABI layout |
| enumeration(name, underlying, variants) | Integer-backed enum with unique names/values and range checks |

Scalar alignment is limited to powers of two up to 16 bytes and cannot exceed scalar width. Pointer size and alignment are taken from the selected platform. Arrays inherit their element alignment. Struct fields are placed in declaration order, with checked natural alignment, explicit offsets, packing, overlap rejection and tail padding. By-value recursive types are rejected; pointer indirection is allowed.

## Platform declarations

A platform descriptor records:

[name, triple, architecture, operating_system, abi, pointer_bits, endian, calling_convention, memory_model, features, declared_capabilities]

Supported architecture names in v1 are x86_64, aarch64, riscv64 and wasm32. Platform validation checks pointer width, byte order, memory model, ABI/calling-convention pairings, duplicate features and capability names. DABI64 is constrained to a 64-bit DAK target using the dabi64 calling convention.

The registry example contains DAK x86_64 and AArch64 target declarations. These are target contracts, not evidence that a native backend, kernel port or physical board adapter is already qualified for both targets.

## Bindings, effects and authority

A binding descriptor records:

[name, platform, kind, input_type, output_type, effects, requested_capabilities]

Kinds are function, register, service and interrupt. Effects and capabilities are separate lists. A binding must name known types and a known platform, use unique supported effects/capabilities, and request only capabilities declared by that platform profile. Each requested capability must have a matching effect. Register bindings require an MMIO read or write effect.

**A declaration never grants authority.** Platform capabilities describe the maximum contract a host may support. A trusted OS driver or host adapter must separately grant and enforce access for a specific operation. The registry does not map physical addresses, issue MMIO transactions, register interrupts, allocate DMA buffers, install drivers or execute privileged instructions.

## Validation result

validate(registry) returns:

~~~text
[ok, diagnostics, layouts]
~~~

Each diagnostic is [code, subject, message]. Each computed layout is [platform_name, type_name, byte_size, alignment, field_placements]; each field placement is [field_name, byte_offset, byte_size, effective_alignment].

Validation covers descriptor shape, duplicate names, type references, scalar widths and alignment, array bounds, pointer address spaces, enum value ranges, struct field policies and layout, by-value cycles, platform/ABI consistency, binding references, effects and capability declarations. Stable diagnostics use the RPR-REG-* namespace.

The example includes passing DAK layouts and rejection fixtures for overlapping fields, recursive by-value aggregates, inconsistent DABI64 targets and undeclared MMIO authority.

## Implementation boundary

Available now:
- Reaper .rpr constructors and validation logic in stdlib/typed_registry.rpr;
- target-aware pointer and aggregate layout calculation;
- explicit field placement, access, effects and capability contracts;
- deterministic diagnostics and executable negative conformance fixtures;
- CI coverage through the Reaper CLI.

Not yet claimed:
- dedicated struct, enum, platform or registry grammar productions;
- compile-time type resolution or integration into the canonical HIR/MIR;
- native C17/ELF lowering of these declarations;
- ownership/borrow checking, bitfield lowering or platform linker integration;
- actual device access or physical hardware qualification.

The descriptor shape is deliberately versioned and independent of the current frontend. The next compiler step is to lower equivalent source-level declarations into this same canonical contract rather than creating a competing registry.
