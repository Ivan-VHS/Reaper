# Typed Structures and Target Platforms v1

**Status:** implemented Reaper-native descriptor and layout core; source declaration syntax, canonical compiler IR integration and native aggregate ABI lowering remain separate milestones.

## Scope

This milestone adds a deterministic, versioned type descriptor model and target-platform profile model implemented in Reaper source. It is intentionally narrower than a full type checker or native ABI implementation.

The source of truth is \`selfhost/type_platform.rpr\`. The executable conformance suite is \`selfhost/type_platform_tests.rpr\`.

## Design rules

1. A type descriptor is a versioned value, not an unvalidated string.
2. A target platform is a versioned profile with explicit architecture, OS, data model, pointer size and alignment, endianness, object format, process calling ABI, service wire ABI, maximum alignment, C scalar layout, atomics and CPU features.
3. Layout is target-dependent. Pointer and C scalar sizes are not host-global constants.
4. Recursive by-value types are rejected. Recursive pointers are allowed because pointer layout does not require pointee layout.
5. Aggregate field names must be unique. Size arithmetic is checked before multiplication, addition and alignment.
6. \`packed\` changes field alignment to one; it does not silently make unaligned access safe.
7. A platform profile is descriptive metadata. It does not install drivers, grant capabilities, probe a real CPU or make an object writer available.
8. A service wire ABI is distinct from a process calling convention.

## Type descriptor schema

| Descriptor | Shape |
|---|---|
| Primitive | \`["TYPE_V1", "primitive", name]\` |
| Named | \`["TYPE_V1", "named", name]\` |
| Pointer | \`["TYPE_V1", "pointer", pointee, mutable]\` |
| Fixed array | \`["TYPE_V1", "array", element, count]\` |
| Field | \`["FIELD_V1", name, type]\` |
| Struct | \`["STRUCT_V1", name, representation, explicit_align, fields]\` |
| Union | \`["UNION_V1", name, representation, explicit_align, fields]\` |
| Enum | \`["ENUM_V1", name, underlying, variants]\` |
| Variant | \`["VARIANT_V1", name, integer_value]\` |
| Distinct | \`["DISTINCT_V1", name, underlying]\` |
| Opaque | \`["OPAQUE_V1", name, size, alignment]\` |

Aggregate representation values: \`native\`, \`C\`, \`packed\`. An explicit alignment of zero means no additional alignment request. Empty aggregates are rejected in v1.

## Platform descriptor schema

\`PLATFORM_V1\` contains, in order:

| Index | Field |
|---:|---|
| 1 | Stable platform identifier |
| 2 | Architecture |
| 3 | Operating system |
| 4 | Data model |
| 5–6 | Pointer size and alignment in bytes |
| 7 | Endianness |
| 8 | Object format |
| 9 | Process calling ABI |
| 10 | Service wire ABI |
| 11 | Maximum supported alignment |
| 12–13 | C \`long\` size and alignment |
| 14 | Atomic widths in bits |
| 15 | Declared CPU features |
| 16 | Profile status |

The profile status \`declared\` means the profile has a complete descriptive contract in this module; it is not a claim that a compiler backend or host toolchain has been validated for that target. \`profile_only\` means the profile is intentionally not ready for ABI code generation.

## Initial profiles

- Windows x86_64: LLP64, PE/COFF, Microsoft x64 calling convention, 8-byte pointers, 4-byte C long.
- Linux x86_64: LP64, ELF, System V AMD64 calling convention, 8-byte pointers, 8-byte C long.
- Linux AArch64: LP64, ELF, AAPCS64 calling convention.
- DAK x86_64: descriptive profile only. Process object format and process calling convention remain unfinalized. \`DABI64_DESKTOP_HOST_V1\` is recorded only as the service wire ABI, never as a process calling convention.

CPU features in these profiles are declared target requirements/assumptions, not runtime CPUID/HWCAP detection results. They must be refined with versioned target triples and feature sets before code generation.

## Layout behavior

\`type_layout(type, platform, definitions, stack)\` returns:

- success: \`[true, [size_bytes, alignment_bytes, field_offsets], ""]\`
- failure: \`[false, diagnostic_code, message]\`

\`type_layout_with_metadata\` adds the selected platform, endianness, object format, process calling ABI, service wire ABI and profile status.

Implemented primitives include fixed-width signed/unsigned integers, bool, f32/f64, pointer-sized integers, and selected C scalar names. Arrays, struct, union, enum, distinct and opaque layouts are supported.

## Reaper usage

\`\`\`reaper
import "type_platform.rpr"

make linux := platform_linux_x86_64()

make Vec3 := type_struct("Vec3", "native", 0, [
    type_field("x", type_primitive("f32")),
    type_field("y", type_primitive("f32")),
    type_field("z", type_primitive("f32"))
])

make layout := type_layout_with_metadata(type_named("Vec3"), linux, [Vec3])
assert(layout[0], "Vec3 layout must be valid")
emit layout[1]
\`\`\`

A larger system-data example lives in \`examples/typed_platforms.rpr\`.

## Explicit non-goals of v1

The following are not yet implemented by this milestone:

- Literal \`struct { ... }\`, \`enum { ... }\`, \`platform { ... }\` source declarations in the main Reaper parser.
- Nominal type checking in the reference checker or native C parser.
- Generics, traits/interfaces, methods, visibility/derives or field-level invariants.
- C aggregate argument/return classification, register assignment or stack frame lowering.
- Full SysV AMD64, Microsoft x64 or AAPCS64 ABI call lowering.
- ELF/PE/Mach-O object writing, linking or loading.
- Target-specific LLVM/assembler integration or execution tests on every target.
- Actual CPU feature probing or runtime capability grants.

These features must consume this versioned descriptor model rather than invent parallel metadata formats. The next compiler work is to add typed declaration nodes to the Reaper-written statement parser, normalize them into canonical typed IR with source spans, then connect target-specific layout and calling ABI classification to native lowering.

## Acceptance

Run from the repository root:

\`\`\`sh
python -m reaper selfhost/type_platform_tests.rpr
python -m reaper --check examples/typed_platforms.rpr
\`\`\`

The Python command invokes the existing reference runner to execute Reaper source. No Python implementation of the type or platform model is introduced.
