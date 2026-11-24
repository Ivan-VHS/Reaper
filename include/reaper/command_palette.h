#ifndef REAPER_COMMAND_PALETTE_H
#define REAPER_COMMAND_PALETTE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_PALETTE_QUERY_MAX 256u
#define REAPER_PALETTE_FIELD_MAX 192u

/* Local deterministic fallback for a host-provided semantic/SLM intent adapter.
 * This ranks commands only; it never executes commands or loads a model. */
typedef struct {
    const char *id;
    const char *label;
    const char *keywords;
} ReaperPaletteCommand;

typedef struct {
    size_t command_index;
    uint32_t score;
} ReaperPaletteMatch;

/* Returns the number of ranked matches written (at most capacity).
 * Empty/invalid queries or invalid command records return zero. */
size_t reaper_palette_rank(
    const ReaperPaletteCommand *commands,
    size_t command_count,
    const char *query,
    ReaperPaletteMatch *matches,
    size_t capacity
);

#ifdef __cplusplus
}
#endif
#endif
