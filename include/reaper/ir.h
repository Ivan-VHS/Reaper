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
    REAPER_IR_TYPE_UNIT
} ReaperIrType;

typedef enum {
    REAPER_IR_OP_INVALID = 0,
    REAPER_IR_OP_CONST_I64,
    REAPER_IR_OP_ADD_I64,
    REAPER_IR_OP_RETURN
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
const char *reaper_ir_type_name(ReaperIrType type);
const char *reaper_ir_opcode_name(ReaperIrOpcode opcode);

#ifdef __cplusplus
}
#endif

#endif
