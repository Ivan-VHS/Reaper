#include "reaper/compiler_ir.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

int main(void) {
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
    puts("native compiler IR tests: general typed HIR/MIR/LIR and C17 emission passed");
    return 0;
}
