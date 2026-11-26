#include "reaper/typed_ir.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static const unsigned char source_text[] = "20 + 22";
static ReaperSourceFile sources[] = {
    { 7u, "examples/add.rpr", source_text, sizeof source_text - 1u, 1u }
};
static ReaperSpan spans[] = {
    { 3u, 7u, 0u, sizeof source_text - 1u, 1u, 1u, 1u, 8u }
};
static ReaperTypedIrType types[] = {
    { 0u, REAPER_TIR_TYPE_UNIT, REAPER_TIR_TYPE_FLAG_NONE, REAPER_TIR_NO_ID,
      0u, 0u, 1u, 0u, 0u, 3u, "unit" },
    { 1u, REAPER_TIR_TYPE_I64, REAPER_TIR_TYPE_FLAG_NONE, REAPER_TIR_NO_ID,
      0u, 8u, 8u, 0u, 0u, 3u, "i64" },
    { 2u, REAPER_TIR_TYPE_BOOL, REAPER_TIR_TYPE_FLAG_NONE, REAPER_TIR_NO_ID,
      0u, 1u, 1u, 0u, 0u, 3u, "bool" },
    { 3u, REAPER_TIR_TYPE_U32, REAPER_TIR_TYPE_FLAG_NONE, REAPER_TIR_NO_ID,
      0u, 4u, 4u, 0u, 0u, 3u, "u32" },
    { 4u, REAPER_TIR_TYPE_U64, REAPER_TIR_TYPE_FLAG_NONE, REAPER_TIR_NO_ID,
      0u, 8u, 8u, 0u, 0u, 3u, "u64" },
    { 5u, REAPER_TIR_TYPE_STRUCT, REAPER_TIR_TYPE_FLAG_NONE, REAPER_TIR_NO_ID,
      0u, 16u, 8u, 0u, 2u, 3u, "Packet" }
};
static ReaperTypedIrField fields[] = {
    { 5u, 3u, 3u, 0u, "kind" },
    { 5u, 4u, 3u, 8u, "sequence" }
};
static ReaperTypedIrValue values[] = {
    { 0u, 10u, 1u, REAPER_TIR_OP_CONST_I64,
      REAPER_TIR_NO_ID, REAPER_TIR_NO_ID, 20, 3u },
    { 1u, 10u, 1u, REAPER_TIR_OP_CONST_I64,
      REAPER_TIR_NO_ID, REAPER_TIR_NO_ID, 22, 3u },
    { 2u, 10u, 1u, REAPER_TIR_OP_ADD_I64, 0u, 1u, 0, 3u }
};
static ReaperTypedIrBlock blocks[] = {
    { 10u, 9u, 0u, 3u, REAPER_TIR_TERM_RETURN, 2u,
      REAPER_TIR_NO_ID, REAPER_TIR_NO_ID, 3u }
};
static ReaperTypedIrFunction functions[] = {
    { 9u, "main", 1u, 0u, 0u, 0u, 1u, 10u, 3u }
};
static ReaperTypedIrModule module = {
    REAPER_TIR_VERSION,
    "x86_64-unknown-linux-gnu",
    8u,
    8u,
    { sources, 1u, spans, 1u },
    types, sizeof types / sizeof types[0],
    fields, sizeof fields / sizeof fields[0],
    NULL, 0u,
    values, sizeof values / sizeof values[0],
    blocks, sizeof blocks / sizeof blocks[0],
    functions, sizeof functions / sizeof functions[0]
};

static void valid_module_and_source_map(void) {
    ReaperTypedIrError error;
    assert(reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_NONE);
    assert(strcmp(reaper_typed_ir_type_name(REAPER_TIR_TYPE_STRUCT), "struct") == 0);
    assert(strcmp(reaper_typed_ir_opcode_name(REAPER_TIR_OP_ADD_I64), "add.i64") == 0);

    const ReaperSourceFile *file = NULL;
    const ReaperSpan *span = NULL;
    assert(reaper_source_map_resolve(&module.source_map, 3u, &file, &span));
    assert(strcmp(file->path, "examples/add.rpr") == 0);
    assert(file->contents == source_text);
    assert(span->byte_start == 0u && span->byte_end == 7u);
}

static void source_map_rejects_out_of_range_and_duplicate_spans(void) {
    ReaperTypedIrError error;
    ReaperSpan original = spans[0];

    spans[0].byte_end = 8u;
    assert(!reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_SPAN);
    spans[0] = original;

    ReaperSpan extra = spans[0];
    ReaperSourceFile extra_source = sources[0];
    extra_source.id = 8u;
    module.source_map.files = sources;
    module.source_map.file_count = 1u;
    spans[0].id = 3u;
    extra.id = 3u;
    ReaperSpan span_pair[] = { spans[0], extra };
    module.source_map.spans = span_pair;
    module.source_map.span_count = 2u;
    assert(!reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_SPAN);
    module.source_map.spans = spans;
    module.source_map.span_count = 1u;
    spans[0] = original;
    (void)extra_source;
}

static void aggregate_layout_is_checked(void) {
    ReaperTypedIrError error;
    uint64_t original = fields[1].byte_offset;
    fields[1].byte_offset = 4u;
    assert(!reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_LAYOUT);
    assert(strstr(error.message, "overlap") != NULL);
    fields[1].byte_offset = original;

    uint32_t original_align = types[5].byte_alignment;
    types[5].byte_alignment = 4u;
    assert(!reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_LAYOUT);
    types[5].byte_alignment = original_align;
}

static void invalid_ssa_and_terminators_are_rejected(void) {
    ReaperTypedIrError error;
    uint32_t original_lhs = values[2].lhs;
    values[2].lhs = 99u;
    assert(!reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_VALUE);
    values[2].lhs = original_lhs;

    uint32_t original_return = blocks[0].operand_value_id;
    blocks[0].operand_value_id = 99u;
    assert(!reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_BLOCK);
    blocks[0].operand_value_id = original_return;
}

static void by_value_cycles_are_rejected_but_pointer_recursion_is_allowed(void) {
    ReaperTypedIrError error;
    ReaperTypedIrType recursive_type = {
        6u, REAPER_TIR_TYPE_STRUCT, REAPER_TIR_TYPE_FLAG_NONE, REAPER_TIR_NO_ID,
        0u, 8u, 8u, 2u, 1u, 3u, "Recursive"
    };
    ReaperTypedIrField recursive_field = { 6u, 6u, 3u, 0u, "self" };
    ReaperTypedIrType extended_types[7];
    ReaperTypedIrField extended_fields[3];
    memcpy(extended_types, types, sizeof types);
    memcpy(extended_fields, fields, sizeof fields);
    extended_types[6] = recursive_type;
    extended_fields[2] = recursive_field;

    module.types = extended_types;
    module.type_count = 7u;
    module.fields = extended_fields;
    module.field_count = 3u;
    assert(!reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_TYPE);
    assert(strstr(error.message, "recursive") != NULL);

    ReaperTypedIrType pointer_type = {
        6u, REAPER_TIR_TYPE_POINTER, REAPER_TIR_TYPE_FLAG_NONE, 7u,
        0u, 8u, 8u, 0u, 0u, 3u, "RecursivePointer"
    };
    ReaperTypedIrType node_type = {
        7u, REAPER_TIR_TYPE_STRUCT, REAPER_TIR_TYPE_FLAG_NONE, REAPER_TIR_NO_ID,
        0u, 8u, 8u, 2u, 1u, 3u, "Node"
    };
    ReaperTypedIrField node_field = { 7u, 6u, 3u, 0u, "next" };
    ReaperTypedIrType pointer_types[8];
    ReaperTypedIrField pointer_fields[3];
    memcpy(pointer_types, types, sizeof types);
    memcpy(pointer_fields, fields, sizeof fields);
    pointer_types[6] = pointer_type;
    pointer_types[7] = node_type;
    pointer_fields[2] = node_field;
    module.types = pointer_types;
    module.type_count = 8u;
    module.fields = pointer_fields;
    module.field_count = 3u;
    assert(reaper_typed_ir_verify(&module, &error));

    module.types = types;
    module.type_count = sizeof types / sizeof types[0];
    module.fields = fields;
    module.field_count = sizeof fields / sizeof fields[0];
}

static void target_pointer_layout_must_match(void) {
    ReaperTypedIrError error;
    uint32_t original = module.pointer_size;
    module.pointer_size = 16u;
    assert(!reaper_typed_ir_verify(&module, &error));
    assert(error.code == REAPER_TIR_ERROR_LAYOUT ||
           error.code == REAPER_TIR_ERROR_MODULE);
    module.pointer_size = original;
}

int main(void) {
    valid_module_and_source_map();
    source_map_rejects_out_of_range_and_duplicate_spans();
    aggregate_layout_is_checked();
    invalid_ssa_and_terminators_are_rejected();
    by_value_cycles_are_rejected_but_pointer_recursion_is_allowed();
    target_pointer_layout_must_match();
    puts("canonical typed IR tests: 6 groups passed");
    return 0;
}
