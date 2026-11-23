#include "reaper/elf64.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ELF64_EHDR_SIZE 64u
#define ELF64_SHDR_SIZE 64u
#define ELF64_SYM_SIZE 24u
#define ELF64_RELA_SIZE 24u
#define ELF64_SHN_LORESERVE 0xff00u
#define ELF64_ET_REL 1u
#define ELF64_EM_X86_64 62u
#define ELF64_EV_CURRENT 1u
#define ELF64_SHT_NULL 0u
#define ELF64_SHT_SYMTAB 2u
#define ELF64_SHT_STRTAB 3u
#define ELF64_SHT_RELA 4u
#define ELF64_STT_SECTION 3u

typedef struct {
    uint8_t *data;
    size_t length;
    size_t capacity;
} ByteBuffer;

typedef struct {
    const char *name;
    uint32_t type;
    uint64_t flags;
    uint64_t offset;
    uint64_t size;
    uint64_t alignment;
    uint64_t entry_size;
    uint32_t link;
    uint32_t info;
    const uint8_t *data;
    uint32_t name_offset;
} OutputSection;

static ReaperElf64Status fail(ReaperElf64Error *error, uint32_t index,
                              ReaperElf64Status status, const char *message) {
    if (error != NULL) {
        error->item_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}

static int checked_add_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (left > UINT64_MAX - right) return 0;
    *result = left + right;
    return 1;
}

static int checked_align_u64(uint64_t value, uint64_t alignment, uint64_t *result) {
    uint64_t mask;
    if (alignment <= 1u) {
        *result = value;
        return 1;
    }
    if ((alignment & (alignment - 1u)) != 0u) return 0;
    mask = alignment - 1u;
    if (value > UINT64_MAX - mask) return 0;
    *result = (value + mask) & ~mask;
    return 1;
}

static int buffer_reserve(ByteBuffer *buffer, size_t extra) {
    size_t required;
    size_t next;
    uint8_t *data;
    if (extra > SIZE_MAX - buffer->length) return 0;
    required = buffer->length + extra;
    if (required <= buffer->capacity) return 1;
    next = buffer->capacity == 0u ? 64u : buffer->capacity;
    while (next < required) {
        if (next > SIZE_MAX / 2u) {
            next = required;
            break;
        }
        next *= 2u;
    }
    data = (uint8_t *)realloc(buffer->data, next);
    if (data == NULL) return 0;
    buffer->data = data;
    buffer->capacity = next;
    return 1;
}

static int buffer_append(ByteBuffer *buffer, const void *data, size_t size) {
    if (size != 0u && data == NULL) return 0;
    if (!buffer_reserve(buffer, size)) return 0;
    if (size != 0u) memcpy(buffer->data + buffer->length, data, size);
    buffer->length += size;
    return 1;
}

static int buffer_zero(ByteBuffer *buffer, size_t size) {
    if (!buffer_reserve(buffer, size)) return 0;
    if (size != 0u) memset(buffer->data + buffer->length, 0, size);
    buffer->length += size;
    return 1;
}

static int string_table_add(ByteBuffer *table, const char *value, uint32_t *offset) {
    size_t length;
    if (value == NULL || offset == NULL) return 0;
    length = strlen(value);
    if (length > UINT32_MAX || table->length > UINT32_MAX ||
        length + 1u > UINT32_MAX - table->length) return 0;
    *offset = (uint32_t)table->length;
    return buffer_append(table, value, length + 1u);
}

static void put16(uint8_t *out, uint16_t value) {
    out[0] = (uint8_t)(value & 0xffu);
    out[1] = (uint8_t)((value >> 8u) & 0xffu);
}

static void put32(uint8_t *out, uint32_t value) {
    for (unsigned i = 0u; i < 4u; ++i)
        out[i] = (uint8_t)((value >> (i * 8u)) & 0xffu);
}

static void put64(uint8_t *out, uint64_t value) {
    for (unsigned i = 0u; i < 8u; ++i)
        out[i] = (uint8_t)((value >> (i * 8u)) & 0xffu);
}

static int valid_relocation_width(uint32_t type, uint64_t *width) {
    switch (type) {
    case REAPER_ELF64_R_X86_64_64:
        *width = 8u;
        return 1;
    case REAPER_ELF64_R_X86_64_PC32:
    case REAPER_ELF64_R_X86_64_PLT32:
    case REAPER_ELF64_R_X86_64_32:
    case REAPER_ELF64_R_X86_64_32S:
        *width = 4u;
        return 1;
    default:
        return 0;
    }
}

static void write_symbol(uint8_t *out, uint32_t name, uint8_t info,
                         uint8_t other, uint16_t section, uint64_t value,
                         uint64_t size) {
    put32(out, name);
    out[4] = info;
    out[5] = other;
    put16(out + 6u, section);
    put64(out + 8u, value);
    put64(out + 16u, size);
}

static void write_relocation(uint8_t *out, uint64_t offset,
                             uint32_t symbol, uint32_t type, int64_t addend) {
    uint64_t info = ((uint64_t)symbol << 32u) | (uint64_t)type;
    put64(out, offset);
    put64(out + 8u, info);
    put64(out + 16u, (uint64_t)addend);
}

static void write_section_header(uint8_t *out, const OutputSection *section) {
    put32(out, section->name_offset);
    put32(out + 4u, section->type);
    put64(out + 8u, section->flags);
    put64(out + 16u, 0u);
    put64(out + 24u, section->offset);
    put64(out + 32u, section->size);
    put32(out + 40u, section->link);
    put32(out + 44u, section->info);
    put64(out + 48u, section->alignment);
    put64(out + 56u, section->entry_size);
}

static void cleanup(ByteBuffer *symbol_names, ByteBuffer *symbol_table,
                    ByteBuffer *string_table, ByteBuffer *section_names,
                    OutputSection *sections, ByteBuffer *relocations,
                    uint32_t relocation_section_count, uint32_t *symbol_map,
                    uint32_t *symbol_name_offsets, uint32_t *relocation_counts) {
    if (symbol_names != NULL) free(symbol_names->data);
    if (symbol_table != NULL) free(symbol_table->data);
    if (string_table != NULL) free(string_table->data);
    if (section_names != NULL) free(section_names->data);
    if (relocations != NULL) {
        for (uint32_t i = 0u; i < relocation_section_count; ++i)
            free(relocations[i].data);
    }
    free(relocations);
    free(sections);
    free(symbol_map);
    free(symbol_name_offsets);
    free(relocation_counts);
}

ReaperElf64Status reaper_elf64_write_object(
    const ReaperElf64Object *object,
    ReaperElf64Buffer *output,
    ReaperElf64Error *error
) {
    ByteBuffer symbol_table = {0};
    ByteBuffer string_table = {0};
    ByteBuffer section_names = {0};
    ByteBuffer *relocation_data = NULL;
    OutputSection *sections = NULL;
    uint32_t *symbol_map = NULL;
    uint32_t *symbol_name_offsets = NULL;
    uint32_t *relocation_counts = NULL;
    uint32_t relocation_section_count = 0u;
    uint32_t symbol_section_index = 0u;
    uint32_t string_section_index = 0u;
    uint32_t section_name_index = 0u;
    uint32_t first_global_symbol = 0u;
    uint32_t output_section_count = 0u;
    uint64_t cursor = 0u;
    uint64_t section_header_offset = 0u;
    uint64_t file_size = 0u;
    uint8_t *file = NULL;
    ReaperElf64Status status = REAPER_ELF64_OK;

    if (error != NULL) {
        error->item_index = 0u;
        error->message[0] = '\0';
    }
    if (output != NULL) {
        output->data = NULL;
        output->size = 0u;
    }
    if (object == NULL || output == NULL ||
        (object->section_count != 0u && object->sections == NULL) ||
        (object->symbol_count != 0u && object->symbols == NULL) ||
        (object->relocation_count != 0u && object->relocations == NULL))
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "object, output and declared arrays are required");

    if (object->section_count >= ELF64_SHN_LORESERVE ||
        object->symbol_count > UINT32_MAX / (uint32_t)ELF64_SYM_SIZE ||
        object->relocation_count > UINT32_MAX / (uint32_t)ELF64_RELA_SIZE)
        return fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                    "object exceeds the ELF64 section or table limits");

    if (object->section_count != 0u) {
        relocation_counts = (uint32_t *)calloc(object->section_count, sizeof *relocation_counts);
        if (relocation_counts == NULL)
            return fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY, "cannot allocate relocation index");
    }
    for (uint32_t i = 0u; i < object->section_count; ++i) {
        const ReaperElf64Section *section = &object->sections[i];
        if (section->name == NULL || section->name[0] == '\0' ||
            (section->type != REAPER_ELF64_SHT_PROGBITS &&
             section->type != REAPER_ELF64_SHT_NOBITS) ||
            (section->type == REAPER_ELF64_SHT_PROGBITS &&
             section->size != 0u && section->data == NULL) ||
            (section->alignment > 1u &&
             (section->alignment & (section->alignment - 1u)) != 0u) ||
            section->size > (uint64_t)SIZE_MAX) {
            status = fail(error, i, REAPER_ELF64_INVALID_ARGUMENT,
                          "invalid section name, type, storage, size or alignment");
            goto done;
        }
    }
    for (uint32_t i = 0u; i < object->symbol_count; ++i) {
        const ReaperElf64Symbol *symbol = &object->symbols[i];
        if (symbol->name == NULL ||
            (symbol->binding != REAPER_ELF64_STB_LOCAL &&
             symbol->binding != REAPER_ELF64_STB_GLOBAL &&
             symbol->binding != REAPER_ELF64_STB_WEAK) ||
            symbol->type > REAPER_ELF64_STT_FUNC ||
            symbol->visibility > 3u) {
            status = fail(error, i, REAPER_ELF64_INVALID_ARGUMENT,
                          "invalid symbol name, binding, type or visibility");
            goto done;
        }
        if (symbol->section_index != REAPER_ELF64_NO_SECTION &&
            symbol->section_index != REAPER_ELF64_ABSOLUTE_SECTION) {
            if (symbol->section_index >= object->section_count ||
                symbol->value > object->sections[symbol->section_index].size) {
                status = fail(error, i, REAPER_ELF64_RANGE_ERROR,
                              "symbol section or value is outside the object");
                goto done;
            }
        }
    }
    for (uint32_t i = 0u; i < object->relocation_count; ++i) {
        const ReaperElf64Relocation *relocation = &object->relocations[i];
        uint64_t width = 0u;
        uint64_t end = 0u;
        if (relocation->target_section >= object->section_count ||
            relocation->symbol_index >= object->symbol_count ||
            !valid_relocation_width(relocation->type, &width)) {
            status = fail(error, i, REAPER_ELF64_UNSUPPORTED,
                          "relocation target, symbol or x86-64 type is unsupported");
            goto done;
        }
        const ReaperElf64Section *target = &object->sections[relocation->target_section];
        if (target->type != REAPER_ELF64_SHT_PROGBITS ||
            !checked_add_u64(relocation->offset, width, &end) || end > target->size) {
            status = fail(error, i, REAPER_ELF64_RANGE_ERROR,
                          "relocation field falls outside its PROGBITS target section");
            goto done;
        }
        if (relocation_counts[relocation->target_section] == UINT32_MAX) {
            status = fail(error, i, REAPER_ELF64_RANGE_ERROR,
                          "too many relocations in one section");
            goto done;
        }
        relocation_counts[relocation->target_section]++;
    }
    for (uint32_t i = 0u; i < object->section_count; ++i)
        if (relocation_counts[i] != 0u) relocation_section_count++;

    output_section_count = 1u + object->section_count + 3u + relocation_section_count;
    section_name_index = output_section_count - 1u;
    if (output_section_count >= ELF64_SHN_LORESERVE) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                      "too many output sections for the non-extended ELF64 format");
        goto done;
    }

    sections = (OutputSection *)calloc(output_section_count, sizeof *sections);
    if (sections == NULL) {
        status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY, "cannot allocate output section table");
        goto done;
    }
    relocation_data = (ByteBuffer *)calloc(relocation_section_count,
                                            sizeof *relocation_data);
    if (relocation_section_count != 0u && relocation_data == NULL) {
        status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                      "cannot allocate relocation buffers");
        goto done;
    }

    for (uint32_t i = 0u; i < object->section_count; ++i) {
        OutputSection *target = &sections[1u + i];
        const ReaperElf64Section *source = &object->sections[i];
        target->name = source->name;
        target->type = source->type;
        target->flags = source->flags;
        target->size = source->size;
        target->alignment = source->alignment == 0u ? 1u : source->alignment;
        target->entry_size = source->entry_size;
        target->data = source->type == REAPER_ELF64_SHT_NOBITS ? NULL : source->data;
    }

    if (!buffer_zero(&symbol_table, ELF64_SYM_SIZE) ||
        !buffer_zero(&string_table, 1u) ||
        !buffer_zero(&section_names, 1u)) {
        status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                      "cannot initialize ELF string or symbol tables");
        goto done;
    }

    if (object->symbol_count != 0u) {
        symbol_map = (uint32_t *)calloc(object->symbol_count, sizeof *symbol_map);
        symbol_name_offsets = (uint32_t *)calloc(object->symbol_count,
                                                   sizeof *symbol_name_offsets);
        if (symbol_map == NULL || symbol_name_offsets == NULL) {
            status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                          "cannot allocate symbol index maps");
            goto done;
        }
    }

    for (uint32_t pass = 0u; pass < 2u; ++pass) {
        uint8_t *entry;
        for (uint32_t i = 0u; i < object->section_count; ++i) {
            if (pass == 0u) {
                if (!buffer_zero(&symbol_table, ELF64_SYM_SIZE)) {
                    status = fail(error, i, REAPER_ELF64_OUT_OF_MEMORY,
                                  "cannot append section symbol");
                    goto done;
                }
                entry = symbol_table.data + symbol_table.length - ELF64_SYM_SIZE;
                write_symbol(entry, 0u, (uint8_t)ELF64_STT_SECTION, 0u,
                             (uint16_t)(i + 1u), 0u, 0u);
            }
        }
        if (pass == 0u) first_global_symbol = (uint32_t)(symbol_table.length / ELF64_SYM_SIZE);
        for (uint32_t i = 0u; i < object->symbol_count; ++i) {
            const ReaperElf64Symbol *symbol = &object->symbols[i];
            int is_local = symbol->binding == REAPER_ELF64_STB_LOCAL;
            if ((pass == 0u) != is_local) continue;
            uint16_t section_index = 0u;
            if (symbol->section_index == REAPER_ELF64_ABSOLUTE_SECTION) {
                section_index = (uint16_t)REAPER_ELF64_ABSOLUTE_SECTION;
            } else if (symbol->section_index != REAPER_ELF64_NO_SECTION) {
                section_index = (uint16_t)(symbol->section_index + 1u);
            }
            if (!string_table_add(&string_table, symbol->name,
                                  &symbol_name_offsets[i]) ||
                !buffer_zero(&symbol_table, ELF64_SYM_SIZE)) {
                status = fail(error, i, REAPER_ELF64_OUT_OF_MEMORY,
                              "cannot append symbol or string data");
                goto done;
            }
            symbol_map[i] = (uint32_t)(symbol_table.length / ELF64_SYM_SIZE - 1u);
            entry = symbol_table.data + symbol_table.length - ELF64_SYM_SIZE;
            write_symbol(entry, symbol_name_offsets[i],
                         (uint8_t)((symbol->binding << 4u) | symbol->type),
                         symbol->visibility, section_index, symbol->value, symbol->size);
        }
    }

    symbol_section_index = 1u + object->section_count;
    string_section_index = symbol_section_index + 1u;
    sections[symbol_section_index].name = ".symtab";
    sections[symbol_section_index].type = ELF64_SHT_SYMTAB;
    sections[symbol_section_index].alignment = 8u;
    sections[symbol_section_index].entry_size = ELF64_SYM_SIZE;
    sections[symbol_section_index].link = string_section_index;
    sections[symbol_section_index].info = first_global_symbol;
    sections[symbol_section_index].data = symbol_table.data;
    sections[symbol_section_index].size = (uint64_t)symbol_table.length;

    sections[string_section_index].name = ".strtab";
    sections[string_section_index].type = ELF64_SHT_STRTAB;
    sections[string_section_index].alignment = 1u;
    sections[string_section_index].data = string_table.data;
    sections[string_section_index].size = (uint64_t)string_table.length;

    uint32_t relocation_output_index = string_section_index + 1u;
    uint32_t relocation_buffer_index = 0u;
    for (uint32_t target = 0u; target < object->section_count; ++target) {
        if (relocation_counts[target] == 0u) continue;
        ByteBuffer *buffer = &relocation_data[relocation_buffer_index];
        uint64_t bytes_needed = (uint64_t)relocation_counts[target] * ELF64_RELA_SIZE;
        if (bytes_needed > (uint64_t)SIZE_MAX ||
            !buffer_zero(buffer, (size_t)bytes_needed)) {
            status = fail(error, target, REAPER_ELF64_OUT_OF_MEMORY,
                          "cannot allocate relocation entries");
            goto done;
        }
        uint32_t slot = 0u;
        for (uint32_t i = 0u; i < object->relocation_count; ++i) {
            const ReaperElf64Relocation *relocation = &object->relocations[i];
            if (relocation->target_section != target) continue;
            write_relocation(buffer->data + (size_t)slot * ELF64_RELA_SIZE,
                             relocation->offset, symbol_map[relocation->symbol_index],
                             relocation->type, relocation->addend);
            slot++;
        }
        char *rela_name;
        const char *target_name = object->sections[target].name;
        if (target_name[0] == '.') target_name++;
        size_t name_length = strlen(target_name);
        if (name_length > SIZE_MAX - sizeof ".rela.") {
            status = fail(error, target, REAPER_ELF64_RANGE_ERROR,
                          "relocation section name is too long");
            goto done;
        }
        rela_name = (char *)malloc(sizeof ".rela." + name_length);
        if (rela_name == NULL) {
            status = fail(error, target, REAPER_ELF64_OUT_OF_MEMORY,
                          "cannot allocate relocation section name");
            goto done;
        }
        (void)snprintf(rela_name, sizeof ".rela." + name_length,
                       ".rela.%s", target_name);
        OutputSection *rela = &sections[relocation_output_index++];
        rela->name = rela_name;
        rela->type = ELF64_SHT_RELA;
        rela->alignment = 8u;
        rela->entry_size = ELF64_RELA_SIZE;
        rela->link = symbol_section_index;
        rela->info = target + 1u;
        rela->data = buffer->data;
        rela->size = (uint64_t)buffer->length;
        relocation_buffer_index++;
    }

    sections[section_name_index].name = ".shstrtab";
    sections[section_name_index].type = ELF64_SHT_STRTAB;
    sections[section_name_index].alignment = 1u;
    sections[section_name_index].data = NULL;

    for (uint32_t i = 1u; i < output_section_count; ++i) {
        if (!string_table_add(&section_names, sections[i].name,
                              &sections[i].name_offset)) {
            status = fail(error, i, REAPER_ELF64_OUT_OF_MEMORY,
                          "cannot build section-name string table");
            goto done;
        }
    }
    sections[section_name_index].data = section_names.data;
    sections[section_name_index].size = (uint64_t)section_names.length;

    cursor = ELF64_EHDR_SIZE;
    for (uint32_t i = 1u; i < output_section_count; ++i) {
        OutputSection *section = &sections[i];
        if (!checked_align_u64(cursor, section->alignment, &cursor)) {
            status = fail(error, i, REAPER_ELF64_RANGE_ERROR,
                          "section alignment overflows the ELF file offset");
            goto done;
        }
        section->offset = cursor;
        if (section->type != REAPER_ELF64_SHT_NOBITS &&
            !checked_add_u64(cursor, section->size, &cursor)) {
            status = fail(error, i, REAPER_ELF64_RANGE_ERROR,
                          "section data overflows the ELF file size");
            goto done;
        }
    }
    if (!checked_align_u64(cursor, 8u, &section_header_offset) ||
        !checked_add_u64(section_header_offset,
                         (uint64_t)output_section_count * ELF64_SHDR_SIZE,
                         &file_size) || file_size > (uint64_t)SIZE_MAX) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                      "ELF section header table exceeds addressable memory");
        goto done;
    }

    file = (uint8_t *)calloc((size_t)file_size, 1u);
    if (file == NULL) {
        status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                      "cannot allocate final ELF object");
        goto done;
    }

    file[0] = 0x7fu; file[1] = 'E'; file[2] = 'L'; file[3] = 'F';
    file[4] = 2u;
    file[5] = 1u;
    file[6] = 1u;
    put16(file + 16u, ELF64_ET_REL);
    put16(file + 18u, ELF64_EM_X86_64);
    put32(file + 20u, ELF64_EV_CURRENT);
    put64(file + 24u, 0u);
    put64(file + 32u, 0u);
    put64(file + 40u, section_header_offset);
    put32(file + 48u, 0u);
    put16(file + 52u, ELF64_EHDR_SIZE);
    put16(file + 54u, 0u);
    put16(file + 56u, 0u);
    put16(file + 58u, ELF64_SHDR_SIZE);
    put16(file + 60u, (uint16_t)output_section_count);
    put16(file + 62u, (uint16_t)section_name_index);

    for (uint32_t i = 1u; i < output_section_count; ++i) {
        const OutputSection *section = &sections[i];
        if (section->type != REAPER_ELF64_SHT_NOBITS &&
            section->size != 0u && section->data != NULL)
            memcpy(file + (size_t)section->offset, section->data, (size_t)section->size);
        write_section_header(file + (size_t)section_header_offset +
                             (size_t)i * ELF64_SHDR_SIZE, section);
    }

    output->data = file;
    output->size = file_size;
    file = NULL;

done:
    if (sections != NULL) {
        for (uint32_t i = 0u; i < output_section_count; ++i) {
            if (sections[i].name != NULL && i >= string_section_index + 1u &&
                i < section_name_index)
                free((void *)sections[i].name);
        }
    }
    free(file);
    cleanup(NULL, &symbol_table, &string_table, &section_names,
            sections, relocation_data, relocation_section_count,
            symbol_map, symbol_name_offsets, relocation_counts);
    return status;
}

void reaper_elf64_buffer_destroy(ReaperElf64Buffer *buffer) {
    if (buffer == NULL) return;
    free(buffer->data);
    buffer->data = NULL;
    buffer->size = 0u;
}

const char *reaper_elf64_status_name(ReaperElf64Status status) {
    switch (status) {
    case REAPER_ELF64_OK: return "ok";
    case REAPER_ELF64_INVALID_ARGUMENT: return "invalid_argument";
    case REAPER_ELF64_UNSUPPORTED: return "unsupported";
    case REAPER_ELF64_RANGE_ERROR: return "range_error";
    case REAPER_ELF64_OUT_OF_MEMORY: return "out_of_memory";
    default: return "unknown";
    }
}
