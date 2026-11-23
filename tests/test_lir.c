#include "reaper/ast.h"
#include "reaper/hir.h"
#include "reaper/lir.h"
#include "reaper/mir.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static int build_lir(
    const char *source,
    ReaperHirModule *hir,
    ReaperMirModule *mir,
    ReaperLirModule *lir,
    ReaperLirError *lir_error
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

    ReaperMirError mir_error;
    if (!reaper_mir_build(hir, mir, &mir_error)) return 0;
    return reaper_lir_build(hir, mir, lir, lir_error);
}

static size_t count_opcode(const ReaperLirModule *lir, ReaperLirOpcode opcode) {
    size_t count = 0U;
    for (size_t i = 0U; i < lir->instruction_count; ++i) {
        if (lir->instructions[i].opcode == opcode) ++count;
    }
    return count;
}

static size_t count_terminator(
    const ReaperLirModule *lir,
    ReaperLirTerminator terminator
) {
    size_t count = 0U;
    for (size_t i = 0U; i < lir->block_count; ++i) {
        if (lir->blocks[i].terminator == terminator) ++count;
    }
    return count;
}

static void lowers_calls_locals_and_parameters_to_slots(void) {
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
    ReaperLirModule lir;
    ReaperLirError error;
    assert(build_lir(source, &hir, &mir, &lir, &error));

    assert(lir.function_count == 3U);
    assert(lir.functions[0].stack_slot_count == 2U);
    assert(lir.functions[1].stack_slot_count == 1U);
    assert(lir.functions[2].stack_slot_count == 2U);
    assert(lir.parameter_count == 3U);
    assert(lir.functions[1].parameter_count == 1U);
    assert(lir.functions[2].parameter_count == 2U);
    assert(lir.parameter_slots[0] < lir.functions[1].stack_slot_count);
    assert(lir.parameter_slots[1] < lir.functions[2].stack_slot_count);
    assert(lir.parameter_slots[2] < lir.functions[2].stack_slot_count);
    assert(count_opcode(&lir, REAPER_LIR_PIPE_CALL) == 1U);
    assert(count_opcode(&lir, REAPER_LIR_CALL) == 1U);
    assert(count_opcode(&lir, REAPER_LIR_LOAD_SLOT) >= 2U);
    assert(count_opcode(&lir, REAPER_LIR_STORE_SLOT) == 2U);
    assert(lir.instruction_order_count == lir.instruction_count);
    assert(reaper_lir_verify(&lir, &error));

    reaper_lir_free(&lir);
    reaper_mir_free(&mir);
    reaper_hir_free(&hir);
}

static void lowers_nested_branches_and_loop_slots(void) {
    const char *source =
        "vary total := 0\n"
        "each item in range(1, 4) {\n"
        "    change total := total + item\n"
        "}\n"
        "when total >= 6 {\n"
        "    emit total\n"
        "    when total >= 10 {\n"
        "        emit total\n"
        "    } otherwise {\n"
        "        emit 10\n"
        "    }\n"
        "} otherwise {\n"
        "    emit 0\n"
        "}\n"
        "loop while total > 0 {\n"
        "    change total := total - 1\n"
        "}\n";

    ReaperHirModule hir;
    ReaperMirModule mir;
    ReaperLirModule lir;
    ReaperLirError error;
    assert(build_lir(source, &hir, &mir, &lir, &error));
    assert(count_terminator(&lir, REAPER_LIR_TERM_BRANCH) == 4U);
    assert(count_terminator(&lir, REAPER_LIR_TERM_JUMP) >= 6U);
    assert(count_opcode(&lir, REAPER_LIR_ITER_INIT) == 1U);
    assert(count_opcode(&lir, REAPER_LIR_ITER_NEXT) == 1U);
    assert(count_opcode(&lir, REAPER_LIR_ITER_CURRENT) == 1U);
    assert(reaper_lir_verify(&lir, &error));

    reaper_lir_free(&lir);
    reaper_mir_free(&mir);
    reaper_hir_free(&hir);
}

static void rejects_invalid_local_slots(void) {
    const char *source = "vary counter := 0\nchange counter := counter + 1\n";
    ReaperHirModule hir;
    ReaperMirModule mir;
    ReaperLirModule lir;
    ReaperLirError error;
    assert(build_lir(source, &hir, &mir, &lir, &error));

    size_t load_index = lir.instruction_count;
    for (size_t i = 0U; i < lir.instruction_count; ++i) {
        if (lir.instructions[i].opcode == REAPER_LIR_LOAD_SLOT) {
            load_index = i;
            break;
        }
    }
    assert(load_index < lir.instruction_count);
    uint32_t saved_slot = lir.instructions[load_index].slot_id;
    lir.instructions[load_index].slot_id = REAPER_LIR_NO_SLOT;
    assert(!reaper_lir_verify(&lir, &error));
    assert(strstr(error.message, "stack slot") != NULL);
    lir.instructions[load_index].slot_id = saved_slot;
    assert(reaper_lir_verify(&lir, &error));

    reaper_lir_free(&lir);
    reaper_mir_free(&mir);
    reaper_hir_free(&hir);
}

int main(void) {
    lowers_calls_locals_and_parameters_to_slots();
    lowers_nested_branches_and_loop_slots();
    rejects_invalid_local_slots();
    puts("native LIR tests: 3 groups passed");
    return 0;
}
