#ifdef NDEBUG
#undef NDEBUG
#endif
#include "reaper/dabi64.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t console[2048];
    uint64_t console_length;
    uint8_t file[512];
    uint64_t file_length;
    uint64_t file_position;
    int file_open;
} HostState;

static int32_t host_write(void *context, int64_t fd, const uint8_t *buffer,
                          uint64_t length, uint64_t *written) {
    HostState *state = (HostState *)context;
    uint8_t *target = NULL;
    uint64_t *used = NULL;
    uint64_t capacity = 0u;
    if (fd == 1) {
        target = state->console;
        used = &state->console_length;
        capacity = sizeof state->console;
    } else if (fd == 42 && state->file_open) {
        target = state->file;
        used = &state->file_length;
        capacity = sizeof state->file;
    } else {
        return -1;
    }
    uint64_t chunk = length > 3u ? 3u : length;
    if (chunk > capacity - *used) return -1;
    if (chunk != 0u) memcpy(target + (size_t)*used, buffer, (size_t)chunk);
    *used += chunk;
    *written = chunk;
    return 0;
}

static int32_t host_read(void *context, int64_t fd, uint8_t *buffer,
                         uint64_t capacity, uint64_t *read_count) {
    HostState *state = (HostState *)context;
    if (fd != 42 || !state->file_open) return -1;
    uint64_t remaining = state->file_length - state->file_position;
    uint64_t count = remaining < capacity ? remaining : capacity;
    if (count != 0u)
        memcpy(buffer, state->file + (size_t)state->file_position, (size_t)count);
    state->file_position += count;
    *read_count = count;
    return 0;
}

static int32_t host_open(void *context, const uint8_t *path,
                         uint64_t path_length, uint32_t mode, int64_t *fd_out) {
    HostState *state = (HostState *)context;
    if (path_length != 8u || memcmp(path, "file.txt", 8u) != 0) return -1;
    state->file_open = 1;
    state->file_position = 0u;
    if (mode == REAPER_DABI_OPEN_WRITE) state->file_length = 0u;
    *fd_out = 42;
    return 0;
}

static int32_t host_close(void *context, int64_t fd) {
    HostState *state = (HostState *)context;
    if (fd != 42 || !state->file_open) return -1;
    state->file_open = 0;
    return 0;
}

static ReaperDabiValue make_string(ReaperDabiRuntime *runtime, const char *text) {
    ReaperDabiValue value = reaper_dabi_unit();
    assert(reaper_dabi_string_new(runtime, (const uint8_t *)text,
                                  (uint64_t)strlen(text), &value) == REAPER_DABI_OK);
    return value;
}

static void test_values_and_collections(ReaperDabiRuntime *runtime) {
    ReaperDabiValue first = make_string(runtime, "duck");
    ReaperDabiValue second = make_string(runtime, "OS");
    ReaperDabiValue joined = reaper_dabi_unit();
    assert(reaper_dabi_string_concat(runtime, &first, &second, &joined) == REAPER_DABI_OK);
    const uint8_t *bytes = NULL;
    uint64_t length = 0u;
    assert(reaper_dabi_string_view(&joined, &bytes, &length) == REAPER_DABI_OK);
    assert(length == 6u && memcmp(bytes, "duckOS", 6u) == 0);

    ReaperDabiValue array = reaper_dabi_unit();
    assert(reaper_dabi_array_new(runtime, &array) == REAPER_DABI_OK);
    ReaperDabiValue number = reaper_dabi_i64(64);
    assert(reaper_dabi_array_push(runtime, &array, &first) == REAPER_DABI_OK);
    assert(reaper_dabi_array_push(runtime, &array, &number) == REAPER_DABI_OK);
    assert(reaper_dabi_array_push(runtime, &array, &array) == REAPER_DABI_RANGE_ERROR);
    uint64_t count = 0u;
    assert(reaper_dabi_array_length(&array, &count) == REAPER_DABI_OK && count == 2u);

    ReaperDabiValue iterator = reaper_dabi_unit();
    assert(reaper_dabi_iter_begin(runtime, &array, &iterator) == REAPER_DABI_OK);
    reaper_dabi_value_drop(runtime, &array);
    int has_value = 0;
    ReaperDabiValue item = reaper_dabi_unit();
    assert(reaper_dabi_iter_next(runtime, &iterator, &has_value, &item) == REAPER_DABI_OK);
    assert(has_value == 1 && item.tag == REAPER_DABI_TAG_STRING);
    reaper_dabi_value_drop(runtime, &item);
    assert(reaper_dabi_iter_next(runtime, &iterator, &has_value, &item) == REAPER_DABI_OK);
    assert(has_value == 1 && item.tag == REAPER_DABI_TAG_I64 && item.payload.i64 == 64);
    assert(reaper_dabi_iter_next(runtime, &iterator, &has_value, &item) == REAPER_DABI_OK);
    assert(has_value == 0 && item.tag == REAPER_DABI_TAG_UNIT);
    reaper_dabi_value_drop(runtime, &iterator);

    ReaperDabiValue parent = reaper_dabi_unit();
    ReaperDabiValue child = reaper_dabi_unit();
    ReaperDabiValue parent_iterator = reaper_dabi_unit();
    assert(reaper_dabi_array_new(runtime, &parent) == REAPER_DABI_OK);
    assert(reaper_dabi_array_new(runtime, &child) == REAPER_DABI_OK);
    assert(reaper_dabi_array_push(runtime, &parent, &child) == REAPER_DABI_OK);
    assert(reaper_dabi_iter_begin(runtime, &parent, &parent_iterator) == REAPER_DABI_OK);
    assert(reaper_dabi_array_push(runtime, &child, &parent_iterator) == REAPER_DABI_RANGE_ERROR);
    reaper_dabi_value_drop(runtime, &parent_iterator);
    reaper_dabi_value_drop(runtime, &parent);
    reaper_dabi_value_drop(runtime, &child);

    reaper_dabi_value_drop(runtime, &first);
    reaper_dabi_value_drop(runtime, &second);
    reaper_dabi_value_drop(runtime, &joined);
}

static void test_frame_cleanup(ReaperDabiRuntime *runtime) {
    ReaperDabiFrame frame;
    uint64_t slot = REAPER_DABI64_NO_SLOT;
    ReaperDabiValue string = make_string(runtime, "owned");
    assert(reaper_dabi_frame_init(&frame, runtime) == REAPER_DABI_OK);
    assert(reaper_dabi_frame_hold(&frame, &string, &slot) == REAPER_DABI_OK);
    assert(slot == 0u);
    reaper_dabi_value_drop(runtime, &string);
    assert(reaper_dabi_frame_release(&frame, slot) == REAPER_DABI_OK);
    reaper_dabi_frame_destroy(&frame);
}

static void test_dispatch_emit_and_io(ReaperDabiRuntime *runtime, HostState *state) {
    ReaperDabiValue text = make_string(runtime, "hello");
    ReaperDabiValue fd = reaper_dabi_unit();
    uint64_t written = 0u;
    ReaperDabiValue wrong_path = reaper_dabi_i64(7);
    assert(reaper_dabi_open(runtime, &wrong_path, REAPER_DABI_OPEN_READ, &fd) == REAPER_DABI_TYPE_ERROR);
    ReaperDabiValue path = make_string(runtime, "file.txt");
    assert(reaper_dabi_open(runtime, &path, REAPER_DABI_OPEN_WRITE, &fd) == REAPER_DABI_OK);
    assert(reaper_dabi_file_write(runtime, &fd, &text, &written) == REAPER_DABI_OK);
    assert(written == 5u);
    assert(reaper_dabi_close(runtime, &fd) == REAPER_DABI_OK);
    assert(reaper_dabi_open(runtime, &path, REAPER_DABI_OPEN_READ, &fd) == REAPER_DABI_OK);
    uint8_t read_buffer[16] = {0};
    uint64_t read_count = 0u;
    assert(reaper_dabi_read(runtime, &fd, read_buffer, sizeof read_buffer,
                            &read_count) == REAPER_DABI_OK);
    assert(read_count == 5u && memcmp(read_buffer, "hello", 5u) == 0);
    assert(reaper_dabi_close(runtime, &fd) == REAPER_DABI_OK);

    ReaperDabiValue args[1] = {text};
    ReaperDabiValue result = reaper_dabi_unit();
    uint64_t table_count = 0u;
    assert(reaper_dabi_call_table(&table_count) != NULL && table_count >= 9u);
    assert(reaper_dabi_dispatch(runtime, REAPER_DABI_CALL_EMIT, args, 1u,
                                &result, NULL) == REAPER_DABI_OK);
    assert(state->console_length == 6u);
    assert(memcmp(state->console, "hello\n", 6u) == 0);
    reaper_dabi_value_drop(runtime, &text);
    reaper_dabi_value_drop(runtime, &path);
}

int main(void) {
    assert(reaper_dabi64_layout_is_valid());
    HostState state = {0};
    ReaperDabiHostV1 host = {
        REAPER_DABI64_VERSION, (uint32_t)sizeof(ReaperDabiHostV1), &state,
        host_write, host_read, host_open, host_close
    };
    ReaperDabiRuntime runtime;
    assert(reaper_dabi_runtime_init(&runtime, &host, NULL) == REAPER_DABI_OK);

    test_values_and_collections(&runtime);
    test_frame_cleanup(&runtime);
    test_dispatch_emit_and_io(&runtime, &state);
    assert(runtime.live_objects == 0u);
    assert(reaper_dabi_runtime_destroy(&runtime) == REAPER_DABI_OK);
    puts("DABI64 v1 runtime tests passed");
    return 0;
}
