#ifndef REAPER_SELFHOOD_H
#define REAPER_SELFHOOD_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t ordinal;
    const char *identity;
    const char *transformation;
    const char *autonomy;
} ReaperSelfhoodEntry;

/* Immutable, process-local vocabulary; pointers remain valid for process life. */
size_t reaper_selfhood_count(void);
const ReaperSelfhoodEntry *reaper_selfhood_at(size_t index);
const ReaperSelfhoodEntry *reaper_selfhood_find(const char *identity);

#ifdef __cplusplus
}
#endif

#endif
