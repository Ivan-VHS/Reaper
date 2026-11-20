#ifndef REAPER_OPERATORS_H
#define REAPER_OPERATORS_H
#ifdef __cplusplus
extern "C" {
#endif
#define REAPER_OPERATOR_COUNT 666u
#define REAPER_OPERATOR_ANCHOR_COUNT 48u
typedef enum {
    REAPER_OP_MEMORY = 0, REAPER_OP_FLOW, REAPER_OP_BINDING,
    REAPER_OP_ARITHMETIC, REAPER_OP_METRIC, REAPER_OP_SYSTEM
} ReaperOperatorFamily;
typedef struct {
    unsigned id;
    const char *glyph;
    ReaperOperatorFamily family;
    int executable;
} ReaperOperatorInfo;
int reaper_operator_lookup(const char *glyph, ReaperOperatorInfo *out);
int reaper_operator_glyph(unsigned id, char out[6]);
const char *reaper_operator_family_name(ReaperOperatorFamily family);
#ifdef __cplusplus
}
#endif
#endif
