#ifndef REAPER_LOWER_H
#define REAPER_LOWER_H

#include "reaper/ast.h"
#include "reaper/ir.h"

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Lower the currently supported integer-expression subset of the owned AST
 * into verified canonical IR, followed by a RETURN node.
 *
 * Supported source forms: integer literals and binary integer addition.
 * All other AST forms fail explicitly; no coercion or guessed semantics.
 *
 * The caller owns output storage and must provide ast->length + 1 slots.
 * The resulting IR references only earlier nodes and is verified before
 * success is reported. Signed overflow is left explicit in ADD_I64 IR and
 * is rejected if encountered by the checked constant-folding pass.
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
