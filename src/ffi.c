#include "reaper/ffi.h"
#include "reaper/ast.h"
#include "reaper/ir.h"

#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REAPER_FFI_DIAGNOSTIC_MAX 4096u

static void diagnostic_write(char *buffer, uint64_t capacity, const char *message) {
    size_t bounded;
    if (buffer == NULL || capacity == 0u) return;
    bounded = capacity > REAPER_FFI_DIAGNOSTIC_MAX
        ? REAPER_FFI_DIAGNOSTIC_MAX : (size_t)capacity;
    (void)snprintf(buffer, bounded, "%s", message != NULL ? message : "");
}

static int add_ir_node(ReaperIrNode *nodes, size_t capacity, size_t *length,
                       ReaperIrOpcode opcode, ReaperIrType type,
                       uint32_t lhs, uint32_t rhs, int64_t immediate,
                       uint32_t line, uint32_t column,
                       uint64_t source_start_byte, uint64_t source_end_byte,
                       uint32_t *index_out) {
    if (nodes == NULL || length == NULL || index_out == NULL ||
        *length >= capacity || *length >= UINT32_MAX) return 0;
    *index_out = (uint32_t)*length;
    nodes[*length] = (ReaperIrNode){
        opcode, type, lhs, rhs, immediate, line, column,
        source_start_byte, source_end_byte
    };
    ++*length;
    return 1;
}

static int parse_i64(const char *text, int64_t *value) {
    char *end = NULL;
    intmax_t parsed;
    if (text == NULL || value == NULL || text[0] == '\0') return 0;
    errno = 0;
    parsed = strtoimax(text, &end, 10);
    if (errno == ERANGE || end == text || *end != '\0' ||
        parsed < INT64_MIN || parsed > INT64_MAX) return 0;
    *value = (int64_t)parsed;
    return 1;
}

static int parse_negative_i64_literal(const char *text, int64_t *value) {
    char *end = NULL;
    uintmax_t magnitude;
    const uintmax_t minimum_magnitude = (uintmax_t)INT64_MAX + UINTMAX_C(1);
    if (text == NULL || value == NULL || text[0] == '\0') return 0;
    errno = 0;
    magnitude = strtoumax(text, &end, 10);
    if (errno == ERANGE || end == text || end == NULL || *end != '\0' ||
        magnitude != minimum_magnitude) return 0;
    *value = INT64_MIN;
    return 1;
}

static const ReaperAstNode *negative_literal_parent(
    const ReaperAst *ast, size_t child_index) {
    for (size_t i = child_index + 1u; i < ast->length; ++i) {
        const ReaperAstNode *node = &ast->items[i];
        if (node->kind == REAPER_AST_UNARY && node->left == child_index &&
            node->text != NULL && strcmp(node->text, "-") == 0)
            return node;
    }
    return NULL;
}

static int build_i64_ir(const ReaperAst *ast, ReaperIrNode **nodes_out,
                        size_t *length_out, char *diagnostic,
                        uint64_t diagnostic_capacity) {
    ReaperIrNode *nodes = NULL;
    uint32_t *mapped = NULL;
    size_t capacity, length = 0u, index;
    if (ast == NULL || ast->items == NULL || ast->length == 0u ||
        nodes_out == NULL || length_out == NULL ||
        ast->length > (SIZE_MAX - 1u) / 2u) {
        diagnostic_write(diagnostic, diagnostic_capacity, "invalid or empty expression tree");
        return 0;
    }
    capacity = ast->length * 2u + 1u;
    if (capacity > UINT32_MAX || capacity > SIZE_MAX / sizeof *nodes ||
        ast->length > SIZE_MAX / sizeof *mapped) {
        diagnostic_write(diagnostic, diagnostic_capacity, "expression exceeds the i64 IR limit");
        return 0;
    }
    nodes = (ReaperIrNode *)calloc(capacity, sizeof *nodes);
    mapped = (uint32_t *)malloc(ast->length * sizeof *mapped);
    if (nodes == NULL || mapped == NULL) {
        diagnostic_write(diagnostic, diagnostic_capacity, "out of memory building i64 IR");
        free(nodes);
        free(mapped);
        return 0;
    }

    for (index = 0u; index < ast->length; ++index) {
        const ReaperAstNode *node = &ast->items[index];
        uint32_t output_index = REAPER_IR_NO_VALUE;
        uint32_t lhs = REAPER_IR_NO_VALUE;
        uint32_t rhs = REAPER_IR_NO_VALUE;
        int64_t immediate = 0;
        ReaperIrOpcode opcode = REAPER_IR_OP_INVALID;
        uint32_t source_line, source_column;
        uint64_t source_start_byte = (uint64_t)node->source_start_byte;
        uint64_t source_end_byte = (uint64_t)node->source_end_byte;
        if (node->line > UINT32_MAX || node->column > UINT32_MAX ||
            node->source_end_byte < node->source_start_byte) {
            diagnostic_write(diagnostic, diagnostic_capacity,
                             "source span exceeds the canonical IR representation");
            goto fail;
        }
        source_line = (uint32_t)node->line;
        source_column = (uint32_t)node->column;

        if (node->kind == REAPER_AST_INTEGER) {
            opcode = REAPER_IR_OP_CONST_I64;
            if (!parse_i64(node->text, &immediate)) {
                const ReaperAstNode *parent = negative_literal_parent(ast, index);
                if (parent == NULL ||
                    !parse_negative_i64_literal(node->text, &immediate)) {
                    diagnostic_write(diagnostic, diagnostic_capacity,
                                     "integer literal is outside signed i64 range");
                    goto fail;
                }
                source_line = (uint32_t)parent->line;
                source_column = (uint32_t)parent->column;
                source_start_byte = (uint64_t)parent->source_start_byte;
                source_end_byte = (uint64_t)parent->source_end_byte;
            }
        } else if (node->kind == REAPER_AST_UNARY) {
            if (node->left >= index) {
                diagnostic_write(diagnostic, diagnostic_capacity, "invalid unary node reference");
                goto fail;
            }
            lhs = mapped[node->left];
            if (node->text != NULL && strcmp(node->text, "+") == 0) {
                mapped[index] = lhs;
                continue;
            }
            if (ast->items[node->left].kind == REAPER_AST_INTEGER &&
                nodes[lhs].opcode == REAPER_IR_OP_CONST_I64 &&
                nodes[lhs].immediate == INT64_MIN) {
                mapped[index] = lhs;
                continue;
            }
            if (node->text == NULL || strcmp(node->text, "-") != 0) {
                diagnostic_write(diagnostic, diagnostic_capacity,
                                 "only unary plus and minus are supported");
                goto fail;
            }
            if (!add_ir_node(nodes, capacity, &length,
                             REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
                             REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, -1,
                             source_line, source_column,
                             source_start_byte, source_end_byte, &rhs) ||
                !add_ir_node(nodes, capacity, &length,
                             REAPER_IR_OP_MUL_I64, REAPER_IR_TYPE_I64,
                             lhs, rhs, 0, source_line, source_column,
                             source_start_byte, source_end_byte, &output_index)) {
                diagnostic_write(diagnostic, diagnostic_capacity, "i64 IR capacity exceeded");
                goto fail;
            }
            mapped[index] = output_index;
            continue;
        } else if (node->kind == REAPER_AST_BINARY) {
            if (node->left >= index || node->right >= index) {
                diagnostic_write(diagnostic, diagnostic_capacity, "invalid binary node reference");
                goto fail;
            }
            lhs = mapped[node->left];
            rhs = mapped[node->right];
            if (node->text == NULL) {
                diagnostic_write(diagnostic, diagnostic_capacity, "binary operator is missing");
                goto fail;
            }
            if (strcmp(node->text, "+") == 0) opcode = REAPER_IR_OP_ADD_I64;
            else if (strcmp(node->text, "-") == 0) opcode = REAPER_IR_OP_SUB_I64;
            else if (strcmp(node->text, "*") == 0) opcode = REAPER_IR_OP_MUL_I64;
            else if (strcmp(node->text, "/") == 0) opcode = REAPER_IR_OP_DIV_I64;
            else {
                diagnostic_write(diagnostic, diagnostic_capacity,
                                 "operator is outside the supported i64 subset");
                goto fail;
            }
        } else {
            diagnostic_write(diagnostic, diagnostic_capacity,
                             "expression contains a non-integer or unsupported node");
            goto fail;
        }

        if (!add_ir_node(nodes, capacity, &length, opcode, REAPER_IR_TYPE_I64,
                         lhs, rhs, immediate, source_line,
                         source_column, source_start_byte, source_end_byte,
                         &output_index)) {
            diagnostic_write(diagnostic, diagnostic_capacity, "i64 IR capacity exceeded");
            goto fail;
        }
        mapped[index] = output_index;
    }

    if (ast->root >= ast->length) {
        diagnostic_write(diagnostic, diagnostic_capacity, "expression root is invalid");
        goto fail;
    }
    {
        uint32_t ignored_return_index = REAPER_IR_NO_VALUE;
        const ReaperAstNode *root = &ast->items[ast->root];
        if (root->line > UINT32_MAX || root->column > UINT32_MAX ||
            root->source_end_byte < root->source_start_byte ||
            !add_ir_node(nodes, capacity, &length, REAPER_IR_OP_RETURN,
                         REAPER_IR_TYPE_UNIT, mapped[ast->root],
                         REAPER_IR_NO_VALUE, 0, (uint32_t)root->line,
                         (uint32_t)root->column,
                         (uint64_t)root->source_start_byte,
                         (uint64_t)root->source_end_byte,
                         &ignored_return_index)) {
            diagnostic_write(diagnostic, diagnostic_capacity, "i64 IR return node could not be added");
            goto fail;
        }
    }

    free(mapped);
    *nodes_out = nodes;
    *length_out = length;
    return 1;

fail:
    free(mapped);
    free(nodes);
    return 0;
}

uint32_t reaper_abi_version(void) {
    return REAPER_ABI_VERSION;
}

int32_t reaper_v1_eval_i64(const char *source, uint64_t source_size,
                           int64_t *result, char *diagnostic,
                           uint64_t diagnostic_capacity) {
    char *terminated = NULL;
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0u, 0u};
    ReaperAst ast = {0};
    ReaperParseError parse_error = {{0}, 0u, 0u};
    ReaperIrNode *nodes = NULL;
    size_t ir_length = 0u;
    int64_t *values = NULL;
    int64_t candidate = 0;
    ReaperIrError ir_error = {0};
    int32_t status = REAPER_ABI_INVALID_ARGUMENT;

    diagnostic_write(diagnostic, diagnostic_capacity, "");
    if (source == NULL || result == NULL ||
        (diagnostic == NULL && diagnostic_capacity != 0u)) {
        diagnostic_write(diagnostic, diagnostic_capacity, "source and result are required");
        return REAPER_ABI_INVALID_ARGUMENT;
    }
    if (source_size == 0u || source_size > REAPER_V1_MAX_SOURCE_BYTES ||
        source_size > (uint64_t)(SIZE_MAX - 1u)) {
        diagnostic_write(diagnostic, diagnostic_capacity,
                         "source length is empty or exceeds the 1 MiB ABI limit");
        return REAPER_ABI_LIMIT;
    }
    if (memchr(source, '\0', (size_t)source_size) != NULL) {
        diagnostic_write(diagnostic, diagnostic_capacity, "source contains an embedded NUL byte");
        return REAPER_ABI_INVALID_ARGUMENT;
    }

    terminated = (char *)malloc((size_t)source_size + 1u);
    if (terminated == NULL) {
        diagnostic_write(diagnostic, diagnostic_capacity, "out of memory copying source");
        return REAPER_ABI_LIMIT;
    }
    memcpy(terminated, source, (size_t)source_size);
    terminated[(size_t)source_size] = '\0';

    if (!reaper_lex(terminated, &tokens, &lex_error)) {
        char message[384];
        (void)snprintf(message, sizeof message, "lexer error at %zu:%zu: %s",
                       lex_error.line, lex_error.column, lex_error.message);
        diagnostic_write(diagnostic, diagnostic_capacity, message);
        status = REAPER_ABI_SYNTAX_ERROR;
        goto cleanup;
    }
    if (!reaper_parse_expression(&tokens, &ast, &parse_error)) {
        char message[384];
        (void)snprintf(message, sizeof message, "parser error at %zu:%zu: %s",
                       parse_error.line, parse_error.column, parse_error.message);
        diagnostic_write(diagnostic, diagnostic_capacity, message);
        status = REAPER_ABI_SYNTAX_ERROR;
        goto cleanup;
    }
    if (!build_i64_ir(&ast, &nodes, &ir_length, diagnostic, diagnostic_capacity)) {
        status = REAPER_ABI_UNSUPPORTED_EXPRESSION;
        goto cleanup;
    }
    if (ir_length > SIZE_MAX / sizeof *values) {
        diagnostic_write(diagnostic, diagnostic_capacity, "i64 execution buffer exceeds host limits");
        status = REAPER_ABI_LIMIT;
        goto cleanup;
    }
    values = (int64_t *)calloc(ir_length, sizeof *values);
    if (values == NULL) {
        diagnostic_write(diagnostic, diagnostic_capacity, "out of memory allocating i64 execution buffer");
        status = REAPER_ABI_LIMIT;
        goto cleanup;
    }
    {
        const ReaperIrModule module = {nodes, ir_length};
        if (!reaper_ir_verify(&module, &ir_error)) {
            diagnostic_write(diagnostic, diagnostic_capacity, ir_error.message);
            status = REAPER_ABI_UNSUPPORTED_EXPRESSION;
            goto cleanup;
        }
        if (!reaper_ir_execute_i64(&module, values, ir_length, &candidate, &ir_error)) {
            diagnostic_write(diagnostic, diagnostic_capacity, ir_error.message);
            status = REAPER_ABI_ARITHMETIC_ERROR;
            goto cleanup;
        }
    }

    *result = candidate;
    diagnostic_write(diagnostic, diagnostic_capacity, "");
    status = REAPER_ABI_OK;

cleanup:
    free(values);
    free(nodes);
    reaper_ast_free(&ast);
    reaper_tokens_free(&tokens);
    free(terminated);
    return status;
}

int32_t reaper_v1_selfhood_lookup(const char *identity, uint64_t *ordinal) {
    static const struct {
        const char *identity;
        uint64_t ordinal;
    } canonical[] = {
        {"Сам", UINT64_C(2)}
    };
    size_t index;
    if (identity == NULL || ordinal == NULL || identity[0] == '\0')
        return REAPER_ABI_INVALID_ARGUMENT;
    if (strlen(identity) > 128u) return REAPER_ABI_LIMIT;
    for (index = 0u; index < sizeof canonical / sizeof canonical[0]; ++index) {
        if (strcmp(identity, canonical[index].identity) == 0) {
            *ordinal = canonical[index].ordinal;
            return REAPER_ABI_OK;
        }
    }
    return REAPER_ABI_NOT_FOUND;
}
