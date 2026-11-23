#include "reaper/elf64_linker.h"
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BASE_ADDR UINT64_C(0x400000)
#define PAGE_SIZE UINT64_C(4096)
#define ELF_HEADER_SIZE 64u
#define PHDR_SIZE 56u
#define PHDR_COUNT 4u
#define MAX_OBJECTS 256u
#define MAX_SECTIONS 4096u

typedef struct { uint8_t *data; size_t size; size_t capacity; } Buffer;
typedef struct { uint64_t *offsets; int32_t *groups; uint32_t count; } Layout;
typedef struct { const ReaperElf64Symbol *symbol; uint32_t object; uint32_t index; } FoundSymbol;

static ReaperElf64Status fail(ReaperElf64Error *error, uint32_t index,
                              ReaperElf64Status status, const char *message) {
    if (error != NULL) {
        error->item_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}
static int add64(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return 0;
    *out = a + b; return 1;
}
static int align64(uint64_t value, uint64_t alignment, uint64_t *out) {
    uint64_t mask;
    if (alignment == 0u || (alignment & (alignment - 1u)) != 0u) return 0;
    mask = alignment - 1u;
    if (value > UINT64_MAX - mask) return 0;
    *out = (value + mask) & ~mask; return 1;
}
static int reserve(Buffer *buffer, size_t required) {
    size_t next;
    uint8_t *memory;
    if (required <= buffer->capacity) return 1;
    next = buffer->capacity == 0u ? 256u : buffer->capacity;
    while (next < required) {
        if (next > SIZE_MAX / 2u) { next = required; break; }
        next *= 2u;
    }
    memory = (uint8_t *)realloc(buffer->data, next);
    if (memory == NULL) return 0;
    buffer->data = memory; buffer->capacity = next; return 1;
}
static int append(Buffer *buffer, const uint8_t *data, size_t size) {
    if (size > SIZE_MAX - buffer->size || (size != 0u && data == NULL)) return 0;
    if (!reserve(buffer, buffer->size + size)) return 0;
    if (size != 0u) memcpy(buffer->data + buffer->size, data, size);
    buffer->size += size; return 1;
}
static void put16(uint8_t *p, uint16_t x) {
    p[0] = (uint8_t)x; p[1] = (uint8_t)(x >> 8u);
}
static void put32(uint8_t *p, uint32_t x) {
    for (unsigned i = 0u; i < 4u; ++i) p[i] = (uint8_t)(x >> (i * 8u));
}
static void put64(uint8_t *p, uint64_t x) {
    for (unsigned i = 0u; i < 8u; ++i) p[i] = (uint8_t)(x >> (i * 8u));
}
static int add_signed(uint64_t value, int64_t addend, uint64_t *out) {
    if (addend >= 0) return add64(value, (uint64_t)addend, out);
    uint64_t magnitude = (uint64_t)(-(addend + 1)) + 1u;
    if (value < magnitude) return 0;
    *out = value - magnitude; return 1;
}
static int group_for(const char *name) {
    if (name == NULL) return -1;
    if (strcmp(name, ".text") == 0) return 0;
    if (strcmp(name, ".rodata") == 0) return 1;
    if (strcmp(name, ".data") == 0) return 2;
    if (strcmp(name, ".bss") == 0) return 3;
    return -1;
}
static void free_layouts(Layout *layouts, uint32_t count) {
    if (layouts == NULL) return;
    for (uint32_t i = 0u; i < count; ++i) { free(layouts[i].offsets); free(layouts[i].groups); }
    free(layouts);
}
static ReaperElf64Status find_global(
    const ReaperElf64Object *objects, uint32_t count, const char *name,
    FoundSymbol *result, ReaperElf64Error *error
) {
    const ReaperElf64Symbol *strong = NULL, *weak = NULL;
    uint32_t so = 0u, si = 0u, wo = 0u, wi = 0u;
    for (uint32_t oi = 0u; oi < count; ++oi) {
        for (uint32_t j = 0u; j < objects[oi].symbol_count; ++j) {
            const ReaperElf64Symbol *s = &objects[oi].symbols[j];
            if (s->name == NULL || strcmp(s->name, name) != 0 ||
                s->section_index == REAPER_ELF64_NO_SECTION ||
                s->binding == REAPER_ELF64_STB_LOCAL) continue;
            if (s->binding == REAPER_ELF64_STB_GLOBAL) {
                if (strong != NULL) return fail(error, j, REAPER_ELF64_DUPLICATE_SYMBOL,
                                                 "multiple strong definitions for global symbol");
                strong = s; so = oi; si = j;
            } else if (s->binding == REAPER_ELF64_STB_WEAK && weak == NULL) {
                weak = s; wo = oi; wi = j;
            }
        }
    }
    if (strong != NULL) { result->symbol = strong; result->object = so; result->index = si; return REAPER_ELF64_OK; }
    if (weak != NULL) { result->symbol = weak; result->object = wo; result->index = wi; return REAPER_ELF64_OK; }
    return fail(error, 0u, REAPER_ELF64_UNRESOLVED_SYMBOL, "unresolved external symbol");
}
static ReaperElf64Status symbol_address(
    const ReaperElf64Object *objects, uint32_t object_count, const Layout *layouts,
    const uint64_t group_va[4], uint32_t source_object, uint32_t symbol_index,
    uint64_t *address, ReaperElf64Error *error
) {
    const ReaperElf64Object *source = &objects[source_object];
    if (symbol_index >= source->symbol_count)
        return fail(error, symbol_index, REAPER_ELF64_RANGE_ERROR, "symbol index out of range");
    const ReaperElf64Symbol *symbol = &source->symbols[symbol_index];
    FoundSymbol found;
    const ReaperElf64Symbol *selected = symbol;
    uint32_t owner = source_object, selected_index = symbol_index;
    if (symbol->section_index == REAPER_ELF64_NO_SECTION ||
        symbol->binding != REAPER_ELF64_STB_LOCAL) {
        if (symbol->binding == REAPER_ELF64_STB_LOCAL)
            return fail(error, symbol_index, REAPER_ELF64_UNRESOLVED_SYMBOL, "undefined local symbol");
        ReaperElf64Status status = find_global(objects, object_count, symbol->name, &found, error);
        if (status != REAPER_ELF64_OK) return status;
        selected = found.symbol; owner = found.object; selected_index = found.index;
    }
    if (selected->section_index == REAPER_ELF64_ABSOLUTE_SECTION) {
        *address = selected->value; return REAPER_ELF64_OK;
    }
    if (selected->section_index == REAPER_ELF64_NO_SECTION ||
        selected->section_index >= layouts[owner].count)
        return fail(error, selected_index, REAPER_ELF64_RANGE_ERROR, "resolved symbol section invalid");
    int32_t group = layouts[owner].groups[selected->section_index];
    uint64_t base;
    if (group < 0 || group > 3 ||
        !add64(group_va[(uint32_t)group], layouts[owner].offsets[selected->section_index], &base) ||
        !add64(base, selected->value, address))
        return fail(error, selected_index, REAPER_ELF64_RANGE_ERROR, "resolved symbol address invalid");
    return REAPER_ELF64_OK;
}
static ReaperElf64Status relocate(
    uint8_t *field, uint64_t place, uint64_t symbol, uint32_t type, int64_t addend,
    ReaperElf64Error *error, uint32_t index
) {
    uint64_t absolute;
    if (!add_signed(symbol, addend, &absolute))
        return fail(error, index, REAPER_ELF64_RANGE_ERROR, "relocation addition overflow");
    switch (type) {
    case REAPER_ELF64_R_X86_64_64:
        put64(field, absolute); return REAPER_ELF64_OK;
    case REAPER_ELF64_R_X86_64_PC32:
    case REAPER_ELF64_R_X86_64_PLT32: {
        int64_t delta;
        if (absolute >= place) {
            uint64_t d = absolute - place;
            if (d > (uint64_t)INT32_MAX)
                return fail(error, index, REAPER_ELF64_RANGE_ERROR, "PC32 relocation overflow");
            delta = (int64_t)d;
        } else {
            uint64_t d = place - absolute;
            if (d > (uint64_t)INT32_MAX + 1u)
                return fail(error, index, REAPER_ELF64_RANGE_ERROR, "PC32 relocation overflow");
            delta = -(int64_t)d;
        }
        put32(field, (uint32_t)(int32_t)delta); return REAPER_ELF64_OK;
    }
    case REAPER_ELF64_R_X86_64_32:
        if (absolute > UINT32_MAX) return fail(error, index, REAPER_ELF64_RANGE_ERROR, "R_X86_64_32 overflow");
        put32(field, (uint32_t)absolute); return REAPER_ELF64_OK;
    case REAPER_ELF64_R_X86_64_32S:
        if (absolute > (uint64_t)INT32_MAX) return fail(error, index, REAPER_ELF64_RANGE_ERROR, "R_X86_64_32S overflow");
        put32(field, (uint32_t)(int32_t)absolute); return REAPER_ELF64_OK;
    default:
        return fail(error, index, REAPER_ELF64_UNSUPPORTED, "unsupported relocation type");
    }
}
static int write_phdr(
    uint8_t *file, uint64_t file_size, uint32_t index, uint32_t flags,
    uint64_t offset, uint64_t address, uint64_t filesz, uint64_t memsz
) {
    uint64_t p = 64u + (uint64_t)index * 56u;
    if (p > file_size || 56u > file_size - p || offset > file_size || filesz > file_size - offset) return 0;
    put32(file + p, 1u); put32(file + p + 4u, flags);
    put64(file + p + 8u, offset); put64(file + p + 16u, address);
    put64(file + p + 24u, address); put64(file + p + 32u, filesz);
    put64(file + p + 40u, memsz); put64(file + p + 48u, PAGE_SIZE);
    return 1;
}
void reaper_elf64_executable_destroy(ReaperElf64Executable *image) {
    if (image == NULL) return;
    free(image->data); memset(image, 0, sizeof *image);
}

ReaperElf64Status reaper_elf64_link_executable(
    const ReaperElf64Object *objects, uint32_t object_count, const char *entry_symbol,
    ReaperElf64Executable *output, ReaperElf64Error *error
) {
    Buffer groups[3] = {{0}};
    Layout *layouts = NULL;
    uint64_t bss_size = 0u, header_end = 64u + 4u * 56u;
    uint64_t text_off, rodata_off, data_off, file_size, entry = 0u;
    uint64_t group_va[4] = {0u, 0u, 0u, 0u};
    uint8_t *file = NULL;
    ReaperElf64Status status = REAPER_ELF64_OK;

    if (output == NULL || objects == NULL || object_count == 0u ||
        object_count > MAX_OBJECTS || entry_symbol == NULL || entry_symbol[0] == '\0')
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT, "invalid linker arguments");
    memset(output, 0, sizeof *output);
    layouts = (Layout *)calloc(object_count, sizeof *layouts);
    if (layouts == NULL) return fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY, "layout allocation failed");

    for (uint32_t oi = 0u; oi < object_count; ++oi) {
        const ReaperElf64Object *object = &objects[oi];
        if ((object->section_count && object->sections == NULL) ||
            (object->symbol_count && object->symbols == NULL) ||
            (object->relocation_count && object->relocations == NULL) ||
            object->section_count > MAX_SECTIONS) {
            status = fail(error, oi, REAPER_ELF64_INVALID_ARGUMENT, "malformed object tables"); goto done;
        }
        Layout *layout = &layouts[oi];
        layout->count = object->section_count;
        size_t slots = object->section_count ? object->section_count : 1u;
        layout->offsets = (uint64_t *)calloc(slots, sizeof(uint64_t));
        layout->groups = (int32_t *)malloc(slots * sizeof(int32_t));
        if (layout->offsets == NULL || layout->groups == NULL) {
            status = fail(error, oi, REAPER_ELF64_OUT_OF_MEMORY, "section map allocation failed"); goto done;
        }
        for (uint32_t si = 0u; si < object->section_count; ++si) {
            const ReaperElf64Section *section = &object->sections[si];
            int group = group_for(section->name);
            layout->groups[si] = group;
            if (group < 0) { status = fail(error, si, REAPER_ELF64_UNSUPPORTED, "only .text/.rodata/.data/.bss supported"); goto done; }
            if (section->alignment == 0u || (section->alignment & (section->alignment - 1u)) != 0u) {
                status = fail(error, si, REAPER_ELF64_INVALID_ARGUMENT, "invalid section alignment"); goto done;
            }
            if (group == 3) {
                if (section->type != REAPER_ELF64_SHT_NOBITS ||
                    !align64(bss_size, section->alignment, &layout->offsets[si]) ||
                    !add64(layout->offsets[si], section->size, &bss_size)) {
                    status = fail(error, si, REAPER_ELF64_RANGE_ERROR, "invalid or oversized .bss"); goto done;
                }
                continue;
            }
            Buffer *dest = &groups[group];
            uint64_t aligned;
            if (section->type != REAPER_ELF64_SHT_PROGBITS ||
                (section->size && section->data == NULL) ||
                !align64((uint64_t)dest->size, section->alignment, &aligned) || aligned > SIZE_MAX) {
                status = fail(error, si, REAPER_ELF64_INVALID_ARGUMENT, "invalid PROGBITS section"); goto done;
            }
            if (aligned > dest->size) {
                size_t padding = (size_t)(aligned - dest->size);
                if (padding > SIZE_MAX - dest->size || !reserve(dest, dest->size + padding)) {
                    status = fail(error, si, REAPER_ELF64_OUT_OF_MEMORY, "section alignment failed"); goto done;
                }
                memset(dest->data + dest->size, 0, padding); dest->size += padding;
            }
            layout->offsets[si] = (uint64_t)dest->size;
            if (!append(dest, section->data, (size_t)section->size)) {
                status = fail(error, si, REAPER_ELF64_OUT_OF_MEMORY, "section append failed"); goto done;
            }
        }
    }

    if (!align64(header_end, PAGE_SIZE, &text_off) ||
        !add64(text_off, (uint64_t)groups[0].size, &rodata_off) ||
        !align64(rodata_off, PAGE_SIZE, &rodata_off) ||
        !add64(rodata_off, (uint64_t)groups[1].size, &data_off) ||
        !align64(data_off, PAGE_SIZE, &data_off) ||
        !add64(data_off, (uint64_t)groups[2].size, &file_size) || file_size > SIZE_MAX ||
        bss_size > UINT64_MAX - (uint64_t)groups[2].size) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR, "output image size overflow"); goto done;
    }
    if (!add64(BASE_ADDR, text_off, &group_va[0]) ||
        !add64(BASE_ADDR, rodata_off, &group_va[1]) ||
        !add64(BASE_ADDR, data_off, &group_va[2]) ||
        !add64(group_va[2], (uint64_t)groups[2].size, &group_va[3])) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR, "virtual address overflow"); goto done;
    }

    {
        FoundSymbol start;
        status = find_global(objects, object_count, entry_symbol, &start, error);
        if (status != REAPER_ELF64_OK) { status = fail(error, 0u, REAPER_ELF64_INVALID_ENTRY, "entry symbol is not globally defined"); goto done; }
        status = symbol_address(objects, object_count, layouts, group_va,
                                start.object, start.index, &entry, error);
        if (status != REAPER_ELF64_OK) goto done;
        uint32_t sec = start.symbol->section_index;
        if (sec >= layouts[start.object].count || layouts[start.object].groups[sec] != 0 ||
            entry < group_va[0] || entry >= group_va[0] + (uint64_t)groups[0].size) {
            status = fail(error, start.index, REAPER_ELF64_INVALID_ENTRY, "entry must reside in .text"); goto done;
        }
    }

    for (uint32_t oi = 0u; oi < object_count; ++oi) {
        const ReaperElf64Object *object = &objects[oi];
        for (uint32_t ri = 0u; ri < object->relocation_count; ++ri) {
            const ReaperElf64Relocation *rel = &object->relocations[ri];
            uint32_t target = rel->target_section;
            if (target >= object->section_count) { status = fail(error, ri, REAPER_ELF64_RANGE_ERROR, "relocation target out of range"); goto done; }
            int32_t group = layouts[oi].groups[target];
            if (group < 0 || group == 3) { status = fail(error, ri, REAPER_ELF64_UNSUPPORTED, "relocation into unsupported section"); goto done; }
            uint32_t width = rel->type == REAPER_ELF64_R_X86_64_64 ? 8u :
                (rel->type == REAPER_ELF64_R_X86_64_PC32 || rel->type == REAPER_ELF64_R_X86_64_PLT32 ||
                 rel->type == REAPER_ELF64_R_X86_64_32 || rel->type == REAPER_ELF64_R_X86_64_32S) ? 4u : 0u;
            if (width == 0u) { status = fail(error, ri, REAPER_ELF64_UNSUPPORTED, "unsupported relocation"); goto done; }
            const ReaperElf64Section *input = &object->sections[target];
            if (rel->offset > input->size || width > input->size - rel->offset) {
                status = fail(error, ri, REAPER_ELF64_RANGE_ERROR, "relocation outside input section"); goto done;
            }
            Buffer *dest = &groups[(uint32_t)group];
            uint64_t section_offset = layouts[oi].offsets[target];
            if (section_offset > dest->size || rel->offset + width > dest->size - section_offset) {
                status = fail(error, ri, REAPER_ELF64_RANGE_ERROR, "relocation outside merged section"); goto done;
            }
            uint64_t place, symbol;
            if (!add64(group_va[(uint32_t)group], section_offset + rel->offset, &place)) {
                status = fail(error, ri, REAPER_ELF64_RANGE_ERROR, "relocation place overflow"); goto done;
            }
            status = symbol_address(objects, object_count, layouts, group_va, oi, rel->symbol_index, &symbol, error);
            if (status != REAPER_ELF64_OK) goto done;
            status = relocate(dest->data + (size_t)(section_offset + rel->offset),
                              place, symbol, rel->type, rel->addend, error, ri);
            if (status != REAPER_ELF64_OK) goto done;
        }
    }

    file = (uint8_t *)calloc(1u, (size_t)file_size);
    if (file == NULL) { status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY, "image allocation failed"); goto done; }
    file[0] = 0x7fu; file[1] = 'E'; file[2] = 'L'; file[3] = 'F';
    file[4] = 2u; file[5] = 1u; file[6] = 1u;
    put16(file + 16u, 2u); put16(file + 18u, 62u); put32(file + 20u, 1u);
    put64(file + 24u, entry); put64(file + 32u, ELF_HEADER_SIZE);
    put16(file + 52u, ELF_HEADER_SIZE); put16(file + 54u, PHDR_SIZE);
    put16(file + 56u, PHDR_COUNT);
    if (!write_phdr(file, file_size, 0u, 4u, 0u, BASE_ADDR, header_end, header_end) ||
        !write_phdr(file, file_size, 1u, 5u, text_off, group_va[0], (uint64_t)groups[0].size, (uint64_t)groups[0].size) ||
        !write_phdr(file, file_size, 2u, 4u, rodata_off, group_va[1], (uint64_t)groups[1].size, (uint64_t)groups[1].size) ||
        !write_phdr(file, file_size, 3u, 6u, data_off, group_va[2], (uint64_t)groups[2].size,
                    (uint64_t)groups[2].size + bss_size)) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR, "program header serialization failed"); goto done;
    }
    if (groups[0].size) memcpy(file + (size_t)text_off, groups[0].data, groups[0].size);
    if (groups[1].size) memcpy(file + (size_t)rodata_off, groups[1].data, groups[1].size);
    if (groups[2].size) memcpy(file + (size_t)data_off, groups[2].data, groups[2].size);
    output->data = file; output->size = file_size; output->entry_address = entry; file = NULL;

done:
    free(file);
    free(groups[0].data); free(groups[1].data); free(groups[2].data);
    free_layouts(layouts, object_count);
    return status;
}
