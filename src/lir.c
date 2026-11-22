#include "reaper/lir.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fail(ReaperLirError *error, size_t node, const char *message) {
    if (error != NULL && error->message[0] == '\0') {
        error->node_index = node;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static char *copy_text(const char *text) {
    size_t length = strlen(text);
    char *copy = malloc(length + 1U);
    if (copy != NULL) memcpy(copy, text, length + 1U);
    return copy;
}

static uint32_t find_local(
    const ReaperLirModule *module,
    uint32_t function_id,
    uint32_t symbol_id
) {
    if (function_id >= module->function_count) return REAPER_LIR_NO_SLOT;
    const ReaperLirFunction *function = &module->functions[function_id];
    size_t end = (size_t)function->local_offset + function->local_count;
    for (size_t i = function->local_offset; i < end; ++i) {
        const ReaperLirLocal *local = &module->locals[i];
        if (local->symbol_id == symbol_id) return local->slot_id;
    }
    return REAPER_LIR_NO_SLOT;
}

static int append_local(
    const ReaperHirModule *hir,
    ReaperLirModule *module,
    uint32_t function_id,
    uint32_t symbol_id,
    ReaperLirError *error
) {
    if (symbol_id >= hir->symbol_count) {
        return fail(error, symbol_id, "MIR references a symbol outside the HIR symbol table");
    }
    if (find_local(module, function_id, symbol_id) != REAPER_LIR_NO_SLOT) return 1;

    if (function_id >= module->function_count) {
        return fail(error, function_id, "local slot has no owning LIR function");
    }
    ReaperLirFunction *function = &module->functions[function_id];
    if ((size_t)function->local_offset + function->local_count != module->local_count ||
        function->local_count == UINT32_MAX ||
        module->local_count >= UINT32_MAX ||
        module->local_count > SIZE_MAX / sizeof *module->locals) {
        return fail(error, symbol_id, "LIR local slot index or storage limit exceeded");
    }

    ReaperLirLocal *locals = realloc(
        module->locals, (module->local_count + 1U) * sizeof *module->locals
    );
    if (locals == NULL) return fail(error, symbol_id, "unable to allocate LIR local slots");
    module->locals = locals;

    const ReaperHirSymbol *symbol = &hir->symbols[symbol_id];
    uint32_t slot = function->local_count;
    module->locals[module->local_count++] = (ReaperLirLocal) {
        function_id, symbol_id, slot, symbol->type, symbol->kind,
        symbol->mutable_value
    };
    ++function->local_count;
    function->stack_slot_count = function->local_count;
    return 1;
}

static uint32_t vreg_count_for_function(
    const ReaperMirModule *mir,
    uint32_t function_id
) {
    const ReaperMirFunction *function = &mir->functions[function_id];
    uint32_t count = 0U;
    size_t block_end = (size_t)function->first_block + function->block_count;
    for (size_t block_id = function->first_block; block_id < block_end; ++block_id) {
        const ReaperMirBlock *block = &mir->blocks[block_id];
        size_t order_end = (size_t)block->first_instruction + block->instruction_count;
        for (size_t order = block->first_instruction;
             block->instruction_count != 0U && order < order_end; ++order) {
            uint32_t instruction_id = mir->instruction_order[order];
            const ReaperMirInstruction *instruction = &mir->instructions[instruction_id];
            if (instruction->result_id != REAPER_MIR_NO_VALUE &&
                instruction->result_id >= count) {
                if (instruction->result_id == UINT32_MAX - 1U) return UINT32_MAX;
                count = instruction->result_id + 1U;
            }
        }
        if (block->terminator_value != REAPER_MIR_NO_VALUE &&
            block->terminator_value >= count) {
            if (block->terminator_value == UINT32_MAX - 1U) return UINT32_MAX;
            count = block->terminator_value + 1U;
        }
    }
    return count;
}

static int append_function_locals(
    const ReaperHirModule *hir,
    const ReaperMirModule *mir,
    ReaperLirModule *output,
    uint32_t function_id,
    ReaperLirError *error
) {
    const ReaperMirFunction *source = &mir->functions[function_id];
    ReaperLirFunction *target = &output->functions[function_id];
    target->local_offset = (uint32_t)output->local_count;

    if ((size_t)source->parameter_offset + source->parameter_count > mir->parameter_count) {
        return fail(error, function_id, "MIR function parameter range is invalid");
    }

    for (size_t i = 0U; i < source->parameter_count; ++i) {
        uint32_t symbol_id = mir->parameters[source->parameter_offset + i];
        if (!append_local(hir, output, function_id, symbol_id, error)) return 0;
        uint32_t slot = find_local(output, function_id, symbol_id);
        if (slot == REAPER_LIR_NO_SLOT) {
            return fail(error, symbol_id, "function parameter has no allocated LIR slot");
        }
        output->parameter_slots[output->parameter_count++] = slot;
    }

    size_t block_end = (size_t)source->first_block + source->block_count;
    for (size_t block_id = source->first_block; block_id < block_end; ++block_id) {
        const ReaperMirBlock *block = &mir->blocks[block_id];
        size_t order_end = (size_t)block->first_instruction + block->instruction_count;
        for (size_t order = block->first_instruction;
             block->instruction_count != 0U && order < order_end; ++order) {
            uint32_t instruction_id = mir->instruction_order[order];
            const ReaperMirInstruction *instruction = &mir->instructions[instruction_id];
            if (instruction->opcode != REAPER_MIR_LOAD_LOCAL &&
                instruction->opcode != REAPER_MIR_STORE_LOCAL) {
                if (instruction->opcode == REAPER_MIR_ITER_INIT ||
                    instruction->opcode == REAPER_MIR_ITER_NEXT ||
                    instruction->opcode == REAPER_MIR_ITER_CURRENT) {
                    if (instruction->symbol_id != REAPER_HIR_NO_SYMBOL &&
                        !append_local(hir, output, function_id,
                            instruction->symbol_id, error)) return 0;
                }
                continue;
            }
            if (!append_local(
                    hir, output, function_id, instruction->symbol_id, error)) return 0;
        }
    }
    return 1;
}

static ReaperLirOpcode map_opcode(ReaperMirOpcode opcode) {
    switch (opcode) {
    case REAPER_MIR_CONST: return REAPER_LIR_CONST;
    case REAPER_MIR_FUNCTION_REF: return REAPER_LIR_FUNCTION_REF;
    case REAPER_MIR_BUILTIN_REF: return REAPER_LIR_BUILTIN_REF;
    case REAPER_MIR_LOAD_LOCAL: return REAPER_LIR_LOAD_SLOT;
    case REAPER_MIR_STORE_LOCAL: return REAPER_LIR_STORE_SLOT;
    case REAPER_MIR_UNARY: return REAPER_LIR_UNARY;
    case REAPER_MIR_BINARY: return REAPER_LIR_BINARY;
    case REAPER_MIR_LIST: return REAPER_LIR_LIST;
    case REAPER_MIR_INDEX: return REAPER_LIR_INDEX;
    case REAPER_MIR_CALL: return REAPER_LIR_CALL;
    case REAPER_MIR_PIPE_CALL: return REAPER_LIR_PIPE_CALL;
    case REAPER_MIR_EMIT: return REAPER_LIR_EMIT;
    case REAPER_MIR_DROP: return REAPER_LIR_DROP;
    case REAPER_MIR_ITER_INIT: return REAPER_LIR_ITER_INIT;
    case REAPER_MIR_ITER_NEXT: return REAPER_LIR_ITER_NEXT;
    case REAPER_MIR_ITER_CURRENT: return REAPER_LIR_ITER_CURRENT;
    default: return 0;
    }
}

void reaper_lir_free(ReaperLirModule *module) {
    if (module == NULL) return;
    for (size_t i = 0U; i < module->instruction_count; ++i)
        free(module->instructions[i].text);
    for (size_t i = 0U; i < module->function_count; ++i)
        free(module->functions[i].name);
    free(module->instructions);
    free(module->blocks);
    free(module->functions);
    free(module->instruction_order);
    free(module->operands);
    free(module->parameter_slots);
    free(module->locals);
    memset(module, 0, sizeof *module);
}

int reaper_lir_build(
    const ReaperHirModule *hir,
    const ReaperMirModule *mir,
    ReaperLirModule *output,
    ReaperLirError *error
) {
    if (output != NULL) memset(output, 0, sizeof *output);
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }
    if (hir == NULL || mir == NULL || output == NULL ||
        hir->nodes == NULL || mir->functions == NULL || mir->blocks == NULL ||
        mir->function_count == 0U || mir->block_count == 0U) {
        if (error != NULL)
            (void)snprintf(error->message, sizeof error->message,
                "checked HIR, MIR and LIR output are required");
        return 0;
    }

    ReaperMirError mir_error;
    if (!reaper_mir_verify(mir, &mir_error)) {
        return fail(error, mir_error.node_index, mir_error.message);
    }

    output->function_count = mir->function_count;
    output->block_count = mir->block_count;
    output->instruction_count = mir->instruction_count;
    output->instruction_order_count = mir->instruction_order_count;
    output->operand_count = mir->operand_count;
    output->parameter_count = 0U;

    output->functions = calloc(output->function_count, sizeof *output->functions);
    output->blocks = calloc(output->block_count, sizeof *output->blocks);
    output->instructions = output->instruction_count == 0U ? NULL :
        calloc(output->instruction_count, sizeof *output->instructions);
    output->instruction_order = output->instruction_order_count == 0U ? NULL :
        malloc(output->instruction_order_count * sizeof *output->instruction_order);
    output->operands = output->operand_count == 0U ? NULL :
        malloc(output->operand_count * sizeof *output->operands);
    output->parameter_slots = mir->parameter_count == 0U ? NULL :
        malloc(mir->parameter_count * sizeof *output->parameter_slots);
    if (output->functions == NULL || output->blocks == NULL ||
        (output->instruction_count != 0U && output->instructions == NULL) ||
        (output->instruction_order_count != 0U && output->instruction_order == NULL) ||
        (output->operand_count != 0U && output->operands == NULL) ||
        (mir->parameter_count != 0U && output->parameter_slots == NULL)) {
        (void)fail(error, 0U, "unable to allocate LIR module storage");
        reaper_lir_free(output);
        return 0;
    }

    if (output->instruction_order_count != 0U) {
        memcpy(output->instruction_order, mir->instruction_order,
            output->instruction_order_count * sizeof *output->instruction_order);
    }
    if (output->operand_count != 0U) {
        memcpy(output->operands, mir->operands,
            output->operand_count * sizeof *output->operands);
    }

    for (size_t i = 0U; i < output->function_count; ++i) {
        const ReaperMirFunction *source = &mir->functions[i];
        ReaperLirFunction *target = &output->functions[i];
        target->id = source->id;
        target->symbol_id = source->symbol_id;
        target->source_hir_node = source->source_hir_node;
        target->entry_block = source->entry_block;
        target->first_block = source->first_block;
        target->block_count = source->block_count;
        target->parameter_offset = source->parameter_offset;
        target->parameter_count = source->parameter_count;
        target->name = copy_text(source->name != NULL ? source->name : "");
        target->vreg_count = vreg_count_for_function(mir, (uint32_t)i);
        if (target->name == NULL || target->vreg_count == UINT32_MAX ||
            (size_t)target->parameter_offset + target->parameter_count >
                output->parameter_count) {
            (void)fail(error, i, "invalid MIR function metadata or virtual-register range");
            reaper_lir_free(output);
            return 0;
        }
    }

    for (size_t i = 0U; i < output->block_count; ++i) {
        const ReaperMirBlock *source = &mir->blocks[i];
        output->blocks[i] = (ReaperLirBlock) {
            source->id, source->function_id, source->first_instruction,
            source->instruction_count, (ReaperLirTerminator)source->terminator,
            source->terminator_value, source->target_true, source->target_false
        };
    }

    for (size_t function_id = 0U; function_id < output->function_count; ++function_id) {
        if (!append_function_locals(hir, mir, output, (uint32_t)function_id, error)) {
            reaper_lir_free(output);
            return 0;
        }
    }
    if (output->parameter_count != mir->parameter_count) {
        (void)fail(error, output->parameter_count, "LIR parameter-slot table is incomplete");
        reaper_lir_free(output);
        return 0;
    }

    for (size_t i = 0U; i < output->instruction_count; ++i) {
        const ReaperMirInstruction *source = &mir->instructions[i];
        ReaperLirInstruction *target = &output->instructions[i];
        target->opcode = map_opcode(source->opcode);
        target->type = source->type;
        target->destination = source->result_id;
        target->left = source->left;
        target->right = source->right;
        target->slot_id = REAPER_LIR_NO_SLOT;
        target->symbol_id = source->symbol_id;
        target->source_hir_node = source->source_hir_node;
        target->operand_offset = source->operand_offset;
        target->operand_count = source->operand_count;
        target->text = copy_text(source->text != NULL ? source->text : "");
        if (target->opcode == 0 || target->text == NULL) {
            (void)fail(error, i, "MIR instruction has no LIR opcode or text");
            reaper_lir_free(output);
            return 0;
        }

        if (source->opcode == REAPER_MIR_LOAD_LOCAL ||
            source->opcode == REAPER_MIR_STORE_LOCAL ||
            source->opcode == REAPER_MIR_ITER_INIT ||
            source->opcode == REAPER_MIR_ITER_NEXT ||
            source->opcode == REAPER_MIR_ITER_CURRENT) {
            if (source->symbol_id == REAPER_HIR_NO_SYMBOL) {
                if (source->opcode == REAPER_MIR_LOAD_LOCAL ||
                    source->opcode == REAPER_MIR_STORE_LOCAL) {
                    (void)fail(error, i, "local MIR instruction has no symbol");
                    reaper_lir_free(output);
                    return 0;
                }
            } else {
                uint32_t owner_function = REAPER_MIR_NO_VALUE;
                for (size_t block_id = 0U; block_id < mir->block_count; ++block_id) {
                    const ReaperMirBlock *block = &mir->blocks[block_id];
                    size_t block_end = (size_t)block->first_instruction + block->instruction_count;
                    for (size_t order = block->first_instruction;
                         block->instruction_count != 0U && order < block_end; ++order) {
                        if (mir->instruction_order[order] == i) {
                            owner_function = block->function_id;
                            break;
                        }
                    }
                    if (owner_function != REAPER_MIR_NO_VALUE) break;
                }
                if (owner_function == REAPER_MIR_NO_VALUE) {
                    (void)fail(error, i, "MIR local instruction has no owning function");
                    reaper_lir_free(output);
                    return 0;
                }
                target->slot_id = find_local(output, owner_function, source->symbol_id);
                if (target->slot_id == REAPER_LIR_NO_SLOT) {
                    (void)fail(error, i, "MIR local has no assigned LIR stack slot");
                    reaper_lir_free(output);
                    return 0;
                }
            }
        }
    }

    if (!reaper_lir_verify(output, error)) {
        reaper_lir_free(output);
        return 0;
    }
    return 1;
}

static int verify_fail(
    ReaperLirError *error,
    size_t index,
    const char *message
) {
    return fail(error, index, message);
}

int reaper_lir_verify(const ReaperLirModule *module, ReaperLirError *error) {
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }
    if (module == NULL || module->functions == NULL || module->blocks == NULL ||
        (module->instruction_count != 0U &&
         (module->instructions == NULL || module->instruction_order == NULL)) ||
        (module->operand_count != 0U && module->operands == NULL) ||
        (module->parameter_count != 0U && module->parameter_slots == NULL) ||
        (module->local_count != 0U && module->locals == NULL)) {
        return verify_fail(error, 0U, "LIR module storage is incomplete");
    }

    for (size_t i = 0U; i < module->function_count; ++i) {
        const ReaperLirFunction *function = &module->functions[i];
        if (function->id != i || function->name == NULL ||
            function->entry_block >= module->block_count ||
            function->block_count == 0U ||
            (size_t)function->first_block + function->block_count > module->block_count ||
            function->entry_block != function->first_block ||
            (size_t)function->local_offset + function->local_count > module->local_count ||
            function->stack_slot_count != function->local_count ||
            (size_t)function->parameter_offset + function->parameter_count >
                module->parameter_count) {
            return verify_fail(error, i, "LIR function metadata or stack layout is invalid");
        }

        for (size_t j = 0U; j < function->local_count; ++j) {
            const ReaperLirLocal *local = &module->locals[function->local_offset + j];
            if (local->function_id != function->id ||
                local->slot_id != j || local->symbol_id >= UINT32_MAX) {
                return verify_fail(error, function->local_offset + j, "LIR local-slot identity is invalid");
            }
        }
        for (size_t j = 0U; j < function->parameter_count; ++j) {
            uint32_t slot = module->parameter_slots[function->parameter_offset + j];
            if (slot >= function->stack_slot_count) {
                return verify_fail(error, function->parameter_offset + j,
                    "LIR parameter does not map to a local stack slot");
            }
        }
    }

    for (size_t i = 0U; i < module->block_count; ++i) {
        const ReaperLirBlock *block = &module->blocks[i];
        if (block->id != i || block->function_id >= module->function_count ||
            block->terminator == REAPER_LIR_TERM_NONE) {
            return verify_fail(error, i, "LIR block identity or terminator is invalid");
        }
        const ReaperLirFunction *owner = &module->functions[block->function_id];
        size_t owner_end = (size_t)owner->first_block + owner->block_count;
        if (block->terminator == REAPER_LIR_TERM_JUMP) {
            if (block->target_true < owner->first_block || block->target_true >= owner_end ||
                block->target_false != REAPER_LIR_NO_BLOCK ||
                block->terminator_value != REAPER_LIR_NO_VALUE) {
                return verify_fail(error, i, "LIR jump target leaves its function");
            }
        } else if (block->terminator == REAPER_LIR_TERM_BRANCH) {
            if (block->terminator_value >= owner->vreg_count ||
                block->target_true < owner->first_block || block->target_true >= owner_end ||
                block->target_false < owner->first_block || block->target_false >= owner_end) {
                return verify_fail(error, i, "LIR branch target or condition register is invalid");
            }
        } else if (block->terminator == REAPER_LIR_TERM_RETURN) {
            if (block->target_true != REAPER_LIR_NO_BLOCK ||
                block->target_false != REAPER_LIR_NO_BLOCK ||
                (block->terminator_value != REAPER_LIR_NO_VALUE &&
                 block->terminator_value >= owner->vreg_count)) {
                return verify_fail(error, i, "LIR return terminator is invalid");
            }
        } else {
            return verify_fail(error, i, "unknown LIR terminator");
        }
    }

    unsigned char *seen = NULL;
    if (module->instruction_count != 0U) {
        seen = calloc(module->instruction_count, sizeof *seen);
        if (seen == NULL) return verify_fail(error, 0U, "unable to allocate LIR verifier workspace");
    }

    int success = 0;
    for (size_t i = 0U; i < module->block_count; ++i) {
        const ReaperLirBlock *block = &module->blocks[i];
        if (block->instruction_count == 0U) {
            if (block->first_instruction != UINT32_MAX) {
                (void)verify_fail(error, i, "empty LIR block has an instruction offset");
                goto cleanup;
            }
            continue;
        }
        size_t end = (size_t)block->first_instruction + block->instruction_count;
        if (block->first_instruction == UINT32_MAX ||
            end > module->instruction_order_count) {
            (void)verify_fail(error, i, "LIR block instruction range is invalid");
            goto cleanup;
        }
        const ReaperLirFunction *owner = &module->functions[block->function_id];
        for (size_t order = block->first_instruction; order < end; ++order) {
            uint32_t instruction_id = module->instruction_order[order];
            if (instruction_id >= module->instruction_count || seen[instruction_id] != 0U) {
                (void)verify_fail(error, order, "LIR instruction order contains an invalid or repeated index");
                goto cleanup;
            }
            seen[instruction_id] = 1U;
            const ReaperLirInstruction *instruction = &module->instructions[instruction_id];
            if (instruction->text == NULL || instruction->opcode < REAPER_LIR_CONST ||
                instruction->opcode > REAPER_LIR_ITER_CURRENT ||
                (size_t)instruction->operand_offset + instruction->operand_count >
                    module->operand_count) {
                (void)verify_fail(error, instruction_id, "LIR instruction layout is invalid");
                goto cleanup;
            }
            int has_result =
                instruction->opcode != REAPER_LIR_STORE_SLOT &&
                instruction->opcode != REAPER_LIR_EMIT &&
                instruction->opcode != REAPER_LIR_DROP;
            if (has_result != (instruction->destination != REAPER_LIR_NO_VALUE) ||
                (has_result && instruction->destination >= owner->vreg_count)) {
                (void)verify_fail(error, instruction_id, "LIR destination register is invalid");
                goto cleanup;
            }
            if ((instruction->opcode == REAPER_LIR_LOAD_SLOT ||
                 instruction->opcode == REAPER_LIR_STORE_SLOT ||
                 instruction->opcode == REAPER_LIR_ITER_INIT ||
                 instruction->opcode == REAPER_LIR_ITER_NEXT ||
                 instruction->opcode == REAPER_LIR_ITER_CURRENT) &&
                instruction->symbol_id != REAPER_HIR_NO_SYMBOL &&
                instruction->slot_id >= owner->stack_slot_count) {
                (void)verify_fail(error, instruction_id, "LIR local stack slot is invalid");
                goto cleanup;
            }
            if ((instruction->opcode == REAPER_LIR_LOAD_SLOT ||
                 instruction->opcode == REAPER_LIR_STORE_SLOT) &&
                instruction->slot_id == REAPER_LIR_NO_SLOT) {
                (void)verify_fail(error, instruction_id, "LIR local access has no stack slot");
                goto cleanup;
            }
            if ((instruction->opcode == REAPER_LIR_UNARY ||
                 instruction->opcode == REAPER_LIR_STORE_SLOT ||
                 instruction->opcode == REAPER_LIR_EMIT ||
                 instruction->opcode == REAPER_LIR_DROP ||
                 instruction->opcode == REAPER_LIR_ITER_INIT ||
                 instruction->opcode == REAPER_LIR_ITER_NEXT ||
                 instruction->opcode == REAPER_LIR_ITER_CURRENT) &&
                instruction->left >= owner->vreg_count) {
                (void)verify_fail(error, instruction_id, "LIR left virtual register is invalid");
                goto cleanup;
            }
            if ((instruction->opcode == REAPER_LIR_BINARY ||
                 instruction->opcode == REAPER_LIR_INDEX) &&
                instruction->right >= owner->vreg_count) {
                (void)verify_fail(error, instruction_id, "LIR right virtual register is invalid");
                goto cleanup;
            }
            if ((instruction->opcode == REAPER_LIR_CALL ||
                 instruction->opcode == REAPER_LIR_PIPE_CALL) &&
                (instruction->left >= owner->vreg_count ||
                 instruction->right != REAPER_LIR_NO_VALUE)) {
                (void)verify_fail(error, instruction_id, "LIR call target is invalid");
                goto cleanup;
            }
            for (size_t arg = instruction->operand_offset;
                 arg < (size_t)instruction->operand_offset + instruction->operand_count; ++arg) {
                if (module->operands[arg] >= owner->vreg_count) {
                    (void)verify_fail(error, instruction_id, "LIR call operand register is invalid");
                    goto cleanup;
                }
            }
        }
    }

    for (size_t i = 0U; i < module->instruction_count; ++i) {
        if (seen[i] == 0U) {
            (void)verify_fail(error, i, "LIR instruction is not owned by a basic block");
            goto cleanup;
        }
    }
    if (module->instruction_order_count != module->instruction_count) {
        (void)verify_fail(error, module->instruction_order_count, "LIR instruction order is incomplete");
        goto cleanup;
    }

    success = 1;

cleanup:
    free(seen);
    return success;
}

const char *reaper_lir_opcode_name(ReaperLirOpcode opcode) {
    switch (opcode) {
    case REAPER_LIR_CONST: return "const";
    case REAPER_LIR_FUNCTION_REF: return "function-ref";
    case REAPER_LIR_BUILTIN_REF: return "builtin-ref";
    case REAPER_LIR_LOAD_SLOT: return "load-slot";
    case REAPER_LIR_STORE_SLOT: return "store-slot";
    case REAPER_LIR_UNARY: return "unary";
    case REAPER_LIR_BINARY: return "binary";
    case REAPER_LIR_LIST: return "list";
    case REAPER_LIR_INDEX: return "index";
    case REAPER_LIR_CALL: return "call";
    case REAPER_LIR_PIPE_CALL: return "pipe-call";
    case REAPER_LIR_EMIT: return "emit";
    case REAPER_LIR_DROP: return "drop";
    case REAPER_LIR_ITER_INIT: return "iter-init";
    case REAPER_LIR_ITER_NEXT: return "iter-next";
    case REAPER_LIR_ITER_CURRENT: return "iter-current";
    default: return "invalid";
    }
}
