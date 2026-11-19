#include "reaper/optimizer.h"

#include <limits.h>
#include <stdio.h>
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
        if (node.opcode == REAPER_IR_OP_ADD_I64) {
            const ReaperIrNode *lhs = &output[node.lhs];
            const ReaperIrNode *rhs = &output[node.rhs];
            if (lhs->opcode == REAPER_IR_OP_CONST_I64 &&
                rhs->opcode == REAPER_IR_OP_CONST_I64) {
                if (add_overflows_i64(lhs->immediate, rhs->immediate)) {
                    return fail(error, i, "constant addition overflows signed i64");
                }
                node.opcode = REAPER_IR_OP_CONST_I64;
                node.lhs = REAPER_IR_NO_VALUE;
                node.rhs = REAPER_IR_NO_VALUE;
                node.immediate = lhs->immediate + rhs->immediate;
            }
        }
        output[i] = node;
    }

    ReaperIrModule folded = { output, input->length };
    if (!reaper_ir_verify(&folded, error)) return 0;
    *output_length = input->length;
    return 1;
}
