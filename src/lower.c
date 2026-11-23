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

static int source_position(
    const ReaperAstNode *node,
    uint32_t *line,
    uint32_t *column
) {
    if (node->line > UINT32_MAX || node->column > UINT32_MAX) {
        return 0;
    }

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

static int parse_i64_literal(
    const ReaperAstNode *node,
    int64_t *value,
    ReaperIrError *error,
    size_t ast_index
) {
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

    *value = (int64_t)parsed;
    return 1;
}

static ReaperIrOpcode binary_opcode(const char *operator_text) {
    if (strcmp(operator_text, "+") == 0) return REAPER_IR_OP_ADD_I64;
    if (strcmp(operator_text, "-") == 0) return REAPER_IR_OP_SUB_I64;
    if (strcmp(operator_text, "*") == 0) return REAPER_IR_OP_MUL_I64;
    if (strcmp(operator_text, "/") == 0) return REAPER_IR_OP_DIV_I64;
    return REAPER_IR_OP_INVALID;
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
    uint32_t line = 0U;
    uint32_t column = 0U;
    if (!source_position(node, &line, &column)) {
        return lower_fail(error, ast_index, "source location exceeds canonical IR range");
    }

    if (node->kind == REAPER_AST_INTEGER) {
        int64_t value = 0;
        if (!parse_i64_literal(node, &value, error, ast_index)) {
            return 0;
        }

        ReaperIrNode constant = {
            REAPER_IR_OP_CONST_I64,
            REAPER_IR_TYPE_I64,
            REAPER_IR_NO_VALUE,
            REAPER_IR_NO_VALUE,
            value,
            line,
            column
        };
        return append_node(output, capacity, length, constant, result, error, ast_index);
    }

    if (node->kind == REAPER_AST_UNARY) {
        if (node->left >= ast_index || node->text == NULL) {
            return lower_fail(error, ast_index, "unary AST node has an invalid operand or operator");
        }

        const ReaperAstNode *operand_node = &ast->items[node->left];

        /* The positive magnitude of INT64_MIN is not representable as i64. */
        if (strcmp(node->text, "-") == 0 &&
            operand_node->kind == REAPER_AST_INTEGER &&
            operand_node->text != NULL &&
            strcmp(operand_node->text, "9223372036854775808") == 0) {
            ReaperIrNode minimum = {
                REAPER_IR_OP_CONST_I64,
                REAPER_IR_TYPE_I64,
                REAPER_IR_NO_VALUE,
                REAPER_IR_NO_VALUE,
                INT64_MIN,
                line,
                column
            };
            return append_node(output, capacity, length, minimum, result, error, ast_index);
        }

        uint32_t operand = 0U;
        if (!lower_node(
                ast, node->left, output, capacity, length,
                &operand, depth + 1U, error)) {
            return 0;
        }

        if (strcmp(node->text, "+") == 0) {
            *result = operand;
            return 1;
        }
        if (strcmp(node->text, "-") != 0) {
            return lower_fail(error, ast_index, "unary operator is not supported by the i64 backend");
        }

        ReaperIrNode zero = {
            REAPER_IR_OP_CONST_I64,
            REAPER_IR_TYPE_I64,
            REAPER_IR_NO_VALUE,
            REAPER_IR_NO_VALUE,
            0,
            line,
            column
        };
        uint32_t zero_index = 0U;
        if (!append_node(output, capacity, length, zero, &zero_index, error, ast_index)) {
            return 0;
        }

        ReaperIrNode negate = {
            REAPER_IR_OP_SUB_I64,
            REAPER_IR_TYPE_I64,
            zero_index,
            operand,
            0,
            line,
            column
        };
        return append_node(output, capacity, length, negate, result, error, ast_index);
    }

    if (node->kind == REAPER_AST_BINARY && node->text != NULL) {
        ReaperIrOpcode opcode = binary_opcode(node->text);
        if (opcode == REAPER_IR_OP_INVALID) {
            return lower_fail(error, ast_index, "binary operator is not supported by the i64 backend");
        }
        if (node->left >= ast_index || node->right >= ast_index) {
            return lower_fail(error, ast_index, "AST children must precede their parent");
        }

        uint32_t lhs = 0U;
        uint32_t rhs = 0U;
        if (!lower_node(
                ast, node->left, output, capacity, length,
                &lhs, depth + 1U, error) ||
            !lower_node(
                ast, node->right, output, capacity, length,
                &rhs, depth + 1U, error)) {
            return 0;
        }

        ReaperIrNode operation = {
            opcode,
            REAPER_IR_TYPE_I64,
            lhs,
            rhs,
            0,
            line,
            column
        };
        return append_node(
            output, capacity, length, operation, result, error, ast_index
        );
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
    if (output_length != NULL) {
        *output_length = 0U;
    }
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }

    if (ast == NULL || ast->items == NULL || ast->length == 0U ||
        ast->root >= ast->length || output == NULL || output_length == NULL) {
        return lower_fail(error, 0U, "valid AST, output storage, and output length are required");
    }
    if (ast->length > (SIZE_MAX - 1U) / 2U) {
        return lower_fail(error, ast->root, "AST is too large for bounded IR lowering");
    }

    size_t required_capacity = ast->length * 2U + 1U;
    if (output_capacity < required_capacity) {
        return lower_fail(error, ast->root, "output capacity must hold twice the AST size plus RETURN");
    }

    size_t length = 0U;
    uint32_t value = 0U;
    if (!lower_node(
            ast, ast->root, output, output_capacity,
            &length, &value, 0U, error)) {
        return 0;
    }

    const ReaperAstNode *root = &ast->items[ast->root];
    uint32_t line = 0U;
    uint32_t column = 0U;
    if (!source_position(root, &line, &column)) {
        return lower_fail(error, ast->root, "source location exceeds canonical IR range");
    }

    ReaperIrNode ret = {
        REAPER_IR_OP_RETURN,
        REAPER_IR_TYPE_UNIT,
        value,
        REAPER_IR_NO_VALUE,
        0,
        line,
        column
    };
    uint32_t ignored = 0U;
    if (!append_node(output, output_capacity, &length, ret, &ignored, error, ast->root)) {
        return 0;
    }

    ReaperIrModule module = { output, length };
    if (!reaper_ir_verify(&module, error)) {
        return 0;
    }

    *output_length = length;
    return 1;
}
