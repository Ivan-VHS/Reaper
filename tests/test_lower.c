#include "reaper/ast.h"
#include "reaper/ir.h"
#include "reaper/lexer.h"
#include "reaper/lower.h"
#include "reaper/optimizer.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static int parse_source(const char *source, ReaperAst *ast, ReaperParseError *error) {
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0, 0};
    assert(reaper_lex(source, &tokens, &lex_error));
    int ok = reaper_parse_expression(&tokens, ast, error);
    reaper_tokens_free(&tokens);
    return ok;
}

static void lowers_integer_addition(void) {
    ReaperAst ast;
    ReaperParseError parse_error;
    assert(parse_source("19 + 23", &ast, &parse_error));
    ReaperIrNode nodes[16];
    size_t length = 0;
    ReaperIrError error;
    assert(reaper_lower_ast_to_ir(&ast, nodes, 16, &length, &error));
    assert(length == 4);
    assert(nodes[0].opcode == REAPER_IR_OP_CONST_I64 && nodes[0].immediate == 19);
    assert(nodes[1].opcode == REAPER_IR_OP_CONST_I64 && nodes[1].immediate == 23);
    assert(nodes[2].opcode == REAPER_IR_OP_ADD_I64 && nodes[2].lhs == 0 && nodes[2].rhs == 1);
    assert(nodes[3].opcode == REAPER_IR_OP_RETURN && nodes[3].lhs == 2);
    ReaperIrModule module = { nodes, length };
    assert(reaper_ir_verify(&module, &error));
    reaper_ast_free(&ast);
}

static void lowers_nested_expression_and_folds(void) {
    ReaperAst ast;
    ReaperParseError parse_error;
    assert(parse_source("1 + 2 + 3", &ast, &parse_error));
    ReaperIrNode nodes[16], folded[16];
    size_t length = 0, folded_length = 0;
    ReaperIrError error;
    assert(reaper_lower_ast_to_ir(&ast, nodes, 16, &length, &error));
    ReaperIrModule module = { nodes, length };
    assert(reaper_ir_fold_constants(&module, folded, 16, &folded_length, &error));
    assert(folded_length == length);
    assert(folded[4].opcode == REAPER_IR_OP_CONST_I64);
    assert(folded[4].immediate == 6);
    assert(folded[5].opcode == REAPER_IR_OP_RETURN);
    reaper_ast_free(&ast);
}

static void rejects_unsupported_syntax(void) {
    ReaperAst ast;
    ReaperParseError parse_error;
    assert(parse_source("value + 2", &ast, &parse_error));
    ReaperIrNode nodes[16];
    size_t length = 0;
    ReaperIrError error;
    assert(!reaper_lower_ast_to_ir(&ast, nodes, 16, &length, &error));
    assert(length == 0);
    assert(strstr(error.message, "not supported") != NULL);
    reaper_ast_free(&ast);
}

static void rejects_small_output(void) {
    ReaperAst ast;
    ReaperParseError parse_error;
    assert(parse_source("4 + 5", &ast, &parse_error));
    ReaperIrNode nodes[2];
    size_t length = 0;
    ReaperIrError error;
    assert(!reaper_lower_ast_to_ir(&ast, nodes, 2, &length, &error));
    reaper_ast_free(&ast);
}

static void rejects_out_of_range_integer(void) {
    ReaperAst ast;
    ReaperParseError parse_error;
    assert(parse_source("9223372036854775808", &ast, &parse_error));
    ReaperIrNode nodes[8];
    size_t length = 0;
    ReaperIrError error;
    assert(!reaper_lower_ast_to_ir(&ast, nodes, 8, &length, &error));
    assert(strstr(error.message, "outside signed i64") != NULL);
    reaper_ast_free(&ast);
}

int main(void) {
    lowers_integer_addition();
    lowers_nested_expression_and_folds();
    rejects_unsupported_syntax();
    rejects_small_output();
    rejects_out_of_range_integer();
    puts("native lowering tests: 5 groups passed");
    return 0;
}
