#ifndef REAPER_DABI64_PROGRAM_H
#define REAPER_DABI64_PROGRAM_H

#include "reaper/dabi64.h"

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_DABI_PROGRAM_NO_SLOT REAPER_DABI64_NO_SLOT
#define REAPER_DABI_PROGRAM_MAX_SLOTS 65536u

typedef enum {
    REAPER_DABI_OP_INVALID = 0,
    REAPER_DABI_OP_CONST_I64,
    REAPER_DABI_OP_CONST_STRING,
    REAPER_DABI_OP_CALL,
    REAPER_DABI_OP_JUMP,
    REAPER_DABI_OP_JUMP_IF_FALSE,
    REAPER_DABI_OP_RETURN
} ReaperDabiProgramOpcode;

typedef struct {
    ReaperDabiProgramOpcode opcode;
    uint32_t call_id;
    uint64_t dst;
    uint64_t auxiliary_dst;
    uint64_t lhs;
    uint64_t rhs;
    uint64_t target;
    int64_t immediate;
    const uint8_t *bytes;
    uint64_t byte_length;
} ReaperDabiInstruction;

typedef struct {
    const ReaperDabiInstruction *instructions;
    uint64_t instruction_count;
    uint64_t slot_count;
    uint64_t step_limit;
} ReaperDabiProgram;

typedef struct {
    uint64_t instruction_index;
    ReaperDabiStatus status;
    char message[160];
} ReaperDabiProgramError;

ReaperDabiStatus reaper_dabi_program_verify(
    const ReaperDabiProgram *program, ReaperDabiProgramError *error
);

/*
 * Executes a verified DABI64 runtime-call program. Strings and collections
 * use the runtime-call table. Iteration is lowered to iterator.begin,
 * iterator.next and verified conditional/unconditional branches. All slots
 * are owned by one cleanup frame and are dropped on every exit path.
 */
ReaperDabiStatus reaper_dabi_program_execute(
    ReaperDabiRuntime *runtime,
    const ReaperDabiProgram *program,
    ReaperDabiValue *result,
    ReaperDabiProgramError *error
);

const char *reaper_dabi_program_opcode_name(ReaperDabiProgramOpcode opcode);

#ifdef __cplusplus
}
#endif

#endif
