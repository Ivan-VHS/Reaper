#include "reaper/dabi64_desktop.h"
#include "reaper/system.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

_Static_assert(sizeof(ReaperDabi64DesktopRequestV1) == 40U, "request v1 size");
_Static_assert(_Alignof(ReaperDabi64DesktopRequestV1) == 8U, "request v1 alignment");
_Static_assert(offsetof(ReaperDabi64DesktopRequestV1, request_id) == 16U, "request id offset");
_Static_assert(offsetof(ReaperDabi64DesktopRequestV1, object_handle) == 24U, "request handle offset");
_Static_assert(offsetof(ReaperDabi64DesktopRequestV1, sequence) == 32U, "request sequence offset");
_Static_assert(sizeof(ReaperDabi64DesktopResponseV1) == 32U, "response v1 size");
_Static_assert(_Alignof(ReaperDabi64DesktopResponseV1) == 8U, "response v1 alignment");
_Static_assert(offsetof(ReaperDabi64DesktopResponseV1, request_id) == 16U, "response id offset");
_Static_assert(offsetof(ReaperDabi64DesktopResponseV1, object_handle) == 24U, "response handle offset");

static ReaperDabi64DesktopRequestV1 make_request(void) {
 ReaperDabi64DesktopRequestV1 r = {0};
 r.struct_size = (uint32_t)sizeof(r);
 r.abi_version = REAPER_DABI64_DESKTOP_ABI_VERSION;
 r.operation = (uint16_t)REAPER_SYSTEM_WINDOW_CREATE;
 r.request_id = 7U;
 r.sequence = 1U;
 return r;
}
static void test_request(void) {
 ReaperDabi64DesktopRequestV1 r = make_request();
 assert(sizeof(r) == 40U);
 assert(_Alignof(ReaperDabi64DesktopRequestV1) == 8U);
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_OK);
 assert(reaper_dabi64_desktop_request_validate(NULL,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_INVALID_ARGUMENT);
 r.abi_version=2U;
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_UNSUPPORTED_ABI);
 r=make_request(); r.struct_size--;
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_UNSUPPORTED_ABI);
 r=make_request(); r.operation=0xffffU;
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_UNKNOWN_OPERATION);
 r=make_request(); r.payload_size=4U;
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)+4U) == REAPER_DABI64_DESKTOP_STATUS_OK);
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME);
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)+5U) == REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME);
 r.payload_size=REAPER_DABI64_DESKTOP_MAX_PAYLOAD_BYTES+1U;
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)+r.payload_size) == REAPER_DABI64_DESKTOP_STATUS_BUFFER_TOO_LARGE);
 r=make_request(); r.flags=1U;
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME);
 r=make_request(); r.request_id=0U;
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME);
 r=make_request(); r.sequence=0U;
 assert(reaper_dabi64_desktop_request_validate(&r,sizeof(r)) == REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME);
}
static void test_response(void) {
 ReaperDabi64DesktopResponseV1 r={0};
 r.struct_size=(uint32_t)sizeof(r); r.abi_version=REAPER_DABI64_DESKTOP_ABI_VERSION;
 r.status=REAPER_DABI64_DESKTOP_STATUS_OK; r.request_id=7U;
 assert(sizeof(r)==32U);
 assert(_Alignof(ReaperDabi64DesktopResponseV1)==8U);
 assert(reaper_dabi64_desktop_response_validate(&r,sizeof(r))==REAPER_DABI64_DESKTOP_STATUS_OK);
 r.flags=1U;
 assert(reaper_dabi64_desktop_response_validate(&r,sizeof(r))==REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME);
 r.flags=0U; r.status=0xffffU;
 assert(reaper_dabi64_desktop_response_validate(&r,sizeof(r))==REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME);
 r.status=REAPER_DABI64_DESKTOP_STATUS_OK; r.request_id=0U;
 assert(reaper_dabi64_desktop_response_validate(&r,sizeof(r))==REAPER_DABI64_DESKTOP_STATUS_MALFORMED_FRAME);
 assert(reaper_dabi64_desktop_response_validate(NULL,sizeof(r))==REAPER_DABI64_DESKTOP_STATUS_INVALID_ARGUMENT);
}
int main(void) {
 test_request(); test_response();
 assert(strcmp(reaper_dabi64_desktop_status_name(REAPER_DABI64_DESKTOP_STATUS_BUFFER_TOO_LARGE),
               "buffer-too-large")==0);
 puts("reaper DABI64 desktop ABI tests passed");
 return 0;
}
