#include "reaper/processor_backends.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const ReaperRv32Instruction instructions[4] = {
        {REAPER_RV32_ADDI, 1u, 0u, 0u, 16, 0u},
        {REAPER_RV32_ADDI, 2u, 0u, 0u, 123, 0u},
        {REAPER_RV32_SW, 0u, 1u, 2u, 0, 0u},
        {REAPER_RV32_LW, 3u, 1u, 0u, 0, 0u}
    };
    const ReaperRv32Label labels[1] = {{1u, 0u, 1u}};
    ReaperRv32Object object;
    ReaperRv32LinkedImage image;
    ReaperRv32ExecutionReport report;
    assert(reaper_rv32_assemble(instructions, 4u, labels, 1u, &object) ==
           REAPER_BACKEND_OK);
    assert(reaper_rv32_link(&object, 1u, 1u, 0x1000u, &image) == REAPER_BACKEND_OK);
    assert(reaper_rv32_emulate(&image, NULL, 100u, &report) == REAPER_BACKEND_OK);
    assert(report.halted == 1u);
    assert(report.steps == 4u);
    assert(report.registers[3] == 123u);
    assert(report.trace_count == 4u);
    assert(report.memory[16] == 123u);
    assert(report.memory[17] == 0u);
    assert(reaper_rv32_emulate(&image, NULL, 2u, &report) == REAPER_BACKEND_STEP_LIMIT);
    assert(report.steps == 2u);
    puts("RV32I bounded emulator backend tests passed");
    return 0;
}
