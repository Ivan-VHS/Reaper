#ifndef REAPER_PARSER_H
#define REAPER_PARSER_H

#include "reaper/lexer.h"
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_AST_NO_NODE UINT32_MAX

typedef enum {
    REAPER_AST_NUMBER = 1,
    REAPER_AST_STRING,
    REAPER_AST_IDENTIFIER,
    REAPER_AST_BOOLEAN,
    REAPER_AST_NOTHING,
    REAPER_AST_UNARY,
    REAPER_AST_BINARY,
    REAPER_AST_CALL
} ReaperAstKind;

typedef struct {
    ReaperAstKind kind;
    char *text;
    uint32_t left;
    uint32_t right;
    uint32_t first_argument;
    uint32_t next_sibling;
    size_t line;
    size_t column;
} ReaperAstNode;

typedef struct {
    ReaperAstNode *nodes;
    size_t length;
    size_t capacity;
    uint32_t root;
} ReaperAst;

typedef struct {
    char message[256];
    size_t line;
    size_t column;
} ReaperParseError;

/* Parse one expression from a token stream. AST text is copied and owned by
 * the AST; the token stream may be released after this function returns. */
int reaper_parse_expression(const ReaperTokenArray *tokens,
                            ReaperAst *out,
                            ReaperParseError *error);
void reaper_ast_free(ReaperAst *ast);
const char *reaper_ast_kind_name(ReaperAstKind kind);

#ifdef __cplusplus
}
#endif
#endif
