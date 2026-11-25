#include "reaper/system.h"

#include <stdio.h>
#include <string.h>

#define OP(id, group, label, caps, effect_name) \
    { id, group, label, caps, effect_name }

static const ReaperSystemOperationInfo OPERATIONS[] = {
    OP(REAPER_SYSTEM_PROCESS_SPAWN, REAPER_SYSTEM_DOMAIN_PROCESS, "process.spawn", REAPER_SYSTEM_CAP_PROCESS_CONTROL, "process.spawn"),
    OP(REAPER_SYSTEM_PROCESS_WAIT, REAPER_SYSTEM_DOMAIN_PROCESS, "process.wait", REAPER_SYSTEM_CAP_PROCESS_INSPECT, "process.wait"),
    OP(REAPER_SYSTEM_PROCESS_SIGNAL, REAPER_SYSTEM_DOMAIN_PROCESS, "process.signal", REAPER_SYSTEM_CAP_PROCESS_CONTROL, "process.signal"),
    OP(REAPER_SYSTEM_PROCESS_EXIT, REAPER_SYSTEM_DOMAIN_PROCESS, "process.exit", REAPER_SYSTEM_CAP_PROCESS_CONTROL, "process.exit"),
    OP(REAPER_SYSTEM_PROCESS_CURRENT_ID, REAPER_SYSTEM_DOMAIN_PROCESS, "process.current_id", REAPER_SYSTEM_CAP_PROCESS_INSPECT, "process.inspect"),
    OP(REAPER_SYSTEM_PROCESS_PARENT_ID, REAPER_SYSTEM_DOMAIN_PROCESS, "process.parent_id", REAPER_SYSTEM_CAP_PROCESS_INSPECT, "process.inspect"),

    OP(REAPER_SYSTEM_THREAD_SPAWN, REAPER_SYSTEM_DOMAIN_THREAD, "thread.spawn", REAPER_SYSTEM_CAP_THREAD_CONTROL, "thread.spawn"),
    OP(REAPER_SYSTEM_THREAD_JOIN, REAPER_SYSTEM_DOMAIN_THREAD, "thread.join", REAPER_SYSTEM_CAP_THREAD_CONTROL, "thread.join"),
    OP(REAPER_SYSTEM_THREAD_DETACH, REAPER_SYSTEM_DOMAIN_THREAD, "thread.detach", REAPER_SYSTEM_CAP_THREAD_CONTROL, "thread.detach"),
    OP(REAPER_SYSTEM_THREAD_YIELD, REAPER_SYSTEM_DOMAIN_THREAD, "thread.yield", REAPER_SYSTEM_CAP_THREAD_CONTROL, "thread.schedule"),
    OP(REAPER_SYSTEM_THREAD_SLEEP, REAPER_SYSTEM_DOMAIN_THREAD, "thread.sleep", REAPER_SYSTEM_CAP_THREAD_CONTROL, "thread.schedule"),
    OP(REAPER_SYSTEM_THREAD_SET_PRIORITY, REAPER_SYSTEM_DOMAIN_THREAD, "thread.set_priority", REAPER_SYSTEM_CAP_THREAD_CONTROL, "thread.priority"),

    OP(REAPER_SYSTEM_SYNC_MUTEX_CREATE, REAPER_SYSTEM_DOMAIN_SYNC, "sync.mutex_create", REAPER_SYSTEM_CAP_SYNC, "sync.create"),
    OP(REAPER_SYSTEM_SYNC_MUTEX_LOCK, REAPER_SYSTEM_DOMAIN_SYNC, "sync.mutex_lock", REAPER_SYSTEM_CAP_SYNC, "sync.block"),
    OP(REAPER_SYSTEM_SYNC_MUTEX_UNLOCK, REAPER_SYSTEM_DOMAIN_SYNC, "sync.mutex_unlock", REAPER_SYSTEM_CAP_SYNC, "sync.mutate"),
    OP(REAPER_SYSTEM_SYNC_SEMAPHORE_POST, REAPER_SYSTEM_DOMAIN_SYNC, "sync.semaphore_post", REAPER_SYSTEM_CAP_SYNC, "sync.signal"),
    OP(REAPER_SYSTEM_SYNC_SEMAPHORE_WAIT, REAPER_SYSTEM_DOMAIN_SYNC, "sync.semaphore_wait", REAPER_SYSTEM_CAP_SYNC, "sync.block"),
    OP(REAPER_SYSTEM_SYNC_EVENT_SIGNAL, REAPER_SYSTEM_DOMAIN_SYNC, "sync.event_signal", REAPER_SYSTEM_CAP_SYNC, "sync.signal"),

    OP(REAPER_SYSTEM_FS_OPEN, REAPER_SYSTEM_DOMAIN_FILESYSTEM, "fs.open", REAPER_SYSTEM_CAP_FS_HANDLE, "fs.open"),
    OP(REAPER_SYSTEM_FS_READ, REAPER_SYSTEM_DOMAIN_FILESYSTEM, "fs.read", REAPER_SYSTEM_CAP_FS_READ, "fs.read"),
    OP(REAPER_SYSTEM_FS_WRITE, REAPER_SYSTEM_DOMAIN_FILESYSTEM, "fs.write", REAPER_SYSTEM_CAP_FS_WRITE, "fs.write"),
    OP(REAPER_SYSTEM_FS_SEEK, REAPER_SYSTEM_DOMAIN_FILESYSTEM, "fs.seek", REAPER_SYSTEM_CAP_FS_HANDLE, "fs.seek"),
    OP(REAPER_SYSTEM_FS_STAT, REAPER_SYSTEM_DOMAIN_FILESYSTEM, "fs.stat", REAPER_SYSTEM_CAP_FS_HANDLE, "fs.metadata"),
    OP(REAPER_SYSTEM_FS_CLOSE, REAPER_SYSTEM_DOMAIN_FILESYSTEM, "fs.close", REAPER_SYSTEM_CAP_FS_HANDLE, "fs.close"),

    OP(REAPER_SYSTEM_CLOCK_MONOTONIC_NS, REAPER_SYSTEM_DOMAIN_CLOCK, "clock.monotonic_ns", REAPER_SYSTEM_CAP_CLOCK, "clock.read"),
    OP(REAPER_SYSTEM_CLOCK_REALTIME_NS, REAPER_SYSTEM_DOMAIN_CLOCK, "clock.realtime_ns", REAPER_SYSTEM_CAP_CLOCK, "clock.read"),
    OP(REAPER_SYSTEM_TIMER_CREATE, REAPER_SYSTEM_DOMAIN_CLOCK, "timer.create", REAPER_SYSTEM_CAP_CLOCK, "timer.create"),
    OP(REAPER_SYSTEM_TIMER_WAIT, REAPER_SYSTEM_DOMAIN_CLOCK, "timer.wait", REAPER_SYSTEM_CAP_CLOCK, "timer.wait"),
    OP(REAPER_SYSTEM_SLEEP_UNTIL, REAPER_SYSTEM_DOMAIN_CLOCK, "clock.sleep_until", REAPER_SYSTEM_CAP_CLOCK, "clock.block"),
    OP(REAPER_SYSTEM_DEADLINE_AFTER, REAPER_SYSTEM_DOMAIN_CLOCK, "clock.deadline_after", REAPER_SYSTEM_CAP_CLOCK, "clock.calculate"),

    OP(REAPER_SYSTEM_NET_SOCKET_OPEN, REAPER_SYSTEM_DOMAIN_NETWORK, "net.socket_open", REAPER_SYSTEM_CAP_NETWORK, "net.open"),
    OP(REAPER_SYSTEM_NET_CONNECT, REAPER_SYSTEM_DOMAIN_NETWORK, "net.connect", REAPER_SYSTEM_CAP_NETWORK, "net.connect"),
    OP(REAPER_SYSTEM_NET_SEND, REAPER_SYSTEM_DOMAIN_NETWORK, "net.send", REAPER_SYSTEM_CAP_NETWORK, "net.write"),
    OP(REAPER_SYSTEM_NET_RECEIVE, REAPER_SYSTEM_DOMAIN_NETWORK, "net.receive", REAPER_SYSTEM_CAP_NETWORK, "net.read"),
    OP(REAPER_SYSTEM_NET_SHUTDOWN, REAPER_SYSTEM_DOMAIN_NETWORK, "net.shutdown", REAPER_SYSTEM_CAP_NETWORK, "net.close"),
    OP(REAPER_SYSTEM_NET_RESOLVE, REAPER_SYSTEM_DOMAIN_NETWORK, "net.resolve", REAPER_SYSTEM_CAP_NETWORK, "net.resolve"),

    OP(REAPER_SYSTEM_CRYPTO_RANDOM_FILL, REAPER_SYSTEM_DOMAIN_CRYPTO, "crypto.random_fill", REAPER_SYSTEM_CAP_CRYPTO, "crypto.entropy"),
    OP(REAPER_SYSTEM_CRYPTO_SHA256, REAPER_SYSTEM_DOMAIN_CRYPTO, "crypto.sha256", REAPER_SYSTEM_CAP_CRYPTO, "crypto.hash"),
    OP(REAPER_SYSTEM_CRYPTO_HMAC_SHA256, REAPER_SYSTEM_DOMAIN_CRYPTO, "crypto.hmac_sha256", REAPER_SYSTEM_CAP_CRYPTO, "crypto.authenticate"),
    OP(REAPER_SYSTEM_CRYPTO_CONSTANT_TIME_EQUAL, REAPER_SYSTEM_DOMAIN_CRYPTO, "crypto.constant_time_equal", REAPER_SYSTEM_CAP_CRYPTO, "crypto.compare"),
    OP(REAPER_SYSTEM_CRYPTO_ZEROIZE, REAPER_SYSTEM_DOMAIN_CRYPTO, "crypto.zeroize", REAPER_SYSTEM_CAP_CRYPTO, "crypto.erase"),
    OP(REAPER_SYSTEM_CRYPTO_KEY_IMPORT, REAPER_SYSTEM_DOMAIN_CRYPTO, "crypto.key_import", REAPER_SYSTEM_CAP_CRYPTO, "crypto.key_import")
};

#undef OP

static void set_error(ReaperSystemError *error, ReaperSystemStatus status,
                      ReaperSystemOperation operation, const char *message) {
    if (error == NULL) return;
    error->status = status;
    error->operation = operation;
    (void)snprintf(error->message, sizeof(error->message), "%s", message);
}

size_t reaper_system_operation_count(void) {
    return sizeof(OPERATIONS) / sizeof(OPERATIONS[0]);
}

const ReaperSystemOperationInfo *reaper_system_operation_at(size_t index) {
    return index < reaper_system_operation_count() ? &OPERATIONS[index] : NULL;
}

const ReaperSystemOperationInfo *reaper_system_operation_find(
    ReaperSystemOperation operation
) {
    size_t index;
    for (index = 0U; index < reaper_system_operation_count(); ++index) {
        if (OPERATIONS[index].operation == operation) return &OPERATIONS[index];
    }
    return NULL;
}

ReaperSystemStatus reaper_system_host_validate(
    const ReaperSystemHost *host,
    ReaperSystemError *error
) {
    if (host == NULL) {
        set_error(error, REAPER_SYSTEM_INVALID_ARGUMENT, REAPER_SYSTEM_OP_INVALID,
                  "host is null");
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    }
    if (host->abi_version != REAPER_SYSTEM_ABI_VERSION ||
        host->struct_size < (uint32_t)sizeof(ReaperSystemHost)) {
        set_error(error, REAPER_SYSTEM_UNSUPPORTED_ABI, REAPER_SYSTEM_OP_INVALID,
                  "host ABI version or structure size is unsupported");
        return REAPER_SYSTEM_UNSUPPORTED_ABI;
    }
    if (host->dispatch == NULL ||
        (host->granted_capabilities & ~REAPER_SYSTEM_CAP_KNOWN_MASK) != 0U) {
        set_error(error, REAPER_SYSTEM_INVALID_ARGUMENT, REAPER_SYSTEM_OP_INVALID,
                  "host dispatch or capability mask is invalid");
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    }
    set_error(error, REAPER_SYSTEM_OK, REAPER_SYSTEM_OP_INVALID, "ok");
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_invoke(
    const ReaperSystemHost *host,
    ReaperSystemOperation operation,
    const void *input,
    size_t input_size,
    void *output,
    size_t output_capacity,
    size_t *output_size,
    ReaperSystemError *error
) {
    const ReaperSystemOperationInfo *info;
    ReaperSystemStatus status;
    size_t produced = 0U;
    int host_status;

    if (output_size == NULL) {
        set_error(error, REAPER_SYSTEM_INVALID_ARGUMENT, operation,
                  "output_size is required");
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    }
    *output_size = 0U;

    status = reaper_system_host_validate(host, error);
    if (status != REAPER_SYSTEM_OK) {
        if (error != NULL) error->operation = operation;
        return status;
    }

    info = reaper_system_operation_find(operation);
    if (info == NULL) {
        set_error(error, REAPER_SYSTEM_UNKNOWN_OPERATION, operation,
                  "operation is not registered in system ABI v1");
        return REAPER_SYSTEM_UNKNOWN_OPERATION;
    }
    if ((host->granted_capabilities & info->required_capabilities) !=
        info->required_capabilities) {
        set_error(error, REAPER_SYSTEM_ACCESS_DENIED, operation,
                  "host did not grant the operation capability");
        return REAPER_SYSTEM_ACCESS_DENIED;
    }
    if ((input_size > 0U && input == NULL) ||
        (output_capacity > 0U && output == NULL)) {
        set_error(error, REAPER_SYSTEM_INVALID_ARGUMENT, operation,
                  "non-empty buffers require valid pointers");
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    }
    if (input_size > REAPER_SYSTEM_MAX_IO_BYTES ||
        output_capacity > REAPER_SYSTEM_MAX_IO_BYTES) {
        set_error(error, REAPER_SYSTEM_IO_LIMIT, operation,
                  "system ABI buffers exceed the one MiB limit");
        return REAPER_SYSTEM_IO_LIMIT;
    }

    host_status = host->dispatch(host->context, operation, input, input_size,
                                 output, output_capacity, &produced);
    if (host_status != 0) {
        set_error(error, REAPER_SYSTEM_HOST_FAILURE, operation,
                  "host adapter reported an operation failure");
        return REAPER_SYSTEM_HOST_FAILURE;
    }
    if (produced > output_capacity) {
        set_error(error, REAPER_SYSTEM_HOST_CONTRACT_VIOLATION, operation,
                  "host adapter returned a size larger than output capacity");
        return REAPER_SYSTEM_HOST_CONTRACT_VIOLATION;
    }

    *output_size = produced;
    set_error(error, REAPER_SYSTEM_OK, operation, "ok");
    return REAPER_SYSTEM_OK;
}

const char *reaper_system_status_name(ReaperSystemStatus status) {
    switch (status) {
        case REAPER_SYSTEM_OK: return "ok";
        case REAPER_SYSTEM_INVALID_ARGUMENT: return "invalid-argument";
        case REAPER_SYSTEM_UNSUPPORTED_ABI: return "unsupported-abi";
        case REAPER_SYSTEM_UNKNOWN_OPERATION: return "unknown-operation";
        case REAPER_SYSTEM_ACCESS_DENIED: return "access-denied";
        case REAPER_SYSTEM_IO_LIMIT: return "io-limit";
        case REAPER_SYSTEM_HOST_FAILURE: return "host-failure";
        case REAPER_SYSTEM_HOST_CONTRACT_VIOLATION: return "host-contract-violation";
    }
    return "unknown-status";
}
