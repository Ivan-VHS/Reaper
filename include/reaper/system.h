#ifndef REAPER_SYSTEM_H
#define REAPER_SYSTEM_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_SYSTEM_ABI_VERSION 1U
#define REAPER_SYSTEM_MAX_IO_BYTES (1024U * 1024U)

#define REAPER_SYSTEM_CAP_PROCESS_INSPECT (UINT64_C(1) << 0)
#define REAPER_SYSTEM_CAP_PROCESS_CONTROL (UINT64_C(1) << 1)
#define REAPER_SYSTEM_CAP_THREAD_CONTROL (UINT64_C(1) << 2)
#define REAPER_SYSTEM_CAP_SYNC (UINT64_C(1) << 3)
#define REAPER_SYSTEM_CAP_FS_HANDLE (UINT64_C(1) << 4)
#define REAPER_SYSTEM_CAP_FS_READ (UINT64_C(1) << 5)
#define REAPER_SYSTEM_CAP_FS_WRITE (UINT64_C(1) << 6)
#define REAPER_SYSTEM_CAP_CLOCK (UINT64_C(1) << 7)
#define REAPER_SYSTEM_CAP_NETWORK (UINT64_C(1) << 8)
#define REAPER_SYSTEM_CAP_CRYPTO (UINT64_C(1) << 9)
#define REAPER_SYSTEM_CAP_DESKTOP_DISPLAY_READ (UINT64_C(1) << 10)
#define REAPER_SYSTEM_CAP_DESKTOP_WINDOW_CREATE (UINT64_C(1) << 11)
#define REAPER_SYSTEM_CAP_DESKTOP_WINDOW_CONTROL (UINT64_C(1) << 12)
#define REAPER_SYSTEM_CAP_DESKTOP_SURFACE_PRESENT (UINT64_C(1) << 13)
#define REAPER_SYSTEM_CAP_DESKTOP_INPUT_READ (UINT64_C(1) << 14)
#define REAPER_SYSTEM_CAP_DESKTOP_SESSION_CONTROL (UINT64_C(1) << 15)
#define REAPER_SYSTEM_CAP_DESKTOP_NOTIFICATION_POST (UINT64_C(1) << 16)
#define REAPER_SYSTEM_CAP_KNOWN_MASK ((UINT64_C(1) << 17) - UINT64_C(1))

typedef enum {
    REAPER_SYSTEM_DOMAIN_INVALID = 0,
    REAPER_SYSTEM_DOMAIN_PROCESS,
    REAPER_SYSTEM_DOMAIN_THREAD,
    REAPER_SYSTEM_DOMAIN_SYNC,
    REAPER_SYSTEM_DOMAIN_FILESYSTEM,
    REAPER_SYSTEM_DOMAIN_CLOCK,
    REAPER_SYSTEM_DOMAIN_NETWORK,
    REAPER_SYSTEM_DOMAIN_CRYPTO,
    REAPER_SYSTEM_DOMAIN_DESKTOP
} ReaperSystemDomain;

typedef enum {
    REAPER_SYSTEM_OP_INVALID = 0,
    REAPER_SYSTEM_PROCESS_SPAWN = 0x1001,
    REAPER_SYSTEM_PROCESS_WAIT = 0x1002,
    REAPER_SYSTEM_PROCESS_SIGNAL = 0x1003,
    REAPER_SYSTEM_PROCESS_EXIT = 0x1004,
    REAPER_SYSTEM_PROCESS_CURRENT_ID = 0x1005,
    REAPER_SYSTEM_PROCESS_PARENT_ID = 0x1006,
    REAPER_SYSTEM_THREAD_SPAWN = 0x2001,
    REAPER_SYSTEM_THREAD_JOIN = 0x2002,
    REAPER_SYSTEM_THREAD_DETACH = 0x2003,
    REAPER_SYSTEM_THREAD_YIELD = 0x2004,
    REAPER_SYSTEM_THREAD_SLEEP = 0x2005,
    REAPER_SYSTEM_THREAD_SET_PRIORITY = 0x2006,
    REAPER_SYSTEM_SYNC_MUTEX_CREATE = 0x3001,
    REAPER_SYSTEM_SYNC_MUTEX_LOCK = 0x3002,
    REAPER_SYSTEM_SYNC_MUTEX_UNLOCK = 0x3003,
    REAPER_SYSTEM_SYNC_SEMAPHORE_POST = 0x3004,
    REAPER_SYSTEM_SYNC_SEMAPHORE_WAIT = 0x3005,
    REAPER_SYSTEM_SYNC_EVENT_SIGNAL = 0x3006,
    REAPER_SYSTEM_FS_OPEN = 0x4001,
    REAPER_SYSTEM_FS_READ = 0x4002,
    REAPER_SYSTEM_FS_WRITE = 0x4003,
    REAPER_SYSTEM_FS_SEEK = 0x4004,
    REAPER_SYSTEM_FS_STAT = 0x4005,
    REAPER_SYSTEM_FS_CLOSE = 0x4006,
    REAPER_SYSTEM_CLOCK_MONOTONIC_NS = 0x5001,
    REAPER_SYSTEM_CLOCK_REALTIME_NS = 0x5002,
    REAPER_SYSTEM_TIMER_CREATE = 0x5003,
    REAPER_SYSTEM_TIMER_WAIT = 0x5004,
    REAPER_SYSTEM_SLEEP_UNTIL = 0x5005,
    REAPER_SYSTEM_DEADLINE_AFTER = 0x5006,
    REAPER_SYSTEM_NET_SOCKET_OPEN = 0x6001,
    REAPER_SYSTEM_NET_CONNECT = 0x6002,
    REAPER_SYSTEM_NET_SEND = 0x6003,
    REAPER_SYSTEM_NET_RECEIVE = 0x6004,
    REAPER_SYSTEM_NET_SHUTDOWN = 0x6005,
    REAPER_SYSTEM_NET_RESOLVE = 0x6006,
    REAPER_SYSTEM_CRYPTO_RANDOM_FILL = 0x7001,
    REAPER_SYSTEM_CRYPTO_SHA256 = 0x7002,
    REAPER_SYSTEM_CRYPTO_HMAC_SHA256 = 0x7003,
    REAPER_SYSTEM_CRYPTO_CONSTANT_TIME_EQUAL = 0x7004,
    REAPER_SYSTEM_CRYPTO_ZEROIZE = 0x7005,
    REAPER_SYSTEM_CRYPTO_KEY_IMPORT = 0x7006,
    REAPER_SYSTEM_DESKTOP_OUTPUT_ENUMERATE = 0x8001,
    REAPER_SYSTEM_DESKTOP_SURFACE_CREATE = 0x8002,
    REAPER_SYSTEM_DESKTOP_SURFACE_COMMIT = 0x8003,
    REAPER_SYSTEM_DESKTOP_WINDOW_CREATE = 0x8004,
    REAPER_SYSTEM_DESKTOP_WINDOW_CONFIGURE = 0x8005,
    REAPER_SYSTEM_DESKTOP_WINDOW_DESTROY = 0x8006,
    REAPER_SYSTEM_DESKTOP_WINDOW_FOCUS = 0x8007,
    REAPER_SYSTEM_DESKTOP_INPUT_READ = 0x8008,
    REAPER_SYSTEM_DESKTOP_SESSION_SWITCH = 0x8009,
    REAPER_SYSTEM_DESKTOP_NOTIFICATION_POST = 0x800A
} ReaperSystemOperation;

typedef enum {
    REAPER_SYSTEM_OK = 0,
    REAPER_SYSTEM_INVALID_ARGUMENT = -1,
    REAPER_SYSTEM_UNSUPPORTED_ABI = -2,
    REAPER_SYSTEM_UNKNOWN_OPERATION = -3,
    REAPER_SYSTEM_ACCESS_DENIED = -4,
    REAPER_SYSTEM_IO_LIMIT = -5,
    REAPER_SYSTEM_HOST_FAILURE = -6,
    REAPER_SYSTEM_HOST_CONTRACT_VIOLATION = -7
} ReaperSystemStatus;

typedef struct {
    ReaperSystemOperation operation;
    ReaperSystemDomain domain;
    const char *name;
    uint64_t required_capabilities;
    const char *effect;
} ReaperSystemOperationInfo;

/*
 * The host is trusted platform code: DuckOS, an OS adapter, a simulator or a
 * reviewed system library. Reaper validates the ABI, operation, capability
 * grant and bounded buffers before entering the adapter. The adapter must
 * validate operation-specific payloads and must not retain input/output
 * pointers after dispatch returns.
 */
typedef int (*ReaperSystemDispatch)(
    void *context,
    ReaperSystemOperation operation,
    const void *input,
    size_t input_size,
    void *output,
    size_t output_capacity,
    size_t *output_size
);

typedef struct {
    uint32_t abi_version;
    uint32_t struct_size;
    uint64_t granted_capabilities;
    void *context;
    ReaperSystemDispatch dispatch;
} ReaperSystemHost;

typedef struct {
    ReaperSystemStatus status;
    ReaperSystemOperation operation;
    char message[160];
} ReaperSystemError;

size_t reaper_system_operation_count(void);
const ReaperSystemOperationInfo *reaper_system_operation_at(size_t index);
const ReaperSystemOperationInfo *reaper_system_operation_find(
    ReaperSystemOperation operation
);

ReaperSystemStatus reaper_system_host_validate(
    const ReaperSystemHost *host,
    ReaperSystemError *error
);

ReaperSystemStatus reaper_system_invoke(
    const ReaperSystemHost *host,
    ReaperSystemOperation operation,
    const void *input,
    size_t input_size,
    void *output,
    size_t output_capacity,
    size_t *output_size,
    ReaperSystemError *error
);

const char *reaper_system_status_name(ReaperSystemStatus status);

#ifdef __cplusplus
}
#endif

#endif
