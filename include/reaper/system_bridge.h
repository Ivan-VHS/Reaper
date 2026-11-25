#ifndef REAPER_SYSTEM_BRIDGE_H
#define REAPER_SYSTEM_BRIDGE_H

#include "reaper/system.h"

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_SYSTEM_JSON_MAX_BYTES (64U * 1024U)

/*
 * A trusted OS embedder attaches a host to the current Reaper execution
 * thread before running .rpr code. The host context must remain alive until
 * detach. Grants are copied; handles and provider state remain host-owned.
 */
ReaperSystemStatus reaper_system_host_attach(
    const ReaperSystemHost *host,
    ReaperSystemError *error
);

void reaper_system_host_detach(void);

/*
 * Calls one registered operation using UTF-8 JSON request/response payloads.
 * The OS adapter owns operation-specific JSON validation and serialization.
 * The returned string is thread-local and remains valid until the next call
 * on this thread or detach. NULL indicates failure; inspect the status/error.
 */
const char *reaper_system_call_json(
    const char *operation_name,
    const char *request_json
);

int32_t reaper_system_last_status(void);
const char *reaper_system_last_error(void);

#ifdef __cplusplus
}
#endif

#endif
