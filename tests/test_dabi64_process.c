#include "reaper/dabi64_process.h"
#include "reaper/system.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

static ReaperDabi64ProcessFrameV1 make_frame(void) {
    ReaperDabi64ProcessFrameV1 frame = {0};
    frame.rax = (uint64_t)REAPER_SYSTEM_PROCESS_CURRENT_ID;
    frame.user_rip = UINT64_C(0x0000000000401000);
    frame.user_rflags = UINT64_C(0x202);
    frame.user_rsp = UINT64_C(0x000000007fff0000);
    frame.user_cs = REAPER_DABI64_USER_CODE_SELECTOR;
    frame.user_ss = REAPER_DABI64_USER_DATA_SELECTOR;
    return frame;
}

static void test_frame_layout_and_valid_snapshot(void) {
    ReaperDabi64ProcessFrameV1 frame = make_frame();
    assert(sizeof(frame) == 160U);
    assert(offsetof(ReaperDabi64ProcessFrameV1, rax) == 112U);
    assert(offsetof(ReaperDabi64ProcessFrameV1, user_rip) == 120U);
    assert(offsetof(ReaperDabi64ProcessFrameV1, user_rsp) == 136U);
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame), REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_OK);
}

static void test_abi_and_frame_size_fail_closed(void) {
    ReaperDabi64ProcessFrameV1 frame = make_frame();
    assert(reaper_dabi64_process_frame_validate(
        NULL, sizeof(frame), REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_INVALID_ARGUMENT);
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame) - 1U, REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_MALFORMED_FRAME);
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame), 2U) ==
        REAPER_DABI64_PROCESS_UNSUPPORTED_ABI);
}

static void test_syscall_catalogue_and_return_state(void) {
    ReaperDabi64ProcessFrameV1 frame = make_frame();
    frame.rax = UINT64_C(0xffff);
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame), REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_UNKNOWN_SYSCALL);

    frame = make_frame();
    frame.user_rip = REAPER_DABI64_USER_LIMIT;
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame), REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_INVALID_USER_RETURN);

    frame = make_frame();
    frame.user_rsp += 1U;
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame), REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_INVALID_USER_RETURN);

    frame = make_frame();
    frame.user_rsp += 8U; /* 8 mod 16 is valid at a syscall boundary. */
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame), REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_OK);

    frame = make_frame();
    frame.user_cs = 0x08U;
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame), REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_INVALID_USER_RETURN);

    frame = make_frame();
    frame.user_rflags |= UINT64_C(0x3000);
    assert(reaper_dabi64_process_frame_validate(
        &frame, sizeof(frame), REAPER_DABI64_PROCESS_ABI_VERSION) ==
        REAPER_DABI64_PROCESS_INVALID_USER_RETURN);
}

static void test_user_range_bounds_and_overflow(void) {
    assert(reaper_dabi64_process_user_range_valid(0x1000U, 0x1000U));
    assert(reaper_dabi64_process_user_range_valid(REAPER_DABI64_USER_LIMIT - 1U, 1U));
    assert(!reaper_dabi64_process_user_range_valid(0U, 1U));
    assert(!reaper_dabi64_process_user_range_valid(REAPER_DABI64_USER_LIMIT, 1U));
    assert(!reaper_dabi64_process_user_range_valid(REAPER_DABI64_USER_LIMIT - 4U, 8U));
    assert(!reaper_dabi64_process_user_range_valid(UINT64_C(0xffff800000000000), 1U));
    assert(reaper_dabi64_process_user_range_valid(REAPER_DABI64_USER_LIMIT, 0U));
}

int main(void) {
    test_frame_layout_and_valid_snapshot();
    test_abi_and_frame_size_fail_closed();
    test_syscall_catalogue_and_return_state();
    test_user_range_bounds_and_overflow();
    puts("Reaper DABI64 process ABI tests passed");
    return 0;
}
