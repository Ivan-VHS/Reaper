#include "reaper/ast.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int write_string(FILE *out, const char *s) {
    static const char hex[] = "0123456789abcdef";
    if (fputc('"', out) == EOF) return 0;
    for (const unsigned char *p = (const unsigned char *)s; *p; ++p) {
        unsigned char c = *p;
        if (c == '"' || c == '\\') {
            if (fputc('\\', out) == EOF || fputc(c, out) == EOF) return 0;
        } else if (c < 0x20u) {
            if (fputs("\\u00", out) == EOF ||
                fputc(hex[c >> 4], out) == EOF ||
                fputc(hex[c & 0x0fu], out) == EOF) return 0;
        } else if (fputc(c, out) == EOF) {
            return 0;
        }
    }
    return fputc('"', out) != EOF;
}

static int valid_node(const ReaperAst *ast, size_t i) {
    const ReaperAstNode *n = &ast->items[i];
    if (!n->text || n->source_end_byte < n->source_start_byte ||
        strcmp(reaper_ast_kind_name(n->kind), "invalid") == 0) return 0;
    switch (n->kind) {
        case REAPER_AST_INTEGER: case REAPER_AST_DECIMAL:
        case REAPER_AST_STRING: case REAPER_AST_BOOLEAN:
        case REAPER_AST_NULL: case REAPER_AST_IDENTIFIER:
            return n->left == REAPER_AST_NO_NODE && n->right == REAPER_AST_NO_NODE;
        case REAPER_AST_UNARY:
            return n->left < i && n->right == REAPER_AST_NO_NODE;
        case REAPER_AST_BINARY:
            return n->left < i && n->right < i;
        default: return 0;
    }
}

int reaper_ast_write_json(const ReaperAst *ast, FILE *output) {
    if (!ast || !output || !ast->items || ast->length == 0 ||
        ast->root >= ast->length || ast->length > UINT32_MAX) return 0;
    for (size_t i = 0; i < ast->length; ++i)
        if (!valid_node(ast, i)) return 0;
    if (fprintf(output, "{\"root\":%u,\"nodes\":[", ast->root) < 0) return 0;
    for (size_t i = 0; i < ast->length; ++i) {
        const ReaperAstNode *n = &ast->items[i];
        if (i && fputc(',', output) == EOF) return 0;
        if (fprintf(output, "{\"id\":%zu,\"kind\":", i) < 0 ||
            !write_string(output, reaper_ast_kind_name(n->kind)) ||
            fputs(",\"text\":", output) == EOF || !write_string(output, n->text)) return 0;
        if (n->left == REAPER_AST_NO_NODE) {
            if (fputs(",\"left\":null", output) == EOF) return 0;
        } else if (fprintf(output, ",\"left\":%u", n->left) < 0) return 0;
        if (n->right == REAPER_AST_NO_NODE) {
            if (fputs(",\"right\":null", output) == EOF) return 0;
        } else if (fprintf(output, ",\"right\":%u", n->right) < 0) return 0;
        if (fprintf(output,
                ",\"line\":%zu,\"column\":%zu,"
                "\"source_start_byte\":%zu,\"source_end_byte\":%zu}",
                n->line, n->column, n->source_start_byte,
                n->source_end_byte) < 0) return 0;
    }
    return fputs("]}\n", output) != EOF && !ferror(output);
}
