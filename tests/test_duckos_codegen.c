#include "reaper/codegen.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char *contents(FILE *stream) {
    assert(fflush(stream) == 0);
    assert(fseek(stream, 0L, SEEK_END) == 0);
    long size = ftell(stream);
    assert(size >= 0L);
    assert(fseek(stream, 0L, SEEK_SET) == 0);
    char *buffer = malloc((size_t)size + 1U);
    assert(buffer != NULL);
    size_t length = fread(buffer, 1U, (size_t)size, stream);
    assert(length == (size_t)size);
    buffer[length] = '\0';
    return buffer;
}

static void emits_duckos_abi_note_and_call_contract(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
          REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 40, 1, 1 },
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
          REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 2, 1, 6 },
        { REAPER_IR_OP_ADD_I64, REAPER_IR_TYPE_I64, 0, 1, 0, 1, 4 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 2,
          REAPER_IR_NO_VALUE, 0, 1, 1 }
    };
    const ReaperIrModule module = { nodes, 4U };
    ReaperCodegenError error;
    FILE *first = tmpfile();
    FILE *second = tmpfile();
    assert(first != NULL && second != NULL);

    assert(reaper_codegen_duckos_dabi64_v1(&module, first, &error));
    assert(reaper_codegen_duckos_dabi64_v1(&module, second, &error));

    char *a = contents(first);
    char *b = contents(second);
    assert(strcmp(a, b) == 0);
    assert(strstr(a, ".note.duckos.abi") != NULL);
    assert(strstr(a, ".globl duck_program") != NULL);
    assert(strstr(a, "testq %r11, %r11") != NULL);
    assert(strstr(a, "testq $15, %r11") != NULL);
    assert(strstr(a, "movq %rax, 0(%r11)") != NULL);
    assert(strstr(a, "movl $16, %eax") != NULL);
    assert(strstr(a, "movl $17, %eax") != NULL);

    free(a);
    free(b);
    fclose(first);
    fclose(second);
}

static void rejects_non_i64_and_invalid_ir(void) {
    const ReaperIrNode nodes[] = {
        { REAPER_IR_OP_CONST_I64, REAPER_IR_TYPE_I64,
          REAPER_IR_NO_VALUE, REAPER_IR_NO_VALUE, 7, 1, 1 },
        { REAPER_IR_OP_RETURN, REAPER_IR_TYPE_UNIT, 0,
          REAPER_IR_NO_VALUE, 0, 1, 2 }
    };
    const ReaperIrModule module = { nodes, 2U };
    ReaperCodegenError error;
    FILE *output = tmpfile();
    assert(output != NULL);
    assert(reaper_codegen_duckos_dabi64_v1(&module, output, &error));
    fclose(output);
}

static void requires_module_and_output(void) {
    ReaperCodegenError error;
    assert(!reaper_codegen_duckos_dabi64_v1(NULL, NULL, &error));
    assert(strstr(error.message, "required") != NULL);
}

int main(void) {
    emits_duckos_abi_note_and_call_contract();
    rejects_non_i64_and_invalid_ir();
    requires_module_and_output();
    puts("DuckOS DABI64 codegen tests: 3 groups passed");
    return 0;
}
