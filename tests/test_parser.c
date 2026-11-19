#include "reaper/lexer.h"
#include "reaper/parser.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static ReaperAst parse(const char *source) {
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0},0,0};
    ReaperParseError parse_error = {{0},0,0};
    ReaperAst ast = {0};
    assert(reaper_lex(source, &tokens, &lex_error));
    assert(reaper_parse_expression(&tokens, &ast, &parse_error));
    reaper_tokens_free(&tokens);
    return ast;
}
static void test_precedence(void) {
    ReaperAst ast = parse("1 + 2 * 3");
    const ReaperAstNode *root = &ast.nodes[ast.root];
    assert(root->kind == REAPER_AST_BINARY && !strcmp(root->text, "+"));
    assert(ast.nodes[root->right].kind == REAPER_AST_BINARY);
    assert(!strcmp(ast.nodes[root->right].text, "*"));
    reaper_ast_free(&ast);
}
static void test_parentheses(void) {
    ReaperAst ast = parse("(1 + 2) * 3");
    assert(!strcmp(ast.nodes[ast.root].text, "*"));
    assert(!strcmp(ast.nodes[ast.nodes[ast.root].left].text, "+"));
    reaper_ast_free(&ast);
}
static void test_calls_and_flow(void) {
    ReaperAst ast = parse("items ~> map(double)");
    const ReaperAstNode *root = &ast.nodes[ast.root];
    assert(!strcmp(root->text, "~>"));
    assert(ast.nodes[root->right].kind == REAPER_AST_CALL);
    assert(ast.nodes[ast.nodes[root->right].first_argument].kind == REAPER_AST_IDENTIFIER);
    reaper_ast_free(&ast);
}
static void test_source_location(void) {
    ReaperAst ast = parse("alpha + 2");
    assert(ast.nodes[ast.root].line == 1 && ast.nodes[ast.root].column == 7);
    reaper_ast_free(&ast);
}
static void test_utf8_identifier(void) {
    ReaperAst ast = parse("значение + 1");
    assert(ast.nodes[ast.nodes[ast.root].left].kind == REAPER_AST_IDENTIFIER);
    reaper_ast_free(&ast);
}
static void test_invalid_expression(void) {
    ReaperTokenArray tokens = {0};
    ReaperLexError le = {{0},0,0};
    ReaperParseError pe = {{0},0,0};
    ReaperAst ast = {0};
    assert(reaper_lex("1 +", &tokens, &le));
    assert(!reaper_parse_expression(&tokens, &ast, &pe));
    assert(pe.message[0] != '\0');
    reaper_tokens_free(&tokens);
}
int main(void) {
    test_precedence(); test_parentheses(); test_calls_and_flow();
    test_source_location(); test_utf8_identifier(); test_invalid_expression();
    puts("native parser tests: 6 groups passed");
    return 0;
}
