#include "reaper/codegen.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

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

static size_t stack_slot(size_t node_index) {
    return 16U + node_index * 8U;
}

int reaper_codegen_x86_64_sysv_elf(
    const ReaperIrModule *module,
    FILE *output,
    ReaperCodegenError *error
) {
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }

    if (module == NULL || output == NULL || module->nodes == NULL) {
        return codegen_fail(error, 0U, "IR module and output stream are required");
    }
    if (module->length == 0U) {
        return codegen_fail(error, 0U, "executable IR cannot be empty");
    }
    if (module->length > REAPER_CODEGEN_X86_64_MAX_NODES) {
        return codegen_fail(error, 0U, "IR module exceeds the x86-64 codegen node limit");
    }

    ReaperIrError ir_error;
    if (!reaper_ir_verify(module, &ir_error)) {
        return codegen_fail(error, ir_error.node_index, ir_error.message);
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
        return codegen_fail(
            error,
            return_index,
            "IR must end with exactly one RETURN"
        );
    }
    if (module->nodes[return_index].lhs >= module->length ||
        module->nodes[module->nodes[return_index].lhs].type != REAPER_IR_TYPE_I64) {
        return codegen_fail(
            error,
            return_index,
            "x86-64 expression backend requires an i64 RETURN operand"
        );
    }

    size_t frame_size = 8U + module->length * 8U;
    frame_size = (frame_size + 15U) & ~(size_t)15U;

    if (fprintf(output,
        "# Reaper native backend: x86-64 System V ELF\n"
        "# int reaper_program(int64_t *result)\n"
        ".section .text\n"
        ".globl reaper_program\n"
        ".type reaper_program, @function\n"
        "reaper_program:\n"
        "    pushq %%rbp\n"
        "    movq %%rsp, %%rbp\n"
        "    subq $%zu, %%rsp\n"
        "    movq %%rdi, -8(%%rbp)\n"
        "    testq %%rdi, %%rdi\n"
        "    je .Lreaper_bad_output\n",
        frame_size) < 0) {
        return codegen_fail(error, 0U, "failed to write assembly prologue");
    }

    for (size_t i = 0U; i < module->length; ++i) {
        const ReaperIrNode *node = &module->nodes[i];
        if (node->opcode == REAPER_IR_OP_RETURN) {
            if (fprintf(output,
                "    movq -%zu(%%rbp), %%rax\n"
                "    movq -8(%%rbp), %%rcx\n"
                "    movq %%rax, (%%rcx)\n"
                "    xorl %%eax, %%eax\n"
                "    leave\n"
                "    ret\n",
                stack_slot(node->lhs)) < 0) {
                return codegen_fail(error, i, "failed to write RETURN sequence");
            }
            continue;
        }

        if (node->opcode == REAPER_IR_OP_CONST_I64) {
            if (fprintf(output,
                "    movabsq $%" PRId64 ", %%rax\n"
                "    movq %%rax, -%zu(%%rbp)\n",
                node->immediate, stack_slot(i)) < 0) {
                return codegen_fail(error, i, "failed to write integer constant");
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
                "    jo .Lreaper_overflow\n"
                "    movq %%rax, -%zu(%%rbp)\n",
                stack_slot(node->lhs),
                operation,
                stack_slot(node->rhs),
                stack_slot(i)) < 0) {
                return codegen_fail(error, i, "failed to write checked arithmetic");
            }
            continue;
        }

        if (node->opcode == REAPER_IR_OP_DIV_I64) {
            if (fprintf(output,
                "    movq -%zu(%%rbp), %%rcx\n"
                "    testq %%rcx, %%rcx\n"
                "    je .Lreaper_divzero\n"
                "    movq -%zu(%%rbp), %%rax\n"
                "    cmpq $-1, %%rcx\n"
                "    jne .Lreaper_div_ready_%zu\n"
                "    movabsq $-9223372036854775808, %%rdx\n"
                "    cmpq %%rdx, %%rax\n"
                "    je .Lreaper_overflow\n"
                ".Lreaper_div_ready_%zu:\n"
                "    cqto\n"
                "    idivq %%rcx\n"
                "    movq %%rax, -%zu(%%rbp)\n",
                stack_slot(node->rhs),
                stack_slot(node->lhs),
                i,
                i,
                stack_slot(i)) < 0) {
                return codegen_fail(error, i, "failed to write checked division");
            }
            continue;
        }

        return codegen_fail(error, i, "IR opcode has no x86-64 lowering");
    }

    if (fprintf(output,
        ".Lreaper_overflow:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lreaper_divzero:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".Lreaper_bad_output:\n"
        "    movl $%d, %%eax\n"
        "    leave\n"
        "    ret\n"
        ".size reaper_program, .-reaper_program\n"
        ".section .note.GNU-stack,\"\",@progbits\n",
        REAPER_CODEGEN_OVERFLOW,
        REAPER_CODEGEN_DIVISION_BY_ZERO,
        REAPER_CODEGEN_INVALID_OUTPUT) < 0 || ferror(output)) {
        return codegen_fail(error, module->length - 1U, "failed to finish assembly output");
    }

    return 1;
}
