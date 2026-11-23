#ifndef REAPER_HARDWARE_H
#define REAPER_HARDWARE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Hardware access is delegated to a host-supplied bus adapter. This API
 * validates descriptors and capabilities; it never maps or dereferences a
 * physical address by itself.
 */

typedef enum {
    REAPER_HW_SPACE_INVALID = 0,
    REAPER_HW_SPACE_MMIO = 1
} ReaperHwSpace;

typedef enum {
    REAPER_HW_ACCESS_INVALID = 0,
    REAPER_HW_ACCESS_READ_ONLY,
    REAPER_HW_ACCESS_WRITE_ONLY,
    REAPER_HW_ACCESS_READ_WRITE,
    REAPER_HW_ACCESS_WRITE_ONE_TO_CLEAR,
    REAPER_HW_ACCESS_WRITE_ONE_TO_SET
} ReaperHwAccess;

typedef enum {
    REAPER_HW_ENDIAN_NATIVE = 0,
    REAPER_HW_ENDIAN_LITTLE,
    REAPER_HW_ENDIAN_BIG
} ReaperHwEndian;

typedef enum {
    REAPER_HW_ORDER_INVALID = 0,
    REAPER_HW_ORDER_RELAXED,
    REAPER_HW_ORDER_ACQUIRE,
    REAPER_HW_ORDER_RELEASE,
    REAPER_HW_ORDER_SEQ_CST
} ReaperHwMemoryOrder;

typedef enum {
    REAPER_HW_OK = 0,
    REAPER_HW_INVALID_ARGUMENT,
    REAPER_HW_UNSUPPORTED_SPACE,
    REAPER_HW_INVALID_REGION,
    REAPER_HW_INVALID_REGISTER,
    REAPER_HW_OUT_OF_BOUNDS,
    REAPER_HW_MISALIGNED,
    REAPER_HW_ACCESS_DENIED,
    REAPER_HW_INVALID_MEMORY_ORDER,
    REAPER_HW_BUS_FAILURE
} ReaperHwStatus;

enum {
    REAPER_HW_CAP_MMIO_READ = UINT32_C(1) << 0,
    REAPER_HW_CAP_MMIO_WRITE = UINT32_C(1) << 1
};

typedef struct {
    uint64_t base;
    uint64_t size;
    ReaperHwSpace space;
} ReaperHwRegion;

typedef struct {
    const char *name;
    uint64_t offset;
    uint8_t width_bits;
    ReaperHwAccess access;
    ReaperHwEndian endian;
    uint32_t required_capabilities;
} ReaperHwRegister;

typedef struct {
    ReaperHwStatus status;
    uint64_t address;
    char message[160];
} ReaperHwError;

/*
 * The adapter is normally implemented by a trusted OS driver, platform HAL,
 * or a simulator. Return non-zero on success. Implementations must honour
 * the requested width, byte order and memory-order contract.
 */
typedef struct {
    void *context;
    int (*read)(void *context, ReaperHwSpace space, uint64_t address,
                uint8_t width_bits, ReaperHwEndian endian,
                ReaperHwMemoryOrder order, uint64_t *value);
    int (*write)(void *context, ReaperHwSpace space, uint64_t address,
                 uint8_t width_bits, ReaperHwEndian endian,
                 ReaperHwMemoryOrder order, uint64_t value);
} ReaperHwBus;

ReaperHwStatus reaper_hw_region_validate(
    const ReaperHwRegion *region,
    ReaperHwError *error
);

ReaperHwStatus reaper_hw_register_validate(
    const ReaperHwRegion *region,
    const ReaperHwRegister *reg,
    uint64_t *absolute_address,
    ReaperHwError *error
);

ReaperHwStatus reaper_hw_read(
    const ReaperHwBus *bus,
    const ReaperHwRegion *region,
    const ReaperHwRegister *reg,
    uint32_t granted_capabilities,
    ReaperHwMemoryOrder order,
    uint64_t *value,
    ReaperHwError *error
);

ReaperHwStatus reaper_hw_write(
    const ReaperHwBus *bus,
    const ReaperHwRegion *region,
    const ReaperHwRegister *reg,
    uint32_t granted_capabilities,
    ReaperHwMemoryOrder order,
    uint64_t value,
    ReaperHwError *error
);

const char *reaper_hw_status_name(ReaperHwStatus status);

#ifdef __cplusplus
}
#endif

#endif
