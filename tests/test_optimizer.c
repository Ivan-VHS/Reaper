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

static void preserves_nonconstant_add(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, N, N, 1, 1, 1 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 0, 0, 1, 3 }
    };
    ReaperIrNode out[2];
    size_t length = 0;
    ReaperIrError error;
    ReaperIrModule input = { nodes, 2 };
    assert(reaper_ir_fold_constants(&input, out, 2, &length, &error));
    assert(out[1].opcode == REAPER_IR_OP_CONST_I64);
    assert(out[1].immediate == 2);
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

int main(void) {
    folds_constant_add();
    preserves_nonconstant_add();
    rejects_signed_overflow();
    rejects_small_output();
    puts("native optimizer tests: 4 groups passed");
    return 0;
}
