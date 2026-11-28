#ifndef REAPER_AST_H
#define REAPER_AST_H
#include "reaper/lexer.h"
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#ifdef __cplusplus
extern "C" {
#endif
#define REAPER_AST_NO_NODE UINT32_MAX
typedef enum { REAPER_AST_INTEGER=1, REAPER_AST_DECIMAL, REAPER_AST_STRING, REAPER_AST_BOOLEAN, REAPER_AST_NULL, REAPER_AST_IDENTIFIER, REAPER_AST_UNARY, REAPER_AST_BINARY } ReaperAstKind;
typedef struct { ReaperAstKind kind; uint32_t left; uint32_t right; char *text; size_t line; size_t column; size_t source_start_byte; size_t source_end_byte; } ReaperAstNode;
typedef struct { ReaperAstNode *items; size_t length; size_t capacity; uint32_t root; } ReaperAst;
typedef struct { char message[256]; size_t line; size_t column; } ReaperParseError;
int reaper_parse_expression(const ReaperTokenArray *tokens, ReaperAst *out, ReaperParseError *error);
void reaper_ast_free(ReaperAst *ast);
const char *reaper_ast_kind_name(ReaperAstKind kind);
/* Write deterministic JSON; reject malformed ASTs before output. */
int reaper_ast_write_json(const ReaperAst *ast, FILE *output);
#ifdef __cplusplus
}
#endif
#endif
