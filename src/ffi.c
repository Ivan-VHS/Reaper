#include "reaper/ffi.h"
#include "reaper/ast.h"
#include "reaper/ir.h"
#include "reaper/lexer.h"
#include "reaper/lower.h"
#include "reaper/optimizer.h"
#include "reaper/selfhood.h"

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void write_error(char *output, uint64_t capacity, const char *message) {
    if (output == NULL || capacity == 0u) return;
    size_t limit = capacity > (uint64_t)SIZE_MAX ? SIZE_MAX : (size_t)capacity;
    if (limit == 0u) return;
    (void)snprintf(output, limit, "%s", message != NULL ? message : "native evaluation failed");
}

static int32_t fail_with(
    int32_t status, char *error, uint64_t error_capacity, const char *message
) {
    write_error(error, error_capacity, message);
    return status;
}

uint32_t reaper_abi_version(void) {
    return REAPER_ABI_VERSION;
}

int32_t reaper_v1_eval_i64(
    const char *source, uint64_t source_length, int64_t *output,
    char *error, uint64_t error_capacity
) {
    char *owned_source = NULL;
    ReaperTokenArray tokens = {0};
    ReaperAst ast = {0};
    ReaperIrNode *lowered = NULL;
    ReaperIrNode *optimized = NULL;
    int64_t *values = NULL;
    ReaperLexError lex_error = {{0}, 0u, 0u};
    ReaperParseError parse_error = {{0}, 0u, 0u};
    ReaperIrError ir_error = {0u, {0}};
    ReaperOptimizationReport report = {0u, 0u, 0};
    int64_t value = 0;
    size_t lowered_length = 0u;
    size_t optimized_length = 0u;
    int32_t status = REAPER_ABI_OK;

    if (error != NULL && error_capacity > 0u) error[0] = '\0';
    if (source == NULL || output == NULL || (error != NULL && error_capacity == 0u))
        return fail_with(REAPER_ABI_INVALID_ARGUMENT, error, error_capacity,
                         "source, output and a valid optional error buffer are required");
    if (source_length > REAPER_MAX_SOURCE_BYTES)
        return fail_with(REAPER_ABI_SOURCE_TOO_LARGE, error, error_capacity,
                         "source exceeds the 1 MiB native evaluation limit");
    if (source_length > (uint64_t)(SIZE_MAX - 1u))
        return fail_with(REAPER_ABI_SOURCE_TOO_LARGE, error, error_capacity,
                         "source length cannot be represented on this platform");
    if (memchr(source, '\0', (size_t)source_length) != NULL)
        return fail_with(REAPER_ABI_INVALID_ARGUMENT, error, error_capacity,
                         "source contains an embedded NUL byte");

    owned_source = (char *)malloc((size_t)source_length + 1u);
    if (owned_source == NULL)
        return fail_with(REAPER_ABI_INVALID_ARGUMENT, error, error_capacity,
                         "unable to allocate bounded source buffer");
    if (source_length > 0u) memcpy(owned_source, source, (size_t)source_length);
    owned_source[source_length] = '\0';

    if (!reaper_lex(owned_source, &tokens, &lex_error)) {
        char message[320];
        (void)snprintf(message, sizeof message, "%zu:%zu: %s",
                       lex_error.line, lex_error.column, lex_error.message);
        status = fail_with(REAPER_ABI_LEX_ERROR, error, error_capacity, message);
        goto cleanup;
    }
    if (!reaper_parse_expression(&tokens, &ast, &parse_error)) {
        char message[320];
        (void)snprintf(message, sizeof message, "%zu:%zu: %s",
                       parse_error.line, parse_error.column, parse_error.message);
        status = fail_with(REAPER_ABI_PARSE_ERROR, error, error_capacity, message);
        goto cleanup;
    }
    if (ast.length == 0u || ast.length >= SIZE_MAX / sizeof *lowered) {
        status = fail_with(REAPER_ABI_LOWER_ERROR, error, error_capacity,
                           "AST exceeds native lowering workspace limits");
        goto cleanup;
    }

    lowered = (ReaperIrNode *)malloc((ast.length + 1u) * sizeof *lowered);
    optimized = (ReaperIrNode *)malloc((ast.length + 1u) * sizeof *optimized);
    values = (int64_t *)calloc(ast.length + 1u, sizeof *values);
    if (lowered == NULL || optimized == NULL || values == NULL) {
        status = fail_with(REAPER_ABI_LOWER_ERROR, error, error_capacity,
                           "unable to allocate bounded native IR workspaces");
        goto cleanup;
    }
    if (!reaper_lower_ast_to_ir(&ast, lowered, ast.length + 1u,
                                &lowered_length, &ir_error)) {
        status = fail_with(REAPER_ABI_LOWER_ERROR, error, error_capacity,
                           ir_error.message);
        goto cleanup;
    }

    {
        const ReaperIrModule module = { lowered, lowered_length };
        if (!reaper_ir_optimize_fixed_point(&module, optimized, ast.length + 1u,
                &optimized_length, REAPER_OPTIMIZER_MAX_ITERATIONS, &report, &ir_error)) {
            status = fail_with(REAPER_ABI_OPTIMIZE_ERROR, error, error_capacity,
                               ir_error.message);
            goto cleanup;
        }
    }
    {
        const ReaperIrModule module = { optimized, optimized_length };
        if (!reaper_ir_execute_i64(&module, values, ast.length + 1u, &value, &ir_error)) {
            status = fail_with(REAPER_ABI_EXECUTION_ERROR, error, error_capacity,
                               ir_error.message);
            goto cleanup;
        }
    }

    *output = value;

cleanup:
    free(values);
    free(optimized);
    free(lowered);
    reaper_ast_free(&ast);
    reaper_tokens_free(&tokens);
    free(owned_source);
    return status;
}

int32_t reaper_v1_selfhood_count(uint64_t *count) {
    if (count == NULL) return REAPER_ABI_INVALID_ARGUMENT;
    *count = (uint64_t)reaper_selfhood_count();
    return REAPER_ABI_OK;
}

int32_t reaper_v1_selfhood_lookup(const char *identity, uint64_t *ordinal) {
    const ReaperSelfhoodEntry *entry;
    if (identity == NULL || ordinal == NULL) return REAPER_ABI_INVALID_ARGUMENT;
    entry = reaper_selfhood_find(identity);
    if (entry == NULL) return REAPER_ABI_NOT_FOUND;
    *ordinal = (uint64_t)entry->ordinal;
    return REAPER_ABI_OK;
}
