#ifndef REAPER_DABI64_DESKTOP_H
#define REAPER_DABI64_DESKTOP_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define REAPER_DABI64_DESKTOP_ABI_VERSION 1U
#define REAPER_DABI64_DESKTOP_MAX_PAYLOAD_BYTES (64U * 1024U)
typedef enum {
 REAPER_DABI64_DESKTOP_STATUS_OK = 0,
 REAPER_DABI64_DESKTOP_STATUS_INVALID_ARGUMENT = 1,
 REAPER_DABI64_DESKTOP_STATUS_UNSUPPORTED_ABI = 2,
 REAPER_DABI64_DESKTOP_STATUS_UNKNOWN_OPERATION = 3,
 REAPER_DABI64_DESKTOP_STATUS_ACCESS_DENIED = 4,
 REAPER_DABI64_DESKTOP_STATUS_BUFFER_TOO_LARGE = 5,
 REAPER_DABI64_DESKTOP_STATUS_INVALID_HANDLE = 6,
 REAPER_DABI64_DESKTOP_STATUS_TRY_AGAIN = 7,
 REAPER_DABI64_DESKTOP_STATUS_INTERNAL = 8,
 REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME = 9
} ReaperDabi64DesktopStatus;
/* Fixed-width little-endian wire header. No native pointers or authority claims. */
typedef struct {
 uint32_t struct_size;
 uint16_t abi_version;
 uint16_t operation;
 uint32_t flags;
 uint32_t payload_size;
 uint64_t request_id;
 uint64_t object_handle;
 uint64_t sequence;
} ReaperDabi64DesktopRequestV1;
typedef struct {
 uint32_t struct_size;
 uint16_t abi_version;
 uint16_t status;
 uint32_t flags;
 uint32_t payload_size;
 uint64_t request_id;
 uint64_t object_handle;
} ReaperDabi64DesktopResponseV1;
ReaperDabi64DesktopStatus reaper_dabi64_desktop_request_validate(
 const ReaperDabi64DesktopRequestV1 *request, size_t frame_size);
ReaperDabi64DesktopStatus reaper_dabi64_desktop_response_validate(
 const ReaperDabi64DesktopResponseV1 *response, size_t frame_size);
const char *reaper_dabi64_desktop_status_name(ReaperDabi64DesktopStatus status);
#ifdef __cplusplus
}
#endif
#endif
