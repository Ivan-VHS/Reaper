#include "reaper/compiler_ir.h"
#include "reaper/lexer.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static int lower_source_to_hir(const char *source_text, const char *source_name,
                                ReaperCompilerIrNode *nodes, size_t capacity,
                                ReaperCompilerIrModule *hir,
                                ReaperCompilerIrError *error) {
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0u, 0u};
    ReaperAst ast;
    ReaperParseError parse_error = {{0}, 0u, 0u};
    int result;
    if (!reaper_lex(source_text, &tokens, &lex_error)) return 0;
    if (!reaper_parse_expression(&tokens, &ast, &parse_error)) {
        reaper_tokens_free(&tokens);
        return 0;
    }
    result = reaper_compiler_ir_lower_ast_to_hir(
        &ast, source_name, nodes, capacity, hir, error);
    reaper_ast_free(&ast);
    reaper_tokens_free(&tokens);
    return result;
}

static void test_native_ast_to_typed_hir(void) {
    ReaperCompilerIrNode nodes[32], mir_nodes[32], lir_nodes[32];
    ReaperCompilerIrModule hir, mir, lir;
    ReaperCompilerIrError error;
    char generated[16384];
    size_t generated_length = 0u;

    assert(lower_source_to_hir("-(19 + 23) * 2", "native_expr.rpr",
        nodes, 32u, &hir, &error));
    assert(hir.stage == REAPER_COMPILER_IR_HIR);
    assert(hir.length == 6u);
    assert(hir.nodes[0].type == REAPER_COMPILER_IR_TYPE_I64);
    assert(hir.nodes[2].opcode == REAPER_COMPILER_IR_HIR_BINARY);
    assert(hir.nodes[3].opcode == REAPER_COMPILER_IR_HIR_UNARY);
    assert(hir.nodes[5].opcode == REAPER_COMPILER_IR_HIR_BINARY);
    assert(hir.nodes[5].key[0] == '*');
    assert(strcmp(hir.nodes[5].span.source, "native_expr.rpr") == 0);
    assert(hir.nodes[5].span.line == 1u && hir.nodes[5].span.column > 0u);

    assert(reaper_compiler_ir_lower_hir_to_mir(&hir, mir_nodes, 32u, &mir, &error));
    assert(reaper_compiler_ir_lower_mir_to_lir(
        &mir, "native.desktop", lir_nodes, 32u, &lir, &error));
    assert(reaper_compiler_ir_emit_c17(
        &lir, generated, sizeof generated, &generated_length, &error));
    assert(generated_length == strlen(generated));
    assert(strstr(generated, "lir.native_unary") != NULL);
    assert(strstr(generated, "lir.native_arithmetic") != NULL);

    assert(lower_source_to_hir("12.5", "literal.rpr",
        nodes, 32u, &hir, &error));
    assert(hir.nodes[0].type == REAPER_COMPILER_IR_TYPE_F64);
    assert(hir.nodes[0].number == 12.5);

    assert(lower_source_to_hir("\"a\\\"b\\n\"", "literal.rpr",
        nodes, 32u, &hir, &error));
    assert(hir.nodes[0].type == REAPER_COMPILER_IR_TYPE_TEXT);
    assert(strcmp(hir.nodes[0].text, "a\"b\n") == 0);
    assert(reaper_compiler_ir_verify(&hir, REAPER_COMPILER_IR_HIR, &error));

    assert(lower_source_to_hir("true", "literal.rpr",
        nodes, 32u, &hir, &error));
    assert(hir.nodes[0].type == REAPER_COMPILER_IR_TYPE_BOOL);
    assert(hir.nodes[0].integer == 1);

    {
        ReaperTokenArray tokens = {0};
        ReaperLexError lex_error = {{0}, 0u, 0u};
        ReaperAst ast;
        ReaperParseError parse_error = {{0}, 0u, 0u};
        assert(reaper_lex("unknown_name + 2", &tokens, &lex_error));
        assert(reaper_parse_expression(&tokens, &ast, &parse_error));
        assert(!reaper_compiler_ir_lower_ast_to_hir(
            &ast, "unsupported.rpr", nodes, 32u, &hir, &error));
        assert(error.span.line == 1u && error.span.column > 0u);
        assert(strcmp(error.span.source, "unsupported.rpr") == 0);
        assert(strstr(error.message, "identifier") != NULL);
        reaper_ast_free(&ast);
        reaper_tokens_free(&tokens);
    }

    assert(lower_source_to_hir("-1.5 * 2.0", "decimal.rpr",
        nodes, 32u, &hir, &error));
    assert(hir.length == 4u);
    assert(hir.nodes[1].opcode == REAPER_COMPILER_IR_HIR_UNARY);
    assert(hir.nodes[1].type == REAPER_COMPILER_IR_TYPE_F64);
    assert(hir.nodes[3].opcode == REAPER_COMPILER_IR_HIR_BINARY);
    assert(hir.nodes[3].type == REAPER_COMPILER_IR_TYPE_F64);
    assert(reaper_compiler_ir_lower_hir_to_mir(&hir, mir_nodes, 32u, &mir, &error));
    assert(reaper_compiler_ir_lower_mir_to_lir(
        &mir, "native.desktop", lir_nodes, 32u, &lir, &error));
    assert(reaper_compiler_ir_emit_c17(
        &lir, generated, sizeof generated, &generated_length, &error));
    assert(strstr(generated, "f64") != NULL);

    assert(lower_source_to_hir("\"empty\"", "literal.rpr",
        nodes, 32u, &hir, &error));
    assert(hir.length == 1u && hir.nodes[0].type == REAPER_COMPILER_IR_TYPE_TEXT);
    assert(hir.nodes[0].text[0] == '\0');
    assert(reaper_compiler_ir_verify(&hir, REAPER_COMPILER_IR_HIR, &error));

    {
        ReaperTokenArray tokens = {0};
        ReaperLexError lex_error = {{0}, 0u, 0u};
        ReaperAst ast;
        ReaperParseError parse_error = {{0}, 0u, 0u};
        assert(reaper_lex("nothing", &tokens, &lex_error));
        assert(reaper_parse_expression(&tokens, &ast, &parse_error));
        assert(!reaper_compiler_ir_lower_ast_to_hir(
            &ast, "unsupported.rpr", nodes, 32u, &hir, &error));
        assert(strstr(error.message, "unit/option") != NULL);
        reaper_ast_free(&ast);
        reaper_tokens_free(&tokens);
    }
}

int main(int argc, char **argv) {
    test_native_ast_to_typed_hir();
    const ReaperCompilerIrNode hir_nodes[] = {
        { .opcode = REAPER_COMPILER_IR_HIR_VALUE, .type = REAPER_COMPILER_IR_TYPE_I64,
          .integer = 20, .span = {"math.rpr", 1, 1},
          .lhs = REAPER_COMPILER_IR_NO_VALUE, .rhs = REAPER_COMPILER_IR_NO_VALUE },
        { .opcode = REAPER_COMPILER_IR_HIR_VALUE, .type = REAPER_COMPILER_IR_TYPE_I64,
          .integer = 22, .span = {"math.rpr", 1, 6},
          .lhs = REAPER_COMPILER_IR_NO_VALUE, .rhs = REAPER_COMPILER_IR_NO_VALUE },
        { .opcode = REAPER_COMPILER_IR_HIR_BINARY, .type = REAPER_COMPILER_IR_TYPE_I64,
          .key = "+", .span = {"math.rpr", 1, 4}, .lhs = 0, .rhs = 1 },
        { .opcode = REAPER_COMPILER_IR_HIR_COLOR_ROLE, .type = REAPER_COMPILER_IR_TYPE_COLOR,
          .key = "surface.background", .text = "#070707",
          .span = {"profile.rpr", 4, 5},
          .lhs = REAPER_COMPILER_IR_NO_VALUE, .rhs = REAPER_COMPILER_IR_NO_VALUE },
        { .opcode = REAPER_COMPILER_IR_HIR_MOTION_ROLE, .type = REAPER_COMPILER_IR_TYPE_DURATION,
          .key = "motion.standard", .integer = 180, .span = {"profile.rpr", 12, 5},
          .lhs = REAPER_COMPILER_IR_NO_VALUE, .rhs = REAPER_COMPILER_IR_NO_VALUE },
        { .opcode = REAPER_COMPILER_IR_HIR_MOTION_ROLE, .type = REAPER_COMPILER_IR_TYPE_TEXT,
          .key = "motion.easing", .text = "spring.standard", .span = {"profile.rpr", 13, 5},
          .lhs = REAPER_COMPILER_IR_NO_VALUE, .rhs = REAPER_COMPILER_IR_NO_VALUE },
        { .opcode = REAPER_COMPILER_IR_HIR_ACCESSIBILITY_ROLE, .type = REAPER_COMPILER_IR_TYPE_BOOL,
          .key = "a11y.reduced_motion", .integer = 1, .span = {"profile.rpr", 20, 5},
          .lhs = REAPER_COMPILER_IR_NO_VALUE, .rhs = REAPER_COMPILER_IR_NO_VALUE }
    };
    ReaperCompilerIrNode mir_nodes[7];
    ReaperCompilerIrNode lir_nodes[7];
    ReaperCompilerIrModule hir = {
        REAPER_COMPILER_IR_VERSION, REAPER_COMPILER_IR_HIR,
        0u, "", hir_nodes, 7u
    };
    ReaperCompilerIrModule mir, lir;
    ReaperCompilerIrError error;
    char generated[16384];
    size_t generated_length = 0u;

    assert(reaper_compiler_ir_verify(&hir, REAPER_COMPILER_IR_HIR, &error));
    assert(reaper_compiler_ir_lower_hir_to_mir(&hir, mir_nodes, 7u, &mir, &error));
    assert(mir.stage == REAPER_COMPILER_IR_MIR);
    assert(mir.nodes[2].opcode == REAPER_COMPILER_IR_MIR_ARITHMETIC);
    assert(mir.nodes[2].lhs == 0u && mir.nodes[2].rhs == 1u);
    assert(mir.nodes[4].integer == 0);
    assert(strcmp(mir.nodes[5].text, "linear") == 0);
    assert(reaper_compiler_ir_lower_mir_to_lir(
        &mir, "native.desktop", lir_nodes, 7u, &lir, &error));
    assert(lir.stage == REAPER_COMPILER_IR_LIR);
    assert(lir.nodes[2].opcode == REAPER_COMPILER_IR_LIR_NATIVE_ARITHMETIC);
    assert(reaper_compiler_ir_emit_c17(
        &lir, generated, sizeof generated, &generated_length, &error));
    assert(generated_length == strlen(generated));
    assert(strstr(generated, "ReaperGeneratedInstruction") != NULL);
    assert(strstr(generated, "surface.background") != NULL);
    assert(strstr(generated, "native.desktop") != NULL);
    assert(strstr(generated, "lir.native_arithmetic") != NULL);

    {
        ReaperCompilerIrNode invalid_nodes[1] = {
            { .opcode = REAPER_COMPILER_IR_HIR_COLOR_ROLE,
              .type = REAPER_COMPILER_IR_TYPE_COLOR, .key = "surface.background",
              .text = "#GGGGGG", .span = {"profile.rpr", 1, 1} }
        };
        ReaperCompilerIrModule invalid = {
            REAPER_COMPILER_IR_VERSION, REAPER_COMPILER_IR_HIR, 0u, "",
            invalid_nodes, 1u
        };
        assert(!reaper_compiler_ir_verify(&invalid, REAPER_COMPILER_IR_HIR, &error));
    }
    {
        ReaperCompilerIrNode invalid_nodes[1] = {
            { .opcode = REAPER_COMPILER_IR_HIR_METRIC_ROLE,
              .type = REAPER_COMPILER_IR_TYPE_F64, .key = "layout.scale",
              .number = NAN, .span = {"profile.rpr", 1, 1} }
        };
        ReaperCompilerIrModule invalid = {
            REAPER_COMPILER_IR_VERSION, REAPER_COMPILER_IR_HIR, 0u, "",
            invalid_nodes, 1u
        };
        assert(!reaper_compiler_ir_verify(&invalid, REAPER_COMPILER_IR_HIR, &error));
    }
    {
        ReaperCompilerIrNode invalid_names[1];
        ReaperCompilerIrModule invalid;
        memset(invalid_names, 0, sizeof invalid_names);
        invalid_names[0].opcode = REAPER_COMPILER_IR_HIR_NAME;
        invalid_names[0].type = REAPER_COMPILER_IR_TYPE_TEXT;
        (void)snprintf(invalid_names[0].key, sizeof invalid_names[0].key, "%s", "user.name");
        memset(invalid_names[0].text, 'x', sizeof invalid_names[0].text);
        invalid_names[0].span = (ReaperCompilerSourceSpan){"math.rpr", 2, 3};
        invalid_names[0].lhs = REAPER_COMPILER_IR_NO_VALUE;
        invalid_names[0].rhs = REAPER_COMPILER_IR_NO_VALUE;
        invalid = (ReaperCompilerIrModule){
            REAPER_COMPILER_IR_VERSION, REAPER_COMPILER_IR_HIR, 0u, "",
            invalid_names, 1u
        };
        assert(!reaper_compiler_ir_verify(&invalid, REAPER_COMPILER_IR_HIR, &error));
    }
    if (argc == 3 && strcmp(argv[1], "--emit-c17") == 0) {
        FILE *stream = fopen(argv[2], "wb");
        if (stream == NULL) return 2;
        if (fwrite(generated, 1u, generated_length, stream) != generated_length) {
            (void)fclose(stream);
            return 3;
        }
        if (fclose(stream) != 0) return 4;
    }
    puts("native compiler IR tests: general typed HIR/MIR/LIR and C17 emission passed");
    return 0;
}
