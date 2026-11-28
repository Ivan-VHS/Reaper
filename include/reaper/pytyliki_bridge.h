#ifndef REAPER_PYTYLIKI_BRIDGE_H
#define REAPER_PYTYLIKI_BRIDGE_H

#include <stdint.h>
#include "native_intelligence.h"

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_PYTYLIKI_ABI_VERSION UINT32_C(1)

typedef enum {
    REAPER_PYTYLIKI_OK = 0,
    REAPER_PYTYLIKI_INVALID_ARGUMENT,
    REAPER_PYTYLIKI_ABI_MISMATCH,
    REAPER_PYTYLIKI_PROVIDER_FAILURE,
    REAPER_PYTYLIKI_INVALID_SNAPSHOT,
    REAPER_PYTYLIKI_STALE_PLACEMENT
} ReaperPytylikiStatus;

typedef struct {
    uint32_t (*abi_version)(void);
    int32_t (*snapshot_descriptor)(uint32_t *contract_version,
                                   uint64_t *structure_size);
    int32_t (*snapshot_collect)(pl_ni_snapshot *out, uint64_t capacity);
    int32_t (*placement)(const pl_ni_snapshot *snapshot,
                         const pl_ppf_request *request,
                         const pl_ppf_telemetry *telemetry,
                         uint64_t telemetry_count,
                         pl_ppf_report *out);
} ReaperPytylikiProvider;

/* The caller supplies trusted, explicitly acquired function pointers.
 * This adapter never loads a library or changes process/thread affinity. */
ReaperPytylikiStatus reaper_pytyliki_snapshot_read(
    const ReaperPytylikiProvider *provider,
    pl_ni_snapshot *out
);

ReaperPytylikiStatus reaper_pytyliki_plan_placement(
    const ReaperPytylikiProvider *provider,
    const pl_ppf_request *request,
    const pl_ppf_telemetry *telemetry,
    uint64_t telemetry_count,
    pl_ni_snapshot *snapshot_out,
    pl_ppf_report *report_out
);

#ifdef __cplusplus
}
#endif
#endif
