#include "reaper/ir.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_valid_module(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 20, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 22, 1, 10 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 5 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2, REAPER_IR_NO_VALUE, 0, 2, 1 }
    };
    const ReaperIrModule module = { nodes, sizeof nodes / sizeof nodes[0] };
    ReaperIrError error;
    assert(reaper_ir_verify(&module, &error));
    assert(strcmp(reaper_ir_type_name(REAPER_IR_TYPE_I64), "i64") == 0);
    assert(strcmp(reaper_ir_opcode_name(REAPER_IR_OP_ADD_I64), "add.i64") == 0);
}

static void test_forward_reference_rejected(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 1, 1, 0, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 1, 1, 2 }
    };
    const ReaperIrModule module = { nodes, 2 };
    ReaperIrError error;
    assert(!reaper_ir_verify(&module, &error));
    assert(error.node_index == 0);
    assert(strstr(error.message, "earlier") != NULL);
}

static void test_type_mismatch_rejected(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 1, 1, 1 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_I64, 0, REAPER_IR_NO_VALUE, 0, 1, 2 }
    };
    const ReaperIrModule module = { nodes, 2 };
    ReaperIrError error;
    assert(!reaper_ir_verify(&module, &error));
    assert(error.node_index == 1);
    assert(strstr(error.message, "unit") != NULL);
}

static void test_null_module_rejected(void) {
    ReaperIrError error;
    assert(!reaper_ir_verify(NULL, &error));
    assert(strstr(error.message, "required") != NULL);
}

int main(void) {
    test_valid_module();
    test_forward_reference_rejected();
    test_type_mismatch_rejected();
    test_null_module_rejected();
    puts("native IR tests: 4 groups passed");
    return 0;
}
