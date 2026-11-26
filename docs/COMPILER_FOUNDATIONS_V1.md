# Reaper compiler foundations v1

**Status:** partial, review-gated implementation.
**Language:** Reaper source.
**Reference host:** Python interpreter and conservative type checker.
**Native backend:** experimental scalar C17 AOT; aggregate, generic and effect lowering are not claimed.

This increment connects typed function contracts, generic types, explicit result values, effect declarations, source-level ownership checks, typed intermediate representations, and offline package-lock contracts. It deliberately does not promote these slices to a complete systems compiler.

## 1. Typed craft signatures

The reference grammar accepts parameter and return annotations, generic parameters, built-in trait bounds, reference parameters, and explicit effect sets:

    craft identity<T>(value: T) -> T {
        yield value
    }

    craft twice<T: Numeric>(value: T) -> T {
        yield value * 2
    }

    craft parse_count(value: Int) -> Result<Int, Text> effects() {
        when value >= 0 {
            yield ok(value)
        } otherwise {
            yield err("negative value")
        }
    }

The parameter names remain in the compatibility AST shape. A separate AST metadata record preserves parameter types, return type, generic parameters, trait bounds, and effects. This avoids breaking the existing tree-walk runtime, bytecode VM, and scalar AOT function representation.

The current built-in trait-bound vocabulary is Numeric, Copy, Clone, Eq, Ord, and Display. Generic substitution and call-site argument checks are partial and conservative. User-defined trait declarations, impl coherence, associated types, specialization, and monomorphized native generic code are not implemented.

## 2. Aggregate and target types

The stacked typed-layout foundation provides versioned descriptors for primitive, named, pointer, fixed-array, struct, union, enum, distinct, and opaque types. Target profiles carry data model, pointer size/alignment, endianness, object format, process calling ABI, service wire ABI, atomic widths, and declared CPU features.

The statement-parser layer also recognizes basic struct and platform declarations. The descriptor model is more expressive than the current source grammar. In particular, enum/trait/impl declarations and generic aggregate syntax are not yet integrated into the production Python parser or native C17 compiler.

## 3. Result and Option

The reference runtime now exposes immutable tagged ResultValue and OptionValue values with constructors and checked accessors:

- ok, err, result_is_ok, result_is_err, result_value, result_error;
- some, none, option_is_some, option_is_none, option_value, option_or;
- map_ok, map_err, zip_ok, and zip3_ok.

Unwrapping the wrong variant is an explicit runtime error. The static checker recognizes Result<T, E> and Option<T> and checks their generic arity in typed signatures. The ? propagation operator, exhaustive match, Result/Option native layout, and VM/AOT lowering remain open gates.

## 4. Ownership, borrowing, regions, and drop

selfhost/ownership.rpr implements a bounded executable semantic model:

- unique owned-resource declarations;
- nested region ancestry and escape checks;
- overlapping shared borrows;
- rejection of mutable/shared overlap;
- deterministic reverse-declaration drop order.

This is a Reaper-written verifier model with positive and negative fixtures. It is not yet the production borrow checker, does not track moves across every control-flow path, and is not wired into the runtime, bytecode verifier, or native cleanup lowering. No unsafe pointer or MMIO authority is added by this change.

## 5. Effects and capabilities

Typed functions may declare effects with effects(console, filesystem, native, ...). The reference type checker validates effect names and ensures that explicitly restricted callers declare the effects required by their callees. Built-in effect mapping currently covers console, filesystem, native FFI, allocation, and consent/unsafe operations.

This is a static effect contract, not a capability grant. Actual filesystem, network, process, device, and system operations continue to require their existing explicit runtime or host capability boundary. Network/process/device dispatch and host policy proofs are not added by this increment.

## 6. HIR to MIR to LIR

selfhost/typed_pipeline.rpr defines a bounded scalar-expression pipeline:

- HIR nodes carry type names and half-open source spans;
- HIR lowering emits deterministic, topologically ordered MIR instructions;
- MIR verification checks dense IDs, source spans, and input dominance;
- MIR lowering emits a target-independent virtual-register LIR;
- LIR verification retains the source map.

This is an executable compiler slice, not yet a whole-program IR. Control-flow graphs, phi nodes, generic instantiation, effect/ownership metadata on every instruction, optimization passes, register allocation, and backend-specific instruction selection remain future acceptance gates.

## 7. Target-aware backends

The typed target profiles describe supported data layouts and declared process/service ABIs. They do not by themselves compile or link a target program.

A separate open review branch, PR #239, contains an x86-64 ELF ET_REL writer and bounded static ET_EXEC linker. It is not part of this stacked change and must pass its own CI/review before being treated as merged capability. PE/COFF, Mach-O, and WebAssembly object writers and end-to-end source-to-object lowering remain unimplemented.

## 8. Packages and reproducibility

selfhost/package_contract.rpr validates explicit package identity, semantic versions, pinned dependency digests, lock/manifest agreement, and offline-cache digest presence. It performs no download, install, registry publication, or network access.

The existing toolchain inventory lock hashes selected local compiler executables. A complete package manager still needs content-addressed storage, dependency graph resolution, secure archive extraction, signatures/provenance, transactional install/uninstall, workspace manifests, registry client policy, and independent offline tests. Lock contract validation is not package installation.

## 9. Developer tooling

The repository already contains a stdio LSP with diagnostics, completion, hover, symbols, navigation, semantic tokens and formatting; a formatter; DAP/debugging support; and a CLI --profile report for elapsed time and interpreter steps. These are useful existing foundations, not yet a complete production IDE toolchain. Typed-signature hover, whole-program cross-file analysis, CPU/memory sampling, p95/p99 tracing, and native-backend source-map debugging remain separate work.

## 10. Self-hosting

The Reaper-written lexer, expression/statement parser, type/ownership/package contracts, and typed HIR/MIR/LIR slice execute under the Python reference host in the current bootstrap workflow. That is real Reaper source execution, but not self-hosting closure.

The compiler is not yet able to compile itself, bootstrap from a minimal independent stage, reproduce its own binary, or validate native output against the full language conformance suite. The exit gate remains clean Stage-0 to Stage-1 to Stage-2 rebuild parity with recorded compiler, target, source hash, toolchain lock, and deterministic artifacts.

## Acceptance commands

The focused review workflow runs:

    python -m unittest tests.test_typecheck tests.test_typed_results tests.test_compiler_foundations -v
    python -m reaper selfhost/type_system.rpr
    python -m reaper selfhost/ownership.rpr
    python -m reaper selfhost/typed_pipeline.rpr
    python -m reaper selfhost/package_contract.rpr

Repository-wide Python CI, native C/CTest, architecture contracts, security checks, and the stacked parent PR checks remain required before merge. A queued or skipped GitHub job is not a passing result.

## Capability summary

| Area | Current increment | Still required |
|---|---|---|
| Typed craft | parameter/return syntax, generic variables, basic trait bounds | AST/VM/AOT contract parity, user traits, generic native lowering |
| struct/enum/trait/impl | typed layout descriptors and basic struct declarations | complete declaration grammar, semantic resolution, ABI lowering |
| Result/Option | reference runtime values and static generic arity | ?, exhaustive matching, VM/AOT |
| Ownership | Reaper verifier model | CFG move/borrow checker and integrated cleanup |
| Effects | typed effect declarations and call checks | host-enforced end-to-end capabilities |
| HIR/MIR/LIR | scalar expression slice with spans | whole-program CFG/optimization/codegen |
| Backends | target descriptors; separate ELF review work | merged end-to-end ELF, PE, Mach-O, WASM |
| Packages | manifest/lock/offline digest checks | full transactional package manager and registry |
| Tooling | LSP, formatter, DAP, basic profile | typed semantic services and production profiler |
| Self-hosting | Reaper-written frontend and compiler slices | independent bootstrap and reproducible compiler rebuild |

