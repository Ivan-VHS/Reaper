#ifndef REAPER_CODEGEN_DUCKOS_LIR_H
#define REAPER_CODEGEN_DUCKOS_LIR_H

#include "reaper/codegen.h"
#include "reaper/lir.h"

#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_DUCK_LIR_MAX_FUNCTIONS 512U
#define REAPER_DUCK_LIR_MAX_BLOCKS 65536U
#define REAPER_DUCK_LIR_MAX_VREGS 65536U
#define REAPER_DUCK_LIR_MAX_SLOTS 4096U
#define REAPER_DUCK_LIR_MAX_CALL_ARGUMENTS 64U

/*
 * Emit x86-64 GNU assembly for the scalar DABI64 v1 program subset:
 * i64 locals/parameters, direct craft calls, arithmetic/comparisons,
 * when, loop while and :: pipe-calls. Lists, each, dynamic calls and host
 * I/O are rejected until their DuckOS runtime operations are available.
 *
 * User functions are exported as duck_fn_<function-id>; the program entry
 * is duck_program. Every entry uses R10=frame, R11=result, RAX=status.
 */
int reaper_codegen_duckos_dabi64_lir(
    const ReaperLirModule *module,
    FILE *output,
    ReaperCodegenError *error
);

#ifdef __cplusplus
}
#endif

#endif
