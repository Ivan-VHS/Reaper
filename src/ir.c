#include "reaper/ir.h"

#include <stdio.h>
#include <string.h>

static int reject(ReaperIrError *error, size_t index, const char *message) {
    if (error != NULL) {
        error->node_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static int valid_ref(uint32_t ref, size_t current) {
    return ref != REAPER_IR_NO_VALUE && (size_t)ref < current;
}

int reaper_ir_verify(const ReaperIrModule *module, ReaperIrError *error) {
    if (error != NULL) {
        error->node_index = 0;
        error->message[0] = '\0';
    }
    if (module == NULL || (module->length != 0 && module->nodes == NULL))
        return reject(error, 0, "module and node storage are required");

    for (size_t i = 0; i < module->length; ++i) {
        const ReaperIrNode *node = &module->nodes[i];
        switch (node->opcode) {
        case REAPER_IR_OP_CONST_I64:
            if (node->type != REAPER_IR_TYPE_I64)
                return reject(error, i, "CONST_I64 must produce i64");
            if (node->lhs != REAPER_IR_NO_VALUE || node->rhs != REAPER_IR_NO_VALUE)
                return reject(error, i, "CONST_I64 cannot have operands");
            break;
        case REAPER_IR_OP_ADD_I64:
        case REAPER_IR_OP_SUB_I64:
        case REAPER_IR_OP_MUL_I64:
        case REAPER_IR_OP_DIV_I64:
            if (node->type != REAPER_IR_TYPE_I64)
                return reject(error, i, "integer arithmetic must produce i64");
            if (!valid_ref(node->lhs, i) || !valid_ref(node->rhs, i))
                return reject(error, i, "integer arithmetic operands must reference earlier nodes");
            if (module->nodes[node->lhs].type != REAPER_IR_TYPE_I64 ||
                module->nodes[node->rhs].type != REAPER_IR_TYPE_I64)
                return reject(error, i, "integer arithmetic operands must both be i64");
            break;
        case REAPER_IR_OP_RETURN:
            if (node->type != REAPER_IR_TYPE_UNIT)
                return reject(error, i, "RETURN must produce unit");
            if (!valid_ref(node->lhs, i) || node->rhs != REAPER_IR_NO_VALUE)
                return reject(error, i, "RETURN requires one earlier value operand");
            break;
        default:
            return reject(error, i, "unknown or unsupported IR opcode");
        }
    }
    return 1;
}

const char *reaper_ir_type_name(ReaperIrType type) {
    switch (type) {
    case REAPER_IR_TYPE_I64: return "i64";
    case REAPER_IR_TYPE_BOOL: return "bool";
    case REAPER_IR_TYPE_UNIT: return "unit";
    default: return "invalid";
    }
}

const char *reaper_ir_opcode_name(ReaperIrOpcode opcode) {
    switch (opcode) {
    case REAPER_IR_OP_CONST_I64: return "const.i64";
    case REAPER_IR_OP_ADD_I64: return "add.i64";
    case REAPER_IR_OP_RETURN: return "return";
    case REAPER_IR_OP_SUB_I64: return "sub.i64";
    case REAPER_IR_OP_MUL_I64: return "mul.i64";
    case REAPER_IR_OP_DIV_I64: return "div.i64";
    default: return "invalid";
    }
}
