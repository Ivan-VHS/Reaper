# DuckOS target: boot-info v1 contract

**Status:** executable scalar specification and reference/AOT conformance fixtures  
**Runtime:** Reaper reference interpreter and experimental C17 AOT subset  
**Target OS:** DuckOS  
**Source:** `targets/duckos/boot_contract_v1.rpr`

## Purpose

This target brings a bounded part of DuckOS's boot handoff contract into Reaper source. It models the fixed-width unsigned address arithmetic used by `foundation/boot_info.c` without relying on Reaper's signed i64 arithmetic: each u64 value is represented as a pair of validated u32 words.

The source covers:

- u32/u64 range validation and overflow-safe u64 addition;
- half-open u64 range ordering and overlap checks;
- memory-region type and individual region validation;
- adjacency/order checks for consecutive memory regions;
- exact 32-by-32-bit multiplication into a u64 pair for framebuffer-size validation;
- framebuffer completeness, pitch, pixel format and backing-size checks;
- the v1 handoff header version, fixed structure-size and memory-region-count checks;
- a two-region fixture validator whose status values match the existing DuckOS C contract.

## Verification

The Reaper test suite compiles the target source through both the reference runtime and the experimental native AOT subset:

```sh
python -m unittest tests.test_duckos_target -v
python -m reaper --check --syntax-only targets/duckos/boot_contract_v1.rpr
python -m reaper targets/duckos/boot_contract_v1.rpr
```

The DuckOS superproject runs the same fixture matrix beside the C implementation. Its CTest bridge compares the exact status stream from the Reaper reference runtime, the Reaper native executable and a C harness linked to `duckos_boot_contract`.

## Deliberate boundary

This is not yet a replacement for `foundation/boot_info.c` and is not a freestanding kernel object. The native Reaper backend currently emits hosted C17 and has a scalar-only language subset; it does not yet provide records, general collections, a complete unsigned integer type system, target-specific calling conventions, direct ELF/PE object generation, a linker script contract or bootloader entry points.

The fixture validator currently models two memory regions because the checked scalar subset has no array/record representation. The reusable region helpers operate on full split-u64 values, while the C implementation remains authoritative for arbitrary maps up to `DUCKOS_BOOT_MAX_MEMORY_REGIONS`.

The next safe expansion gate is to add typed records and bounded collections to Reaper, expose a versioned DuckOS boot ABI declaration, and then extend differential tests to arbitrary 1–256 entry maps before considering a freestanding backend. Until those gates pass, DuckOS keeps its tested C boot contract and Reaper provides a second, independently executable specification.
