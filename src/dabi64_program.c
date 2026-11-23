#include "reaper/dabi64_program.h"

#include <stdio.h>
#include <string.h>
#include <limits.h>

static ReaperDabiStatus program_fail(ReaperDabiProgramError *error,
                                     uint64_t index, ReaperDabiStatus status,
                                     const char *message) {
    if (error != NULL) {
        error->instruction_index = index;
        error->status = status;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
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

static const ReaperDabiCallDescriptor *find_call(uint32_t id) {
    uint64_t count = 0u;
    const ReaperDabiCallDescriptor *table = reaper_dabi_call_table(&count);
    for (uint64_t i = 0u; i < count; ++i)
        if (table[i].id == id) return &table[i];
    return NULL;
}

ReaperDabiStatus reaper_dabi_lower_ir(
    const ReaperIrModule *module,
    ReaperDabiInstruction *output,
    uint64_t output_capacity,
    uint64_t step_limit,
    ReaperDabiProgram *program_out,
    ReaperDabiProgramError *error
) {
    ReaperIrError ir_error;
    if (program_out != NULL) memset(program_out, 0, sizeof *program_out);
    if (module == NULL || output == NULL || program_out == NULL ||
        step_limit == 0u || module->length == 0u ||
        output_capacity < (uint64_t)module->length)
        return program_fail(error, 0u, REAPER_DABI_INVALID_ARGUMENT,
                            "valid IR, output storage and step limit are required");
    if (!reaper_ir_verify(module, &ir_error))
        return program_fail(error, (uint64_t)ir_error.node_index,
                            REAPER_DABI_INVALID_ARGUMENT, ir_error.message);
    for (size_t i = 0u; i < module->length; ++i) {
        const ReaperIrNode *node = &module->nodes[i];
        ReaperDabiInstruction instruction;
        memset(&instruction, 0, sizeof instruction);
        instruction.dst = (uint64_t)i;
        instruction.auxiliary_dst = REAPER_DABI_PROGRAM_NO_SLOT;
        instruction.lhs = REAPER_DABI_PROGRAM_NO_SLOT;
        instruction.rhs = REAPER_DABI_PROGRAM_NO_SLOT;
        instruction.target = 0u;
        instruction.bytes = NULL;
        instruction.byte_length = 0u;
        switch (node->opcode) {
        case REAPER_IR_OP_CONST_I64:
            instruction.opcode = REAPER_DABI_OP_CONST_I64;
            instruction.immediate = node->immediate;
            break;
        case REAPER_IR_OP_ADD_I64:
            instruction.opcode = REAPER_DABI_OP_ADD_I64;
            instruction.lhs = node->lhs;
            instruction.rhs = node->rhs;
            break;
        case REAPER_IR_OP_SUB_I64:
            instruction.opcode = REAPER_DABI_OP_SUB_I64;
            instruction.lhs = node->lhs;
            instruction.rhs = node->rhs;
            break;
        case REAPER_IR_OP_MUL_I64:
            instruction.opcode = REAPER_DABI_OP_MUL_I64;
            instruction.lhs = node->lhs;
            instruction.rhs = node->rhs;
            break;
        case REAPER_IR_OP_DIV_I64:
            instruction.opcode = REAPER_DABI_OP_DIV_I64;
            instruction.lhs = node->lhs;
            instruction.rhs = node->rhs;
            break;
        case REAPER_IR_OP_RETURN:
            instruction.opcode = REAPER_DABI_OP_RETURN;
            instruction.dst = REAPER_DABI_PROGRAM_NO_SLOT;
            instruction.lhs = node->lhs;
            break;
        default:
            return program_fail(error, (uint64_t)i, REAPER_DABI_UNSUPPORTED,
                                "canonical IR opcode has no DABI64 lowering");
        }
        output[i] = instruction;
    }
    program_out->instructions = output;
    program_out->instruction_count = (uint64_t)module->length;
    program_out->slot_count = (uint64_t)module->length;
    program_out->step_limit = step_limit;
    return reaper_dabi_program_verify(program_out, error);
}

ReaperDabiStatus reaper_dabi_program_verify(
    const ReaperDabiProgram *program, ReaperDabiProgramError *error
) {
    if (error != NULL) {
        error->instruction_index = 0u;
        error->status = REAPER_DABI_OK;
        error->message[0] = '\0';
    }
    if (program == NULL || program->instructions == NULL ||
        program->instruction_count == 0u)
        return program_fail(error, 0u, REAPER_DABI_INVALID_ARGUMENT,
                            "program and instructions are required");
    if (program->slot_count == 0u ||
        program->slot_count > REAPER_DABI_PROGRAM_MAX_SLOTS)
        return program_fail(error, 0u, REAPER_DABI_RANGE_ERROR,
                            "program slot count is outside the supported range");
    if (program->step_limit == 0u)
        return program_fail(error, 0u, REAPER_DABI_RANGE_ERROR,
                            "program step limit must be positive");

    uint64_t return_count = 0u;
    for (uint64_t i = 0u; i < program->instruction_count; ++i) {
        const ReaperDabiInstruction *instruction = &program->instructions[i];
        switch (instruction->opcode) {
        case REAPER_DABI_OP_CONST_I64:
            if (instruction->dst >= program->slot_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "CONST_I64 destination is out of range");
            break;
        case REAPER_DABI_OP_ADD_I64:
        case REAPER_DABI_OP_SUB_I64:
        case REAPER_DABI_OP_MUL_I64:
        case REAPER_DABI_OP_DIV_I64:
            if (instruction->dst >= program->slot_count ||
                instruction->lhs >= program->slot_count ||
                instruction->rhs >= program->slot_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "integer operation slot is out of range");
            break;
        case REAPER_DABI_OP_CONST_STRING:
            if (instruction->dst >= program->slot_count ||
                (instruction->byte_length != 0u && instruction->bytes == NULL))
                return program_fail(error, i, REAPER_DABI_INVALID_ARGUMENT,
                                    "CONST_STRING requires valid destination and bytes");
            break;
        case REAPER_DABI_OP_CALL: {
            const ReaperDabiCallDescriptor *call = find_call(instruction->call_id);
            if (call == NULL)
                return program_fail(error, i, REAPER_DABI_UNSUPPORTED,
                                    "CALL references an unknown runtime function");
            uint64_t arity = call->min_arity;
            if (call->min_arity != call->max_arity)
                return program_fail(error, i, REAPER_DABI_UNSUPPORTED,
                                    "variable-arity calls are not supported by this IR");
            if (arity > 0u && instruction->lhs >= program->slot_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "CALL first argument is out of range");
            if (arity > 1u && instruction->rhs >= program->slot_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "CALL second argument is out of range");
            if (arity == 0u && instruction->lhs != REAPER_DABI_PROGRAM_NO_SLOT)
                return program_fail(error, i, REAPER_DABI_INVALID_ARGUMENT,
                                    "zero-argument CALL must use NO_SLOT");
            if (arity < 2u && instruction->rhs != REAPER_DABI_PROGRAM_NO_SLOT)
                return program_fail(error, i, REAPER_DABI_INVALID_ARGUMENT,
                                    "CALL has an unexpected second argument");
            if (instruction->dst != REAPER_DABI_PROGRAM_NO_SLOT &&
                instruction->dst >= program->slot_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "CALL result slot is out of range");
            if (instruction->auxiliary_dst != REAPER_DABI_PROGRAM_NO_SLOT &&
                instruction->auxiliary_dst >= program->slot_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "CALL auxiliary slot is out of range");
            if (instruction->auxiliary_dst != REAPER_DABI_PROGRAM_NO_SLOT &&
                instruction->call_id != REAPER_DABI_CALL_ITER_NEXT)
                return program_fail(error, i, REAPER_DABI_INVALID_ARGUMENT,
                                    "only iterator.next produces an auxiliary value");
            if (instruction->call_id == REAPER_DABI_CALL_ITER_NEXT &&
                (instruction->dst == REAPER_DABI_PROGRAM_NO_SLOT ||
                 instruction->auxiliary_dst == REAPER_DABI_PROGRAM_NO_SLOT))
                return program_fail(error, i, REAPER_DABI_INVALID_ARGUMENT,
                                    "iterator.next requires two result slots");
            break;
        }
        case REAPER_DABI_OP_JUMP:
            if (instruction->target >= program->instruction_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "JUMP target is outside the program");
            break;
        case REAPER_DABI_OP_JUMP_IF_FALSE:
            if (instruction->lhs >= program->slot_count ||
                instruction->target >= program->instruction_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "conditional branch slot or target is out of range");
            break;
        case REAPER_DABI_OP_RETURN:
            if (instruction->lhs >= program->slot_count)
                return program_fail(error, i, REAPER_DABI_RANGE_ERROR,
                                    "RETURN result slot is out of range");
            return_count++;
            break;
        default:
            return program_fail(error, i, REAPER_DABI_UNSUPPORTED,
                                "unknown DABI64 program opcode");
        }
    }
    if (return_count == 0u)
        return program_fail(error, program->instruction_count,
                            REAPER_DABI_INVALID_ARGUMENT,
                            "program has no RETURN instruction");
    return REAPER_DABI_OK;
}

ReaperDabiStatus reaper_dabi_program_execute(
    ReaperDabiRuntime *runtime,
    const ReaperDabiProgram *program,
    ReaperDabiValue *result,
    ReaperDabiProgramError *error
) {
    ReaperDabiFrame frame;
    ReaperDabiStatus status;
    uint64_t pc = 0u;
    uint64_t steps = 0u;
    int returned = 0;

    if (result != NULL) *result = reaper_dabi_unit();
    if (runtime == NULL || result == NULL)
        return program_fail(error, 0u, REAPER_DABI_INVALID_ARGUMENT,
                            "runtime and result output are required");
    status = reaper_dabi_program_verify(program, error);
    if (status != REAPER_DABI_OK) return status;
    status = reaper_dabi_frame_init(&frame, runtime);
    if (status != REAPER_DABI_OK)
        return program_fail(error, 0u, status, "cannot initialize execution frame");

    for (uint64_t i = 0u; i < program->slot_count; ++i) {
        uint64_t slot = REAPER_DABI64_NO_SLOT;
        ReaperDabiValue unit = reaper_dabi_unit();
        status = reaper_dabi_frame_hold(&frame, &unit, &slot);
        if (status != REAPER_DABI_OK) {
            status = program_fail(error, i, status, "cannot allocate value slot");
            goto cleanup;
        }
    }

    while (pc < program->instruction_count) {
        const ReaperDabiInstruction *instruction = &program->instructions[pc];
        if (++steps > program->step_limit) {
            status = program_fail(error, pc, REAPER_DABI_RANGE_ERROR,
                                  "DABI64 program step limit exceeded");
            goto cleanup;
        }
        switch (instruction->opcode) {
        case REAPER_DABI_OP_CONST_I64: {
            ReaperDabiValue value = reaper_dabi_i64(instruction->immediate);
            status = reaper_dabi_frame_set(&frame, instruction->dst, &value);
            if (status != REAPER_DABI_OK) goto instruction_error;
            pc++;
            break;
        }
        case REAPER_DABI_OP_ADD_I64:
        case REAPER_DABI_OP_SUB_I64:
        case REAPER_DABI_OP_MUL_I64:
        case REAPER_DABI_OP_DIV_I64: {
            const ReaperDabiValue *left = &frame.values[instruction->lhs];
            const ReaperDabiValue *right = &frame.values[instruction->rhs];
            int64_t value = 0;
            if (left->tag != REAPER_DABI_TAG_I64 || right->tag != REAPER_DABI_TAG_I64) {
                status = REAPER_DABI_TYPE_ERROR;
                goto instruction_error;
            }
            if (instruction->opcode == REAPER_DABI_OP_ADD_I64 &&
                !add_i64_checked(left->payload.i64, right->payload.i64, &value)) {
                status = REAPER_DABI_RANGE_ERROR;
                goto instruction_error;
            }
            if (instruction->opcode == REAPER_DABI_OP_SUB_I64 &&
                !sub_i64_checked(left->payload.i64, right->payload.i64, &value)) {
                status = REAPER_DABI_RANGE_ERROR;
                goto instruction_error;
            }
            if (instruction->opcode == REAPER_DABI_OP_MUL_I64 &&
                !mul_i64_checked(left->payload.i64, right->payload.i64, &value)) {
                status = REAPER_DABI_RANGE_ERROR;
                goto instruction_error;
            }
            if (instruction->opcode == REAPER_DABI_OP_DIV_I64) {
                if (right->payload.i64 == 0 ||
                    (left->payload.i64 == INT64_MIN && right->payload.i64 == -1)) {
                    status = REAPER_DABI_RANGE_ERROR;
                    goto instruction_error;
                }
                value = left->payload.i64 / right->payload.i64;
            }
            ReaperDabiValue output_value = reaper_dabi_i64(value);
            status = reaper_dabi_frame_set(&frame, instruction->dst, &output_value);
            if (status != REAPER_DABI_OK) goto instruction_error;
            pc++;
            break;
        }
        case REAPER_DABI_OP_CONST_STRING: {
            ReaperDabiValue value = reaper_dabi_unit();
            status = reaper_dabi_string_new(runtime, instruction->bytes,
                instruction->byte_length, &value);
            if (status == REAPER_DABI_OK)
                status = reaper_dabi_frame_set(&frame, instruction->dst, &value);
            reaper_dabi_value_drop(runtime, &value);
            if (status != REAPER_DABI_OK) goto instruction_error;
            pc++;
            break;
        }
        case REAPER_DABI_OP_CALL: {
            ReaperDabiValue arguments[2] = {
                reaper_dabi_unit(), reaper_dabi_unit()
            };
            ReaperDabiValue call_result = reaper_dabi_unit();
            ReaperDabiValue auxiliary = reaper_dabi_unit();
            const ReaperDabiCallDescriptor *call = find_call(instruction->call_id);
            uint64_t arity = call->min_arity;
            if (arity > 0u) {
                status = reaper_dabi_value_copy(runtime,
                    &frame.values[instruction->lhs], &arguments[0]);
                if (status != REAPER_DABI_OK) goto call_cleanup;
            }
            if (arity > 1u) {
                status = reaper_dabi_value_copy(runtime,
                    &frame.values[instruction->rhs], &arguments[1]);
                if (status != REAPER_DABI_OK) goto call_cleanup;
            }
            status = reaper_dabi_dispatch(runtime, instruction->call_id,
                arguments, arity, &call_result, &auxiliary);
            if (status == REAPER_DABI_OK &&
                instruction->dst != REAPER_DABI_PROGRAM_NO_SLOT)
                status = reaper_dabi_frame_set(&frame, instruction->dst, &call_result);
            if (status == REAPER_DABI_OK &&
                instruction->auxiliary_dst != REAPER_DABI_PROGRAM_NO_SLOT)
                status = reaper_dabi_frame_set(&frame, instruction->auxiliary_dst,
                                               &auxiliary);
call_cleanup:
            reaper_dabi_value_drop(runtime, &arguments[0]);
            reaper_dabi_value_drop(runtime, &arguments[1]);
            reaper_dabi_value_drop(runtime, &call_result);
            reaper_dabi_value_drop(runtime, &auxiliary);
            if (status != REAPER_DABI_OK) goto instruction_error;
            pc++;
            break;
        }
        case REAPER_DABI_OP_JUMP:
            pc = instruction->target;
            break;
        case REAPER_DABI_OP_JUMP_IF_FALSE: {
            const ReaperDabiValue *condition = &frame.values[instruction->lhs];
            if (condition->tag != REAPER_DABI_TAG_BOOL) {
                status = REAPER_DABI_TYPE_ERROR;
                goto instruction_error;
            }
            pc = condition->payload.i64 == 0 ? instruction->target : pc + 1u;
            break;
        }
        case REAPER_DABI_OP_RETURN:
            status = reaper_dabi_value_copy(runtime,
                &frame.values[instruction->lhs], result);
            if (status != REAPER_DABI_OK) goto instruction_error;
            returned = 1;
            pc = program->instruction_count;
            break;
        default:
            status = REAPER_DABI_UNSUPPORTED;
            goto instruction_error;
        }
        continue;

instruction_error:
        status = program_fail(error, pc, status, reaper_dabi_status_name(status));
        goto cleanup;
    }

    if (!returned)
        status = program_fail(error, pc, REAPER_DABI_INVALID_ARGUMENT,
                              "program reached the end without RETURN");
    else
        status = REAPER_DABI_OK;

cleanup:
    reaper_dabi_frame_destroy(&frame);
    if (status != REAPER_DABI_OK) reaper_dabi_value_drop(runtime, result);
    return status;
}

const char *reaper_dabi_program_opcode_name(ReaperDabiProgramOpcode opcode) {
    switch (opcode) {
    case REAPER_DABI_OP_CONST_I64: return "const.i64";
    case REAPER_DABI_OP_ADD_I64: return "add.i64";
    case REAPER_DABI_OP_SUB_I64: return "sub.i64";
    case REAPER_DABI_OP_MUL_I64: return "mul.i64";
    case REAPER_DABI_OP_DIV_I64: return "div.i64";
    case REAPER_DABI_OP_CONST_STRING: return "const.string";
    case REAPER_DABI_OP_CALL: return "call";
    case REAPER_DABI_OP_JUMP: return "jump";
    case REAPER_DABI_OP_JUMP_IF_FALSE: return "jump.if_false";
    case REAPER_DABI_OP_RETURN: return "return";
    default: return "invalid";
    }
}
