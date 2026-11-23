#include "reaper/elf64_link.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define EHDR 64u
#define PHDR 56u
#define SHDR 64u
#define SYM 24u
#define RELA 24u
#define ET_REL 1u
#define ET_EXEC 2u
#define EM_X86_64 62u
#define SHT_PROGBITS 1u
#define SHT_SYMTAB 2u
#define SHT_STRTAB 3u
#define SHT_RELA 4u
#define SHT_NOBITS 8u
#define SHN_UNDEF 0u
#define SHN_ABS 0xfff1u
#define SHF_WRITE 1u
#define SHF_ALLOC 2u
#define SHF_EXECINSTR 4u
#define PF_X 1u
#define PF_W 2u
#define PF_R 4u
#define PT_LOAD 1u

typedef struct {
    uint32_t type, link, info;
    uint64_t flags, offset, size, align, entsize;
    uint64_t image_offset, address;
} Section;

typedef struct {
    uint32_t name;
    uint8_t info, other;
    uint16_t shndx;
    uint64_t value, size;
    const char *text;
} Symbol;

static uint16_t r16(const uint8_t *p) {
    return (uint16_t)(p[0] | ((uint16_t)p[1] << 8u));
}
static uint32_t r32(const uint8_t *p) {
    uint32_t v = 0u;
    for (unsigned i = 0u; i < 4u; ++i) v |= (uint32_t)p[i] << (i * 8u);
    return v;
}
static uint64_t r64(const uint8_t *p) {
    uint64_t v = 0u;
    for (unsigned i = 0u; i < 8u; ++i) v |= (uint64_t)p[i] << (i * 8u);
    return v;
}
static void w16(uint8_t *p, uint16_t v) {
    for (unsigned i = 0u; i < 2u; ++i) p[i] = (uint8_t)(v >> (i * 8u));
}
static void w32(uint8_t *p, uint32_t v) {
    for (unsigned i = 0u; i < 4u; ++i) p[i] = (uint8_t)(v >> (i * 8u));
}
static void w64(uint8_t *p, uint64_t v) {
    for (unsigned i = 0u; i < 8u; ++i) p[i] = (uint8_t)(v >> (i * 8u));
}
static int inside(uint64_t off, uint64_t len, uint64_t total) {
    return off <= total && len <= total - off;
}
static int add64(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return 0;
    *out = a + b;
    return 1;
}
static int align64(uint64_t value, uint64_t align, uint64_t *out) {
    if (align == 0u || (align & (align - 1u)) != 0u) return 0;
    uint64_t mask = align - 1u;
    if (value > UINT64_MAX - mask) return 0;
    *out = (value + mask) & ~mask;
    return 1;
}
static ReaperElf64Status fail(ReaperElf64Error *error, uint32_t index,
                              ReaperElf64Status status, const char *message) {
    if (error != NULL) {
        error->item_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}
static int bounded_name(const char *table, uint64_t size, uint32_t offset,
                        const char **name) {
    if ((uint64_t)offset >= size ||
        memchr(table + offset, '\0', (size_t)(size - offset)) == NULL) return 0;
    *name = table + offset;
    return 1;
}
static int relocation_width(uint32_t type, uint64_t *width) {
    if (type == 1u) { *width = 8u; return 1; }
    if (type == 2u || type == 4u || type == 10u || type == 11u) {
        *width = 4u;
        return 1;
    }
    return 0;
}
static int add_signed(uint64_t base, int64_t addend, uint64_t *out) {
    if (addend >= 0) return add64(base, (uint64_t)addend, out);
    uint64_t magnitude = (uint64_t)(-(addend + 1)) + 1u;
    if (base < magnitude) return 0;
    *out = base - magnitude;
    return 1;
}
static int patch_relocation(uint8_t *where, uint32_t type, uint64_t symbol,
                            uint64_t place, int64_t addend) {
    uint64_t value;
    if (type == 1u) {
        if (!add_signed(symbol, addend, &value)) return 0;
        w64(where, value);
        return 1;
    }
    if (type == 10u) {
        if (!add_signed(symbol, addend, &value) || value > UINT32_MAX) return 0;
        w32(where, (uint32_t)value);
        return 1;
    }
    if (type == 11u) {
        if (!add_signed(symbol, addend, &value) || value > (uint64_t)INT32_MAX) return 0;
        w32(where, (uint32_t)value);
        return 1;
    }
    if (type == 2u || type == 4u) {
        if (!add_signed(symbol, addend, &value)) return 0;
        if (value >= place) {
            uint64_t d = value - place;
            if (d > (uint64_t)INT32_MAX) return 0;
            w32(where, (uint32_t)(int32_t)d);
        } else {
            uint64_t d = place - value;
            if (d > (uint64_t)INT32_MAX + 1u) return 0;
            w32(where, (uint32_t)(int32_t)(-(int64_t)d));
        }
        return 1;
    }
    return 0;
}

ReaperElf64Status reaper_elf64_link(
    const ReaperElf64LinkInput *input,
    ReaperElf64Buffer *output,
    ReaperElf64Error *error
) {
    Section *sections = NULL;
    Symbol *symbols = NULL;
    uint8_t *image = NULL;
    uint32_t section_count = 0u, symbol_count = 0u, symtab_index = UINT32_MAX;
    uint32_t strtab_index = UINT32_MAX, alloc_count = 0u, phnum = 0u;
    uint64_t image_base, page_size, shoff, header_bytes, file_cursor, memory_cursor;
    uint64_t file_size, entry = 0u;
    int entry_found = 0;
    const ReaperElf64Buffer *object;
    ReaperElf64Status status = REAPER_ELF64_OK;

    if (error != NULL) { error->item_index = 0u; error->message[0] = '\0'; }
    if (output != NULL) { output->data = NULL; output->size = 0u; }
    if (input == NULL || output == NULL || input->object == NULL ||
        input->entry_symbol == NULL || input->entry_symbol[0] == '\0' ||
        input->object->data == NULL)
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "object, entry symbol and output are required");
    object = input->object;
    const uint8_t *file = object->data;
    if (object->size < EHDR || file[0] != 0x7fu || file[1] != 'E' ||
        file[2] != 'L' || file[3] != 'F' || file[4] != 2u ||
        file[5] != 1u || file[6] != 1u || r16(file + 16u) != ET_REL ||
        r16(file + 18u) != EM_X86_64)
        return fail(error, 0u, REAPER_ELF64_UNSUPPORTED,
                    "input must be little-endian x86-64 ELF64 ET_REL");
    shoff = r64(file + 40u);
    section_count = r16(file + 60u);
    if (r16(file + 58u) != SHDR || section_count == 0u ||
        !inside(shoff, (uint64_t)section_count * SHDR, object->size))
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "invalid ELF section-header table");

    sections = (Section *)calloc(section_count, sizeof *sections);
    if (sections == NULL)
        return fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY, "cannot allocate sections");
    for (uint32_t i = 0u; i < section_count; ++i) {
        const uint8_t *p = file + (size_t)shoff + (size_t)i * SHDR;
        Section *s = &sections[i];
        s->type = r32(p + 4u);
        s->flags = r64(p + 8u);
        s->offset = r64(p + 24u);
        s->size = r64(p + 32u);
        s->link = r32(p + 40u);
        s->info = r32(p + 44u);
        s->align = r64(p + 48u);
        s->entsize = r64(p + 56u);
        if (s->type != 0u && s->type != SHT_NOBITS &&
            !inside(s->offset, s->size, object->size)) {
            status = fail(error, i, REAPER_ELF64_INVALID_ARGUMENT,
                          "section data lies outside the input object");
            goto done;
        }
        if (s->align > 1u && (s->align & (s->align - 1u)) != 0u) {
            status = fail(error, i, REAPER_ELF64_INVALID_ARGUMENT,
                          "section alignment is not a power of two");
            goto done;
        }
        if (s->type == SHT_SYMTAB) {
            if (symtab_index != UINT32_MAX) {
                status = fail(error, i, REAPER_ELF64_UNSUPPORTED,
                              "multiple symbol tables are not supported");
                goto done;
            }
            symtab_index = i;
        }
    }
    if (symtab_index == UINT32_MAX || sections[symtab_index].link >= section_count ||
        sections[symtab_index].entsize != SYM ||
        sections[symtab_index].size % SYM != 0u) {
        status = fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                      "ELF object has no valid symbol table");
        goto done;
    }
    strtab_index = sections[symtab_index].link;
    if (sections[strtab_index].type != SHT_STRTAB) {
        status = fail(error, strtab_index, REAPER_ELF64_INVALID_ARGUMENT,
                      "symbol string table is invalid");
        goto done;
    }
    const Section *strtab = &sections[strtab_index];
    const char *strings = (const char *)(file + (size_t)strtab->offset);
    symbol_count = (uint32_t)(sections[symtab_index].size / SYM);
    symbols = (Symbol *)calloc(symbol_count, sizeof *symbols);
    if (symbols == NULL) {
        status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY, "cannot allocate symbols");
        goto done;
    }
    for (uint32_t i = 0u; i < symbol_count; ++i) {
        const uint8_t *p = file + (size_t)sections[symtab_index].offset +
                           (size_t)i * SYM;
        Symbol *symbol = &symbols[i];
        symbol->name = r32(p);
        symbol->info = p[4];
        symbol->other = p[5];
        symbol->shndx = r16(p + 6u);
        symbol->value = r64(p + 8u);
        symbol->size = r64(p + 16u);
        if (!bounded_name(strings, strtab->size, symbol->name, &symbol->text) ||
            (symbol->shndx != SHN_UNDEF && symbol->shndx != SHN_ABS &&
             symbol->shndx >= section_count)) {
            status = fail(error, i, REAPER_ELF64_INVALID_ARGUMENT,
                          "invalid symbol name or section index");
            goto done;
        }
    }

    image_base = input->image_base == 0u ? 0x400000u : input->image_base;
    page_size = input->page_size == 0u ? 4096u : input->page_size;
    if ((page_size & (page_size - 1u)) != 0u ||
        (image_base & (page_size - 1u)) != 0u) {
        status = fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                      "image base and page size must be page-aligned");
        goto done;
    }
    for (uint32_t i = 0u; i < section_count; ++i) {
        Section *s = &sections[i];
        if ((s->flags & SHF_ALLOC) == 0u || s->size == 0u) continue;
        if (s->type != SHT_PROGBITS && s->type != SHT_NOBITS) {
            status = fail(error, i, REAPER_ELF64_UNSUPPORTED,
                          "allocated section type is unsupported");
            goto done;
        }
        if ((s->flags & (SHF_WRITE | SHF_EXECINSTR)) ==
            (SHF_WRITE | SHF_EXECINSTR)) {
            status = fail(error, i, REAPER_ELF64_UNSUPPORTED,
                          "W+X sections are rejected");
            goto done;
        }
        alloc_count++;
    }
    if (alloc_count >= UINT16_MAX) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                      "too many loadable sections");
        goto done;
    }
    phnum = alloc_count + 1u;
    header_bytes = EHDR + (uint64_t)phnum * PHDR;
    if (!align64(header_bytes, page_size, &file_cursor)) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR, "image header overflows");
        goto done;
    }
    memory_cursor = file_cursor;
    for (uint32_t i = 0u; i < section_count; ++i) {
        Section *s = &sections[i];
        if ((s->flags & SHF_ALLOC) == 0u || s->size == 0u) continue;
        uint64_t align = s->align > page_size ? s->align : page_size;
        if (!align64(file_cursor, align, &s->image_offset) ||
            !align64(memory_cursor, align, &s->address) ||
            !add64(image_base, s->address, &s->address)) {
            status = fail(error, i, REAPER_ELF64_RANGE_ERROR,
                          "loadable section address overflows");
            goto done;
        }
        if (!add64(memory_cursor, s->size, &memory_cursor)) {
            status = fail(error, i, REAPER_ELF64_RANGE_ERROR,
                          "loadable section memory range overflows");
            goto done;
        }
        if (s->type == SHT_PROGBITS &&
            !add64(s->image_offset, s->size, &file_cursor)) {
            status = fail(error, i, REAPER_ELF64_RANGE_ERROR,
                          "loadable section file range overflows");
            goto done;
        }
    }
    file_size = file_cursor;
    if (file_size > (uint64_t)SIZE_MAX) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                      "executable image is too large for this host");
        goto done;
    }
    image = (uint8_t *)calloc((size_t)file_size, 1u);
    if (image == NULL) {
        status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                      "cannot allocate executable image");
        goto done;
    }
    for (uint32_t i = 0u; i < section_count; ++i) {
        Section *s = &sections[i];
        if ((s->flags & SHF_ALLOC) != 0u && s->type == SHT_PROGBITS &&
            s->size != 0u)
            memcpy(image + (size_t)s->image_offset,
                   file + (size_t)s->offset, (size_t)s->size);
    }

    /* Resolve the entry symbol after section addresses have been assigned. */
    for (uint32_t i = 0u; i < symbol_count; ++i) {
        Symbol *symbol = &symbols[i];
        if (strcmp(symbol->text, input->entry_symbol) != 0 ||
            symbol->shndx == SHN_UNDEF) continue;
        uint64_t value = symbol->value;
        if (symbol->shndx != SHN_ABS) {
            Section *target = &sections[symbol->shndx];
            if ((target->flags & SHF_ALLOC) == 0u || value > target->size ||
                !add64(target->address, value, &value)) continue;
        }
        if (entry_found) {
            status = fail(error, i, REAPER_ELF64_INVALID_ARGUMENT,
                          "entry symbol is ambiguous");
            goto done;
        }
        entry = value;
        entry_found = 1;
    }
    if (!entry_found) {
        status = fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                      "entry symbol is not defined in an allocated section");
        goto done;
    }

    for (uint32_t ri = 0u; ri < section_count; ++ri) {
        const Section *rela = &sections[ri];
        if (rela->type != SHT_RELA) continue;
        if (rela->link != symtab_index || rela->info >= section_count ||
            rela->entsize != RELA || rela->size % RELA != 0u) {
            status = fail(error, ri, REAPER_ELF64_INVALID_ARGUMENT,
                          "invalid RELA section linkage");
            goto done;
        }
        Section *target = &sections[rela->info];
        if (target->type != SHT_PROGBITS || (target->flags & SHF_ALLOC) == 0u) {
            status = fail(error, ri, REAPER_ELF64_UNSUPPORTED,
                          "relocation target must be allocated PROGBITS");
            goto done;
        }
        uint64_t count = rela->size / RELA;
        for (uint64_t j = 0u; j < count; ++j) {
            const uint8_t *p = file + (size_t)rela->offset + (size_t)j * RELA;
            uint64_t offset = r64(p), info = r64(p + 8u);
            uint32_t sym = (uint32_t)(info >> 32u), type = (uint32_t)info;
            int64_t addend = (int64_t)r64(p + 16u);
            uint64_t width = 0u, end = 0u, symbol_address = 0u;
            if (!relocation_width(type, &width) || sym >= symbol_count ||
                !add64(offset, width, &end) || end > target->size) {
                status = fail(error, (uint32_t)j, REAPER_ELF64_UNSUPPORTED,
                              "unsupported relocation type or out-of-range relocation");
                goto done;
            }
            Symbol *symbol = &symbols[sym];
            if (symbol->shndx == SHN_ABS) {
                symbol_address = symbol->value;
            } else if (symbol->shndx != SHN_UNDEF) {
                Section *defined = &sections[symbol->shndx];
                if ((defined->flags & SHF_ALLOC) == 0u ||
                    symbol->value > defined->size ||
                    !add64(defined->address, symbol->value, &symbol_address)) {
                    status = fail(error, (uint32_t)j, REAPER_ELF64_RANGE_ERROR,
                                  "relocation references a non-loadable symbol");
                    goto done;
                }
            } else if ((symbol->info >> 4u) == 2u) {
                symbol_address = 0u;
            } else {
                status = fail(error, (uint32_t)j, REAPER_ELF64_UNSUPPORTED,
                              "unresolved external symbol in static link");
                goto done;
            }
            uint64_t place;
            if (!add64(target->address, offset, &place) ||
                !patch_relocation(image + (size_t)target->image_offset +
                                  (size_t)offset, type, symbol_address, place, addend)) {
                status = fail(error, (uint32_t)j, REAPER_ELF64_RANGE_ERROR,
                              "relocation value does not fit the selected encoding");
                goto done;
            }
        }
    }

    image[0] = 0x7fu; image[1] = 'E'; image[2] = 'L'; image[3] = 'F';
    image[4] = 2u; image[5] = 1u; image[6] = 1u;
    w16(image + 16u, ET_EXEC);
    w16(image + 18u, EM_X86_64);
    w32(image + 20u, 1u);
    w64(image + 24u, entry);
    w64(image + 32u, EHDR);
    w64(image + 40u, 0u);
    w16(image + 52u, EHDR);
    w16(image + 54u, PHDR);
    w16(image + 56u, (uint16_t)phnum);

    uint8_t *ph = image + EHDR;
    w32(ph, PT_LOAD); w32(ph + 4u, PF_R);
    w64(ph + 8u, 0u); w64(ph + 16u, image_base);
    w64(ph + 24u, image_base); w64(ph + 32u, header_bytes);
    w64(ph + 40u, header_bytes); w64(ph + 48u, page_size);

    uint32_t ph_index = 1u;
    for (uint32_t i = 0u; i < section_count; ++i) {
        Section *s = &sections[i];
        if ((s->flags & SHF_ALLOC) == 0u || s->size == 0u) continue;
        uint32_t flags = PF_R;
        if ((s->flags & SHF_WRITE) != 0u) flags |= PF_W;
        if ((s->flags & SHF_EXECINSTR) != 0u) flags |= PF_X;
        ph = image + EHDR + (size_t)ph_index * PHDR;
        w32(ph, PT_LOAD); w32(ph + 4u, flags);
        w64(ph + 8u, s->type == SHT_NOBITS ? file_size : s->image_offset);
        w64(ph + 16u, s->address);
        w64(ph + 24u, s->address);
        w64(ph + 32u, s->type == SHT_NOBITS ? 0u : s->size);
        w64(ph + 40u, s->size);
        w64(ph + 48u, s->type == SHT_NOBITS ? 1u : page_size);
        ph_index++;
    }

    output->data = image;
    output->size = file_size;
    image = NULL;

done:
    free(image);
    free(symbols);
    free(sections);
    return status;
}
