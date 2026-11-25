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

static int execute_binary(ReaperIrOpcode opcode, int64_t left, int64_t right,
                          int64_t *result, ReaperIrError *error) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, left, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, right, 1, 2 },
        { opcode, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 3 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2, REAPER_IR_NO_VALUE, 0, 1, 4 }
    };
    const ReaperIrModule module = { nodes, 4 };
    int64_t values[4] = {0};
    return reaper_ir_execute_i64(&module, values, 4, result, error);
}

static void test_deterministic_execution(void) {
    ReaperIrError error; int64_t result = -1;
    assert(execute_binary(REAPER_IR_OP_ADD_I64, 20, 22, &result, &error) && result == 42);
    assert(execute_binary(REAPER_IR_OP_SUB_I64, 50, 8, &result, &error) && result == 42);
    assert(execute_binary(REAPER_IR_OP_MUL_I64, 6, 7, &result, &error) && result == 42);
    assert(execute_binary(REAPER_IR_OP_DIV_I64, 84, 2, &result, &error) && result == 42);
}

static void test_arithmetic_failures_are_explicit(void) {
    ReaperIrError error; int64_t result = 777;
    assert(!execute_binary(REAPER_IR_OP_ADD_I64, INT64_MAX, 1, &result, &error));
    assert(strstr(error.message, "overflow") != NULL && result == 777);
    assert(!execute_binary(REAPER_IR_OP_SUB_I64, INT64_MIN, 1, &result, &error));
    assert(strstr(error.message, "overflow") != NULL && result == 777);
    assert(!execute_binary(REAPER_IR_OP_MUL_I64, INT64_MAX, 2, &result, &error));
    assert(strstr(error.message, "overflow") != NULL && result == 777);
    assert(!execute_binary(REAPER_IR_OP_MUL_I64, INT64_MIN, -1, &result, &error));
    assert(strstr(error.message, "overflow") != NULL && result == 777);
    assert(!execute_binary(REAPER_IR_OP_DIV_I64, INT64_MIN, -1, &result, &error));
    assert(strstr(error.message, "overflow") != NULL && result == 777);
    assert(!execute_binary(REAPER_IR_OP_DIV_I64, 7, 0, &result, &error));
    assert(strstr(error.message, "zero") != NULL && result == 777);
}

static void test_execution_contract(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 7, 1, 1 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 0, REAPER_IR_NO_VALUE, 0, 1, 2 }
    };
    const ReaperIrModule module = { nodes, 2 };
    ReaperIrError error; int64_t values[2] = {0}; int64_t result = 123;
    assert(!reaper_ir_execute_i64(&module, values, 1, &result, &error));
    assert(strstr(error.message, "capacity") != NULL && result == 123);
    assert(reaper_ir_execute_i64(&module, values, 2, &result, &error) && result == 7);
    const ReaperIrNode no_return[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 7, 1, 1 }
    };
    const ReaperIrModule invalid = { no_return, 1 }; result = 123;
    assert(!reaper_ir_execute_i64(&invalid, values, 2, &result, &error));
    assert(strstr(error.message, "RETURN") != NULL && result == 123);
}


static int execute_binary_u32(ReaperIrOpcode opcode, uint32_t left, uint32_t right,
                              uint32_t *result, ReaperIrError *error) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_U32, REAPER_IR_TYPE_U32, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, (int64_t)left, 1, 1 },
        { REAPER_IR_OP_CONST_U32, REAPER_IR_TYPE_U32, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, (int64_t)right, 1, 2 },
        { opcode, REAPER_IR_TYPE_U32, 0, 1, 0, 1, 3 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2, REAPER_IR_NO_VALUE, 0, 1, 4 }
    };
    const ReaperIrModule module = { nodes, 4 };
    uint32_t values[4] = {0};
    return reaper_ir_execute_u32(&module, values, 4, result, error);
}

static void test_u32_verification_and_execution(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_U32, REAPER_IR_TYPE_U32, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 20, 1, 1 },
        { REAPER_IR_OP_CONST_U32, REAPER_IR_TYPE_U32, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 22, 1, 2 },
        { REAPER_IR_OP_ADD_U32, REAPER_IR_TYPE_U32, 0, 1, 0, 1, 3 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2, REAPER_IR_NO_VALUE, 0, 1, 4 }
    };
    const ReaperIrModule module = { nodes, 4 };
    ReaperIrError error;
    uint32_t values[4] = {0};
    uint32_t result = 0;
    assert(reaper_ir_verify(&module, &error));
    assert(strcmp(reaper_ir_type_name(REAPER_IR_TYPE_U32), "u32") == 0);
    assert(strcmp(reaper_ir_opcode_name(REAPER_IR_OP_ADD_U32), "add.u32") == 0);
    assert(reaper_ir_execute_u32(&module, values, 4, &result, &error));
    assert(result == 42u);

    assert(execute_binary_u32(REAPER_IR_OP_ADD_U32, 20u, 22u, &result, &error) && result == 42u);
    assert(execute_binary_u32(REAPER_IR_OP_SUB_U32, 50u, 8u, &result, &error) && result == 42u);
    assert(execute_binary_u32(REAPER_IR_OP_MUL_U32, 6u, 7u, &result, &error) && result == 42u);
    assert(execute_binary_u32(REAPER_IR_OP_DIV_U32, 84u, 2u, &result, &error) && result == 42u);
}

static void test_u32_arithmetic_failures_are_explicit(void) {
    ReaperIrError error;
    uint32_t result = 777u;
    assert(!execute_binary_u32(REAPER_IR_OP_ADD_U32, UINT32_MAX, 1u, &result, &error));
    assert(strstr(error.message, "overflow") != NULL && result == 777u);
    assert(!execute_binary_u32(REAPER_IR_OP_SUB_U32, 0u, 1u, &result, &error));
    assert(strstr(error.message, "underflow") != NULL && result == 777u);
    assert(!execute_binary_u32(REAPER_IR_OP_MUL_U32, UINT32_MAX, 2u, &result, &error));
    assert(strstr(error.message, "overflow") != NULL && result == 777u);
    assert(!execute_binary_u32(REAPER_IR_OP_DIV_U32, 7u, 0u, &result, &error));
    assert(strstr(error.message, "zero") != NULL && result == 777u);
}

static void test_u32_constants_and_type_errors_are_rejected(void) {
    const ReaperIrNode negative_constant[] = {
        { REAPER_IR_OP_CONST_U32, REAPER_IR_TYPE_U32, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, -1, 1, 1 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 0, REAPER_IR_NO_VALUE, 0, 1, 2 }
    };
    const ReaperIrModule negative_module = { negative_constant, 2 };
    const ReaperIrNode oversized_constant[] = {
        { REAPER_IR_OP_CONST_U32, REAPER_IR_TYPE_U32, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, (int64_t)UINT32_MAX + 1, 1, 1 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 0, REAPER_IR_NO_VALUE, 0, 1, 2 }
    };
    const ReaperIrModule oversized_module = { oversized_constant, 2 };
    const ReaperIrNode mixed_operands[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 1, 1, 1 },
        { REAPER_IR_OP_CONST_U32, REAPER_IR_TYPE_U32, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 2, 1, 2 },
        { REAPER_IR_OP_ADD_U32, REAPER_IR_TYPE_U32, 0, 1, 0, 1, 3 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2, REAPER_IR_NO_VALUE, 0, 1, 4 }
    };
    const ReaperIrModule mixed_module = { mixed_operands, 4 };
    ReaperIrError error;
    assert(!reaper_ir_verify(&negative_module, &error));
    assert(strstr(error.message, "fit in u32") != NULL);
    assert(!reaper_ir_verify(&oversized_module, &error));
    assert(strstr(error.message, "fit in u32") != NULL);
    assert(!reaper_ir_verify(&mixed_module, &error));
    assert(strstr(error.message, "both be u32") != NULL);
}

static void test_u32_executor_checks_capacity_and_return_type(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_U32, REAPER_IR_TYPE_U32, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 7, 1, 1 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 0, REAPER_IR_NO_VALUE, 0, 1, 2 }
    };
    const ReaperIrModule module = { nodes, 2 };
    ReaperIrError error;
    uint32_t values[2] = {0};
    uint32_t result = 123u;
    assert(!reaper_ir_execute_u32(&module, values, 1, &result, &error));
    assert(strstr(error.message, "capacity") != NULL && result == 123u);
    assert(reaper_ir_execute_u32(&module, values, 2, &result, &error) && result == 7u);

    const ReaperIrNode i64_nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64, REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 7, 1, 1 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 0, REAPER_IR_NO_VALUE, 0, 1, 2 }
    };
    const ReaperIrModule i64_module = { i64_nodes, 2 };
    result = 123u;
    assert(!reaper_ir_execute_u32(&i64_module, values, 2, &result, &error));
    assert(strstr(error.message, "requires a u32") != NULL && result == 123u);
}

int main(void) {
    test_valid_module();
    test_forward_reference_rejected();
    test_type_mismatch_rejected();
    test_null_module_rejected();
    test_deterministic_execution();
    test_arithmetic_failures_are_explicit();
    test_execution_contract();
    test_u32_verification_and_execution();
    test_u32_arithmetic_failures_are_explicit();
    test_u32_constants_and_type_errors_are_rejected();
    test_u32_executor_checks_capacity_and_return_type();
    puts("native IR tests: 11 groups passed");
    return 0;
}
