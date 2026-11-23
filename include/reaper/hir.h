#ifndef REAPER_HIR_H
#define REAPER_HIR_H

#include "reaper/ast.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_HIR_NO_SYMBOL UINT32_MAX

typedef enum ReaperHirType {
    REAPER_HIR_TYPE_UNKNOWN = 0,
    REAPER_HIR_TYPE_UNIT,
    REAPER_HIR_TYPE_I64,
    REAPER_HIR_TYPE_F64,
    REAPER_HIR_TYPE_BOOL,
    REAPER_HIR_TYPE_STRING,
    REAPER_HIR_TYPE_LIST,
    REAPER_HIR_TYPE_FUNCTION
} ReaperHirType;

typedef enum ReaperHirSymbolKind {
    REAPER_HIR_SYMBOL_VALUE = 1,
    REAPER_HIR_SYMBOL_PARAMETER,
    REAPER_HIR_SYMBOL_FUNCTION,
    REAPER_HIR_SYMBOL_ITERATION
} ReaperHirSymbolKind;

typedef struct ReaperHirNode {
    ReaperAstKind kind;
    ReaperHirType type;
    uint32_t source_node;
    uint32_t left;
    uint32_t right;
    uint32_t symbol_id;
    char *text;
    size_t line;
    size_t column;
    unsigned mutable_value : 1;
} ReaperHirNode;

typedef struct ReaperHirSymbol {
    uint32_t id;
    uint32_t scope_id;
    uint32_t declaration_node;
    uint32_t parameter_count;
    ReaperHirSymbolKind kind;
    ReaperHirType type;
    ReaperHirType return_type;
    char *name;
    unsigned mutable_value : 1;
} ReaperHirSymbol;

typedef struct ReaperHirModule {
    ReaperHirNode *nodes;
    size_t node_count;
    ReaperHirSymbol *symbols;
    size_t symbol_count;
    size_t symbol_capacity;
} ReaperHirModule;

typedef struct ReaperHirError {
    size_t node_index;
    char message[256];
} ReaperHirError;

/*
 * Build a typed, name-resolved high-level IR from a complete program AST.
 *
 * This pass checks lexical scope, duplicate declarations, mutability,
 * function parameters/arity, return placement, condition types and the
 * argument-insertion semantics of the :: flow operator. Unknown value types
 * remain explicit where the current language has no declared type syntax.
 *
 * On failure the partially built module is released and returned empty.
 */
int reaper_hir_build(
    const ReaperAst *ast,
    ReaperHirModule *output,
    ReaperHirError *error
);

void reaper_hir_free(ReaperHirModule *module);
const char *reaper_hir_type_name(ReaperHirType type);

#ifdef __cplusplus
}
#endif

#endif
