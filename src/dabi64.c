#include "reaper/dabi64.h"

#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef enum {
    DABI_OBJECT_STRING = REAPER_DABI_TAG_STRING,
    DABI_OBJECT_ARRAY = REAPER_DABI_TAG_ARRAY,
    DABI_OBJECT_ITERATOR = REAPER_DABI_TAG_ITERATOR
} DabiObjectKind;

typedef struct DabiObject DabiObject;

struct DabiObject {
    uint64_t references;
    uint64_t length;
    uint64_t capacity;
    uint32_t kind;
    uint32_t reserved;
    union {
        uint8_t *bytes;
        ReaperDabiValue *items;
        struct {
            DabiObject *source;
            uint64_t index;
        } iterator;
    } data;
};

static void *default_alloc(void *context, uint64_t size) {
    (void)context;
    if (size > (uint64_t)SIZE_MAX) return NULL;
    return malloc((size_t)size);
}

static void default_free(void *context, void *pointer) {
    (void)context;
    free(pointer);
}

static int runtime_ready(const ReaperDabiRuntime *runtime) {
    return runtime != NULL && runtime->initialized == 1u &&
           runtime->host.abi_version == REAPER_DABI64_VERSION;
}

static int value_tag_valid(uint32_t tag) {
    return tag <= REAPER_DABI_TAG_ITERATOR;
}

static ReaperDabiValue value_with_tag(uint32_t tag) {
    ReaperDabiValue value;
    memset(&value, 0, sizeof value);
    value.tag = tag;
    return value;
}

static DabiObject *object_of(const ReaperDabiValue *value) {
    return (DabiObject *)value->payload.object;
}

static ReaperDabiStatus object_create(
    ReaperDabiRuntime *runtime, DabiObjectKind kind, DabiObject **out
) {
    if (!runtime_ready(runtime) || out == NULL)
        return REAPER_DABI_INVALID_ARGUMENT;
    DabiObject *object = (DabiObject *)runtime->allocator.alloc(
        runtime->allocator.context, (uint64_t)sizeof *object);
    if (object == NULL) return REAPER_DABI_OUT_OF_MEMORY;
    memset(object, 0, sizeof *object);
    object->references = 1u;
    object->kind = (uint32_t)kind;
    runtime->live_objects++;
    *out = object;
    return REAPER_DABI_OK;
}

static ReaperDabiStatus retain_object(DabiObject *object) {
    if (object == NULL || object->references == 0u)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (object->references == UINT64_MAX) return REAPER_DABI_RANGE_ERROR;
    object->references++;
    return REAPER_DABI_OK;
}

static void release_object(ReaperDabiRuntime *runtime, DabiObject *object,
                           uint32_t depth) {
    if (object == NULL || object->references == 0u) return;
    object->references--;
    if (object->references != 0u) return;

    if (object->kind == DABI_OBJECT_ARRAY) {
        for (uint64_t i = object->length; i > 0u; --i)
            reaper_dabi_value_drop(runtime, &object->data.items[i - 1u]);
        if (object->data.items != NULL)
            runtime->allocator.free(runtime->allocator.context, object->data.items);
    } else if (object->kind == DABI_OBJECT_STRING) {
        if (object->data.bytes != NULL)
            runtime->allocator.free(runtime->allocator.context, object->data.bytes);
    } else if (object->kind == DABI_OBJECT_ITERATOR) {
        if (object->data.iterator.source != NULL) {
            DabiObject *source = object->data.iterator.source;
            object->data.iterator.source = NULL;
            release_object(runtime, source, depth + 1u);
        }
    }

    runtime->allocator.free(runtime->allocator.context, object);
    if (runtime->live_objects > 0u) runtime->live_objects--;
}

int reaper_dabi64_layout_is_valid(void) {
    return sizeof(void *) == 8u && sizeof(ReaperDabiValue) == 16u &&
           offsetof(ReaperDabiValue, payload) == 8u;
}

ReaperDabiStatus reaper_dabi_runtime_init(
    ReaperDabiRuntime *runtime,
    const ReaperDabiHostV1 *host,
    const ReaperDabiAllocator *allocator
) {
    if (runtime == NULL || host == NULL) return REAPER_DABI_INVALID_ARGUMENT;
    memset(runtime, 0, sizeof *runtime);
    if (!reaper_dabi64_layout_is_valid()) return REAPER_DABI_ABI_MISMATCH;
    if (host->abi_version != REAPER_DABI64_VERSION ||
        host->struct_size < (uint32_t)sizeof *host)
        return REAPER_DABI_ABI_MISMATCH;
    if ((allocator != NULL) &&
        ((allocator->alloc == NULL) != (allocator->free == NULL)))
        return REAPER_DABI_INVALID_ARGUMENT;

    runtime->host = *host;
    if (allocator != NULL && allocator->alloc != NULL) {
        runtime->allocator = *allocator;
    } else {
        runtime->allocator.context = NULL;
        runtime->allocator.alloc = default_alloc;
        runtime->allocator.free = default_free;
    }
    runtime->stdout_fd = 1;
    runtime->initialized = 1u;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_runtime_destroy(ReaperDabiRuntime *runtime) {
    if (!runtime_ready(runtime)) return REAPER_DABI_INVALID_ARGUMENT;
    if (runtime->live_objects != 0u) return REAPER_DABI_CLOSED;
    memset(runtime, 0, sizeof *runtime);
    return REAPER_DABI_OK;
}

ReaperDabiValue reaper_dabi_unit(void) { return value_with_tag(REAPER_DABI_TAG_UNIT); }
ReaperDabiValue reaper_dabi_bool(int value) {
    ReaperDabiValue result = value_with_tag(REAPER_DABI_TAG_BOOL);
    result.payload.i64 = value != 0 ? 1 : 0;
    return result;
}
ReaperDabiValue reaper_dabi_i64(int64_t value) {
    ReaperDabiValue result = value_with_tag(REAPER_DABI_TAG_I64);
    result.payload.i64 = value;
    return result;
}
ReaperDabiValue reaper_dabi_f64(double value) {
    ReaperDabiValue result = value_with_tag(REAPER_DABI_TAG_F64);
    result.payload.f64 = value;
    return result;
}
ReaperDabiValue reaper_dabi_fd(int64_t fd) {
    ReaperDabiValue result = value_with_tag(REAPER_DABI_TAG_FD);
    result.payload.i64 = fd;
    return result;
}

ReaperDabiStatus reaper_dabi_string_new(
    ReaperDabiRuntime *runtime, const uint8_t *bytes, uint64_t length,
    ReaperDabiValue *out
) {
    if (!runtime_ready(runtime) || out == NULL || (length != 0u && bytes == NULL))
        return REAPER_DABI_INVALID_ARGUMENT;
    if (length > (uint64_t)SIZE_MAX) return REAPER_DABI_RANGE_ERROR;
    DabiObject *object = NULL;
    ReaperDabiStatus status = object_create(runtime, DABI_OBJECT_STRING, &object);
    if (status != REAPER_DABI_OK) return status;
    if (length != 0u) {
        object->data.bytes = (uint8_t *)runtime->allocator.alloc(
            runtime->allocator.context, length);
        if (object->data.bytes == NULL) {
            release_object(runtime, object, 0u);
            return REAPER_DABI_OUT_OF_MEMORY;
        }
        memcpy(object->data.bytes, bytes, (size_t)length);
    }
    object->length = length;
    *out = value_with_tag(REAPER_DABI_TAG_STRING);
    out->payload.object = object;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_array_new(
    ReaperDabiRuntime *runtime, ReaperDabiValue *out
) {
    if (!runtime_ready(runtime) || out == NULL) return REAPER_DABI_INVALID_ARGUMENT;
    DabiObject *object = NULL;
    ReaperDabiStatus status = object_create(runtime, DABI_OBJECT_ARRAY, &object);
    if (status != REAPER_DABI_OK) return status;
    *out = value_with_tag(REAPER_DABI_TAG_ARRAY);
    out->payload.object = object;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_value_copy(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *source,
    ReaperDabiValue *out
) {
    if (!runtime_ready(runtime) || source == NULL || out == NULL ||
        !value_tag_valid(source->tag)) return REAPER_DABI_INVALID_ARGUMENT;
    if (source == out) return REAPER_DABI_OK;
    if (source->tag == REAPER_DABI_TAG_STRING ||
        source->tag == REAPER_DABI_TAG_ARRAY ||
        source->tag == REAPER_DABI_TAG_ITERATOR) {
        ReaperDabiStatus status = retain_object(object_of(source));
        if (status != REAPER_DABI_OK) return status;
    }
    *out = *source;
    return REAPER_DABI_OK;
}

void reaper_dabi_value_drop(ReaperDabiRuntime *runtime, ReaperDabiValue *value) {
    if (value == NULL) return;
    if (runtime_ready(runtime) &&
        (value->tag == REAPER_DABI_TAG_STRING ||
         value->tag == REAPER_DABI_TAG_ARRAY ||
         value->tag == REAPER_DABI_TAG_ITERATOR))
        release_object(runtime, object_of(value), 0u);
    *value = reaper_dabi_unit();
}

ReaperDabiStatus reaper_dabi_string_view(
    const ReaperDabiValue *value, const uint8_t **bytes, uint64_t *length
) {
    if (value == NULL || bytes == NULL || length == NULL)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (value->tag != REAPER_DABI_TAG_STRING) return REAPER_DABI_TYPE_ERROR;
    DabiObject *object = object_of(value);
    if (object == NULL || object->kind != DABI_OBJECT_STRING)
        return REAPER_DABI_INVALID_ARGUMENT;
    *bytes = object->data.bytes;
    *length = object->length;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_string_concat(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *left,
    const ReaperDabiValue *right, ReaperDabiValue *out
) {
    const uint8_t *left_bytes = NULL, *right_bytes = NULL;
    uint64_t left_length = 0u, right_length = 0u;
    if (!runtime_ready(runtime) || out == NULL || out == left || out == right)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (reaper_dabi_string_view(left, &left_bytes, &left_length) != REAPER_DABI_OK ||
        reaper_dabi_string_view(right, &right_bytes, &right_length) != REAPER_DABI_OK)
        return REAPER_DABI_TYPE_ERROR;
    if (left_length > UINT64_MAX - right_length)
        return REAPER_DABI_RANGE_ERROR;
    uint64_t length = left_length + right_length;
    if (length > (uint64_t)SIZE_MAX) return REAPER_DABI_RANGE_ERROR;
    uint8_t *joined = NULL;
    if (length != 0u) {
        joined = (uint8_t *)runtime->allocator.alloc(runtime->allocator.context, length);
        if (joined == NULL) return REAPER_DABI_OUT_OF_MEMORY;
        if (left_length != 0u) memcpy(joined, left_bytes, (size_t)left_length);
        if (right_length != 0u)
            memcpy(joined + (size_t)left_length, right_bytes, (size_t)right_length);
    }
    ReaperDabiStatus status = reaper_dabi_string_new(runtime, joined, length, out);
    if (joined != NULL) runtime->allocator.free(runtime->allocator.context, joined);
    return status;
}

ReaperDabiStatus reaper_dabi_array_length(
    const ReaperDabiValue *array, uint64_t *length
) {
    if (array == NULL || length == NULL) return REAPER_DABI_INVALID_ARGUMENT;
    if (array->tag != REAPER_DABI_TAG_ARRAY) return REAPER_DABI_TYPE_ERROR;
    DabiObject *object = object_of(array);
    if (object == NULL || object->kind != DABI_OBJECT_ARRAY)
        return REAPER_DABI_INVALID_ARGUMENT;
    *length = object->length;
    return REAPER_DABI_OK;
}

static int contains_object(const ReaperDabiValue *value, DabiObject *target,
                           uint32_t depth) {
    if (value->tag == REAPER_DABI_TAG_ITERATOR) {
        DabiObject *iterator = object_of(value);
        return iterator == NULL || iterator->kind != DABI_OBJECT_ITERATOR ||
               iterator->data.iterator.source == target;
    }
    if (value->tag != REAPER_DABI_TAG_ARRAY) return 0;
    DabiObject *object = object_of(value);
    if (object == target) return 1;
    if (object == NULL || object->kind != DABI_OBJECT_ARRAY ||
        depth >= REAPER_DABI64_MAX_NESTING) return 1;
    for (uint64_t i = 0u; i < object->length; ++i)
        if (contains_object(&object->data.items[i], target, depth + 1u)) return 1;
    return 0;
}

ReaperDabiStatus reaper_dabi_array_push(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *array,
    const ReaperDabiValue *value
) {
    if (!runtime_ready(runtime) || array == NULL || value == NULL ||
        !value_tag_valid(value->tag)) return REAPER_DABI_INVALID_ARGUMENT;
    if (array->tag != REAPER_DABI_TAG_ARRAY) return REAPER_DABI_TYPE_ERROR;
    DabiObject *object = object_of(array);
    if (object == NULL || object->kind != DABI_OBJECT_ARRAY)
        return REAPER_DABI_INVALID_ARGUMENT;
    if ((value->tag == REAPER_DABI_TAG_ARRAY || value->tag == REAPER_DABI_TAG_ITERATOR) &&
        contains_object(value, object, 0u))
        return REAPER_DABI_RANGE_ERROR;
    if (object->length == UINT64_MAX) return REAPER_DABI_RANGE_ERROR;

    if (object->length == object->capacity) {
        uint64_t next = object->capacity == 0u ? 4u : object->capacity * 2u;
        if (next < object->capacity || next > (uint64_t)(SIZE_MAX / sizeof(ReaperDabiValue)))
            return REAPER_DABI_RANGE_ERROR;
        ReaperDabiValue *items = (ReaperDabiValue *)runtime->allocator.alloc(
            runtime->allocator.context, next * (uint64_t)sizeof(ReaperDabiValue));
        if (items == NULL) return REAPER_DABI_OUT_OF_MEMORY;
        if (object->length != 0u)
            memcpy(items, object->data.items,
                   (size_t)(object->length * (uint64_t)sizeof(ReaperDabiValue)));
        if (object->data.items != NULL)
            runtime->allocator.free(runtime->allocator.context, object->data.items);
        object->data.items = items;
        object->capacity = next;
    }

    ReaperDabiValue copy;
    ReaperDabiStatus status = reaper_dabi_value_copy(runtime, value, &copy);
    if (status != REAPER_DABI_OK) return status;
    object->data.items[object->length++] = copy;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_array_get(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *array,
    uint64_t index, ReaperDabiValue *out
) {
    if (array == NULL || out == NULL || out == array) return REAPER_DABI_INVALID_ARGUMENT;
    if (array->tag != REAPER_DABI_TAG_ARRAY) return REAPER_DABI_TYPE_ERROR;
    DabiObject *object = object_of(array);
    if (object == NULL || object->kind != DABI_OBJECT_ARRAY)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (index >= object->length) return REAPER_DABI_RANGE_ERROR;
    return reaper_dabi_value_copy(runtime, &object->data.items[index], out);
}

ReaperDabiStatus reaper_dabi_iter_begin(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *array,
    ReaperDabiValue *out
) {
    if (!runtime_ready(runtime) || array == NULL || out == NULL || out == array)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (array->tag != REAPER_DABI_TAG_ARRAY) return REAPER_DABI_TYPE_ERROR;
    DabiObject *source = object_of(array);
    if (source == NULL || source->kind != DABI_OBJECT_ARRAY)
        return REAPER_DABI_INVALID_ARGUMENT;
    DabiObject *iterator = NULL;
    ReaperDabiStatus status = object_create(runtime, DABI_OBJECT_ITERATOR, &iterator);
    if (status != REAPER_DABI_OK) return status;
    status = retain_object(source);
    if (status != REAPER_DABI_OK) {
        release_object(runtime, iterator, 0u);
        return status;
    }
    iterator->data.iterator.source = source;
    iterator->data.iterator.index = 0u;
    *out = value_with_tag(REAPER_DABI_TAG_ITERATOR);
    out->payload.object = iterator;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_iter_next(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *iterator_value,
    int *has_value, ReaperDabiValue *value_out
) {
    if (!runtime_ready(runtime) || iterator_value == NULL ||
        has_value == NULL || value_out == NULL || value_out == iterator_value)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (iterator_value->tag != REAPER_DABI_TAG_ITERATOR)
        return REAPER_DABI_TYPE_ERROR;
    DabiObject *iterator = object_of(iterator_value);
    if (iterator == NULL || iterator->kind != DABI_OBJECT_ITERATOR ||
        iterator->data.iterator.source == NULL)
        return REAPER_DABI_CLOSED;
    DabiObject *source = iterator->data.iterator.source;
    uint64_t index = iterator->data.iterator.index;
    if (index >= source->length) {
        *has_value = 0;
        *value_out = reaper_dabi_unit();
        return REAPER_DABI_OK;
    }
    ReaperDabiStatus status = reaper_dabi_value_copy(
        runtime, &source->data.items[index], value_out);
    if (status != REAPER_DABI_OK) return status;
    iterator->data.iterator.index++;
    *has_value = 1;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_frame_init(
    ReaperDabiFrame *frame, ReaperDabiRuntime *runtime
) {
    if (frame == NULL || !runtime_ready(runtime)) return REAPER_DABI_INVALID_ARGUMENT;
    memset(frame, 0, sizeof *frame);
    frame->runtime = runtime;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_frame_hold(
    ReaperDabiFrame *frame, const ReaperDabiValue *value, uint64_t *slot_out
) {
    if (frame == NULL || frame->runtime == NULL || value == NULL || slot_out == NULL)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (frame->count == frame->capacity) {
        uint64_t next = frame->capacity == 0u ? 8u : frame->capacity * 2u;
        if (next < frame->capacity || next >
            (uint64_t)(SIZE_MAX / sizeof(ReaperDabiValue)))
            return REAPER_DABI_RANGE_ERROR;
        ReaperDabiValue *values = (ReaperDabiValue *)frame->runtime->allocator.alloc(
            frame->runtime->allocator.context,
            next * (uint64_t)sizeof(ReaperDabiValue));
        if (values == NULL) return REAPER_DABI_OUT_OF_MEMORY;
        if (frame->count != 0u)
            memcpy(values, frame->values,
                   (size_t)(frame->count * (uint64_t)sizeof(ReaperDabiValue)));
        if (frame->values != NULL)
            frame->runtime->allocator.free(frame->runtime->allocator.context, frame->values);
        frame->values = values;
        frame->capacity = next;
    }
    ReaperDabiValue copy;
    ReaperDabiStatus status = reaper_dabi_value_copy(frame->runtime, value, &copy);
    if (status != REAPER_DABI_OK) return status;
    *slot_out = frame->count;
    frame->values[frame->count++] = copy;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_frame_release(ReaperDabiFrame *frame, uint64_t slot) {
    if (frame == NULL || frame->runtime == NULL) return REAPER_DABI_INVALID_ARGUMENT;
    if (slot >= frame->count) return REAPER_DABI_RANGE_ERROR;
    reaper_dabi_value_drop(frame->runtime, &frame->values[slot]);
    return REAPER_DABI_OK;
}

void reaper_dabi_frame_drop_all(ReaperDabiFrame *frame) {
    if (frame == NULL || frame->runtime == NULL) return;
    for (uint64_t i = frame->count; i > 0u; --i)
        reaper_dabi_value_drop(frame->runtime, &frame->values[i - 1u]);
    frame->count = 0u;
}

void reaper_dabi_frame_destroy(ReaperDabiFrame *frame) {
    if (frame == NULL) return;
    reaper_dabi_frame_drop_all(frame);
    if (frame->runtime != NULL && frame->values != NULL)
        frame->runtime->allocator.free(frame->runtime->allocator.context, frame->values);
    memset(frame, 0, sizeof *frame);
}

ReaperDabiStatus reaper_dabi_open(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *path,
    ReaperDabiOpenMode mode, ReaperDabiValue *fd_out
) {
    const uint8_t *bytes = NULL;
    uint64_t length = 0u;
    if (!runtime_ready(runtime) || fd_out == NULL)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (reaper_dabi_string_view(path, &bytes, &length) != REAPER_DABI_OK)
        return REAPER_DABI_TYPE_ERROR;
    if (runtime->host.open == NULL) return REAPER_DABI_UNSUPPORTED;
    if (mode < REAPER_DABI_OPEN_READ || mode > REAPER_DABI_OPEN_APPEND)
        return REAPER_DABI_INVALID_ARGUMENT;
    int64_t fd = -1;
    if (runtime->host.open(runtime->host.context, bytes, length, (uint32_t)mode, &fd) != 0)
        return REAPER_DABI_IO_ERROR;
    *fd_out = reaper_dabi_fd(fd);
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_read(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *fd,
    uint8_t *buffer, uint64_t capacity, uint64_t *read_count
) {
    if (!runtime_ready(runtime) || fd == NULL || read_count == NULL ||
        (capacity != 0u && buffer == NULL)) return REAPER_DABI_INVALID_ARGUMENT;
    if (fd->tag != REAPER_DABI_TAG_FD) return REAPER_DABI_TYPE_ERROR;
    if (runtime->host.read == NULL) return REAPER_DABI_UNSUPPORTED;
    uint64_t count = 0u;
    if (runtime->host.read(runtime->host.context, fd->payload.i64,
                           buffer, capacity, &count) != 0)
        return REAPER_DABI_IO_ERROR;
    if (count > capacity) return REAPER_DABI_IO_ERROR;
    *read_count = count;
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_write(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *fd,
    const uint8_t *buffer, uint64_t length, uint64_t *written
) {
    if (!runtime_ready(runtime) || fd == NULL || written == NULL ||
        (length != 0u && buffer == NULL)) return REAPER_DABI_INVALID_ARGUMENT;
    if (fd->tag != REAPER_DABI_TAG_FD) return REAPER_DABI_TYPE_ERROR;
    if (runtime->host.write == NULL) return REAPER_DABI_UNSUPPORTED;
    uint64_t count = 0u;
    if (runtime->host.write(runtime->host.context, fd->payload.i64,
                            buffer, length, &count) != 0)
        return REAPER_DABI_IO_ERROR;
    if (count > length || (length != 0u && count == 0u)) return REAPER_DABI_IO_ERROR;
    *written = count;
    return REAPER_DABI_OK;
}

static ReaperDabiStatus write_all(ReaperDabiRuntime *runtime, int64_t fd,
                                  const uint8_t *bytes, uint64_t length);

ReaperDabiStatus reaper_dabi_file_write(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *fd,
    const ReaperDabiValue *text, uint64_t *written
) {
    const uint8_t *bytes = NULL;
    uint64_t length = 0u;
    if (!runtime_ready(runtime) || written == NULL)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (reaper_dabi_string_view(text, &bytes, &length) != REAPER_DABI_OK)
        return REAPER_DABI_TYPE_ERROR;
    if (fd == NULL || fd->tag != REAPER_DABI_TAG_FD)
        return REAPER_DABI_TYPE_ERROR;
    ReaperDabiStatus status = write_all(runtime, fd->payload.i64, bytes, length);
    if (status == REAPER_DABI_OK) *written = length;
    return status;
}

ReaperDabiStatus reaper_dabi_close(
    ReaperDabiRuntime *runtime, ReaperDabiValue *fd
) {
    if (!runtime_ready(runtime) || fd == NULL) return REAPER_DABI_INVALID_ARGUMENT;
    if (fd->tag != REAPER_DABI_TAG_FD) return REAPER_DABI_TYPE_ERROR;
    if (runtime->host.close == NULL) return REAPER_DABI_UNSUPPORTED;
    if (runtime->host.close(runtime->host.context, fd->payload.i64) != 0)
        return REAPER_DABI_IO_ERROR;
    *fd = reaper_dabi_unit();
    return REAPER_DABI_OK;
}

static ReaperDabiStatus write_all(ReaperDabiRuntime *runtime, int64_t fd,
                                  const uint8_t *bytes, uint64_t length) {
    uint64_t offset = 0u;
    while (offset < length) {
        uint64_t written = 0u;
        if (runtime->host.write == NULL) return REAPER_DABI_UNSUPPORTED;
        if (runtime->host.write(runtime->host.context, fd, bytes + (size_t)offset,
                                length - offset, &written) != 0)
            return REAPER_DABI_IO_ERROR;
        if (written == 0u || written > length - offset) return REAPER_DABI_IO_ERROR;
        offset += written;
    }
    return REAPER_DABI_OK;
}

static ReaperDabiStatus emit_value(ReaperDabiRuntime *runtime,
                                   const ReaperDabiValue *value, uint32_t depth,
                                   int quoted) {
    if (depth > REAPER_DABI64_MAX_NESTING) return REAPER_DABI_RANGE_ERROR;
    char buffer[96];
    int length = 0;
    switch (value->tag) {
    case REAPER_DABI_TAG_UNIT:
        return write_all(runtime, runtime->stdout_fd, (const uint8_t *)"unit", 4u);
    case REAPER_DABI_TAG_BOOL:
        return write_all(runtime, runtime->stdout_fd,
                         (const uint8_t *)(value->payload.i64 ? "true" : "false"),
                         value->payload.i64 ? 4u : 5u);
    case REAPER_DABI_TAG_I64:
        length = snprintf(buffer, sizeof buffer, "%" PRId64, value->payload.i64);
        break;
    case REAPER_DABI_TAG_F64:
        length = snprintf(buffer, sizeof buffer, "%.*g", DBL_DECIMAL_DIG,
                          value->payload.f64);
        break;
    case REAPER_DABI_TAG_FD:
        length = snprintf(buffer, sizeof buffer, "<fd:%" PRId64 ">", value->payload.i64);
        break;
    case REAPER_DABI_TAG_ITERATOR:
        return write_all(runtime, runtime->stdout_fd,
                         (const uint8_t *)"<iterator>", 10u);
    case REAPER_DABI_TAG_STRING: {
        DabiObject *object = object_of(value);
        if (object == NULL || object->kind != DABI_OBJECT_STRING)
            return REAPER_DABI_INVALID_ARGUMENT;
        if (!quoted) return write_all(runtime, runtime->stdout_fd,
                                      object->data.bytes, object->length);
        ReaperDabiStatus status = write_all(runtime, runtime->stdout_fd,
                                            (const uint8_t *)"\"", 1u);
        if (status != REAPER_DABI_OK) return status;
        for (uint64_t i = 0u; i < object->length; ++i) {
            uint8_t byte = object->data.bytes[i];
            if (byte == '"' || byte == '\\') {
                uint8_t escaped[2] = {'\\', byte};
                status = write_all(runtime, runtime->stdout_fd, escaped, 2u);
            } else if (byte == '\n') {
                status = write_all(runtime, runtime->stdout_fd,
                                   (const uint8_t *)"\\n", 2u);
            } else if (byte == '\r') {
                status = write_all(runtime, runtime->stdout_fd,
                                   (const uint8_t *)"\\r", 2u);
            } else if (byte == '\t') {
                status = write_all(runtime, runtime->stdout_fd,
                                   (const uint8_t *)"\\t", 2u);
            } else {
                status = write_all(runtime, runtime->stdout_fd, &byte, 1u);
            }
            if (status != REAPER_DABI_OK) return status;
        }
        return write_all(runtime, runtime->stdout_fd, (const uint8_t *)"\"", 1u);
    }
    case REAPER_DABI_TAG_ARRAY: {
        DabiObject *object = object_of(value);
        if (object == NULL || object->kind != DABI_OBJECT_ARRAY)
            return REAPER_DABI_INVALID_ARGUMENT;
        ReaperDabiStatus status = write_all(runtime, runtime->stdout_fd,
                                            (const uint8_t *)"[", 1u);
        for (uint64_t i = 0u; status == REAPER_DABI_OK && i < object->length; ++i) {
            if (i != 0u)
                status = write_all(runtime, runtime->stdout_fd,
                                   (const uint8_t *)", ", 2u);
            if (status == REAPER_DABI_OK)
                status = emit_value(runtime, &object->data.items[i], depth + 1u,
                                    object->data.items[i].tag == REAPER_DABI_TAG_STRING);
        }
        if (status != REAPER_DABI_OK) return status;
        return write_all(runtime, runtime->stdout_fd, (const uint8_t *)"]", 1u);
    }
    default:
        return REAPER_DABI_TYPE_ERROR;
    }
    if (length < 0 || (size_t)length >= sizeof buffer) return REAPER_DABI_RANGE_ERROR;
    return write_all(runtime, runtime->stdout_fd, (const uint8_t *)buffer,
                     (uint64_t)length);
}

ReaperDabiStatus reaper_dabi_emit(
    ReaperDabiRuntime *runtime, const ReaperDabiValue *value
) {
    if (!runtime_ready(runtime) || value == NULL) return REAPER_DABI_INVALID_ARGUMENT;
    ReaperDabiStatus status = emit_value(runtime, value, 0u, 0);
    if (status != REAPER_DABI_OK) return status;
    return write_all(runtime, runtime->stdout_fd, (const uint8_t *)"\n", 1u);
}

static const ReaperDabiCallDescriptor CALLS[] = {
    {REAPER_DABI_CALL_EMIT, 1u, 1u, "emit"},
    {REAPER_DABI_CALL_STRING_CONCAT, 2u, 2u, "string.concat"},
    {REAPER_DABI_CALL_STRING_LENGTH, 1u, 1u, "string.length"},
    {REAPER_DABI_CALL_ARRAY_NEW, 0u, 0u, "array.new"},
    {REAPER_DABI_CALL_ARRAY_PUSH, 2u, 2u, "array.push"},
    {REAPER_DABI_CALL_ARRAY_GET, 2u, 2u, "array.get"},
    {REAPER_DABI_CALL_ARRAY_LENGTH, 1u, 1u, "array.length"},
    {REAPER_DABI_CALL_ITER_BEGIN, 1u, 1u, "iterator.begin"},
    {REAPER_DABI_CALL_ITER_NEXT, 1u, 1u, "iterator.next"}
};

const ReaperDabiCallDescriptor *reaper_dabi_call_table(uint64_t *count) {
    if (count != NULL) *count = (uint64_t)(sizeof CALLS / sizeof CALLS[0]);
    return CALLS;
}

ReaperDabiStatus reaper_dabi_dispatch(
    ReaperDabiRuntime *runtime, uint32_t call_id,
    const ReaperDabiValue *arguments, uint64_t argument_count,
    ReaperDabiValue *result, ReaperDabiValue *auxiliary
) {
    if (!runtime_ready(runtime) || result == NULL ||
        (argument_count != 0u && arguments == NULL))
        return REAPER_DABI_INVALID_ARGUMENT;
    const ReaperDabiCallDescriptor *descriptor = NULL;
    for (size_t i = 0u; i < sizeof CALLS / sizeof CALLS[0]; ++i)
        if (CALLS[i].id == call_id) { descriptor = &CALLS[i]; break; }
    if (descriptor == NULL) return REAPER_DABI_UNSUPPORTED;
    if (argument_count < descriptor->min_arity || argument_count > descriptor->max_arity)
        return REAPER_DABI_INVALID_ARGUMENT;

    *result = reaper_dabi_unit();
    if (auxiliary != NULL) *auxiliary = reaper_dabi_unit();
    switch (call_id) {
    case REAPER_DABI_CALL_EMIT:
        return reaper_dabi_emit(runtime, &arguments[0]);
    case REAPER_DABI_CALL_STRING_CONCAT:
        return reaper_dabi_string_concat(runtime, &arguments[0], &arguments[1], result);
    case REAPER_DABI_CALL_STRING_LENGTH: {
        const uint8_t *bytes = NULL;
        uint64_t length = 0u;
        ReaperDabiStatus status = reaper_dabi_string_view(&arguments[0], &bytes, &length);
        (void)bytes;
        if (status != REAPER_DABI_OK) return status;
        if (length > (uint64_t)INT64_MAX) return REAPER_DABI_RANGE_ERROR;
        *result = reaper_dabi_i64((int64_t)length);
        return REAPER_DABI_OK;
    }
    case REAPER_DABI_CALL_ARRAY_NEW:
        return reaper_dabi_array_new(runtime, result);
    case REAPER_DABI_CALL_ARRAY_PUSH:
        if (arguments[0].tag != REAPER_DABI_TAG_ARRAY) return REAPER_DABI_TYPE_ERROR;
        return reaper_dabi_array_push(runtime, &arguments[0], &arguments[1]);
    case REAPER_DABI_CALL_ARRAY_GET: {
        if (arguments[1].tag != REAPER_DABI_TAG_I64 || arguments[1].payload.i64 < 0)
            return REAPER_DABI_RANGE_ERROR;
        return reaper_dabi_array_get(runtime, &arguments[0],
                                     (uint64_t)arguments[1].payload.i64, result);
    }
    case REAPER_DABI_CALL_ARRAY_LENGTH: {
        uint64_t length = 0u;
        ReaperDabiStatus status = reaper_dabi_array_length(&arguments[0], &length);
        if (status != REAPER_DABI_OK) return status;
        if (length > (uint64_t)INT64_MAX) return REAPER_DABI_RANGE_ERROR;
        *result = reaper_dabi_i64((int64_t)length);
        return REAPER_DABI_OK;
    }
    case REAPER_DABI_CALL_ITER_BEGIN:
        return reaper_dabi_iter_begin(runtime, &arguments[0], result);
    case REAPER_DABI_CALL_ITER_NEXT: {
        if (auxiliary == NULL) return REAPER_DABI_INVALID_ARGUMENT;
        int has_value = 0;
        ReaperDabiStatus status = reaper_dabi_iter_next(
            runtime, &arguments[0], &has_value, auxiliary);
        if (status != REAPER_DABI_OK) return status;
        *result = reaper_dabi_bool(has_value);
        return REAPER_DABI_OK;
    }
    default:
        return REAPER_DABI_UNSUPPORTED;
    }
}

const char *reaper_dabi_status_name(ReaperDabiStatus status) {
    switch (status) {
    case REAPER_DABI_OK: return "ok";
    case REAPER_DABI_INVALID_ARGUMENT: return "invalid_argument";
    case REAPER_DABI_ABI_MISMATCH: return "abi_mismatch";
    case REAPER_DABI_TYPE_ERROR: return "type_error";
    case REAPER_DABI_RANGE_ERROR: return "range_error";
    case REAPER_DABI_OUT_OF_MEMORY: return "out_of_memory";
    case REAPER_DABI_IO_ERROR: return "io_error";
    case REAPER_DABI_UNSUPPORTED: return "unsupported";
    case REAPER_DABI_CLOSED: return "closed";
    default: return "unknown";
    }
}
