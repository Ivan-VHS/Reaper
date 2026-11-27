#include "reaper/optimizer.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fail(ReaperIrError *error, size_t index, const char *message) {
    if (error != NULL) {
        error->node_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static int add_overflows_i64(int64_t a, int64_t b) {
    if (b > 0) return a > INT64_MAX - b;
    if (b < 0) return a < INT64_MIN - b;
    return 0;
}

static int sub_overflows_i64(int64_t a, int64_t b) {
    if (b < 0) return a > INT64_MAX + b;
    if (b > 0) return a < INT64_MIN + b;
    return 0;
}

static int mul_overflows_i64(int64_t a, int64_t b) {
    if (a == 0 || b == 0) return 0;
    if (a == -1) return b == INT64_MIN;
    if (b == -1) return a == INT64_MIN;
    if (a > 0) {
        if (b > 0) return a > INT64_MAX / b;
        return b < INT64_MIN / a;
    }
    if (b > 0) return a < INT64_MIN / b;
    return a < INT64_MAX / b;
}

int reaper_ir_fold_constants(
    const ReaperIrModule *input,
    ReaperIrNode *output,
    size_t output_capacity,
    size_t *output_length,
    ReaperIrError *error
) {
    if (output_length != NULL) *output_length = 0;
    if (error != NULL) {
        error->node_index = 0;
        error->message[0] = '\0';
    }
    if (input == NULL || output_length == NULL ||
        (input->length != 0 && (input->nodes == NULL || output == NULL))) {
        return fail(error, 0, "input, output storage, and output length are required");
    }
    if (output_capacity < input->length) {
        return fail(error, 0, "output capacity is smaller than input module");
    }
    if (!reaper_ir_verify(input, error)) return 0;

    for (size_t i = 0; i < input->length; ++i) {
        ReaperIrNode node = input->nodes[i];
        if (node.opcode == REAPER_IR_OP_BIT_NOT_I64) {
            const ReaperIrNode *operand = &output[node.lhs];
            if (operand->opcode == REAPER_IR_OP_CONST_I64) {
                uint64_t bits = 0u;
                int64_t value = 0;
                memcpy(&bits, &operand->immediate, sizeof bits);
                bits = ~bits;
                memcpy(&value, &bits, sizeof value);
                node.opcode = REAPER_IR_OP_CONST_I64;
                node.lhs = REAPER_IR_NO_VALUE;
                node.rhs = REAPER_IR_NO_VALUE;
                node.immediate = value;
            }
        }
        if (node.opcode == REAPER_IR_OP_ADD_I64 ||
            node.opcode == REAPER_IR_OP_SUB_I64 ||
            node.opcode == REAPER_IR_OP_MUL_I64 ||
            node.opcode == REAPER_IR_OP_DIV_I64 ||
            node.opcode == REAPER_IR_OP_BIT_AND_I64 ||
            node.opcode == REAPER_IR_OP_BIT_OR_I64 ||
            node.opcode == REAPER_IR_OP_BIT_XOR_I64 ||
            node.opcode == REAPER_IR_OP_SHL_I64 ||
            node.opcode == REAPER_IR_OP_SHR_I64) {
            const ReaperIrNode *lhs = &output[node.lhs];
            const ReaperIrNode *rhs = &output[node.rhs];
            if (lhs->opcode == REAPER_IR_OP_CONST_I64 &&
                rhs->opcode == REAPER_IR_OP_CONST_I64) {
                int64_t value = 0;
                switch (node.opcode) {
                case REAPER_IR_OP_ADD_I64:
                    if (add_overflows_i64(lhs->immediate, rhs->immediate))
                        return fail(error, i, "constant addition overflows signed i64");
                    value = lhs->immediate + rhs->immediate;
                    break;
                case REAPER_IR_OP_SUB_I64:
                    if (sub_overflows_i64(lhs->immediate, rhs->immediate))
                        return fail(error, i, "constant subtraction overflows signed i64");
                    value = lhs->immediate - rhs->immediate;
                    break;
                case REAPER_IR_OP_MUL_I64:
                    if (mul_overflows_i64(lhs->immediate, rhs->immediate))
                        return fail(error, i, "constant multiplication overflows signed i64");
                    value = lhs->immediate * rhs->immediate;
                    break;
                case REAPER_IR_OP_DIV_I64:
                    if (rhs->immediate == 0)
                        return fail(error, i, "constant division by zero");
                    if (lhs->immediate == INT64_MIN && rhs->immediate == -1)
                        return fail(error, i, "constant division overflows signed i64");
                    value = lhs->immediate / rhs->immediate;
                    break;
                case REAPER_IR_OP_BIT_AND_I64:
                case REAPER_IR_OP_BIT_OR_I64:
                case REAPER_IR_OP_BIT_XOR_I64:
                case REAPER_IR_OP_SHL_I64:
                case REAPER_IR_OP_SHR_I64: {
                    uint64_t left = 0u, right = 0u, bits = 0u;
                    memcpy(&left, &lhs->immediate, sizeof left);
                    memcpy(&right, &rhs->immediate, sizeof right);
                    if ((node.opcode == REAPER_IR_OP_SHL_I64 ||
                         node.opcode == REAPER_IR_OP_SHR_I64) &&
                        (rhs->immediate < 0 || rhs->immediate >= 64)) {
                        return fail(error, i,
                            "constant bit shift count must be between 0 and 63");
                    }
                    if (node.opcode == REAPER_IR_OP_BIT_AND_I64) bits = left & right;
                    else if (node.opcode == REAPER_IR_OP_BIT_OR_I64) bits = left | right;
                    else if (node.opcode == REAPER_IR_OP_BIT_XOR_I64) bits = left ^ right;
                    else if (node.opcode == REAPER_IR_OP_SHL_I64)
                        bits = left << (unsigned)rhs->immediate;
                    else bits = left >> (unsigned)rhs->immediate;
                    memcpy(&value, &bits, sizeof value);
                    break;
                }
                default:
                    return fail(error, i, "unsupported integer arithmetic opcode");
                }
                node.opcode = REAPER_IR_OP_CONST_I64;
                node.lhs = REAPER_IR_NO_VALUE;
                node.rhs = REAPER_IR_NO_VALUE;
                node.immediate = value;
            }
        }
        output[i] = node;
    }

    ReaperIrModule folded = { output, input->length };
    if (!reaper_ir_verify(&folded, error)) return 0;
    *output_length = input->length;
    return 1;
}

static int same_node(const ReaperIrNode *a, const ReaperIrNode *b) {
    return a->opcode == b->opcode && a->type == b->type &&
        a->lhs == b->lhs && a->rhs == b->rhs &&
        a->immediate == b->immediate &&
        a->source_line == b->source_line &&
        a->source_column == b->source_column;
}

int reaper_ir_optimize_fixed_point(
    const ReaperIrModule *input,
    ReaperIrNode *output,
    size_t output_capacity,
    size_t *output_length,
    size_t max_iterations,
    ReaperOptimizationReport *report,
    ReaperIrError *error
) {
    if (output_length != NULL) *output_length = 0;
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }
    if (report != NULL) {
        report->iterations = 0U;
        report->folded_nodes = 0U;
        report->converged = 0;
    }
    if (input == NULL || output_length == NULL || report == NULL ||
        (input->length != 0U && (input->nodes == NULL || output == NULL))) {
        return fail(error, 0U, "input, output, length and report are required");
    }
    if (max_iterations == 0U || max_iterations > REAPER_OPTIMIZER_MAX_ITERATIONS) {
        return fail(error, 0U, "optimizer iteration budget must be between 1 and 64");
    }
    if (output_capacity < input->length) {
        return fail(error, 0U, "output capacity is smaller than input module");
    }
    if (!reaper_ir_verify(input, error)) return 0;
    if (input->length > SIZE_MAX / sizeof(ReaperIrNode)) {
        return fail(error, 0U, "IR module size exceeds optimizer workspace limits");
    }
    if (input->length == 0U) {
        report->iterations = 1U;
        report->converged = 1;
        return 1;
    }

    ReaperIrNode *current = malloc(input->length * sizeof *current);
    ReaperIrNode *next = malloc(input->length * sizeof *next);
    if (current == NULL || next == NULL) {
        free(current);
        free(next);
        return fail(error, 0U, "unable to allocate bounded optimizer workspace");
    }
    memcpy(current, input->nodes, input->length * sizeof *current);

    int success = 0;
    for (size_t iteration = 0U; iteration < max_iterations; ++iteration) {
        ReaperIrModule current_module = { current, input->length };
        size_t next_length = 0U;
        if (!reaper_ir_fold_constants(&current_module, next,
                input->length, &next_length, error)) {
            goto cleanup;
        }
        if (next_length != input->length) {
            (void)fail(error, iteration, "optimizer pass changed canonical IR length");
            goto cleanup;
        }

        size_t changed = 0U;
        for (size_t i = 0U; i < input->length; ++i) {
            if (!same_node(&current[i], &next[i])) ++changed;
        }
        if (changed > SIZE_MAX - report->folded_nodes) {
            (void)fail(error, iteration, "optimizer change counter overflow");
            goto cleanup;
        }
        report->iterations = iteration + 1U;
        report->folded_nodes += changed;
        memcpy(current, next, input->length * sizeof *current);

        if (changed == 0U) {
            memcpy(output, current, input->length * sizeof *output);
            *output_length = input->length;
            report->converged = 1;
            success = 1;
            break;
        }
    }
    if (!success) {
        (void)fail(error, report->iterations,
            "optimizer did not reach a fixed point within the iteration budget");
    }

cleanup:
    free(current);
    free(next);
    return success;
}
