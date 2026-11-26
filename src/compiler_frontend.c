#include "reaper/compiler_ir.h"

#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int frontend_fail(ReaperCompilerIrError *error, size_t index,
                         const char *source, size_t line, size_t column,
                         const char *message) {
    if (error != NULL) {
        memset(error, 0, sizeof *error);
        error->node_index = index;
        if (source != NULL)
            (void)snprintf(error->span.source, sizeof error->span.source, "%s", source);
        error->span.line = line <= UINT32_MAX ? (uint32_t)line : 0u;
        error->span.column = column <= UINT32_MAX ? (uint32_t)column : 0u;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static int copy_span(ReaperCompilerSourceSpan *span,
                     const char *source, const ReaperAstNode *node) {
    if (span == NULL || source == NULL || node == NULL ||
        node->line == 0u || node->column == 0u ||
        node->line > UINT32_MAX || node->column > UINT32_MAX ||
        strlen(source) >= sizeof span->source) return 0;
    memset(span, 0, sizeof *span);
    (void)snprintf(span->source, sizeof span->source, "%s", source);
    span->line = (uint32_t)node->line;
    span->column = (uint32_t)node->column;
    return 1;
}

static int parse_i64_literal(const char *text, int64_t *value) {
    char *end = NULL;
    intmax_t parsed;
    if (text == NULL || text[0] == '\0' || value == NULL) return 0;
    errno = 0;
    parsed = strtoimax(text, &end, 10);
    if (errno == ERANGE || end == text || end == NULL || *end != '\0' ||
        parsed < INT64_MIN || parsed > INT64_MAX) return 0;
    *value = (int64_t)parsed;
    return 1;
}

static int parse_f64_literal(const char *text, double *value) {
    char *end = NULL;
    double parsed;
    if (text == NULL || text[0] == '\0' || value == NULL) return 0;
    errno = 0;
    parsed = strtod(text, &end);
    if (errno == ERANGE || end == text || end == NULL || *end != '\0' ||
        !isfinite(parsed)) return 0;
    *value = parsed;
    return 1;
}

static int supported_binary_operator(const char *text) {
    return text != NULL &&
        (strcmp(text, "+") == 0 || strcmp(text, "-") == 0 ||
         strcmp(text, "*") == 0 || strcmp(text, "/") == 0);
}

static int supported_unary_operator(const char *text) {
    return text != NULL && (strcmp(text, "+") == 0 || strcmp(text, "-") == 0);
}

int reaper_compiler_ir_lower_ast_to_hir(
    const ReaperAst *ast,
    const char *source_name,
    ReaperCompilerIrNode *output,
    size_t output_capacity,
    ReaperCompilerIrModule *hir,
    ReaperCompilerIrError *error
) {
    size_t index;
    if (error != NULL) memset(error, 0, sizeof *error);
    if (hir != NULL) memset(hir, 0, sizeof *hir);

    if (ast == NULL || ast->items == NULL || ast->length == 0u ||
        ast->length > REAPER_COMPILER_IR_MAX_NODES ||
        ast->root >= ast->length || source_name == NULL ||
        source_name[0] == '\0' ||
        strlen(source_name) >= REAPER_COMPILER_IR_SOURCE_MAX ||
        output == NULL || hir == NULL || output_capacity < ast->length) {
        return frontend_fail(error, 0u, source_name, 0u, 0u,
            "valid AST, source name and sufficient HIR output storage are required");
    }

    for (index = 0u; index < ast->length; ++index) {
        const ReaperAstNode *source_node = &ast->items[index];
        ReaperCompilerIrNode node;
        uint32_t left = source_node->left;
        uint32_t right = source_node->right;

        memset(&node, 0, sizeof node);
        node.lhs = REAPER_COMPILER_IR_NO_VALUE;
        node.rhs = REAPER_COMPILER_IR_NO_VALUE;
        if (source_node->text == NULL ||
            !copy_span(&node.span, source_name, source_node)) {
            return frontend_fail(error, index, source_name,
                source_node->line, source_node->column,
                "AST node has missing text or an invalid source span");
        }

        switch (source_node->kind) {
        case REAPER_AST_INTEGER:
            node.opcode = REAPER_COMPILER_IR_HIR_VALUE;
            node.type = REAPER_COMPILER_IR_TYPE_I64;
            if (!parse_i64_literal(source_node->text, &node.integer)) {
                return frontend_fail(error, index, source_name,
                    source_node->line, source_node->column,
                    "integer literal is outside the signed i64 range or malformed");
            }
            break;

        case REAPER_AST_DECIMAL:
            node.opcode = REAPER_COMPILER_IR_HIR_VALUE;
            node.type = REAPER_COMPILER_IR_TYPE_F64;
            if (!parse_f64_literal(source_node->text, &node.number)) {
                return frontend_fail(error, index, source_name,
                    source_node->line, source_node->column,
                    "decimal literal is not a finite representable f64 value");
            }
            break;

        case REAPER_AST_STRING: {
            const size_t text_length = strlen(source_node->text);
            node.opcode = REAPER_COMPILER_IR_HIR_VALUE;
            node.type = REAPER_COMPILER_IR_TYPE_TEXT;
            if (text_length >= sizeof node.text) {
                return frontend_fail(error, index, source_name,
                    source_node->line, source_node->column,
                    "decoded string literal exceeds the native HIR text limit");
            }
            memcpy(node.text, source_node->text, text_length + 1u);
            break;
        }

        case REAPER_AST_BOOLEAN:
            node.opcode = REAPER_COMPILER_IR_HIR_VALUE;
            node.type = REAPER_COMPILER_IR_TYPE_BOOL;
            if (strcmp(source_node->text, "true") == 0) node.integer = 1;
            else if (strcmp(source_node->text, "false") == 0) node.integer = 0;
            else {
                return frontend_fail(error, index, source_name,
                    source_node->line, source_node->column,
                    "boolean literal must be true or false");
            }
            break;

        case REAPER_AST_UNARY:
            if (!supported_unary_operator(source_node->text) ||
                left >= index || right != REAPER_AST_NO_NODE) {
                return frontend_fail(error, index, source_name,
                    source_node->line, source_node->column,
                    "native HIR supports unary + and - over one earlier operand");
            }
            if (output[left].type != REAPER_COMPILER_IR_TYPE_I64) {
                return frontend_fail(error, index, source_name,
                    source_node->line, source_node->column,
                    "native unary arithmetic currently requires an i64 operand");
            }
            node.opcode = REAPER_COMPILER_IR_HIR_UNARY;
            node.type = REAPER_COMPILER_IR_TYPE_I64;
            (void)snprintf(node.key, sizeof node.key, "%s", source_node->text);
            node.lhs = left;
            break;

        case REAPER_AST_BINARY:
            if (!supported_binary_operator(source_node->text) ||
                left >= index || right >= index) {
                return frontend_fail(error, index, source_name,
                    source_node->line, source_node->column,
                    "native HIR supports binary +, -, * and / with earlier operands");
            }
            if (output[left].type != REAPER_COMPILER_IR_TYPE_I64 ||
                output[right].type != REAPER_COMPILER_IR_TYPE_I64) {
                return frontend_fail(error, index, source_name,
                    source_node->line, source_node->column,
                    "native binary arithmetic currently requires two i64 operands");
            }
            node.opcode = REAPER_COMPILER_IR_HIR_BINARY;
            node.type = REAPER_COMPILER_IR_TYPE_I64;
            (void)snprintf(node.key, sizeof node.key, "%s", source_node->text);
            node.lhs = left;
            node.rhs = right;
            break;

        case REAPER_AST_IDENTIFIER:
            return frontend_fail(error, index, source_name,
                source_node->line, source_node->column,
                "identifier lowering requires semantic name resolution and is not implicit");
        case REAPER_AST_NULL:
            return frontend_fail(error, index, source_name,
                source_node->line, source_node->column,
                "null/nothing lowering requires an explicit unit/option type contract");
        default:
            return frontend_fail(error, index, source_name,
                source_node->line, source_node->column,
                "AST node kind is not supported by the current native HIR frontend");
        }
        output[index] = node;
    }

    hir->version = REAPER_COMPILER_IR_VERSION;
    hir->stage = REAPER_COMPILER_IR_HIR;
    hir->flags = 0u;
    hir->target[0] = '\0';
    hir->nodes = output;
    hir->length = ast->length;
    if (!reaper_compiler_ir_verify(hir, REAPER_COMPILER_IR_HIR, error)) {
        if (error != NULL && error->node_index < ast->length) {
            const ReaperAstNode *node = &ast->items[error->node_index];
            (void)snprintf(error->span.source, sizeof error->span.source, "%s", source_name);
            error->span.line = node->line <= UINT32_MAX ? (uint32_t)node->line : 0u;
            error->span.column = node->column <= UINT32_MAX ? (uint32_t)node->column : 0u;
        }
        memset(hir, 0, sizeof *hir);
        return 0;
    }
    return 1;
}
