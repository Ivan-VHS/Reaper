#ifndef REAPER_OPTIMIZER_H
#define REAPER_OPTIMIZER_H

#include "reaper/ir.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_OPTIMIZER_MAX_ITERATIONS 64U

typedef struct {
    size_t iterations;
    size_t folded_nodes;
    int converged;
} ReaperOptimizationReport;

/*
 * Run verified optimizer passes to a fixed point. The current pass set
 * includes checked constant folding. The pass budget is bounded to 1..64.
 * Input and output may alias. A budget exhausted before convergence fails.
 */
int reaper_ir_optimize_fixed_point(
    const ReaperIrModule *input,
    ReaperIrNode *output,
    size_t output_capacity,
    size_t *output_length,
    size_t max_iterations,
    ReaperOptimizationReport *report,
    ReaperIrError *error
);

/*
 * Fold checked ADD/SUB/MUL/DIV and NEG integer nodes whose operands are
 * constants. Division by zero and signed i64 overflow are rejected.
 * The input module is verified before optimization. Output storage is
 * caller-owned and must hold at least input->length nodes. Input and output
 * may alias. Arithmetic never invokes undefined behavior or silently wraps.
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
