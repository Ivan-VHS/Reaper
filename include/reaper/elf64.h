#ifndef REAPER_ELF64_H
#define REAPER_ELF64_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_ELF64_NO_SECTION UINT32_MAX
#define REAPER_ELF64_ABSOLUTE_SECTION (UINT32_MAX - 1u)

typedef enum {
    REAPER_ELF64_OK = 0,
    REAPER_ELF64_INVALID_ARGUMENT,
    REAPER_ELF64_UNSUPPORTED,
    REAPER_ELF64_RANGE_ERROR,
    REAPER_ELF64_OUT_OF_MEMORY,
    REAPER_ELF64_UNRESOLVED_SYMBOL,
    REAPER_ELF64_DUPLICATE_SYMBOL,
    REAPER_ELF64_INVALID_ENTRY
} ReaperElf64Status;

typedef enum {
    REAPER_ELF64_SHT_PROGBITS = 1,
    REAPER_ELF64_SHT_NOBITS = 8
} ReaperElf64SectionType;

typedef enum {
    REAPER_ELF64_SHF_WRITE = 1u,
    REAPER_ELF64_SHF_ALLOC = 2u,
    REAPER_ELF64_SHF_EXECINSTR = 4u
} ReaperElf64SectionFlags;

typedef enum {
    REAPER_ELF64_STB_LOCAL = 0,
    REAPER_ELF64_STB_GLOBAL = 1,
    REAPER_ELF64_STB_WEAK = 2
} ReaperElf64Binding;

typedef enum {
    REAPER_ELF64_STT_NOTYPE = 0,
    REAPER_ELF64_STT_OBJECT = 1,
    REAPER_ELF64_STT_FUNC = 2
} ReaperElf64SymbolType;

typedef enum {
    REAPER_ELF64_R_X86_64_64 = 1,
    REAPER_ELF64_R_X86_64_PC32 = 2,
    REAPER_ELF64_R_X86_64_PLT32 = 4,
    REAPER_ELF64_R_X86_64_32 = 10,
    REAPER_ELF64_R_X86_64_32S = 11
} ReaperElf64RelocationType;

typedef struct {
    const char *name;
    uint32_t type;
    uint64_t flags;
    uint64_t alignment;
    uint64_t entry_size;
    const uint8_t *data;
    uint64_t size;
} ReaperElf64Section;

typedef struct {
    const char *name;
    uint32_t section_index;
    uint64_t value;
    uint64_t size;
    uint8_t binding;
    uint8_t type;
    uint8_t visibility;
} ReaperElf64Symbol;

typedef struct {
    uint32_t target_section;
    uint64_t offset;
    uint32_t symbol_index;
    uint32_t type;
    int64_t addend;
} ReaperElf64Relocation;

typedef struct {
    const ReaperElf64Section *sections;
    uint32_t section_count;
    const ReaperElf64Symbol *symbols;
    uint32_t symbol_count;
    const ReaperElf64Relocation *relocations;
    uint32_t relocation_count;
} ReaperElf64Object;

typedef struct {
    uint8_t *data;
    uint64_t size;
} ReaperElf64Buffer;

typedef struct {
    uint32_t item_index;
    char message[192];
} ReaperElf64Error;

/*
 * Writes a deterministic ELF64 little-endian ET_REL object for EM_X86_64.
 * Section and symbol indices in the input model are zero-based. Relocations
 * use input symbol indices and are emitted in SHT_RELA sections.
 */
ReaperElf64Status reaper_elf64_write_object(
    const ReaperElf64Object *object,
    ReaperElf64Buffer *output,
    ReaperElf64Error *error
);
void reaper_elf64_buffer_destroy(ReaperElf64Buffer *buffer);
const char *reaper_elf64_status_name(ReaperElf64Status status);

#ifdef __cplusplus
}
#endif

#endif
