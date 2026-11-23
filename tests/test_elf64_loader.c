#ifdef NDEBUG
#undef NDEBUG
#endif
#include "reaper/elf64_loader.h"
#include "reaper/elf64_link.h"

#include <assert.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint8_t *blocks[8];
    uint64_t addresses[8];
    uint64_t sizes[8];
    uint32_t flags[8];
    uint32_t count;
    uint32_t protected_count;
} MockMemory;

static int mock_map(void *context, uint64_t address, uint64_t size,
                    uint32_t flags, uint8_t **memory) {
    MockMemory *mock = (MockMemory *)context;
    if (mock->count >= 8u || size > (uint64_t)SIZE_MAX) return -1;
    uint8_t *block = (uint8_t *)malloc((size_t)size);
    if (block == NULL) return -1;
    memset(block, 0xcc, (size_t)size);
    mock->blocks[mock->count] = block;
    mock->addresses[mock->count] = address;
    mock->sizes[mock->count] = size;
    mock->flags[mock->count] = flags;
    mock->count++;
    *memory = block;
    return 0;
}

static int mock_protect(void *context, uint64_t address, uint64_t size,
                        uint32_t flags) {
    MockMemory *mock = (MockMemory *)context;
    for (uint32_t i = 0u; i < mock->count; ++i) {
        if (mock->addresses[i] == address && mock->sizes[i] == size &&
            mock->flags[i] == flags) {
            mock->protected_count++;
            return 0;
        }
    }
    return -1;
}

static void mock_release(void *context) {
    MockMemory *mock = (MockMemory *)context;
    for (uint32_t i = 0u; i < mock->count; ++i) {
        free(mock->blocks[i]);
        mock->blocks[i] = NULL;
    }
    mock->count = 0u;
}

static void test_elf_load_plan_and_apply(void) {
    static const uint8_t text[] = {0xb8, 42, 0, 0, 0, 0xc3};
    const ReaperElf64Section sections[] = {
        {".text", REAPER_ELF64_SHT_PROGBITS, 0x6u, 16u, 0u, text, sizeof text},
        {".bss", REAPER_ELF64_SHT_NOBITS, 0x3u, 16u, 0u, NULL, 64u}
    };
    const ReaperElf64Symbol symbols[] = {
        {"_start", 0u, 0u, sizeof text, REAPER_ELF64_STB_GLOBAL,
         REAPER_ELF64_STT_FUNC, 0u}
    };
    const ReaperElf64Object model = {sections, 2u, symbols, 1u, NULL, 0u};
    ReaperElf64Buffer object = {0}, executable = {0};
    ReaperElf64Error error = {0};
    assert(reaper_elf64_write_object(&model, &object, &error) == REAPER_ELF64_OK);
    ReaperElf64Buffer link_objects[] = {object};
    ReaperElf64LinkInput link = {link_objects, 1u, "_start", 0x400000u, 4096u};
    assert(reaper_elf64_link(&link, &executable, &error) == REAPER_ELF64_OK);

    ReaperElf64LoadPlan plan;
    assert(reaper_elf64_plan_load(&executable, &plan, &error) == REAPER_ELF64_OK);
    assert(plan.segment_count == 3u);
    assert(plan.entry >= plan.lowest_address && plan.entry < plan.highest_address);
    MockMemory mock = {0};
    ReaperElf64MemoryOps memory = {&mock, mock_map, mock_protect, mock_release};
    assert(reaper_elf64_apply_load(&executable, &plan, &memory, &error) == REAPER_ELF64_OK);
    assert(mock.count == 3u && mock.protected_count == 3u);

    int found_text = 0, found_bss = 0;
    for (uint32_t i = 0u; i < mock.count; ++i) {
        if ((mock.flags[i] & 5u) == 5u) {
            assert(memcmp(mock.blocks[i], text, sizeof text) == 0);
            found_text = 1;
        }
        if ((mock.flags[i] & 3u) == 3u) {
            for (uint64_t j = 0u; j < mock.sizes[i]; ++j)
                assert(mock.blocks[i][j] == 0u);
            found_bss = 1;
        }
    }
    assert(found_text && found_bss);
    mock_release(&mock);
    reaper_elf64_load_plan_destroy(&plan);
    reaper_elf64_buffer_destroy(&object);
    reaper_elf64_buffer_destroy(&executable);
}

static void test_initial_stack(void) {
    uint8_t storage[4096] = {0};
    const char *argv[] = {"reaper", "--native"};
    const char *envp[] = {"MODE=duckos"};
    ReaperElf64StackInput input = {
        argv, 2u, envp, 1u, 0x70000000u, 0x401000u, 4096u
    };
    ReaperElf64InitialStack stack;
    ReaperElf64Error error;
    assert(reaper_elf64_build_initial_stack(storage, sizeof storage, &input,
                                             &stack, &error) == REAPER_ELF64_OK);
    assert((stack.stack_pointer & 15u) == 0u);
    assert(stack.argc_address == stack.stack_pointer);
    uint64_t argc = 0u, argv0 = 0u, argv1 = 0u, argv_end = 1u, env0 = 0u;
    memcpy(&argc, storage + (size_t)(stack.argc_address - input.virtual_base), 8u);
    memcpy(&argv0, storage + (size_t)(stack.argv_address - input.virtual_base), 8u);
    memcpy(&argv1, storage + (size_t)(stack.argv_address - input.virtual_base) + 8u, 8u);
    memcpy(&argv_end, storage + (size_t)(stack.argv_address - input.virtual_base) + 16u, 8u);
    memcpy(&env0, storage + (size_t)(stack.envp_address - input.virtual_base), 8u);
    assert(argc == 2u && argv_end == 0u);
    assert(strcmp((const char *)(storage + (size_t)(argv0 - input.virtual_base)),
                  "reaper") == 0);
    assert(strcmp((const char *)(storage + (size_t)(argv1 - input.virtual_base)),
                  "--native") == 0);
    assert(strcmp((const char *)(storage + (size_t)(env0 - input.virtual_base)),
                  "MODE=duckos") == 0);
}

int main(void) {
    test_elf_load_plan_and_apply();
    test_initial_stack();
    return 0;
}
