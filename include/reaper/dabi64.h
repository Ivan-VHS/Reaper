#ifndef REAPER_DABI64_H
#define REAPER_DABI64_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_DABI64_VERSION 1u
#define REAPER_DABI64_MAX_NESTING 256u
#define REAPER_DABI64_NO_SLOT UINT64_MAX

typedef enum {
    REAPER_DABI_OK = 0,
    REAPER_DABI_INVALID_ARGUMENT = 1,
    REAPER_DABI_ABI_MISMATCH = 2,
    REAPER_DABI_TYPE_ERROR = 3,
    REAPER_DABI_RANGE_ERROR = 4,
    REAPER_DABI_OUT_OF_MEMORY = 5,
    REAPER_DABI_IO_ERROR = 6,
    REAPER_DABI_UNSUPPORTED = 7,
    REAPER_DABI_CLOSED = 8
} ReaperDabiStatus;

typedef enum {
    REAPER_DABI_TAG_UNIT = 0,
    REAPER_DABI_TAG_BOOL = 1,
    REAPER_DABI_TAG_I64 = 2,
    REAPER_DABI_TAG_F64 = 3,
    REAPER_DABI_TAG_STRING = 4,
    REAPER_DABI_TAG_ARRAY = 5,
    REAPER_DABI_TAG_FD = 6,
    REAPER_DABI_TAG_ITERATOR = 7
} ReaperDabiTag;

typedef union {
    int64_t i64;
    double f64;
    uint64_t bits;
    void *object;
} ReaperDabiPayload;

typedef struct {
    uint32_t tag;
    uint32_t flags;
    ReaperDabiPayload payload;
} ReaperDabiValue;

typedef void *(*ReaperDabiAllocFn)(void *context, uint64_t size);
typedef void (*ReaperDabiFreeFn)(void *context, void *pointer);

typedef struct {
    void *context;
    ReaperDabiAllocFn alloc;
    ReaperDabiFreeFn free;
} ReaperDabiAllocator;

typedef int32_t (*ReaperDabiWriteFn)(void *context, int64_t fd,
                                     const uint8_t *buffer, uint64_t length,
                                     uint64_t *written);
typedef int32_t (*ReaperDabiReadFn)(void *context, int64_t fd,
                                    uint8_t *buffer, uint64_t capacity,
                                    uint64_t *read_count);
typedef int32_t (*ReaperDabiOpenFn)(void *context, const uint8_t *path,
                                    uint64_t path_length, uint32_t mode,
                                    int64_t *fd_out);
typedef int32_t (*ReaperDabiCloseFn)(void *context, int64_t fd);

typedef struct {
    uint32_t abi_version;
    uint32_t struct_size;
    void *context;
    ReaperDabiWriteFn write;
    ReaperDabiReadFn read;
    ReaperDabiOpenFn open;
    ReaperDabiCloseFn close;
} ReaperDabiHostV1;

typedef struct {
    ReaperDabiHostV1 host;
    ReaperDabiAllocator allocator;
    int64_t stdout_fd;
    uint64_t live_objects;
    uint32_t initialized;
    uint32_t reserved;
} ReaperDabiRuntime;

typedef struct {
    ReaperDabiRuntime *runtime;
    ReaperDabiValue *values;
    uint64_t count;
    uint64_t capacity;
} ReaperDabiFrame;

typedef enum {
    REAPER_DABI_OPEN_READ = 0,
    REAPER_DABI_OPEN_WRITE = 1,
    REAPER_DABI_OPEN_APPEND = 2
} ReaperDabiOpenMode;

typedef enum {
    REAPER_DABI_CALL_EMIT = 0x0001,
    REAPER_DABI_CALL_STRING_CONCAT = 0x0101,
    REAPER_DABI_CALL_STRING_LENGTH = 0x0102,
    REAPER_DABI_CALL_ARRAY_NEW = 0x0201,
    REAPER_DABI_CALL_ARRAY_PUSH = 0x0202,
    REAPER_DABI_CALL_ARRAY_GET = 0x0203,
    REAPER_DABI_CALL_ARRAY_LENGTH = 0x0204,
    REAPER_DABI_CALL_ITER_BEGIN = 0x0301,
    REAPER_DABI_CALL_ITER_NEXT = 0x0302
} ReaperDabiCallId;

typedef struct {
    uint32_t id;
    uint16_t min_arity;
    uint16_t max_arity;
    const char *name;
} ReaperDabiCallDescriptor;

/* The public value layout is fixed at 16 bytes on a 64-bit target. */
int reaper_dabi64_layout_is_valid(void);

ReaperDabiStatus reaper_dabi_runtime_init(
    ReaperDabiRuntime *runtime,
    const ReaperDabiHostV1 *host,
    const ReaperDabiAllocator *allocator
);
ReaperDabiStatus reaper_dabi_runtime_destroy(ReaperDabiRuntime *runtime);

ReaperDabiValue reaper_dabi_unit(void);
ReaperDabiValue reaper_dabi_bool(int value);
ReaperDabiValue reaper_dabi_i64(int64_t value);
ReaperDabiValue reaper_dabi_f64(double value);
ReaperDabiValue reaper_dabi_fd(int64_t fd);
ReaperDabiStatus reaper_dabi_string_new(
    ReaperDabiRuntime *runtime, const uint8_t *bytes, uint64_t length,
    ReaperDabiValue *out
);
ReaperDabiStatus reaper_dabi_array_new(
    ReaperDabiRuntime *runtime, ReaperDabiValue *out
);
ReaperDabiStatus reaper_dabi_value_copy(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *source,
    ReaperDabiValue *out
);
void reaper_dabi_value_drop(ReaperDabiRuntime *runtime, ReaperDabiValue *value);

ReaperDabiStatus reaper_dabi_string_view(
    const ReaperDabiValue *value, const uint8_t **bytes, uint64_t *length
);
ReaperDabiStatus reaper_dabi_string_concat(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *left,
    const ReaperDabiValue *right, ReaperDabiValue *out
);
ReaperDabiStatus reaper_dabi_array_length(
    const ReaperDabiValue *array, uint64_t *length
);
ReaperDabiStatus reaper_dabi_array_push(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *array,
    const ReaperDabiValue *value
);
ReaperDabiStatus reaper_dabi_array_get(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *array,
    uint64_t index, ReaperDabiValue *out
);

/* An iterator retains its source array. Each yielded value is an owned copy. */
ReaperDabiStatus reaper_dabi_iter_begin(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *array,
    ReaperDabiValue *out
);
ReaperDabiStatus reaper_dabi_iter_next(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *iterator,
    int *has_value, ReaperDabiValue *value_out
);

/* Code generation places owned temporaries in a frame and drops it on every exit. */
ReaperDabiStatus reaper_dabi_frame_init(
    ReaperDabiFrame *frame, ReaperDabiRuntime *runtime
);
ReaperDabiStatus reaper_dabi_frame_hold(
    ReaperDabiFrame *frame, const ReaperDabiValue *value, uint64_t *slot_out
);
ReaperDabiStatus reaper_dabi_frame_release(ReaperDabiFrame *frame, uint64_t slot);
void reaper_dabi_frame_drop_all(ReaperDabiFrame *frame);
void reaper_dabi_frame_destroy(ReaperDabiFrame *frame);

/* I/O is supplied by the host. DuckOS can map these callbacks to syscalls. */
ReaperDabiStatus reaper_dabi_open(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *path,
    ReaperDabiOpenMode mode, ReaperDabiValue *fd_out
);
ReaperDabiStatus reaper_dabi_read(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *fd,
    uint8_t *buffer, uint64_t capacity, uint64_t *read_count
);
ReaperDabiStatus reaper_dabi_write(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *fd,
    const uint8_t *buffer, uint64_t length, uint64_t *written
);
ReaperDabiStatus reaper_dabi_file_write(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *fd,
    const ReaperDabiValue *text, uint64_t *written
);
ReaperDabiStatus reaper_dabi_close(
    ReaperDabiRuntime *runtime, ReaperDabiValue *fd
);
ReaperDabiStatus reaper_dabi_emit(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *value
);

const ReaperDabiCallDescriptor *reaper_dabi_call_table(uint64_t *count);
ReaperDabiStatus reaper_dabi_dispatch(
    ReaperDabiRuntime *runtime, uint32_t call_id,
    const ReaperDabiValue *arguments, uint64_t argument_count,
    ReaperDabiValue *result, ReaperDabiValue *auxiliary
);
const char *reaper_dabi_status_name(ReaperDabiStatus status);

#ifdef __cplusplus
}
#endif

#endif
