#ifdef NDEBUG
#undef NDEBUG
#endif
#include "reaper/elf64_link.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint16_t read16(const uint8_t *p) {
    return (uint16_t)(p[0] | ((uint16_t)p[1] << 8u));
}
static uint32_t read32(const uint8_t *p) {
    uint32_t value = 0u;
    for (unsigned i = 0u; i < 4u; ++i) value |= (uint32_t)p[i] << (i * 8u);
    return value;
}
static uint64_t read64(const uint8_t *p) {
    uint64_t value = 0u;
    for (unsigned i = 0u; i < 8u; ++i) value |= (uint64_t)p[i] << (i * 8u);
    return value;
}

static void test_static_link_and_relocation(void) {
    static const uint8_t text[] = {
        0x48, 0xb8, 0, 0, 0, 0, 0, 0, 0, 0,
        0xc3
    };
    static const uint8_t data[] = {1,2,3,4,5,6,7,8};
    const ReaperElf64Section sections[] = {
        {".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 16u, 0u, text, sizeof text},
        {".data", REAPER_ELF64_SHT_PROGBITS, 0x3u, 8u, 0u, data, sizeof data}
    };
    const ReaperElf64Symbol symbols[] = {
        {"_start", 0u, 0u, sizeof text, REAPER_ELF64_STB_GLOBAL,
         REAPER_ELF64_STT_FUNC, 0u},
        {"target", 1u, 0u, sizeof data, REAPER_ELF64_STB_GLOBAL,
         REAPER_ELF64_STT_OBJECT, 0u}
    };
    const ReaperElf64Relocation relocations[] = {
        {0u, 2u, 1u, REAPER_ELF64_R_X86_64_64, 0}
    };
    const ReaperElf64Object model = {sections, 2u, symbols, 2u, relocations, 1u};
    ReaperElf64Buffer object = {0}, executable = {0};
    ReaperElf64Error error = {0};
    assert(reaper_elf64_write_object(&model, &object, &error) == REAPER_ELF64_OK);

    ReaperElf64Buffer input_objects[] = {object};
    ReaperElf64LinkInput input = {input_objects, 1u, "_start", 0x400000u, 4096u};
    assert(reaper_elf64_link(&input, &executable, &error) == REAPER_ELF64_OK);
    assert(executable.size > 0x2000u);
    assert(memcmp(executable.data, "\x7f" "ELF", 4u) == 0);
    assert(read16(executable.data + 16u) == 2u);
    assert(read16(executable.data + 18u) == 62u);
    assert(read64(executable.data + 24u) == 0x401000u);
    assert(read64(executable.data + 32u) == 64u);
    assert(read16(executable.data + 56u) == 3u);

    const uint8_t *ph_text = executable.data + 64u + 56u;
    const uint8_t *ph_data = executable.data + 64u + 112u;
    assert(read32(ph_text) == 1u);
    assert((read32(ph_text + 4u) & 5u) == 5u);
    assert(read64(ph_text + 8u) == 0x1000u);
    assert(read64(ph_text + 16u) == 0x401000u);
    assert(read32(ph_data) == 1u);
    assert((read32(ph_data + 4u) & 6u) == 6u);
    assert(read64(ph_data + 8u) == 0x2000u);
    assert(read64(executable.data + 0x1002u) == 0x402000u);

    reaper_elf64_buffer_destroy(&object);
    reaper_elf64_buffer_destroy(&executable);
}

static void test_cross_object_symbol_resolution(void) {
    static const uint8_t caller_text[] = {0xe8, 0, 0, 0, 0, 0xc3};
    static const uint8_t callee_text[] = {0xc3};
    const ReaperElf64Section caller_sections[] = {
        {".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 16u, 0u,
         caller_text, sizeof caller_text}
    };
    const ReaperElf64Symbol caller_symbols[] = {
        {"_start", 0u, 0u, sizeof caller_text, REAPER_ELF64_STB_GLOBAL,
         REAPER_ELF64_STT_FUNC, 0u},
        {"external_fn", REAPER_ELF64_NO_SECTION, 0u, 0u,
         REAPER_ELF64_STB_GLOBAL, REAPER_ELF64_STT_NOTYPE, 0u}
    };
    const ReaperElf64Relocation caller_relocations[] = {
        {0u, 1u, 1u, REAPER_ELF64_R_X86_64_PLT32, -4}
    };
    const ReaperElf64Object caller_model = {
        caller_sections, 1u, caller_symbols, 2u, caller_relocations, 1u
    };
    const ReaperElf64Section callee_sections[] = {
        {".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 16u, 0u,
         callee_text, sizeof callee_text}
    };
    const ReaperElf64Symbol callee_symbols[] = {
        {"external_fn", 0u, 0u, sizeof callee_text, REAPER_ELF64_STB_GLOBAL,
         REAPER_ELF64_STT_FUNC, 0u}
    };
    const ReaperElf64Object callee_model = {
        callee_sections, 1u, callee_symbols, 1u, NULL, 0u
    };

    ReaperElf64Buffer objects[2] = {{0}};
    ReaperElf64Buffer executable = {0};
    ReaperElf64Error error = {0};
    assert(reaper_elf64_write_object(&caller_model, &objects[0], &error) == REAPER_ELF64_OK);
    assert(reaper_elf64_write_object(&callee_model, &objects[1], &error) == REAPER_ELF64_OK);
    ReaperElf64LinkInput input = {objects, 2u, "_start", 0x400000u, 4096u};
    assert(reaper_elf64_link(&input, &executable, &error) == REAPER_ELF64_OK);
    assert(read64(executable.data + 24u) == 0x401000u);
    assert((int32_t)read32(executable.data + 0x1001u) == 0xffbu);

    reaper_elf64_buffer_destroy(&objects[0]);
    reaper_elf64_buffer_destroy(&objects[1]);
    reaper_elf64_buffer_destroy(&executable);
}

static void test_duplicate_strong_symbol_rejected(void) {
    static const uint8_t code_a[] = {0xc3};
    static const uint8_t code_b[] = {0xc3};
    const ReaperElf64Section section_a = {
        ".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 16u, 0u, code_a, sizeof code_a
    };
    const ReaperElf64Section section_b = {
        ".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 16u, 0u, code_b, sizeof code_b
    };
    const ReaperElf64Symbol symbol_a = {
        "_start", 0u, 0u, 1u, REAPER_ELF64_STB_GLOBAL, REAPER_ELF64_STT_FUNC, 0u
    };
    const ReaperElf64Symbol symbol_b = {
        "_start", 0u, 0u, 1u, REAPER_ELF64_STB_GLOBAL, REAPER_ELF64_STT_FUNC, 0u
    };
    const ReaperElf64Object model_a = {&section_a, 1u, &symbol_a, 1u, NULL, 0u};
    const ReaperElf64Object model_b = {&section_b, 1u, &symbol_b, 1u, NULL, 0u};
    ReaperElf64Buffer objects[2] = {{0}};
    ReaperElf64Buffer output = {0};
    ReaperElf64Error error = {0};
    assert(reaper_elf64_write_object(&model_a, &objects[0], &error) == REAPER_ELF64_OK);
    assert(reaper_elf64_write_object(&model_b, &objects[1], &error) == REAPER_ELF64_OK);
    ReaperElf64LinkInput input = {objects, 2u, "_start", 0x400000u, 4096u};
    assert(reaper_elf64_link(&input, &output, &error) == REAPER_ELF64_INVALID_ARGUMENT);
    assert(output.data == NULL);
    reaper_elf64_buffer_destroy(&objects[0]);
    reaper_elf64_buffer_destroy(&objects[1]);
}

static void test_unresolved_symbol_and_wx_rejected(void) {
    static const uint8_t text[] = {0xe8, 0, 0, 0, 0, 0xc3};
    const ReaperElf64Section sections[] = {
        {".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 16u, 0u, text, sizeof text}
    };
    const ReaperElf64Symbol symbols[] = {
        {"_start", 0u, 0u, sizeof text, REAPER_ELF64_STB_GLOBAL,
         REAPER_ELF64_STT_FUNC, 0u},
        {"missing", REAPER_ELF64_NO_SECTION, 0u, 0u,
         REAPER_ELF64_STB_GLOBAL, REAPER_ELF64_STT_NOTYPE, 0u}
    };
    const ReaperElf64Relocation relocation = {
        0u, 1u, 1u, REAPER_ELF64_R_X86_64_PC32, -4
    };
    const ReaperElf64Object model = {sections, 1u, symbols, 2u, &relocation, 1u};
    ReaperElf64Buffer object = {0}, executable = {0};
    ReaperElf64Error error = {0};
    assert(reaper_elf64_write_object(&model, &object, &error) == REAPER_ELF64_OK);
    ReaperElf64Buffer input_objects[] = {object};
    ReaperElf64LinkInput input = {input_objects, 1u, "_start", 0x400000u, 4096u};
    assert(reaper_elf64_link(&input, &executable, &error) == REAPER_ELF64_UNSUPPORTED);
    assert(executable.data == NULL);

    reaper_elf64_buffer_destroy(&object);
    ReaperElf64Section wx = sections[0];
    wx.flags = 0x7u;
    const ReaperElf64Symbol local_symbols[] = {
        {"_start", 0u, 0u, sizeof text, REAPER_ELF64_STB_GLOBAL,
         REAPER_ELF64_STT_FUNC, 0u}
    };
    const ReaperElf64Object wx_model = {&wx, 1u, local_symbols, 1u, NULL, 0u};
    assert(reaper_elf64_write_object(&wx_model, &object, &error) == REAPER_ELF64_OK);
    input_objects[0] = object;
    assert(reaper_elf64_link(&input, &executable, &error) == REAPER_ELF64_UNSUPPORTED);
    reaper_elf64_buffer_destroy(&object);
}

int main(void) {
    test_static_link_and_relocation();
    test_unresolved_symbol_and_wx_rejected();
    test_cross_object_symbol_resolution();
    test_duplicate_strong_symbol_rejected();
    puts("ELF64 static linker tests passed");
    return 0;
}
