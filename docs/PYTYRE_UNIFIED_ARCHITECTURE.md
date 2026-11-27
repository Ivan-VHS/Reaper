# PytyRe unified architecture

**PytyRe = Reaper + Pytyliki.** This is one reciprocal development system, not two adjacent products connected by an optional integration project.

## Canonical ownership

| Domain | Canonical owner | Shared responsibility |
|---|---|---|
| .rpr syntax, language semantics, canonical typed IR, source spans, diagnostics, compiler/runtime and language ABI | Reaper | Pytyliki supplies processor-domain requirements and validates target-specific behavior |
| CPU discovery, processor inventory, ISA/microarchitecture workbench, processor models, metrics, embedded profiles, target maps and processor verification | Pytyliki | Reaper expresses typed programs and consumes bounded processor services |
| Hardware effects, memory ordering, MMIO/IRQ/DMA intent and capability policy | Shared contract | Reaper owns language-level semantics; Pytyliki owns target constraints and hardware-domain validation; a trusted host backend owns actual device access |

This ownership model prevents two competing parsers, compilers or hardware models. Shared systems use versioned interfaces, not copied implementations with independent evolution.

## Reciprocal native paths

### Reaper consumes Pytyliki

Reaper's native adapter in `reaper/native.py` consumes `pytyliki.c-abi.v1`. The current high-level adapter supports bounded numerical operations, embedded target-profile metadata and FLASH/SRAM budget evaluation. Pytyliki's native provider also exports metadata catalogue APIs; those exports are not all wrapped as dedicated Reaper builtins yet.

Activation is explicit: the caller supplies an absolute library path and enables native FFI. There is no PATH probing, ambient library search, plugin loading or retained caller buffer.

### Pytyliki consumes Reaper

The optional native integration uses Reaper's C17 `reaper_ffi` target. Configure Pytyliki with a trusted local source checkout:

```sh
cmake -S . -B build -DREAPER_SOURCE_DIR=/absolute/path/to/Reaper
cmake --build build --parallel --target pytyliki-interop-tests
ctest --test-dir build --output-on-failure -R '^interop-abi-tests$'
```

The Pytyliki shared ABI exposes availability/version checks and wrappers for Reaper's bounded signed-i64 expression evaluation and exact selfhood lookup. Reaper is linked at build time; default Pytyliki builds do not download, discover or load Reaper.

## Compatibility and evidence

The shared machine-readable contract is `contracts/pytyre.reciprocal.v1.json`. It records component ownership, ABI direction, enablement, pinned baseline revisions, limits and the reciprocal development rule.

The integration test paths are independent and complementary:

- Reaper's live adapter test builds the real Pytyliki shared ABI and calls it through Reaper's native adapter.
- Pytyliki's native interop test links the real Reaper C17 ABI when `REAPER_SOURCE_DIR` is supplied and checks availability, version, expression evaluation and exact lookup.
- Default builds remain independently buildable and explicitly report an absent optional peer backend.

An ABI change must update the contract, the provider header, the consumer adapter, tests and both pinned cross-repository CI workflows in coordinated PRs.

## Copying, provenance and safety

The repositories are not recursively nested as Git submodules and are not bulk-copied into one another. Such a layout creates self-referential checkout chains, stale duplicated implementations and ambiguous ownership. The existing `vendor/reaper_frontend` snapshot remains a deliberately limited, attributed Apache-2.0 compatibility frontend. Full integration uses the authoritative source checkout and C ABI instead of pretending that this expression-only snapshot is the entire Reaper system.

Reaper remains Apache-2.0 and Pytyliki remains MIT. Keep each work's license and notices intact. No integration grants physical MMIO access, driver installation, firmware flashing, privilege escalation or implicit network access.

## Reciprocal development rule

A feature developed in Reaper is also PytyRe development and must be evaluated against Pytyliki's processor and target contracts. A feature developed in Pytyliki is also PytyRe development and must be evaluated against Reaper's language, typed IR, compiler and ABI contracts. Shared changes are reviewed and tested on both sides before being called complete.
