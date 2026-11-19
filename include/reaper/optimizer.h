#ifndef REAPER_OPTIMIZER_H
#define REAPER_OPTIMIZER_H

#include "reaper/ir.h"

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Fold ADD_I64 nodes whose operands are both CONST_I64.
 *
 * The input module is verified before optimization. Output storage is
 * caller-owned and must hold at least input->length nodes. Input and output
 * may alias for in-place optimization. Signed overflow is rejected rather
 * than invoking undefined behavior or silently wrapping.
 *
 * Returns 1 on success and 0 on invalid input, insufficient capacity,
 * allocation-independent validation failure, or checked overflow.
 */
int reaper_ir_fold_constants(
    const ReaperIrModule *input,
    ReaperIrNode *output,
    size_t output_capacity,
    size_t *output_length,
    ReaperIrError *error
);

#ifdef __cplusplus
}
#endif

#endif
