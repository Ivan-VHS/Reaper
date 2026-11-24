#include "reaper/ffi.h"

#include "reaper/ast.h"
#include "reaper/ir.h"

#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REAPER_FFI_MAX_SOURCE_BYTES (1024u * 1024u)
#define REAPER_FFI_DIAGNOSTIC_MAX 4096u

static void write_diagnostic(char *output, uint64_t capacity, const char *message) {
    size_t bounded_capacity;
    if (output == NULL || capacity == 0u) return;
    bounded_capacity = capacity > REAPER_FFI_DIAGNOSTIC_MAX
        ? REAPER_FFI_DIAGNOSTIC_MAX : (size_t)capacity;
    if (bounded_capacity == 0u) return;
    (void)snprintf(output, bounded_capacity, "%s", message != NULL ? message : "");
}

static int append_ir_node(ReaperIrNode *nodes, size_t capacity, size_t *length,
                          ReaperIrOpcode opcode, ReaperIrType type,
                          uint32_t lhs, uint32_t rhs, int64_t immediate,
                          uint32_t line, uint32_t column, uint32_t *out_index) {
    if (nodes == NULL || length == NULL || out_index == NULL ||
        *length >= capacity || *length >= UINT32_MAX) return 0;
    *out_index = (uint32_t)*length;
    nodes[*length] = (ReaperIrNode){
        opcode, type, lhs, rhs, immediate, line, column
    };
    ++*length;
    return 1;
}

static int parse_integer(const char *text, int64_t *value) {
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

static int build_integer_ir(const ReaperAst *ast, ReaperIrNode **nodes_out,
                            size_t *length_out, char *diagnostic,
                            uint64_t diagnostic_capacity) {
    ReaperIrNode *nodes = NULL;
    uint32_t *mapped = NULL;
    size_t capacity, length = 0u, index;
    int success = 0;

    if (ast == NULL || nodes_out == NULL || length_out == NULL ||
        ast->items == NULL || ast->length == 0u ||
        ast->length > (SIZE_MAX - 1u) / 2u) {
        write_diagnostic(diagnostic, diagnostic_capacity, "invalid or empty syntax tree");
        return 0;
    }
    capacity = ast->length * 2u + 1u;
    if (capacity > UINT32_MAX || capacity > SIZE_MAX / sizeof *nodes) {
        write_diagnostic(diagnostic, diagnostic_capacity, "expression exceeds the native IR limit");
        return 0;
    }
    nodes = (ReaperIrNode *)calloc(capacity, sizeof *nodes);
    mapped = (uint32_t *)malloc(ast->length * sizeof *mapped);
    if (nodes == NULL || mapped == NULL) {
        write_diagnostic(diagnostic, diagnostic_capacity, "out of memory building integer IR");
        goto cleanup;
    }

    for (index = 0u; index < ast->length; ++index) {
        const ReaperAstNode *node = &ast->items[index];
        uint32_t left = REAPER_IR_NO_VALUE, right = REAPER_IR_NO_VALUE;
        uint32_t output_index = REAPER_IR_NO_VALUE;
        int64_t immediate = 0;
        ReaperIrOpcode opcode = REAPER_IR_OP_INVALID;

        if (node->kind == REAPER_AST_INTEGER) {
            opcode = REAPER_IR_OP_CONST_I64;
            if (!parse_integer(node->text, &immediate)) {
                write_diagnostic(diagnostic, diagnostic_capacity,
                                 "integer literal is outside the signed i64 range");
                goto cleanup;
            }
        } else if (node->kind == REAPER_AST_UNARY) {
            if (node->left >= index) {
                write_diagnostic(diagnostic, diagnostic_capacity, "invalid unary expression reference");
                goto cleanup;
            }
            left = mapped[node->left];
            if (node->text != NULL && strcmp(node->text, "+") == 0) {
                mapped[index] = left;
                continue;
            }
            if (node->text == NULL || strcmp(node->text, "-") != 0) {
                write_diagnostic(diagnostic, diagnostic_capacity,
                                 "only unary plus and minus are supported by the integer ABI");
                goto cleanup;
            }
            if (!append_ir_node(nodes, capacity, &length,
                                REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
                                REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, -1,
                                (uint32_t)node->line, (uint32_t)node->column,
                                &right) ||
                !append_ir_node(nodes, capacity, &length,
                                REAPER_IR_OP_MUL_I64, REAPER_IR_TYPE_I64,
                                left, right, 0,
                                (uint32_t)node->line, (uint32_t)node->column,
                                &output_index)) {
                write_diagnostic(diagnostic, diagnostic_capacity, "integer IR capacity exceeded");
                goto cleanup;
            }
            mapped[index] = output_index;
            continue;
        } else if (node->kind == REAPER_AST_BINARY) {
            if (node->left >= index || node->right >= index) {
                write_diagnostic(diagnostic, diagnostic_capacity, "invalid binary expression reference");
                goto cleanup;
            }
            left = mapped[node->left];
            right = mapped[node->right];
            if (node->text == NULL) {
                write_diagnostic(diagnostic, diagnostic_capacity, "missing binary operator");
                goto cleanup;
            }
            if (strcmp(node->text, "+") == 0) opcode = REAPER_IR_OP_ADD_I64;
            else if (strcmp(node->text, "-") == 0) opcode = REAPER_IR_OP_SUB_I64;
            else if (strcmp(node->text, "*") == 0) opcode = REAPER_IR_OP_MUL_I64;
            else if (strcmp(node->text, "/") == 0) opcode = REAPER_IR_OP_DIV_I64;
            else {
                write_diagnostic(diagnostic, diagnostic_capacity,
                                 "operator is outside the supported integer ABI subset");
                goto cleanup;
            }
        } else {
            write_diagnostic(diagnostic, diagnostic_capacity,
                             "expression contains a non-integer literal or unsupported node");
            goto cleanup;
        }

        if (!append_ir_node(nodes, capacity, &length, opcode, REAPER_IR_TYPE_I64,
                            left, right, immediate, (uint32_t)node->line,
                            (uint32_t)node->column, &output_index)) {
            write_diagnostic(diagnostic, diagnostic_capacity, "integer IR capacity exceeded");
            goto cleanup;
        }
        mapped[index] = output_index;
    }

    if (ast->root >= ast->length) {
        write_diagnostic(diagnostic, diagnostic_capacity, "syntax tree root is invalid");
        goto cleanup;
    }
    {
        uint32_t return_index = REAPER_IR_NO_VALUE;
        if (!append_ir_node(nodes, capacity, &length, REAPER_IR_OP_RETURN,
                            REAPER_IR_TYPE_UNIT, mapped[ast->root],
                            REAPER_IR_NO_VALUE, 0, 1u, 1u, &return_index)) {
            write_diagnostic(diagnostic, diagnostic_capacity, "integer IR return node could not be added");
            goto cleanup;
        }
    }
    *nodes_out = nodes;
    *length_out = length;
    nodes = NULL;
    success = 1;

cleanup:
    free(nodes);
    free(mapped);
    return success;
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

    write_diagnostic(diagnostic, diagnostic_capacity, "");
    if (source == NULL || result == NULL ||
        (diagnostic == NULL && diagnostic_capacity != 0u)) {
        write_diagnostic(diagnostic, diagnostic_capacity, "source and result are required");
        return REAPER_ABI_INVALID_ARGUMENT;
    }
    if (source_size == 0u || source_size > REAPER_FFI_MAX_SOURCE_BYTES ||
        source_size > (uint64_t)(SIZE_MAX - 1u)) {
        write_diagnostic(diagnostic, diagnostic_capacity, "source length is empty or exceeds the 1 MiB ABI limit");
        return REAPER_ABI_LIMIT;
    }
    if (memchr(source, '\0', (size_t)source_size) != NULL) {
        write_diagnostic(diagnostic, diagnostic_capacity, "source contains an embedded NUL byte");
        return REAPER_ABI_INVALID_ARGUMENT;
    }

    terminated = (char *)malloc((size_t)source_size + 1u);
    if (terminated == NULL) {
        write_diagnostic(diagnostic, diagnostic_capacity, "out of memory copying source");
        return REAPER_ABI_LIMIT;
    }
    memcpy(terminated, source, (size_t)source_size);
    terminated[source_size] = '\0';

    if (!reaper_lex(terminated, &tokens, &lex_error)) {
        char message[384];
        (void)snprintf(message, sizeof message, "lexer error at %zu:%zu: %s",
                       lex_error.line, lex_error.column, lex_error.message);
        write_diagnostic(diagnostic, diagnostic_capacity, message);
        status = REAPER_ABI_SYNTAX_ERROR;
        goto cleanup;
    }
    if (!reaper_parse_expression(&tokens, &ast, &parse_error)) {
        char message[384];
        (void)snprintf(message, sizeof message, "parser error at %zu:%zu: %s",
                       parse_error.line, parse_error.column, parse_error.message);
        write_diagnostic(diagnostic, diagnostic_capacity, message);
        status = REAPER_ABI_SYNTAX_ERROR;
        goto cleanup;
    }
    if (!build_integer_ir(&ast, &nodes, &ir_length, diagnostic, diagnostic_capacity)) {
        status = REAPER_ABI_UNSUPPORTED_EXPRESSION;
        goto cleanup;
    }
    if (ir_length > SIZE_MAX / sizeof *values) {
        write_diagnostic(diagnostic, diagnostic_capacity, "integer execution buffer is too large");
        status = REAPER_ABI_LIMIT;
        goto cleanup;
    }
    values = (int64_t *)calloc(ir_length, sizeof *values);
    if (values == NULL) {
        write_diagnostic(diagnostic, diagnostic_capacity, "out of memory allocating integer execution buffer");
        status = REAPER_ABI_LIMIT;
        goto cleanup;
    }
    {
        const ReaperIrModule module = {nodes, ir_length};
        if (!reaper_ir_verify(&module, &ir_error)) {
            write_diagnostic(diagnostic, diagnostic_capacity, ir_error.message);
            status = REAPER_ABI_UNSUPPORTED_EXPRESSION;
            goto cleanup;
        }
        if (!reaper_ir_execute_i64(&module, values, ir_length, &candidate, &ir_error)) {
            write_diagnostic(diagnostic, diagnostic_capacity, ir_error.message);
            status = REAPER_ABI_ARITHMETIC_ERROR;
            goto cleanup;
        }
    }

    *result = candidate;
    write_diagnostic(diagnostic, diagnostic_capacity, "");
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
    } entries[] = {
        {"Сам", UINT64_C(2)}
    };
    size_t index;
    if (identity == NULL || ordinal == NULL || identity[0] == '\0')
        return REAPER_ABI_INVALID_ARGUMENT;
    if (strlen(identity) > 128u) return REAPER_ABI_LIMIT;
    for (index = 0u; index < sizeof entries / sizeof entries[0]; ++index) {
        if (strcmp(identity, entries[index].identity) == 0) {
            *ordinal = entries[index].ordinal;
            return REAPER_ABI_OK;
        }
    }
    return REAPER_ABI_NOT_FOUND;
}
