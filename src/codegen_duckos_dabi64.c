#include "reaper/codegen.h"
#include "reaper/duckos_abi.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

static int duck_codegen_fail(
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

static size_t duck_stack_slot(size_t index) {
    return 16U + index * 8U;
}

static int emit_note(FILE *output) {
    return fprintf(output,
        ".section .note.duckos.abi,\"a\",@note\n"
        ".balign 4\n"
        ".long 7\n"
        ".long 16\n"
        ".long 0x%08" PRIx32 "\n"
        ".asciz \"DUCKOS\"\n"
        ".balign 4\n"
        ".long %u\n"
        ".long %u\n"
        ".long 1\n"
        ".long 0\n"
        ".balign 4\n",
        REAPER_DABI64_NOTE_TYPE,
        REAPER_DABI64_MAJOR,
        REAPER_DABI64_MINOR
    ) >= 0;
}

int reaper_codegen_duckos_dabi64_v1(
    const ReaperIrModule *module,
    FILE *output,
    ReaperCodegenError *error
) {
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }
    if (module == NULL || output == NULL || module->nodes == NULL) {
        return duck_codegen_fail(error, 0U, "IR module and output stream are required");
    }
    if (module->length == 0U ||
        module->length > REAPER_CODEGEN_X86_64_MAX_NODES) {
        return duck_codegen_fail(error, 0U, "IR length is outside DABI64 backend limits");
    }

    ReaperIrError ir_error;
    if (!reaper_ir_verify(module, &ir_error)) {
        return duck_codegen_fail(error, ir_error.node_index, ir_error.message);
    }

    size_t return_count = 0U;
    size_t return_index = 0U;
    for (size_t i = 0U; i < module->length; ++i) {
        if (module->nodes[i].opcode == REAPER_IR_OP_RETURN) {
            ++return_count;
            return_index = i;
        }
    }
    if (return_count != 1U || return_index != module->length - 1U) {
        return duck_codegen_fail(
            error, return_index, "IR must end with exactly one RETURN"
        );
    }
    if (module->nodes[return_index].lhs >= module->length ||
        module->nodes[module->nodes[return_index].lhs].type != REAPER_IR_TYPE_I64) {
        return duck_codegen_fail(
            error, return_index, "DABI64 expression entry requires an i64 RETURN operand"
        );
    }

    size_t frame_size = 8U + module->length * 8U;
    frame_size = (frame_size + 15U) & ~(size_t)15U;

    if (!emit_note(output) || fprintf(output,
        ".section .text\n"
        ".globl duck_program\n"
        ".type duck_program, @function\n"
        "duck_program:\n"
        "    pushq %%rbp\n"
        "    movq %%rsp, %%rbp\n"
        "    subq $%zu, %%rsp\n"
        "    testq %%r11, %%r11\n"
        "    je .Lduck_bad_result\n"
        "    testq $15, %%r11\n"
        "    jne .Lduck_bad_alignment\n",
        frame_size) < 0) {
        return duck_codegen_fail(error, 0U, "failed to write DABI64 assembly prologue");
    }

    for (size_t i = 0U; i < module->length; ++i) {
        const ReaperIrNode *node = &module->nodes[i];

        if (node->opcode == REAPER_IR_OP_RETURN) {
            if (fprintf(output,
                "    movq -%zu(%%rbp), %%rax\n"
                "    movq %%rax, 0(%%r11)\n"
                "    movl $1, 8(%%r11)\n"
                "    movl $0, 12(%%r11)\n"
                "    xorl %%eax, %%eax\n"
                "    leave\n"
                "    ret\n",
                duck_stack_slot(node->lhs)) < 0) {
                return duck_codegen_fail(error, i, "failed to write DABI64 RETURN sequence");
            }
            continue;
        }

        if (node->opcode == REAPER_IR_OP_CONST_I64) {
            if (fprintf(output,
                "    movabsq $%" PRId64 ", %%rax\n"
                "    movq %%rax, -%zu(%%rbp)\n",
                node->immediate, duck_stack_slot(i)) < 0) {
                return duck_codegen_fail(error, i, "failed to write DABI64 integer constant");
            }
            continue;
        }

        if (node->opcode == REAPER_IR_OP_ADD_I64 ||
            node->opcode == REAPER_IR_OP_SUB_I64 ||
            node->opcode == REAPER_IR_OP_MUL_I64) {
            const char *operation =
                node->opcode == REAPER_IR_OP_ADD_I64 ? "addq" :
                node->opcode == REAPER_IR_OP_SUB_I64 ? "subq" : "imulq";

            if (fprintf(output,
                "    movq -%zu(%%rbp), %%rax\n"
                "    %s -%zu(%%rbp), %%rax\n"
                "    jo .Lduck_overflow\n"
                "    movq %%rax, -%zu(%%rbp)\n",
                duck_stack_slot(node->lhs),
                operation,
                duck_stack_slot(node->rhs),
                duck_stack_slot(i)) < 0) {
                return duck_codegen_fail(error, i, "failed to write DABI64 checked arithmetic");
            }
            continue;
        }

        if (node->opcode == REAPER_IR_OP_DIV_I64) {
            if (fprintf(output,
                "    movq -%zu(%%rbp), %%rcx\n"
                "    testq %%rcx, %%rcx\n"
                "    je .Lduck_divzero\n"
                "    movq -%zu(%%rbp), %%rax\n"
                "    cmpq $-1, %%rcx\n"
                "    jne .Lduck_div_ready_%zu\n"
                "    movabsq $-9223372036854775808, %%rdx\n"
                "    cmpq %%rdx, %%rax\n"
                "    je .Lduck_overflow\n"
                ".Lduck_div_ready_%zu:\n"
                "    cqto\n"
                "    idivq %%rcx\n"
                "    movq %%rax, -%zu(%%rbp)\n",
                duck_stack_slot(node->rhs),
                duck_stack_slot(node->lhs),
                i,
                i,
                duck_stack_slot(i)) < 0) {
                return duck_codegen_fail(error, i, "failed to write DABI64 checked division");
            }
            continue;
        }

        return duck_codegen_fail(error, i, "IR opcode has no DABI64 x86-64 lowering");
    }

    if (fprintf(output,
        ".Lduck_overflow:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_divzero:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_bad_result:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lduck_bad_alignment:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".size duck_program, .-duck_program\n"
        ".section .note.GNU-stack,\"\",@progbits\n",
        REAPER_DUCK_STATUS_ARITHMETIC_OVERFLOW,
        REAPER_DUCK_STATUS_DIVISION_BY_ZERO,
        REAPER_DUCK_STATUS_INVALID_POINTER,
        REAPER_DUCK_STATUS_BAD_ALIGNMENT) < 0 || ferror(output)) {
        return duck_codegen_fail(error, module->length - 1U, "failed to finish DABI64 assembly output");
    }

    return 1;
}
