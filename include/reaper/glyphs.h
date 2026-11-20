#ifndef REAPER_GLYPHS_H
#define REAPER_GLYPHS_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
size_t reaper_glyph_count(void);
const char *reaper_glyph_at(size_t index);
const char *reaper_glyph_match(const char *source, size_t *matched_length);
#ifdef __cplusplus
}
#endif
#endif
