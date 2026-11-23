#ifdef NDEBUG
#undef NDEBUG
#endif
#include "reaper/dabi64.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static size_t release_count = 0u;

static void *host_allocate(void *context, uint64_t size, uint64_t alignment) {
    (void)context;
    (void)alignment;
    return malloc((size_t)size);
}

static void host_release(void *context, void *allocation) {
    (void)context;
    if (allocation != NULL) ++release_count;
    free(allocation);
}

static void host_log(void *context, uint32_t level, const char *message, uint64_t length) {
    (void)context; (void)level; (void)message; (void)length;
}

static ReaperDabi64Status sum_i64(
    const ReaperDabi64HostV1 *host,
    const ReaperDabi64Value *arguments,
    uint64_t argument_count,
    ReaperDabi64Value *result
) {
    (void)host;
    if (argument_count != 2u) return REAPER_DABI64_ARITY_ERROR;
    if (arguments[0].kind != REAPER_DABI64_VALUE_I64 ||
        arguments[1].kind != REAPER_DABI64_VALUE_I64)
        return REAPER_DABI64_INVALID_VALUE;
    int64_t left = 0, right = 0;
    memcpy(&left, &arguments[0].payload, sizeof left);
    memcpy(&right, &arguments[1].payload, sizeof right);
    int64_t sum = left + right;
    result->kind = REAPER_DABI64_VALUE_I64;
    memcpy(&result->payload, &sum, sizeof sum);
    return REAPER_DABI64_OK;
}

static const ReaperDabi64ModuleV1 sample_module = {
    REAPER_DABI64_ABI_VERSION, sizeof(ReaperDabi64ModuleV1),
    "sample.sum", 0u, 0u, NULL, sum_i64, NULL
};

static void test_version_and_layout(void) {
    assert(sizeof(ReaperDabi64Value) == 24u);
    assert(reaper_dabi64_abi_version() == REAPER_DABI64_ABI_VERSION);
    assert(reaper_dabi64_validate_module(&sample_module) == REAPER_DABI64_OK);
    ReaperDabi64ModuleV1 wrong = sample_module;
    wrong.abi_version = 9u;
    assert(reaper_dabi64_validate_module(&wrong) == REAPER_DABI64_ABI_MISMATCH);
}

static void test_call_contract(void) {
    const ReaperDabi64HostV1 host = {
        REAPER_DABI64_ABI_VERSION, sizeof(ReaperDabi64HostV1),
        NULL, host_allocate, host_release, host_log
    };
    ReaperDabi64Value arguments[2] = {
        {REAPER_DABI64_VALUE_I64, 0u, 19u, 0u},
        {REAPER_DABI64_VALUE_I64, 0u, 23u, 0u}
    };
    ReaperDabi64Value result = {0};
    assert(reaper_dabi64_validate_host(&host) == REAPER_DABI64_OK);
    assert(reaper_dabi64_invoke(&host, &sample_module, arguments, 2u, &result) == REAPER_DABI64_OK);
    assert(result.kind == REAPER_DABI64_VALUE_I64 && result.payload == 42u);
    assert(reaper_dabi64_invoke(&host, &sample_module, arguments, 1u, &result) == REAPER_DABI64_ARITY_ERROR);
    const ReaperDabi64HostV1 wrong_host = {
        2u, sizeof(ReaperDabi64HostV1), NULL, host_allocate, host_release, host_log
    };
    assert(reaper_dabi64_invoke(&wrong_host, &sample_module, arguments, 2u, &result) == REAPER_DABI64_ABI_MISMATCH);
}

static void test_owned_value_release(void) {
    const ReaperDabi64HostV1 host = {
        REAPER_DABI64_ABI_VERSION, sizeof(ReaperDabi64HostV1),
        NULL, host_allocate, host_release, host_log
    };
    char *memory = (char *)host_allocate(NULL, 8u, 8u);
    assert(memory != NULL);
    ReaperDabi64Value value = {
        REAPER_DABI64_VALUE_UTF8, REAPER_DABI64_VALUE_OWNED,
        (uint64_t)(uintptr_t)memory, 7u
    };
    reaper_dabi64_value_release(&host, &value);
    assert(release_count == 1u);
    assert(value.kind == REAPER_DABI64_VALUE_UNIT && value.payload == 0u);
}

static void test_rejects_invalid_values(void) {
    ReaperDabi64Value value = {REAPER_DABI64_VALUE_BOOL, 0u, 2u, 0u};
    assert(reaper_dabi64_validate_value(&value) == REAPER_DABI64_INVALID_VALUE);
    value.kind = REAPER_DABI64_VALUE_UTF8;
    value.payload = 0u;
    value.length = 4u;
    assert(reaper_dabi64_validate_value(&value) == REAPER_DABI64_INVALID_VALUE);

    static const uint8_t valid_text[] = {0x52u, 0xd0u, 0xb5u, 0xd0u, 0xb0u, 0xd0u, 0xb5u};
    value.payload = (uint64_t)(uintptr_t)valid_text;
    value.length = sizeof valid_text;
    assert(reaper_dabi64_validate_value(&value) == REAPER_DABI64_OK);

    static const uint8_t overlong_utf8[] = {0xc0u, 0xafu};
    value.payload = (uint64_t)(uintptr_t)overlong_utf8;
    value.length = sizeof overlong_utf8;
    assert(reaper_dabi64_validate_value(&value) == REAPER_DABI64_INVALID_VALUE);

    static const uint8_t surrogate_utf8[] = {0xedu, 0xa0u, 0x80u};
    value.payload = (uint64_t)(uintptr_t)surrogate_utf8;
    value.length = sizeof surrogate_utf8;
    assert(reaper_dabi64_validate_value(&value) == REAPER_DABI64_INVALID_VALUE);
}

int main(void) {
    test_version_and_layout();
    test_call_contract();
    test_owned_value_release();
    test_rejects_invalid_values();
    puts("DABI64 ABI tests passed");
    return 0;
}
