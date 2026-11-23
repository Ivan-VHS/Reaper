#include "reaper/ast.h"
#include "reaper/codegen_duckos_lir.h"
#include "reaper/hir.h"
#include "reaper/lir.h"
#include "reaper/mir.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int build_lir(
    const char *source,
    ReaperAst *ast,
    ReaperHirModule *hir,
    ReaperMirModule *mir,
    ReaperLirModule *lir,
    ReaperLirError *lir_error
) {
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0U, 0U};
    if (!reaper_lex(source, &tokens, &lex_error)) return 0;

    ReaperParseError parse_error = {{0}, 0U, 0U};
    if (!reaper_parse_program(&tokens, ast, &parse_error)) {
        reaper_tokens_free(&tokens);
        return 0;
    }
    reaper_tokens_free(&tokens);

    ReaperHirError hir_error = {0};
    if (!reaper_hir_build(ast, hir, &hir_error)) return 0;

    ReaperMirError mir_error = {0};
    if (!reaper_mir_build(hir, mir, &mir_error)) return 0;

    return reaper_lir_build(hir, mir, lir, lir_error);
}

static char *read_stream(FILE *stream) {
    assert(fflush(stream) == 0);
    assert(fseek(stream, 0L, SEEK_END) == 0);
    long size = ftell(stream);
    assert(size >= 0L);
    assert(fseek(stream, 0L, SEEK_SET) == 0);

    char *text = malloc((size_t)size + 1U);
    assert(text != NULL);
    size_t length = fread(text, 1U, (size_t)size, stream);
    assert(length == (size_t)size);
    text[length] = '\0';
    return text;
}

static void frees_pipeline(
    ReaperAst *ast,
    ReaperHirModule *hir,
    ReaperMirModule *mir,
    ReaperLirModule *lir
) {
    reaper_lir_free(lir);
    reaper_mir_free(mir);
    reaper_hir_free(hir);
    reaper_ast_free(ast);
}

static void emits_complete_scalar_program_deterministically(void) {
    const char *source =
        "craft bump(value) { yield value + 1 }\n"
        "craft calculate(seed) {\n"
        "    make initial := bump(seed)\n"
        "    vary total := initial\n"
        "    change total := total :: bump()\n"
        "    when total < 10 {\n"
        "        change total := total * 2\n"
        "    } otherwise {\n"
        "        change total := total - 2\n"
        "    }\n"
        "    loop while total < 50 {\n"
        "        change total := total + 5\n"
        "    }\n"
        "    yield total\n"
        "}\n";

    ReaperAst ast = {0};
    ReaperHirModule hir = {0};
    ReaperMirModule mir = {0};
    ReaperLirModule lir = {0};
    ReaperLirError lir_error = {0};
    assert(build_lir(source, &ast, &hir, &mir, &lir, &lir_error));

    assert(lir.function_count == 3U);
    assert(lir.functions[0].parameter_count == 0U);
    assert(lir.functions[1].parameter_count == 1U);
    assert(lir.functions[2].parameter_count == 1U);

    size_t calls = 0U;
    size_t pipe_calls = 0U;
    size_t stores = 0U;
    for (size_t i = 0U; i < lir.instruction_count; ++i) {
        calls += lir.instructions[i].opcode == REAPER_LIR_CALL;
        pipe_calls += lir.instructions[i].opcode == REAPER_LIR_PIPE_CALL;
        stores += lir.instructions[i].opcode == REAPER_LIR_STORE_SLOT;
    }
    assert(calls >= 1U);
    assert(pipe_calls == 1U);
    assert(stores >= 4U);
    assert(reaper_lir_verify(&lir, &lir_error));

    FILE *first = tmpfile();
    FILE *second = tmpfile();
    assert(first != NULL && second != NULL);
    ReaperCodegenError error = {0};
    assert(reaper_codegen_duckos_dabi64_lir(&lir, first, &error));
    assert(reaper_codegen_duckos_dabi64_lir(&lir, second, &error));

    char *a = read_stream(first);
    char *b = read_stream(second);
    assert(strcmp(a, b) == 0);
    assert(strstr(a, ".note.duckos.abi") != NULL);
    assert(strstr(a, ".globl duck_program") != NULL);
    assert(strstr(a, ".globl duck_fn_1") != NULL);
    assert(strstr(a, ".globl duck_fn_2") != NULL);
    assert(strstr(a, "call duck_fn_1") != NULL);
    assert(strstr(a, "imulq") != NULL);
    assert(strstr(a, "jne .Lduck_fn_2_block_") != NULL);
    assert(strstr(a, ".size duck_program, .-duck_program") != NULL);

    free(a);
    free(b);
    fclose(first);
    fclose(second);
    frees_pipeline(&ast, &hir, &mir, &lir);
}

static void rejects_each_until_the_collection_runtime_is_present(void) {
    const char *source =
        "craft consume(value) { yield value }\n"
        "craft main() {\n"
        "    each item in [1, 2, 3] { emit item }\n"
        "    yield 0\n"
        "}\n";

    ReaperAst ast = {0};
    ReaperHirModule hir = {0};
    ReaperMirModule mir = {0};
    ReaperLirModule lir = {0};
    ReaperLirError lir_error = {0};
    assert(build_lir(source, &ast, &hir, &mir, &lir, &lir_error));

    FILE *output = tmpfile();
    assert(output != NULL);
    ReaperCodegenError error = {0};
    assert(!reaper_codegen_duckos_dabi64_lir(&lir, output, &error));
    assert(strstr(error.message, "collection runtime") != NULL);

    fclose(output);
    frees_pipeline(&ast, &hir, &mir, &lir);
}

static void rejects_output_until_the_io_runtime_is_present(void) {
    const char *source =
        "craft main() {\n"
        "    emit 42\n"
        "    yield 0\n"
        "}\n";

    ReaperAst ast = {0};
    ReaperHirModule hir = {0};
    ReaperMirModule mir = {0};
    ReaperLirModule lir = {0};
    ReaperLirError lir_error = {0};
    assert(build_lir(source, &ast, &hir, &mir, &lir, &lir_error));

    FILE *output = tmpfile();
    assert(output != NULL);
    ReaperCodegenError error = {0};
    assert(!reaper_codegen_duckos_dabi64_lir(&lir, output, &error));
    assert(strstr(error.message, "I/O runtime") != NULL);

    fclose(output);
    frees_pipeline(&ast, &hir, &mir, &lir);
}

int main(void) {
    emits_complete_scalar_program_deterministically();
    rejects_each_until_the_collection_runtime_is_present();
    rejects_output_until_the_io_runtime_is_present();
    puts("DuckOS DABI64 LIR codegen tests: 3 groups passed");
    return 0;
}
