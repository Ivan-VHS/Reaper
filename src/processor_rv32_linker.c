#include "reaper/processor_backends.h"
#include "processor_backend_internal.h"

static ReaperProcessorBackendStatus find_symbol(
    const ReaperRv32LinkedImage *image, uint32_t symbol_id, uint32_t *address
) {
    uint32_t i;
    for (i = 0u; i < image->symbol_count; ++i) {
        if (image->symbols[i].symbol_id == symbol_id) {
            *address = image->symbols[i].address;
            return REAPER_BACKEND_OK;
        }
    }
    return REAPER_BACKEND_UNRESOLVED_SYMBOL;
}

static ReaperProcessorBackendStatus apply_relocation(
    uint32_t *word, const ReaperRv32Relocation *relocation,
    uint32_t symbol_address, uint32_t source_address
) {
    const int64_t target = (int64_t)symbol_address + relocation->addend;
    const int64_t delta = target - (int64_t)source_address;
    uint32_t value;
    if (target < 0 || target > UINT32_MAX || (delta & 1) != 0)
        return REAPER_BACKEND_RELOCATION_RANGE;
    value = (uint32_t)delta;
    if (relocation->kind == REAPER_RV32_RELOC_JAL20) {
        if ((*word & UINT32_C(0x7F)) != UINT32_C(0x6F))
            return REAPER_BACKEND_INVALID_ABI;
        if (delta < -1048576 || delta > 1048574)
            return REAPER_BACKEND_RELOCATION_RANGE;
        *word &= UINT32_C(0x00000FFF);
        *word |= ((value >> 20u) & 1u) << 31u;
        *word |= ((value >> 1u) & UINT32_C(0x3FF)) << 21u;
        *word |= ((value >> 11u) & 1u) << 20u;
        *word |= ((value >> 12u) & UINT32_C(0xFF)) << 12u;
        return REAPER_BACKEND_OK;
    }
    if (relocation->kind == REAPER_RV32_RELOC_BRANCH13) {
        if ((*word & UINT32_C(0x7F)) != UINT32_C(0x63))
            return REAPER_BACKEND_INVALID_ABI;
        if (delta < -4096 || delta > 4094)
            return REAPER_BACKEND_RELOCATION_RANGE;
        *word &= UINT32_C(0x01FFF07F);
        *word |= ((value >> 12u) & 1u) << 31u;
        *word |= ((value >> 5u) & UINT32_C(0x3F)) << 25u;
        *word |= ((value >> 1u) & UINT32_C(0xF)) << 8u;
        *word |= ((value >> 11u) & 1u) << 7u;
        return REAPER_BACKEND_OK;
    }
    return REAPER_BACKEND_INVALID_ABI;
}

ReaperProcessorBackendStatus reaper_rv32_link(
    const ReaperRv32Object *objects, size_t object_count,
    uint32_t entry_symbol_id, uint32_t base_address,
    ReaperRv32LinkedImage *output
) {
    uint32_t object_base[REAPER_RV32_MAX_OBJECTS];
    size_t i, j;
    uint32_t total_words = 0u;
    int entry_found = 0;
    if (objects == NULL || output == NULL || entry_symbol_id == 0u ||
        object_count == 0u || object_count > REAPER_RV32_MAX_OBJECTS ||
        (base_address & 3u) != 0u)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    memset(output, 0, sizeof(*output));
    output->magic = REAPER_RV32_IMAGE_MAGIC;
    output->abi_major = REAPER_PROCESSOR_BACKEND_ABI_MAJOR;
    output->target_id = REAPER_RV32_TARGET_RV32I;
    output->abi_id = REAPER_RV32_ABI_ILP32;
    output->base_address = base_address;

    for (i = 0u; i < object_count; ++i) {
        const ReaperRv32Object *object = &objects[i];
        if (object->magic != REAPER_RV32_OBJECT_MAGIC ||
            object->abi_major != REAPER_PROCESSOR_BACKEND_ABI_MAJOR ||
            object->target_id != REAPER_RV32_TARGET_RV32I ||
            object->abi_id != REAPER_RV32_ABI_ILP32)
            return REAPER_BACKEND_INVALID_ABI;
        if (object->word_count == 0u ||
            object->word_count > REAPER_RV32_MAX_INSTRUCTIONS ||
            object->symbol_count > REAPER_RV32_MAX_SYMBOLS ||
            object->relocation_count > REAPER_RV32_MAX_RELOCATIONS ||
            total_words > (REAPER_RV32_MAX_IMAGE_BYTES / 4u) - object->word_count)
            return REAPER_BACKEND_LIMIT_EXCEEDED;
        object_base[i] = total_words;
        total_words += object->word_count;
        if (output->symbol_count + object->symbol_count > REAPER_RV32_MAX_LINK_SYMBOLS)
            return REAPER_BACKEND_LIMIT_EXCEEDED;
        for (j = 0u; j < object->symbol_count; ++j) {
            const ReaperRv32Symbol *symbol = &object->symbols[j];
            uint32_t k;
            if (symbol->symbol_id == 0u || symbol->global_symbol != 1u ||
                symbol->value_offset > object->word_count * 4u)
                return REAPER_BACKEND_INVALID_ARGUMENT;
            for (k = 0u; k < output->symbol_count; ++k)
                if (output->symbols[k].symbol_id == symbol->symbol_id)
                    return REAPER_BACKEND_DUPLICATE_SYMBOL;
            output->symbols[output->symbol_count].symbol_id = symbol->symbol_id;
            ++output->symbol_count;
        }
    }
    output->byte_count = total_words * 4u;
    if ((uint64_t)base_address + output->byte_count > UINT32_MAX)
        return REAPER_BACKEND_RELOCATION_RANGE;

    /* Symbol addresses are calculated only after the full image range is bounded. */
    {
        uint32_t symbol_index = 0u;
        for (i = 0u; i < object_count; ++i) {
            const ReaperRv32Object *object = &objects[i];
            for (j = 0u; j < object->symbol_count; ++j) {
                const ReaperRv32Symbol *symbol = &object->symbols[j];
                const uint64_t address = (uint64_t)base_address +
                    (uint64_t)object_base[i] * 4u + symbol->value_offset;
                if ((symbol->value_offset & 3u) != 0u || address > UINT32_MAX)
                    return REAPER_BACKEND_RELOCATION_RANGE;
                output->symbols[symbol_index].symbol_id = symbol->symbol_id;
                output->symbols[symbol_index].address = (uint32_t)address;
                ++symbol_index;
            }
        }
    }

    for (i = 0u; i < object_count; ++i) {
        const ReaperRv32Object *object = &objects[i];
        for (j = 0u; j < object->word_count; ++j)
            reaper_write_le32(&output->bytes[(object_base[i] + (uint32_t)j) * 4u],
                              object->words[j]);
    }

    for (i = 0u; i < object_count; ++i) {
        const ReaperRv32Object *object = &objects[i];
        for (j = 0u; j < object->relocation_count; ++j) {
            const ReaperRv32Relocation *relocation = &object->relocations[j];
            uint32_t target_address = 0u;
            uint32_t source_address;
            uint32_t word_index;
            uint32_t word;
            ReaperProcessorBackendStatus status;
            if (relocation->word_index >= object->word_count)
                return REAPER_BACKEND_INVALID_ARGUMENT;
            status = find_symbol(output, relocation->symbol_id, &target_address);
            if (status != REAPER_BACKEND_OK) return status;
            word_index = object_base[i] + relocation->word_index;
            source_address = base_address + word_index * 4u;
            word = reaper_read_le32(&output->bytes[word_index * 4u]);
            status = apply_relocation(&word, relocation, target_address, source_address);
            if (status != REAPER_BACKEND_OK) return status;
            reaper_write_le32(&output->bytes[word_index * 4u], word);
        }
    }

    for (i = 0u; i < output->symbol_count; ++i) {
        if (output->symbols[i].symbol_id == entry_symbol_id) {
            output->entry_address = output->symbols[i].address;
            entry_found = 1;
            break;
        }
    }
    if (!entry_found) return REAPER_BACKEND_UNRESOLVED_SYMBOL;
    return REAPER_BACKEND_OK;
}
