#ifndef REAPER_DABI64_PROCESS_H
#define REAPER_DABI64_PROCESS_H

#include "reaper/dabi64.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef int64_t (*ReaperDabiEntryV1)(
    ReaperDabiRuntime *runtime,
    uint64_t argc,
    const char *const *argv,
    uint64_t envc,
    const char *const *envp
);

typedef struct {
    int64_t exit_code;
    uint64_t live_objects_at_exit;
} ReaperDabiProcessResult;

/*
 * Host-side process entry dispatcher for a loaded DABI64 entry stub.
 * The caller owns the address space and reclaims it after return. A non-zero
 * live-object count is reported as REAPER_DABI_CLOSED; the dispatcher never
 * hides leaks by silently discarding owned runtime objects.
 */
ReaperDabiStatus reaper_dabi_process_dispatch(
    const ReaperDabiHostV1 *host,
    const ReaperDabiAllocator *allocator,
    ReaperDabiEntryV1 entry,
    uint64_t argc,
    const char *const *argv,
    uint64_t envc,
    const char *const *envp,
    ReaperDabiProcessResult *result
);

#ifdef __cplusplus
}
#endif

#endif
