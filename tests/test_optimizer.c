#include "reaper/optimizer.h"

#include <assert.h>
#include <limits.h>
#include <stdio.h>

#define N REAPER_IR_NO_VALUE

static void folds_constant_add(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 19, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 23, 1, 6 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 4 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2, N, 0, 1, 1 }
    };
    ReaperIrNode out[4];
    size_t length = 0;
    ReaperIrError error;
    ReaperIrModule input = { nodes, 4 };
    assert(reaper_ir_fold_constants(&input, out, 4, &length, &error));
    assert(length == 4);
    assert(out[2].opcode == REAPER_IR_OP_CONST_I64);
    assert(out[2].immediate == 42);
    assert(out[2].lhs == N && out[2].rhs == N);
    assert(out[3].opcode == REAPER_IR_OP_RETURN && out[3].lhs == 2);
}

static void folds_dependency_chain(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 2, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 3, 1, 5 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 7, 1, 9 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 2, 3, 0, 1, 7 }
    };
    ReaperIrNode out[5];
    size_t length = 0;
    ReaperIrError error;
    ReaperIrModule input = { nodes, 5 };
    assert(reaper_ir_fold_constants(&input, out, 5, &length, &error));
    assert(length == 5);
    assert(out[2].opcode == REAPER_IR_OP_CONST_I64 && out[2].immediate == 5);
    assert(out[4].opcode == REAPER_IR_OP_CONST_I64 && out[4].immediate == 12);
}

static void folds_checked_integer_arithmetic(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 100, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 40, 1, 7 },
        { REAPER_IR_OP_SUB_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 5 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 6, 1, 11 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 7, 1, 15 },
        { REAPER_IR_OP_MUL_I64, REAPER_IR_TYPE_I64, 3, 4, 0, 1, 13 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 84, 1, 19 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 2, 1, 24 },
        { REAPER_IR_OP_DIV_I64, REAPER_IR_TYPE_I64, 6, 7, 0, 1, 22 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 2, 5, 0, 1, 27 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 9, 8, 0, 1, 31 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 10, N, 0, 1, 1 }
    };
    ReaperIrNode out[12];
    size_t length = 0;
    ReaperIrError error;
    ReaperIrModule input = { nodes, 12 };
    assert(reaper_ir_fold_constants(&input, out, 12, &length, &error));
    assert(length == 12);
    assert(out[2].opcode == REAPER_IR_OP_CONST_I64 && out[2].immediate == 60);
    assert(out[5].opcode == REAPER_IR_OP_CONST_I64 && out[5].immediate == 42);
    assert(out[8].opcode == REAPER_IR_OP_CONST_I64 && out[8].immediate == 42);
    assert(out[10].opcode == REAPER_IR_OP_CONST_I64 && out[10].immediate == 144);
}

static void rejects_invalid_constant_arithmetic(void) {
    const ReaperIrNode divide_by_zero[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 1, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 0, 1, 5 },
        { REAPER_IR_OP_DIV_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 }
    };
    const ReaperIrNode multiply_overflow[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, INT64_MAX, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 2, 1, 5 },
        { REAPER_IR_OP_MUL_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 }
    };
    const ReaperIrNode divide_overflow[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, INT64_MIN, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, -1, 1, 5 },
        { REAPER_IR_OP_DIV_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 }
    };
    const ReaperIrNode subtract_overflow[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, INT64_MIN, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 1, 1, 5 },
        { REAPER_IR_OP_SUB_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 }
    };
    const ReaperIrNode *cases[] = {
        divide_by_zero, multiply_overflow, divide_overflow, subtract_overflow
    };
    for (size_t i = 0; i < sizeof cases / sizeof cases[0]; ++i) {
        ReaperIrNode output[3];
        size_t length = 99;
        ReaperIrError error;
        ReaperIrModule input = { cases[i], 3 };
        assert(!reaper_ir_fold_constants(&input, output, 3, &length, &error));
        assert(length == 0 && error.node_index == 2);
    }
}

static void rejects_signed_overflow(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, INT64_MAX, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 1, 1, 5 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 }
    };
    ReaperIrNode out[3];
    size_t length = 99;
    ReaperIrError error;
    ReaperIrModule input = { nodes, 3 };
    assert(!reaper_ir_fold_constants(&input, out, 3, &length, &error));
    assert(length == 0);
    assert(error.node_index == 2);
}

static void rejects_small_output(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 7, 1, 1 }
    };
    ReaperIrNode out[1];
    size_t length = 0;
    ReaperIrError error;
    ReaperIrModule input = { nodes, 1 };
    assert(!reaper_ir_fold_constants(&input, out, 0, &length, &error));
}

static void supports_in_place_operation(void) {
    ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 10, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 5, 1, 5 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 }
    };
    ReaperIrModule input = { nodes, 3 };
    size_t length = 0;
    ReaperIrError error;
    assert(reaper_ir_fold_constants(&input, nodes, 3, &length, &error));
    assert(length == 3);
    assert(nodes[2].opcode == REAPER_IR_OP_CONST_I64 && nodes[2].immediate == 15);
}


static void fixed_point_pipeline_converges_and_is_idempotent(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 8, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 9, 1, 5 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2, N, 0, 1, 1 }
    };
    ReaperIrNode optimized[4], optimized_again[4];
    size_t length = 0, length_again = 0;
    ReaperIrError error;
    ReaperOptimizationReport report, second_report;
    ReaperIrModule input = { nodes, 4 };
    assert(reaper_ir_optimize_fixed_point(&input, optimized, 4, &length,
        8, &report, &error));
    assert(length == 4 && report.converged);
    assert(report.iterations == 2);
    assert(report.folded_nodes == 1);
    assert(optimized[2].opcode == REAPER_IR_OP_CONST_I64);
    assert(optimized[2].immediate == 17);

    ReaperIrModule once = { optimized, length };
    assert(reaper_ir_optimize_fixed_point(&once, optimized_again, 4,
        &length_again, 8, &second_report, &error));
    assert(length_again == length);
    assert(second_report.converged && second_report.iterations == 1);
    assert(second_report.folded_nodes == 0);
}

static void fixed_point_pipeline_rejects_exhausted_budget(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 8, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 9, 1, 5 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 }
    };
    ReaperIrNode optimized[3];
    size_t length = 77;
    ReaperIrError error;
    ReaperOptimizationReport report;
    ReaperIrModule input = { nodes, 3 };
    assert(!reaper_ir_optimize_fixed_point(&input, optimized, 3, &length,
        1, &report, &error));
    assert(length == 0);
    assert(!report.converged);
    assert(report.iterations == 1);
}

static void fixed_point_pipeline_rejects_unbounded_budget(void) {
    ReaperIrNode output[1];
    size_t length = 0;
    ReaperIrError error;
    ReaperOptimizationReport report;
    ReaperIrModule empty = { NULL, 0 };
    assert(!reaper_ir_optimize_fixed_point(&empty, output, 1, &length,
        REAPER_OPTIMIZER_MAX_ITERATIONS + 1U, &report, &error));
}


int main(void) {
    folds_constant_add();
    folds_checked_integer_arithmetic();
    rejects_invalid_constant_arithmetic();
    folds_dependency_chain();
    rejects_signed_overflow();
    rejects_small_output();
    supports_in_place_operation();
    fixed_point_pipeline_converges_and_is_idempotent();
    fixed_point_pipeline_rejects_exhausted_budget();
    fixed_point_pipeline_rejects_unbounded_budget();
    puts("native optimizer tests: 8 groups passed");
    return 0;
}
