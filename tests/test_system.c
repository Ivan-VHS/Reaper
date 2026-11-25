#include "reaper/system.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    ReaperSystemOperation last_operation;
    unsigned calls;
    int fail;
    int report_oversize;
} FakeHost;

static int fake_dispatch(void *context, ReaperSystemOperation operation,
                         const void *input, size_t input_size, void *output,
                         size_t output_capacity, size_t *output_size) {
    FakeHost *fake = (FakeHost *)context;
    fake->last_operation = operation;
    fake->calls += 1U;
    if (fake->fail) return -1;
    if (fake->report_oversize) {
        *output_size = output_capacity + 1U;
        return 0;
    }
    if (input_size > 0U && output_capacity > 0U) {
        size_t copied = input_size < output_capacity ? input_size : output_capacity;
        (void)memcpy(output, input, copied);
        *output_size = copied;
    } else {
        *output_size = 0U;
    }
    return 0;
}

static ReaperSystemHost make_host(FakeHost *fake, uint64_t capabilities) {
    ReaperSystemHost host;
    host.abi_version = REAPER_SYSTEM_ABI_VERSION;
    host.struct_size = (uint32_t)sizeof(host);
    host.granted_capabilities = capabilities;
    host.context = fake;
    host.dispatch = fake_dispatch;
    return host;
}

static void test_catalog(void) {
    size_t index;
    assert(reaper_system_operation_count() == 42U);
    for (index = 0U; index < reaper_system_operation_count(); ++index) {
        const ReaperSystemOperationInfo *info = reaper_system_operation_at(index);
        assert(info != NULL);
        assert(info->operation != REAPER_SYSTEM_OP_INVALID);
        assert(info->name != NULL && info->name[0] != '\0');
        assert(info->effect != NULL && info->effect[0] != '\0');
        assert(reaper_system_operation_find(info->operation) == info);
    }
    assert(reaper_system_operation_at(42U) == NULL);
    assert(reaper_system_operation_find((ReaperSystemOperation)0x7fff) == NULL);
}

static void test_host_validation(void) {
    FakeHost fake = {0};
    ReaperSystemHost host = make_host(&fake, REAPER_SYSTEM_CAP_PROCESS_INSPECT);
    ReaperSystemError error;
    assert(reaper_system_host_validate(&host, &error) == REAPER_SYSTEM_OK);
    assert(reaper_system_host_validate(NULL, &error) == REAPER_SYSTEM_INVALID_ARGUMENT);
    host.abi_version = 99U;
    assert(reaper_system_host_validate(&host, &error) == REAPER_SYSTEM_UNSUPPORTED_ABI);
    host.abi_version = REAPER_SYSTEM_ABI_VERSION;
    host.struct_size = 1U;
    assert(reaper_system_host_validate(&host, &error) == REAPER_SYSTEM_UNSUPPORTED_ABI);
    host = make_host(&fake, UINT64_C(1) << 63);
    assert(reaper_system_host_validate(&host, &error) == REAPER_SYSTEM_INVALID_ARGUMENT);
    host = make_host(&fake, REAPER_SYSTEM_CAP_PROCESS_INSPECT);
    host.dispatch = NULL;
    assert(reaper_system_host_validate(&host, &error) == REAPER_SYSTEM_INVALID_ARGUMENT);
}

static void test_rights_and_unknown_operations(void) {
    FakeHost fake = {0};
    ReaperSystemHost host = make_host(&fake, REAPER_SYSTEM_CAP_PROCESS_INSPECT);
    ReaperSystemError error;
    size_t output_size = 99U;
    assert(reaper_system_invoke(&host, REAPER_SYSTEM_PROCESS_SPAWN,
                                NULL, 0U, NULL, 0U, &output_size, &error) ==
           REAPER_SYSTEM_ACCESS_DENIED);
    assert(output_size == 0U);
    assert(fake.calls == 0U);
    assert(reaper_system_invoke(&host, (ReaperSystemOperation)0x7fff,
                                NULL, 0U, NULL, 0U, &output_size, &error) ==
           REAPER_SYSTEM_UNKNOWN_OPERATION);
    assert(fake.calls == 0U);
}

static void test_bounded_dispatch(void) {
    FakeHost fake = {0};
    ReaperSystemHost host = make_host(&fake, REAPER_SYSTEM_CAP_FS_HANDLE |
                                              REAPER_SYSTEM_CAP_FS_READ);
    ReaperSystemError error;
    const char input[] = "bounded-payload";
    char output[sizeof(input)] = {0};
    size_t output_size = 0U;
    assert(reaper_system_invoke(&host, REAPER_SYSTEM_FS_READ,
                                input, sizeof(input), output, sizeof(output),
                                &output_size, &error) == REAPER_SYSTEM_OK);
    assert(output_size == sizeof(input));
    assert(memcmp(input, output, sizeof(input)) == 0);
    assert(fake.last_operation == REAPER_SYSTEM_FS_READ);
    assert(fake.calls == 1U);

    assert(reaper_system_invoke(&host, REAPER_SYSTEM_FS_READ,
                                NULL, 1U, output, sizeof(output),
                                &output_size, &error) == REAPER_SYSTEM_INVALID_ARGUMENT);
    assert(reaper_system_invoke(&host, REAPER_SYSTEM_FS_READ,
                                input, sizeof(input), NULL, 1U,
                                &output_size, &error) == REAPER_SYSTEM_INVALID_ARGUMENT);
    assert(reaper_system_invoke(&host, REAPER_SYSTEM_FS_READ,
                                input, REAPER_SYSTEM_MAX_IO_BYTES + 1U,
                                output, sizeof(output), &output_size, &error) ==
           REAPER_SYSTEM_IO_LIMIT);
    assert(fake.calls == 1U);
}

static void test_host_failures_and_contract_violation(void) {
    FakeHost fake = {0};
    ReaperSystemHost host = make_host(&fake, REAPER_SYSTEM_CAP_CLOCK);
    ReaperSystemError error;
    size_t output_size = 55U;
    fake.fail = 1;
    assert(reaper_system_invoke(&host, REAPER_SYSTEM_CLOCK_MONOTONIC_NS,
                                NULL, 0U, NULL, 0U, &output_size, &error) ==
           REAPER_SYSTEM_HOST_FAILURE);
    assert(output_size == 0U);
    fake.fail = 0;
    fake.report_oversize = 1;
    assert(reaper_system_invoke(&host, REAPER_SYSTEM_CLOCK_MONOTONIC_NS,
                                NULL, 0U, NULL, 0U, &output_size, &error) ==
           REAPER_SYSTEM_HOST_CONTRACT_VIOLATION);
    assert(output_size == 0U);
    assert(strcmp(reaper_system_status_name(REAPER_SYSTEM_ACCESS_DENIED),
                  "access-denied") == 0);
}

int main(void) {
    test_catalog();
    test_host_validation();
    test_rights_and_unknown_operations();
    test_bounded_dispatch();
    test_host_failures_and_contract_violation();
    puts("reaper system API tests passed");
    return 0;
}
