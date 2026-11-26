#ifndef REAPER_TYPED_IR_H
#define REAPER_TYPED_IR_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_TIR_NO_ID UINT32_MAX
#define REAPER_TIR_VERSION 1u

typedef enum {
    REAPER_TIR_ERROR_NONE = 0,
    REAPER_TIR_ERROR_MODULE,
    REAPER_TIR_ERROR_SOURCE_MAP,
    REAPER_TIR_ERROR_SPAN,
    REAPER_TIR_ERROR_TYPE,
    REAPER_TIR_ERROR_FIELD,
    REAPER_TIR_ERROR_VALUE,
    REAPER_TIR_ERROR_BLOCK,
    REAPER_TIR_ERROR_FUNCTION,
    REAPER_TIR_ERROR_PARAMETER,
    REAPER_TIR_ERROR_REFERENCE,
    REAPER_TIR_ERROR_LAYOUT,
    REAPER_TIR_ERROR_MEMORY
} ReaperTypedIrErrorCode;

typedef struct {
    uint32_t id;
    const char *path;
    const unsigned char *contents;
    uint64_t byte_length;
    uint32_t line_count;
} ReaperSourceFile;

typedef struct {
    uint32_t id;
    uint32_t source_id;
    uint64_t byte_start;
    uint64_t byte_end;
    uint32_t start_line;
    uint32_t start_column;
    uint32_t end_line;
    uint32_t end_column;
} ReaperSpan;

typedef struct {
    const ReaperSourceFile *files;
    size_t file_count;
    const ReaperSpan *spans;
    size_t span_count;
} ReaperSourceMap;

typedef enum {
    REAPER_TIR_TYPE_INVALID = 0,
    REAPER_TIR_TYPE_UNIT,
    REAPER_TIR_TYPE_BOOL,
    REAPER_TIR_TYPE_I8,
    REAPER_TIR_TYPE_U8,
    REAPER_TIR_TYPE_I16,
    REAPER_TIR_TYPE_U16,
    REAPER_TIR_TYPE_I32,
    REAPER_TIR_TYPE_U32,
    REAPER_TIR_TYPE_I64,
    REAPER_TIR_TYPE_U64,
    REAPER_TIR_TYPE_F32,
    REAPER_TIR_TYPE_F64,
    REAPER_TIR_TYPE_POINTER,
    REAPER_TIR_TYPE_ARRAY,
    REAPER_TIR_TYPE_STRUCT,
    REAPER_TIR_TYPE_UNION,
    REAPER_TIR_TYPE_ENUM,
    REAPER_TIR_TYPE_DISTINCT,
    REAPER_TIR_TYPE_OPAQUE
} ReaperTypedIrTypeKind;

enum {
    REAPER_TIR_TYPE_FLAG_NONE = 0u,
    REAPER_TIR_TYPE_FLAG_PACKED = 1u
};

typedef struct {
    uint32_t id;
    ReaperTypedIrTypeKind kind;
    uint32_t flags;
    uint32_t element_type_id;
    uint64_t element_count;
    uint64_t byte_size;
    uint32_t byte_alignment;
    uint32_t first_field;
    uint32_t field_count;
    uint32_t span_id;
    const char *name;
} ReaperTypedIrType;

typedef struct {
    uint32_t owner_type_id;
    uint32_t type_id;
    uint32_t span_id;
    uint64_t byte_offset;
    const char *name;
} ReaperTypedIrField;

typedef enum {
    REAPER_TIR_OP_INVALID = 0,
    REAPER_TIR_OP_CONST_I64,
    REAPER_TIR_OP_ADD_I64,
    REAPER_TIR_OP_SUB_I64,
    REAPER_TIR_OP_MUL_I64,
    REAPER_TIR_OP_COPY
} ReaperTypedIrOpcode;

typedef struct {
    uint32_t id;
    uint32_t block_id;
    uint32_t type_id;
    ReaperTypedIrOpcode opcode;
    uint32_t lhs;
    uint32_t rhs;
    int64_t immediate;
    uint32_t span_id;
} ReaperTypedIrValue;

typedef enum {
    REAPER_TIR_TERM_INVALID = 0,
    REAPER_TIR_TERM_RETURN,
    REAPER_TIR_TERM_JUMP,
    REAPER_TIR_TERM_COND_JUMP,
    REAPER_TIR_TERM_UNREACHABLE
} ReaperTypedIrTerminatorKind;

typedef struct {
    uint32_t id;
    uint32_t function_id;
    uint32_t first_value;
    uint32_t value_count;
    ReaperTypedIrTerminatorKind terminator;
    uint32_t operand_value_id;
    uint32_t true_target_block_id;
    uint32_t false_target_block_id;
    uint32_t span_id;
} ReaperTypedIrBlock;

typedef struct {
    uint32_t function_id;
    const char *name;
    uint32_t type_id;
    uint32_t span_id;
} ReaperTypedIrParameter;

typedef struct {
    uint32_t id;
    const char *name;
    uint32_t return_type_id;
    uint32_t first_parameter;
    uint32_t parameter_count;
    uint32_t first_block;
    uint32_t block_count;
    uint32_t entry_block_id;
    uint32_t span_id;
} ReaperTypedIrFunction;

typedef struct {
    uint32_t version;
    const char *target_triple;
    uint32_t pointer_size;
    uint32_t pointer_alignment;
    ReaperSourceMap source_map;
    const ReaperTypedIrType *types;
    size_t type_count;
    const ReaperTypedIrField *fields;
    size_t field_count;
    const ReaperTypedIrParameter *parameters;
    size_t parameter_count;
    const ReaperTypedIrValue *values;
    size_t value_count;
    const ReaperTypedIrBlock *blocks;
    size_t block_count;
    const ReaperTypedIrFunction *functions;
    size_t function_count;
} ReaperTypedIrModule;

typedef struct {
    ReaperTypedIrErrorCode code;
    size_t item_index;
    char message[192];
} ReaperTypedIrError;

/*
 * Verify Canonical Typed IR v1 before optimization or target lowering.
 * SourceMap offsets are UTF-8 byte offsets; line/column coordinates are
 * one-based Unicode code-point positions. Value operands are SSA references
 * to earlier values in the same basic block in v1.
 */
int reaper_typed_ir_verify(
    const ReaperTypedIrModule *module,
    ReaperTypedIrError *error
);

const char *reaper_typed_ir_type_name(ReaperTypedIrTypeKind kind);
const char *reaper_typed_ir_opcode_name(ReaperTypedIrOpcode opcode);
int reaper_source_map_resolve(
    const ReaperSourceMap *source_map,
    uint32_t span_id,
    const ReaperSourceFile **source_file,
    const ReaperSpan **span
);

#ifdef __cplusplus
}
#endif

#endif
