#include "reaper/dabi64_process.h"

#include "reaper/system.h"

#include <stddef.h>

_Static_assert(sizeof(ReaperDabi64ProcessFrameV1) == 160U, "DABI64 process frame size");
_Static_assert(offsetof(ReaperDabi64ProcessFrameV1, rax) == 112U, "DABI64 RAX offset");
_Static_assert(offsetof(ReaperDabi64ProcessFrameV1, user_rip) == 120U, "DABI64 user RIP offset");
_Static_assert(offsetof(ReaperDabi64ProcessFrameV1, user_rsp) == 136U, "DABI64 user RSP offset");
_Static_assert(offsetof(ReaperDabi64ProcessFrameV1, user_ss) == 152U, "DABI64 user SS offset");

int reaper_dabi64_process_user_range_valid(uint64_t address, uint64_t bytes) {
    if (bytes == 0U) {
        return address <= REAPER_DABI64_USER_LIMIT;
    }
    if (address == 0U || address >= REAPER_DABI64_USER_LIMIT) {
        return 0;
    }
    return bytes <= REAPER_DABI64_USER_LIMIT - address;
}

ReaperDabi64ProcessStatus reaper_dabi64_process_frame_validate(
    const ReaperDabi64ProcessFrameV1 *frame,
    size_t frame_size,
    uint32_t abi_version
) {
    if (frame == NULL) return REAPER_DABI64_PROCESS_INVALID_ARGUMENT;
    if (abi_version != REAPER_DABI64_PROCESS_ABI_VERSION) {
        return REAPER_DABI64_PROCESS_UNSUPPORTED_ABI;
    }
    if (frame_size != sizeof(*frame)) {
        return REAPER_DABI64_PROCESS_MALFORMED_FRAME;
    }

    if (frame->rax > UINT16_MAX ||
        reaper_system_operation_find((ReaperSystemOperation)frame->rax) == NULL) {
        return REAPER_DABI64_PROCESS_UNKNOWN_SYSCALL;
    }

    if (!reaper_dabi64_process_user_range_valid(frame->user_rip, 1U) ||
        !reaper_dabi64_process_user_range_valid(frame->user_rsp, 1U) ||
        (frame->user_rsp & UINT64_C(0x0f)) != 0U ||
        frame->user_cs != REAPER_DABI64_USER_CODE_SELECTOR ||
        frame->user_ss != REAPER_DABI64_USER_DATA_SELECTOR) {
        return REAPER_DABI64_PROCESS_INVALID_USER_RETURN;
    }

    /* RFLAGS bit 1 must be set; IOPL, NT and VM are never user-controlled. */
    if ((frame->user_rflags & UINT64_C(0x2)) == 0U ||
        (frame->user_rflags & UINT64_C(0x0000000000027000)) != 0U) {
        return REAPER_DABI64_PROCESS_INVALID_USER_RETURN;
    }

    return REAPER_DABI64_PROCESS_OK;
}

const char *reaper_dabi64_process_status_name(ReaperDabi64ProcessStatus status) {
    switch (status) {
    case REAPER_DABI64_PROCESS_OK: return "ok";
    case REAPER_DABI64_PROCESS_INVALID_ARGUMENT: return "invalid-argument";
    case REAPER_DABI64_PROCESS_UNSUPPORTED_ABI: return "unsupported-abi";
    case REAPER_DABI64_PROCESS_MALFORMED_FRAME: return "malformed-frame";
    case REAPER_DABI64_PROCESS_UNKNOWN_SYSCALL: return "unknown-syscall";
    case REAPER_DABI64_PROCESS_INVALID_USER_RETURN: return "invalid-user-return";
    case REAPER_DABI64_PROCESS_INVALID_USER_RANGE: return "invalid-user-range";
    }
    return "unknown-status";
}
