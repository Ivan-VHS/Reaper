#include "reaper/processor_backends.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const ReaperRv32Instruction instructions[2] = {
        {REAPER_RV32_ADDI, 5u, 0u, 0u, 42, 0u},
        {REAPER_RV32_ADD, 6u, 5u, 5u, 0, 0u}
    };
    const ReaperRv32Label labels[1] = {{10u, 0u, 1u}};
    ReaperRv32Object object;
    assert(reaper_rv32_assemble(instructions, 2u, labels, 1u, &object) == REAPER_BACKEND_OK);
    assert(object.magic == REAPER_RV32_OBJECT_MAGIC);
    assert(object.abi_major == REAPER_PROCESSOR_BACKEND_ABI_MAJOR);
    assert(object.target_id == REAPER_RV32_TARGET_RV32I);
    assert(object.abi_id == REAPER_RV32_ABI_ILP32);
    assert(object.word_count == 2u);
    assert(object.words[0] == UINT32_C(0x02A00293));
    assert(object.words[1] == UINT32_C(0x00528333));
    assert(object.symbol_count == 1u && object.symbols[0].value_offset == 0u);
    {
        ReaperRv32Instruction invalid = {REAPER_RV32_ADDI, 32u, 0u, 0u, 1, 0u};
        assert(reaper_rv32_assemble(&invalid, 1u, NULL, 0u, &object) ==
               REAPER_BACKEND_INVALID_ARGUMENT);
    }
    {
        ReaperRv32Instruction invalid = {REAPER_RV32_ADDI, 1u, 0u, 0u, 4096, 0u};
        assert(reaper_rv32_assemble(&invalid, 1u, NULL, 0u, &object) ==
               REAPER_BACKEND_RELOCATION_RANGE);
    }
    {
        const ReaperRv32Instruction lui = {
            REAPER_RV32_LUI, 1u, 0u, 0u, 1048575, 0u
        };
        assert(reaper_rv32_assemble(&lui, 1u, NULL, 0u, &object) == REAPER_BACKEND_OK);
        assert(object.words[0] == UINT32_C(0xFFFFF0B7));
    }
    {
        const ReaperRv32Instruction branch = {
            REAPER_RV32_BEQ, 0u, 1u, 2u, 8, 0u
        };
        assert(reaper_rv32_assemble(&branch, 1u, NULL, 0u, &object) == REAPER_BACKEND_OK);
        assert((object.words[0] & UINT32_C(0x7F)) == UINT32_C(0x63));
    }
    puts("RV32I assembler backend tests passed");
    return 0;
}
