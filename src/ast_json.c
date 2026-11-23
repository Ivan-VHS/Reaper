#include "reaper/ast.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int write_string(FILE *output, const char *value) {
    static const char hex[] = "0123456789abcdef";
    if (fputc('"', output) == EOF) return 0;

    for (const unsigned char *cursor = (const unsigned char *)value;
         *cursor != 0U; ++cursor) {
        unsigned char byte = *cursor;
        if (byte == '"' || byte == '\\') {
            if (fputc('\\', output) == EOF ||
                fputc(byte, output) == EOF) return 0;
        } else if (byte < 0x20U) {
            if (fputs("\\u00", output) == EOF ||
                fputc(hex[byte >> 4], output) == EOF ||
                fputc(hex[byte & 0x0fU], output) == EOF) return 0;
        } else if (fputc(byte, output) == EOF) {
            return 0;
        }
    }
    return fputc('"', output) != EOF;
}

static int earlier_ref(uint32_t reference, size_t current) {
    return reference != REAPER_AST_NO_NODE && (size_t)reference < current;
}

static int optional_ref(uint32_t reference, size_t current) {
    return reference == REAPER_AST_NO_NODE || earlier_ref(reference, current);
}

static int sequence_ref(const ReaperAst *ast, uint32_t reference, size_t current) {
    return reference == REAPER_AST_NO_NODE ||
        (earlier_ref(reference, current) &&
         ast->items[reference].kind == REAPER_AST_SEQUENCE);
}

static int block_ref(const ReaperAst *ast, uint32_t reference, size_t current) {
    return earlier_ref(reference, current) &&
        ast->items[reference].kind == REAPER_AST_BLOCK;
}

static int valid_node(const ReaperAst *ast, size_t index) {
    const ReaperAstNode *node = &ast->items[index];
    if (node->text == NULL ||
        strcmp(reaper_ast_kind_name(node->kind), "invalid") == 0) {
        return 0;
    }

    switch (node->kind) {
    case REAPER_AST_INTEGER:
    case REAPER_AST_DECIMAL:
    case REAPER_AST_STRING:
    case REAPER_AST_BOOLEAN:
    case REAPER_AST_NULL:
    case REAPER_AST_IDENTIFIER:
        return node->left == REAPER_AST_NO_NODE &&
            node->right == REAPER_AST_NO_NODE;

    case REAPER_AST_UNARY:
        return earlier_ref(node->left, index) &&
            node->right == REAPER_AST_NO_NODE;

    case REAPER_AST_BINARY:
        return earlier_ref(node->left, index) &&
            earlier_ref(node->right, index);

    case REAPER_AST_CALL:
        return earlier_ref(node->left, index) &&
            sequence_ref(ast, node->right, index);

    case REAPER_AST_INDEX:
        return earlier_ref(node->left, index) &&
            earlier_ref(node->right, index);

    case REAPER_AST_LIST:
    case REAPER_AST_PROGRAM:
    case REAPER_AST_BLOCK:
        return sequence_ref(ast, node->left, index) &&
            node->right == REAPER_AST_NO_NODE;

    case REAPER_AST_SEQUENCE:
        return earlier_ref(node->left, index) &&
            sequence_ref(ast, node->right, index);

    case REAPER_AST_DECLARE_IMMUTABLE:
    case REAPER_AST_DECLARE_MUTABLE:
    case REAPER_AST_CHANGE:
    case REAPER_AST_EMIT:
    case REAPER_AST_EXPRESSION_STATEMENT:
        return earlier_ref(node->left, index) &&
            node->right == REAPER_AST_NO_NODE;

    case REAPER_AST_YIELD:
        return optional_ref(node->left, index) &&
            node->right == REAPER_AST_NO_NODE;

    case REAPER_AST_FUNCTION:
        return sequence_ref(ast, node->left, index) &&
            block_ref(ast, node->right, index);

    case REAPER_AST_WHEN:
        return earlier_ref(node->left, index) &&
            sequence_ref(ast, node->right, index) &&
            node->right != REAPER_AST_NO_NODE;

    case REAPER_AST_EACH:
    case REAPER_AST_WHILE:
        return earlier_ref(node->left, index) &&
            block_ref(ast, node->right, index);

    default:
        return 0;
    }
}

int reaper_ast_write_json(const ReaperAst *ast, FILE *output) {
    if (ast == NULL || output == NULL || ast->items == NULL ||
        ast->length == 0U || ast->root >= ast->length ||
        ast->length > UINT32_MAX) {
        return 0;
    }

    for (size_t i = 0U; i < ast->length; ++i) {
        if (!valid_node(ast, i)) return 0;
    }

    if (fprintf(output, "{\"root\":%u,\"nodes\":[", ast->root) < 0)
        return 0;

    for (size_t i = 0U; i < ast->length; ++i) {
        const ReaperAstNode *node = &ast->items[i];
        if (i != 0U && fputc(',', output) == EOF) return 0;
        if (fprintf(output, "{\"id\":%zu,\"kind\":", i) < 0 ||
            !write_string(output, reaper_ast_kind_name(node->kind)) ||
            fputs(",\"text\":", output) == EOF ||
            !write_string(output, node->text)) {
            return 0;
        }
        if (node->left == REAPER_AST_NO_NODE) {
            if (fputs(",\"left\":null", output) == EOF) return 0;
        } else if (fprintf(output, ",\"left\":%u", node->left) < 0) {
            return 0;
        }
        if (node->right == REAPER_AST_NO_NODE) {
            if (fputs(",\"right\":null", output) == EOF) return 0;
        } else if (fprintf(output, ",\"right\":%u", node->right) < 0) {
            return 0;
        }
        if (fprintf(
                output,
                ",\"line\":%zu,\"column\":%zu}",
                node->line,
                node->column
            ) < 0) {
            return 0;
        }
    }

    return fputs("]}\n", output) != EOF && !ferror(output);
}
