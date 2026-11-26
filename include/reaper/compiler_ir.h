#ifndef REAPER_COMPILER_IR_H
#define REAPER_COMPILER_IR_H

#include "reaper/ast.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_COMPILER_IR_VERSION UINT32_C(1)
#define REAPER_COMPILER_IR_MAX_NODES 4096u
#define REAPER_COMPILER_IR_KEY_MAX 96u
#define REAPER_COMPILER_IR_TEXT_MAX 96u
#define REAPER_COMPILER_IR_SOURCE_MAX 128u
#define REAPER_COMPILER_IR_NO_VALUE UINT32_MAX

typedef enum {
    REAPER_COMPILER_IR_INVALID = 0,
    REAPER_COMPILER_IR_HIR = 1,
    REAPER_COMPILER_IR_MIR = 2,
    REAPER_COMPILER_IR_LIR = 3
} ReaperCompilerIrStage;

typedef enum {
    REAPER_COMPILER_IR_TYPE_INVALID = 0,
    REAPER_COMPILER_IR_TYPE_I64,
    REAPER_COMPILER_IR_TYPE_F64,
    REAPER_COMPILER_IR_TYPE_BOOL,
    REAPER_COMPILER_IR_TYPE_TEXT,
    REAPER_COMPILER_IR_TYPE_COLOR,
    REAPER_COMPILER_IR_TYPE_LENGTH,
    REAPER_COMPILER_IR_TYPE_DURATION,
    REAPER_COMPILER_IR_TYPE_FONT,
    REAPER_COMPILER_IR_TYPE_RATIO
} ReaperCompilerIrType;

typedef enum {
    REAPER_COMPILER_IR_OP_INVALID = 0,
    REAPER_COMPILER_IR_HIR_VALUE,
    REAPER_COMPILER_IR_HIR_NAME,
    REAPER_COMPILER_IR_HIR_UNARY,
    REAPER_COMPILER_IR_HIR_BINARY,
    REAPER_COMPILER_IR_HIR_CALL,
    REAPER_COMPILER_IR_HIR_COLOR_ROLE,
    REAPER_COMPILER_IR_HIR_FONT_ROLE,
    REAPER_COMPILER_IR_HIR_METRIC_ROLE,
    REAPER_COMPILER_IR_HIR_MOTION_ROLE,
    REAPER_COMPILER_IR_HIR_ACCESSIBILITY_ROLE,
    REAPER_COMPILER_IR_MIR_CONSTANT,
    REAPER_COMPILER_IR_MIR_NAME,
    REAPER_COMPILER_IR_MIR_UNARY,
    REAPER_COMPILER_IR_MIR_ARITHMETIC,
    REAPER_COMPILER_IR_MIR_CALL,
    REAPER_COMPILER_IR_MIR_SET_PROPERTY,
    REAPER_COMPILER_IR_LIR_NATIVE_CONSTANT,
    REAPER_COMPILER_IR_LIR_NATIVE_NAME,
    REAPER_COMPILER_IR_LIR_NATIVE_UNARY,
    REAPER_COMPILER_IR_LIR_NATIVE_ARITHMETIC,
    REAPER_COMPILER_IR_LIR_NATIVE_CALL,
    REAPER_COMPILER_IR_LIR_NATIVE_PROPERTY
} ReaperCompilerIrOpcode;

enum {
    REAPER_COMPILER_IR_FLAG_REDUCED_MOTION = UINT32_C(1) << 0
};

typedef struct {
    char source[REAPER_COMPILER_IR_SOURCE_MAX];
    uint32_t line;
    uint32_t column;
} ReaperCompilerSourceSpan;

typedef struct {
    ReaperCompilerIrOpcode opcode;
    ReaperCompilerIrType type;
    char key[REAPER_COMPILER_IR_KEY_MAX];
    char text[REAPER_COMPILER_IR_TEXT_MAX];
    int64_t integer;
    double number;
    ReaperCompilerSourceSpan span;
    uint32_t lhs;
    uint32_t rhs;
} ReaperCompilerIrNode;

typedef struct {
    uint32_t version;
    ReaperCompilerIrStage stage;
    uint32_t flags;
    char target[REAPER_COMPILER_IR_KEY_MAX];
    const ReaperCompilerIrNode *nodes;
    size_t length;
} ReaperCompilerIrModule;

typedef struct {
    size_t node_index;
    ReaperCompilerSourceSpan span;
    char message[192];
} ReaperCompilerIrError;

/*
 * Lower the current native expression AST into typed HIR.
 * Supported source nodes: i64 literals, finite decimal literals, decoded
 * strings, booleans, unary +/- and binary + - * / over matching i64 or f64
 * operands. Mixed numeric operands are rejected; no implicit promotion occurs.
 * Identifiers, null, calls, collections and unsupported operators fail
 * explicitly with a source-located diagnostic.
 *
 * The AST is borrowed and remains caller-owned. The output array is also
 * caller-owned and must hold ast->length nodes. The returned HIR borrows
 * that output storage.
 */
int reaper_compiler_ir_lower_ast_to_hir(
    const ReaperAst *ast,
    const char *source_name,
    ReaperCompilerIrNode *output,
    size_t output_capacity,
    ReaperCompilerIrModule *hir,
    ReaperCompilerIrError *error
);
int reaper_compiler_ir_verify(
    const ReaperCompilerIrModule *module,
    ReaperCompilerIrStage expected_stage,
    ReaperCompilerIrError *error
);
int reaper_compiler_ir_lower_hir_to_mir(
    const ReaperCompilerIrModule *hir,
    ReaperCompilerIrNode *output,
    size_t output_capacity,
    ReaperCompilerIrModule *mir,
    ReaperCompilerIrError *error
);
int reaper_compiler_ir_lower_mir_to_lir(
    const ReaperCompilerIrModule *mir,
    const char *target,
    ReaperCompilerIrNode *output,
    size_t output_capacity,
    ReaperCompilerIrModule *lir,
    ReaperCompilerIrError *error
);
int reaper_compiler_ir_emit_c17(
    const ReaperCompilerIrModule *lir,
    char *output,
    size_t output_capacity,
    size_t *output_length,
    ReaperCompilerIrError *error
);
const char *reaper_compiler_ir_stage_name(ReaperCompilerIrStage stage);
const char *reaper_compiler_ir_type_name(ReaperCompilerIrType type);
const char *reaper_compiler_ir_opcode_name(ReaperCompilerIrOpcode opcode);

#ifdef __cplusplus
}
#endif
#endif
