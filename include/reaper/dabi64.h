#ifndef REAPER_DABI64_H
#define REAPER_DABI64_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define REAPER_DABI64_ABI_VERSION 1u
#define REAPER_DABI64_MAX_ARGUMENTS 4096u
#define REAPER_DABI64_MAX_VALUE_BYTES (1024u * 1024u)
#define REAPER_DABI64_MAX_ARRAY_ITEMS 100000u
#if defined(_WIN32) && defined(REAPER_DABI64_BUILD)
#define REAPER_DABI64_EXPORT __declspec(dllexport)
#elif defined(_WIN32)
#define REAPER_DABI64_EXPORT __declspec(dllimport)
#elif defined(__GNUC__) || defined(__clang__)
#define REAPER_DABI64_EXPORT __attribute__((visibility("default")))
#else
#define REAPER_DABI64_EXPORT
#endif
#if defined(_WIN32) && !defined(_WIN64)
#error "DABI64 requires a 64-bit target"
#endif

typedef enum {
    REAPER_DABI64_OK = 0,
    REAPER_DABI64_INVALID_ARGUMENT = 1,
    REAPER_DABI64_ABI_MISMATCH = 2,
    REAPER_DABI64_INVALID_VALUE = 3,
    REAPER_DABI64_ARITY_ERROR = 4,
    REAPER_DABI64_EXECUTION_ERROR = 5,
    REAPER_DABI64_OUT_OF_MEMORY = 6
} ReaperDabi64Status;

typedef enum {
    REAPER_DABI64_VALUE_UNIT = 0,
    REAPER_DABI64_VALUE_I64 = 1,
    REAPER_DABI64_VALUE_BOOL = 2,
    REAPER_DABI64_VALUE_UTF8 = 3,
    REAPER_DABI64_VALUE_BYTES = 4,
    REAPER_DABI64_VALUE_ARRAY_I64 = 5,
    REAPER_DABI64_VALUE_HANDLE = 6
} ReaperDabi64ValueKind;

typedef enum {
    REAPER_DABI64_VALUE_BORROWED = 0u,
    REAPER_DABI64_VALUE_OWNED = 1u,
    REAPER_DABI64_VALUE_IMMUTABLE = 2u
} ReaperDabi64ValueFlags;

typedef enum {
    REAPER_DABI64_LOG_DEBUG = 0,
    REAPER_DABI64_LOG_INFO = 1,
    REAPER_DABI64_LOG_WARNING = 2,
    REAPER_DABI64_LOG_ERROR = 3
} ReaperDabi64LogLevel;

/*
 * Stable 24-byte value layout. I64 stores two's-complement bits in payload;
 * BOOL stores exactly 0 or 1. UTF8/BYTES use payload as a byte pointer and
 * length in bytes. ARRAY_I64 uses length in elements. HANDLE is opaque.
 * Pointer-bearing values are valid for the call duration unless marked owned.
 */
typedef struct {
    uint32_t kind;
    uint32_t flags;
    uint64_t payload;
    uint64_t length;
} ReaperDabi64Value;

typedef struct ReaperDabi64HostV1 ReaperDabi64HostV1;
typedef struct ReaperDabi64ModuleV1 ReaperDabi64ModuleV1;

typedef void *(*ReaperDabi64AllocateFn)(void *context, uint64_t size, uint64_t alignment);
typedef void (*ReaperDabi64ReleaseFn)(void *context, void *allocation);
typedef void (*ReaperDabi64LogFn)(void *context, uint32_t level, const char *message, uint64_t length);

struct ReaperDabi64HostV1 {
    uint32_t abi_version;
    uint32_t struct_size;
    void *context;
    ReaperDabi64AllocateFn allocate;
    ReaperDabi64ReleaseFn release;
    ReaperDabi64LogFn log;
};

typedef ReaperDabi64Status (*ReaperDabi64InvokeFn)(
    const ReaperDabi64HostV1 *host,
    const ReaperDabi64Value *arguments,
    uint64_t argument_count,
    ReaperDabi64Value *result
);
typedef void (*ReaperDabi64DestroyFn)(const ReaperDabi64HostV1 *host, void *module_state);

struct ReaperDabi64ModuleV1 {
    uint32_t abi_version;
    uint32_t struct_size;
    const char *name;
    uint32_t flags;
    uint32_t reserved;
    void *module_state;
    ReaperDabi64InvokeFn invoke;
    ReaperDabi64DestroyFn destroy;
};

/* Every DABI64 module exports this one versioned descriptor entry point. */
REAPER_DABI64_EXPORT const ReaperDabi64ModuleV1 *reaper_dabi64_module_v1(void);
REAPER_DABI64_EXPORT uint32_t reaper_dabi64_abi_version(void);
REAPER_DABI64_EXPORT ReaperDabi64Status reaper_dabi64_validate_host(const ReaperDabi64HostV1 *host);
REAPER_DABI64_EXPORT ReaperDabi64Status reaper_dabi64_validate_module(const ReaperDabi64ModuleV1 *module);
REAPER_DABI64_EXPORT ReaperDabi64Status reaper_dabi64_validate_value(const ReaperDabi64Value *value);
REAPER_DABI64_EXPORT ReaperDabi64Status reaper_dabi64_invoke(
    const ReaperDabi64HostV1 *host, const ReaperDabi64ModuleV1 *module,
    const ReaperDabi64Value *arguments, uint64_t argument_count,
    ReaperDabi64Value *result
);
REAPER_DABI64_EXPORT void reaper_dabi64_value_release(
    const ReaperDabi64HostV1 *host, ReaperDabi64Value *value
);

#if defined(__cplusplus)
static_assert(sizeof(ReaperDabi64Value) == 24u, "DABI64 value layout changed");
static_assert(sizeof(void *) == 8u, "DABI64 needs 64-bit pointers");
#else
_Static_assert(sizeof(ReaperDabi64Value) == 24u, "DABI64 value layout changed");
_Static_assert(sizeof(void *) == 8u, "DABI64 needs 64-bit pointers");
#endif
#ifdef __cplusplus
}
#endif
#endif
