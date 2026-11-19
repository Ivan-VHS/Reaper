#include "reaper/parser.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    const ReaperTokenArray *tokens;
    size_t pos;
    ReaperAst *ast;
    ReaperParseError *error;
} Parser;

static const ReaperToken *peek(Parser *p) {
    if (p->pos >= p->tokens->length) return NULL;
    return &p->tokens->items[p->pos];
}
static const ReaperToken *previous(Parser *p) {
    if (p->pos == 0 || p->pos > p->tokens->length) return NULL;
    return &p->tokens->items[p->pos - 1];
}
static int is_text(Parser *p, const char *s) {
    const ReaperToken *t = peek(p);
    return t && strcmp(t->text, s) == 0;
}
static int fail(Parser *p, const ReaperToken *t, const char *message) {
    if (p->error) {
        (void)snprintf(p->error->message, sizeof p->error->message, "%s", message);
        p->error->line = t ? t->line : 1;
        p->error->column = t ? t->column : 1;
    }
    return 0;
}
static char *copy_text(const char *s) {
    size_t n = strlen(s);
    char *r = malloc(n + 1);
    if (r) memcpy(r, s, n + 1);
    return r;
}
static uint32_t add_node(Parser *p, ReaperAstKind kind, const char *text,
                         uint32_t left, uint32_t right,
                         size_t line, size_t column) {
    if (p->ast->length == p->ast->capacity) {
        size_t cap = p->ast->capacity ? p->ast->capacity * 2 : 32;
        if (cap < p->ast->capacity || cap > SIZE_MAX / sizeof *p->ast->nodes) return REAPER_AST_NO_NODE;
        ReaperAstNode *nodes = realloc(p->ast->nodes, cap * sizeof *nodes);
        if (!nodes) return REAPER_AST_NO_NODE;
        p->ast->nodes = nodes;
        p->ast->capacity = cap;
    }
    char *owned = copy_text(text ? text : "");
    if (!owned) return REAPER_AST_NO_NODE;
    uint32_t id = (uint32_t)p->ast->length;
    if ((size_t)id != p->ast->length) { free(owned); return REAPER_AST_NO_NODE; }
    p->ast->nodes[p->ast->length++] = (ReaperAstNode){
        kind, owned, left, right, REAPER_AST_NO_NODE, REAPER_AST_NO_NODE, line, column
    };
    return id;
}
static int precedence(const char *op) {
    if (!strcmp(op, "or") || !strcmp(op, "||")) return 1;
    if (!strcmp(op, "and") || !strcmp(op, "&&")) return 2;
    if (!strcmp(op, "==") || !strcmp(op, "!=") || !strcmp(op, "<") ||
        !strcmp(op, ">") || !strcmp(op, "<=") || !strcmp(op, ">=")) return 3;
    if (!strcmp(op, "~>") || !strcmp(op, "|>")) return 4;
    if (!strcmp(op, "+") || !strcmp(op, "-") || !strcmp(op, "++") ||
        !strcmp(op, "+%") || !strcmp(op, "+|")) return 5;
    if (!strcmp(op, "*") || !strcmp(op, "/") || !strcmp(op, "%")) return 6;
    if (!strcmp(op, "**")) return 7;
    return 0;
}
static uint32_t parse_bp(Parser *p, int min_bp);

static uint32_t parse_primary(Parser *p) {
    const ReaperToken *t = peek(p);
    if (!t) { (void)fail(p, t, "expected expression"); return REAPER_AST_NO_NODE; }
    if (!strcmp(t->text, "-") || !strcmp(t->text, "+") || !strcmp(t->text, "not") || !strcmp(t->text, "!")) {
        char op[16];
        (void)snprintf(op, sizeof op, "%s", t->text);
        ++p->pos;
        uint32_t operand = parse_bp(p, 7);
        if (operand == REAPER_AST_NO_NODE) return operand;
        uint32_t id = add_node(p, REAPER_AST_UNARY, op, operand, REAPER_AST_NO_NODE, t->line, t->column);
        if (id == REAPER_AST_NO_NODE) (void)fail(p, t, "out of memory while building AST");
        return id;
    }
    if (!strcmp(t->text, "(")) {
        ++p->pos;
        uint32_t inner = parse_bp(p, 1);
        if (inner == REAPER_AST_NO_NODE) return inner;
        if (!is_text(p, ")")) { (void)fail(p, peek(p), "expected ')' after expression"); return REAPER_AST_NO_NODE; }
        ++p->pos;
        return inner;
    }
    ReaperAstKind kind;
    if (t->kind == REAPER_TOK_NUMBER) kind = REAPER_AST_NUMBER;
    else if (t->kind == REAPER_TOK_STRING) kind = REAPER_AST_STRING;
    else if (t->kind == REAPER_TOK_IDENTIFIER) kind = REAPER_AST_IDENTIFIER;
    else if (!strcmp(t->text, "true") || !strcmp(t->text, "false")) kind = REAPER_AST_BOOLEAN;
    else if (!strcmp(t->text, "nothing")) kind = REAPER_AST_NOTHING;
    else { (void)fail(p, t, "expected a literal, identifier, unary expression or '('"); return REAPER_AST_NO_NODE; }
    ++p->pos;
    uint32_t id = add_node(p, kind, t->text, REAPER_AST_NO_NODE, REAPER_AST_NO_NODE, t->line, t->column);
    if (id == REAPER_AST_NO_NODE) (void)fail(p, t, "out of memory while building AST");
    return id;
}
static uint32_t parse_postfix(Parser *p) {
    uint32_t value = parse_primary(p);
    if (value == REAPER_AST_NO_NODE) return value;
    while (is_text(p, "(")) {
        const ReaperToken *open = peek(p);
        ++p->pos;
        uint32_t call = add_node(p, REAPER_AST_CALL, "call", value, REAPER_AST_NO_NODE,
                                 open->line, open->column);
        if (call == REAPER_AST_NO_NODE) { (void)fail(p, open, "out of memory while building AST"); return call; }
        uint32_t first = REAPER_AST_NO_NODE, last = REAPER_AST_NO_NODE;
        if (!is_text(p, ")")) {
            for (;;) {
                uint32_t arg = parse_bp(p, 1);
                if (arg == REAPER_AST_NO_NODE) return arg;
                if (first == REAPER_AST_NO_NODE) first = arg;
                else p->ast->nodes[last].next_sibling = arg;
                last = arg;
                if (!is_text(p, ",")) break;
                ++p->pos;
            }
        }
        if (!is_text(p, ")")) { (void)fail(p, peek(p), "expected ')' after call arguments"); return REAPER_AST_NO_NODE; }
        ++p->pos;
        p->ast->nodes[call].first_argument = first;
        value = call;
    }
    return value;
}
static uint32_t parse_bp(Parser *p, int min_bp) {
    uint32_t lhs = parse_postfix(p);
    if (lhs == REAPER_AST_NO_NODE) return lhs;
    for (;;) {
        const ReaperToken *op = peek(p);
        if (!op) break;
        int prec = precedence(op->text);
        if (prec < min_bp || prec == 0) break;
        ++p->pos;
        int next_min = prec + (strcmp(op->text, "**") == 0 ? 0 : 1);
        uint32_t rhs = parse_bp(p, next_min);
        if (rhs == REAPER_AST_NO_NODE) return rhs;
        uint32_t node = add_node(p, REAPER_AST_BINARY, op->text, lhs, rhs, op->line, op->column);
        if (node == REAPER_AST_NO_NODE) { (void)fail(p, op, "out of memory while building AST"); return node; }
        lhs = node;
    }
    return lhs;
}
int reaper_parse_expression(const ReaperTokenArray *tokens, ReaperAst *out, ReaperParseError *error) {
    if (!tokens || !out || tokens->length == 0) {
        if (error) { (void)snprintf(error->message, sizeof error->message, "tokens and output are required"); error->line=1; error->column=1; }
        return 0;
    }
    memset(out, 0, sizeof *out);
    out->root = REAPER_AST_NO_NODE;
    if (error) memset(error, 0, sizeof *error);
    Parser p = { tokens, 0, out, error };
    while (is_text(&p, "\n")) ++p.pos;
    out->root = parse_bp(&p, 1);
    if (out->root == REAPER_AST_NO_NODE) { reaper_ast_free(out); return 0; }
    while (is_text(&p, "\n")) ++p.pos;
    if (peek(&p) && peek(&p)->kind != REAPER_TOK_EOF) {
        (void)fail(&p, peek(&p), "unexpected token after expression");
        reaper_ast_free(out);
        return 0;
    }
    return 1;
}
void reaper_ast_free(ReaperAst *ast) {
    if (!ast) return;
    for (size_t i=0; i<ast->length; ++i) free(ast->nodes[i].text);
    free(ast->nodes);
    memset(ast, 0, sizeof *ast);
    ast->root = REAPER_AST_NO_NODE;
}
const char *reaper_ast_kind_name(ReaperAstKind kind) {
    switch(kind) {
        case REAPER_AST_NUMBER: return "NUMBER";
        case REAPER_AST_STRING: return "STRING";
        case REAPER_AST_IDENTIFIER: return "IDENTIFIER";
        case REAPER_AST_BOOLEAN: return "BOOLEAN";
        case REAPER_AST_NOTHING: return "NOTHING";
        case REAPER_AST_UNARY: return "UNARY";
        case REAPER_AST_BINARY: return "BINARY";
        case REAPER_AST_CALL: return "CALL";
        default: return "UNKNOWN";
    }
}
