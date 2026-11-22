#include "reaper/ast.h"
#include "reaper/hir.h"
#include "reaper/mir.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static int compile_mir(
    const char *source,
    ReaperHirModule *hir,
    ReaperMirModule *mir,
    ReaperMirError *mir_error
) {
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0, 0};
    if (!reaper_lex(source, &tokens, &lex_error)) return 0;

    ReaperAst ast;
    ReaperParseError parse_error;
    if (!reaper_parse_program(&tokens, &ast, &parse_error)) {
        reaper_tokens_free(&tokens);
        return 0;
    }
    reaper_tokens_free(&tokens);

    ReaperHirError hir_error;
    if (!reaper_hir_build(&ast, hir, &hir_error)) {
        reaper_ast_free(&ast);
        return 0;
    }
    reaper_ast_free(&ast);

    return reaper_mir_build(hir, mir, mir_error);
}

static size_t count_opcode(const ReaperMirModule *mir, ReaperMirOpcode opcode) {
    size_t count = 0U;
    for (size_t i = 0U; i < mir->instruction_count; ++i) {
        if (mir->instructions[i].opcode == opcode) ++count;
    }
    return count;
}

static size_t count_terminator(
    const ReaperMirModule *mir,
    ReaperMirTerminator terminator
) {
    size_t count = 0U;
    for (size_t i = 0U; i < mir->block_count; ++i) {
        if (mir->blocks[i].terminator == terminator) ++count;
    }
    return count;
}

static void lowers_functions_calls_and_pipeline(void) {
    const char *source =
        "craft double(value) {\n"
        "    yield value * 2\n"
        "}\n"
        "craft add(total, value) {\n"
        "    yield total + value\n"
        "}\n"
        "make values := [1, 2, 3]\n"
        "make mapped := values :: map(double)\n"
        "emit add(1, 2)\n"
        "emit mapped\n";

    ReaperHirModule hir;
    ReaperMirModule mir;
    ReaperMirError error;
    assert(compile_mir(source, &hir, &mir, &error));
    assert(mir.function_count == 3U);
    assert(mir.functions[0].id == 0U);
    assert(strcmp(mir.functions[0].name, "duck_main") == 0);
    assert(mir.functions[0].parameter_count == 0U);
    assert(mir.functions[1].parameter_count == 1U);
    assert(mir.functions[2].parameter_count == 2U);
    assert(count_opcode(&mir, REAPER_MIR_PIPE_CALL) == 1U);
    assert(count_opcode(&mir, REAPER_MIR_CALL) == 1U);
    assert(count_opcode(&mir, REAPER_MIR_STORE_LOCAL) == 2U);
    assert(count_opcode(&mir, REAPER_MIR_LOAD_LOCAL) >= 2U);
    assert(count_terminator(&mir, REAPER_MIR_TERM_RETURN) == 3U);
    assert(reaper_mir_verify(&mir, &error));
    reaper_mir_free(&mir);
    reaper_hir_free(&hir);
}

static void lowers_structured_control_flow(void) {
    const char *source =
        "vary total := 0\n"
        "each item in range(1, 4) {\n"
        "    change total := total + item\n"
        "}\n"
        "when total >= 6 {\n"
        "    emit total\n"
        "} otherwise {\n"
        "    emit 0\n"
        "}\n"
        "loop while total > 0 {\n"
        "    change total := total - 1\n"
        "}\n";

    ReaperHirModule hir;
    ReaperMirModule mir;
    ReaperMirError error;
    assert(compile_mir(source, &hir, &mir, &error));
    assert(count_opcode(&mir, REAPER_MIR_ITER_INIT) == 1U);
    assert(count_opcode(&mir, REAPER_MIR_ITER_NEXT) == 1U);
    assert(count_opcode(&mir, REAPER_MIR_ITER_CURRENT) == 1U);
    assert(count_terminator(&mir, REAPER_MIR_TERM_BRANCH) == 3U);
    assert(count_terminator(&mir, REAPER_MIR_TERM_JUMP) >= 4U);
    assert(reaper_mir_verify(&mir, &error));
    reaper_mir_free(&mir);
    reaper_hir_free(&hir);
}

static void creates_a_valid_empty_program_entry(void) {
    ReaperHirModule hir;
    ReaperMirModule mir;
    ReaperMirError error;
    assert(compile_mir("", &hir, &mir, &error));
    assert(mir.function_count == 1U);
    assert(mir.block_count == 1U);
    assert(mir.instruction_count == 0U);
    assert(mir.blocks[0].terminator == REAPER_MIR_TERM_RETURN);
    assert(reaper_mir_verify(&mir, &error));
    reaper_mir_free(&mir);
    reaper_hir_free(&hir);
}

static void verifier_rejects_bad_branch_targets(void) {
    ReaperHirModule hir;
    ReaperMirModule mir;
    ReaperMirError error;
    assert(compile_mir("when true { emit 1 }\n", &hir, &mir, &error));
    mir.blocks[0].target_true = UINT32_MAX;
    assert(!reaper_mir_verify(&mir, &error));
    assert(strstr(error.message, "branch target") != NULL);
    reaper_mir_free(&mir);
    reaper_hir_free(&hir);
}

int main(void) {
    lowers_functions_calls_and_pipeline();
    lowers_structured_control_flow();
    creates_a_valid_empty_program_entry();
    verifier_rejects_bad_branch_targets();
    puts("native MIR CFG tests: 4 groups passed");
    return 0;
}
