#include "reaper/ir.h"

#include <stdio.h>
#include <string.h>
#include <stdint.h>

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
        case REAPER_IR_OP_BIT_AND_I64:
        case REAPER_IR_OP_BIT_OR_I64:
        case REAPER_IR_OP_BIT_XOR_I64:
        case REAPER_IR_OP_SHL_I64:
        case REAPER_IR_OP_SHR_I64:
            if (node->type != REAPER_IR_TYPE_I64)
                return reject(error, i, "integer arithmetic must produce i64");
            if (!valid_ref(node->lhs, i) || !valid_ref(node->rhs, i))
                return reject(error, i, "integer arithmetic operands must reference earlier nodes");
            if (module->nodes[node->lhs].type != REAPER_IR_TYPE_I64 ||
                module->nodes[node->rhs].type != REAPER_IR_TYPE_I64)
                return reject(error, i, "integer arithmetic operands must both be i64");
            break;
        case REAPER_IR_OP_BIT_NOT_I64:
            if (node->type != REAPER_IR_TYPE_I64)
                return reject(error, i, "BIT_NOT_I64 must produce i64");
            if (!valid_ref(node->lhs, i) || node->rhs != REAPER_IR_NO_VALUE)
                return reject(error, i, "BIT_NOT_I64 requires one earlier i64 operand");
            if (module->nodes[node->lhs].type != REAPER_IR_TYPE_I64)
                return reject(error, i, "BIT_NOT_I64 operand must be i64");
            break;
        case REAPER_IR_OP_CONST_U32:
            if (node->type != REAPER_IR_TYPE_U32)
                return reject(error, i, "CONST_U32 must produce u32");
            if (node->lhs != REAPER_IR_NO_VALUE || node->rhs != REAPER_IR_NO_VALUE)
                return reject(error, i, "CONST_U32 cannot have operands");
            if (node->immediate < 0 || (uint64_t)node->immediate > UINT32_MAX)
                return reject(error, i, "CONST_U32 immediate must fit in u32");
            break;
        case REAPER_IR_OP_ADD_U32:
        case REAPER_IR_OP_SUB_U32:
        case REAPER_IR_OP_MUL_U32:
        case REAPER_IR_OP_DIV_U32:
            if (node->type != REAPER_IR_TYPE_U32)
                return reject(error, i, "unsigned arithmetic must produce u32");
            if (!valid_ref(node->lhs, i) || !valid_ref(node->rhs, i))
                return reject(error, i, "unsigned arithmetic operands must reference earlier nodes");
            if (module->nodes[node->lhs].type != REAPER_IR_TYPE_U32 ||
                module->nodes[node->rhs].type != REAPER_IR_TYPE_U32)
                return reject(error, i, "unsigned arithmetic operands must both be u32");
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

static int execute_error(ReaperIrError *error, size_t index, const char *message) {
    if (error != NULL) {
        error->node_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static int add_i64_checked(int64_t left, int64_t right, int64_t *out) {
    if ((right > 0 && left > INT64_MAX - right) ||
        (right < 0 && left < INT64_MIN - right)) return 0;
    *out = left + right;
    return 1;
}

static int sub_i64_checked(int64_t left, int64_t right, int64_t *out) {
    if ((right < 0 && left > INT64_MAX + right) ||
        (right > 0 && left < INT64_MIN + right)) return 0;
    *out = left - right;
    return 1;
}

static int mul_i64_checked(int64_t left, int64_t right, int64_t *out) {
    if (left == 0 || right == 0) { *out = 0; return 1; }
    if ((left == -1 && right == INT64_MIN) ||
        (right == -1 && left == INT64_MIN)) return 0;
    if (left > 0) {
        if ((right > 0 && left > INT64_MAX / right) ||
            (right < 0 && right < INT64_MIN / left)) return 0;
    } else {
        if ((right > 0 && left < INT64_MIN / right) ||
            (right < 0 && left < INT64_MAX / right)) return 0;
    }
    *out = left * right;
    return 1;
}

int reaper_ir_execute_i64(const ReaperIrModule *module, int64_t *values,
                          size_t value_capacity, int64_t *result,
                          ReaperIrError *error) {
    if (error != NULL) { error->node_index = 0; error->message[0] = '\0'; }
    if (!reaper_ir_verify(module, error)) return 0;
    if (module->length == 0u)
        return execute_error(error, 0u, "executable IR must contain a RETURN");
    if (values == NULL || result == NULL)
        return execute_error(error, 0u, "scratch storage and result output are required");
    if (value_capacity < module->length)
        return execute_error(error, 0u, "scratch capacity is smaller than IR length");

    size_t return_count = 0u, return_index = 0u;
    for (size_t i = 0u; i < module->length; ++i) {
        if (module->nodes[i].opcode == REAPER_IR_OP_RETURN) {
            ++return_count; return_index = i;
        }
    }
    if (return_count != 1u || return_index != module->length - 1u)
        return execute_error(error, return_index, "IR must end with exactly one RETURN");

    for (size_t i = 0u; i < module->length; ++i) {
        const ReaperIrNode *node = &module->nodes[i];
        int64_t value = 0;
        switch (node->opcode) {
        case REAPER_IR_OP_CONST_I64: value = node->immediate; break;
        case REAPER_IR_OP_ADD_I64:
            if (!add_i64_checked(values[node->lhs], values[node->rhs], &value))
                return execute_error(error, i, "signed i64 addition overflow");
            break;
        case REAPER_IR_OP_SUB_I64:
            if (!sub_i64_checked(values[node->lhs], values[node->rhs], &value))
                return execute_error(error, i, "signed i64 subtraction overflow");
            break;
        case REAPER_IR_OP_MUL_I64:
            if (!mul_i64_checked(values[node->lhs], values[node->rhs], &value))
                return execute_error(error, i, "signed i64 multiplication overflow");
            break;
        case REAPER_IR_OP_DIV_I64:
            if (values[node->rhs] == 0)
                return execute_error(error, i, "integer division by zero");
            if (values[node->lhs] == INT64_MIN && values[node->rhs] == -1)
                return execute_error(error, i, "signed i64 division overflow");
            value = values[node->lhs] / values[node->rhs];
            break;
        case REAPER_IR_OP_BIT_NOT_I64: {
            uint64_t bits = 0u;
            memcpy(&bits, &values[node->lhs], sizeof bits);
            bits = ~bits;
            memcpy(&value, &bits, sizeof value);
            break;
        }
        case REAPER_IR_OP_BIT_AND_I64:
        case REAPER_IR_OP_BIT_OR_I64:
        case REAPER_IR_OP_BIT_XOR_I64:
        case REAPER_IR_OP_SHL_I64:
        case REAPER_IR_OP_SHR_I64: {
            uint64_t left = 0u, right = 0u, bits = 0u;
            const int64_t shift = values[node->rhs];
            memcpy(&left, &values[node->lhs], sizeof left);
            memcpy(&right, &values[node->rhs], sizeof right);
            switch (node->opcode) {
            case REAPER_IR_OP_BIT_AND_I64: bits = left & right; break;
            case REAPER_IR_OP_BIT_OR_I64: bits = left | right; break;
            case REAPER_IR_OP_BIT_XOR_I64: bits = left ^ right; break;
            case REAPER_IR_OP_SHL_I64:
                if (shift < 0 || shift >= 64)
                    return execute_error(error, i, "bit shift count must be between 0 and 63");
                bits = left << (unsigned)shift;
                break;
            case REAPER_IR_OP_SHR_I64:
                if (shift < 0 || shift >= 64)
                    return execute_error(error, i, "bit shift count must be between 0 and 63");
                bits = left >> (unsigned)shift;
                break;
            default: break;
            }
            memcpy(&value, &bits, sizeof value);
            break;
        }
        case REAPER_IR_OP_RETURN:
            *result = values[node->lhs];
            return 1;
        default:
            return execute_error(error, i, "unsupported executable IR opcode");
        }
        values[i] = value;
    }
    return execute_error(error, module->length - 1u, "IR execution reached no RETURN");
}
int reaper_ir_execute_u32(const ReaperIrModule *module, uint32_t *values,
                          size_t value_capacity, uint32_t *result,
                          ReaperIrError *error) {
    if (error != NULL) { error->node_index = 0; error->message[0] = '\0'; }
    if (!reaper_ir_verify(module, error)) return 0;
    if (module->length == 0u)
        return execute_error(error, 0u, "executable IR must contain a RETURN");
    if (values == NULL || result == NULL)
        return execute_error(error, 0u, "scratch storage and result output are required");
    if (value_capacity < module->length)
        return execute_error(error, 0u, "scratch capacity is smaller than IR length");

    size_t return_count = 0u, return_index = 0u;
    for (size_t i = 0u; i < module->length; ++i) {
        if (module->nodes[i].opcode == REAPER_IR_OP_RETURN) {
            ++return_count;
            return_index = i;
        }
    }
    if (return_count != 1u || return_index != module->length - 1u)
        return execute_error(error, return_index, "IR must end with exactly one RETURN");
    if (module->nodes[return_index].lhs >= module->length ||
        module->nodes[module->nodes[return_index].lhs].type != REAPER_IR_TYPE_U32)
        return execute_error(error, return_index, "u32 execution requires a u32 return value");

    for (size_t i = 0u; i < module->length; ++i) {
        const ReaperIrNode *node = &module->nodes[i];
        uint32_t value = 0u;
        switch (node->opcode) {
        case REAPER_IR_OP_CONST_U32:
            value = (uint32_t)node->immediate;
            break;
        case REAPER_IR_OP_ADD_U32: {
            uint32_t left = values[node->lhs];
            uint32_t right = values[node->rhs];
            if (left > UINT32_MAX - right)
                return execute_error(error, i, "unsigned u32 addition overflow");
            value = left + right;
            break;
        }
        case REAPER_IR_OP_SUB_U32: {
            uint32_t left = values[node->lhs];
            uint32_t right = values[node->rhs];
            if (left < right)
                return execute_error(error, i, "unsigned u32 subtraction underflow");
            value = left - right;
            break;
        }
        case REAPER_IR_OP_MUL_U32: {
            uint32_t left = values[node->lhs];
            uint32_t right = values[node->rhs];
            if (right != 0u && left > UINT32_MAX / right)
                return execute_error(error, i, "unsigned u32 multiplication overflow");
            value = left * right;
            break;
        }
        case REAPER_IR_OP_DIV_U32:
            if (values[node->rhs] == 0u)
                return execute_error(error, i, "unsigned u32 division by zero");
            value = values[node->lhs] / values[node->rhs];
            break;
        case REAPER_IR_OP_RETURN:
            *result = values[node->lhs];
            return 1;
        default:
            return execute_error(error, i, "unsupported opcode in u32 executor");
        }
        values[i] = value;
    }
    return execute_error(error, module->length - 1u, "IR execution reached no RETURN");
}

const char *reaper_ir_type_name(ReaperIrType type) {
    switch (type) {
    case REAPER_IR_TYPE_I64: return "i64";
    case REAPER_IR_TYPE_BOOL: return "bool";
    case REAPER_IR_TYPE_UNIT: return "unit";
    case REAPER_IR_TYPE_U32: return "u32";
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
    case REAPER_IR_OP_CONST_U32: return "const.u32";
    case REAPER_IR_OP_ADD_U32: return "add.u32";
    case REAPER_IR_OP_SUB_U32: return "sub.u32";
    case REAPER_IR_OP_MUL_U32: return "mul.u32";
    case REAPER_IR_OP_DIV_U32: return "div.u32";
    case REAPER_IR_OP_BIT_AND_I64: return "bit.and.i64";
    case REAPER_IR_OP_BIT_OR_I64: return "bit.or.i64";
    case REAPER_IR_OP_BIT_XOR_I64: return "bit.xor.i64";
    case REAPER_IR_OP_BIT_NOT_I64: return "bit.not.i64";
    case REAPER_IR_OP_SHL_I64: return "shift.left.i64";
    case REAPER_IR_OP_SHR_I64: return "shift.right.logical.i64";
    default: return "invalid";
    }
}
