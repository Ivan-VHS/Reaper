#ifndef REAPER_DABI64_PROCESS_H
#define REAPER_DABI64_PROCESS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_DABI64_PROCESS_ABI_VERSION 1U
#define REAPER_DABI64_USER_LIMIT UINT64_C(0x0000800000000000)
#define REAPER_DABI64_USER_CODE_SELECTOR UINT16_C(0x23)
#define REAPER_DABI64_USER_DATA_SELECTOR UINT16_C(0x1b)

/*
 * Kernel-owned snapshot of the DABI64 x86-64 SYSCALL register state.
 * It is not a user-provided pointer-bearing request structure.
 */
typedef struct ReaperDabi64ProcessFrameV1 {
    uint64_t r15;
    uint64_t r14;
    uint64_t r13;
    uint64_t r12;
    uint64_t r11;
    uint64_t r10;
    uint64_t r9;
    uint64_t r8;
    uint64_t rdi;
    uint64_t rsi;
    uint64_t rbp;
    uint64_t rdx;
    uint64_t rcx;
    uint64_t rbx;
    uint64_t rax;
    uint64_t user_rip;
    uint64_t user_rflags;
    uint64_t user_rsp;
    uint64_t user_cs;
    uint64_t user_ss;
} ReaperDabi64ProcessFrameV1;

typedef enum ReaperDabi64ProcessStatus {
    REAPER_DABI64_PROCESS_OK = 0,
    REAPER_DABI64_PROCESS_INVALID_ARGUMENT,
    REAPER_DABI64_PROCESS_UNSUPPORTED_ABI,
    REAPER_DABI64_PROCESS_MALFORMED_FRAME,
    REAPER_DABI64_PROCESS_UNKNOWN_SYSCALL,
    REAPER_DABI64_PROCESS_INVALID_USER_RETURN,
    REAPER_DABI64_PROCESS_INVALID_USER_RANGE
} ReaperDabi64ProcessStatus;

/*
 * Validates the kernel-owned return/trap snapshot before dispatch or SYSRET.
 * The caller must still validate every operation-specific user buffer and
 * derive capabilities/identity from kernel-owned process state.
 */
ReaperDabi64ProcessStatus reaper_dabi64_process_frame_validate(
    const ReaperDabi64ProcessFrameV1 *frame,
    size_t frame_size,
    uint32_t abi_version
);

/* Validate a half-open range inside the lower canonical user address space. */
int reaper_dabi64_process_user_range_valid(uint64_t address, uint64_t bytes);

const char *reaper_dabi64_process_status_name(ReaperDabi64ProcessStatus status);

#ifdef __cplusplus
}
#endif

#endif
