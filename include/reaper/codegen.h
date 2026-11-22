#ifndef REAPER_CODEGEN_H
#define REAPER_CODEGEN_H

#include "reaper/ir.h"

#include <stddef.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_CODEGEN_X86_64_MAX_NODES 4096U

typedef enum {
    REAPER_CODEGEN_OK = 0,
    REAPER_CODEGEN_OVERFLOW = 1,
    REAPER_CODEGEN_DIVISION_BY_ZERO = 2,
    REAPER_CODEGEN_INVALID_OUTPUT = 3
} ReaperCodegenStatus;

typedef struct {
    size_t node_index;
    char message[192];
} ReaperCodegenError;

/*
 * Emit deterministic GNU assembler for the verified i64 expression subset.
 *
 * The output defines:
 *
 *     int reaper_program(int64_t *result);
 *
 * The generated function returns ReaperCodegenStatus and writes *result
 * only on success. The target is x86-64 System V ELF, not a generic
 * cross-platform assembly format. No runtime library calls are emitted.
 *
 * The module must contain exactly one final RETURN and no more than
 * REAPER_CODEGEN_X86_64_MAX_NODES instructions.
 */
int reaper_codegen_x86_64_sysv_elf(
    const ReaperIrModule *module,
    FILE *output,
    ReaperCodegenError *error
);

#ifdef __cplusplus
}
#endif

#endif
