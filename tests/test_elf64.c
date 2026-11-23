#ifdef NDEBUG
#undef NDEBUG
#endif
#include "reaper/elf64.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint16_t get16(const uint8_t *data) {
    return (uint16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8u));
}

static uint32_t get32(const uint8_t *data) {
    uint32_t value = 0u;
    for (unsigned i = 0u; i < 4u; ++i)
        value |= (uint32_t)data[i] << (i * 8u);
    return value;
}

static uint64_t get64(const uint8_t *data) {
    uint64_t value = 0u;
    for (unsigned i = 0u; i < 8u; ++i)
        value |= (uint64_t)data[i] << (i * 8u);
    return value;
}

static const char *section_name(const uint8_t *file, uint64_t shoff,
                                uint16_t shstrndx, uint32_t index) {
    const uint8_t *header = file + (size_t)shoff + (size_t)index * 64u;
    uint64_t names_offset = get64(file + (size_t)shoff +
                                  (size_t)shstrndx * 64u + 24u);
    uint32_t name_offset = get32(header);
    return (const char *)(file + (size_t)names_offset + name_offset);
}

static void test_object_with_symbols_and_relocations(void) {
    static const uint8_t text[] = {
        0xe8, 0, 0, 0, 0,       /* call external_function */
        0x48, 0xb8, 0, 0, 0, 0, 0, 0, 0, 0, /* movabs address */
        0xc3
    };
    static const uint8_t rodata[] = "reaper";
    static const uint8_t data[] = {0, 0, 0, 0, 0, 0, 0, 0};
    const ReaperElf64Section sections[] = {
        {".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 16u, 0u,
         text, sizeof text},
        {".rodata", REAPER_ELF64_SHT_PROGBITS, 0x2u, 1u, 0u,
         rodata, sizeof rodata},
        {".data", REAPER_ELF64_SHT_PROGBITS, 0x3u, 8u, 0u,
         data, sizeof data},
        {".bss", REAPER_ELF64_SHT_NOBITS, 0x3u, 16u, 0u,
         NULL, 32u}
    };
    const ReaperElf64Symbol symbols[] = {
        {"_start", 0u, 0u, sizeof text, REAPER_ELF64_STB_GLOBAL,
         REAPER_ELF64_STT_FUNC, 0u},
        {"message", 1u, 0u, sizeof rodata, REAPER_ELF64_STB_LOCAL,
         REAPER_ELF64_STT_OBJECT, 0u},
        {"external_function", REAPER_ELF64_NO_SECTION, 0u, 0u,
         REAPER_ELF64_STB_GLOBAL, REAPER_ELF64_STT_NOTYPE, 0u}
    };
    const ReaperElf64Relocation relocations[] = {
        {0u, 1u, 2u, REAPER_ELF64_R_X86_64_PLT32, -4},
        {0u, 7u, 1u, REAPER_ELF64_R_X86_64_64, 0},
        {2u, 0u, 1u, REAPER_ELF64_R_X86_64_64, 0}
    };
    const ReaperElf64Object object = {
        sections, 4u, symbols, 3u, relocations, 3u
    };
    ReaperElf64Buffer output = {0};
    ReaperElf64Error error = {0};

    assert(reaper_elf64_write_object(&object, &output, &error) == REAPER_ELF64_OK);
    assert(output.data != NULL && output.size > 64u);
    assert(memcmp(output.data, "\x7f" "ELF", 4u) == 0);
    assert(output.data[4] == 2u && output.data[5] == 1u && output.data[6] == 1u);
    assert(get16(output.data + 16u) == 1u);
    assert(get16(output.data + 18u) == 62u);
    assert(get16(output.data + 52u) == 64u);
    assert(get16(output.data + 58u) == 64u);

    uint64_t shoff = get64(output.data + 40u);
    uint16_t shnum = get16(output.data + 60u);
    uint16_t shstrndx = get16(output.data + 62u);
    assert(shnum == 10u);
    assert(shstrndx == 9u);
    assert(shoff + (uint64_t)shnum * 64u == output.size);

    uint32_t symtab_index = UINT32_MAX;
    uint32_t rela_text_index = UINT32_MAX;
    uint32_t rela_data_index = UINT32_MAX;
    uint32_t bss_index = UINT32_MAX;
    for (uint32_t i = 1u; i < shnum; ++i) {
        const uint8_t *header = output.data + (size_t)shoff + (size_t)i * 64u;
        const char *name = section_name(output.data, shoff, shstrndx, i);
        uint32_t type = get32(header + 4u);
        if (strcmp(name, ".symtab") == 0) symtab_index = i;
        if (strcmp(name, ".rela.text") == 0)
            rela_text_index = i;
        if (strcmp(name, ".rela.data") == 0)
            rela_data_index = i;
        if (strcmp(name, ".bss") == 0) {
            bss_index = i;
            assert(type == REAPER_ELF64_SHT_NOBITS);
            assert(get64(header + 32u) == 32u);
        }
    }
    assert(symtab_index != UINT32_MAX);
    assert(rela_text_index != UINT32_MAX);
    assert(rela_data_index != UINT32_MAX);
    assert(bss_index == 4u);

    const uint8_t *symtab = output.data + (size_t)shoff +
                            (size_t)symtab_index * 64u;
    assert(get32(symtab + 40u) == symtab_index + 1u);
    assert(get64(symtab + 56u) == 24u);
    assert(get64(symtab + 32u) == 8u * 24u);
    assert(get32(symtab + 44u) == 6u);

    const uint8_t *rela_text = output.data + (size_t)shoff +
                               (size_t)rela_text_index * 64u;
    assert(get32(rela_text + 40u) == symtab_index);
    assert(get32(rela_text + 44u) == 1u);
    assert(get64(rela_text + 32u) == 2u * 24u);
    uint64_t rela_text_offset = get64(rela_text + 24u);
    assert(get32(output.data + (size_t)rela_text_offset + 8u) ==
           REAPER_ELF64_R_X86_64_PLT32);
    assert(get32(output.data + (size_t)rela_text_offset + 12u) == 7u);
    assert((int64_t)get64(output.data + (size_t)rela_text_offset + 16u) == -4);

    const uint8_t *rela_data = output.data + (size_t)shoff +
                               (size_t)rela_data_index * 64u;
    assert(get32(rela_data + 40u) == symtab_index);
    assert(get32(rela_data + 44u) == 3u);
    assert(get64(rela_data + 32u) == 24u);

    reaper_elf64_buffer_destroy(&output);
    assert(output.data == NULL && output.size == 0u);
}

static void test_rejects_bad_relocations_and_alignment(void) {
    static const uint8_t code[] = {0x90, 0xc3, 0, 0};
    const ReaperElf64Section section = {
        ".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 3u, 0u, code, sizeof code
    };
    const ReaperElf64Symbol symbol = {
        "external", REAPER_ELF64_NO_SECTION, 0u, 0u,
        REAPER_ELF64_STB_GLOBAL, REAPER_ELF64_STT_NOTYPE, 0u
    };
    ReaperElf64Relocation relocation = {
        0u, 1u, 0u, REAPER_ELF64_R_X86_64_PC32, 0
    };
    ReaperElf64Object object = {&section, 1u, &symbol, 1u, &relocation, 1u};
    ReaperElf64Buffer output = {0};
    ReaperElf64Error error = {0};

    assert(reaper_elf64_write_object(&object, &output, &error) ==
           REAPER_ELF64_RANGE_ERROR);
    assert(output.data == NULL);
    relocation.offset = 0u;
    relocation.type = 0xdeadbeefu;
    assert(reaper_elf64_write_object(&object, &output, &error) ==
           REAPER_ELF64_UNSUPPORTED);
    relocation.type = REAPER_ELF64_R_X86_64_PC32;
    ReaperElf64Section invalid = section;
    invalid.alignment = 3u;
    object.sections = &invalid;
    object.relocation_count = 0u;
    assert(reaper_elf64_write_object(&object, &output, &error) ==
           REAPER_ELF64_INVALID_ARGUMENT);
    assert(output.data == NULL);
}

static void test_empty_object(void) {
    const ReaperElf64Object object = {0};
    ReaperElf64Buffer output = {0};
    assert(reaper_elf64_write_object(&object, &output, NULL) == REAPER_ELF64_OK);
    assert(output.data != NULL);
    assert(get16(output.data + 60u) == 4u);
    reaper_elf64_buffer_destroy(&output);
}

int main(void) {
    test_object_with_symbols_and_relocations();
    test_rejects_bad_relocations_and_alignment();
    test_empty_object();
    puts("ELF64 writer tests passed");
    return 0;
}
