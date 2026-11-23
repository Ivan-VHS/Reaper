#ifdef NDEBUG
#undef NDEBUG
#endif
#include "reaper/dabi64_program.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t output[256];
    uint64_t output_length;
    int fail_writes;
} ProgramHost;

static int32_t program_write(void *context, int64_t fd, const uint8_t *bytes,
                             uint64_t length, uint64_t *written) {
    ProgramHost *host = (ProgramHost *)context;
    if (host->fail_writes || fd != 1) return -1;
    uint64_t count = length > 5u ? 5u : length;
    if (count > sizeof host->output - host->output_length) return -1;
    memcpy(host->output + (size_t)host->output_length, bytes, (size_t)count);
    host->output_length += count;
    *written = count;
    return 0;
}

static void test_runtime_program_each(void) {
    static const uint8_t red[] = "red";
    static const uint8_t blue[] = "blue";
    ProgramHost state = {0};
    ReaperDabiHostV1 host = {
        REAPER_DABI64_VERSION, (uint32_t)sizeof(ReaperDabiHostV1),
        &state, program_write, NULL, NULL, NULL
    };
    ReaperDabiRuntime runtime;
    assert(reaper_dabi_runtime_init(&runtime, &host, NULL) == REAPER_DABI_OK);

    const ReaperDabiInstruction code[] = {
        {REAPER_DABI_OP_CONST_STRING, 0u, 0u, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, REAPER_DABI_PROGRAM_NO_SLOT, 0u, 0, red, 3u},
        {REAPER_DABI_OP_CONST_STRING, 0u, 1u, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, REAPER_DABI_PROGRAM_NO_SLOT, 0u, 0, blue, 4u},
        {REAPER_DABI_OP_CALL, REAPER_DABI_CALL_ARRAY_NEW, 2u,
         REAPER_DABI_PROGRAM_NO_SLOT, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, 0u, 0, NULL, 0u},
        {REAPER_DABI_OP_CALL, REAPER_DABI_CALL_ARRAY_PUSH, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, 2u, 0u, 0u, 0, NULL, 0u},
        {REAPER_DABI_OP_CALL, REAPER_DABI_CALL_ARRAY_PUSH, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, 2u, 1u, 0u, 0, NULL, 0u},
        {REAPER_DABI_OP_CALL, REAPER_DABI_CALL_ITER_BEGIN, 3u,
         REAPER_DABI_PROGRAM_NO_SLOT, 2u, REAPER_DABI_PROGRAM_NO_SLOT, 0u, 0, NULL, 0u},
        {REAPER_DABI_OP_CALL, REAPER_DABI_CALL_ITER_NEXT, 4u, 5u, 3u,
         REAPER_DABI_PROGRAM_NO_SLOT, 0u, 0, NULL, 0u},
        {REAPER_DABI_OP_JUMP_IF_FALSE, 0u, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, 4u, REAPER_DABI_PROGRAM_NO_SLOT, 10u, 0, NULL, 0u},
        {REAPER_DABI_OP_CALL, REAPER_DABI_CALL_EMIT, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, 5u, REAPER_DABI_PROGRAM_NO_SLOT, 0u, 0, NULL, 0u},
        {REAPER_DABI_OP_JUMP, 0u, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, 6u, 0, NULL, 0u},
        {REAPER_DABI_OP_RETURN, 0u, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, 1u, REAPER_DABI_PROGRAM_NO_SLOT, 0u, 0, NULL, 0u}
    };
    ReaperDabiProgram program = {code, 11u, 6u, 100u};
    ReaperDabiProgramError error;
    ReaperDabiValue result;
    assert(reaper_dabi_program_verify(&program, &error) == REAPER_DABI_OK);
    assert(reaper_dabi_program_execute(&runtime, &program, &result, &error) == REAPER_DABI_OK);
    assert(result.tag == REAPER_DABI_TAG_STRING);
    assert(state.output_length == 9u);
    assert(memcmp(state.output, "red\nblue\n", 9u) == 0);
    reaper_dabi_value_drop(&runtime, &result);
    assert(runtime.live_objects == 0u);

    state.fail_writes = 1;
    assert(reaper_dabi_program_execute(&runtime, &program, &result, &error) == REAPER_DABI_IO_ERROR);
    assert(runtime.live_objects == 0u);
    assert(reaper_dabi_runtime_destroy(&runtime) == REAPER_DABI_OK);
}

static void test_verifier_rejects_bad_control_flow(void) {
    const ReaperDabiInstruction code[] = {
        {REAPER_DABI_OP_JUMP, 0u, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, REAPER_DABI_PROGRAM_NO_SLOT,
         REAPER_DABI_PROGRAM_NO_SLOT, 99u, 0, NULL, 0u}
    };
    ReaperDabiProgram program = {code, 1u, 1u, 20u};
    assert(reaper_dabi_program_verify(&program, NULL) == REAPER_DABI_RANGE_ERROR);
}

int main(void) {
    test_runtime_program_each();
    test_verifier_rejects_bad_control_flow();
    puts("DABI64 runtime-call program tests passed");
    return 0;
}
