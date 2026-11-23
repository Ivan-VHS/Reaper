#ifndef REAPER_ELF64_LOADER_H
#define REAPER_ELF64_LOADER_H

#include "reaper/elf64.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint64_t virtual_address;
    uint64_t memory_size;
    uint64_t file_offset;
    uint64_t file_size;
    uint64_t alignment;
    uint32_t flags;
} ReaperElf64LoadSegment;

typedef struct {
    uint64_t entry;
    uint64_t lowest_address;
    uint64_t highest_address;
    uint32_t segment_count;
    ReaperElf64LoadSegment *segments;
} ReaperElf64LoadPlan;

typedef struct {
    void *context;
    int (*map)(void *context, uint64_t address, uint64_t size,
               uint32_t flags, uint8_t **writable_memory);
    int (*protect)(void *context, uint64_t address, uint64_t size,
                   uint32_t flags);
    void (*release_all)(void *context);
} ReaperElf64MemoryOps;

typedef struct {
    const char *const *argv;
    uint64_t argc;
    const char *const *envp;
    uint64_t envc;
    uint64_t virtual_base;
    uint64_t entry;
    uint64_t page_size;
} ReaperElf64StackInput;

typedef struct {
    uint64_t stack_pointer;
    uint64_t argc_address;
    uint64_t argv_address;
    uint64_t envp_address;
    uint64_t auxv_address;
} ReaperElf64InitialStack;

ReaperElf64Status reaper_elf64_plan_load(
    const ReaperElf64Buffer *image,
    ReaperElf64LoadPlan *plan,
    ReaperElf64Error *error
);

ReaperElf64Status reaper_elf64_apply_load(
    const ReaperElf64Buffer *image,
    const ReaperElf64LoadPlan *plan,
    const ReaperElf64MemoryOps *memory,
    ReaperElf64Error *error
);

void reaper_elf64_load_plan_destroy(ReaperElf64LoadPlan *plan);

ReaperElf64Status reaper_elf64_build_initial_stack(
    uint8_t *storage,
    uint64_t storage_size,
    const ReaperElf64StackInput *input,
    ReaperElf64InitialStack *stack,
    ReaperElf64Error *error
);

#ifdef __cplusplus
}
#endif

#endif
