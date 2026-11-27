#include "reaper/lower.h"

#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int lower_fail(ReaperIrError *error, size_t index, const char *message) {
    if (error != NULL) {
        error->node_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static int source_position(const ReaperAstNode *node, uint32_t *line, uint32_t *column) {
    if (node->line > UINT32_MAX || node->column > UINT32_MAX) return 0;
    *line = (uint32_t)node->line;
    *column = (uint32_t)node->column;
    return 1;
}

static int append_node(
    ReaperIrNode *output,
    size_t capacity,
    size_t *length,
    ReaperIrNode node,
    uint32_t *result,
    ReaperIrError *error,
    size_t ast_index
) {
    if (*length >= capacity || *length >= UINT32_MAX) {
        return lower_fail(error, ast_index, "IR output capacity or value index limit exceeded");
    }
    *result = (uint32_t)*length;
    output[*length] = node;
    ++*length;
    return 1;
}

static int lower_node(
    const ReaperAst *ast,
    uint32_t ast_index,
    ReaperIrNode *output,
    size_t capacity,
    size_t *length,
    uint32_t *result,
    size_t depth,
    ReaperIrError *error
) {
    if (depth > ast->length || ast_index >= ast->length) {
        return lower_fail(error, ast_index, "invalid AST reference or excessive lowering depth");
    }

    const ReaperAstNode *node = &ast->items[ast_index];
    uint32_t line = 0, column = 0;
    if (!source_position(node, &line, &column)) {
        return lower_fail(error, ast_index, "source location exceeds canonical IR range");
    }

    if (node->kind == REAPER_AST_INTEGER) {
        if (node->text == NULL || node->text[0] == '\0') {
            return lower_fail(error, ast_index, "empty integer literal");
        }
        errno = 0;
        char *end = NULL;
        intmax_t parsed = strtoimax(node->text, &end, 10);
        if (errno == ERANGE || end == node->text || end == NULL || *end != '\0' ||
            parsed < INT64_MIN || parsed > INT64_MAX) {
            return lower_fail(error, ast_index, "integer literal is outside signed i64 range");
        }
        ReaperIrNode constant = {
            REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
            REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, (int64_t)parsed,
            line, column
        };
        return append_node(output, capacity, length, constant, result, error, ast_index);
    }

    if (node->kind == REAPER_AST_UNARY && node->text != NULL &&
        strcmp(node->text, "~") == 0) {
        if (node->left >= ast_index) {
            return lower_fail(error, ast_index, "AST child must precede its parent");
        }
        uint32_t operand = 0;
        if (!lower_node(ast, node->left, output, capacity, length,
                        &operand, depth + 1, error)) return 0;
        ReaperIrNode bit_not = {
            REAPER_IR_OP_BIT_NOT_I64, REAPER_IR_TYPE_I64,
            operand, REAPER_IR_NO_VALUE, 0, line, column
        };
        return append_node(output, capacity, length, bit_not,
                           result, error, ast_index);
    }

    if (node->kind == REAPER_AST_BINARY && node->text != NULL) {
        if (node->left >= ast_index || node->right >= ast_index) {
            return lower_fail(error, ast_index, "AST children must precede their parent");
        }
        uint32_t lhs = 0, rhs = 0;
        if (!lower_node(ast, node->left, output, capacity, length, &lhs, depth + 1, error) ||
            !lower_node(ast, node->right, output, capacity, length, &rhs, depth + 1, error)) {
            return 0;
        }
        ReaperIrOpcode opcode;
        if (strcmp(node->text, "+") == 0) opcode = REAPER_IR_OP_ADD_I64;
        else if (strcmp(node->text, "-") == 0) opcode = REAPER_IR_OP_SUB_I64;
        else if (strcmp(node->text, "*") == 0) opcode = REAPER_IR_OP_MUL_I64;
        else if (strcmp(node->text, "/") == 0) opcode = REAPER_IR_OP_DIV_I64;
        else if (strcmp(node->text, "&") == 0) opcode = REAPER_IR_OP_BIT_AND_I64;
        else if (strcmp(node->text, "|") == 0) opcode = REAPER_IR_OP_BIT_OR_I64;
        else if (strcmp(node->text, "^") == 0) opcode = REAPER_IR_OP_BIT_XOR_I64;
        else if (strcmp(node->text, "<<") == 0) opcode = REAPER_IR_OP_SHL_I64;
        else if (strcmp(node->text, ">>") == 0) opcode = REAPER_IR_OP_SHR_I64;
        else return lower_fail(error, ast_index,
            "binary operator is not supported by the integer IR lowering slice");
        ReaperIrNode operation = {
            opcode, REAPER_IR_TYPE_I64, lhs, rhs, 0, line, column
        };
        return append_node(output, capacity, length, operation,
                           result, error, ast_index);
    }

    return lower_fail(error, ast_index, "AST node is not supported by the integer IR lowering slice");
}

int reaper_lower_ast_to_ir(
    const ReaperAst *ast,
    ReaperIrNode *output,
    size_t output_capacity,
    size_t *output_length,
    ReaperIrError *error
) {
    if (output_length != NULL) *output_length = 0;
    if (error != NULL) {
        error->node_index = 0;
        error->message[0] = '\0';
    }
    if (ast == NULL || ast->items == NULL || ast->length == 0 || ast->length == SIZE_MAX ||
        ast->root >= ast->length || output == NULL || output_length == NULL) {
        return lower_fail(error, 0, "valid AST, output storage, and output length are required");
    }
    if (output_capacity < ast->length + 1) {
        return lower_fail(error, ast->root, "output capacity must hold AST nodes plus RETURN");
    }

    size_t length = 0;
    uint32_t value = 0;
    if (!lower_node(ast, ast->root, output, output_capacity, &length, &value, 0, error)) {
        return 0;
    }

    const ReaperAstNode *root = &ast->items[ast->root];
    uint32_t line = 0, column = 0;
    if (!source_position(root, &line, &column)) {
        return lower_fail(error, ast->root, "source location exceeds canonical IR range");
    }
    ReaperIrNode ret = {
        REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, value,
        REAPER_IR_NO_VALUE, 0, line, column
    };
    uint32_t ignored = 0;
    if (!append_node(output, output_capacity, &length, ret, &ignored, error, ast->root)) {
        return 0;
    }

    ReaperIrModule module = { output, length };
    if (!reaper_ir_verify(&module, error)) return 0;
    *output_length = length;
    return 1;
}
