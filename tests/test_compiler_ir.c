#include "reaper/compiler_ir.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const ReaperCompilerIrNode hir_nodes[] = {
        { REAPER_COMPILER_IR_HIR_COLOR_ROLE, REAPER_COMPILER_IR_TYPE_COLOR,
          "surface.background", "#070707", 0, 0.0, {"profile.rpr", 4, 5} },
        { REAPER_COMPILER_IR_HIR_MOTION_ROLE, REAPER_COMPILER_IR_TYPE_DURATION,
          "motion.standard", "", 180, 0.0, {"profile.rpr", 12, 5} },
        { REAPER_COMPILER_IR_HIR_MOTION_ROLE, REAPER_COMPILER_IR_TYPE_TEXT,
          "motion.easing", "spring.standard", 0, 0.0, {"profile.rpr", 13, 5} },
        { REAPER_COMPILER_IR_HIR_ACCESSIBILITY_ROLE, REAPER_COMPILER_IR_TYPE_BOOL,
          "a11y.reduced_motion", "", 1, 0.0, {"profile.rpr", 20, 5} }
    };
    ReaperCompilerIrNode mir_nodes[4];
    ReaperCompilerIrNode lir_nodes[4];
    ReaperCompilerIrModule hir = {
        REAPER_COMPILER_IR_VERSION, REAPER_COMPILER_IR_HIR,
        REAPER_COMPILER_IR_FLAG_REDUCED_MOTION, "", hir_nodes, 4u
    };
    ReaperCompilerIrModule mir, lir;
    ReaperCompilerIrError error;
    char generated[8192];
    size_t generated_length = 0u;

    assert(reaper_compiler_ir_verify(&hir, REAPER_COMPILER_IR_HIR, &error));
    assert(reaper_compiler_ir_lower_hir_to_mir(&hir, mir_nodes, 4u, &mir, &error));
    assert(mir.stage == REAPER_COMPILER_IR_MIR);
    assert(mir.nodes[1].integer == 0);
    assert(strcmp(mir.nodes[2].text, "linear") == 0);
    assert(reaper_compiler_ir_lower_mir_to_lir(
        &mir, "native.desktop", lir_nodes, 4u, &lir, &error));
    assert(lir.stage == REAPER_COMPILER_IR_LIR);
    assert(reaper_compiler_ir_emit_c17(
        &lir, generated, sizeof generated, &generated_length, &error));
    assert(generated_length == strlen(generated));
    assert(strstr(generated, "ReaperGeneratedProperty") != NULL);
    assert(strstr(generated, "surface.background") != NULL);
    assert(strstr(generated, "native.desktop") != NULL);

    {
        ReaperCompilerIrNode invalid_nodes[1] = {
            { REAPER_COMPILER_IR_HIR_COLOR_ROLE, REAPER_COMPILER_IR_TYPE_COLOR,
              "surface.background", "#GGGGGG", 0, 0.0, {"profile.rpr", 1, 1} }
        };
        ReaperCompilerIrModule invalid = {
            REAPER_COMPILER_IR_VERSION, REAPER_COMPILER_IR_HIR, 0u, "",
            invalid_nodes, 1u
        };
        assert(!reaper_compiler_ir_verify(&invalid, REAPER_COMPILER_IR_HIR, &error));
    }
    {
        ReaperCompilerIrNode invalid_nodes[1] = {
            { REAPER_COMPILER_IR_HIR_METRIC_ROLE, REAPER_COMPILER_IR_TYPE_F64,
              "layout.scale", "", 0, 1.0 / 0.0, {"profile.rpr", 1, 1} }
        };
        ReaperCompilerIrModule invalid = {
            REAPER_COMPILER_IR_VERSION, REAPER_COMPILER_IR_HIR, 0u, "",
            invalid_nodes, 1u
        };
        assert(!reaper_compiler_ir_verify(&invalid, REAPER_COMPILER_IR_HIR, &error));
    }
    puts("native typed compiler IR tests: HIR/MIR/LIR and C17 emission passed");
    return 0;
}
