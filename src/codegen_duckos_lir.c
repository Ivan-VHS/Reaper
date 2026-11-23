#include "reaper/codegen_duckos_lir.h"
#include "reaper/duckos_abi.h"

#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct DuckLirLayout {
    size_t frame_offset;
    size_t result_offset;
    size_t frame_size;
    size_t max_call_arguments;
} DuckLirLayout;

static int codegen_fail(
    ReaperCodegenError *error,
    size_t node_index,
    const char *message
) {
    if (error != NULL) {
        error->node_index = node_index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static size_t align_up(size_t value, size_t alignment) {
    size_t remainder = value % alignment;
    if (remainder == 0U) return value;
    return value + (alignment - remainder);
}

static size_t vreg_offset(uint32_t vreg) {
    return 24U + (size_t)vreg * 8U;
}

static size_t local_offset(
    const ReaperLirFunction *function,
    uint32_t slot
) {
    return 24U + (size_t)function->vreg_count * 8U + (size_t)slot * 8U;
}

static const ReaperLirFunction *function_by_symbol(
    const ReaperLirModule *module,
    uint32_t symbol_id
) {
    for (size_t i = 0U; i < module->function_count; ++i) {
        if (module->functions[i].symbol_id == symbol_id)
            return &module->functions[i];
    }
    return NULL;
}

static const ReaperLirInstruction *instruction_for_vreg(
    const ReaperLirModule *module,
    uint32_t function_id,
    uint32_t vreg
) {
    const ReaperLirFunction *function = &module->functions[function_id];
    size_t block_end = (size_t)function->first_block + function->block_count;
    for (size_t block_id = function->first_block; block_id < block_end; ++block_id) {
        const ReaperLirBlock *block = &module->blocks[block_id];
        size_t order_end = (size_t)block->first_instruction + block->instruction_count;
        for (size_t order = block->first_instruction;
             block->instruction_count != 0U && order < order_end;
             ++order) {
            uint32_t id = module->instruction_order[order];
            const ReaperLirInstruction *instruction = &module->instructions[id];
            if (instruction->destination == vreg)
                return instruction;
        }
    }
    return NULL;
}

static int value_is_i64(
    const ReaperLirModule *module,
    uint32_t function_id,
    uint32_t vreg
) {
    const ReaperLirInstruction *definition =
        instruction_for_vreg(module, function_id, vreg);
    return definition != NULL &&
        (definition->type == REAPER_HIR_TYPE_I64 ||
         definition->type == REAPER_HIR_TYPE_UNKNOWN);
}

static int function_returns_i64(
    const ReaperLirModule *module,
    const ReaperLirFunction *function
) {
    int saw_return = 0;
    size_t end = (size_t)function->first_block + function->block_count;
    for (size_t block_id = function->first_block; block_id < end; ++block_id) {
        const ReaperLirBlock *block = &module->blocks[block_id];
        if (block->terminator != REAPER_LIR_TERM_RETURN) continue;
        saw_return = 1;
        if (block->terminator_value == REAPER_LIR_NO_VALUE ||
            !value_is_i64(module, function->id, block->terminator_value)) {
            return 0;
        }
    }
    return saw_return;
}

static int resolve_call_target(
    const ReaperLirModule *module,
    uint32_t caller_id,
    const ReaperLirInstruction *call,
    const ReaperLirFunction **target,
    ReaperCodegenError *error,
    size_t instruction_id
) {
    const ReaperLirInstruction *callee =
        instruction_for_vreg(module, caller_id, call->left);
    if (callee == NULL || callee->opcode != REAPER_LIR_FUNCTION_REF ||
        callee->symbol_id == REAPER_HIR_NO_SYMBOL) {
        return codegen_fail(
            error,
            instruction_id,
            "DABI64 scalar backend supports direct craft calls only"
        );
    }

    *target = function_by_symbol(module, callee->symbol_id);
    if (*target == NULL || (*target)->id == 0U) {
        return codegen_fail(
            error,
            instruction_id,
            "call target is not a compiled craft function"
        );
    }
    if (call->operand_count != (*target)->parameter_count) {
        return codegen_fail(
            error,
            instruction_id,
            "call argument count does not match the DABI64 callee signature"
        );
    }
    if (!function_returns_i64(module, *target)) {
        return codegen_fail(
            error,
            instruction_id,
            "scalar calls require every callee return path to produce i64"
        );
    }

    for (size_t i = 0U; i < call->operand_count; ++i) {
        uint32_t argument = module->operands[call->operand_offset + i];
        if (!value_is_i64(module, caller_id, argument)) {
            return codegen_fail(
                error,
                instruction_id,
                "DABI64 scalar calls accept i64 arguments only"
            );
        }
    }
    return 1;
}

static int parse_integer(const char *text, int64_t *value) {
    errno = 0;
    char *end = NULL;
    intmax_t parsed = strtoimax(text, &end, 10);
    if (errno == ERANGE || end == text || end == NULL || *end != '\0' ||
        parsed < INT64_MIN || parsed > INT64_MAX) return 0;
    *value = (int64_t)parsed;
    return 1;
}

static int validate_module(
    const ReaperLirModule *module,
    DuckLirLayout *layouts,
    ReaperCodegenError *error
) {
    ReaperLirError lir_error;
    if (!reaper_lir_verify(module, &lir_error)) {
        return codegen_fail(error, lir_error.node_index, lir_error.message);
    }
    if (module->function_count > REAPER_DUCK_LIR_MAX_FUNCTIONS ||
        module->block_count > REAPER_DUCK_LIR_MAX_BLOCKS ||
        module->function_count == 0U || module->functions[0].parameter_count != 0U) {
        return codegen_fail(error, 0U, "DABI64 scalar module exceeds its limits or has an invalid entry");
    }

    memset(layouts, 0, module->function_count * sizeof *layouts);

    for (size_t f = 0U; f < module->function_count; ++f) {
        const ReaperLirFunction *function = &module->functions[f];
        if (function->vreg_count > REAPER_DUCK_LIR_MAX_VREGS ||
            function->stack_slot_count > REAPER_DUCK_LIR_MAX_SLOTS ||
            function->parameter_count > REAPER_DUCK_LIR_MAX_CALL_ARGUMENTS) {
            return codegen_fail(error, f, "DABI64 function exceeds vreg, stack-slot or parameter limits");
        }
        if (function->stack_slot_count != function->local_count) {
            return codegen_fail(error, f, "DABI64 function has an inconsistent local-slot table");
        }

        const ReaperLirFunction *unused_target = NULL;
        (void)unused_target;

        size_t max_arguments = 0U;
        size_t block_end = (size_t)function->first_block + function->block_count;
        for (size_t block_id = function->first_block; block_id < block_end; ++block_id) {
            const ReaperLirBlock *block = &module->blocks[block_id];
            size_t order_end = (size_t)block->first_instruction + block->instruction_count;
            for (size_t order = block->first_instruction;
                 block->instruction_count != 0U && order < order_end;
                 ++order) {
                uint32_t instruction_id = module->instruction_order[order];
                const ReaperLirInstruction *instruction =
                    &module->instructions[instruction_id];
                switch (instruction->opcode) {
                case REAPER_LIR_CONST:
                    if (instruction->type == REAPER_HIR_TYPE_I64) {
                        int64_t ignored;
                        if (!parse_integer(instruction->text, &ignored)) {
                            return codegen_fail(error, instruction_id, "invalid i64 constant in DABI64 LIR");
                        }
                    } else if (instruction->type == REAPER_HIR_TYPE_BOOL) {
                        if (strcmp(instruction->text, "true") != 0 &&
                            strcmp(instruction->text, "false") != 0) {
                            return codegen_fail(error, instruction_id, "invalid boolean constant in DABI64 LIR");
                        }
                    } else {
                        return codegen_fail(error, instruction_id, "DABI64 scalar backend supports i64 and bool constants only");
                    }
                    break;

                case REAPER_LIR_FUNCTION_REF:
                    if (function_by_symbol(module, instruction->symbol_id) == NULL) {
                        return codegen_fail(error, instruction_id, "function reference has no compiled DABI64 function");
                    }
                    break;

                case REAPER_LIR_BUILTIN_REF:
                    return codegen_fail(error, instruction_id, "built-in runtime calls are not linked into this DABI64 backend yet");

                case REAPER_LIR_LOAD_SLOT:
                case REAPER_LIR_STORE_SLOT:
                    if (instruction->type != REAPER_HIR_TYPE_I64 &&
                        instruction->type != REAPER_HIR_TYPE_UNKNOWN) {
                        return codegen_fail(error, instruction_id, "DABI64 local slots currently carry i64 values only");
                    }
                    break;

                case REAPER_LIR_UNARY:
                    if (strcmp(instruction->text, "+") != 0 &&
                        strcmp(instruction->text, "-") != 0 &&
                        strcmp(instruction->text, "!") != 0 &&
                        strcmp(instruction->text, "not") != 0) {
                        return codegen_fail(error, instruction_id, "unary operator is not implemented by the DABI64 scalar backend");
                    }
                    break;

                case REAPER_LIR_BINARY:
                    if (strcmp(instruction->text, "+") != 0 &&
                        strcmp(instruction->text, "-") != 0 &&
                        strcmp(instruction->text, "*") != 0 &&
                        strcmp(instruction->text, "/") != 0 &&
                        strcmp(instruction->text, "//") != 0 &&
                        strcmp(instruction->text, "%") != 0 &&
                        strcmp(instruction->text, "==") != 0 &&
                        strcmp(instruction->text, "!=") != 0 &&
                        strcmp(instruction->text, "<") != 0 &&
                        strcmp(instruction->text, "<=") != 0 &&
                        strcmp(instruction->text, ">") != 0 &&
                        strcmp(instruction->text, ">=") != 0 &&
                        strcmp(instruction->text, "and") != 0 &&
                        strcmp(instruction->text, "or") != 0 &&
                        strcmp(instruction->text, "&&") != 0 &&
                        strcmp(instruction->text, "||") != 0) {
                        return codegen_fail(error, instruction_id, "binary operator is not implemented by the DABI64 scalar backend");
                    }
                    break;

                case REAPER_LIR_CALL:
                case REAPER_LIR_PIPE_CALL: {
                    const ReaperLirFunction *target = NULL;
                    if (!resolve_call_target(module, function->id,
                            instruction, &target, error, instruction_id)) return 0;
                    if (instruction->operand_count > max_arguments)
                        max_arguments = instruction->operand_count;
                    break;
                }

                case REAPER_LIR_DROP:
                    break;

                case REAPER_LIR_EMIT:
                    return codegen_fail(error, instruction_id, "emit requires the DuckOS I/O runtime, which is not linked yet");

                case REAPER_LIR_LIST:
                case REAPER_LIR_INDEX:
                case REAPER_LIR_ITER_INIT:
                case REAPER_LIR_ITER_NEXT:
                case REAPER_LIR_ITER_CURRENT:
                    return codegen_fail(error, instruction_id, "collections and each require the DuckOS collection runtime, which is not linked yet");

                default:
                    return codegen_fail(error, instruction_id, "unknown LIR opcode for DABI64 code generation");
                }
            }
        }

        layouts[f].max_call_arguments = max_arguments;
        size_t vregs_bytes = (size_t)function->vreg_count * 8U;
        size_t locals_bytes = (size_t)function->stack_slot_count * 8U;
        if (vregs_bytes > SIZE_MAX - 24U ||
            locals_bytes > SIZE_MAX - 24U - vregs_bytes) {
            return codegen_fail(error, f, "DABI64 stack layout size overflow");
        }
        size_t call_frame_offset = align_up(24U + vregs_bytes + locals_bytes, 16U);
        size_t call_frame_bytes = 48U + max_arguments * 16U;
        if (call_frame_bytes > SIZE_MAX - call_frame_offset) {
            return codegen_fail(error, f, "DABI64 call-frame workspace size overflow");
        }
        size_t result_offset = call_frame_offset + call_frame_bytes;
        if (result_offset > SIZE_MAX - 16U) {
            return codegen_fail(error, f, "DABI64 result workspace size overflow");
        }
        size_t data_size = result_offset + 16U;
        size_t frame_size = data_size +
            ((16U + 32U - (data_size % 32U)) % 32U);
        if (frame_size > INT32_MAX) {
            return codegen_fail(error, f, "DABI64 stack frame exceeds x86-64 displacement limits");
        }

        layouts[f].frame_offset = call_frame_offset;
        layouts[f].result_offset = result_offset;
        layouts[f].frame_size = frame_size;
    }

    for (size_t i = 0U; i < module->instruction_count; ++i) {
        const ReaperLirInstruction *instruction = &module->instructions[i];
        if (instruction->opcode != REAPER_LIR_CALL &&
            instruction->opcode != REAPER_LIR_PIPE_CALL) continue;
        for (size_t f = 0U; f < module->function_count; ++f) {
            const ReaperLirFunction *function = &module->functions[f];
            size_t end = (size_t)function->first_block + function->block_count;
            int belongs = 0;
            for (size_t b = function->first_block; b < end && !belongs; ++b) {
                const ReaperLirBlock *block = &module->blocks[b];
                size_t order_end = (size_t)block->first_instruction + block->instruction_count;
                for (size_t order = block->first_instruction;
                     block->instruction_count != 0U && order < order_end; ++order) {
                    if (module->instruction_order[order] == i) {
                        belongs = 1;
                        break;
                    }
                }
            }
            if (belongs) {
                const ReaperLirFunction *target = NULL;
                if (!resolve_call_target(module, function->id, instruction,
                        &target, error, i)) return 0;
                if (target->id == 0U) {
                    return codegen_fail(error, i, "the top-level duck_main entry cannot be called as a value");
                }
                break;
            }
        }
    }
    return 1;
}

static int emit_frame_validation(
    FILE *output,
    const ReaperLirFunction *function,
    const DuckLirLayout *layout,
    size_t function_id
) {
#define EMIT(...) do { if (fprintf(output, __VA_ARGS__) < 0) return 0; } while (0)
    EMIT(
        "    pushq %%rbp\n"
        "    movq %%rsp, %%rbp\n"
        "    subq $%zu, %%rsp\n"
        "    movq %%r10, -8(%%rbp)\n"
        "    movq %%r11, -16(%%rbp)\n",
        layout->frame_size
    );

    EMIT(
        "    testq %%r10, %%r10\n"
        "    je .Lduck_fn_%zu_bad_pointer\n"
        "    testq $15, %%r10\n"
        "    jne .Lduck_fn_%zu_bad_alignment\n"
        "    testq %%r11, %%r11\n"
        "    je .Lduck_fn_%zu_bad_pointer\n"
        "    testq $15, %%r11\n"
        "    jne .Lduck_fn_%zu_bad_alignment\n",
        function_id, function_id, function_id, function_id
    );

    EMIT(
        "    cmpl $0x49424144, 0(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_magic\n"
        "    cmpw $1, 4(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_version\n"
        "    cmpw $0, 6(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_version\n"
        "    cmpl $48, 8(%%r10)\n"
        "    jb .Lduck_fn_%zu_bad_frame_size\n"
        "    cmpl $%u, 12(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_arguments\n",
        function_id, function_id, function_id, function_id,
        function->parameter_count, function_id
    );

    EMIT(
        "    cmpl $0, 16(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_arguments\n"
        "    cmpl $0, 20(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_flags\n"
        "    cmpl $0, 24(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_flags\n"
        "    cmpl $0, 28(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_flags\n"
        "    cmpq $0, 40(%%r10)\n"
        "    jne .Lduck_fn_%zu_bad_arguments\n",
        function_id, function_id, function_id, function_id, function_id
    );

    if (function->parameter_count == 0U) {
        EMIT(
            "    cmpq $0, 32(%%r10)\n"
            "    jne .Lduck_fn_%zu_bad_arguments\n",
            function_id
        );
    } else {
        EMIT(
            "    movq 32(%%r10), %%r8\n"
            "    testq %%r8, %%r8\n"
            "    je .Lduck_fn_%zu_bad_arguments\n"
            "    testq $15, %%r8\n"
            "    jne .Lduck_fn_%zu_bad_alignment\n",
            function_id, function_id
        );
    }
#undef EMIT
    return 1;
}

static int emit_parameter_loads(
    const ReaperLirModule *module,
    const ReaperLirFunction *function,
    size_t function_index,
    FILE *output
) {
    if (function->parameter_count == 0U) return 1;
    if (fprintf(output, "    movq 32(%%r10), %%r8\n") < 0) return 0;

    for (size_t parameter = 0U; parameter < function->parameter_count; ++parameter) {
        uint32_t slot = module->parameter_slots[function->parameter_offset + parameter];
        if (fprintf(output,
            "    cmpl $1, %zu(%%r8)\n"
            "    jne .Lduck_fn_%zu_bad_arguments\n"
            "    cmpl $0, %zu(%%r8)\n"
            "    jne .Lduck_fn_%zu_bad_arguments\n"
            "    movq %zu(%%r8), %%rax\n"
            "    movq %%rax, -%zu(%%rbp)\n",
            parameter * 16U + 8U, function_index,
            parameter * 16U + 12U, function_index,
            parameter * 16U,
            local_offset(function, slot)) < 0) return 0;
    }
    return 1;
}

static int emit_call(
    const ReaperLirModule *module,
    const ReaperLirFunction *caller,
    const DuckLirLayout *layout,
    const ReaperLirInstruction *instruction,
    size_t instruction_id,
    FILE *output,
    ReaperCodegenError *error
) {
    const ReaperLirFunction *target = NULL;
    if (!resolve_call_target(module, caller->id, instruction,
            &target, error, instruction_id)) return 0;

    if (fprintf(output,
        "    leaq -%zu(%%rbp), %%r10\n"
        "    movl $0x49424144, 0(%%r10)\n"
        "    movw $1, 4(%%r10)\n"
        "    movw $0, 6(%%r10)\n"
        "    movl $48, 8(%%r10)\n"
        "    movl $%u, 12(%%r10)\n"
        "    movl $0, 16(%%r10)\n"
        "    movl $0, 20(%%r10)\n"
        "    movl $0, 24(%%r10)\n"
        "    movl $0, 28(%%r10)\n"
        "    movl $0, 40(%%r10)\n",
        layout->frame_offset, instruction->operand_count) < 0) {
        return codegen_fail(error, instruction_id, "failed to emit DABI64 call frame");
    }

    if (instruction->operand_count == 0U) {
        if (fprintf(output, "    movq $0, 32(%%r10)\n") < 0) return 0;
    } else if (fprintf(output, "    leaq 48(%%r10), %%rax\n    movq %%rax, 32(%%r10)\n") < 0) {
        return 0;
    }

    for (size_t argument = 0U; argument < instruction->operand_count; ++argument) {
        uint32_t vreg = module->operands[instruction->operand_offset + argument];
        if (fprintf(output,
            "    movq -%zu(%%rbp), %%rax\n"
            "    movq %%rax, %zu(%%r10)\n"
            "    movl $1, %zu(%%r10)\n"
            "    movl $0, %zu(%%r10)\n",
            vreg_offset(vreg),
            48U + argument * 16U,
            48U + argument * 16U + 8U,
            48U + argument * 16U + 12U) < 0) {
            return codegen_fail(error, instruction_id, "failed to write DABI64 call argument");
        }
    }

    if (fprintf(output,
        "    movq $0, -%zu(%%rbp)\n"
        "    movq $0, -%zu(%%rbp)\n"
        "    leaq -%zu(%%rbp), %%r11\n"
        "    call duck_fn_%u\n"
        "    testl %%eax, %%eax\n"
        "    jne .Lduck_fn_%u_propagate\n"
        "    cmpl $1, -%zu(%%rbp)\n"
        "    jne .Lduck_fn_%u_bad_arguments\n"
        "    cmpl $0, -%zu(%%rbp)\n"
        "    jne .Lduck_fn_%u_bad_arguments\n"
        "    movq -%zu(%%rbp), %%rax\n"
        "    movq %%rax, -%zu(%%rbp)\n",
        layout->result_offset,
        layout->result_offset - 8U,
        layout->result_offset,
        target->id,
        caller->id,
        layout->result_offset - 8U,
        caller->id,
        layout->result_offset - 12U,
        caller->id,
        layout->result_offset,
        vreg_offset(instruction->destination)) < 0) {
        return codegen_fail(error, instruction_id, "failed to emit DABI64 function call");
    }
    return 1;
}

static int emit_instruction(
    const ReaperLirModule *module,
    const ReaperLirFunction *function,
    const DuckLirLayout *layout,
    const ReaperLirInstruction *instruction,
    size_t instruction_id,
    FILE *output,
    ReaperCodegenError *error
) {
    int64_t immediate = 0;
    switch (instruction->opcode) {
    case REAPER_LIR_CONST:
        if (instruction->type == REAPER_HIR_TYPE_BOOL) {
            immediate = strcmp(instruction->text, "true") == 0 ? 1 : 0;
        } else if (!parse_integer(instruction->text, &immediate)) {
            return codegen_fail(error, instruction_id, "invalid integer constant");
        }
        if (fprintf(output,
            "    movabsq $%" PRId64 ", %%rax\n"
            "    movq %%rax, -%zu(%%rbp)\n",
            immediate, vreg_offset(instruction->destination)) < 0) {
            return codegen_fail(error, instruction_id, "failed to emit constant");
        }
        return 1;

    case REAPER_LIR_FUNCTION_REF:
        if (fprintf(output,
            "    movabsq $%u, %%rax\n"
            "    movq %%rax, -%zu(%%rbp)\n",
            instruction->symbol_id, vreg_offset(instruction->destination)) < 0) {
            return codegen_fail(error, instruction_id, "failed to emit function reference");
        }
        return 1;

    case REAPER_LIR_LOAD_SLOT:
        if (fprintf(output,
            "    movq -%zu(%%rbp), %%rax\n"
            "    movq %%rax, -%zu(%%rbp)\n",
            local_offset(function, instruction->slot_id),
            vreg_offset(instruction->destination)) < 0) {
            return codegen_fail(error, instruction_id, "failed to emit local load");
        }
        return 1;

    case REAPER_LIR_STORE_SLOT:
        if (fprintf(output,
            "    movq -%zu(%%rbp), %%rax\n"
            "    movq %%rax, -%zu(%%rbp)\n",
            vreg_offset(instruction->left),
            local_offset(function, instruction->slot_id)) < 0) {
            return codegen_fail(error, instruction_id, "failed to emit local store");
        }
        return 1;

    case REAPER_LIR_UNARY:
        if (fprintf(output,
            "    movq -%zu(%%rbp), %%rax\n",
            vreg_offset(instruction->left)) < 0) return 0;
        if (strcmp(instruction->text, "-") == 0) {
            if (fprintf(output, "    negq %%rax\n    jo .Lduck_fn_%u_overflow\n",
                    function->id) < 0) return 0;
        } else if (strcmp(instruction->text, "!") == 0 ||
                   strcmp(instruction->text, "not") == 0) {
            if (fprintf(output, "    xorq $1, %%rax\n") < 0) return 0;
        }
        if (fprintf(output, "    movq %%rax, -%zu(%%rbp)\n",
                vreg_offset(instruction->destination)) < 0) return 0;
        return 1;

    case REAPER_LIR_BINARY: {
        const char *op = instruction->text;
        if (fprintf(output,
            "    movq -%zu(%%rbp), %%rax\n",
            vreg_offset(instruction->left)) < 0) return 0;

        if (strcmp(op, "+") == 0 || strcmp(op, "-") == 0 ||
            strcmp(op, "*") == 0) {
            const char *machine = strcmp(op, "+") == 0 ? "addq" :
                strcmp(op, "-") == 0 ? "subq" : "imulq";
            if (fprintf(output,
                "    %s -%zu(%%rbp), %%rax\n"
                "    jo .Lduck_fn_%u_overflow\n",
                machine, vreg_offset(instruction->right), function->id) < 0) return 0;
        } else if (strcmp(op, "/") == 0 || strcmp(op, "//") == 0 ||
                   strcmp(op, "%") == 0) {
            if (fprintf(output,
                "    movq -%zu(%%rbp), %%rcx\n"
                "    testq %%rcx, %%rcx\n"
                "    je .Lduck_fn_%u_divzero\n"
                "    cmpq $-1, %%rcx\n"
                "    jne .Lduck_fn_%u_div_ready_%zu\n"
                "    movabsq $-9223372036854775808, %%rdx\n"
                "    cmpq %%rdx, %%rax\n"
                "    je .Lduck_fn_%u_overflow\n"
                ".Lduck_fn_%u_div_ready_%zu:\n"
                "    cqto\n"
                "    idivq %%rcx\n",
                vreg_offset(instruction->right), function->id,
                function->id, instruction_id, function->id,
                function->id, instruction_id) < 0) return 0;
            if (strcmp(op, "%") == 0 && fprintf(output, "    movq %%rdx, %%rax\n") < 0)
                return 0;
        } else if (strcmp(op, "and") == 0 || strcmp(op, "&&") == 0 ||
                   strcmp(op, "or") == 0 || strcmp(op, "||") == 0) {
            const char *machine = (strcmp(op, "and") == 0 || strcmp(op, "&&") == 0)
                ? "andq" : "orq";
            if (fprintf(output, "    %s -%zu(%%rbp), %%rax\n",
                machine, vreg_offset(instruction->right)) < 0) return 0;
        } else {
            const char *condition = NULL;
            if (strcmp(op, "==") == 0) condition = "sete";
            else if (strcmp(op, "!=") == 0) condition = "setne";
            else if (strcmp(op, "<") == 0) condition = "setl";
            else if (strcmp(op, "<=") == 0) condition = "setle";
            else if (strcmp(op, ">") == 0) condition = "setg";
            else if (strcmp(op, ">=") == 0) condition = "setge";
            if (condition == NULL) {
                return codegen_fail(error, instruction_id, "unsupported binary operation");
            }
            if (fprintf(output,
                "    cmpq -%zu(%%rbp), %%rax\n"
                "    %s %%al\n"
                "    movzbq %%al, %%rax\n",
                vreg_offset(instruction->right), condition) < 0) return 0;
        }

        if (fprintf(output, "    movq %%rax, -%zu(%%rbp)\n",
                vreg_offset(instruction->destination)) < 0) return 0;
        return 1;
    }

    case REAPER_LIR_CALL:
    case REAPER_LIR_PIPE_CALL:
        return emit_call(
            module, function, layout, instruction, instruction_id, output, error
        );

    case REAPER_LIR_DROP:
        return 1;

    default:
        return codegen_fail(
            error,
            instruction_id,
            "LIR operation requires a DuckOS runtime lowering not yet available"
        );
    }
}

static int emit_terminator(
    const ReaperLirModule *module,
    const ReaperLirFunction *function,
    const ReaperLirBlock *block,
    FILE *output,
    ReaperCodegenError *error
) {
    switch (block->terminator) {
    case REAPER_LIR_TERM_JUMP:
        return fprintf(output, "    jmp .Lduck_fn_%u_block_%u\n",
            function->id, block->target_true) >= 0;

    case REAPER_LIR_TERM_BRANCH:
        if (fprintf(output,
            "    movq -%zu(%%rbp), %%rax\n"
            "    testq %%rax, %%rax\n"
            "    jne .Lduck_fn_%u_block_%u\n"
            "    jmp .Lduck_fn_%u_block_%u\n",
            vreg_offset(block->terminator_value),
            function->id, block->target_true,
            function->id, block->target_false) < 0) {
            return codegen_fail(error, block->id, "failed to emit conditional branch");
        }
        return 1;

    case REAPER_LIR_TERM_RETURN:
        if (fprintf(output,
            "    movq -16(%%rbp), %%r11\n"
            "    movq $0, 0(%%r11)\n"
            "    movl $0, 8(%%r11)\n"
            "    movl $0, 12(%%r11)\n") < 0) return 0;
        if (block->terminator_value != REAPER_LIR_NO_VALUE) {
            if (fprintf(output,
                "    movq -%zu(%%rbp), %%rax\n"
                "    movq %%rax, 0(%%r11)\n"
                "    movl $1, 8(%%r11)\n",
                vreg_offset(block->terminator_value)) < 0) return 0;
        }
        return fprintf(output, "    xorl %%eax, %%eax\n    leave\n    ret\n") >= 0;

    default:
        return codegen_fail(error, block->id, "MIR block has no supported terminator");
    }
}

static int emit_function(
    const ReaperLirModule *module,
    const DuckLirLayout *layouts,
    const ReaperLirFunction *function,
    FILE *output,
    ReaperCodegenError *error
) {
    size_t f = function->id;
    if (f == 0U) {
        if (fprintf(output,
            ".globl duck_program\n"
            ".type duck_program, @function\n"
            "duck_program:\n") < 0) return 0;
    } else {
        if (fprintf(output,
            ".globl duck_fn_%zu\n"
            ".type duck_fn_%zu, @function\n"
            "duck_fn_%zu:\n",
            f, f, f) < 0) return 0;
    }

    if (!emit_frame_validation(output, function, &layouts[f], f) ||
        !emit_parameter_loads(module, function, f, output)) {
        return codegen_fail(error, f, "failed to emit DABI64 function entry");
    }

    size_t block_end = (size_t)function->first_block + function->block_count;
    for (size_t block_id = function->first_block; block_id < block_end; ++block_id) {
        const ReaperLirBlock *block = &module->blocks[block_id];
        if (fprintf(output, ".Lduck_fn_%zu_block_%zu:\n", f, block_id) < 0) return 0;

        size_t order_end = (size_t)block->first_instruction + block->instruction_count;
        for (size_t order = block->first_instruction;
             block->instruction_count != 0U && order < order_end;
             ++order) {
            uint32_t instruction_id = module->instruction_order[order];
            if (!emit_instruction(
                    module, function, &layouts[f],
                    &module->instructions[instruction_id],
                    instruction_id, output, error)) return 0;
        }

        if (!emit_terminator(module, function, block, output, error)) return 0;
    }

    if (fprintf(output,
        ".Lduck_fn_%zu_propagate:\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_overflow:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_divzero:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_bad_pointer:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_bad_alignment:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_bad_magic:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_bad_version:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_bad_frame_size:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_bad_flags:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_fn_%zu_bad_arguments:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n",
        f, f, REAPER_DUCK_STATUS_ARITHMETIC_OVERFLOW,
        f, REAPER_DUCK_STATUS_DIVISION_BY_ZERO,
        f, REAPER_DUCK_STATUS_INVALID_POINTER,
        f, REAPER_DUCK_STATUS_BAD_ALIGNMENT,
        f, REAPER_DUCK_STATUS_BAD_MAGIC,
        f, REAPER_DUCK_STATUS_VERSION_MISMATCH,
        f, REAPER_DUCK_STATUS_BAD_FRAME_SIZE,
        f, REAPER_DUCK_STATUS_INVALID_FLAGS,
        f, REAPER_DUCK_STATUS_BAD_ARGUMENT_LAYOUT) < 0) {
        return codegen_fail(error, f, "failed to write DABI64 function error exits");
    }

    if (fprintf(output, ".size %s%zu, .-%s%zu\n",
            f == 0U ? "duck_program" : "duck_fn_",
            f,
            f == 0U ? "duck_program" : "duck_fn_",
            f) < 0) return 0;
    return 1;
}

int reaper_codegen_duckos_dabi64_lir(
    const ReaperLirModule *module,
    FILE *output,
    ReaperCodegenError *error
) {
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }
    if (module == NULL || output == NULL) {
        return codegen_fail(error, 0U, "LIR module and output stream are required");
    }
    if (module->function_count == 0U ||
        module->function_count > SIZE_MAX / sizeof(DuckLirLayout)) {
        return codegen_fail(error, 0U, "DABI64 LIR module function count is invalid");
    }

    DuckLirLayout *layouts = calloc(module->function_count, sizeof *layouts);
    if (layouts == NULL) {
        return codegen_fail(error, 0U, "unable to allocate DABI64 function layouts");
    }

    if (!validate_module(module, layouts, error)) {
        free(layouts);
        return 0;
    }

    if (fprintf(output,
        "# Reaper target: DuckOS DABI64 v1, scalar MIR/LIR subset\n"
        ".section .text\n") < 0) {
        free(layouts);
        return codegen_fail(error, 0U, "failed to write DABI64 assembly header");
    }

    int success = 1;
    for (size_t i = 0U; i < module->function_count; ++i) {
        if (!emit_function(module, layouts, &module->functions[i], output, error)) {
            success = 0;
            break;
        }
    }

    if (success && fprintf(output,
        ".section .note.duckos.abi,\"a\",@note\n"
        ".align 4\n"
        ".long 7\n"
        ".long 16\n"
        ".long %u\n"
        ".asciz \"DUCKOS\"\n"
        ".align 4\n"
        ".long %u\n"
        ".long %u\n"
        ".long %u\n"
        ".long %u\n"
        ".section .note.GNU-stack,\"\",@progbits\n",
        REAPER_DUCK_ABI_NOTE_TYPE,
        REAPER_DUCK_ABI_MAJOR,
        REAPER_DUCK_ABI_MINOR,
        REAPER_DUCK_ABI_ARCH_X86_64,
        REAPER_DUCK_ABI_NOTE_FLAGS) < 0) {
        success = 0;
        (void)codegen_fail(error, 0U, "failed to write DABI64 ELF ABI note");
    }

    if (success && ferror(output)) {
        success = 0;
        (void)codegen_fail(error, 0U, "failed to finish DABI64 assembly output");
    }

    free(layouts);
    return success;
}
