#include "reaper/system_bridge.h"

#include <stdio.h>
#include <string.h>

#if defined(_MSC_VER)
#define REAPER_THREAD_LOCAL __declspec(thread)
#else
#define REAPER_THREAD_LOCAL _Thread_local
#endif

#define REAPER_SYSTEM_OPERATION_NAME_MAX 127U

static REAPER_THREAD_LOCAL ReaperSystemHost current_host;
static REAPER_THREAD_LOCAL int host_attached;
static REAPER_THREAD_LOCAL ReaperSystemStatus last_status;
static REAPER_THREAD_LOCAL char last_error[160];
static REAPER_THREAD_LOCAL char response_buffer[REAPER_SYSTEM_JSON_MAX_BYTES + 1U];

static void set_last_error(
    ReaperSystemStatus status,
    const char *message,
    ReaperSystemError *error
) {
    last_status = status;
    (void)snprintf(last_error, sizeof(last_error), "%s", message);

    if (error != NULL) {
        error->status = status;
        error->operation = REAPER_SYSTEM_OP_INVALID;
        (void)snprintf(error->message, sizeof(error->message), "%s", message);
    }
}

static size_t bounded_length(const char *value, size_t maximum) {
    size_t length;

    for (length = 0U; length <= maximum; ++length) {
        if (value[length] == '\0') {
            return length;
        }
    }

    return maximum + 1U;
}

static const ReaperSystemOperationInfo *find_operation_name(const char *name) {
    size_t index;

    for (index = 0U; index < reaper_system_operation_count(); ++index) {
        const ReaperSystemOperationInfo *operation =
            reaper_system_operation_at(index);

        if (operation != NULL && strcmp(operation->name, name) == 0) {
            return operation;
        }
    }

    return NULL;
}

ReaperSystemStatus reaper_system_host_attach(
    const ReaperSystemHost *host,
    ReaperSystemError *error
) {
    ReaperSystemStatus status;

    if (host_attached) {
        set_last_error(
            REAPER_SYSTEM_INVALID_ARGUMENT,
            "a system host is already attached to this thread",
            error
        );
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    }

    status = reaper_system_host_validate(host, error);
    if (status != REAPER_SYSTEM_OK) {
        last_status = status;
        if (error != NULL) {
            (void)snprintf(last_error, sizeof(last_error), "%s", error->message);
        } else {
            (void)snprintf(last_error, sizeof(last_error), "%s",
                           reaper_system_status_name(status));
        }
        return status;
    }

    current_host = *host;
    host_attached = 1;
    response_buffer[0] = '\0';
    set_last_error(REAPER_SYSTEM_OK, "ok", error);
    return REAPER_SYSTEM_OK;
}

void reaper_system_host_detach(void) {
    (void)memset(&current_host, 0, sizeof(current_host));
    host_attached = 0;
    response_buffer[0] = '\0';
    set_last_error(REAPER_SYSTEM_ACCESS_DENIED,
                   "no system host is attached to this thread", NULL);
}

const char *reaper_system_call_json(
    const char *operation_name,
    const char *request_json
) {
    const ReaperSystemOperationInfo *operation;
    size_t operation_length;
    size_t request_length;
    size_t response_length = 0U;
    ReaperSystemStatus status;

    response_buffer[0] = '\0';

    if (!host_attached) {
        set_last_error(REAPER_SYSTEM_ACCESS_DENIED,
                       "no system host is attached to this thread", NULL);
        return NULL;
    }

    if (operation_name == NULL || request_json == NULL) {
        set_last_error(REAPER_SYSTEM_INVALID_ARGUMENT,
                       "operation name and JSON request are required", NULL);
        return NULL;
    }

    operation_length = bounded_length(
        operation_name, REAPER_SYSTEM_OPERATION_NAME_MAX
    );
    if (operation_length == 0U ||
        operation_length > REAPER_SYSTEM_OPERATION_NAME_MAX) {
        set_last_error(REAPER_SYSTEM_INVALID_ARGUMENT,
                       "operation name is empty or exceeds 127 bytes", NULL);
        return NULL;
    }

    request_length = bounded_length(
        request_json, (size_t)REAPER_SYSTEM_JSON_MAX_BYTES
    );
    if (request_length == 0U ||
        request_length > (size_t)REAPER_SYSTEM_JSON_MAX_BYTES) {
        set_last_error(REAPER_SYSTEM_IO_LIMIT,
                       "JSON request is empty or exceeds 64 KiB", NULL);
        return NULL;
    }

    operation = find_operation_name(operation_name);
    if (operation == NULL) {
        set_last_error(REAPER_SYSTEM_UNKNOWN_OPERATION,
                       "operation name is not registered in system ABI v1",
                       NULL);
        return NULL;
    }

    status = reaper_system_invoke(
        &current_host,
        operation->operation,
        request_json,
        request_length,
        response_buffer,
        (size_t)REAPER_SYSTEM_JSON_MAX_BYTES,
        &response_length,
        NULL
    );
    if (status != REAPER_SYSTEM_OK) {
        set_last_error(status, reaper_system_status_name(status), NULL);
        return NULL;
    }

    if (response_length == 0U ||
        memchr(response_buffer, '\0', response_length) != NULL) {
        set_last_error(
            REAPER_SYSTEM_HOST_CONTRACT_VIOLATION,
            "host response must be non-empty and contain no embedded NUL",
            NULL
        );
        return NULL;
    }

    response_buffer[response_length] = '\0';
    set_last_error(REAPER_SYSTEM_OK, "ok", NULL);
    return response_buffer;
}

int32_t reaper_system_last_status(void) {
    return (int32_t)last_status;
}

const char *reaper_system_last_error(void) {
    return last_error;
}
