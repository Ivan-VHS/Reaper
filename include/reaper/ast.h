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

typedef enum {
    REAPER_AST_INTEGER = 1,
    REAPER_AST_DECIMAL,
    REAPER_AST_STRING,
    REAPER_AST_BOOLEAN,
    REAPER_AST_NULL,
    REAPER_AST_IDENTIFIER,
    REAPER_AST_UNARY,
    REAPER_AST_BINARY,
    REAPER_AST_CALL,
    REAPER_AST_INDEX,
    REAPER_AST_LIST,
    REAPER_AST_SEQUENCE,
    REAPER_AST_PROGRAM,
    REAPER_AST_DECLARE_IMMUTABLE,
    REAPER_AST_DECLARE_MUTABLE,
    REAPER_AST_CHANGE,
    REAPER_AST_EMIT,
    REAPER_AST_YIELD,
    REAPER_AST_FUNCTION,
    REAPER_AST_BLOCK,
    REAPER_AST_WHEN,
    REAPER_AST_EACH,
    REAPER_AST_WHILE,
    REAPER_AST_EXPRESSION_STATEMENT
} ReaperAstKind;

/*
 * Flat owned AST. Every non-sentinel child index points to an earlier node.
 *
 * CALL: left=callee, right=argument SEQUENCE
 * LIST: left=item SEQUENCE
 * SEQUENCE: left=item, right=next SEQUENCE or NO_NODE
 * PROGRAM/BLOCK: left=statement SEQUENCE or NO_NODE
 * DECLARE/CHANGE/EMIT/YIELD/EXPRESSION_STATEMENT: left=value or NO_NODE
 * FUNCTION: text=name, left=parameter SEQUENCE, right=BLOCK
 * WHEN: left=condition, right=SEQUENCE containing one/two BLOCK nodes
 * EACH: text=iterator, left=iterable, right=BLOCK
 * WHILE: left=condition, right=BLOCK
 */
typedef struct {
    ReaperAstKind kind;
    uint32_t left;
    uint32_t right;
    char *text;
    size_t line;
    size_t column;
} ReaperAstNode;

typedef struct {
    ReaperAstNode *items;
    size_t length;
    size_t capacity;
    uint32_t root;
} ReaperAst;

typedef struct {
    char message[256];
    size_t line;
    size_t column;
} ReaperParseError;

/* Parse a single expression. Kept for expression-level compiler clients. */
int reaper_parse_expression(
    const ReaperTokenArray *tokens,
    ReaperAst *out,
    ReaperParseError *error
);

/* Parse complete source programs, including declarations and control flow. */
int reaper_parse_program(
    const ReaperTokenArray *tokens,
    ReaperAst *out,
    ReaperParseError *error
);

void reaper_ast_free(ReaperAst *ast);
const char *reaper_ast_kind_name(ReaperAstKind kind);

/* Write deterministic JSON; reject malformed ASTs before output. */
int reaper_ast_write_json(const ReaperAst *ast, FILE *output);

#ifdef __cplusplus
}
#endif

#endif
