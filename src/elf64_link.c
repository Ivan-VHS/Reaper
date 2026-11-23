#include "reaper/elf64_link.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ELF_EHDR_SIZE 64u
#define ELF_PHDR_SIZE 56u
#define ELF_SHDR_SIZE 64u
#define ELF_SYM_SIZE 24u
#define ELF_RELA_SIZE 24u
#define ELF_ET_REL 1u
#define ELF_ET_EXEC 2u
#define ELF_EM_X86_64 62u
#define ELF_EV_CURRENT 1u
#define ELF_SHT_PROGBITS 1u
#define ELF_SHT_SYMTAB 2u
#define ELF_SHT_STRTAB 3u
#define ELF_SHT_RELA 4u
#define ELF_SHT_NOBITS 8u
#define ELF_SHN_UNDEF 0u
#define ELF_SHN_ABS 0xfff1u
#define ELF_SHF_WRITE 1u
#define ELF_SHF_ALLOC 2u
#define ELF_SHF_EXECINSTR 4u
#define ELF_PF_X 1u
#define ELF_PF_W 2u
#define ELF_PF_R 4u
#define ELF_PT_LOAD 1u
#define ELF_R_X86_64_64 1u
#define ELF_R_X86_64_PC32 2u
#define ELF_R_X86_64_PLT32 4u
#define ELF_R_X86_64_32 10u
#define ELF_R_X86_64_32S 11u

typedef struct {
    uint32_t type;
    uint32_t link;
    uint32_t info;
    uint64_t flags;
    uint64_t offset;
    uint64_t size;
    uint64_t alignment;
    uint64_t entry_size;
    uint64_t image_offset;
    uint64_t address;
} LinkSection;

typedef struct {
    uint8_t info;
    uint8_t visibility;
    uint16_t section_index;
    uint64_t value;
    uint64_t size;
    const char *name;
} LinkSymbol;

typedef struct {
    const uint8_t *file;
    uint64_t file_size;
    LinkSection *sections;
    uint32_t section_count;
    LinkSymbol *symbols;
    uint32_t symbol_count;
    uint32_t symbol_table_index;
    const char *strings;
    uint64_t string_size;
} LinkObject;

static uint16_t read16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8u));
}
static uint32_t read32(const uint8_t *p) {
    uint32_t value = 0u;
    for (unsigned i = 0u; i < 4u; ++i)
        value |= (uint32_t)p[i] << (i * 8u);
    return value;
}
static uint64_t read64(const uint8_t *p) {
    uint64_t value = 0u;
    for (unsigned i = 0u; i < 8u; ++i)
        value |= (uint64_t)p[i] << (i * 8u);
    return value;
}
static void write16(uint8_t *p, uint16_t value) {
    for (unsigned i = 0u; i < 2u; ++i)
        p[i] = (uint8_t)(value >> (i * 8u));
}
static void write32(uint8_t *p, uint32_t value) {
    for (unsigned i = 0u; i < 4u; ++i)
        p[i] = (uint8_t)(value >> (i * 8u));
}
static void write64(uint8_t *p, uint64_t value) {
    for (unsigned i = 0u; i < 8u; ++i)
        p[i] = (uint8_t)(value >> (i * 8u));
}
static int range_ok(uint64_t offset, uint64_t length, uint64_t total) {
    return offset <= total && length <= total - offset;
}
static int checked_add_u64(uint64_t left, uint64_t right, uint64_t *out) {
    if (left > UINT64_MAX - right) return 0;
    *out = left + right;
    return 1;
}
static int checked_align_u64(uint64_t value, uint64_t alignment, uint64_t *out) {
    if (alignment == 0u || (alignment & (alignment - 1u)) != 0u) return 0;
    uint64_t mask = alignment - 1u;
    if (value > UINT64_MAX - mask) return 0;
    *out = (value + mask) & ~mask;
    return 1;
}
static int power_of_two(uint64_t value) {
    return value != 0u && (value & (value - 1u)) == 0u;
}
static ReaperElf64Status link_fail(ReaperElf64Error *error, uint32_t index,
                                   ReaperElf64Status status, const char *message) {
    if (error != NULL) {
        error->item_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}
static int string_at(const char *table, uint64_t size, uint32_t offset,
                     const char **out) {
    if ((uint64_t)offset >= size) return 0;
    const char *value = table + offset;
    if (memchr(value, '\0', (size_t)(size - offset)) == NULL) return 0;
    *out = value;
    return 1;
}
static uint8_t symbol_binding(const LinkSymbol *symbol) {
    return (uint8_t)(symbol->info >> 4u);
}
static void destroy_objects(LinkObject *objects, uint32_t count) {
    if (objects == NULL) return;
    for (uint32_t i = 0u; i < count; ++i) {
        free(objects[i].sections);
        free(objects[i].symbols);
    }
    free(objects);
}

static int parse_object(const ReaperElf64Buffer *input, LinkObject *out) {
    const uint8_t *file = input->data;
    uint64_t size = input->size;
    uint64_t shoff;
    uint16_t shnum, shentsize, shstrndx;
    uint64_t shstr_offset, shstr_size;

    if (file == NULL || size < ELF_EHDR_SIZE ||
        file[0] != 0x7fu || file[1] != 'E' || file[2] != 'L' || file[3] != 'F' ||
        file[4] != 2u || file[5] != 1u || file[6] != 1u ||
        read16(file + 16u) != ELF_ET_REL ||
        read16(file + 18u) != ELF_EM_X86_64 ||
        read32(file + 20u) != ELF_EV_CURRENT)
        return 0;

    shoff = read64(file + 40u);
    shentsize = read16(file + 58u);
    shnum = read16(file + 60u);
    shstrndx = read16(file + 62u);
    if (shentsize != ELF_SHDR_SIZE || shnum == 0u || shstrndx >= shnum ||
        !range_ok(shoff, (uint64_t)shnum * ELF_SHDR_SIZE, size))
        return 0;

    const uint8_t *shstr = file + (size_t)shoff +
                           (size_t)shstrndx * ELF_SHDR_SIZE;
    if (read32(shstr + 4u) != ELF_SHT_STRTAB) return 0;
    shstr_offset = read64(shstr + 24u);
    shstr_size = read64(shstr + 32u);
    if (shstr_size == 0u || !range_ok(shstr_offset, shstr_size, size)) return 0;

    memset(out, 0, sizeof *out);
    out->file = file;
    out->file_size = size;
    out->section_count = shnum;
    out->sections = (LinkSection *)calloc(shnum, sizeof *out->sections);
    if (out->sections == NULL) return 0;

    const char *section_names = (const char *)(file + (size_t)shstr_offset);
    for (uint32_t i = 0u; i < shnum; ++i) {
        const uint8_t *p = file + (size_t)shoff + (size_t)i * ELF_SHDR_SIZE;
        LinkSection *section = &out->sections[i];
        section->type = read32(p + 4u);
        section->flags = read64(p + 8u);
        section->offset = read64(p + 24u);
        section->size = read64(p + 32u);
        section->link = read32(p + 40u);
        section->info = read32(p + 44u);
        section->alignment = read64(p + 48u);
        section->entry_size = read64(p + 56u);
        uint32_t name_offset = read32(p);
        const char *unused_name = NULL;
        if (!string_at(section_names, shstr_size, name_offset, &unused_name))
            return 0;
        if (section->type != 0u && section->type != ELF_SHT_NOBITS &&
            !range_ok(section->offset, section->size, size))
            return 0;
        if (section->alignment > 1u && !power_of_two(section->alignment))
            return 0;
    }

    uint32_t symbol_tables = 0u;
    for (uint32_t i = 0u; i < shnum; ++i) {
        if (out->sections[i].type == ELF_SHT_SYMTAB) {
            out->symbol_table_index = i;
            symbol_tables++;
        }
    }
    if (symbol_tables != 1u) return 0;

    LinkSection *symtab = &out->sections[out->symbol_table_index];
    if (symtab->entry_size != ELF_SYM_SIZE ||
        symtab->size % ELF_SYM_SIZE != 0u || symtab->link >= shnum)
        return 0;
    LinkSection *strtab = &out->sections[symtab->link];
    if (strtab->type != ELF_SHT_STRTAB ||
        !range_ok(strtab->offset, strtab->size, size) || strtab->size == 0u)
        return 0;
    out->strings = (const char *)(file + (size_t)strtab->offset);
    out->string_size = strtab->size;

    if (symtab->size / ELF_SYM_SIZE > UINT32_MAX) return 0;
    out->symbol_count = (uint32_t)(symtab->size / ELF_SYM_SIZE);
    out->symbols = (LinkSymbol *)calloc(out->symbol_count, sizeof *out->symbols);
    if (out->symbol_count != 0u && out->symbols == NULL) return 0;

    for (uint32_t i = 0u; i < out->symbol_count; ++i) {
        const uint8_t *p = file + (size_t)symtab->offset +
                           (size_t)i * ELF_SYM_SIZE;
        LinkSymbol *symbol = &out->symbols[i];
        uint32_t name_offset = read32(p);
        symbol->info = p[4];
        symbol->visibility = p[5];
        symbol->section_index = read16(p + 6u);
        symbol->value = read64(p + 8u);
        symbol->size = read64(p + 16u);
        if (!string_at(out->strings, out->string_size, name_offset, &symbol->name))
            return 0;
        if (symbol->section_index != ELF_SHN_UNDEF &&
            symbol->section_index != ELF_SHN_ABS) {
            if (symbol->section_index >= shnum ||
                symbol->value > out->sections[symbol->section_index].size)
                return 0;
        }
    }
    return 1;
}

static int section_symbol_value(const LinkObject *object,
                                const LinkSymbol *symbol,
                                uint64_t *address) {
    if (symbol->section_index == ELF_SHN_ABS) {
        *address = symbol->value;
        return 1;
    }
    if (symbol->section_index == ELF_SHN_UNDEF ||
        symbol->section_index >= object->section_count)
        return 0;
    const LinkSection *section = &object->sections[symbol->section_index];
    if ((section->flags & ELF_SHF_ALLOC) == 0u ||
        symbol->value >= section->size ||
        !checked_add_u64(section->address, symbol->value, address))
        return 0;
    return 1;
}

static int resolve_symbol(const LinkObject *objects, uint32_t object_count,
                          uint32_t source_object, uint32_t symbol_index,
                          uint64_t *address) {
    const LinkObject *owner = &objects[source_object];
    if (symbol_index >= owner->symbol_count) return 0;
    const LinkSymbol *reference = &owner->symbols[symbol_index];
    uint8_t binding = symbol_binding(reference);

    if (reference->section_index != ELF_SHN_UNDEF)
        return section_symbol_value(owner, reference, address);
    if (binding == 0u) return 0;

    const LinkSymbol *strong = NULL;
    const LinkObject *strong_owner = NULL;
    const LinkSymbol *weak = NULL;
    const LinkObject *weak_owner = NULL;
    for (uint32_t oi = 0u; oi < object_count; ++oi) {
        for (uint32_t si = 0u; si < objects[oi].symbol_count; ++si) {
            const LinkSymbol *candidate = &objects[oi].symbols[si];
            uint8_t candidate_binding = symbol_binding(candidate);
            if (candidate->name[0] == '\0' ||
                strcmp(candidate->name, reference->name) != 0 ||
                candidate->section_index == ELF_SHN_UNDEF ||
                (candidate_binding != 1u && candidate_binding != 2u))
                continue;
            if (candidate_binding == 1u) {
                if (strong != NULL) return 0;
                strong = candidate;
                strong_owner = &objects[oi];
            } else if (weak == NULL) {
                weak = candidate;
                weak_owner = &objects[oi];
            }
        }
    }
    if (strong != NULL)
        return section_symbol_value(strong_owner, strong, address);
    if (weak != NULL)
        return section_symbol_value(weak_owner, weak, address);
    if (binding == 2u) {
        *address = 0u;
        return 1;
    }
    return 0;
}

static int relocation_width(uint32_t type, uint64_t *width) {
    if (type == ELF_R_X86_64_64) { *width = 8u; return 1; }
    if (type == ELF_R_X86_64_PC32 || type == ELF_R_X86_64_PLT32 ||
        type == ELF_R_X86_64_32 || type == ELF_R_X86_64_32S) {
        *width = 4u;
        return 1;
    }
    return 0;
}
static int add_signed_u64(uint64_t base, int64_t addend, uint64_t *result) {
    if (addend >= 0) return checked_add_u64(base, (uint64_t)addend, result);
    uint64_t magnitude = (uint64_t)(-(addend + 1)) + 1u;
    if (base < magnitude) return 0;
    *result = base - magnitude;
    return 1;
}
static int patch_relocation(uint8_t *place_bytes, uint32_t type,
                            uint64_t symbol, uint64_t place, int64_t addend) {
    uint64_t value;
    if (type == ELF_R_X86_64_64) {
        if (!add_signed_u64(symbol, addend, &value)) return 0;
        write64(place_bytes, value);
        return 1;
    }
    if (type == ELF_R_X86_64_32) {
        if (!add_signed_u64(symbol, addend, &value) || value > UINT32_MAX)
            return 0;
        write32(place_bytes, (uint32_t)value);
        return 1;
    }
    if (type == ELF_R_X86_64_32S) {
        if (!add_signed_u64(symbol, addend, &value) ||
            (value > (uint64_t)INT32_MAX &&
             value < UINT64_MAX - (uint64_t)INT32_MAX))
            return 0;
        write32(place_bytes, (uint32_t)value);
        return 1;
    }
    if (type == ELF_R_X86_64_PC32 || type == ELF_R_X86_64_PLT32) {
        if (!add_signed_u64(symbol, addend, &value)) return 0;
        if (value >= place) {
            uint64_t distance = value - place;
            if (distance > (uint64_t)INT32_MAX) return 0;
            write32(place_bytes, (uint32_t)distance);
        } else {
            uint64_t distance = place - value;
            if (distance > (uint64_t)INT32_MAX + 1u) return 0;
            write32(place_bytes, (uint32_t)(int32_t)(-(int64_t)distance));
        }
        return 1;
    }
    return 0;
}

static int duplicate_strong_symbols(const LinkObject *objects,
                                    uint32_t object_count,
                                    uint32_t *bad_object,
                                    uint32_t *bad_symbol) {
    for (uint32_t oi = 0u; oi < object_count; ++oi) {
        for (uint32_t si = 0u; si < objects[oi].symbol_count; ++si) {
            const LinkSymbol *left = &objects[oi].symbols[si];
            if (symbol_binding(left) != 1u || left->name[0] == '\0' ||
                left->section_index == ELF_SHN_UNDEF)
                continue;
            for (uint32_t oj = oi; oj < object_count; ++oj) {
                uint32_t start = oj == oi ? si + 1u : 0u;
                for (uint32_t sj = start; sj < objects[oj].symbol_count; ++sj) {
                    const LinkSymbol *right = &objects[oj].symbols[sj];
                    if (symbol_binding(right) == 1u &&
                        right->section_index != ELF_SHN_UNDEF &&
                        strcmp(left->name, right->name) == 0) {
                        *bad_object = oj;
                        *bad_symbol = sj;
                        return 1;
                    }
                }
            }
        }
    }
    return 0;
}

ReaperElf64Status reaper_elf64_link(
    const ReaperElf64LinkInput *input,
    ReaperElf64Buffer *output,
    ReaperElf64Error *error
) {
    LinkObject *objects = NULL;
    uint8_t *image = NULL;
    uint64_t image_base, page_size, header_bytes, file_cursor, memory_cursor;
    uint64_t file_size, entry_address = 0u;
    uint32_t alloc_count = 0u, program_header_count = 0u;
    int entry_found = 0;
    ReaperElf64Status status = REAPER_ELF64_OK;

    if (error != NULL) { error->item_index = 0u; error->message[0] = '\0'; }
    if (output != NULL) { output->data = NULL; output->size = 0u; }
    if (input == NULL || output == NULL || input->objects == NULL ||
        input->object_count == 0u || input->entry_symbol == NULL ||
        input->entry_symbol[0] == '\0')
        return link_fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                         "link input, object array, entry symbol and output are required");

    objects = (LinkObject *)calloc(input->object_count, sizeof *objects);
    if (objects == NULL)
        return link_fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                         "cannot allocate input object table");

    for (uint32_t oi = 0u; oi < input->object_count; ++oi) {
        if (!parse_object(&input->objects[oi], &objects[oi])) {
            status = link_fail(error, oi, REAPER_ELF64_INVALID_ARGUMENT,
                               "input is not a supported x86-64 ET_REL object");
            goto done;
        }
        for (uint32_t si = 0u; si < objects[oi].section_count; ++si) {
            const LinkSection *section = &objects[oi].sections[si];
            if ((section->flags & ELF_SHF_ALLOC) == 0u || section->size == 0u)
                continue;
            if (section->type != ELF_SHT_PROGBITS &&
                section->type != ELF_SHT_NOBITS) {
                status = link_fail(error, si, REAPER_ELF64_UNSUPPORTED,
                                   "allocated section type is unsupported");
                goto done;
            }
            if ((section->flags & (ELF_SHF_WRITE | ELF_SHF_EXECINSTR)) ==
                (ELF_SHF_WRITE | ELF_SHF_EXECINSTR)) {
                status = link_fail(error, si, REAPER_ELF64_UNSUPPORTED,
                                   "writable executable sections are rejected by W^X policy");
                goto done;
            }
            alloc_count++;
        }
    }
    uint32_t bad_object = 0u, bad_symbol = 0u;
    if (duplicate_strong_symbols(objects, input->object_count,
                                 &bad_object, &bad_symbol)) {
        status = link_fail(error, bad_symbol, REAPER_ELF64_INVALID_ARGUMENT,
                           "duplicate strong symbol definition");
        goto done;
    }
    if (alloc_count >= UINT16_MAX) {
        status = link_fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                           "too many loadable sections");
        goto done;
    }

    image_base = input->image_base == 0u ? 0x400000u : input->image_base;
    page_size = input->page_size == 0u ? 4096u : input->page_size;
    if (!power_of_two(page_size) || (image_base & (page_size - 1u)) != 0u) {
        status = link_fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                           "image base and page size must be page-aligned");
        goto done;
    }
    program_header_count = alloc_count + 1u;
    header_bytes = ELF_EHDR_SIZE + (uint64_t)program_header_count * ELF_PHDR_SIZE;
    if (!checked_align_u64(header_bytes, page_size, &file_cursor)) {
        status = link_fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                           "ELF header layout overflows");
        goto done;
    }
    memory_cursor = file_cursor;

    for (uint32_t oi = 0u; oi < input->object_count; ++oi) {
        for (uint32_t si = 0u; si < objects[oi].section_count; ++si) {
            LinkSection *section = &objects[oi].sections[si];
            if ((section->flags & ELF_SHF_ALLOC) == 0u || section->size == 0u)
                continue;
            uint64_t alignment = section->alignment > page_size ?
                                 section->alignment : page_size;
            if (!checked_align_u64(file_cursor, alignment, &section->image_offset) ||
                !checked_align_u64(memory_cursor, alignment, &section->address) ||
                !checked_add_u64(image_base, section->address, &section->address)) {
                status = link_fail(error, si, REAPER_ELF64_RANGE_ERROR,
                                   "loadable section address overflows");
                goto done;
            }
            if (!checked_add_u64(memory_cursor, section->size, &memory_cursor)) {
                status = link_fail(error, si, REAPER_ELF64_RANGE_ERROR,
                                   "loadable section memory range overflows");
                goto done;
            }
            if (section->type == ELF_SHT_PROGBITS &&
                !checked_add_u64(section->image_offset, section->size, &file_cursor)) {
                status = link_fail(error, si, REAPER_ELF64_RANGE_ERROR,
                                   "loadable section file range overflows");
                goto done;
            }
        }
    }
    file_size = file_cursor;
    if (file_size > (uint64_t)SIZE_MAX) {
        status = link_fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                           "linked executable exceeds addressable memory");
        goto done;
    }
    image = (uint8_t *)calloc((size_t)file_size, 1u);
    if (image == NULL) {
        status = link_fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                           "cannot allocate linked executable");
        goto done;
    }
    for (uint32_t oi = 0u; oi < input->object_count; ++oi) {
        for (uint32_t si = 0u; si < objects[oi].section_count; ++si) {
            const LinkSection *section = &objects[oi].sections[si];
            if ((section->flags & ELF_SHF_ALLOC) != 0u &&
                section->type == ELF_SHT_PROGBITS && section->size != 0u)
                memcpy(image + (size_t)section->image_offset,
                       objects[oi].file + (size_t)section->offset,
                       (size_t)section->size);
        }
    }

    /* Resolve the requested entry symbol from all supplied objects. */
    for (uint32_t oi = 0u; oi < input->object_count; ++oi) {
        for (uint32_t si = 0u; si < objects[oi].symbol_count; ++si) {
            const LinkSymbol *symbol = &objects[oi].symbols[si];
            if (strcmp(symbol->name, input->entry_symbol) != 0 ||
                symbol->section_index == ELF_SHN_UNDEF)
                continue;
            uint64_t address = 0u;
            if (!section_symbol_value(&objects[oi], symbol, &address)) continue;
            if (entry_found) {
                status = link_fail(error, si, REAPER_ELF64_INVALID_ARGUMENT,
                                   "entry symbol is ambiguous");
                goto done;
            }
            entry_address = address;
            entry_found = 1;
        }
    }
    if (!entry_found) {
        status = link_fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                           "entry symbol is missing or not in a loadable section");
        goto done;
    }

    for (uint32_t oi = 0u; oi < input->object_count; ++oi) {
        LinkObject *object = &objects[oi];
        for (uint32_t ri = 0u; ri < object->section_count; ++ri) {
            const LinkSection *rela = &object->sections[ri];
            if (rela->type != ELF_SHT_RELA) continue;
            if (rela->link != object->symbol_table_index ||
                rela->info >= object->section_count ||
                rela->entry_size != ELF_RELA_SIZE ||
                rela->size % ELF_RELA_SIZE != 0u) {
                status = link_fail(error, ri, REAPER_ELF64_INVALID_ARGUMENT,
                                   "malformed RELA section linkage or entry size");
                goto done;
            }
            LinkSection *target = &object->sections[rela->info];
            if (target->type != ELF_SHT_PROGBITS ||
                (target->flags & ELF_SHF_ALLOC) == 0u) {
                status = link_fail(error, ri, REAPER_ELF64_UNSUPPORTED,
                                   "relocation target must be allocated PROGBITS");
                goto done;
            }
            uint64_t count = rela->size / ELF_RELA_SIZE;
            for (uint64_t ri_index = 0u; ri_index < count; ++ri_index) {
                const uint8_t *p = object->file + (size_t)rela->offset +
                                   (size_t)ri_index * ELF_RELA_SIZE;
                uint64_t offset = read64(p);
                uint64_t info = read64(p + 8u);
                uint32_t symbol_index = (uint32_t)(info >> 32u);
                uint32_t type = (uint32_t)info;
                int64_t addend = (int64_t)read64(p + 16u);
                uint64_t width = 0u, end = 0u, symbol_address = 0u;
                if (!relocation_width(type, &width) ||
                    !checked_add_u64(offset, width, &end) || end > target->size ||
                    symbol_index >= object->symbol_count ||
                    !resolve_symbol(objects, input->object_count, oi,
                                    symbol_index, &symbol_address)) {
                    status = link_fail(error, (uint32_t)ri_index,
                                       REAPER_ELF64_UNSUPPORTED,
                                       "unsupported relocation or unresolved symbol");
                    goto done;
                }
                uint64_t place_address = 0u;
                if (!checked_add_u64(target->address, offset, &place_address) ||
                    !patch_relocation(image + (size_t)target->image_offset +
                                      (size_t)offset, type, symbol_address,
                                      place_address, addend)) {
                    status = link_fail(error, (uint32_t)ri_index,
                                       REAPER_ELF64_RANGE_ERROR,
                                       "relocation value is outside its encoding range");
                    goto done;
                }
            }
        }
    }

    image[0] = 0x7fu; image[1] = 'E'; image[2] = 'L'; image[3] = 'F';
    image[4] = 2u; image[5] = 1u; image[6] = 1u;
    write16(image + 16u, ELF_ET_EXEC);
    write16(image + 18u, ELF_EM_X86_64);
    write32(image + 20u, ELF_EV_CURRENT);
    write64(image + 24u, entry_address);
    write64(image + 32u, ELF_EHDR_SIZE);
    write64(image + 40u, 0u);
    write16(image + 52u, ELF_EHDR_SIZE);
    write16(image + 54u, ELF_PHDR_SIZE);
    write16(image + 56u, (uint16_t)program_header_count);
    write16(image + 58u, 0u);
    write16(image + 60u, 0u);
    write16(image + 62u, 0u);

    uint8_t *ph = image + ELF_EHDR_SIZE;
    write32(ph, ELF_PT_LOAD);
    write32(ph + 4u, ELF_PF_R);
    write64(ph + 8u, 0u);
    write64(ph + 16u, image_base);
    write64(ph + 24u, image_base);
    write64(ph + 32u, header_bytes);
    write64(ph + 40u, header_bytes);
    write64(ph + 48u, page_size);

    uint32_t ph_index = 1u;
    for (uint32_t oi = 0u; oi < input->object_count; ++oi) {
        for (uint32_t si = 0u; si < objects[oi].section_count; ++si) {
            const LinkSection *section = &objects[oi].sections[si];
            if ((section->flags & ELF_SHF_ALLOC) == 0u || section->size == 0u)
                continue;
            uint32_t flags = ELF_PF_R;
            if ((section->flags & ELF_SHF_WRITE) != 0u) flags |= ELF_PF_W;
            if ((section->flags & ELF_SHF_EXECINSTR) != 0u) flags |= ELF_PF_X;
            ph = image + ELF_EHDR_SIZE + (size_t)ph_index * ELF_PHDR_SIZE;
            write32(ph, ELF_PT_LOAD);
            write32(ph + 4u, flags);
            write64(ph + 8u,
                    section->type == ELF_SHT_NOBITS ? file_size : section->image_offset);
            write64(ph + 16u, section->address);
            write64(ph + 24u, section->address);
            write64(ph + 32u,
                    section->type == ELF_SHT_NOBITS ? 0u : section->size);
            write64(ph + 40u, section->size);
            write64(ph + 48u,
                    section->type == ELF_SHT_NOBITS ? 1u : page_size);
            ph_index++;
        }
    }

    output->data = image;
    output->size = file_size;
    image = NULL;

done:
    free(image);
    destroy_objects(objects, input->object_count);
    return status;
}
