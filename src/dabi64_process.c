#include "reaper/dabi64_process.h"

#include <string.h>

ReaperDabiStatus reaper_dabi_process_dispatch(
    const ReaperDabiHostV1 *host,
    const ReaperDabiAllocator *allocator,
    ReaperDabiEntryV1 entry,
    uint64_t argc,
    const char *const *argv,
    uint64_t envc,
    const char *const *envp,
    ReaperDabiProcessResult *result
) {
    ReaperDabiRuntime runtime;
    ReaperDabiStatus status;
    if (result != NULL) memset(result, 0, sizeof *result);
    if (host == NULL || entry == NULL || result == NULL ||
        (argc != 0u && argv == NULL) || (envc != 0u && envp == NULL))
        return REAPER_DABI_INVALID_ARGUMENT;

    status = reaper_dabi_runtime_init(&runtime, host, allocator);
    if (status != REAPER_DABI_OK) return status;
    result->exit_code = entry(&runtime, argc, argv, envc, envp);
    result->live_objects_at_exit = runtime.live_objects;

    status = reaper_dabi_runtime_destroy(&runtime);
    if (status != REAPER_DABI_OK) return REAPER_DABI_CLOSED;
    return REAPER_DABI_OK;
}
