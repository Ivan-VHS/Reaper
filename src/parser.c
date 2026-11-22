#include "reaper/ast.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REAPER_PARSE_MAX_DEPTH 256u

typedef struct {
    uint32_t *items;
    size_t length;
    size_t capacity;
} NodeVector;

typedef struct {
    const ReaperTokenArray *tokens;
    size_t pos;
    unsigned depth;
    ReaperAst *ast;
    ReaperParseError *error;
    ReaperParseError local_error;
} Parser;

static const ReaperToken *peek(Parser *parser) {
    if (parser->pos >= parser->tokens->length) return NULL;
    return &parser->tokens->items[parser->pos];
}

static const char *peek_text(Parser *parser) {
    const ReaperToken *token = peek(parser);
    if (token == NULL) return "";
    return reaper_token_canonical_text(token);
}

static int is_eof(Parser *parser) {
    const ReaperToken *token = peek(parser);
    return token == NULL || token->kind == REAPER_TOK_EOF;
}

static int is_newline(Parser *parser) {
    const ReaperToken *token = peek(parser);
    return token != NULL && token->kind == REAPER_TOK_NEWLINE;
}

static int token_is(Parser *parser, const char *text) {
    return strcmp(peek_text(parser), text) == 0;
}

static int token_kind_is(Parser *parser, ReaperTokenKind kind) {
    const ReaperToken *token = peek(parser);
    return token != NULL && token->kind == kind;
}

static void set_error_at(
    Parser *parser,
    const ReaperToken *token,
    const char *message
) {
    if (parser->error == NULL || parser->error->message[0] != '\0') return;

    (void)snprintf(
        parser->error->message,
        sizeof parser->error->message,
        "%s",
        message
    );
    parser->error->line = token != NULL ? token->line : 1U;
    parser->error->column = token != NULL ? token->column : 1U;
}

static int parse_fail(Parser *parser, const char *message) {
    set_error_at(parser, peek(parser), message);
    return 0;
}

static uint32_t add_node(
    Parser *parser,
    ReaperAstKind kind,
    const char *text,
    uint32_t left,
    uint32_t right,
    size_t line,
    size_t column
) {
    if (parser->ast->length >= UINT32_MAX) {
        (void)parse_fail(parser, "AST node index limit exceeded");
        return REAPER_AST_NO_NODE;
    }

    if (parser->ast->length == parser->ast->capacity) {
        size_t next = parser->ast->capacity == 0U
            ? 32U : parser->ast->capacity * 2U;
        if (next < parser->ast->capacity ||
            next > SIZE_MAX / sizeof *parser->ast->items) {
            (void)parse_fail(parser, "AST storage size overflow");
            return REAPER_AST_NO_NODE;
        }

        ReaperAstNode *items = realloc(
            parser->ast->items,
            next * sizeof *parser->ast->items
        );
        if (items == NULL) {
            (void)parse_fail(parser, "out of memory building AST");
            return REAPER_AST_NO_NODE;
        }
        parser->ast->items = items;
        parser->ast->capacity = next;
    }

    size_t text_length = text != NULL ? strlen(text) : 0U;
    char *copy = malloc(text_length + 1U);
    if (copy == NULL) {
        (void)parse_fail(parser, "out of memory copying AST text");
        return REAPER_AST_NO_NODE;
    }
    if (text_length != 0U) memcpy(copy, text, text_length);
    copy[text_length] = '\0';

    uint32_t id = (uint32_t)parser->ast->length;
    parser->ast->items[parser->ast->length++] = (ReaperAstNode) {
        kind, left, right, copy, line, column
    };
    return id;
}

static int vector_push(NodeVector *vector, uint32_t node) {
    if (node == REAPER_AST_NO_NODE) return 0;

    if (vector->length == vector->capacity) {
        size_t next = vector->capacity == 0U
            ? 8U : vector->capacity * 2U;
        if (next < vector->capacity ||
            next > SIZE_MAX / sizeof *vector->items) {
            return 0;
        }
        uint32_t *items = realloc(vector->items, next * sizeof *items);
        if (items == NULL) return 0;
        vector->items = items;
        vector->capacity = next;
    }

    vector->items[vector->length++] = node;
    return 1;
}

static void vector_free(NodeVector *vector) {
    if (vector == NULL) return;
    free(vector->items);
    memset(vector, 0, sizeof *vector);
}

static uint32_t make_sequence(
    Parser *parser,
    const NodeVector *items,
    size_t line,
    size_t column
) {
    uint32_t head = REAPER_AST_NO_NODE;
    for (size_t i = items->length; i > 0U; --i) {
        uint32_t next = add_node(
            parser,
            REAPER_AST_SEQUENCE,
            "",
            items->items[i - 1U],
            head,
            line,
            column
        );
        if (next == REAPER_AST_NO_NODE) return REAPER_AST_NO_NODE;
        head = next;
    }
    return head;
}

static void skip_newlines(Parser *parser) {
    while (is_newline(parser)) ++parser->pos;
}

static int consume_text(Parser *parser, const char *text, const char *message) {
    if (token_is(parser, text)) {
        ++parser->pos;
        return 1;
    }
    return parse_fail(parser, message);
}

static int consume_kind(
    Parser *parser,
    ReaperTokenKind kind,
    const char *message
) {
    if (token_kind_is(parser, kind)) {
        ++parser->pos;
        return 1;
    }
    return parse_fail(parser, message);
}

static int statement_end(Parser *parser) {
    if (is_newline(parser)) {
        skip_newlines(parser);
        return 1;
    }
    if (token_is(parser, "}") || is_eof(parser)) return 1;
    return parse_fail(parser, "expected a new line after this statement");
}

static int precedence(const char *operator_text) {
    if (strcmp(operator_text, "::") == 0) return 1;
    if (strcmp(operator_text, "??") == 0) return 2;
    if (strcmp(operator_text, "or") == 0 ||
        strcmp(operator_text, "||") == 0) return 2;
    if (strcmp(operator_text, "and") == 0 ||
        strcmp(operator_text, "&&") == 0) return 3;
    if (strcmp(operator_text, "==") == 0 ||
        strcmp(operator_text, "!=") == 0 ||
        strcmp(operator_text, "<") == 0 ||
        strcmp(operator_text, "<=") == 0 ||
        strcmp(operator_text, ">") == 0 ||
        strcmp(operator_text, ">=") == 0) return 4;
    if (strcmp(operator_text, "++") == 0) return 5;
    if (strcmp(operator_text, "+") == 0 ||
        strcmp(operator_text, "-") == 0) return 6;
    if (strcmp(operator_text, "*") == 0 ||
        strcmp(operator_text, "/") == 0 ||
        strcmp(operator_text, "//") == 0 ||
        strcmp(operator_text, "%") == 0) return 7;
    if (strcmp(operator_text, "**") == 0) return 8;
    return 0;
}

static uint32_t parse_expression_bp(Parser *parser, int minimum);
static uint32_t parse_statement(Parser *parser);
static uint32_t parse_block(Parser *parser);

static uint32_t parse_expression_items(
    Parser *parser,
    const char *closing,
    const char *error_message,
    size_t line,
    size_t column
) {
    NodeVector items = {0};
    skip_newlines(parser);

    if (!token_is(parser, closing)) {
        for (;;) {
            uint32_t expression = parse_expression_bp(parser, 1);
            if (expression == REAPER_AST_NO_NODE ||
                !vector_push(&items, expression)) {
                vector_free(&items);
                if (expression != REAPER_AST_NO_NODE)
                    (void)parse_fail(parser, "out of memory collecting expression items");
                return REAPER_AST_NO_NODE;
            }

            skip_newlines(parser);
            if (!token_is(parser, ",")) break;
            ++parser->pos;
            skip_newlines(parser);
        }
    }

    if (!consume_text(parser, closing, error_message)) {
        vector_free(&items);
        return REAPER_AST_NO_NODE;
    }

    uint32_t sequence = make_sequence(parser, &items, line, column);
    vector_free(&items);
    return sequence;
}

static uint32_t parse_call(Parser *parser, uint32_t callee, size_t line, size_t column) {
    ++parser->pos; /* '(' */
    uint32_t arguments = parse_expression_items(
        parser, ")", "expected ')' after arguments", line, column
    );
    if (parser->error != NULL && parser->error->message[0] != '\0')
        return REAPER_AST_NO_NODE;

    return add_node(
        parser, REAPER_AST_CALL, "", callee, arguments, line, column
    );
}

static uint32_t parse_index(Parser *parser, uint32_t target, size_t line, size_t column) {
    ++parser->pos; /* '[' */
    uint32_t index = parse_expression_bp(parser, 1);
    if (index == REAPER_AST_NO_NODE) return REAPER_AST_NO_NODE;
    if (!consume_text(parser, "]", "expected ']' after index"))
        return REAPER_AST_NO_NODE;

    return add_node(
        parser, REAPER_AST_INDEX, "", target, index, line, column
    );
}

static uint32_t parse_primary(Parser *parser) {
    const ReaperToken *token = peek(parser);
    if (token == NULL) {
        (void)parse_fail(parser, "unexpected end of token stream");
        return REAPER_AST_NO_NODE;
    }

    if (token->kind == REAPER_TOK_CATALOG_OPERATOR) {
        (void)parse_fail(
            parser,
            "catalogue operator is reserved; executable semantics are not registered"
        );
        return REAPER_AST_NO_NODE;
    }

    if (token_is(parser, "-") || token_is(parser, "+") ||
        token_is(parser, "not") || token_is(parser, "!")) {
        const char *operator_text = peek_text(parser);
        size_t line = token->line;
        size_t column = token->column;
        ++parser->pos;

        uint32_t operand = parse_expression_bp(parser, 9);
        if (operand == REAPER_AST_NO_NODE) return REAPER_AST_NO_NODE;
        return add_node(
            parser, REAPER_AST_UNARY, operator_text,
            operand, REAPER_AST_NO_NODE, line, column
        );
    }

    if (token_is(parser, "(")) {
        ++parser->pos;
        uint32_t expression = parse_expression_bp(parser, 1);
        if (expression == REAPER_AST_NO_NODE) return REAPER_AST_NO_NODE;
        if (!consume_text(parser, ")", "expected ')' to close expression"))
            return REAPER_AST_NO_NODE;
        return expression;
    }

    if (token_is(parser, "[")) {
        size_t line = token->line;
        size_t column = token->column;
        ++parser->pos;
        uint32_t items = parse_expression_items(
            parser, "]", "expected ']' after list", line, column
        );
        if (parser->error != NULL && parser->error->message[0] != '\0')
            return REAPER_AST_NO_NODE;
        return add_node(
            parser, REAPER_AST_LIST, "", items, REAPER_AST_NO_NODE, line, column
        );
    }

    ReaperAstKind kind;
    if (token->kind == REAPER_TOK_NUMBER) {
        kind = strchr(token->text, '.') != NULL
            ? REAPER_AST_DECIMAL : REAPER_AST_INTEGER;
    } else if (token->kind == REAPER_TOK_STRING) {
        kind = REAPER_AST_STRING;
    } else if (token->kind == REAPER_TOK_IDENTIFIER) {
        kind = REAPER_AST_IDENTIFIER;
    } else if (token->kind == REAPER_TOK_KEYWORD &&
        (strcmp(peek_text(parser), "true") == 0 ||
         strcmp(peek_text(parser), "false") == 0)) {
        kind = REAPER_AST_BOOLEAN;
    } else if (token->kind == REAPER_TOK_KEYWORD &&
        strcmp(peek_text(parser), "nothing") == 0) {
        kind = REAPER_AST_NULL;
    } else {
        (void)parse_fail(
            parser,
            "expected a literal, identifier, list or parenthesized expression"
        );
        return REAPER_AST_NO_NODE;
    }

    uint32_t node = add_node(
        parser, kind, token->text,
        REAPER_AST_NO_NODE, REAPER_AST_NO_NODE,
        token->line, token->column
    );
    if (node == REAPER_AST_NO_NODE) return node;
    ++parser->pos;
    return node;
}

static uint32_t parse_expression_bp(Parser *parser, int minimum) {
    if (++parser->depth > REAPER_PARSE_MAX_DEPTH) {
        --parser->depth;
        (void)parse_fail(parser, "expression nesting limit exceeded");
        return REAPER_AST_NO_NODE;
    }

    uint32_t left = parse_primary(parser);
    if (left == REAPER_AST_NO_NODE) {
        --parser->depth;
        return REAPER_AST_NO_NODE;
    }

    for (;;) {
        const ReaperToken *token = peek(parser);
        if (token == NULL) break;

        if (token->kind == REAPER_TOK_CATALOG_OPERATOR) {
            (void)parse_fail(
                parser,
                "catalogue operator is reserved; executable semantics are not registered"
            );
            left = REAPER_AST_NO_NODE;
            break;
        }

        if (token_is(parser, "(")) {
            size_t line = token->line;
            size_t column = token->column;
            left = parse_call(parser, left, line, column);
            if (left == REAPER_AST_NO_NODE) break;
            continue;
        }

        if (token_is(parser, "[")) {
            size_t line = token->line;
            size_t column = token->column;
            left = parse_index(parser, left, line, column);
            if (left == REAPER_AST_NO_NODE) break;
            continue;
        }

        int binding_power = precedence(peek_text(parser));
        if (binding_power == 0 || binding_power < minimum) break;

        char operator_copy[16];
        const char *canonical_operator = peek_text(parser);
        size_t operator_length = strlen(canonical_operator);
        if (operator_length >= sizeof operator_copy) {
            (void)parse_fail(parser, "operator spelling exceeds parser limit");
            left = REAPER_AST_NO_NODE;
            break;
        }
        memcpy(operator_copy, canonical_operator, operator_length + 1U);

        size_t line = token->line;
        size_t column = token->column;
        ++parser->pos;
        skip_newlines(parser);

        int next_minimum = binding_power + (strcmp(operator_copy, "**") == 0 ? 0 : 1);
        uint32_t right = parse_expression_bp(parser, next_minimum);
        if (right == REAPER_AST_NO_NODE) {
            left = REAPER_AST_NO_NODE;
            break;
        }

        left = add_node(
            parser, REAPER_AST_BINARY, operator_copy,
            left, right, line, column
        );
        if (left == REAPER_AST_NO_NODE) break;
    }

    --parser->depth;
    return left;
}

static uint32_t parse_block(Parser *parser) {
    const ReaperToken *opening = peek(parser);
    if (!consume_text(parser, "{", "expected '{' to start a block"))
        return REAPER_AST_NO_NODE;

    NodeVector statements = {0};
    skip_newlines(parser);

    while (!is_eof(parser) && !token_is(parser, "}")) {
        uint32_t statement = parse_statement(parser);
        if (statement == REAPER_AST_NO_NODE ||
            !vector_push(&statements, statement)) {
            vector_free(&statements);
            if (statement != REAPER_AST_NO_NODE)
                (void)parse_fail(parser, "out of memory collecting block statements");
            return REAPER_AST_NO_NODE;
        }
        if (!statement_end(parser)) {
            vector_free(&statements);
            return REAPER_AST_NO_NODE;
        }
    }

    if (!consume_text(parser, "}", "expected '}' after block")) {
        vector_free(&statements);
        return REAPER_AST_NO_NODE;
    }

    uint32_t sequence = make_sequence(
        parser, &statements, opening->line, opening->column
    );
    vector_free(&statements);
    if (parser->error != NULL && parser->error->message[0] != '\0')
        return REAPER_AST_NO_NODE;

    return add_node(
        parser, REAPER_AST_BLOCK, "", sequence, REAPER_AST_NO_NODE,
        opening->line, opening->column
    );
}

static uint32_t parse_function(Parser *parser, const ReaperToken *keyword) {
    ++parser->pos;
    const ReaperToken *name = peek(parser);
    if (!consume_kind(parser, REAPER_TOK_IDENTIFIER, "expected a function name after 'craft'"))
        return REAPER_AST_NO_NODE;
    if (!consume_text(parser, "(", "expected '(' after function name"))
        return REAPER_AST_NO_NODE;

    NodeVector parameters = {0};
    skip_newlines(parser);
    if (!token_is(parser, ")")) {
        for (;;) {
            const ReaperToken *parameter = peek(parser);
            if (!consume_kind(parser, REAPER_TOK_IDENTIFIER, "expected a parameter name")) {
                vector_free(&parameters);
                return REAPER_AST_NO_NODE;
            }
            uint32_t node = add_node(
                parser, REAPER_AST_IDENTIFIER, parameter->text,
                REAPER_AST_NO_NODE, REAPER_AST_NO_NODE,
                parameter->line, parameter->column
            );
            if (node == REAPER_AST_NO_NODE || !vector_push(&parameters, node)) {
                vector_free(&parameters);
                if (node != REAPER_AST_NO_NODE)
                    (void)parse_fail(parser, "out of memory collecting function parameters");
                return REAPER_AST_NO_NODE;
            }

            skip_newlines(parser);
            if (!token_is(parser, ",")) break;
            ++parser->pos;
            skip_newlines(parser);
        }
    }

    if (!consume_text(parser, ")", "expected ')' after parameters")) {
        vector_free(&parameters);
        return REAPER_AST_NO_NODE;
    }

    uint32_t parameter_sequence = make_sequence(
        parser, &parameters, keyword->line, keyword->column
    );
    vector_free(&parameters);
    if (parser->error != NULL && parser->error->message[0] != '\0')
        return REAPER_AST_NO_NODE;

    uint32_t body = parse_block(parser);
    if (body == REAPER_AST_NO_NODE) return body;

    return add_node(
        parser, REAPER_AST_FUNCTION, name->text,
        parameter_sequence, body, keyword->line, keyword->column
    );
}

static uint32_t parse_when(Parser *parser, const ReaperToken *keyword) {
    ++parser->pos;
    uint32_t condition = parse_expression_bp(parser, 1);
    if (condition == REAPER_AST_NO_NODE) return condition;

    uint32_t yes = parse_block(parser);
    if (yes == REAPER_AST_NO_NODE) return yes;

    NodeVector branches = {0};
    if (!vector_push(&branches, yes)) {
        (void)parse_fail(parser, "out of memory building conditional AST");
        return REAPER_AST_NO_NODE;
    }

    size_t saved_position = parser->pos;
    skip_newlines(parser);
    if (token_is(parser, "otherwise")) {
        ++parser->pos;
        uint32_t no = parse_block(parser);
        if (no == REAPER_AST_NO_NODE || !vector_push(&branches, no)) {
            vector_free(&branches);
            if (no != REAPER_AST_NO_NODE)
                (void)parse_fail(parser, "out of memory building alternative branch");
            return REAPER_AST_NO_NODE;
        }
    } else {
        parser->pos = saved_position;
    }

    uint32_t branch_sequence = make_sequence(
        parser, &branches, keyword->line, keyword->column
    );
    vector_free(&branches);
    if (parser->error != NULL && parser->error->message[0] != '\0')
        return REAPER_AST_NO_NODE;

    return add_node(
        parser, REAPER_AST_WHEN, "", condition, branch_sequence,
        keyword->line, keyword->column
    );
}

static uint32_t parse_each(Parser *parser, const ReaperToken *keyword) {
    ++parser->pos;
    const ReaperToken *name = peek(parser);
    if (!consume_kind(parser, REAPER_TOK_IDENTIFIER, "expected an iteration variable after 'each'"))
        return REAPER_AST_NO_NODE;
    if (!consume_text(parser, "in", "expected 'in' after iteration variable"))
        return REAPER_AST_NO_NODE;

    uint32_t iterable = parse_expression_bp(parser, 1);
    if (iterable == REAPER_AST_NO_NODE) return iterable;
    uint32_t body = parse_block(parser);
    if (body == REAPER_AST_NO_NODE) return body;

    return add_node(
        parser, REAPER_AST_EACH, name->text,
        iterable, body, keyword->line, keyword->column
    );
}

static uint32_t parse_while(Parser *parser, const ReaperToken *keyword) {
    ++parser->pos;
    if (!consume_text(parser, "while", "expected 'while' after 'loop'"))
        return REAPER_AST_NO_NODE;

    uint32_t condition = parse_expression_bp(parser, 1);
    if (condition == REAPER_AST_NO_NODE) return condition;
    uint32_t body = parse_block(parser);
    if (body == REAPER_AST_NO_NODE) return body;

    return add_node(
        parser, REAPER_AST_WHILE, "", condition, body,
        keyword->line, keyword->column
    );
}

static uint32_t parse_declaration(Parser *parser, const ReaperToken *keyword) {
    int mutable = strcmp(reaper_token_canonical_text(keyword), "vary") == 0;
    ++parser->pos;

    const ReaperToken *name = peek(parser);
    if (!consume_kind(parser, REAPER_TOK_IDENTIFIER, "expected a name after declaration"))
        return REAPER_AST_NO_NODE;
    if (!consume_text(parser, ":=", "expected ':=' after declared name"))
        return REAPER_AST_NO_NODE;

    uint32_t value = parse_expression_bp(parser, 1);
    if (value == REAPER_AST_NO_NODE) return value;

    return add_node(
        parser,
        mutable ? REAPER_AST_DECLARE_MUTABLE : REAPER_AST_DECLARE_IMMUTABLE,
        name->text,
        value,
        REAPER_AST_NO_NODE,
        keyword->line,
        keyword->column
    );
}

static uint32_t parse_change(Parser *parser, const ReaperToken *keyword) {
    ++parser->pos;
    const ReaperToken *name = peek(parser);
    if (!consume_kind(parser, REAPER_TOK_IDENTIFIER, "expected a mutable name after 'change'"))
        return REAPER_AST_NO_NODE;
    if (!consume_text(parser, ":=", "expected ':=' after changed name"))
        return REAPER_AST_NO_NODE;

    uint32_t value = parse_expression_bp(parser, 1);
    if (value == REAPER_AST_NO_NODE) return value;

    return add_node(
        parser, REAPER_AST_CHANGE, name->text,
        value, REAPER_AST_NO_NODE, keyword->line, keyword->column
    );
}

static uint32_t parse_statement(Parser *parser) {
    const ReaperToken *keyword = peek(parser);
    if (keyword == NULL) {
        (void)parse_fail(parser, "unexpected end of token stream");
        return REAPER_AST_NO_NODE;
    }

    const char *word = peek_text(parser);
    if (strcmp(word, "make") == 0 || strcmp(word, "vary") == 0)
        return parse_declaration(parser, keyword);
    if (strcmp(word, "change") == 0)
        return parse_change(parser, keyword);
    if (strcmp(word, "craft") == 0)
        return parse_function(parser, keyword);
    if (strcmp(word, "when") == 0)
        return parse_when(parser, keyword);
    if (strcmp(word, "each") == 0)
        return parse_each(parser, keyword);
    if (strcmp(word, "loop") == 0)
        return parse_while(parser, keyword);

    if (strcmp(word, "emit") == 0) {
        ++parser->pos;
        uint32_t value = parse_expression_bp(parser, 1);
        if (value == REAPER_AST_NO_NODE) return value;
        return add_node(
            parser, REAPER_AST_EMIT, "", value, REAPER_AST_NO_NODE,
            keyword->line, keyword->column
        );
    }

    if (strcmp(word, "yield") == 0) {
        ++parser->pos;
        uint32_t value = REAPER_AST_NO_NODE;
        if (!is_newline(parser) && !token_is(parser, "}") && !is_eof(parser)) {
            value = parse_expression_bp(parser, 1);
            if (value == REAPER_AST_NO_NODE) return value;
        }
        return add_node(
            parser, REAPER_AST_YIELD, "", value, REAPER_AST_NO_NODE,
            keyword->line, keyword->column
        );
    }

    uint32_t expression = parse_expression_bp(parser, 1);
    if (expression == REAPER_AST_NO_NODE) return expression;
    return add_node(
        parser, REAPER_AST_EXPRESSION_STATEMENT, "",
        expression, REAPER_AST_NO_NODE,
        keyword->line, keyword->column
    );
}

static int parser_init(
    const ReaperTokenArray *tokens,
    ReaperAst *out,
    ReaperParseError *error,
    Parser *parser
) {
    if (out == NULL || tokens == NULL || tokens->items == NULL ||
        tokens->length == 0U) {
        if (error != NULL) {
            (void)snprintf(error->message, sizeof error->message,
                "tokens and output are required");
            error->line = 1U;
            error->column = 1U;
        }
        return 0;
    }

    memset(out, 0, sizeof *out);
    out->root = REAPER_AST_NO_NODE;
    memset(parser, 0, sizeof *parser);
    parser->tokens = tokens;
    parser->pos = 0U;
    parser->depth = 0U;
    parser->ast = out;
    parser->error = error != NULL ? error : &parser->local_error;
    memset(parser->error, 0, sizeof *parser->error);
    return 1;
}

int reaper_parse_expression(
    const ReaperTokenArray *tokens,
    ReaperAst *out,
    ReaperParseError *error
) {
    Parser parser;
    if (!parser_init(tokens, out, error, &parser)) return 0;

    skip_newlines(&parser);
    out->root = parse_expression_bp(&parser, 1);
    if (out->root == REAPER_AST_NO_NODE) {
        reaper_ast_free(out);
        return 0;
    }

    skip_newlines(&parser);
    if (!is_eof(&parser)) {
        (void)parse_fail(&parser, "unexpected token after expression");
        reaper_ast_free(out);
        return 0;
    }
    return 1;
}

int reaper_parse_program(
    const ReaperTokenArray *tokens,
    ReaperAst *out,
    ReaperParseError *error
) {
    Parser parser;
    if (!parser_init(tokens, out, error, &parser)) return 0;

    NodeVector statements = {0};
    skip_newlines(&parser);

    while (!is_eof(&parser)) {
        uint32_t statement = parse_statement(&parser);
        if (statement == REAPER_AST_NO_NODE ||
            !vector_push(&statements, statement)) {
            vector_free(&statements);
            if (statement != REAPER_AST_NO_NODE)
                (void)parse_fail(&parser, "out of memory collecting program statements");
            reaper_ast_free(out);
            return 0;
        }
        if (!statement_end(&parser)) {
            vector_free(&statements);
            reaper_ast_free(out);
            return 0;
        }
    }

    uint32_t sequence = make_sequence(&parser, &statements, 1U, 1U);
    vector_free(&statements);
    if (parser.error != NULL && parser.error->message[0] != '\0') {
        reaper_ast_free(out);
        return 0;
    }

    out->root = add_node(
        &parser, REAPER_AST_PROGRAM, "",
        sequence, REAPER_AST_NO_NODE, 1U, 1U
    );
    if (out->root == REAPER_AST_NO_NODE) {
        reaper_ast_free(out);
        return 0;
    }
    return 1;
}

void reaper_ast_free(ReaperAst *ast) {
    if (ast == NULL) return;
    for (size_t i = 0U; i < ast->length; ++i) {
        free(ast->items[i].text);
    }
    free(ast->items);
    memset(ast, 0, sizeof *ast);
    ast->root = REAPER_AST_NO_NODE;
}

const char *reaper_ast_kind_name(ReaperAstKind kind) {
    switch (kind) {
    case REAPER_AST_INTEGER: return "integer";
    case REAPER_AST_DECIMAL: return "decimal";
    case REAPER_AST_STRING: return "string";
    case REAPER_AST_BOOLEAN: return "boolean";
    case REAPER_AST_NULL: return "null";
    case REAPER_AST_IDENTIFIER: return "identifier";
    case REAPER_AST_UNARY: return "unary";
    case REAPER_AST_BINARY: return "binary";
    case REAPER_AST_CALL: return "call";
    case REAPER_AST_INDEX: return "index";
    case REAPER_AST_LIST: return "list";
    case REAPER_AST_SEQUENCE: return "sequence";
    case REAPER_AST_PROGRAM: return "program";
    case REAPER_AST_DECLARE_IMMUTABLE: return "declare-immutable";
    case REAPER_AST_DECLARE_MUTABLE: return "declare-mutable";
    case REAPER_AST_CHANGE: return "change";
    case REAPER_AST_EMIT: return "emit";
    case REAPER_AST_YIELD: return "yield";
    case REAPER_AST_FUNCTION: return "function";
    case REAPER_AST_BLOCK: return "block";
    case REAPER_AST_WHEN: return "when";
    case REAPER_AST_EACH: return "each";
    case REAPER_AST_WHILE: return "while";
    case REAPER_AST_EXPRESSION_STATEMENT: return "expression-statement";
    default: return "invalid";
    }
}
