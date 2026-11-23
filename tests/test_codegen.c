#include "reaper/codegen.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

static void emits_checked_x86_64_assembly(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
          REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 100, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
          REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 5, 1, 7 },
        { REAPER_IR_OP_DIV_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 5 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
          REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 2, 1, 11 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 2, 3, 0, 1, 9 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 4,
          REAPER_IR_NO_VALUE, 0, 1, 1 }
    };
    const ReaperIrModule module = { nodes, sizeof nodes / sizeof nodes[0] };
    ReaperCodegenError error;
    FILE *first = tmpfile();
    FILE *second = tmpfile();
    assert(first != NULL && second != NULL);

    assert(reaper_codegen_x86_64_sysv_elf(&module, first, &error));
    assert(reaper_codegen_x86_64_sysv_elf(&module, second, &error));

    char *assembly_a = read_stream(first);
    char *assembly_b = read_stream(second);
    assert(strcmp(assembly_a, assembly_b) == 0);
    assert(strstr(assembly_a, ".globl reaper_program") != NULL);
    assert(strstr(assembly_a, "idivq %rcx") != NULL);
    assert(strstr(assembly_a, "jo .Lreaper_overflow") != NULL);
    assert(strstr(assembly_a, ".Lreaper_divzero:") != NULL);
    assert(strstr(assembly_a, "movq %rax, (%rcx)") != NULL);

    free(assembly_a);
    free(assembly_b);
    fclose(first);
    fclose(second);
}

static void rejects_modules_without_a_final_return(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
          REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 42, 1, 1 }
    };
    const ReaperIrModule module = { nodes, 1U };
    ReaperCodegenError error;
    FILE *output = tmpfile();
    assert(output != NULL);

    assert(!reaper_codegen_x86_64_sysv_elf(&module, output, &error));
    assert(strstr(error.message, "RETURN") != NULL);
    fclose(output);
}

static void rejects_null_output_pointer_at_generation_time(void) {
    ReaperCodegenError error;
    ReaperIrModule module = { NULL, 0U };
    assert(!reaper_codegen_x86_64_sysv_elf(&module, NULL, &error));
    assert(strstr(error.message, "required") != NULL);
}

int main(void) {
    emits_checked_x86_64_assembly();
    rejects_modules_without_a_final_return();
    rejects_null_output_pointer_at_generation_time();
    puts("native codegen tests: 3 groups passed");
    return 0;
}
