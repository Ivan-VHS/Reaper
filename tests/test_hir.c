#include "reaper/ast.h"
#include "reaper/hir.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static int build_hir(const char *source, ReaperHirModule *hir, ReaperHirError *error) {
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0, 0};
    ReaperAst ast;
    if (!reaper_lex(source, &tokens, &lex_error)) return 0;
    ReaperParseError parse_error;
    int parsed = reaper_parse_program(&tokens, &ast, &parse_error);
    reaper_tokens_free(&tokens);
    if (!parsed) return 0;
    int built = reaper_hir_build(&ast, hir, error);
    reaper_ast_free(&ast);
    return built;
}

static void resolves_functions_locals_and_flow_calls(void) {
    const char *source =
        "craft double(value) {\n"
        "    yield value * 2\n"
        "}\n"
        "craft large(value) {\n"
        "    yield value >= 6\n"
        "}\n"
        "craft add(total, value) {\n"
        "    yield total + value\n"
        "}\n"
        "make values := [1, 2, 3, 4]\n"
        "make result := values :: map(double) :: keep(large) :: fold(0, add)\n"
        "vary counter := 0\n"
        "each item in values {\n"
        "    change counter := counter + item\n"
        "}\n"
        "when counter >= 1 { emit text(result) }\n";
    ReaperHirModule hir;
    ReaperHirError error;
    assert(build_hir(source, &hir, &error));
    assert(hir.node_count > 0U);
    assert(hir.symbol_count >= 8U);
    assert(strcmp(reaper_hir_type_name(hir.nodes[hir.nodes[hir.node_count - 1U].source_node].type),
                  "unit") == 0);
    reaper_hir_free(&hir);
}

static void enforces_mutability_and_scope(void) {
    ReaperHirModule hir;
    ReaperHirError error;
    assert(!build_hir("make answer := 1\nchange answer := 2\n", &hir, &error));
    assert(strstr(error.message, "mutable 'vary'") != NULL);

    assert(build_hir(
        "vary counter := 0\n"
        "when true { vary counter := 4; }\n"
        "change counter := 5\n", &hir, &error));
    reaper_hir_free(&hir);

    assert(!build_hir(
        "when true { make inner := 2 }\n"
        "emit inner\n", &hir, &error));
    assert(strstr(error.message, "not declared") != NULL);
}

static void checks_function_arity_and_return_context(void) {
    ReaperHirModule hir;
    ReaperHirError error;
    assert(!build_hir(
        "craft add(a, b) { yield a + b }\n"
        "make value := add(1)\n", &hir, &error));
    assert(strstr(error.message, "wrong number") != NULL);

    assert(!build_hir("yield 42\n", &hir, &error));
    assert(strstr(error.message, "inside a function") != NULL);

    assert(!build_hir("make value := missing\n", &hir, &error));
    assert(strstr(error.message, "not declared") != NULL);
}

static void checks_builtin_pipe_arity(void) {
    ReaperHirModule hir;
    ReaperHirError error;
    assert(build_hir("make values := [1, 2]\nmake result := values :: map(text)\n", &hir, &error));
    reaper_hir_free(&hir);

    assert(!build_hir("make values := [1, 2]\nmake result := values :: map()\n", &hir, &error));
    assert(strstr(error.message, "wrong number") != NULL);
}

int main(void) {
    resolves_functions_locals_and_flow_calls();
    enforces_mutability_and_scope();
    checks_function_arity_and_return_context();
    checks_builtin_pipe_arity();
    puts("native HIR semantic tests: 4 groups passed");
    return 0;
}
