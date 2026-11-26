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

#if defined(__cplusplus)
# define REAPER_DABI64_STATIC_ASSERT(condition, message) static_assert((condition), message)
# define REAPER_DABI64_ALIGNOF(type) alignof(type)
#else
# define REAPER_DABI64_STATIC_ASSERT(condition, message) _Static_assert((condition), message)
# define REAPER_DABI64_ALIGNOF(type) _Alignof(type)
#endif
REAPER_DABI64_STATIC_ASSERT(sizeof(ReaperDabi64DesktopRequestV1) == 40U,
                            "DABI64 request v1 size changed");
REAPER_DABI64_STATIC_ASSERT(REAPER_DABI64_ALIGNOF(ReaperDabi64DesktopRequestV1) == 8U,
                            "DABI64 request v1 alignment changed");
REAPER_DABI64_STATIC_ASSERT(offsetof(ReaperDabi64DesktopRequestV1, request_id) == 16U,
                            "DABI64 request v1 request_id offset changed");
REAPER_DABI64_STATIC_ASSERT(offsetof(ReaperDabi64DesktopRequestV1, object_handle) == 24U,
                            "DABI64 request v1 object_handle offset changed");
REAPER_DABI64_STATIC_ASSERT(offsetof(ReaperDabi64DesktopRequestV1, sequence) == 32U,
                            "DABI64 request v1 sequence offset changed");
REAPER_DABI64_STATIC_ASSERT(sizeof(ReaperDabi64DesktopResponseV1) == 32U,
                            "DABI64 response v1 size changed");
REAPER_DABI64_STATIC_ASSERT(REAPER_DABI64_ALIGNOF(ReaperDabi64DesktopResponseV1) == 8U,
                            "DABI64 response v1 alignment changed");
REAPER_DABI64_STATIC_ASSERT(offsetof(ReaperDabi64DesktopResponseV1, request_id) == 16U,
                            "DABI64 response v1 request_id offset changed");
REAPER_DABI64_STATIC_ASSERT(offsetof(ReaperDabi64DesktopResponseV1, object_handle) == 24U,
                            "DABI64 response v1 object_handle offset changed");
#undef REAPER_DABI64_STATIC_ASSERT
#undef REAPER_DABI64_ALIGNOF

ReaperDabi64DesktopStatus reaper_dabi64_desktop_request_validate(
 const ReaperDabi64DesktopRequestV1 *request, size_t frame_size);
ReaperDabi64DesktopStatus reaper_dabi64_desktop_response_validate(
 const ReaperDabi64DesktopResponseV1 *response, size_t frame_size);
const char *reaper_dabi64_desktop_status_name(ReaperDabi64DesktopStatus status);
#ifdef __cplusplus
}
#endif
#endif
