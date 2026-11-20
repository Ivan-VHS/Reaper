#ifndef REAPER_TOKEN_CATALOG_H
#define REAPER_TOKEN_CATALOG_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct {
    size_t ordinal;
    const char *lexeme;
    const char *group;
    const char *category;
    const char *name;
    const char *description;
} ReaperCatalogEntry;
size_t reaper_token_catalog_count(void);
const ReaperCatalogEntry *reaper_token_catalog_at(size_t index);
const ReaperCatalogEntry *reaper_token_catalog_lookup(const char *lexeme);
int reaper_token_catalog_validate(void);
#ifdef __cplusplus
}
#endif
#endif
