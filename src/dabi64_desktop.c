#include "reaper/dabi64_desktop.h"
#include "reaper/system.h"
#include <stddef.h>
#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__)
#if __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "DABI64 desktop v1 wire encoding is little-endian"
#endif
#endif
_Static_assert(sizeof(ReaperDabi64DesktopRequestV1) == 40U, "request v1 size");
_Static_assert(offsetof(ReaperDabi64DesktopRequestV1, request_id) == 16U, "request id offset");
_Static_assert(offsetof(ReaperDabi64DesktopRequestV1, sequence) == 32U, "sequence offset");
_Static_assert(sizeof(ReaperDabi64DesktopResponseV1) == 32U, "response v1 size");
_Static_assert(offsetof(ReaperDabi64DesktopResponseV1, request_id) == 16U, "response id offset");
static int frame_size_matches(uint32_t payload_size, size_t frame_size, size_t header_size) {
 if (payload_size > REAPER_DABI64_DESKTOP_MAX_PAYLOAD_BYTES) return 0;
 if ((size_t)payload_size > SIZE_MAX - header_size) return 0;
 return frame_size == header_size + (size_t)payload_size;
}
ReaperDabi64DesktopStatus reaper_dabi64_desktop_request_validate(
 const ReaperDabi64DesktopRequestV1 *request, size_t frame_size) {
 if (request == NULL) return REAPER_DABI64_DESKTOP_STATUS_INVALID_ARGUMENT;
 if (frame_size < sizeof(*request)) return REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME;
 if (request->abi_version != REAPER_DABI64_DESKTOP_ABI_VERSION ||
     request->struct_size != (uint32_t)sizeof(*request))
  return REAPER_DABI64_DESKTOP_STATUS_UNSUPPORTED_ABI;
 if (request->flags != 0U || request->request_id == 0U || request->sequence == 0U)
  return REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME;
 if (reaper_system_operation_find((ReaperSystemOperation)request->operation) == NULL)
  return REAPER_DABI64_DESKTOP_STATUS_UNKNOWN_OPERATION;
 if (request->payload_size > REAPER_DABI64_DESKTOP_MAX_PAYLOAD_BYTES)
  return REAPER_DABI64_DESKTOP_STATUS_BUFFER_TOO_LARGE;
 if (!frame_size_matches(request->payload_size, frame_size, sizeof(*request)))
  return REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME;
 return REAPER_DABI64_DESKTOP_STATUS_OK;
}
ReaperDabi64DesktopStatus reaper_dabi64_desktop_response_validate(
 const ReaperDabi64DesktopResponseV1 *response, size_t frame_size) {
 if (response == NULL) return REAPER_DABI64_DESKTOP_STATUS_INVALID_ARGUMENT;
 if (frame_size < sizeof(*response)) return REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME;
 if (response->abi_version != REAPER_DABI64_DESKTOP_ABI_VERSION ||
     response->struct_size != (uint32_t)sizeof(*response))
  return REAPER_DABI64_DESKTOP_STATUS_UNSUPPORTED_ABI;
 if (response->flags != 0U || response->request_id == 0U)
  return REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME;
 if (response->status > REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME)
  return REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME;
 if (response->payload_size > REAPER_DABI64_DESKTOP_MAX_PAYLOAD_BYTES)
  return REAPER_DABI64_DESKTOP_STATUS_BUFFER_TOO_LARGE;
 if (!frame_size_matches(response->payload_size, frame_size, sizeof(*response)))
  return REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME;
 return REAPER_DABI64_DESKTOP_STATUS_OK;
}
const char *reaper_dabi64_desktop_status_name(ReaperDabi64DesktopStatus status) {
 switch (status) {
 case REAPER_DABI64_DESKTOP_STATUS_OK: return "ok";
 case REAPER_DABI64_DESKTOP_STATUS_INVALID_ARGUMENT: return "invalid-argument";
 case REAPER_DABI64_DESKTOP_STATUS_UNSUPPORTED_ABI: return "unsupported-abi";
 case REAPER_DABI64_DESKTOP_STATUS_UNKNOWN_OPERATION: return "unknown-operation";
 case REAPER_DABI64_DESKTOP_STATUS_ACCESS_DENIED: return "access-denied";
 case REAPER_DABI64_DESKTOP_STATUS_BUFFER_TOO_LARGE: return "buffer-too-large";
 case REAPER_DABI64_DESKTOP_STATUS_INVALID_HANDLE: return "invalid-handle";
 case REAPER_DABI64_DESKTOP_STATUS_TRY_AGAIN: return "try-again";
 case REAPER_DABI64_DESKTOP_STATUS_INTERNAL: return "internal";
 case REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME: return "malformed-frame";
 }
 return "unknown-status";
}
