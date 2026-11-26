#ifndef REAPER_TYPED_REGISTRY_H
#define REAPER_TYPED_REGISTRY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_TYPED_REGISTRY_ABI_VERSION 1U
#define REAPER_TYPED_MAX_ARGUMENTS 32U

typedef enum {
    REAPER_TYPED_OK = 0,
    REAPER_TYPED_INVALID_ARGUMENT = -1,
    REAPER_TYPED_NOT_FOUND = -2,
    REAPER_TYPED_DUPLICATE = -3,
    REAPER_TYPED_FULL = -4,
    REAPER_TYPED_TYPE_MISMATCH = -5,
    REAPER_TYPED_ARITY_MISMATCH = -6,
    REAPER_TYPED_ACCESS_DENIED = -7,
    REAPER_TYPED_UNIMPLEMENTED = -8,
    REAPER_TYPED_ABI_MISMATCH = -9,
    REAPER_TYPED_HANDLER_ERROR = -10,
    REAPER_TYPED_SEALED = -11,
    REAPER_TYPED_OUT_OF_RANGE = -12
} ReaperTypedStatus;

typedef enum {
    REAPER_TYPED_VOID = 0,
    REAPER_TYPED_BOOL = 1,
    REAPER_TYPED_I64 = 2,
    REAPER_TYPED_U64 = 3,
    REAPER_TYPED_F64 = 4,
    REAPER_TYPED_UTF8 = 5,
    REAPER_TYPED_BYTES = 6,
    REAPER_TYPED_HANDLE = 7
} ReaperTypedKind;

enum {
    REAPER_TYPED_VALUE_NULL = 1U << 0U
};

enum {
    REAPER_TYPED_ARGUMENT_OPTIONAL = 1U << 0U,
    REAPER_TYPED_ARGUMENT_NULLABLE = 1U << 1U
};

enum {
    REAPER_TYPED_CONSTRAINT_MINIMUM = 1U << 0U,
    REAPER_TYPED_CONSTRAINT_MAXIMUM = 1U << 1U,
    REAPER_TYPED_CONSTRAINT_MAX_LENGTH = 1U << 2U,
    REAPER_TYPED_CONSTRAINT_HANDLE_KIND = 1U << 3U
};

typedef struct {
    uint64_t id;
    uint32_t kind;
    uint32_t generation;
} ReaperTypedHandle;

/*
 * UTF-8 and byte members are borrowed views. Inputs must remain valid for the
 * synchronous handler call; returned views must remain valid while consumed.
 * The registry copies value descriptors, never the pointed-to payload bytes.
 */
typedef struct {
    uint32_t kind;
    uint32_t flags;
    union {
        uint8_t boolean;
        int64_t i64;
        uint64_t u64;
        double f64;
        struct {
            const char *data;
            size_t length;
        } text;
        struct {
            const unsigned char *data;
            size_t length;
        } bytes;
        ReaperTypedHandle handle;
    } as;
} ReaperTypedValue;

typedef struct {
    uint32_t kind;
    uint32_t flags;
    uint32_t constraints;
    uint32_t expected_handle_kind;
    size_t max_length;
    ReaperTypedValue minimum;
    ReaperTypedValue maximum;
} ReaperTypedArgumentSpec;

typedef ReaperTypedStatus (*ReaperTypedHandler)(
    void *context,
    const ReaperTypedValue *arguments,
    size_t argument_count,
    ReaperTypedValue *result);

typedef struct {
    const char *domain;
    const char *name;
    uint16_t abi_major;
    uint16_t abi_minor;
    uint64_t required_capabilities;
    const ReaperTypedArgumentSpec *arguments;
    size_t argument_count;
    ReaperTypedArgumentSpec result;
    ReaperTypedHandler handler;
    void *context;
} ReaperTypedOperationSpec;

typedef struct {
    uint64_t hash;
    const char *domain;
    const char *name;
    uint16_t abi_major;
    uint16_t abi_minor;
    uint64_t required_capabilities;
    const ReaperTypedArgumentSpec *arguments;
    size_t argument_count;
    size_t min_arity;
    ReaperTypedArgumentSpec result;
    ReaperTypedHandler handler;
    void *context;
} ReaperTypedEntry;

typedef struct ReaperTypedRegistry {
    ReaperTypedEntry *entries;
    size_t entry_capacity;
    size_t count;
    size_t *buckets;
    size_t bucket_capacity;
    char *string_storage;
    size_t string_capacity;
    size_t string_used;
    ReaperTypedArgumentSpec *argument_storage;
    size_t argument_capacity;
    size_t argument_used;
    uint32_t abi_version;
    uint8_t sealed;
} ReaperTypedRegistry;

/*
 * All storage is supplied by the caller. bucket_capacity must be a power of
 * two and at least twice entry_capacity. Registration copies key strings and
 * argument schemas into the supplied arenas; handlers and contexts remain
 * owned by their defining modules and must outlive the registry.
 */
ReaperTypedStatus reaper_typed_registry_init(
    ReaperTypedRegistry *registry,
    ReaperTypedEntry *entries,
    size_t entry_capacity,
    size_t *buckets,
    size_t bucket_capacity,
    char *string_storage,
    size_t string_capacity,
    ReaperTypedArgumentSpec *argument_storage,
    size_t argument_capacity);

ReaperTypedStatus reaper_typed_registry_register(
    ReaperTypedRegistry *registry,
    const ReaperTypedOperationSpec *operation);

const ReaperTypedEntry *reaper_typed_registry_find(
    const ReaperTypedRegistry *registry,
    const char *domain,
    const char *name,
    uint16_t abi_major);

ReaperTypedStatus reaper_typed_registry_invoke(
    const ReaperTypedRegistry *registry,
    const char *domain,
    const char *name,
    uint16_t abi_major,
    uint16_t minimum_abi_minor,
    uint64_t granted_capabilities,
    const ReaperTypedValue *arguments,
    size_t argument_count,
    ReaperTypedValue *result);

ReaperTypedStatus reaper_typed_registry_seal(ReaperTypedRegistry *registry);
size_t reaper_typed_registry_count(const ReaperTypedRegistry *registry);
size_t reaper_typed_registry_capacity(const ReaperTypedRegistry *registry);
const char *reaper_typed_status_name(ReaperTypedStatus status);

#ifdef __cplusplus
}
#endif

#endif
