#ifndef REAPER_MIR_H
#define REAPER_MIR_H

#include "reaper/hir.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_MIR_NO_VALUE UINT32_MAX
#define REAPER_MIR_NO_BLOCK UINT32_MAX

typedef enum ReaperMirOpcode {
    REAPER_MIR_CONST = 1,
    REAPER_MIR_FUNCTION_REF,
    REAPER_MIR_BUILTIN_REF,
    REAPER_MIR_LOAD_LOCAL,
    REAPER_MIR_STORE_LOCAL,
    REAPER_MIR_UNARY,
    REAPER_MIR_BINARY,
    REAPER_MIR_LIST,
    REAPER_MIR_INDEX,
    REAPER_MIR_CALL,
    REAPER_MIR_PIPE_CALL,
    REAPER_MIR_EMIT,
    REAPER_MIR_DROP,
    REAPER_MIR_ITER_INIT,
    REAPER_MIR_ITER_NEXT,
    REAPER_MIR_ITER_CURRENT
} ReaperMirOpcode;

typedef enum ReaperMirTerminator {
    REAPER_MIR_TERM_NONE = 0,
    REAPER_MIR_TERM_JUMP,
    REAPER_MIR_TERM_BRANCH,
    REAPER_MIR_TERM_RETURN
} ReaperMirTerminator;

typedef struct ReaperMirInstruction {
    ReaperMirOpcode opcode;
    ReaperHirType type;
    uint32_t result_id;
    uint32_t left;
    uint32_t right;
    uint32_t symbol_id;
    uint32_t source_hir_node;
    uint32_t operand_offset;
    uint32_t operand_count;
    char *text;
} ReaperMirInstruction;

typedef struct ReaperMirBlock {
    uint32_t id;
    uint32_t function_id;
    uint32_t first_instruction;
    uint32_t instruction_count;
    ReaperMirTerminator terminator;
    uint32_t condition_value;
    uint32_t target_true;
    uint32_t target_false;
} ReaperMirBlock;

typedef struct ReaperMirFunction {
    uint32_t id;
    uint32_t symbol_id;
    uint32_t source_hir_node;
    uint32_t entry_block;
    uint32_t first_block;
    uint32_t block_count;
    uint32_t parameter_offset;
    uint32_t parameter_count;
    char *name;
} ReaperMirFunction;

typedef struct ReaperMirModule {
    ReaperMirInstruction *instructions;
    size_t instruction_count;
    size_t instruction_capacity;
    ReaperMirBlock *blocks;
    size_t block_count;
    size_t block_capacity;
    ReaperMirFunction *functions;
    size_t function_count;
    size_t function_capacity;
    uint32_t *operands;
    size_t operand_count;
    size_t operand_capacity;
    uint32_t *parameters;
    size_t parameter_count;
    size_t parameter_capacity;
} ReaperMirModule;

typedef struct ReaperMirError {
    size_t node_index;
    char message[256];
} ReaperMirError;

/*
 * Lower a semantically checked program HIR into target-independent MIR.
 * Functions, local loads/stores, calls, ::, when, loop-while and each receive
 * explicit instruction/control-flow representations. Expression operations
 * retain source HIR references until a later LIR lowering pass.
 *
 * This is structural/control-flow lowering, not machine-code generation.
 */
int reaper_mir_build(
    const ReaperHirModule *hir,
    ReaperMirModule *output,
    ReaperMirError *error
);

int reaper_mir_verify(
    const ReaperMirModule *module,
    ReaperMirError *error
);

void reaper_mir_free(ReaperMirModule *module);
const char *reaper_mir_opcode_name(ReaperMirOpcode opcode);

#ifdef __cplusplus
}
#endif

#endif
