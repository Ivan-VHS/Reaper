#include "reaper/ast.h"
#include "reaper/ir.h"
#include "reaper/lexer.h"
#include "reaper/lower.h"
#include "reaper/optimizer.h"
#include "reaper/seadlow.h"

#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NO_VALUE REAPER_IR_NO_VALUE

static int evaluate(const char *source, int64_t *result, ReaperIrError *error) {
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0u, 0u};
    ReaperAst ast;
    ReaperParseError parse_error = {{0}, 0u, 0u};
    ReaperIrNode *ir = NULL;
    ReaperIrNode *optimized = NULL;
    int64_t *values = NULL;
    int ok = 0;

    if (!reaper_lex(source, &tokens, &lex_error)) goto cleanup;
    if (!reaper_parse_expression(&tokens, &ast, &parse_error)) goto cleanup;
    const size_t capacity = ast.length + 1u;
    if (capacity > SIZE_MAX / sizeof *ir) {
        reaper_ast_free(&ast);
        goto cleanup;
    }
    ir = calloc(capacity, sizeof *ir);
    optimized = calloc(capacity, sizeof *optimized);
    values = calloc(capacity, sizeof *values);
    if (ir == NULL || optimized == NULL || values == NULL) {
        reaper_ast_free(&ast);
        goto cleanup;
    }

    size_t ir_length = 0u, optimized_length = 0u;
    if (!reaper_lower_ast_to_ir(&ast, ir, capacity, &ir_length, error)) {
        reaper_ast_free(&ast);
        goto cleanup;
    }
    reaper_ast_free(&ast);

    ReaperIrModule module = { ir, ir_length };
    ReaperOptimizationReport report;
    if (!reaper_ir_optimize_fixed_point(&module, optimized, capacity,
            &optimized_length, REAPER_OPTIMIZER_MAX_ITERATIONS,
            &report, error)) {
        goto cleanup;
    }
    ReaperIrModule optimized_module = { optimized, optimized_length };
    ok = reaper_ir_execute_i64(&optimized_module, values, capacity, result, error);

cleanup:
    reaper_tokens_free(&tokens);
    free(ir);
    free(optimized);
    free(values);
    return ok;
}

static void test_language_bitwise_pipeline(void) {
    ReaperIrError error;
    int64_t result = 0;
    assert(evaluate("((85 & 255) ^ 15) << 1", &result, &error));
    assert(result == 180);
    assert(evaluate("1 | 2 ^ 3 & 0", &result, &error));
    assert(result == 3);
    assert(evaluate("~0", &result, &error));
    assert(result == -1);
    assert(evaluate("1 + 2 << 3", &result, &error));
    assert(result == 24);
    assert(evaluate("~0 >> 1", &result, &error));
    assert(result == INT64_MAX);
}

static void test_shift_bounds_are_checked(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, NO_VALUE, NO_VALUE, 1, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, NO_VALUE, NO_VALUE, 64, 1, 6 },
        { REAPER_IR_OP_SHL_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2, NO_VALUE, 0, 1, 1 }
    };
    ReaperIrModule module = { nodes, 4u };
    ReaperIrError error;
    int64_t values[4] = {0};
    int64_t result = 91;
    assert(!reaper_ir_execute_i64(&module, values, 4u, &result, &error));
    assert(strstr(error.message, "between 0 and 63") != NULL);
    assert(result == 91);
}

static uint8_t expected_byte(ReaperSeadlowOp operation, uint8_t left, uint8_t right) {
    switch (operation) {
    case REAPER_SEADLOW_AND: return (uint8_t)(left & right);
    case REAPER_SEADLOW_OR: return (uint8_t)(left | right);
    case REAPER_SEADLOW_XOR: return (uint8_t)(left ^ right);
    case REAPER_SEADLOW_NOT: return (uint8_t)~left;
    default: return 0u;
    }
}

static void test_bulk_transform_and_popcount(void) {
    enum { BUFFER_BYTES = 4126 };
    uint8_t left[BUFFER_BYTES], right[BUFFER_BYTES], output[BUFFER_BYTES];
    const size_t bit_count = 33001u;
    const size_t byte_count = bit_count / 8u + 1u;

    for (size_t i = 0u; i < byte_count; ++i) {
        left[i] = (uint8_t)(i * 37u + 11u);
        right[i] = (uint8_t)(i * 19u + 7u);
    }

    ReaperSeadlowReport report;
    ReaperSeadlowError error;
    assert(reaper_seadlow_transform(REAPER_SEADLOW_XOR, output, left, right,
        bit_count, &report, &error));
    assert(report.bits_processed == bit_count);
    assert(report.words_processed == bit_count / 64u);
    assert(report.tiles_processed == 3u);
    assert(report.tail_bits_processed == 1u);

    for (size_t i = 0u; i < byte_count; ++i) {
        const uint8_t mask = (i + 1u == byte_count) ? 0x01u : 0xFFu;
        assert(output[i] == (uint8_t)(expected_byte(
            REAPER_SEADLOW_XOR, left[i], right[i]) & mask));
    }

    size_t count = 0u;
    assert(reaper_seadlow_popcount(output, bit_count, &count, &report, &error));
    size_t expected = 0u;
    for (size_t i = 0u; i < byte_count; ++i) {
        uint8_t value = output[i];
        if (i + 1u == byte_count) value &= 0x01u;
        for (unsigned bit = 0u; bit < 8u; ++bit) {
            expected += (size_t)((value >> bit) & 1u);
        }
    }
    assert(count == expected);
    assert(report.bits_processed == bit_count);
    assert(report.tiles_processed == 3u);

    assert(reaper_seadlow_transform(REAPER_SEADLOW_OR, output, left, right,
        bit_count, &report, &error));
    for (size_t i = 0u; i < byte_count; ++i) {
        const uint8_t mask = (i + 1u == byte_count) ? 0x01u : 0xFFu;
        assert(output[i] == (uint8_t)(expected_byte(
            REAPER_SEADLOW_OR, left[i], right[i]) & mask));
    }
}

static void test_exact_in_place_and_unaligned_buffers(void) {
    uint8_t storage[20] = {0};
    uint8_t rhs[3] = {0xF0u, 0x0Fu, 0x03u};
    storage[1] = 0xAAu;
    storage[2] = 0x55u;
    storage[3] = 0x02u;

    ReaperSeadlowReport report;
    ReaperSeadlowError error;
    assert(reaper_seadlow_transform(REAPER_SEADLOW_AND, storage + 1,
        storage + 1, rhs, 18u, &report, &error));
    assert(storage[1] == 0xA0u);
    assert(storage[2] == 0x05u);
    assert(storage[3] == 0x02u);

    assert(reaper_seadlow_transform(REAPER_SEADLOW_NOT, storage + 1,
        storage + 1, NULL, 18u, &report, &error));
    assert(storage[3] == 0x01u);
}

static void test_partial_overlap_and_empty_input(void) {
    uint8_t buffer[8] = {0x11u, 0x22u, 0x33u, 0x44u};
    uint8_t rhs[4] = {0xFFu, 0xFFu, 0xFFu, 0xFFu};
    uint8_t before[sizeof buffer];
    memcpy(before, buffer, sizeof buffer);

    ReaperSeadlowReport report;
    ReaperSeadlowError error;
    assert(!reaper_seadlow_transform(REAPER_SEADLOW_OR, buffer + 1,
        buffer, rhs, 16u, &report, &error));
    assert(strstr(error.message, "partial") != NULL);
    assert(memcmp(buffer, before, sizeof buffer) == 0);

    assert(reaper_seadlow_transform(REAPER_SEADLOW_NOT, NULL, NULL, NULL,
        0u, &report, &error));
    assert(report.bits_processed == 0u);
    size_t count = 99u;
    assert(reaper_seadlow_popcount(NULL, 0u, &count, &report, &error));
    assert(count == 0u);
}

int main(void) {
    test_language_bitwise_pipeline();
    test_shift_bounds_are_checked();
    test_bulk_transform_and_popcount();
    test_exact_in_place_and_unaligned_buffers();
    test_partial_overlap_and_empty_input();
    puts("native Seadlow tests: 5 groups passed");
    return 0;
}
