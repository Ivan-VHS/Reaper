#ifndef REAPER_ELF64_LINK_H
#define REAPER_ELF64_LINK_H

#include "reaper/elf64.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    const ReaperElf64Buffer *objects;
    uint32_t object_count;
    const char *entry_symbol;
    uint64_t image_base;
    uint64_t page_size;
} ReaperElf64LinkInput;

/* Static multi-object x86-64 linker. Emits a section-header-free ET_EXEC image. */
ReaperElf64Status reaper_elf64_link(
    const ReaperElf64LinkInput *input,
    ReaperElf64Buffer *output,
    ReaperElf64Error *error
);

#ifdef __cplusplus
}
#endif

#endif
