#ifndef REAPER_LIR_H
#define REAPER_LIR_H

#include "reaper/hir.h"
#include "reaper/mir.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_LIR_NO_VALUE UINT32_MAX
#define REAPER_LIR_NO_BLOCK UINT32_MAX
#define REAPER_LIR_NO_SLOT UINT32_MAX

typedef enum ReaperLirOpcode {
    REAPER_LIR_CONST = 1,
    REAPER_LIR_FUNCTION_REF,
    REAPER_LIR_BUILTIN_REF,
    REAPER_LIR_LOAD_SLOT,
    REAPER_LIR_STORE_SLOT,
    REAPER_LIR_UNARY,
    REAPER_LIR_BINARY,
    REAPER_LIR_LIST,
    REAPER_LIR_INDEX,
    REAPER_LIR_CALL,
    REAPER_LIR_PIPE_CALL,
    REAPER_LIR_EMIT,
    REAPER_LIR_DROP,
    REAPER_LIR_ITER_INIT,
    REAPER_LIR_ITER_NEXT,
    REAPER_LIR_ITER_CURRENT
} ReaperLirOpcode;

typedef enum ReaperLirTerminator {
    REAPER_LIR_TERM_NONE = 0,
    REAPER_LIR_TERM_JUMP,
    REAPER_LIR_TERM_BRANCH,
    REAPER_LIR_TERM_RETURN
} ReaperLirTerminator;

typedef struct ReaperLirInstruction {
    ReaperLirOpcode opcode;
    ReaperHirType type;
    uint32_t destination;
    uint32_t left;
    uint32_t right;
    uint32_t slot_id;
    uint32_t symbol_id;
    uint32_t source_hir_node;
    uint32_t operand_offset;
    uint32_t operand_count;
    char *text;
} ReaperLirInstruction;

typedef struct ReaperLirBlock {
    uint32_t id;
    uint32_t function_id;
    uint32_t first_instruction;
    uint32_t instruction_count;
    ReaperLirTerminator terminator;
    uint32_t terminator_value;
    uint32_t target_true;
    uint32_t target_false;
} ReaperLirBlock;

typedef struct ReaperLirFunction {
    uint32_t id;
    uint32_t symbol_id;
    uint32_t source_hir_node;
    uint32_t entry_block;
    uint32_t first_block;
    uint32_t block_count;
    uint32_t vreg_count;
    uint32_t local_offset;
    uint32_t local_count;
    uint32_t stack_slot_count;
    uint32_t parameter_offset;
    uint32_t parameter_count;
    char *name;
} ReaperLirFunction;

typedef struct ReaperLirLocal {
    uint32_t function_id;
    uint32_t symbol_id;
    uint32_t slot_id;
    ReaperHirType type;
    ReaperHirSymbolKind kind;
    unsigned mutable_value : 1;
} ReaperLirLocal;

typedef struct ReaperLirModule {
    ReaperLirInstruction *instructions;
    size_t instruction_count;
    ReaperLirBlock *blocks;
    size_t block_count;
    ReaperLirFunction *functions;
    size_t function_count;
    uint32_t *instruction_order;
    size_t instruction_order_count;
    uint32_t *operands;
    size_t operand_count;
    uint32_t *parameter_slots;
    size_t parameter_count;
    ReaperLirLocal *locals;
    size_t local_count;
} ReaperLirModule;

typedef struct ReaperLirError {
    size_t node_index;
    char message[256];
} ReaperLirError;

/*
 * Convert verified MIR values and calls to explicit virtual registers,
 * local stack slots, function parameter slots and target-neutral blocks.
 * The result is suitable for target-specific ABI lowering, but is not
 * machine code and does not define register allocation or ELF relocations.
 */
int reaper_lir_build(
    const ReaperHirModule *hir,
    const ReaperMirModule *mir,
    ReaperLirModule *output,
    ReaperLirError *error
);

int reaper_lir_verify(
    const ReaperLirModule *module,
    ReaperLirError *error
);

void reaper_lir_free(ReaperLirModule *module);
const char *reaper_lir_opcode_name(ReaperLirOpcode opcode);

#ifdef __cplusplus
}
#endif

#endif
