#ifndef REAPER_TEST_DABI64_ABI_H
#define REAPER_TEST_DABI64_ABI_H

#include <stdint.h>

#define DUCK_ABI_MAGIC UINT32_C(0x49424144)
#define DUCK_ABI_MAJOR 1
#define DUCK_ABI_MINOR 0

typedef enum DuckValueKind {
    DUCK_VALUE_UNIT = 0,
    DUCK_VALUE_I64 = 1
} DuckValueKind;

typedef enum DuckAbiStatus {
    DUCK_STATUS_OK = 0,
    DUCK_STATUS_BAD_ARGUMENT_LAYOUT = 18
} DuckAbiStatus;

typedef struct DuckValue {
    uint64_t payload;
    uint32_t kind;
    uint32_t flags;
} DuckValue;

typedef struct DuckCallFrame {
    uint32_t magic;
    uint16_t abi_major;
    uint16_t abi_minor;
    uint32_t byte_size;
    uint32_t argument_count;
    uint32_t capture_count;
    uint32_t flags;
    uint32_t reserved0;
    uint32_t reserved1;
    const DuckValue *arguments;
    const DuckValue *captures;
} DuckCallFrame;

typedef struct DuckCallResult {
    DuckValue value;
} DuckCallResult;

_Static_assert(sizeof(DuckValue) == 16, "DABI64 value size");
_Static_assert(sizeof(DuckCallFrame) == 48, "DABI64 call-frame size");
_Static_assert(sizeof(DuckCallResult) == 16, "DABI64 result size");

#endif
