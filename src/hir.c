#include "reaper/hir.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct ReaperHirScope {
    uint32_t id;
    uint32_t parent;
} ReaperHirScope;

typedef struct {
    const ReaperAst *ast;
    ReaperHirModule *module;
    ReaperHirError *error;
    ReaperHirScope *scopes;
    size_t scope_count;
    size_t scope_capacity;
    uint32_t current_scope;
    unsigned function_depth;
    uint32_t current_function;
} HirBuilder;

static char *copy_text(const char *source) {
    size_t length = strlen(source);
    char *copy = malloc(length + 1U);
    if (copy != NULL) memcpy(copy, source, length + 1U);
    return copy;
}

static int fail(
    HirBuilder *builder,
    size_t node_index,
    const char *message
) {
    if (builder->error != NULL && builder->error->message[0] == '\0') {
        builder->error->node_index = node_index;
        (void)snprintf(
            builder->error->message,
            sizeof builder->error->message,
            "%s",
            message
        );
    }
    return 0;
}

static const ReaperAstNode *ast_node(HirBuilder *builder, uint32_t id) {
    if (id == REAPER_AST_NO_NODE || id >= builder->ast->length) return NULL;
    return &builder->ast->items[id];
}

static int add_scope(HirBuilder *builder, uint32_t parent, uint32_t *scope_id) {
    if (builder->scope_count >= UINT32_MAX) return 0;
    if (builder->scope_count == builder->scope_capacity) {
        size_t next = builder->scope_capacity == 0U
            ? 8U : builder->scope_capacity * 2U;
        if (next < builder->scope_capacity ||
            next > SIZE_MAX / sizeof *builder->scopes) return 0;
        ReaperHirScope *scopes = realloc(
            builder->scopes, next * sizeof *builder->scopes
        );
        if (scopes == NULL) return 0;
        builder->scopes = scopes;
        builder->scope_capacity = next;
    }

    uint32_t id = (uint32_t)builder->scope_count;
    builder->scopes[builder->scope_count++] = (ReaperHirScope){id, parent};
    *scope_id = id;
    return 1;
}

static int enter_scope(HirBuilder *builder, uint32_t *previous) {
    *previous = builder->current_scope;
    uint32_t child = 0U;
    if (!add_scope(builder, builder->current_scope, &child)) return 0;
    builder->current_scope = child;
    return 1;
}

static void leave_scope(HirBuilder *builder, uint32_t previous) {
    builder->current_scope = previous;
}

static ReaperHirSymbol *symbol_at(HirBuilder *builder, uint32_t id) {
    if (id >= builder->module->symbol_count) return NULL;
    return &builder->module->symbols[id];
}

static uint32_t find_in_scope(
    HirBuilder *builder,
    uint32_t scope_id,
    const char *name
) {
    for (size_t i = builder->module->symbol_count; i > 0U; --i) {
        ReaperHirSymbol *symbol = &builder->module->symbols[i - 1U];
        if (symbol->scope_id == scope_id && strcmp(symbol->name, name) == 0)
            return symbol->id;
    }
    return REAPER_HIR_NO_SYMBOL;
}

static uint32_t resolve_symbol(HirBuilder *builder, const char *name) {
    uint32_t scope = builder->current_scope;
    for (;;) {
        uint32_t found = find_in_scope(builder, scope, name);
        if (found != REAPER_HIR_NO_SYMBOL) return found;
        if (scope == 0U) break;
        if (scope >= builder->scope_count) break;
        scope = builder->scopes[scope].parent;
    }
    return REAPER_HIR_NO_SYMBOL;
}

static uint32_t add_symbol(
    HirBuilder *builder,
    const char *name,
    ReaperHirSymbolKind kind,
    ReaperHirType type,
    ReaperHirType return_type,
    uint32_t parameter_count,
    uint32_t declaration_node,
    int mutable_value
) {
    if (find_in_scope(builder, builder->current_scope, name) != REAPER_HIR_NO_SYMBOL) {
        (void)fail(builder, declaration_node, "duplicate declaration in the same lexical scope");
        return REAPER_HIR_NO_SYMBOL;
    }
    if (builder->module->symbol_count >= UINT32_MAX) {
        (void)fail(builder, declaration_node, "HIR symbol index limit exceeded");
        return REAPER_HIR_NO_SYMBOL;
    }

    if (builder->module->symbol_count == builder->module->symbol_capacity) {
        size_t next = builder->module->symbol_capacity == 0U
            ? 16U : builder->module->symbol_capacity * 2U;
        if (next < builder->module->symbol_capacity ||
            next > SIZE_MAX / sizeof *builder->module->symbols) {
            (void)fail(builder, declaration_node, "HIR symbol storage size overflow");
            return REAPER_HIR_NO_SYMBOL;
        }
        ReaperHirSymbol *symbols = realloc(
            builder->module->symbols,
            next * sizeof *builder->module->symbols
        );
        if (symbols == NULL) {
            (void)fail(builder, declaration_node, "out of memory building HIR symbols");
            return REAPER_HIR_NO_SYMBOL;
        }
        builder->module->symbols = symbols;
        builder->module->symbol_capacity = next;
    }

    char *copy = copy_text(name);
    if (copy == NULL) {
        (void)fail(builder, declaration_node, "out of memory copying HIR symbol name");
        return REAPER_HIR_NO_SYMBOL;
    }

    uint32_t id = (uint32_t)builder->module->symbol_count;
    builder->module->symbols[builder->module->symbol_count++] = (ReaperHirSymbol) {
        id, builder->current_scope, declaration_node, parameter_count,
        kind, type, return_type, copy, mutable_value != 0
    };
    return id;
}

static int is_builtin(const char *name) {
    static const char *const names[] = {
        "map", "keep", "fold", "range", "text", "len"
    };
    for (size_t i = 0U; i < sizeof names / sizeof names[0]; ++i)
        if (strcmp(names[i], name) == 0) return 1;
    return 0;
}

static ReaperHirType builtin_result(const char *name) {
    if (strcmp(name, "map") == 0 || strcmp(name, "keep") == 0 ||
        strcmp(name, "range") == 0) return REAPER_HIR_TYPE_LIST;
    if (strcmp(name, "text") == 0) return REAPER_HIR_TYPE_STRING;
    if (strcmp(name, "len") == 0) return REAPER_HIR_TYPE_I64;
    return REAPER_HIR_TYPE_UNKNOWN;
}

static size_t sequence_count(HirBuilder *builder, uint32_t sequence_id) {
    size_t count = 0U;
    uint32_t current = sequence_id;
    while (current != REAPER_AST_NO_NODE) {
        const ReaperAstNode *sequence = ast_node(builder, current);
        if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE ||
            ++count > builder->ast->length) return SIZE_MAX;
        current = sequence->right;
    }
    return count;
}

static int compatible_types(ReaperHirType expected, ReaperHirType actual) {
    return expected == REAPER_HIR_TYPE_UNKNOWN ||
        actual == REAPER_HIR_TYPE_UNKNOWN || expected == actual;
}

static int require_type(
    HirBuilder *builder,
    uint32_t node_id,
    ReaperHirType actual,
    ReaperHirType expected,
    const char *message
) {
    if (!compatible_types(expected, actual)) return fail(builder, node_id, message);
    return 1;
}

static int infer_expression(
    HirBuilder *builder,
    uint32_t node_id,
    int callee_position,
    ReaperHirType *out_type
);

static int infer_sequence_values(
    HirBuilder *builder,
    uint32_t sequence_id,
    ReaperHirType *first_type
) {
    uint32_t current = sequence_id;
    size_t count = 0U;
    *first_type = REAPER_HIR_TYPE_UNKNOWN;
    while (current != REAPER_AST_NO_NODE) {
        const ReaperAstNode *sequence = ast_node(builder, current);
        if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE ||
            ++count > builder->ast->length) {
            return fail(builder, current, "malformed HIR argument sequence");
        }
        ReaperHirType value_type;
        if (!infer_expression(builder, sequence->left, 0, &value_type)) return 0;
        if (count == 1U) *first_type = value_type;
        current = sequence->right;
    }
    return 1;
}

static int check_call(
    HirBuilder *builder,
    uint32_t node_id,
    uint32_t callee_id,
    uint32_t arguments_id,
    size_t inserted_arguments,
    ReaperHirType *out_type
) {
    const ReaperAstNode *callee = ast_node(builder, callee_id);
    if (callee == NULL) return fail(builder, node_id, "call has no callee expression");

    ReaperHirType callee_type;
    if (!infer_expression(builder, callee_id, 1, &callee_type)) return 0;
    if (callee_type != REAPER_HIR_TYPE_FUNCTION) {
        return fail(builder, node_id, "called value is not a function");
    }

    size_t explicit_count = sequence_count(builder, arguments_id);
    if (explicit_count == SIZE_MAX ||
        explicit_count > SIZE_MAX - inserted_arguments) {
        return fail(builder, node_id, "call argument count is invalid");
    }
    size_t actual_count = explicit_count + inserted_arguments;

    if (callee->kind == REAPER_AST_IDENTIFIER &&
        builder->module->nodes[callee_id].symbol_id == REAPER_HIR_NO_SYMBOL &&
        is_builtin(callee->text)) {
        size_t minimum = 1U;
        size_t maximum = 1U;
        if (strcmp(callee->text, "map") == 0 || strcmp(callee->text, "keep") == 0)
            minimum = maximum = 2U;
        else if (strcmp(callee->text, "fold") == 0)
            minimum = maximum = 3U;
        else if (strcmp(callee->text, "range") == 0) {
            minimum = 1U;
            maximum = 2U;
        }
        if (actual_count < minimum || actual_count > maximum)
            return fail(builder, node_id, "built-in call has the wrong number of arguments");
        ReaperHirType ignored;
        if (!infer_sequence_values(builder, arguments_id, &ignored)) return 0;
        *out_type = builtin_result(callee->text);
        return 1;
    }

    uint32_t symbol_id = builder->module->nodes[callee_id].symbol_id;
    ReaperHirSymbol *symbol = symbol_at(builder, symbol_id);
    if (symbol == NULL || symbol->kind != REAPER_HIR_SYMBOL_FUNCTION) {
        return fail(builder, node_id, "called value is not a declared function or known built-in");
    }
    if (actual_count != symbol->parameter_count) {
        return fail(builder, node_id, "function call has the wrong number of arguments");
    }

    ReaperHirType ignored;
    if (!infer_sequence_values(builder, arguments_id, &ignored)) return 0;
    *out_type = symbol->return_type;
    return 1;
}

static int infer_expression(
    HirBuilder *builder,
    uint32_t node_id,
    int callee_position,
    ReaperHirType *out_type
) {
    (void)callee_position;
    if (node_id >= builder->module->node_count)
        return fail(builder, node_id, "expression node is outside the HIR module");

    ReaperHirNode *node = &builder->module->nodes[node_id];
    ReaperHirType left = REAPER_HIR_TYPE_UNKNOWN;
    ReaperHirType right = REAPER_HIR_TYPE_UNKNOWN;

    switch (node->kind) {
    case REAPER_AST_INTEGER:
        node->type = REAPER_HIR_TYPE_I64;
        break;
    case REAPER_AST_DECIMAL:
        node->type = REAPER_HIR_TYPE_F64;
        break;
    case REAPER_AST_STRING:
        node->type = REAPER_HIR_TYPE_STRING;
        break;
    case REAPER_AST_BOOLEAN:
        node->type = REAPER_HIR_TYPE_BOOL;
        break;
    case REAPER_AST_NULL:
        node->type = REAPER_HIR_TYPE_UNKNOWN;
        break;

    case REAPER_AST_IDENTIFIER: {
        uint32_t symbol_id = resolve_symbol(builder, node->text);
        if (symbol_id == REAPER_HIR_NO_SYMBOL) {
            if (is_builtin(node->text)) {
                node->type = REAPER_HIR_TYPE_FUNCTION;
                break;
            }
            return fail(builder, node_id, "name is not declared in the current lexical scope");
        }
        ReaperHirSymbol *symbol = symbol_at(builder, symbol_id);
        if (symbol == NULL) return fail(builder, node_id, "resolved HIR symbol is invalid");
        node->symbol_id = symbol_id;
        node->type = symbol->type;
        break;
    }

    case REAPER_AST_UNARY:
        if (!infer_expression(builder, node->left, 0, &left)) return 0;
        if (strcmp(node->text, "-") == 0 || strcmp(node->text, "+") == 0) {
            if (left != REAPER_HIR_TYPE_I64 && left != REAPER_HIR_TYPE_F64 &&
                left != REAPER_HIR_TYPE_UNKNOWN)
                return fail(builder, node_id, "unary sign requires a numeric value");
            node->type = left;
        } else if (strcmp(node->text, "not") == 0 ||
                   strcmp(node->text, "!") == 0) {
            if (!require_type(builder, node_id, left, REAPER_HIR_TYPE_BOOL,
                    "logical negation requires a boolean value")) return 0;
            node->type = REAPER_HIR_TYPE_BOOL;
        } else {
            return fail(builder, node_id, "unary operator is not supported by HIR");
        }
        break;

    case REAPER_AST_BINARY:
        if (!infer_expression(builder, node->left, 0, &left)) return 0;
        if (strcmp(node->text, "::") == 0) {
            const ReaperAstNode *right_ast = ast_node(builder, node->right);
            if (right_ast == NULL) return fail(builder, node_id, "flow operator has no right operand");
            if (right_ast->kind == REAPER_AST_CALL) {
                if (!check_call(builder, node_id, right_ast->left,
                        right_ast->right, 1U, &node->type)) return 0;
            } else {
                if (!check_call(builder, node_id, node->right,
                        REAPER_AST_NO_NODE, 1U, &node->type)) return 0;
            }
            break;
        }
        if (!infer_expression(builder, node->right, 0, &right)) return 0;

        if (strcmp(node->text, "+") == 0 || strcmp(node->text, "-") == 0 ||
            strcmp(node->text, "*") == 0 || strcmp(node->text, "/") == 0 ||
            strcmp(node->text, "//") == 0 || strcmp(node->text, "%") == 0) {
            int numeric_left = left == REAPER_HIR_TYPE_I64 || left == REAPER_HIR_TYPE_F64 ||
                left == REAPER_HIR_TYPE_UNKNOWN;
            int numeric_right = right == REAPER_HIR_TYPE_I64 || right == REAPER_HIR_TYPE_F64 ||
                right == REAPER_HIR_TYPE_UNKNOWN;
            if (!numeric_left || !numeric_right)
                return fail(builder, node_id, "arithmetic operator requires numeric operands");
            node->type = left == REAPER_HIR_TYPE_UNKNOWN ? right : left;
            if (left != REAPER_HIR_TYPE_UNKNOWN && right != REAPER_HIR_TYPE_UNKNOWN &&
                left != right)
                return fail(builder, node_id, "arithmetic operands have different numeric types");
        } else if (strcmp(node->text, "++") == 0) {
            if (!require_type(builder, node_id, left, REAPER_HIR_TYPE_STRING,
                    "text concatenation requires string operands") ||
                !require_type(builder, node_id, right, REAPER_HIR_TYPE_STRING,
                    "text concatenation requires string operands")) return 0;
            node->type = REAPER_HIR_TYPE_STRING;
        } else if (strcmp(node->text, "and") == 0 || strcmp(node->text, "or") == 0 ||
                   strcmp(node->text, "&&") == 0 || strcmp(node->text, "||") == 0) {
            if (!require_type(builder, node_id, left, REAPER_HIR_TYPE_BOOL,
                    "logical operator requires boolean operands") ||
                !require_type(builder, node_id, right, REAPER_HIR_TYPE_BOOL,
                    "logical operator requires boolean operands")) return 0;
            node->type = REAPER_HIR_TYPE_BOOL;
        } else if (strcmp(node->text, "==") == 0 || strcmp(node->text, "!=") == 0 ||
                   strcmp(node->text, "<") == 0 || strcmp(node->text, "<=") == 0 ||
                   strcmp(node->text, ">") == 0 || strcmp(node->text, ">=") == 0) {
            if (left != REAPER_HIR_TYPE_UNKNOWN && right != REAPER_HIR_TYPE_UNKNOWN &&
                left != right)
                return fail(builder, node_id, "comparison operands have incompatible types");
            node->type = REAPER_HIR_TYPE_BOOL;
        } else {
            return fail(builder, node_id, "binary operator is not supported by HIR");
        }
        break;

    case REAPER_AST_CALL:
        if (!check_call(builder, node_id, node->left, node->right, 0U, &node->type))
            return 0;
        break;

    case REAPER_AST_LIST: {
        ReaperHirType first = REAPER_HIR_TYPE_UNKNOWN;
        uint32_t current = node->left;
        size_t count = 0U;
        while (current != REAPER_AST_NO_NODE) {
            const ReaperAstNode *sequence = ast_node(builder, current);
            if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE ||
                ++count > builder->ast->length)
                return fail(builder, node_id, "list contains a malformed item sequence");
            ReaperHirType item_type;
            if (!infer_expression(builder, sequence->left, 0, &item_type)) return 0;
            if (count == 1U) first = item_type;
            else if (!compatible_types(first, item_type))
                return fail(builder, sequence->left, "list items must have a consistent type");
            current = sequence->right;
        }
        node->type = REAPER_HIR_TYPE_LIST;
        break;
    }

    case REAPER_AST_INDEX:
        if (!infer_expression(builder, node->left, 0, &left) ||
            !infer_expression(builder, node->right, 0, &right)) return 0;
        if (left != REAPER_HIR_TYPE_LIST && left != REAPER_HIR_TYPE_STRING &&
            left != REAPER_HIR_TYPE_UNKNOWN)
            return fail(builder, node_id, "indexing requires a list or string value");
        if (right != REAPER_HIR_TYPE_I64 && right != REAPER_HIR_TYPE_UNKNOWN)
            return fail(builder, node_id, "index must be an integer");
        node->type = REAPER_HIR_TYPE_UNKNOWN;
        break;

    default:
        return fail(builder, node_id, "statement node cannot be used as an expression");
    }

    *out_type = node->type;
    return 1;
}

static int check_sequence(
    HirBuilder *builder,
    uint32_t sequence_id,
    unsigned function_depth
);

static int check_statement(
    HirBuilder *builder,
    uint32_t node_id,
    unsigned function_depth
);

static int check_block(HirBuilder *builder, uint32_t block_id) {
    const ReaperAstNode *block = ast_node(builder, block_id);
    if (block == NULL || block->kind != REAPER_AST_BLOCK)
        return fail(builder, block_id, "expected a block node");

    uint32_t previous = 0U;
    if (!enter_scope(builder, &previous))
        return fail(builder, block_id, "unable to allocate a lexical scope");
    int success = check_sequence(builder, block->left, builder->function_depth);
    leave_scope(builder, previous);
    return success;
}

static int check_sequence(
    HirBuilder *builder,
    uint32_t sequence_id,
    unsigned function_depth
) {
    uint32_t current = sequence_id;
    size_t count = 0U;
    while (current != REAPER_AST_NO_NODE) {
        const ReaperAstNode *sequence = ast_node(builder, current);
        if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE ||
            ++count > builder->ast->length)
            return fail(builder, current, "malformed statement sequence");
        if (!check_statement(builder, sequence->left, function_depth)) return 0;
        current = sequence->right;
    }
    return 1;
}

static int check_statement(
    HirBuilder *builder,
    uint32_t node_id,
    unsigned function_depth
) {
    ReaperHirNode *node = &builder->module->nodes[node_id];
    ReaperHirType value_type = REAPER_HIR_TYPE_UNIT;
    switch (node->kind) {
    case REAPER_AST_PROGRAM:
        if (!check_sequence(builder, node->left, function_depth)) return 0;
        node->type = REAPER_HIR_TYPE_UNIT;
        return 1;

    case REAPER_AST_BLOCK:
        return check_block(builder, node_id);

    case REAPER_AST_DECLARE_IMMUTABLE:
    case REAPER_AST_DECLARE_MUTABLE:
        if (!infer_expression(builder, node->left, 0, &value_type)) return 0;
        node->symbol_id = add_symbol(
            builder, node->text, REAPER_HIR_SYMBOL_VALUE, value_type,
            REAPER_HIR_TYPE_UNKNOWN, 0U, node_id,
            node->kind == REAPER_AST_DECLARE_MUTABLE
        );
        if (node->symbol_id == REAPER_HIR_NO_SYMBOL) return 0;
        node->type = REAPER_HIR_TYPE_UNIT;
        node->mutable_value = node->kind == REAPER_AST_DECLARE_MUTABLE;
        return 1;

    case REAPER_AST_CHANGE: {
        uint32_t symbol_id = resolve_symbol(builder, node->text);
        ReaperHirSymbol *symbol = symbol_at(builder, symbol_id);
        if (symbol == NULL) return fail(builder, node_id, "changed variable is not declared");
        if (!symbol->mutable_value)
            return fail(builder, node_id, "change requires a mutable 'vary' binding");
        if (!infer_expression(builder, node->left, 0, &value_type)) return 0;
        if (!compatible_types(symbol->type, value_type))
            return fail(builder, node_id, "assigned value does not match the variable's inferred type");
        node->symbol_id = symbol_id;
        node->type = REAPER_HIR_TYPE_UNIT;
        return 1;
    }

    case REAPER_AST_FUNCTION: {
        size_t parameter_count = sequence_count(builder, node->left);
        if (parameter_count == SIZE_MAX || parameter_count > UINT32_MAX)
            return fail(builder, node_id, "function parameter sequence is malformed");

        uint32_t function_id = add_symbol(
            builder, node->text, REAPER_HIR_SYMBOL_FUNCTION,
            REAPER_HIR_TYPE_FUNCTION, REAPER_HIR_TYPE_UNKNOWN,
            (uint32_t)parameter_count, node_id, 0
        );
        if (function_id == REAPER_HIR_NO_SYMBOL) return 0;
        node->symbol_id = function_id;
        node->type = REAPER_HIR_TYPE_UNIT;

        uint32_t previous = 0U;
        if (!enter_scope(builder, &previous))
            return fail(builder, node_id, "unable to allocate function scope");
        uint32_t saved_function = builder->current_function;
        builder->current_function = function_id;
        ++builder->function_depth;

        uint32_t parameter = node->left;
        while (parameter != REAPER_AST_NO_NODE) {
            const ReaperAstNode *sequence = ast_node(builder, parameter);
            if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE) {
                leave_scope(builder, previous);
                --builder->function_depth;
                builder->current_function = saved_function;
                return fail(builder, node_id, "function parameter sequence is malformed");
            }
            const ReaperAstNode *parameter_node = ast_node(builder, sequence->left);
            if (parameter_node == NULL || parameter_node->kind != REAPER_AST_IDENTIFIER) {
                leave_scope(builder, previous);
                --builder->function_depth;
                builder->current_function = saved_function;
                return fail(builder, node_id, "function parameter is not an identifier");
            }
            if (add_symbol(
                    builder, parameter_node->text, REAPER_HIR_SYMBOL_PARAMETER,
                    REAPER_HIR_TYPE_UNKNOWN, REAPER_HIR_TYPE_UNKNOWN,
                    0U, sequence->left, 0
                ) == REAPER_HIR_NO_SYMBOL) {
                leave_scope(builder, previous);
                --builder->function_depth;
                builder->current_function = saved_function;
                return 0;
            }
            parameter = sequence->right;
        }

        int success = check_block(builder, node->right);
        --builder->function_depth;
        builder->current_function = saved_function;
        leave_scope(builder, previous);
        return success;
    }

    case REAPER_AST_EMIT:
        if (!infer_expression(builder, node->left, 0, &value_type)) return 0;
        node->type = REAPER_HIR_TYPE_UNIT;
        return 1;

    case REAPER_AST_YIELD:
        if (function_depth == 0U)
            return fail(builder, node_id, "yield is only valid inside a function");
        if (node->left != REAPER_AST_NO_NODE &&
            !infer_expression(builder, node->left, 0, &value_type)) return 0;
        node->type = REAPER_HIR_TYPE_UNIT;
        return 1;

    case REAPER_AST_WHEN: {
        if (!infer_expression(builder, node->left, 0, &value_type) ||
            !require_type(builder, node_id, value_type, REAPER_HIR_TYPE_BOOL,
                "when condition must be boolean")) return 0;
        uint32_t branch = node->right;
        size_t count = 0U;
        while (branch != REAPER_AST_NO_NODE) {
            const ReaperAstNode *sequence = ast_node(builder, branch);
            if (sequence == NULL || sequence->kind != REAPER_AST_SEQUENCE ||
                ++count > 2U)
                return fail(builder, node_id, "conditional branch sequence is malformed");
            if (!check_block(builder, sequence->left)) return 0;
            branch = sequence->right;
        }
        node->type = REAPER_HIR_TYPE_UNIT;
        return 1;
    }

    case REAPER_AST_EACH: {
        if (!infer_expression(builder, node->left, 0, &value_type)) return 0;
        if (value_type != REAPER_HIR_TYPE_LIST && value_type != REAPER_HIR_TYPE_UNKNOWN)
            return fail(builder, node_id, "each requires a list-like value");
        uint32_t previous = 0U;
        if (!enter_scope(builder, &previous))
            return fail(builder, node_id, "unable to allocate iteration scope");
        uint32_t iterator = add_symbol(
            builder, node->text, REAPER_HIR_SYMBOL_ITERATION,
            REAPER_HIR_TYPE_UNKNOWN, REAPER_HIR_TYPE_UNKNOWN,
            0U, node_id, 0
        );
        int success = iterator != REAPER_HIR_NO_SYMBOL &&
            check_block(builder, node->right);
        leave_scope(builder, previous);
        node->symbol_id = iterator;
        node->type = REAPER_HIR_TYPE_UNIT;
        return success;
    }

    case REAPER_AST_WHILE:
        if (!infer_expression(builder, node->left, 0, &value_type) ||
            !require_type(builder, node_id, value_type, REAPER_HIR_TYPE_BOOL,
                "loop while condition must be boolean")) return 0;
        if (!check_block(builder, node->right)) return 0;
        node->type = REAPER_HIR_TYPE_UNIT;
        return 1;

    case REAPER_AST_EXPRESSION_STATEMENT:
        if (!infer_expression(builder, node->left, 0, &value_type)) return 0;
        node->type = REAPER_HIR_TYPE_UNIT;
        return 1;

    default:
        return fail(builder, node_id, "unsupported statement in HIR semantic analysis");
    }
}

void reaper_hir_free(ReaperHirModule *module) {
    if (module == NULL) return;
    for (size_t i = 0U; i < module->node_count; ++i)
        free(module->nodes[i].text);
    for (size_t i = 0U; i < module->symbol_count; ++i)
        free(module->symbols[i].name);
    free(module->nodes);
    free(module->symbols);
    memset(module, 0, sizeof *module);
}

int reaper_hir_build(
    const ReaperAst *ast,
    ReaperHirModule *output,
    ReaperHirError *error
) {
    if (output != NULL) memset(output, 0, sizeof *output);
    if (error != NULL) {
        error->node_index = 0U;
        error->message[0] = '\0';
    }
    if (ast == NULL || output == NULL || ast->items == NULL ||
        ast->length == 0U || ast->root >= ast->length ||
        ast->length > UINT32_MAX ||
        ast->length > SIZE_MAX / sizeof(ReaperHirNode)) {
        if (error != NULL)
            (void)snprintf(error->message, sizeof error->message,
                "valid complete AST and HIR output are required");
        return 0;
    }

    output->nodes = calloc(ast->length, sizeof *output->nodes);
    if (output->nodes == NULL) {
        if (error != NULL)
            (void)snprintf(error->message, sizeof error->message,
                "unable to allocate HIR nodes");
        return 0;
    }
    output->node_count = ast->length;

    for (size_t i = 0U; i < ast->length; ++i) {
        const ReaperAstNode *source = &ast->items[i];
        if (source->text == NULL ||
            (source->left != REAPER_AST_NO_NODE && source->left >= i) ||
            (source->right != REAPER_AST_NO_NODE && source->right >= i)) {
            if (error != NULL) {
                error->node_index = i;
                (void)snprintf(error->message, sizeof error->message,
                    "AST has a missing text field or non-topological child reference");
            }
            reaper_hir_free(output);
            return 0;
        }
        char *copy = copy_text(source->text);
        if (copy == NULL) {
            if (error != NULL) {
                error->node_index = i;
                (void)snprintf(error->message, sizeof error->message,
                    "unable to copy AST text into HIR");
            }
            reaper_hir_free(output);
            return 0;
        }
        output->nodes[i] = (ReaperHirNode) {
            source->kind,
            REAPER_HIR_TYPE_UNKNOWN,
            (uint32_t)i,
            source->left,
            source->right,
            REAPER_HIR_NO_SYMBOL,
            copy,
            source->line,
            source->column,
            0
        };
    }

    HirBuilder builder;
    memset(&builder, 0, sizeof builder);
    builder.ast = ast;
    builder.module = output;
    builder.error = error;
    builder.current_function = REAPER_HIR_NO_SYMBOL;

    uint32_t root_scope = 0U;
    if (!add_scope(&builder, REAPER_HIR_NO_SYMBOL, &root_scope)) {
        if (error != NULL)
            (void)snprintf(error->message, sizeof error->message,
                "unable to allocate root HIR scope");
        free(builder.scopes);
        reaper_hir_free(output);
        return 0;
    }
    builder.current_scope = root_scope;

    int success = ast->items[ast->root].kind == REAPER_AST_PROGRAM &&
        check_statement(&builder, ast->root, 0U);

    free(builder.scopes);
    if (!success) {
        reaper_hir_free(output);
        return 0;
    }
    return 1;
}

const char *reaper_hir_type_name(ReaperHirType type) {
    switch (type) {
    case REAPER_HIR_TYPE_UNIT: return "unit";
    case REAPER_HIR_TYPE_I64: return "i64";
    case REAPER_HIR_TYPE_F64: return "f64";
    case REAPER_HIR_TYPE_BOOL: return "bool";
    case REAPER_HIR_TYPE_STRING: return "string";
    case REAPER_HIR_TYPE_LIST: return "list";
    case REAPER_HIR_TYPE_FUNCTION: return "function";
    default: return "unknown";
    }
}
