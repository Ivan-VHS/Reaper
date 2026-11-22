#include "reaper/mir.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct MirBuilder {
    const ReaperHirModule *hir;
    ReaperMirModule *module;
    ReaperMirError *error;
    uint32_t current_function;
    uint32_t current_block;
    uint32_t next_value;
} MirBuilder;

static char *copy_text(const char *text) {
    size_t length = strlen(text);
    char *copy = malloc(length + 1U);
    if (copy != NULL) memcpy(copy, text, length + 1U);
    return copy;
}

static int fail(MirBuilder *builder, size_t node, const char *message) {
    if (builder->error != NULL && builder->error->message[0] == '\0') {
        builder->error->node_index = node;
        (void)snprintf(builder->error->message, sizeof builder->error->message,
            "%s", message);
    }
    return 0;
}

static ReaperHirNode *hir_node(MirBuilder *builder, uint32_t id) {
    if (id == REAPER_MIR_NO_VALUE || id >= builder->hir->node_count) return NULL;
    return &builder->hir->nodes[id];
}

static ReaperMirBlock *block_at(ReaperMirModule *module, uint32_t id) {
    if (id >= module->block_count) return NULL;
    return &module->blocks[id];
}

static ReaperMirFunction *function_at(ReaperMirModule *module, uint32_t id) {
    if (id >= module->function_count) return NULL;
    return &module->functions[id];
}

static int grow_array(void **storage, size_t *capacity, size_t count,
                      size_t item_size, size_t minimum) {
    if (count < *capacity) return 1;
    size_t next = *capacity == 0U ? minimum : *capacity * 2U;
    if (next < *capacity || next > SIZE_MAX / item_size) return 0;
    void *items = realloc(*storage, next * item_size);
    if (items == NULL) return 0;
    *storage = items;
    *capacity = next;
    return 1;
}

static uint32_t add_block(MirBuilder *builder, size_t source_node) {
    ReaperMirModule *module = builder->module;
    if (module->block_count >= UINT32_MAX ||
        !grow_array((void **)&module->blocks, &module->block_capacity,
                    module->block_count, sizeof *module->blocks, 8U)) {
        (void)fail(builder, source_node, "unable to allocate MIR basic block");
        return REAPER_MIR_NO_BLOCK;
    }

    uint32_t id = (uint32_t)module->block_count;
    module->blocks[module->block_count++] = (ReaperMirBlock) {
        id, builder->current_function, UINT32_MAX, 0U,
        REAPER_MIR_TERM_NONE, REAPER_MIR_NO_VALUE,
        REAPER_MIR_NO_BLOCK, REAPER_MIR_NO_BLOCK
    };

    ReaperMirFunction *function = function_at(module, builder->current_function);
    if (function == NULL) {
        (void)fail(builder, source_node, "MIR block has no owning function");
        return REAPER_MIR_NO_BLOCK;
    }
    if (function->block_count == 0U) function->first_block = id;
    ++function->block_count;
    return id;
}

static uint32_t add_value(MirBuilder *builder, size_t source_node) {
    if (builder->next_value == UINT32_MAX) {
        (void)fail(builder, source_node, "MIR value index limit exceeded");
        return REAPER_MIR_NO_VALUE;
    }
    return builder->next_value++;
}

static uint32_t add_operand(MirBuilder *builder, uint32_t value, size_t source_node) {
    ReaperMirModule *module = builder->module;
    if (module->operand_count >= UINT32_MAX ||
        !grow_array((void **)&module->operands, &module->operand_capacity,
                    module->operand_count, sizeof *module->operands, 16U)) {
        (void)fail(builder, source_node, "unable to allocate MIR operand storage");
        return UINT32_MAX;
    }
    uint32_t index = (uint32_t)module->operand_count;
    module->operands[module->operand_count++] = value;
    return index;
}

static int append_instruction(
    MirBuilder *builder,
    ReaperMirInstruction instruction,
    size_t source_node
) {
    ReaperMirModule *module = builder->module;
    ReaperMirBlock *block = block_at(module, builder->current_block);
    if (block == NULL || block->terminator != REAPER_MIR_TERM_NONE) {
        return fail(builder, source_node, "cannot append an instruction after a MIR terminator");
    }
    if (module->instruction_count >= UINT32_MAX ||
        module->instruction_order_count >= UINT32_MAX ||
        !grow_array((void **)&module->instructions,
                    &module->instruction_capacity,
                    module->instruction_count,
                    sizeof *module->instructions, 16U) ||
        !grow_array((void **)&module->instruction_order,
                    &module->instruction_order_capacity,
                    module->instruction_order_count,
                    sizeof *module->instruction_order, 16U)) {
        return fail(builder, source_node, "unable to allocate MIR instruction storage");
    }

    uint32_t instruction_id = (uint32_t)module->instruction_count;
    if (block->instruction_count == 0U)
        block->first_instruction = (uint32_t)module->instruction_order_count;
    ++block->instruction_count;
    module->instructions[module->instruction_count++] = instruction;
    module->instruction_order[module->instruction_order_count++] = instruction_id;
    return 1;
}

static uint32_t emit_instruction(
    MirBuilder *builder,
    ReaperMirOpcode opcode,
    ReaperHirType type,
    uint32_t left,
    uint32_t right,
    uint32_t symbol_id,
    uint32_t source_node,
    const char *text
) {
    uint32_t result = add_value(builder, source_node);
    if (result == REAPER_MIR_NO_VALUE) return result;
    char *copy = copy_text(text != NULL ? text : "");
    if (copy == NULL) {
        (void)fail(builder, source_node, "unable to copy MIR instruction text");
        return REAPER_MIR_NO_VALUE;
    }

    ReaperMirInstruction instruction = {
        opcode, type, result, left, right, symbol_id, source_node,
        0U, 0U, copy
    };
    if (!append_instruction(builder, instruction, source_node)) {
        free(copy);
        return REAPER_MIR_NO_VALUE;
    }
    return result;
}

static int emit_void_instruction(
    MirBuilder *builder,
    ReaperMirOpcode opcode,
    uint32_t left,
    uint32_t symbol_id,
    uint32_t source_node
) {
    ReaperMirInstruction instruction = {
        opcode, REAPER_HIR_TYPE_UNIT, REAPER_MIR_NO_VALUE,
        left, REAPER_MIR_NO_VALUE, symbol_id, source_node,
        0U, 0U, copy_text("")
    };
    if (instruction.text == NULL)
        return fail(builder, source_node, "unable to allocate MIR instruction text");
    if (!append_instruction(builder, instruction, source_node)) {
        free(instruction.text);
        return 0;
    }
    return 1;
}

static uint32_t emit_call(
    MirBuilder *builder,
    ReaperMirOpcode opcode,
    ReaperHirType type,
    uint32_t callee_value,
    const uint32_t *arguments,
    size_t argument_count,
    uint32_t source_node,
    const char *callee_name
) {
    if (argument_count > UINT32_MAX ||
        builder->module->operand_count > UINT32_MAX - argument_count) {
        (void)fail(builder, source_node, "MIR call argument vector exceeds the index limit");
        return REAPER_MIR_NO_VALUE;
    }
    uint32_t offset = (uint32_t)builder->module->operand_count;
    for (size_t i = 0U; i < argument_count; ++i) {
        if (add_operand(builder, arguments[i], source_node) == UINT32_MAX)
            return REAPER_MIR_NO_VALUE;
    }

    uint32_t result = add_value(builder, source_node);
    if (result == REAPER_MIR_NO_VALUE) return result;
    char *copy = copy_text(callee_name != NULL ? callee_name : "");
    if (copy == NULL) {
        (void)fail(builder, source_node, "unable to copy MIR callee name");
        return REAPER_MIR_NO_VALUE;
    }

    ReaperMirInstruction instruction = {
        opcode, type, result, callee_value, REAPER_MIR_NO_VALUE,
        REAPER_MIR_NO_VALUE, source_node, offset,
        (uint32_t)argument_count, copy
    };
    if (!append_instruction(builder, instruction, source_node)) {
        free(copy);
        return REAPER_MIR_NO_VALUE;
    }
    return result;
}

static int append_jump(MirBuilder *builder, uint32_t target, size_t source_node) {
    ReaperMirBlock *block = block_at(builder->module, builder->current_block);
    if (block == NULL || target == REAPER_MIR_NO_BLOCK)
        return fail(builder, source_node, "invalid MIR jump");
    if (block->terminator != REAPER_MIR_TERM_NONE)
        return fail(builder, source_node, "MIR block already has a terminator");
    block->terminator = REAPER_MIR_TERM_JUMP;
    block->target_true = target;
    return 1;
}

static int append_branch(
    MirBuilder *builder,
    uint32_t condition,
    uint32_t yes,
    uint32_t no,
    size_t source_node
) {
    ReaperMirBlock *block = block_at(builder->module, builder->current_block);
    if (block == NULL || yes == REAPER_MIR_NO_BLOCK || no == REAPER_MIR_NO_BLOCK)
        return fail(builder, source_node, "invalid MIR branch target");
    if (block->terminator != REAPER_MIR_TERM_NONE)
        return fail(builder, source_node, "MIR block already has a terminator");
    block->terminator = REAPER_MIR_TERM_BRANCH;
    block->terminator_value = condition;
    block->target_true = yes;
    block->target_false = no;
    return 1;
}

static int append_return(
    MirBuilder *builder,
    uint32_t value,
    size_t source_node
) {
    ReaperMirBlock *block = block_at(builder->module, builder->current_block);
    if (block == NULL || block->terminator != REAPER_MIR_TERM_NONE)
        return fail(builder, source_node, "invalid MIR return terminator");
    block->terminator = REAPER_MIR_TERM_RETURN;
    block->terminator_value = value;
    return 1;
}

static uint32_t lower_expression(MirBuilder *builder, uint32_t node_id);

static uint32_t lower_sequence_values(
    MirBuilder *builder,
    uint32_t sequence_id,
    uint32_t *values,
    size_t capacity,
    size_t *value_count,
    size_t source_node
) {
    size_t count = 0U;
    uint32_t current = sequence_id;
    while (current != REAPER_MIR_NO_VALUE) {
        ReaperHirNode *sequence = hir_node(builder, current);
        if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE ||
            count >= capacity) {
            (void)fail(builder, source_node, "malformed MIR expression argument sequence");
            return REAPER_MIR_NO_VALUE;
        }
        uint32_t value = lower_expression(builder, sequence->left);
        if (value == REAPER_MIR_NO_VALUE) return value;
        values[count++] = value;
        current = sequence->right;
    }
    *value_count = count;
    return 0U;
}

static uint32_t lower_expression(MirBuilder *builder, uint32_t node_id) {
    ReaperHirNode *node = hir_node(builder, node_id);
    if (node == NULL) {
        (void)fail(builder, node_id, "MIR expression references a missing HIR node");
        return REAPER_MIR_NO_VALUE;
    }

    uint32_t left = REAPER_MIR_NO_VALUE;
    uint32_t right = REAPER_MIR_NO_VALUE;
    switch (node->kind) {
    case REAPER_AST_INTEGER:
    case REAPER_AST_DECIMAL:
    case REAPER_AST_STRING:
    case REAPER_AST_BOOLEAN:
    case REAPER_AST_NULL:
        return emit_instruction(
            builder, REAPER_MIR_CONST, node->type,
            REAPER_MIR_NO_VALUE, REAPER_MIR_NO_VALUE,
            REAPER_MIR_NO_VALUE, node_id, node->text
        );

    case REAPER_AST_IDENTIFIER: {
        if (node->symbol_id != REAPER_HIR_NO_SYMBOL &&
            node->symbol_id >= builder->hir->symbol_count) {
            (void)fail(builder, node_id, "HIR identifier has an invalid resolved symbol index");
            return REAPER_MIR_NO_VALUE;
        }
        ReaperHirSymbol *symbol = node->symbol_id == REAPER_HIR_NO_SYMBOL
            ? NULL : &builder->hir->symbols[node->symbol_id];
        if (symbol != NULL && symbol->kind == REAPER_HIR_SYMBOL_FUNCTION) {
            return emit_instruction(
                builder, REAPER_MIR_FUNCTION_REF, REAPER_HIR_TYPE_FUNCTION,
                REAPER_MIR_NO_VALUE, REAPER_MIR_NO_VALUE,
                node->symbol_id, node_id, node->text
            );
        }
        if (symbol == NULL) {
            return emit_instruction(
                builder, REAPER_MIR_BUILTIN_REF, REAPER_HIR_TYPE_FUNCTION,
                REAPER_MIR_NO_VALUE, REAPER_MIR_NO_VALUE,
                REAPER_HIR_NO_SYMBOL, node_id, node->text
            );
        }
        return emit_instruction(
            builder, REAPER_MIR_LOAD_LOCAL, node->type,
            REAPER_MIR_NO_VALUE, REAPER_MIR_NO_VALUE,
            node->symbol_id, node_id, node->text
        );
    }

    case REAPER_AST_UNARY:
        left = lower_expression(builder, node->left);
        if (left == REAPER_MIR_NO_VALUE) return left;
        return emit_instruction(
            builder, REAPER_MIR_UNARY, node->type,
            left, REAPER_MIR_NO_VALUE, REAPER_MIR_NO_SYMBOL,
            node_id, node->text
        );

    case REAPER_AST_BINARY:
        if (strcmp(node->text, "::") == 0) {
            ReaperHirNode *right_node = hir_node(builder, node->right);
            if (right_node == NULL) {
                (void)fail(builder, node_id, "flow operator has no right operand");
                return REAPER_MIR_NO_VALUE;
            }

            left = lower_expression(builder, node->left);
            if (left == REAPER_MIR_NO_VALUE) return left;

            uint32_t callee_node = node->right;
            uint32_t argument_sequence = REAPER_MIR_NO_VALUE;
            if (right_node->kind == REAPER_AST_CALL) {
                callee_node = right_node->left;
                argument_sequence = right_node->right;
            }
            uint32_t callee = lower_expression(builder, callee_node);
            if (callee == REAPER_MIR_NO_VALUE) return callee;

            size_t explicit_count = 0U;
            size_t max_args = builder->hir->node_count + 1U;
            uint32_t *arguments = calloc(max_args, sizeof *arguments);
            if (arguments == NULL) {
                (void)fail(builder, node_id, "unable to allocate MIR pipeline arguments");
                return REAPER_MIR_NO_VALUE;
            }
            arguments[explicit_count++] = left;
            size_t lowered_count = 0U;
            if (lower_sequence_values(
                    builder, argument_sequence, arguments + 1U,
                    max_args - 1U, &lowered_count, node_id) == REAPER_MIR_NO_VALUE) {
                free(arguments);
                return REAPER_MIR_NO_VALUE;
            }
            explicit_count += lowered_count;
            uint32_t result = emit_call(
                builder, REAPER_MIR_PIPE_CALL, node->type, callee,
                arguments, explicit_count, node_id,
                right_node->kind == REAPER_AST_CALL
                    ? hir_node(builder, right_node->left)->text : right_node->text
            );
            free(arguments);
            return result;
        }

        left = lower_expression(builder, node->left);
        right = lower_expression(builder, node->right);
        if (left == REAPER_MIR_NO_VALUE || right == REAPER_MIR_NO_VALUE)
            return REAPER_MIR_NO_VALUE;
        return emit_instruction(
            builder, REAPER_MIR_BINARY, node->type,
            left, right, REAPER_HIR_NO_SYMBOL, node_id, node->text
        );

    case REAPER_AST_CALL: {
        uint32_t callee = lower_expression(builder, node->left);
        if (callee == REAPER_MIR_NO_VALUE) return callee;
        size_t max_args = builder->hir->node_count + 1U;
        uint32_t *arguments = calloc(max_args, sizeof *arguments);
        if (arguments == NULL) {
            (void)fail(builder, node_id, "unable to allocate MIR call arguments");
            return REAPER_MIR_NO_VALUE;
        }
        size_t count = 0U;
        if (lower_sequence_values(
                builder, node->right, arguments, max_args, &count, node_id
            ) == REAPER_MIR_NO_VALUE) {
            free(arguments);
            return REAPER_MIR_NO_VALUE;
        }
        ReaperHirNode *callee_node = hir_node(builder, node->left);
        uint32_t result = emit_call(
            builder, REAPER_MIR_CALL, node->type, callee,
            arguments, count, node_id,
            callee_node != NULL ? callee_node->text : ""
        );
        free(arguments);
        return result;
    }

    case REAPER_AST_LIST: {
        size_t max_items = builder->hir->node_count + 1U;
        uint32_t *items = calloc(max_items, sizeof *items);
        if (items == NULL) {
            (void)fail(builder, node_id, "unable to allocate MIR list items");
            return REAPER_MIR_NO_VALUE;
        }
        size_t count = 0U;
        if (lower_sequence_values(
                builder, node->left, items, max_items, &count, node_id
            ) == REAPER_MIR_NO_VALUE) {
            free(items);
            return REAPER_MIR_NO_VALUE;
        }
        uint32_t result = emit_call(
            builder, REAPER_MIR_LIST, node->type, REAPER_MIR_NO_VALUE,
            items, count, node_id, "list"
        );
        free(items);
        return result;
    }

    case REAPER_AST_INDEX:
        left = lower_expression(builder, node->left);
        right = lower_expression(builder, node->right);
        if (left == REAPER_MIR_NO_VALUE || right == REAPER_MIR_NO_VALUE)
            return REAPER_MIR_NO_VALUE;
        return emit_instruction(
            builder, REAPER_MIR_INDEX, node->type,
            left, right, REAPER_HIR_NO_SYMBOL, node_id, "index"
        );

    default:
        (void)fail(builder, node_id, "statement or unsupported node used as a MIR expression");
        return REAPER_MIR_NO_VALUE;
    }
}

static int lower_sequence(MirBuilder *builder, uint32_t sequence_id);

static int lower_block(MirBuilder *builder, uint32_t block_id) {
    ReaperHirNode *block = hir_node(builder, block_id);
    if (block == NULL || block->kind != REAPER_AST_BLOCK)
        return fail(builder, block_id, "MIR expected a block node");
    return lower_sequence(builder, block->left);
}

static int finish_with_jump(MirBuilder *builder, uint32_t target, size_t source_node) {
    ReaperMirBlock *block = block_at(builder->module, builder->current_block);
    if (block == NULL) return fail(builder, source_node, "MIR block is missing");
    if (block->terminator == REAPER_MIR_TERM_NONE)
        return append_jump(builder, target, source_node);
    return 1;
}

static int lower_when(MirBuilder *builder, uint32_t node_id, ReaperHirNode *node) {
    uint32_t condition = lower_expression(builder, node->left);
    if (condition == REAPER_MIR_NO_VALUE) return 0;

    ReaperHirNode *branch_sequence = hir_node(builder, node->right);
    if (branch_sequence == NULL || branch_sequence->kind != REAPER_AST_SEQUENCE)
        return fail(builder, node_id, "MIR conditional requires a branch sequence");

    uint32_t yes_source = branch_sequence->left;
    ReaperHirNode *next_sequence = branch_sequence->right == REAPER_MIR_NO_VALUE
        ? NULL : hir_node(builder, branch_sequence->right);
    uint32_t no_source = next_sequence != NULL ? next_sequence->left : REAPER_MIR_NO_VALUE;

    uint32_t yes = add_block(builder, node_id);
    uint32_t no = add_block(builder, node_id);
    uint32_t join = add_block(builder, node_id);
    if (yes == REAPER_MIR_NO_BLOCK || no == REAPER_MIR_NO_BLOCK ||
        join == REAPER_MIR_NO_BLOCK) return 0;

    if (!append_branch(builder, condition, yes, no, node_id)) return 0;

    builder->current_block = yes;
    if (!lower_block(builder, yes_source) ||
        !finish_with_jump(builder, join, node_id)) return 0;

    builder->current_block = no;
    if (no_source != REAPER_MIR_NO_VALUE && !lower_block(builder, no_source))
        return 0;
    if (!finish_with_jump(builder, join, node_id)) return 0;

    builder->current_block = join;
    return 1;
}

static int lower_while(MirBuilder *builder, uint32_t node_id, ReaperHirNode *node) {
    uint32_t header = add_block(builder, node_id);
    uint32_t body = add_block(builder, node_id);
    uint32_t exit = add_block(builder, node_id);
    if (header == REAPER_MIR_NO_BLOCK || body == REAPER_MIR_NO_BLOCK ||
        exit == REAPER_MIR_NO_BLOCK) return 0;

    if (!append_jump(builder, header, node_id)) return 0;
    builder->current_block = header;
    uint32_t condition = lower_expression(builder, node->left);
    if (condition == REAPER_MIR_NO_VALUE ||
        !append_branch(builder, condition, body, exit, node_id)) return 0;

    builder->current_block = body;
    if (!lower_block(builder, node->right) ||
        !finish_with_jump(builder, header, node_id)) return 0;

    builder->current_block = exit;
    return 1;
}

static int lower_each(MirBuilder *builder, uint32_t node_id, ReaperHirNode *node) {
    uint32_t iterable = lower_expression(builder, node->left);
    if (iterable == REAPER_MIR_NO_VALUE) return 0;
    uint32_t iterator = emit_instruction(
        builder, REAPER_MIR_ITER_INIT, REAPER_HIR_TYPE_UNKNOWN,
        iterable, REAPER_MIR_NO_VALUE, node->symbol_id, node_id, "iter"
    );
    if (iterator == REAPER_MIR_NO_VALUE) return 0;

    uint32_t header = add_block(builder, node_id);
    uint32_t body = add_block(builder, node_id);
    uint32_t exit = add_block(builder, node_id);
    if (header == REAPER_MIR_NO_BLOCK || body == REAPER_MIR_NO_BLOCK ||
        exit == REAPER_MIR_NO_BLOCK) return 0;

    if (!append_jump(builder, header, node_id)) return 0;
    builder->current_block = header;
    uint32_t available = emit_instruction(
        builder, REAPER_MIR_ITER_NEXT, REAPER_HIR_TYPE_BOOL,
        iterator, REAPER_MIR_NO_VALUE, node->symbol_id, node_id, "next"
    );
    if (available == REAPER_MIR_NO_VALUE ||
        !append_branch(builder, available, body, exit, node_id)) return 0;

    builder->current_block = body;
    uint32_t item = emit_instruction(
        builder, REAPER_MIR_ITER_CURRENT, REAPER_HIR_TYPE_UNKNOWN,
        iterator, REAPER_MIR_NO_VALUE, node->symbol_id, node_id, "current"
    );
    if (item == REAPER_MIR_NO_VALUE ||
        !emit_void_instruction(builder, REAPER_MIR_STORE_LOCAL,
            item, node->symbol_id, node_id) ||
        !lower_block(builder, node->right) ||
        !finish_with_jump(builder, header, node_id)) return 0;

    builder->current_block = exit;
    return 1;
}

static int lower_statement(MirBuilder *builder, uint32_t node_id) {
    ReaperHirNode *node = hir_node(builder, node_id);
    if (node == NULL) return fail(builder, node_id, "MIR statement references a missing HIR node");

    uint32_t value;
    switch (node->kind) {
    case REAPER_AST_DECLARE_IMMUTABLE:
    case REAPER_AST_DECLARE_MUTABLE:
    case REAPER_AST_CHANGE:
        value = lower_expression(builder, node->left);
        if (value == REAPER_MIR_NO_VALUE) return 0;
        return emit_void_instruction(
            builder, REAPER_MIR_STORE_LOCAL, value, node->symbol_id, node_id
        );

    case REAPER_AST_EMIT:
        value = lower_expression(builder, node->left);
        if (value == REAPER_MIR_NO_VALUE) return 0;
        return emit_void_instruction(builder, REAPER_MIR_EMIT, value,
            REAPER_HIR_NO_SYMBOL, node_id);

    case REAPER_AST_YIELD:
        value = REAPER_MIR_NO_VALUE;
        if (node->left != REAPER_MIR_NO_VALUE) {
            value = lower_expression(builder, node->left);
            if (value == REAPER_MIR_NO_VALUE) return 0;
        }
        return append_return(builder, value, node_id);

    case REAPER_AST_EXPRESSION_STATEMENT:
        value = lower_expression(builder, node->left);
        if (value == REAPER_MIR_NO_VALUE) return 0;
        return emit_void_instruction(builder, REAPER_MIR_DROP, value,
            REAPER_HIR_NO_SYMBOL, node_id);

    case REAPER_AST_WHEN:
        return lower_when(builder, node_id, node);

    case REAPER_AST_WHILE:
        return lower_while(builder, node_id, node);

    case REAPER_AST_EACH:
        return lower_each(builder, node_id, node);

    case REAPER_AST_FUNCTION:
        return 1;

    case REAPER_AST_BLOCK:
        return lower_block(builder, node_id);

    default:
        return fail(builder, node_id, "unsupported HIR statement in MIR lowering");
    }
}

static int lower_sequence(MirBuilder *builder, uint32_t sequence_id) {
    uint32_t current = sequence_id;
    size_t count = 0U;
    while (current != REAPER_MIR_NO_VALUE) {
        ReaperHirNode *sequence = hir_node(builder, current);
        if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE ||
            ++count > builder->hir->node_count)
            return fail(builder, current, "malformed HIR sequence in MIR lowering");

        ReaperMirBlock *block = block_at(builder->module, builder->current_block);
        if (block == NULL) return fail(builder, current, "MIR current block is invalid");
        if (block->terminator != REAPER_MIR_TERM_NONE) break;

        if (!lower_statement(builder, sequence->left)) return 0;
        current = sequence->right;
    }
    return 1;
}

static int start_function(
    MirBuilder *builder,
    const char *name,
    uint32_t symbol_id,
    uint32_t source_node,
    uint32_t parameter_offset,
    uint32_t parameter_count,
    uint32_t *function_id
) {
    ReaperMirModule *module = builder->module;
    if (module->function_count >= UINT32_MAX ||
        !grow_array((void **)&module->functions, &module->function_capacity,
                    module->function_count, sizeof *module->functions, 4U)) {
        return fail(builder, source_node, "unable to allocate MIR function");
    }

    char *copy = copy_text(name);
    if (copy == NULL) return fail(builder, source_node, "unable to copy MIR function name");

    uint32_t id = (uint32_t)module->function_count;
    module->functions[module->function_count++] = (ReaperMirFunction) {
        id, symbol_id, source_node, REAPER_MIR_NO_BLOCK,
        (uint32_t)module->block_count, 0U,
        parameter_offset, parameter_count, copy
    };
    builder->current_function = id;
    builder->next_value = 0U;
    uint32_t entry = add_block(builder, source_node);
    if (entry == REAPER_MIR_NO_BLOCK) return 0;
    module->functions[id].entry_block = entry;
    builder->current_block = entry;
    *function_id = id;
    return 1;
}

static int append_implicit_return(MirBuilder *builder, size_t source_node) {
    ReaperMirBlock *block = block_at(builder->module, builder->current_block);
    if (block == NULL) return fail(builder, source_node, "missing MIR function exit block");
    if (block->terminator == REAPER_MIR_TERM_NONE)
        return append_return(builder, REAPER_MIR_NO_VALUE, source_node);
    return 1;
}

int reaper_mir_build(
    const ReaperHirModule *hir,
    ReaperMirModule *output,
    ReaperMirError *error
) {
    if (output != NULL) memset(output, 0, sizeof *output);
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }
    if (hir == NULL || output == NULL || hir->nodes == NULL ||
        hir->node_count == 0U) {
        if (error != NULL)
            (void)snprintf(error->message, sizeof error->message,
                "a checked HIR program and MIR output are required");
        return 0;
    }

    MirBuilder builder;
    memset(&builder, 0, sizeof builder);
    builder.hir = hir;
    builder.module = output;
    builder.error = error;

    uint32_t program_id = REAPER_MIR_NO_VALUE;
    for (size_t i = 0U; i < hir->node_count; ++i) {
        if (hir->nodes[i].kind == REAPER_AST_PROGRAM) {
            program_id = (uint32_t)i;
            break;
        }
    }
    ReaperHirNode *root = hir_node(&builder, program_id);
    if (root == NULL || root->kind != REAPER_AST_PROGRAM) {
        (void)fail(&builder, 0U, "HIR has no complete program root");
        reaper_mir_free(output);
        return 0;
    }

    uint32_t main_function = 0U;
    if (!start_function(
            &builder, "duck_main", REAPER_HIR_NO_SYMBOL, program_id,
            0U, 0U, &main_function)) {
        reaper_mir_free(output);
        return 0;
    }
    if (!lower_sequence(&builder, root->left) ||
        !append_implicit_return(&builder, program_id)) {
        reaper_mir_free(output);
        return 0;
    }

    for (size_t i = 0U; i < hir->node_count; ++i) {
        ReaperHirNode *function = &hir->nodes[i];
        if (function->kind != REAPER_AST_FUNCTION) continue;

        size_t parameter_count = 0U;
        uint32_t parameter = function->left;
        size_t guard = 0U;
        while (parameter != REAPER_MIR_NO_VALUE) {
            ReaperHirNode *sequence = hir_node(&builder, parameter);
            if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE ||
                ++guard > hir->node_count) {
                (void)fail(&builder, i, "malformed MIR function parameter sequence");
                reaper_mir_free(output);
                return 0;
            }
            ++parameter_count;
            parameter = sequence->right;
        }

        if (parameter_count > UINT32_MAX ||
            output->parameter_count > UINT32_MAX - parameter_count) {
            (void)fail(&builder, i, "MIR parameter table index limit exceeded");
            reaper_mir_free(output);
            return 0;
        }

        uint32_t parameter_offset = (uint32_t)output->parameter_count;
        parameter = function->left;
        while (parameter != REAPER_MIR_NO_VALUE) {
            ReaperHirNode *sequence = hir_node(&builder, parameter);
            ReaperHirNode *parameter_node = hir_node(&builder, sequence->left);
            if (parameter_node == NULL ||
                !grow_array((void **)&output->parameters,
                    &output->parameter_capacity, output->parameter_count,
                    sizeof *output->parameters, 8U)) {
                (void)fail(&builder, i, "unable to allocate MIR parameter table");
                reaper_mir_free(output);
                return 0;
            }
            output->parameters[output->parameter_count++] = parameter_node->symbol_id;
            parameter = sequence->right;
        }

        uint32_t function_id = 0U;
        if (!start_function(
                &builder, function->text, function->symbol_id, (uint32_t)i,
                parameter_offset, (uint32_t)parameter_count, &function_id) ||
            !lower_block(&builder, function->right) ||
            !append_implicit_return(&builder, i)) {
            reaper_mir_free(output);
            return 0;
        }
    }

    if (!reaper_mir_verify(output, error)) {
        reaper_mir_free(output);
        return 0;
    }
    return 1;
}

static int verify_fail(
    ReaperMirError *error,
    size_t index,
    const char *message
) {
    if (error != NULL && error->message[0] == '\0') {
        error->node_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

int reaper_mir_verify(const ReaperMirModule *module, ReaperMirError *error) {
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }
    if (module == NULL || module->functions == NULL || module->blocks == NULL ||
        (module->instruction_count != 0U &&
         (module->instructions == NULL || module->instruction_order == NULL)) ||
        (module->operand_count != 0U && module->operands == NULL) ||
        (module->parameter_count != 0U && module->parameters == NULL)) {
        return verify_fail(error, 0U, "MIR module storage is incomplete");
    }
    if (module->function_count == 0U || module->block_count == 0U) {
        return verify_fail(error, 0U, "MIR requires at least one function and block");
    }

    for (size_t i = 0U; i < module->function_count; ++i) {
        const ReaperMirFunction *function = &module->functions[i];
        if (function->id != i || function->name == NULL ||
            function->entry_block >= module->block_count ||
            function->block_count == 0U ||
            (size_t)function->first_block + function->block_count > module->block_count ||
            function->entry_block != function->first_block ||
            (size_t)function->parameter_offset + function->parameter_count > module->parameter_count) {
            return verify_fail(error, i, "MIR function layout or entry block is invalid");
        }
        for (size_t block_id = function->first_block;
             block_id < (size_t)function->first_block + function->block_count;
             ++block_id) {
            if (module->blocks[block_id].function_id != function->id) {
                return verify_fail(error, block_id, "MIR function block range is not contiguous");
            }
        }
    }

    unsigned char *instruction_seen = NULL;
    if (module->instruction_count != 0U) {
        instruction_seen = calloc(module->instruction_count, sizeof *instruction_seen);
        if (instruction_seen == NULL) {
            return verify_fail(error, 0U, "unable to allocate MIR verifier workspace");
        }
    }

    for (size_t i = 0U; i < module->block_count; ++i) {
        const ReaperMirBlock *block = &module->blocks[i];
        if (block->id != i || block->function_id >= module->function_count ||
            block->terminator == REAPER_MIR_TERM_NONE) {
            return verify_fail(error, i, "MIR block identity or terminator is invalid");
        }
        if (block->instruction_count == 0U) {
            if (block->first_instruction != UINT32_MAX) {
                return verify_fail(error, i, "empty MIR block has an instruction offset");
            }
        } else if (block->first_instruction == UINT32_MAX ||
                   (size_t)block->first_instruction + block->instruction_count >
                       module->instruction_order_count) {
            return verify_fail(error, i, "MIR block instruction-order range is outside the module");
        }

        const ReaperMirFunction *owner = &module->functions[block->function_id];
        size_t owner_end = (size_t)owner->first_block + owner->block_count;
        if (block->terminator == REAPER_MIR_TERM_JUMP) {
            if (block->target_true < owner->first_block || block->target_true >= owner_end ||
                block->target_false != REAPER_MIR_NO_BLOCK) {
                return verify_fail(error, i, "MIR jump target leaves its function");
            }
        } else if (block->terminator == REAPER_MIR_TERM_BRANCH) {
            if (block->terminator_value == REAPER_MIR_NO_VALUE ||
                block->target_true < owner->first_block || block->target_true >= owner_end ||
                block->target_false < owner->first_block || block->target_false >= owner_end) {
                return verify_fail(error, i, "MIR branch target or condition is invalid");
            }
        } else if (block->terminator == REAPER_MIR_TERM_RETURN) {
            if (block->target_true != REAPER_MIR_NO_BLOCK ||
                block->target_false != REAPER_MIR_NO_BLOCK) {
                return verify_fail(error, i, "MIR return block cannot carry branch targets");
            }
        } else {
            return verify_fail(error, i, "unknown MIR terminator");
        }

        for (size_t order_index = block->first_instruction;
             block->instruction_count != 0U &&
             order_index < (size_t)block->first_instruction + block->instruction_count;
             ++order_index) {
            uint32_t instruction_id = module->instruction_order[order_index];
            if (instruction_id >= module->instruction_count ||
                instruction_seen[instruction_id] != 0U) {
                free(instruction_seen);
                return verify_fail(error, order_index, "MIR instruction order contains an invalid or repeated index");
            }
            instruction_seen[instruction_id] = 1U;
            const ReaperMirInstruction *instruction =
                &module->instructions[instruction_id];
            if (instruction->text == NULL ||
                instruction->opcode < REAPER_MIR_CONST ||
                instruction->opcode > REAPER_MIR_ITER_CURRENT) {
                return verify_fail(error, instruction_id, "MIR instruction identity is invalid");
            }
            if ((size_t)instruction->operand_offset + instruction->operand_count >
                module->operand_count) {
                return verify_fail(error, instruction_id, "MIR operand vector is outside the module");
            }
            if ((instruction->opcode == REAPER_MIR_STORE_LOCAL ||
                 instruction->opcode == REAPER_MIR_LOAD_LOCAL) &&
                instruction->symbol_id == REAPER_HIR_NO_SYMBOL) {
                return verify_fail(error, instruction_id, "MIR local access has no resolved symbol");
            }
            if (instruction->opcode == REAPER_MIR_CALL ||
                instruction->opcode == REAPER_MIR_PIPE_CALL) {
                if (instruction->left == REAPER_MIR_NO_VALUE) {
                    return verify_fail(error, instruction_id, "MIR call has no callee value");
                }
            }
        }
    }

    for (size_t i = 0U; i < module->instruction_count; ++i) {
        if (instruction_seen[i] == 0U) {
            free(instruction_seen);
            return verify_fail(error, i, "MIR instruction is not owned by any basic block");
        }
    }
    free(instruction_seen);
    if (module->instruction_order_count != module->instruction_count) {
        return verify_fail(error, module->instruction_order_count,
            "MIR block instruction order does not cover the complete instruction array");
    }
    return 1;
}

void reaper_mir_free(ReaperMirModule *module) {
    if (module == NULL) return;
    for (size_t i = 0U; i < module->instruction_count; ++i)
        free(module->instructions[i].text);
    for (size_t i = 0U; i < module->function_count; ++i)
        free(module->functions[i].name);
    free(module->instructions);
    free(module->instruction_order);
    free(module->blocks);
    free(module->functions);
    free(module->operands);
    free(module->parameters);
    memset(module, 0, sizeof *module);
}

const char *reaper_mir_opcode_name(ReaperMirOpcode opcode) {
    switch (opcode) {
    case REAPER_MIR_CONST: return "const";
    case REAPER_MIR_FUNCTION_REF: return "function-ref";
    case REAPER_MIR_BUILTIN_REF: return "builtin-ref";
    case REAPER_MIR_LOAD_LOCAL: return "load-local";
    case REAPER_MIR_STORE_LOCAL: return "store-local";
    case REAPER_MIR_UNARY: return "unary";
    case REAPER_MIR_BINARY: return "binary";
    case REAPER_MIR_LIST: return "list";
    case REAPER_MIR_INDEX: return "index";
    case REAPER_MIR_CALL: return "call";
    case REAPER_MIR_PIPE_CALL: return "pipe-call";
    case REAPER_MIR_EMIT: return "emit";
    case REAPER_MIR_DROP: return "drop";
    case REAPER_MIR_ITER_INIT: return "iter-init";
    case REAPER_MIR_ITER_NEXT: return "iter-next";
    case REAPER_MIR_ITER_CURRENT: return "iter-current";
    default: return "invalid";
    }
}
