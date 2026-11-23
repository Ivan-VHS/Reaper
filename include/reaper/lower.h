#ifndef REAPER_LOWER_H
#define REAPER_LOWER_H

#include "reaper/ast.h"
#include "reaper/ir.h"

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Lower the verified i64 expression subset into canonical, topologically
 * ordered IR and append one RETURN instruction.
 *
 * Supported source forms: signed i64 literals, unary + and -, and binary
 * +, -, * and / operations. Division follows the checked signed-i64 IR
 * contract (truncation toward zero). Other syntax is rejected explicitly.
 *
 * Reserve at least 2 * ast->length + 1 output nodes. The result is verified
 * before success is reported, and no arithmetic is executed during lowering.
 */
int reaper_lower_ast_to_ir(
    const ReaperAst *ast,
    ReaperIrNode *output,
    size_t output_capacity,
    size_t *output_length,
    ReaperIrError *error
);

#ifdef __cplusplus
}
#endif

#endif
