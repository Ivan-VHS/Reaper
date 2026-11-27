#include "reaper/processor_backends.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const ReaperRv32Instruction caller_instruction[1] = {
        {REAPER_RV32_JAL, 1u, 0u, 0u, 0, 20u}
    };
    const ReaperRv32Instruction callee_instruction[1] = {
        {REAPER_RV32_ADDI, 10u, 0u, 0u, 7, 0u}
    };
    const ReaperRv32Label caller_labels[1] = {{10u, 0u, 1u}};
    const ReaperRv32Label callee_labels[1] = {{20u, 0u, 1u}};
    ReaperRv32Object objects[2];
    ReaperRv32LinkedImage image;
    assert(reaper_rv32_assemble(caller_instruction, 1u, caller_labels, 1u,
                                &objects[0]) == REAPER_BACKEND_OK);
    assert(reaper_rv32_assemble(callee_instruction, 1u, callee_labels, 1u,
                                &objects[1]) == REAPER_BACKEND_OK);
    assert(objects[0].relocation_count == 1u);
    assert(reaper_rv32_link(objects, 2u, 10u, UINT32_C(0x1000), &image) ==
           REAPER_BACKEND_OK);
    assert(image.byte_count == 8u);
    assert(image.entry_address == UINT32_C(0x1000));
    assert(image.symbol_count == 2u);
    assert(image.bytes[0] == 0xEFu && image.bytes[1] == 0x00u);
    assert(image.bytes[2] == 0x40u && image.bytes[3] == 0x00u);

    objects[1].symbols[0].symbol_id = 10u;
    assert(reaper_rv32_link(objects, 2u, 10u, UINT32_C(0x1000), &image) ==
           REAPER_BACKEND_DUPLICATE_SYMBOL);
    objects[1].symbols[0].symbol_id = 20u;
    objects[1].symbols[0].symbol_id = 21u;
    assert(reaper_rv32_link(objects, 2u, 10u, UINT32_C(0x1000), &image) ==
           REAPER_BACKEND_UNRESOLVED_SYMBOL);
    puts("RV32I linker backend tests passed");
    return 0;
}
