#include "reaper/system_bridge.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    unsigned calls;
    int response_mode;
} FakeHost;

enum {
    RESPONSE_NORMAL = 0,
    RESPONSE_EMPTY,
    RESPONSE_EMBEDDED_NUL,
    RESPONSE_OVERSIZED
};

static int fake_dispatch(
    void *context,
    ReaperSystemOperation operation,
    const void *input,
    size_t input_size,
    void *output,
    size_t output_capacity,
    size_t *output_size
) {
    FakeHost *fake = (FakeHost *)context;
    static const char current_id[] = "{\"process_id\":42}";
    static const char thread_id[] = "{\"thread_id\":7}";

    fake->calls += 1U;

    if (operation != REAPER_SYSTEM_PROCESS_CURRENT_ID &&
        operation != REAPER_SYSTEM_THREAD_YIELD) {
        return -1;
    }

    if (input == NULL || input_size != 2U ||
        memcmp(input, "{}", 2U) != 0) {
        return -1;
    }

    if (fake->response_mode == RESPONSE_EMPTY) {
        *output_size = 0U;
        return 0;
    }

    if (fake->response_mode == RESPONSE_OVERSIZED) {
        *output_size = output_capacity + 1U;
        return 0;
    }

    if (fake->response_mode == RESPONSE_EMBEDDED_NUL) {
        if (output_capacity < 3U) {
            return -1;
        }
        ((char *)output)[0] = '{';
        ((char *)output)[1] = '\0';
        ((char *)output)[2] = '}';
        *output_size = 3U;
        return 0;
    }

    {
        const char *response = operation == REAPER_SYSTEM_PROCESS_CURRENT_ID
            ? current_id
            : thread_id;
        size_t length = strlen(response);

        if (length > output_capacity) {
            return -1;
        }

        (void)memcpy(output, response, length);
        *output_size = length;
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

static void test_requires_attachment(void) {
    reaper_system_host_detach();

    assert(reaper_system_call_json("process.current_id", "{}") == NULL);
    assert(reaper_system_last_status() == REAPER_SYSTEM_ACCESS_DENIED);
    assert(strstr(reaper_system_last_error(), "attached to this thread") != NULL);
}

static void test_capability_and_operation_checks(void) {
    FakeHost fake = {0};
    ReaperSystemHost host = make_host(&fake, 0U);
    ReaperSystemError error;

    assert(reaper_system_host_attach(&host, &error) == REAPER_SYSTEM_OK);
    assert(reaper_system_call_json("process.current_id", "{}") == NULL);
    assert(reaper_system_last_status() == REAPER_SYSTEM_ACCESS_DENIED);
    assert(fake.calls == 0U);

    assert(reaper_system_call_json("process.not_registered", "{}") == NULL);
    assert(reaper_system_last_status() == REAPER_SYSTEM_UNKNOWN_OPERATION);
    assert(fake.calls == 0U);

    reaper_system_host_detach();
}

static void test_json_dispatch_and_status(void) {
    FakeHost fake = {0};
    ReaperSystemHost host = make_host(
        &fake,
        REAPER_SYSTEM_CAP_PROCESS_INSPECT | REAPER_SYSTEM_CAP_THREAD_CONTROL
    );
    ReaperSystemError error;
    const char *response;

    assert(reaper_system_host_attach(&host, &error) == REAPER_SYSTEM_OK);
    response = reaper_system_call_json("process.current_id", "{}");
    assert(response != NULL);
    assert(strcmp(response, "{\"process_id\":42}") == 0);
    assert(reaper_system_last_status() == REAPER_SYSTEM_OK);
    assert(strcmp(reaper_system_last_error(), "ok") == 0);

    response = reaper_system_call_json("thread.yield", "{}");
    assert(response != NULL);
    assert(strcmp(response, "{\"thread_id\":7}") == 0);
    assert(fake.calls == 2U);

    assert(reaper_system_host_attach(&host, &error) ==
           REAPER_SYSTEM_INVALID_ARGUMENT);
    assert(reaper_system_last_status() == REAPER_SYSTEM_INVALID_ARGUMENT);

    reaper_system_host_detach();
}

static void test_response_contract_and_input_limits(void) {
    FakeHost fake = {0};
    ReaperSystemHost host = make_host(&fake, REAPER_SYSTEM_CAP_PROCESS_INSPECT);
    char oversized[REAPER_SYSTEM_JSON_MAX_BYTES + 2U];

    assert(reaper_system_host_attach(&host, NULL) == REAPER_SYSTEM_OK);

    fake.response_mode = RESPONSE_EMPTY;
    assert(reaper_system_call_json("process.current_id", "{}") == NULL);
    assert(reaper_system_last_status() ==
           REAPER_SYSTEM_HOST_CONTRACT_VIOLATION);

    fake.response_mode = RESPONSE_EMBEDDED_NUL;
    assert(reaper_system_call_json("process.current_id", "{}") == NULL);
    assert(reaper_system_last_status() ==
           REAPER_SYSTEM_HOST_CONTRACT_VIOLATION);

    fake.response_mode = RESPONSE_OVERSIZED;
    assert(reaper_system_call_json("process.current_id", "{}") == NULL);
    assert(reaper_system_last_status() ==
           REAPER_SYSTEM_HOST_CONTRACT_VIOLATION);

    memset(oversized, 'x', sizeof(oversized));
    oversized[sizeof(oversized) - 1U] = '\0';
    fake.response_mode = RESPONSE_NORMAL;
    assert(reaper_system_call_json("process.current_id", oversized) == NULL);
    assert(reaper_system_last_status() == REAPER_SYSTEM_IO_LIMIT);

    assert(reaper_system_call_json("", "{}") == NULL);
    assert(reaper_system_last_status() == REAPER_SYSTEM_INVALID_ARGUMENT);

    reaper_system_host_detach();
}

int main(void) {
    test_requires_attachment();
    test_capability_and_operation_checks();
    test_json_dispatch_and_thread_local_result();
    test_response_contract_and_input_limits();
    puts("reaper system language bridge tests passed");
    return 0;
}
