#ifndef REAPER_ELF64_LINKER_H
#define REAPER_ELF64_LINKER_H
#include "reaper/elf64.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef struct {
    uint8_t *data;
    uint64_t size;
    uint64_t entry_address;
} ReaperElf64Executable;
ReaperElf64Status reaper_elf64_link_executable(
    const ReaperElf64Object *objects, uint32_t object_count,
    const char *entry_symbol, ReaperElf64Executable *output,
    ReaperElf64Error *error
);
void reaper_elf64_executable_destroy(ReaperElf64Executable *executable);
#ifdef __cplusplus
}
#endif
#endif
