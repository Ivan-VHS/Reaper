#ifndef REAPER_IR_H
#define REAPER_IR_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_IR_NO_VALUE UINT32_MAX

typedef enum {
    REAPER_IR_TYPE_INVALID = 0,
    REAPER_IR_TYPE_I64,
    REAPER_IR_TYPE_BOOL,
    REAPER_IR_TYPE_UNIT,
    REAPER_IR_TYPE_U32
} ReaperIrType;

typedef enum {
    REAPER_IR_OP_INVALID = 0,
    REAPER_IR_OP_CONST_I64,
    REAPER_IR_OP_ADD_I64,
    REAPER_IR_OP_RETURN,
    REAPER_IR_OP_SUB_I64,
    REAPER_IR_OP_MUL_I64,
    REAPER_IR_OP_DIV_I64,
    REAPER_IR_OP_CONST_U32,
    REAPER_IR_OP_ADD_U32,
    REAPER_IR_OP_SUB_U32,
    REAPER_IR_OP_MUL_U32,
    REAPER_IR_OP_DIV_U32,
    REAPER_IR_OP_BIT_AND_I64,
    REAPER_IR_OP_BIT_OR_I64,
    REAPER_IR_OP_BIT_XOR_I64,
    REAPER_IR_OP_BIT_NOT_I64,
    REAPER_IR_OP_SHL_I64,
    REAPER_IR_OP_SHR_I64
} ReaperIrOpcode;

typedef struct {
    ReaperIrOpcode opcode;
    ReaperIrType type;
    uint32_t lhs;
    uint32_t rhs;
    int64_t immediate;
    uint32_t source_line;
    uint32_t source_column;
} ReaperIrNode;

typedef struct {
    const ReaperIrNode *nodes;
    size_t length;
} ReaperIrModule;

typedef struct {
    size_t node_index;
    char message[192];
} ReaperIrError;

/* Verify a topologically ordered, immutable IR module. Returns 1 on success. */
int reaper_ir_verify(const ReaperIrModule *module, ReaperIrError *error);
/* Execute the verified, pure i64 IR subset.
 * values is caller-owned scratch storage with one slot per IR node.
 * Returns 1 on success, 0 on invalid IR, capacity, division or overflow.
 * The result output is written only after the final RETURN succeeds. */
int reaper_ir_execute_i64(const ReaperIrModule *module, int64_t *values,
                          size_t value_capacity, int64_t *result,
                          ReaperIrError *error);
/* Execute the checked unsigned u32 IR subset. Constants use the non-negative
 * int64_t immediate field and are rejected above UINT32_MAX. values is caller-
 * owned scratch storage. The result is written only after RETURN succeeds. */
int reaper_ir_execute_u32(const ReaperIrModule *module, uint32_t *values,
                          size_t value_capacity, uint32_t *result,
                          ReaperIrError *error);
const char *reaper_ir_type_name(ReaperIrType type);
const char *reaper_ir_opcode_name(ReaperIrOpcode opcode);

#ifdef __cplusplus
}
#endif

#endif
