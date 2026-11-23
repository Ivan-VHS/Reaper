#ifndef REAPER_DUCKOS_ABI_H
#define REAPER_DUCKOS_ABI_H

#include <stddef.h>
#include <stdint.h>

#define REAPER_DABI64_MAJOR 1u
#define REAPER_DABI64_MINOR 0u
#define REAPER_DABI64_MAGIC UINT32_C(0x49424144)
#define REAPER_DABI64_NOTE_TYPE UINT32_C(0x44414249)
#define REAPER_DABI64_ELF_OSABI 0xD5u

/* Shared names used by target-independent code and the DABI64 ELF note writer. */
#define REAPER_DUCK_ABI_MAJOR REAPER_DABI64_MAJOR
#define REAPER_DUCK_ABI_MINOR REAPER_DABI64_MINOR
#define REAPER_DUCK_ABI_NOTE_TYPE REAPER_DABI64_NOTE_TYPE
#define REAPER_DUCK_ABI_ARCH_X86_64 1u
#define REAPER_DUCK_ABI_NOTE_FLAGS 0u

typedef enum ReaperDuckValueKind {
    REAPER_DUCK_VALUE_UNIT = 0,
    REAPER_DUCK_VALUE_I64 = 1
} ReaperDuckValueKind;

typedef struct ReaperDuckValue {
    uint64_t payload;
    uint32_t kind;
    uint32_t flags;
} ReaperDuckValue;

typedef struct ReaperDuckCallFrame {
    uint32_t magic;
    uint16_t abi_major;
    uint16_t abi_minor;
    uint32_t byte_size;
    uint32_t argument_count;
    uint32_t capture_count;
    uint32_t flags;
    uint32_t reserved0;
    uint32_t reserved1;
    const ReaperDuckValue *arguments;
    const ReaperDuckValue *captures;
} ReaperDuckCallFrame;

typedef struct ReaperDuckCallResult {
    ReaperDuckValue value;
} ReaperDuckCallResult;

typedef enum ReaperDuckAbiStatus {
    REAPER_DUCK_STATUS_OK = 0,
    REAPER_DUCK_STATUS_INVALID_POINTER = 1,
    REAPER_DUCK_STATUS_BAD_ALIGNMENT = 5,
    REAPER_DUCK_STATUS_ARITHMETIC_OVERFLOW = 16,
    REAPER_DUCK_STATUS_DIVISION_BY_ZERO = 17,
    REAPER_DUCK_STATUS_BAD_MAGIC = 2,
    REAPER_DUCK_STATUS_VERSION_MISMATCH = 3,
    REAPER_DUCK_STATUS_BAD_FRAME_SIZE = 4,
    REAPER_DUCK_STATUS_INVALID_FLAGS = 7,
    REAPER_DUCK_STATUS_BAD_ARGUMENT_LAYOUT = 18
} ReaperDuckAbiStatus;

_Static_assert(sizeof(ReaperDuckValue) == 16, "DABI64 value layout mismatch");
_Static_assert(offsetof(ReaperDuckValue, payload) == 0, "DABI64 payload offset mismatch");
_Static_assert(offsetof(ReaperDuckValue, kind) == 8, "DABI64 kind offset mismatch");
_Static_assert(offsetof(ReaperDuckValue, flags) == 12, "DABI64 value flags offset mismatch");
_Static_assert(sizeof(ReaperDuckCallFrame) == 48, "DABI64 frame layout mismatch");
_Static_assert(offsetof(ReaperDuckCallFrame, magic) == 0, "DABI64 magic offset mismatch");
_Static_assert(offsetof(ReaperDuckCallFrame, abi_major) == 4, "DABI64 major offset mismatch");
_Static_assert(offsetof(ReaperDuckCallFrame, byte_size) == 8, "DABI64 size offset mismatch");
_Static_assert(offsetof(ReaperDuckCallFrame, argument_count) == 12, "DABI64 argument count offset mismatch");
_Static_assert(offsetof(ReaperDuckCallFrame, arguments) == 32, "DABI64 argument offset mismatch");
_Static_assert(offsetof(ReaperDuckCallFrame, captures) == 40, "DABI64 capture offset mismatch");
_Static_assert(sizeof(ReaperDuckCallResult) == 16, "DABI64 result layout mismatch");

#endif
