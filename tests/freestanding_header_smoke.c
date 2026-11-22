#include "reaper/freestanding.h"

typedef struct RPR_PACKED {
    rpr_u16 limit;
    rpr_u64 base;
} ReaperPackedDescriptor;

typedef struct RPR_ALIGNED(4096) {
    rpr_u8 bytes[4096];
} ReaperPage;

RPR_STATIC_ASSERT(sizeof(ReaperPackedDescriptor) == 10u, "packed descriptor size");
RPR_STATIC_ASSERT(RPR_ALIGNOF(ReaperPackedDescriptor) == 1u, "packed descriptor alignment");
RPR_STATIC_ASSERT(sizeof(ReaperPage) == 4096u, "page size");
RPR_STATIC_ASSERT(RPR_ALIGNOF(ReaperPage) == 4096u, "page alignment");

RPR_SECTION(".rodata.reaper_smoke")
RPR_USED static const rpr_u64 reaper_smoke_marker = 0x5250524652454555ull;

static rpr_u8 arena_storage[128] RPR_ALIGNED(16);
static rpr_atomic_u32 state32;
static rpr_atomic_u64 state64;

rpr_u32 reaper_freestanding_header_smoke(void) {
    rpr_u32 expected = 0u;
    rpr_u64 expected64 = 0u;
    rpr_bump_arena arena = { arena_storage, sizeof(arena_storage), 0u };

    rpr_atomic_store_u32(&state32, 1u, RPR_MEMORY_RELEASE);
    rpr_atomic_store_u64(&state64, 2u, RPR_MEMORY_RELEASE);
    (void)rpr_atomic_compare_exchange_u32(
        &state32, &expected, 3u, RPR_MEMORY_ACQ_REL, RPR_MEMORY_ACQUIRE
    );
    (void)rpr_atomic_compare_exchange_u64(
        &state64, &expected64, 4u, RPR_MEMORY_ACQ_REL, RPR_MEMORY_ACQUIRE
    );
    rpr_memory_fence(RPR_MEMORY_SEQ_CST);

    if (rpr_bump_alloc(&arena, 8u, 8u) == RPR_NULL) {
        return 0u;
    }

#if defined(__x86_64__)
    return (rpr_u32)(rpr_atomic_load_u32(&state32, RPR_MEMORY_ACQUIRE) +
                     (rpr_atomic_load_u64(&state64, RPR_MEMORY_ACQUIRE) & 0xffu) +
                     (rpr_x86_read_cr3() & 0xffu));
#elif defined(__aarch64__)
    rpr_aarch64_dmb_ish();
    rpr_aarch64_isb();
    return (rpr_u32)(rpr_atomic_load_u32(&state32, RPR_MEMORY_ACQUIRE) +
                     (rpr_aarch64_read_ttbr0_el1() & 0xffu));
#elif defined(__riscv)
    rpr_riscv_memory_fence();
    return rpr_atomic_load_u32(&state32, RPR_MEMORY_ACQUIRE);
#else
    return rpr_atomic_load_u32(&state32, RPR_MEMORY_ACQUIRE);
#endif
}
