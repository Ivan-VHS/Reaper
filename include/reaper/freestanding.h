#ifndef REAPER_FREESTANDING_H
#define REAPER_FREESTANDING_H

/*
 * Reaper freestanding system interface.
 *
 * This header uses compiler-provided integer types and builtins. It does not
 * include libc headers, allocate memory implicitly, or start a runtime.
 * Hardware access is intentionally architecture-specific and must only be
 * called from code running at the required privilege level.
 */

typedef __UINT8_TYPE__ rpr_u8;
typedef __UINT16_TYPE__ rpr_u16;
typedef __UINT32_TYPE__ rpr_u32;
typedef __UINT64_TYPE__ rpr_u64;
typedef __INT8_TYPE__ rpr_i8;
typedef __INT16_TYPE__ rpr_i16;
typedef __INT32_TYPE__ rpr_i32;
typedef __INT64_TYPE__ rpr_i64;
typedef __SIZE_TYPE__ rpr_usize;
typedef __UINTPTR_TYPE__ rpr_uptr;

#define RPR_NULL ((void *)0)
#define RPR_ARRAY_LEN(items) (sizeof(items) / sizeof((items)[0]))
#define RPR_NORETURN __attribute__((noreturn))
#define RPR_PACKED __attribute__((packed))
#define RPR_ALIGNED(value) __attribute__((aligned(value)))
#define RPR_SECTION(name) __attribute__((section(name)))
#define RPR_USED __attribute__((used))
#define RPR_ALWAYS_INLINE __attribute__((always_inline)) inline
#define RPR_STATIC_ASSERT(condition, message) _Static_assert((condition), message)
#define RPR_SIZEOF(type) sizeof(type)
#define RPR_ALIGNOF(type) __alignof__(type)
#define RPR_OFFSETOF(type, member) __builtin_offsetof(type, member)

#if defined(__x86_64__) && (defined(__clang__) || defined(__GNUC__))
#define RPR_SYSV_ABI __attribute__((sysv_abi))
#define RPR_WIN64_ABI __attribute__((ms_abi))
#define RPR_INTERRUPT_ABI __attribute__((interrupt))
#else
#define RPR_SYSV_ABI
#define RPR_WIN64_ABI
#define RPR_INTERRUPT_ABI
#endif

#define RPR_MEMORY_RELAXED __ATOMIC_RELAXED
#define RPR_MEMORY_ACQUIRE __ATOMIC_ACQUIRE
#define RPR_MEMORY_RELEASE __ATOMIC_RELEASE
#define RPR_MEMORY_ACQ_REL __ATOMIC_ACQ_REL
#define RPR_MEMORY_SEQ_CST __ATOMIC_SEQ_CST

typedef struct {
    rpr_u32 value;
} rpr_atomic_u32;

typedef struct {
    rpr_u64 value;
} rpr_atomic_u64;

static RPR_ALWAYS_INLINE rpr_u32
rpr_atomic_load_u32(const rpr_atomic_u32 *value, int order) {
    return __atomic_load_n(&value->value, order);
}

static RPR_ALWAYS_INLINE void
rpr_atomic_store_u32(rpr_atomic_u32 *value, rpr_u32 desired, int order) {
    __atomic_store_n(&value->value, desired, order);
}

static RPR_ALWAYS_INLINE int
rpr_atomic_compare_exchange_u32(rpr_atomic_u32 *value, rpr_u32 *expected,
                                rpr_u32 desired, int success_order,
                                int failure_order) {
    return __atomic_compare_exchange_n(
        &value->value, expected, desired, 0, success_order, failure_order
    );
}

static RPR_ALWAYS_INLINE rpr_u64
rpr_atomic_load_u64(const rpr_atomic_u64 *value, int order) {
    return __atomic_load_n(&value->value, order);
}

static RPR_ALWAYS_INLINE void
rpr_atomic_store_u64(rpr_atomic_u64 *value, rpr_u64 desired, int order) {
    __atomic_store_n(&value->value, desired, order);
}

static RPR_ALWAYS_INLINE int
rpr_atomic_compare_exchange_u64(rpr_atomic_u64 *value, rpr_u64 *expected,
                                rpr_u64 desired, int success_order,
                                int failure_order) {
    return __atomic_compare_exchange_n(
        &value->value, expected, desired, 0, success_order, failure_order
    );
}

static RPR_ALWAYS_INLINE void rpr_memory_fence(int order) {
    __atomic_thread_fence(order);
}

typedef struct {
    rpr_atomic_u32 state;
} rpr_spinlock;

#define RPR_SPINLOCK_INIT { { 0u } }

static RPR_ALWAYS_INLINE void rpr_spin_lock(rpr_spinlock *lock) {
    for (;;) {
        rpr_u32 expected = 0u;
        if (rpr_atomic_compare_exchange_u32(
                &lock->state, &expected, 1u,
                RPR_MEMORY_ACQUIRE, RPR_MEMORY_RELAXED)) {
            return;
        }
#if defined(__x86_64__) || defined(__i386__)
        __asm__ volatile("pause" ::: "memory");
#elif defined(__aarch64__)
        __asm__ volatile("yield" ::: "memory");
#else
        __asm__ volatile("" ::: "memory");
#endif
    }
}

static RPR_ALWAYS_INLINE void rpr_spin_unlock(rpr_spinlock *lock) {
    rpr_atomic_store_u32(&lock->state, 0u, RPR_MEMORY_RELEASE);
}

/* MMIO accesses must use volatile-qualified pointers. */
static RPR_ALWAYS_INLINE rpr_u8
rpr_mmio_read8(volatile const rpr_u8 *address) {
    return *address;
}

static RPR_ALWAYS_INLINE rpr_u16
rpr_mmio_read16(volatile const rpr_u16 *address) {
    return *address;
}

static RPR_ALWAYS_INLINE rpr_u32
rpr_mmio_read32(volatile const rpr_u32 *address) {
    return *address;
}

static RPR_ALWAYS_INLINE rpr_u64
rpr_mmio_read64(volatile const rpr_u64 *address) {
    return *address;
}

static RPR_ALWAYS_INLINE void
rpr_mmio_write8(volatile rpr_u8 *address, rpr_u8 value) {
    *address = value;
}

static RPR_ALWAYS_INLINE void
rpr_mmio_write16(volatile rpr_u16 *address, rpr_u16 value) {
    *address = value;
}

static RPR_ALWAYS_INLINE void
rpr_mmio_write32(volatile rpr_u32 *address, rpr_u32 value) {
    *address = value;
}

static RPR_ALWAYS_INLINE void
rpr_mmio_write64(volatile rpr_u64 *address, rpr_u64 value) {
    *address = value;
}

/*
 * A caller-owned bump arena. Allocation is explicit and fails rather than
 * growing a heap. The arena must be backed by suitably aligned writable RAM.
 */
typedef struct {
    rpr_u8 *memory;
    rpr_usize capacity;
    rpr_usize used;
} rpr_bump_arena;

static RPR_ALWAYS_INLINE int
rpr_is_power_of_two(rpr_usize value) {
    return value != 0u && (value & (value - 1u)) == 0u;
}

static RPR_ALWAYS_INLINE void *
rpr_bump_alloc(rpr_bump_arena *arena, rpr_usize size, rpr_usize alignment) {
    if (arena == RPR_NULL || arena->memory == RPR_NULL ||
        !rpr_is_power_of_two(alignment)) {
        return RPR_NULL;
    }

    rpr_uptr base = (rpr_uptr)arena->memory;
    if (arena->used > arena->capacity || base > (rpr_uptr)-1 - arena->used) {
        return RPR_NULL;
    }
    rpr_uptr current = base + arena->used;
    rpr_uptr mask = (rpr_uptr)alignment - 1u;
    if (current > (rpr_uptr)-1 - mask) {
        return RPR_NULL;
    }
    rpr_uptr aligned = (current + mask) & ~mask;
    rpr_usize padding = (rpr_usize)(aligned - current);
    if (padding > arena->capacity - arena->used) {
        return RPR_NULL;
    }
    rpr_usize offset = arena->used + padding;
    if (size > arena->capacity - offset) {
        return RPR_NULL;
    }

    arena->used = offset + size;
    return (void *)aligned;
}

static RPR_ALWAYS_INLINE void rpr_bump_reset(rpr_bump_arena *arena) {
    if (arena != RPR_NULL) {
        arena->used = 0u;
    }
}

#if defined(__x86_64__) || defined(__i386__)
static RPR_ALWAYS_INLINE void rpr_x86_out8(rpr_u16 port, rpr_u8 value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port) : "memory");
}

static RPR_ALWAYS_INLINE rpr_u8 rpr_x86_in8(rpr_u16 port) {
    rpr_u8 value;
    __asm__ volatile("inb %1, %0" : "=a"(value) : "Nd"(port) : "memory");
    return value;
}

static RPR_ALWAYS_INLINE void rpr_x86_disable_interrupts(void) {
    __asm__ volatile("cli" ::: "memory");
}

static RPR_ALWAYS_INLINE void rpr_x86_enable_interrupts(void) {
    __asm__ volatile("sti" ::: "memory");
}

static RPR_ALWAYS_INLINE void rpr_x86_invalidate_page(const void *address) {
    __asm__ volatile("invlpg (%0)" : : "r"(address) : "memory");
}

static RPR_ALWAYS_INLINE void rpr_x86_halt(void) {
    __asm__ volatile("hlt" ::: "memory");
}

static RPR_ALWAYS_INLINE rpr_uptr rpr_x86_read_cr3(void) {
    rpr_uptr value;
    __asm__ volatile("mov %%cr3, %0" : "=r"(value) :: "memory");
    return value;
}

static RPR_ALWAYS_INLINE void rpr_x86_write_cr3(rpr_uptr value) {
    __asm__ volatile("mov %0, %%cr3" :: "r"(value) : "memory");
}

static RPR_ALWAYS_INLINE rpr_u64 rpr_x86_read_msr(rpr_u32 index) {
    rpr_u32 low;
    rpr_u32 high;
    __asm__ volatile("rdmsr" : "=a"(low), "=d"(high) : "c"(index));
    return ((rpr_u64)high << 32u) | low;
}

static RPR_ALWAYS_INLINE void rpr_x86_write_msr(rpr_u32 index, rpr_u64 value) {
    rpr_u32 low = (rpr_u32)value;
    rpr_u32 high = (rpr_u32)(value >> 32u);
    __asm__ volatile("wrmsr" :: "c"(index), "a"(low), "d"(high) : "memory");
}
#endif

#if defined(__aarch64__)
static RPR_ALWAYS_INLINE void rpr_aarch64_dmb_ish(void) {
    __asm__ volatile("dmb ish" ::: "memory");
}

static RPR_ALWAYS_INLINE void rpr_aarch64_dsb_sy(void) {
    __asm__ volatile("dsb sy" ::: "memory");
}

static RPR_ALWAYS_INLINE void rpr_aarch64_isb(void) {
    __asm__ volatile("isb" ::: "memory");
}

static RPR_ALWAYS_INLINE void rpr_aarch64_wait_for_interrupt(void) {
    __asm__ volatile("wfi" ::: "memory");
}

static RPR_ALWAYS_INLINE rpr_u64 rpr_aarch64_read_ttbr0_el1(void) {
    rpr_u64 value;
    __asm__ volatile("mrs %0, ttbr0_el1" : "=r"(value));
    return value;
}

static RPR_ALWAYS_INLINE void rpr_aarch64_write_ttbr0_el1(rpr_u64 value) {
    __asm__ volatile("msr ttbr0_el1, %0" :: "r"(value) : "memory");
}
#endif

#if defined(__riscv)
static RPR_ALWAYS_INLINE void rpr_riscv_memory_fence(void) {
    __asm__ volatile("fence iorw, iorw" ::: "memory");
}

static RPR_ALWAYS_INLINE void rpr_riscv_wait_for_interrupt(void) {
    __asm__ volatile("wfi" ::: "memory");
}
#endif

#endif
