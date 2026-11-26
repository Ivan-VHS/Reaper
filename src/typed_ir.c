#include "reaper/typed_ir.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int reject(
    ReaperTypedIrError *error,
    ReaperTypedIrErrorCode code,
    size_t item_index,
    const char *message
) {
    if (error != NULL) {
        error->code = code;
        error->item_index = item_index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static int power_of_two(uint32_t value) {
    return value != 0u && (value & (value - 1u)) == 0u && value <= 65536u;
}

static int checked_add_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (right > UINT64_MAX - left) return 0;
    *result = left + right;
    return 1;
}

static int checked_mul_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (left != 0u && right > UINT64_MAX / left) return 0;
    *result = left * right;
    return 1;
}

static int range_valid(uint32_t first, uint32_t count, size_t total) {
    return (size_t)first <= total && (size_t)count <= total - (size_t)first;
}

static const ReaperSourceFile *find_source(
    const ReaperSourceMap *map,
    uint32_t id
) {
    for (size_t i = 0u; i < map->file_count; ++i) {
        if (map->files[i].id == id) return &map->files[i];
    }
    return NULL;
}

static const ReaperSpan *find_span(
    const ReaperSourceMap *map,
    uint32_t id
) {
    for (size_t i = 0u; i < map->span_count; ++i) {
        if (map->spans[i].id == id) return &map->spans[i];
    }
    return NULL;
}

static size_t find_type_index(const ReaperTypedIrModule *module, uint32_t id) {
    for (size_t i = 0u; i < module->type_count; ++i) {
        if (module->types[i].id == id) return i;
    }
    return SIZE_MAX;
}

static const ReaperTypedIrType *find_type(
    const ReaperTypedIrModule *module,
    uint32_t id
) {
    size_t index = find_type_index(module, id);
    return index == SIZE_MAX ? NULL : &module->types[index];
}

static size_t find_value_index(const ReaperTypedIrModule *module, uint32_t id) {
    for (size_t i = 0u; i < module->value_count; ++i) {
        if (module->values[i].id == id) return i;
    }
    return SIZE_MAX;
}

static const ReaperTypedIrValue *find_value(
    const ReaperTypedIrModule *module,
    uint32_t id
) {
    size_t index = find_value_index(module, id);
    return index == SIZE_MAX ? NULL : &module->values[index];
}

static const ReaperTypedIrBlock *find_block(
    const ReaperTypedIrModule *module,
    uint32_t id
) {
    for (size_t i = 0u; i < module->block_count; ++i) {
        if (module->blocks[i].id == id) return &module->blocks[i];
    }
    return NULL;
}

static const ReaperTypedIrFunction *find_function(
    const ReaperTypedIrModule *module,
    uint32_t id
) {
    for (size_t i = 0u; i < module->function_count; ++i) {
        if (module->functions[i].id == id) return &module->functions[i];
    }
    return NULL;
}

static int integral_type(ReaperTypedIrTypeKind kind) {
    return kind == REAPER_TIR_TYPE_I8 || kind == REAPER_TIR_TYPE_U8 ||
           kind == REAPER_TIR_TYPE_I16 || kind == REAPER_TIR_TYPE_U16 ||
           kind == REAPER_TIR_TYPE_I32 || kind == REAPER_TIR_TYPE_U32 ||
           kind == REAPER_TIR_TYPE_I64 || kind == REAPER_TIR_TYPE_U64;
}

static int primitive_layout(
    ReaperTypedIrTypeKind kind,
    uint64_t *size,
    uint32_t *alignment
) {
    switch (kind) {
    case REAPER_TIR_TYPE_UNIT:
        *size = 0u; *alignment = 1u; return 1;
    case REAPER_TIR_TYPE_BOOL:
    case REAPER_TIR_TYPE_I8:
    case REAPER_TIR_TYPE_U8:
        *size = 1u; *alignment = 1u; return 1;
    case REAPER_TIR_TYPE_I16:
    case REAPER_TIR_TYPE_U16:
        *size = 2u; *alignment = 2u; return 1;
    case REAPER_TIR_TYPE_I32:
    case REAPER_TIR_TYPE_U32:
    case REAPER_TIR_TYPE_F32:
        *size = 4u; *alignment = 4u; return 1;
    case REAPER_TIR_TYPE_I64:
    case REAPER_TIR_TYPE_U64:
    case REAPER_TIR_TYPE_F64:
        *size = 8u; *alignment = 8u; return 1;
    default:
        return 0;
    }
}

int reaper_source_map_resolve(
    const ReaperSourceMap *source_map,
    uint32_t span_id,
    const ReaperSourceFile **source_file,
    const ReaperSpan **span
) {
    if (source_file != NULL) *source_file = NULL;
    if (span != NULL) *span = NULL;
    if (source_map == NULL || source_file == NULL || span == NULL ||
        (source_map->file_count != 0u && source_map->files == NULL) ||
        (source_map->span_count != 0u && source_map->spans == NULL)) {
        return 0;
    }

    const ReaperSpan *found_span = find_span(source_map, span_id);
    if (found_span == NULL) return 0;
    const ReaperSourceFile *found_file = find_source(source_map, found_span->source_id);
    if (found_file == NULL) return 0;
    *source_file = found_file;
    *span = found_span;
    return 1;
}

static int verify_source_map(
    const ReaperSourceMap *map,
    ReaperTypedIrError *error
) {
    if (map->files == NULL || map->file_count == 0u ||
        map->spans == NULL || map->span_count == 0u) {
        return reject(error, REAPER_TIR_ERROR_SOURCE_MAP, 0u,
                      "SourceMap v1 requires source files and spans");
    }

    for (size_t i = 0u; i < map->file_count; ++i) {
        const ReaperSourceFile *file = &map->files[i];
        if (file->path == NULL || file->path[0] == '\0' ||
            (file->byte_length != 0u && file->contents == NULL) ||
            file->line_count == 0u) {
            return reject(error, REAPER_TIR_ERROR_SOURCE_MAP, i,
                          "source file requires path, source bytes and line count");
        }
        for (size_t prior = 0u; prior < i; ++prior) {
            if (map->files[prior].id == file->id) {
                return reject(error, REAPER_TIR_ERROR_SOURCE_MAP, i,
                              "source file identifiers must be unique");
            }
        }
    }

    for (size_t i = 0u; i < map->span_count; ++i) {
        const ReaperSpan *span = &map->spans[i];
        const ReaperSourceFile *file = find_source(map, span->source_id);
        if (file == NULL) {
            return reject(error, REAPER_TIR_ERROR_SPAN, i,
                          "span references an unknown source file");
        }
        if (span->byte_start > span->byte_end ||
            span->byte_end > file->byte_length) {
            return reject(error, REAPER_TIR_ERROR_SPAN, i,
                          "span byte range is outside its source file");
        }
        if (span->start_line == 0u || span->start_column == 0u ||
            span->end_line == 0u || span->end_column == 0u ||
            span->start_line > span->end_line ||
            span->end_line > file->line_count ||
            (span->start_line == span->end_line &&
             span->start_column > span->end_column)) {
            return reject(error, REAPER_TIR_ERROR_SPAN, i,
                          "span line and column coordinates are invalid");
        }
        for (size_t prior = 0u; prior < i; ++prior) {
            if (map->spans[prior].id == span->id) {
                return reject(error, REAPER_TIR_ERROR_SPAN, i,
                              "span identifiers must be unique");
            }
        }
    }
    return 1;
}

static int verify_type_layout(
    const ReaperTypedIrModule *module,
    size_t index,
    ReaperTypedIrError *error
) {
    const ReaperTypedIrType *type = &module->types[index];
    if (type->kind <= REAPER_TIR_TYPE_INVALID ||
        type->kind > REAPER_TIR_TYPE_OPAQUE) {
        return reject(error, REAPER_TIR_ERROR_TYPE, index,
                      "unknown typed IR type kind");
    }
    if (type->flags & ~(uint32_t)REAPER_TIR_TYPE_FLAG_PACKED) {
        return reject(error, REAPER_TIR_ERROR_TYPE, index,
                      "typed IR type contains unsupported flags");
    }
    if (find_span(&module->source_map, type->span_id) == NULL) {
        return reject(error, REAPER_TIR_ERROR_TYPE, index,
                      "type references an unknown source span");
    }
    if (!power_of_two(type->byte_alignment) ||
        (type->byte_size != 0u &&
         type->byte_size % type->byte_alignment != 0u)) {
        return reject(error, REAPER_TIR_ERROR_LAYOUT, index,
                      "type size and alignment are not canonical");
    }

    uint64_t expected_size = 0u;
    uint32_t expected_alignment = 0u;
    if (primitive_layout(type->kind, &expected_size, &expected_alignment)) {
        if (type->byte_size != expected_size ||
            type->byte_alignment != expected_alignment ||
            type->element_type_id != REAPER_TIR_NO_ID ||
            type->element_count != 0u || type->field_count != 0u) {
            return reject(error, REAPER_TIR_ERROR_LAYOUT, index,
                          "primitive type layout or metadata is invalid");
        }
        return 1;
    }

    if (type->kind == REAPER_TIR_TYPE_POINTER) {
        if (find_type(module, type->element_type_id) == NULL ||
            type->byte_size != module->pointer_size ||
            type->byte_alignment != module->pointer_alignment ||
            type->field_count != 0u) {
            return reject(error, REAPER_TIR_ERROR_LAYOUT, index,
                          "pointer type does not match the selected target layout");
        }
        return 1;
    }

    if (type->kind == REAPER_TIR_TYPE_ARRAY) {
        const ReaperTypedIrType *element = find_type(module, type->element_type_id);
        if (element == NULL || type->element_count == 0u ||
            type->field_count != 0u ||
            !checked_mul_u64(element->byte_size, type->element_count, &expected_size) ||
            type->byte_size != expected_size ||
            type->byte_alignment != element->byte_alignment) {
            return reject(error, REAPER_TIR_ERROR_LAYOUT, index,
                          "fixed array size or alignment is inconsistent with its element type");
        }
        return 1;
    }

    if (type->kind == REAPER_TIR_TYPE_ENUM ||
        type->kind == REAPER_TIR_TYPE_DISTINCT) {
        const ReaperTypedIrType *underlying = find_type(module, type->element_type_id);
        if (underlying == NULL || type->field_count != 0u ||
            (type->kind == REAPER_TIR_TYPE_ENUM && !integral_type(underlying->kind)) ||
            type->byte_size != underlying->byte_size ||
            type->byte_alignment != underlying->byte_alignment) {
            return reject(error, REAPER_TIR_ERROR_LAYOUT, index,
                          "enum or distinct type does not preserve its underlying representation");
        }
        return 1;
    }

    if (type->kind == REAPER_TIR_TYPE_OPAQUE) {
        if (type->name == NULL || type->name[0] == '\0' ||
            type->byte_size == 0u || type->element_type_id != REAPER_TIR_NO_ID ||
            type->field_count != 0u) {
            return reject(error, REAPER_TIR_ERROR_TYPE, index,
                          "opaque type requires a name, positive size and no exposed fields");
        }
        return 1;
    }

    if (type->kind == REAPER_TIR_TYPE_STRUCT ||
        type->kind == REAPER_TIR_TYPE_UNION) {
        if (type->name == NULL || type->name[0] == '\0' ||
            type->field_count == 0u ||
            !range_valid(type->first_field, type->field_count, module->field_count)) {
            return reject(error, REAPER_TIR_ERROR_FIELD, index,
                          "aggregate type requires a name and a valid non-empty field range");
        }
        uint64_t previous_end = 0u;
        uint32_t maximum_field_alignment = 1u;
        uint64_t maximum_member_size = 0u;
        for (size_t j = 0u; j < type->field_count; ++j) {
            size_t field_index = (size_t)type->first_field + j;
            const ReaperTypedIrField *field = &module->fields[field_index];
            const ReaperTypedIrType *field_type = find_type(module, field->type_id);
            if (field->owner_type_id != type->id || field_type == NULL ||
                field->name == NULL || field->name[0] == '\0' ||
                find_span(&module->source_map, field->span_id) == NULL) {
                return reject(error, REAPER_TIR_ERROR_FIELD, field_index,
                              "aggregate field has an invalid owner, name, type or span");
            }
            for (size_t prior = 0u; prior < j; ++prior) {
                const ReaperTypedIrField *previous =
                    &module->fields[(size_t)type->first_field + prior];
                if (strcmp(previous->name, field->name) == 0) {
                    return reject(error, REAPER_TIR_ERROR_FIELD, field_index,
                                  "aggregate field names must be unique");
                }
            }

            const uint32_t effective_alignment =
                (type->flags & REAPER_TIR_TYPE_FLAG_PACKED) != 0u
                    ? 1u : field_type->byte_alignment;
            if (field->byte_offset % effective_alignment != 0u) {
                return reject(error, REAPER_TIR_ERROR_LAYOUT, field_index,
                              "aggregate field offset violates its effective alignment");
            }
            uint64_t field_end = 0u;
            if (!checked_add_u64(field->byte_offset, field_type->byte_size, &field_end) ||
                field_end > type->byte_size) {
                return reject(error, REAPER_TIR_ERROR_LAYOUT, field_index,
                              "aggregate field extends beyond its containing type");
            }
            if (type->kind == REAPER_TIR_TYPE_UNION) {
                if (field->byte_offset != 0u) {
                    return reject(error, REAPER_TIR_ERROR_LAYOUT, field_index,
                                  "union fields must begin at offset zero");
                }
            } else {
                if (field->byte_offset < previous_end) {
                    return reject(error, REAPER_TIR_ERROR_LAYOUT, field_index,
                                  "struct fields overlap or are not in canonical order");
                }
                previous_end = field_end;
            }
            if (field_type->byte_alignment > maximum_field_alignment) {
                maximum_field_alignment = field_type->byte_alignment;
            }
            if (field_type->byte_size > maximum_member_size) {
                maximum_member_size = field_type->byte_size;
            }
        }
        if (type->byte_alignment < maximum_field_alignment ||
            type->byte_size < maximum_member_size) {
            return reject(error, REAPER_TIR_ERROR_LAYOUT, index,
                          "aggregate size or alignment is smaller than a member requires");
        }
        return 1;
    }

    return reject(error, REAPER_TIR_ERROR_TYPE, index,
                  "typed IR type kind has no v1 layout rule");
}

static int visit_type(
    const ReaperTypedIrModule *module,
    size_t index,
    unsigned char *states,
    size_t depth,
    ReaperTypedIrError *error
) {
    if (depth > module->type_count) {
        return reject(error, REAPER_TIR_ERROR_TYPE, index,
                      "by-value type graph exceeds the supported depth");
    }
    if (states[index] == 1u) {
        return reject(error, REAPER_TIR_ERROR_TYPE, index,
                      "by-value recursive type has no finite layout");
    }
    if (states[index] == 2u) return 1;
    states[index] = 1u;

    const ReaperTypedIrType *type = &module->types[index];
    if (type->kind == REAPER_TIR_TYPE_ARRAY ||
        type->kind == REAPER_TIR_TYPE_ENUM ||
        type->kind == REAPER_TIR_TYPE_DISTINCT) {
        size_t child = find_type_index(module, type->element_type_id);
        if (child == SIZE_MAX ||
            !visit_type(module, child, states, depth + 1u, error)) {
            states[index] = 0u;
            return 0;
        }
    } else if (type->kind == REAPER_TIR_TYPE_STRUCT ||
               type->kind == REAPER_TIR_TYPE_UNION) {
        for (size_t j = 0u; j < type->field_count; ++j) {
            const ReaperTypedIrField *field =
                &module->fields[(size_t)type->first_field + j];
            size_t child = find_type_index(module, field->type_id);
            if (child == SIZE_MAX ||
                !visit_type(module, child, states, depth + 1u, error)) {
                states[index] = 0u;
                return 0;
            }
        }
    }
    /* Pointer edges are deliberately excluded: pointer recursion is finite. */
    states[index] = 2u;
    return 1;
}

static int verify_types(
    const ReaperTypedIrModule *module,
    ReaperTypedIrError *error
) {
    if (module->types == NULL || module->type_count == 0u ||
        (module->field_count != 0u && module->fields == NULL)) {
        return reject(error, REAPER_TIR_ERROR_TYPE, 0u,
                      "typed IR requires a non-empty type table");
    }
    for (size_t i = 0u; i < module->type_count; ++i) {
        for (size_t prior = 0u; prior < i; ++prior) {
            if (module->types[prior].id == module->types[i].id) {
                return reject(error, REAPER_TIR_ERROR_TYPE, i,
                              "type identifiers must be unique");
            }
        }
        if (!verify_type_layout(module, i, error)) return 0;
    }

    unsigned char *states = calloc(module->type_count, sizeof *states);
    if (states == NULL) {
        return reject(error, REAPER_TIR_ERROR_MEMORY, 0u,
                      "cannot allocate type graph verification state");
    }
    for (size_t i = 0u; i < module->type_count; ++i) {
        if (!visit_type(module, i, states, 0u, error)) {
            free(states);
            return 0;
        }
    }
    free(states);
    return 1;
}

static int verify_functions_and_blocks(
    const ReaperTypedIrModule *module,
    ReaperTypedIrError *error
) {
    if (module->functions == NULL || module->function_count == 0u ||
        module->blocks == NULL || module->block_count == 0u ||
        (module->parameter_count != 0u && module->parameters == NULL)) {
        return reject(error, REAPER_TIR_ERROR_FUNCTION, 0u,
                      "typed IR requires functions and basic blocks");
    }

    for (size_t i = 0u; i < module->function_count; ++i) {
        const ReaperTypedIrFunction *function = &module->functions[i];
        if (function->name == NULL || function->name[0] == '\0' ||
            find_type(module, function->return_type_id) == NULL ||
            find_span(&module->source_map, function->span_id) == NULL ||
            function->block_count == 0u ||
            !range_valid(function->first_block, function->block_count,
                         module->block_count) ||
            !range_valid(function->first_parameter, function->parameter_count,
                         module->parameter_count)) {
            return reject(error, REAPER_TIR_ERROR_FUNCTION, i,
                          "function has an invalid name, type, span or table range");
        }
        for (size_t prior = 0u; prior < i; ++prior) {
            if (module->functions[prior].id == function->id ||
                strcmp(module->functions[prior].name, function->name) == 0) {
                return reject(error, REAPER_TIR_ERROR_FUNCTION, i,
                              "function identifiers and names must be unique");
            }
        }

        int entry_found = 0;
        for (size_t j = 0u; j < function->block_count; ++j) {
            const ReaperTypedIrBlock *block =
                &module->blocks[(size_t)function->first_block + j];
            if (block->function_id != function->id) {
                return reject(error, REAPER_TIR_ERROR_BLOCK,
                              (size_t)function->first_block + j,
                              "function block range contains a block owned by another function");
            }
            if (block->id == function->entry_block_id) entry_found = 1;
        }
        if (!entry_found) {
            return reject(error, REAPER_TIR_ERROR_FUNCTION, i,
                          "function entry block is not in its block range");
        }

        for (size_t j = 0u; j < function->parameter_count; ++j) {
            size_t parameter_index = (size_t)function->first_parameter + j;
            const ReaperTypedIrParameter *parameter =
                &module->parameters[parameter_index];
            if (parameter->function_id != function->id ||
                parameter->name == NULL || parameter->name[0] == '\0' ||
                find_type(module, parameter->type_id) == NULL ||
                find_span(&module->source_map, parameter->span_id) == NULL) {
                return reject(error, REAPER_TIR_ERROR_PARAMETER, parameter_index,
                              "function parameter has an invalid owner, name, type or span");
            }
            for (size_t prior = 0u; prior < j; ++prior) {
                const ReaperTypedIrParameter *other =
                    &module->parameters[(size_t)function->first_parameter + prior];
                if (strcmp(other->name, parameter->name) == 0) {
                    return reject(error, REAPER_TIR_ERROR_PARAMETER, parameter_index,
                                  "function parameter names must be unique");
                }
            }
        }
    }

    for (size_t i = 0u; i < module->block_count; ++i) {
        const ReaperTypedIrBlock *block = &module->blocks[i];
        if (find_function(module, block->function_id) == NULL ||
            find_span(&module->source_map, block->span_id) == NULL ||
            !range_valid(block->first_value, block->value_count, module->value_count)) {
            return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                          "basic block has an invalid owner, source span or value range");
        }
        for (size_t prior = 0u; prior < i; ++prior) {
            if (module->blocks[prior].id == block->id) {
                return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                              "basic block identifiers must be unique");
            }
        }

        for (size_t function_index = 0u;
             function_index < module->function_count; ++function_index) {
            const ReaperTypedIrFunction *function =
                &module->functions[function_index];
            if (block->function_id == function->id &&
                ((size_t)i < function->first_block ||
                 (size_t)i >= (size_t)function->first_block + function->block_count)) {
                return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                              "basic block is outside its owning function range");
            }
        }
        for (size_t function_index = 0u;
             function_index < module->function_count; ++function_index) {
            const ReaperTypedIrFunction *function =
                &module->functions[function_index];
            if ((size_t)i >= function->first_block &&
                (size_t)i < (size_t)function->first_block + function->block_count &&
                block->function_id != function->id) {
                return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                              "basic block range is claimed by a different function");
            }
        }

        if (block->terminator < REAPER_TIR_TERM_RETURN ||
            block->terminator > REAPER_TIR_TERM_UNREACHABLE) {
            return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                          "basic block has an unsupported terminator");
        }
    }
    return 1;
}

static int value_is_prior_local(
    const ReaperTypedIrModule *module,
    size_t value_index,
    uint32_t referenced_id,
    uint32_t block_id,
    const ReaperTypedIrValue **referenced
) {
    size_t index = find_value_index(module, referenced_id);
    if (index == SIZE_MAX || index >= value_index ||
        module->values[index].block_id != block_id) return 0;
    *referenced = &module->values[index];
    return 1;
}

static int verify_values(
    const ReaperTypedIrModule *module,
    ReaperTypedIrError *error
) {
    if (module->value_count != 0u && module->values == NULL) {
        return reject(error, REAPER_TIR_ERROR_VALUE, 0u,
                      "value storage is missing");
    }

    for (size_t i = 0u; i < module->value_count; ++i) {
        const ReaperTypedIrValue *value = &module->values[i];
        const ReaperTypedIrBlock *block = find_block(module, value->block_id);
        const ReaperTypedIrType *type = find_type(module, value->type_id);
        if (block == NULL || type == NULL ||
            find_span(&module->source_map, value->span_id) == NULL) {
            return reject(error, REAPER_TIR_ERROR_VALUE, i,
                          "value has an unknown block, type or source span");
        }
        if ((size_t)i < block->first_value ||
            (size_t)i >= (size_t)block->first_value + block->value_count) {
            return reject(error, REAPER_TIR_ERROR_VALUE, i,
                          "value is outside its basic block's declared value range");
        }
        for (size_t prior = 0u; prior < i; ++prior) {
            if (module->values[prior].id == value->id) {
                return reject(error, REAPER_TIR_ERROR_VALUE, i,
                              "SSA value identifiers must be unique");
            }
        }

        const ReaperTypedIrValue *lhs = NULL;
        const ReaperTypedIrValue *rhs = NULL;
        switch (value->opcode) {
        case REAPER_TIR_OP_CONST_I64:
            if (type->kind != REAPER_TIR_TYPE_I64 ||
                value->lhs != REAPER_TIR_NO_ID ||
                value->rhs != REAPER_TIR_NO_ID) {
                return reject(error, REAPER_TIR_ERROR_VALUE, i,
                              "CONST_I64 must define i64 without operands");
            }
            break;
        case REAPER_TIR_OP_ADD_I64:
        case REAPER_TIR_OP_SUB_I64:
        case REAPER_TIR_OP_MUL_I64:
            if (type->kind != REAPER_TIR_TYPE_I64 ||
                !value_is_prior_local(module, i, value->lhs, value->block_id, &lhs) ||
                !value_is_prior_local(module, i, value->rhs, value->block_id, &rhs) ||
                lhs->type_id != value->type_id || rhs->type_id != value->type_id) {
                return reject(error, REAPER_TIR_ERROR_VALUE, i,
                              "integer arithmetic requires two earlier local i64 operands");
            }
            break;
        case REAPER_TIR_OP_COPY:
            if (value->rhs != REAPER_TIR_NO_ID ||
                !value_is_prior_local(module, i, value->lhs, value->block_id, &lhs) ||
                lhs->type_id != value->type_id) {
                return reject(error, REAPER_TIR_ERROR_VALUE, i,
                              "COPY requires one earlier local value of the same type");
            }
            break;
        default:
            return reject(error, REAPER_TIR_ERROR_VALUE, i,
                          "unsupported typed IR value opcode");
        }
    }

    /* Block value ranges must partition the value table without gaps or overlap. */
    size_t expected_first = 0u;
    for (size_t i = 0u; i < module->block_count; ++i) {
        const ReaperTypedIrBlock *block = &module->blocks[i];
        if (block->first_value != expected_first) {
            return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                          "basic block value ranges must be contiguous and ordered");
        }
        for (size_t j = 0u; j < block->value_count; ++j) {
            size_t value_index = (size_t)block->first_value + j;
            if (module->values[value_index].block_id != block->id) {
                return reject(error, REAPER_TIR_ERROR_VALUE, value_index,
                              "basic block value range contains a value owned by another block");
            }
        }
        expected_first += block->value_count;
    }
    if (expected_first != module->value_count) {
        return reject(error, REAPER_TIR_ERROR_VALUE, expected_first,
                      "basic block ranges do not cover the value table");
    }
    return 1;
}

static int verify_terminators(
    const ReaperTypedIrModule *module,
    ReaperTypedIrError *error
) {
    for (size_t i = 0u; i < module->block_count; ++i) {
        const ReaperTypedIrBlock *block = &module->blocks[i];
        const ReaperTypedIrFunction *function =
            find_function(module, block->function_id);
        const ReaperTypedIrValue *operand = NULL;
        const ReaperTypedIrType *return_type = find_type(module, function->return_type_id);

        if (block->terminator == REAPER_TIR_TERM_RETURN) {
            if (return_type->kind == REAPER_TIR_TYPE_UNIT) {
                if (block->operand_value_id != REAPER_TIR_NO_ID) {
                    return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                                  "unit-returning function cannot return a value");
                }
            } else {
                size_t value_index = find_value_index(module, block->operand_value_id);
                if (value_index == SIZE_MAX ||
                    module->values[value_index].block_id != block->id ||
                    module->values[value_index].type_id != function->return_type_id) {
                    return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                                  "return operand must be a local value of the function result type");
                }
            }
            if (block->true_target_block_id != REAPER_TIR_NO_ID ||
                block->false_target_block_id != REAPER_TIR_NO_ID) {
                return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                              "RETURN cannot have successor blocks");
            }
        } else if (block->terminator == REAPER_TIR_TERM_JUMP) {
            const ReaperTypedIrBlock *target =
                find_block(module, block->true_target_block_id);
            if (block->operand_value_id != REAPER_TIR_NO_ID || target == NULL ||
                target->function_id != block->function_id ||
                block->false_target_block_id != REAPER_TIR_NO_ID) {
                return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                              "JUMP requires one successor in the same function");
            }
        } else if (block->terminator == REAPER_TIR_TERM_COND_JUMP) {
            size_t value_index = find_value_index(module, block->operand_value_id);
            const ReaperTypedIrBlock *yes =
                find_block(module, block->true_target_block_id);
            const ReaperTypedIrBlock *no =
                find_block(module, block->false_target_block_id);
            if (value_index == SIZE_MAX ||
                module->values[value_index].block_id != block->id ||
                find_type(module, module->values[value_index].type_id)->kind != REAPER_TIR_TYPE_BOOL ||
                yes == NULL || no == NULL ||
                yes->function_id != block->function_id ||
                no->function_id != block->function_id) {
                return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                              "COND_JUMP requires a local bool and two same-function successors");
            }
        } else {
            if (block->operand_value_id != REAPER_TIR_NO_ID ||
                block->true_target_block_id != REAPER_TIR_NO_ID ||
                block->false_target_block_id != REAPER_TIR_NO_ID) {
                return reject(error, REAPER_TIR_ERROR_BLOCK, i,
                              "UNREACHABLE cannot have operands or successors");
            }
        }
        (void)operand;
    }
    return 1;
}

int reaper_typed_ir_verify(
    const ReaperTypedIrModule *module,
    ReaperTypedIrError *error
) {
    if (error != NULL) {
        error->code = REAPER_TIR_ERROR_NONE;
        error->item_index = 0u;
        error->message[0] = '\0';
    }
    if (module == NULL || module->version != REAPER_TIR_VERSION ||
        module->target_triple == NULL || module->target_triple[0] == '\0' ||
        (module->pointer_size != 4u && module->pointer_size != 8u) ||
        !power_of_two(module->pointer_alignment) ||
        module->pointer_alignment > module->pointer_size) {
        return reject(error, REAPER_TIR_ERROR_MODULE, 0u,
                      "Typed IR v1 requires a target triple and valid pointer layout");
    }
    if (!verify_source_map(&module->source_map, error)) return 0;
    if (!verify_types(module, error)) return 0;
    if (!verify_functions_and_blocks(module, error)) return 0;
    if (!verify_values(module, error)) return 0;
    if (!verify_terminators(module, error)) return 0;
    return 1;
}

const char *reaper_typed_ir_type_name(ReaperTypedIrTypeKind kind) {
    switch (kind) {
    case REAPER_TIR_TYPE_UNIT: return "unit";
    case REAPER_TIR_TYPE_BOOL: return "bool";
    case REAPER_TIR_TYPE_I8: return "i8";
    case REAPER_TIR_TYPE_U8: return "u8";
    case REAPER_TIR_TYPE_I16: return "i16";
    case REAPER_TIR_TYPE_U16: return "u16";
    case REAPER_TIR_TYPE_I32: return "i32";
    case REAPER_TIR_TYPE_U32: return "u32";
    case REAPER_TIR_TYPE_I64: return "i64";
    case REAPER_TIR_TYPE_U64: return "u64";
    case REAPER_TIR_TYPE_F32: return "f32";
    case REAPER_TIR_TYPE_F64: return "f64";
    case REAPER_TIR_TYPE_POINTER: return "pointer";
    case REAPER_TIR_TYPE_ARRAY: return "array";
    case REAPER_TIR_TYPE_STRUCT: return "struct";
    case REAPER_TIR_TYPE_UNION: return "union";
    case REAPER_TIR_TYPE_ENUM: return "enum";
    case REAPER_TIR_TYPE_DISTINCT: return "distinct";
    case REAPER_TIR_TYPE_OPAQUE: return "opaque";
    default: return "invalid";
    }
}

const char *reaper_typed_ir_opcode_name(ReaperTypedIrOpcode opcode) {
    switch (opcode) {
    case REAPER_TIR_OP_CONST_I64: return "const.i64";
    case REAPER_TIR_OP_ADD_I64: return "add.i64";
    case REAPER_TIR_OP_SUB_I64: return "sub.i64";
    case REAPER_TIR_OP_MUL_I64: return "mul.i64";
    case REAPER_TIR_OP_COPY: return "copy";
    default: return "invalid";
    }
}
