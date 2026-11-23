#include "reaper/elf64_loader.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define EHDR 64u
#define PHDR 56u
#define ET_EXEC 2u
#define EM_X86_64 62u
#define PT_LOAD 1u
#define PT_DYNAMIC 2u
#define PT_INTERP 3u
#define PF_X 1u
#define PF_W 2u
#define PF_R 4u
#define AT_NULL 0u
#define AT_PAGESZ 6u
#define AT_ENTRY 9u
#define MAX_ARGS 256u
#define MAX_ENVS 256u

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
static int is_power_two(uint64_t value) {
    return value != 0u && (value & (value - 1u)) == 0u;
}
static ReaperElf64Status fail(ReaperElf64Error *error, uint32_t index,
                              ReaperElf64Status status, const char *message) {
    if (error != NULL) {
        error->item_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}

void reaper_elf64_load_plan_destroy(ReaperElf64LoadPlan *plan) {
    if (plan == NULL) return;
    free(plan->segments);
    memset(plan, 0, sizeof *plan);
}

ReaperElf64Status reaper_elf64_plan_load(
    const ReaperElf64Buffer *image,
    ReaperElf64LoadPlan *plan,
    ReaperElf64Error *error
) {
    if (plan != NULL) memset(plan, 0, sizeof *plan);
    if (error != NULL) { error->item_index = 0u; error->message[0] = '\0'; }
    if (image == NULL || image->data == NULL || plan == NULL ||
        image->size < EHDR)
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "ELF image and load plan are required");

    const uint8_t *file = image->data;
    if (file[0] != 0x7fu || file[1] != 'E' || file[2] != 'L' || file[3] != 'F' ||
        file[4] != 2u || file[5] != 1u || file[6] != 1u ||
        r16(file + 16u) != ET_EXEC || r16(file + 18u) != EM_X86_64 ||
        r32(file + 20u) != 1u)
        return fail(error, 0u, REAPER_ELF64_UNSUPPORTED,
                    "loader accepts only little-endian x86-64 ELF64 ET_EXEC");

    uint64_t entry = r64(file + 24u);
    uint64_t phoff = r64(file + 32u);
    uint16_t ehsize = r16(file + 52u);
    uint16_t phentsize = r16(file + 54u);
    uint16_t phnum = r16(file + 56u);
    if (ehsize != EHDR || phentsize != PHDR || phnum == 0u ||
        !inside(phoff, (uint64_t)phnum * PHDR, image->size))
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "invalid ELF program-header table");

    uint32_t load_count = 0u;
    for (uint16_t i = 0u; i < phnum; ++i) {
        const uint8_t *p = file + (size_t)phoff + (size_t)i * PHDR;
        uint32_t type = r32(p);
        if (type == PT_INTERP || type == PT_DYNAMIC)
            return fail(error, i, REAPER_ELF64_UNSUPPORTED,
                        "dynamic interpreters and dynamic linking are not supported");
        if (type == PT_LOAD) load_count++;
    }
    if (load_count == 0u)
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "ELF image has no PT_LOAD segments");

    ReaperElf64LoadSegment *segments =
        (ReaperElf64LoadSegment *)calloc(load_count, sizeof *segments);
    if (segments == NULL)
        return fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                    "cannot allocate load plan segments");

    uint64_t lowest = UINT64_MAX, highest = 0u;
    int entry_executable = 0;
    uint32_t out_index = 0u;
    for (uint16_t i = 0u; i < phnum; ++i) {
        const uint8_t *p = file + (size_t)phoff + (size_t)i * PHDR;
        if (r32(p) != PT_LOAD) continue;
        uint32_t flags = r32(p + 4u);
        uint64_t offset = r64(p + 8u);
        uint64_t vaddr = r64(p + 16u);
        uint64_t filesz = r64(p + 32u);
        uint64_t memsz = r64(p + 40u);
        uint64_t align = r64(p + 48u);
        uint64_t end;
        if ((flags & ~(PF_R | PF_W | PF_X)) != 0u ||
            (flags & (PF_W | PF_X)) == (PF_W | PF_X) ||
            filesz > memsz || !inside(offset, filesz, image->size) ||
            !add64(vaddr, memsz, &end) ||
            (align > 1u && (!is_power_two(align) ||
                            (offset & (align - 1u)) != (vaddr & (align - 1u))))) {
            free(segments);
            return fail(error, i, REAPER_ELF64_INVALID_ARGUMENT,
                        "invalid PT_LOAD range, permissions or alignment");
        }
        if (memsz == 0u) continue;
        segments[out_index++] = (ReaperElf64LoadSegment){
            vaddr, memsz, offset, filesz, align, flags
        };
        if (vaddr < lowest) lowest = vaddr;
        if (end > highest) highest = end;
        if ((flags & PF_X) != 0u && entry >= vaddr && entry < end)
            entry_executable = 1;
    }
    if (out_index == 0u || !entry_executable) {
        free(segments);
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "entry point is not inside an executable load segment");
    }
    for (uint32_t i = 0u; i < out_index; ++i) {
        uint64_t a_end = segments[i].virtual_address + segments[i].memory_size;
        for (uint32_t j = i + 1u; j < out_index; ++j) {
            uint64_t b_end = segments[j].virtual_address + segments[j].memory_size;
            if (segments[i].virtual_address < b_end &&
                segments[j].virtual_address < a_end) {
                free(segments);
                return fail(error, j, REAPER_ELF64_INVALID_ARGUMENT,
                            "PT_LOAD virtual address ranges overlap");
            }
        }
    }
    plan->entry = entry;
    plan->lowest_address = lowest;
    plan->highest_address = highest;
    plan->segment_count = out_index;
    plan->segments = segments;
    return REAPER_ELF64_OK;
}

ReaperElf64Status reaper_elf64_apply_load(
    const ReaperElf64Buffer *image,
    const ReaperElf64LoadPlan *plan,
    const ReaperElf64MemoryOps *memory,
    ReaperElf64Error *error
) {
    if (error != NULL) { error->item_index = 0u; error->message[0] = '\0'; }
    if (image == NULL || image->data == NULL || plan == NULL ||
        plan->segments == NULL || memory == NULL ||
        memory->map == NULL || memory->protect == NULL)
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "image, load plan and memory operations are required");

    uint32_t mapped = 0u;
    for (uint32_t i = 0u; i < plan->segment_count; ++i) {
        const ReaperElf64LoadSegment *segment = &plan->segments[i];
        uint8_t *target = NULL;
        if (memory->map(memory->context, segment->virtual_address,
                        segment->memory_size, segment->flags, &target) != 0 ||
            target == NULL) {
            if (memory->release_all != NULL) memory->release_all(memory->context);
            return fail(error, i, REAPER_ELF64_OUT_OF_MEMORY,
                        "cannot map ELF load segment");
        }
        mapped++;
        if (segment->file_size != 0u)
            memcpy(target, image->data + (size_t)segment->file_offset,
                   (size_t)segment->file_size);
        if (segment->memory_size > segment->file_size)
            memset(target + (size_t)segment->file_size, 0,
                   (size_t)(segment->memory_size - segment->file_size));
        if (memory->protect(memory->context, segment->virtual_address,
                            segment->memory_size, segment->flags) != 0) {
            if (memory->release_all != NULL) memory->release_all(memory->context);
            return fail(error, i, REAPER_ELF64_INVALID_ARGUMENT,
                        "cannot apply final ELF segment permissions");
        }
    }
    (void)mapped;
    return REAPER_ELF64_OK;
}

static int push_string(uint8_t *storage, uint64_t *cursor, uint64_t base,
                       const char *value, uint64_t *address) {
    size_t length = strlen(value) + 1u;
    if ((uint64_t)length > *cursor) return 0;
    *cursor -= (uint64_t)length;
    memcpy(storage + (size_t)*cursor, value, length);
    if (!add64(base, *cursor, address)) return 0;
    return 1;
}

ReaperElf64Status reaper_elf64_build_initial_stack(
    uint8_t *storage,
    uint64_t storage_size,
    const ReaperElf64StackInput *input,
    ReaperElf64InitialStack *stack,
    ReaperElf64Error *error
) {
    uint64_t *argv_addresses = NULL, *env_addresses = NULL;
    uint64_t cursor, words, vector_bytes, vector_start;
    ReaperElf64Status status = REAPER_ELF64_OK;
    if (stack != NULL) memset(stack, 0, sizeof *stack);
    if (error != NULL) { error->item_index = 0u; error->message[0] = '\0'; }
    if (storage == NULL || input == NULL || stack == NULL ||
        (input->argc != 0u && input->argv == NULL) ||
        (input->envc != 0u && input->envp == NULL) ||
        input->argc > MAX_ARGS || input->envc > MAX_ENVS ||
        !is_power_two(input->page_size) ||
        (input->virtual_base & 15u) != 0u)
        return fail(error, 0u, REAPER_ELF64_INVALID_ARGUMENT,
                    "invalid initial stack input");
    argv_addresses = (uint64_t *)calloc((size_t)input->argc, sizeof(uint64_t));
    env_addresses = (uint64_t *)calloc((size_t)input->envc, sizeof(uint64_t));
    if ((input->argc != 0u && argv_addresses == NULL) ||
        (input->envc != 0u && env_addresses == NULL)) {
        status = fail(error, 0u, REAPER_ELF64_OUT_OF_MEMORY,
                      "cannot allocate argument address tables");
        goto done;
    }
    cursor = storage_size;
    for (uint64_t i = input->envc; i > 0u; --i) {
        if (input->envp[i - 1u] == NULL ||
            !push_string(storage, &cursor, input->virtual_base,
                         input->envp[i - 1u], &env_addresses[i - 1u])) {
            status = fail(error, (uint32_t)i, REAPER_ELF64_RANGE_ERROR,
                          "environment strings exceed stack storage");
            goto done;
        }
    }
    for (uint64_t i = input->argc; i > 0u; --i) {
        if (input->argv[i - 1u] == NULL ||
            !push_string(storage, &cursor, input->virtual_base,
                         input->argv[i - 1u], &argv_addresses[i - 1u])) {
            status = fail(error, (uint32_t)i, REAPER_ELF64_RANGE_ERROR,
                          "argument strings exceed stack storage");
            goto done;
        }
    }
    words = 1u + input->argc + 1u + input->envc + 1u + 6u;
    if (words > UINT64_MAX / 8u) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                      "initial stack vector size overflows");
        goto done;
    }
    vector_bytes = words * 8u;
    if (cursor < vector_bytes) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                      "argument vectors do not fit in stack storage");
        goto done;
    }
    vector_start = (cursor - vector_bytes) & ~UINT64_C(15);
    if (vector_start > cursor || !add64(input->virtual_base, vector_start,
                                         &stack->stack_pointer)) {
        status = fail(error, 0u, REAPER_ELF64_RANGE_ERROR,
                      "initial stack pointer overflows");
        goto done;
    }
    uint64_t index = 0u;
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, input->argc);
    stack->argc_address = stack->stack_pointer;
    stack->argv_address = stack->stack_pointer + 8u;
    for (uint64_t i = 0u; i < input->argc; ++i)
        w64(storage + (size_t)vector_start + (size_t)index++ * 8u,
            argv_addresses[i]);
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, 0u);
    stack->envp_address = stack->stack_pointer + index * 8u;
    for (uint64_t i = 0u; i < input->envc; ++i)
        w64(storage + (size_t)vector_start + (size_t)index++ * 8u,
            env_addresses[i]);
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, 0u);
    stack->auxv_address = stack->stack_pointer + index * 8u;
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, AT_PAGESZ);
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, input->page_size);
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, AT_ENTRY);
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, input->entry);
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, AT_NULL);
    w64(storage + (size_t)vector_start + (size_t)index++ * 8u, 0u);

done:
    free(argv_addresses);
    free(env_addresses);
    return status;
}
