#include "reaper/ast.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static int parse_program(const char *source, ReaperAst *ast, ReaperParseError *error) {
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0, 0};
    if (!reaper_lex(source, &tokens, &lex_error)) return 0;
    int success = reaper_parse_program(&tokens, ast, error);
    reaper_tokens_free(&tokens);
    return success;
}

static size_t count_kind(const ReaperAst *ast, ReaperAstKind kind) {
    size_t count = 0U;
    for (size_t i = 0U; i < ast->length; ++i) {
        if (ast->items[i].kind == kind) ++count;
    }
    return count;
}

static void parses_complete_flow_program(void) {
    const char *source =
        "craft double(value) {\n"
        "    yield value * 2\n"
        "}\n"
        "make values := [1, 2, 3]\n"
        "make result := values :: map(double) :: keep(double)\n"
        "when result >= 2 {\n"
        "    emit result\n"
        "} otherwise {\n"
        "    emit 0\n"
        "}\n"
        "each item in values {\n"
        "    emit double(item)\n"
        "}\n"
        "loop while result > 0 {\n"
        "    change result := result - 1\n"
        "}\n";

    ReaperAst ast;
    ReaperParseError error;
    assert(parse_program(source, &ast, &error));
    assert(ast.items[ast.root].kind == REAPER_AST_PROGRAM);
    assert(count_kind(&ast, REAPER_AST_FUNCTION) == 1U);
    assert(count_kind(&ast, REAPER_AST_DECLARE_IMMUTABLE) == 2U);
    assert(count_kind(&ast, REAPER_AST_CHANGE) == 1U);
    assert(count_kind(&ast, REAPER_AST_EMIT) == 3U);
    assert(count_kind(&ast, REAPER_AST_YIELD) == 1U);
    assert(count_kind(&ast, REAPER_AST_WHEN) == 1U);
    assert(count_kind(&ast, REAPER_AST_EACH) == 1U);
    assert(count_kind(&ast, REAPER_AST_WHILE) == 1U);
    assert(count_kind(&ast, REAPER_AST_CALL) >= 4U);
    assert(count_kind(&ast, REAPER_AST_LIST) == 1U);
    assert(count_kind(&ast, REAPER_AST_BINARY) >= 6U);

    FILE *json = tmpfile();
    assert(json != NULL);
    assert(reaper_ast_write_json(&ast, json));
    assert(fflush(json) == 0);
    assert(fseek(json, 0L, SEEK_SET) == 0);
    char buffer[8192];
    size_t length = fread(buffer, 1U, sizeof buffer - 1U, json);
    buffer[length] = '\0';
    assert(strstr(buffer, "\"kind\":\"program\"") != NULL);
    assert(strstr(buffer, "\"kind\":\"function\"") != NULL);
    assert(strstr(buffer, "\"kind\":\"when\"") != NULL);
    fclose(json);
    reaper_ast_free(&ast);
}

static void parses_nested_calls_indexes_and_flow(void) {
    const char *source = "values :: map(double)(2)[0]";
    ReaperAst ast;
    ReaperParseError error;
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0, 0};
    assert(reaper_lex(source, &tokens, &lex_error));
    assert(reaper_parse_expression(&tokens, &ast, &error));
    reaper_tokens_free(&tokens);

    assert(ast.items[ast.root].kind == REAPER_AST_INDEX);
    uint32_t call = ast.items[ast.root].left;
    assert(ast.items[call].kind == REAPER_AST_CALL);
    assert(ast.items[ast.items[call].left].kind == REAPER_AST_CALL);
    reaper_ast_free(&ast);

    assert(reaper_lex("left :: right", &tokens, &lex_error));
    assert(reaper_parse_expression(&tokens, &ast, &error));
    assert(ast.items[ast.root].kind == REAPER_AST_BINARY);
    assert(strcmp(ast.items[ast.root].text, "::") == 0);
    reaper_ast_free(&ast);
    reaper_tokens_free(&tokens);
}

static void parses_empty_blocks_and_empty_lists(void) {
    ReaperAst ast;
    ReaperParseError error;
    assert(parse_program("craft empty() {}\nmake items := []\n", &ast, &error));
    assert(count_kind(&ast, REAPER_AST_FUNCTION) == 1U);
    assert(count_kind(&ast, REAPER_AST_LIST) == 1U);
    FILE *json = tmpfile();
    assert(json != NULL);
    assert(reaper_ast_write_json(&ast, json));
    fclose(json);
    reaper_ast_free(&ast);
}

static void rejects_incomplete_programs(void) {
    ReaperAst ast;
    ReaperParseError error;

    assert(!parse_program("make answer :=\n", &ast, &error));
    assert(error.message[0] != '\0');

    assert(!parse_program("craft add(left, right {\n yield left + right\n}\n", &ast, &error));
    assert(strstr(error.message, "expected ')'") != NULL);

    assert(!parse_program("each item values { emit item }\n", &ast, &error));
    assert(strstr(error.message, "expected 'in'") != NULL);

    assert(!parse_program("when true { emit 1\n", &ast, &error));
    assert(strstr(error.message, "expected '}'") != NULL);
}

int main(void) {
    parses_complete_flow_program();
    parses_nested_calls_indexes_and_flow();
    parses_empty_blocks_and_empty_lists();
    rejects_incomplete_programs();
    puts("native program parser tests: 4 groups passed");
    return 0;
}
