#include "reaper/operators.h"
#include <string.h>
static const char *const anchors[REAPER_OPERATOR_ANCHOR_COUNT] = {
    ";;:",
    "::;",
    "::=",
    ":++",
    "::",
    ":;",
    "=::",
    "++:",
    ":;:",
    ";::",
    ":::",
    ";;;",
    ":=:",
    ":+:",
    ";+:",
    ":+;",
    "=:=",
    ":==",
    "==:",
    "++;",
    ";++;",
    "::+",
    "+::",
    ":;;",
    ";:;",
    ";;=",
    "=;;",
    ":+=",
    "++=",
    ";=:",
    ":=;",
    "::;;",
    ";;::",
    ":+++",
    "+++:",
    ";::;",
    "::;:",
    ":;::",
    "=::=",
    ":==:",
    ";;+:",
    "+:;;",
    "::=+",
    ";=;",
    ":==+",
    ";;=;",
    ":;=:",
    "::=;"
};
static ReaperOperatorFamily family_for_id(unsigned id) {
    if (id <= 120u) return REAPER_OP_MEMORY;
    if (id <= 240u) return REAPER_OP_FLOW;
    if (id <= 360u) return REAPER_OP_BINDING;
    if (id <= 480u) return REAPER_OP_ARITHMETIC;
    if (id <= 580u) return REAPER_OP_METRIC;
    return REAPER_OP_SYSTEM;
}
static int glyph_digit(char c) {
    switch (c) {
        case ':': return 0; case ';': return 1; case '=': return 2; case '+': return 3;
        default: return -1;
    }
}
const char *reaper_operator_family_name(ReaperOperatorFamily family) {
    switch (family) {
        case REAPER_OP_MEMORY: return "memory";
        case REAPER_OP_FLOW: return "flow";
        case REAPER_OP_BINDING: return "binding";
        case REAPER_OP_ARITHMETIC: return "arithmetic";
        case REAPER_OP_METRIC: return "metric";
        case REAPER_OP_SYSTEM: return "system";
        default: return "unknown";
    }
}
int reaper_operator_lookup(const char *glyph, ReaperOperatorInfo *out) {
    if (!glyph || !*glyph) return 0;
    for (unsigned i = 0u; i < REAPER_OPERATOR_ANCHOR_COUNT; ++i) {
        if (strcmp(glyph, anchors[i]) == 0) {
            unsigned id = i + 1u;
            if (out) {
                out->id=id; out->glyph=anchors[i]; out->family=family_for_id(id);
                out->executable=id==3u||id==4u||id==5u||id==7u||id==8u;
            }
            return 1;
        }
    }
    if (strlen(glyph) != 5u) return 0;
    unsigned value=0u;
    for (size_t i=0u;i<5u;++i) {
        int digit=glyph_digit(glyph[i]);
        if (digit<0) return 0;
        value=value*4u+(unsigned)digit;
    }
    if (value >= REAPER_OPERATOR_COUNT-REAPER_OPERATOR_ANCHOR_COUNT) return 0;
    unsigned id=REAPER_OPERATOR_ANCHOR_COUNT+value+1u;
    if (out) {out->id=id;out->glyph=glyph;out->family=family_for_id(id);out->executable=0;}
    return 1;
}
int reaper_operator_glyph(unsigned id, char out[6]) {
    if (!out||id==0u||id>REAPER_OPERATOR_COUNT) return 0;
    if (id<=REAPER_OPERATOR_ANCHOR_COUNT) {
        size_t length=strlen(anchors[id-1u]);
        memcpy(out,anchors[id-1u],length+1u);
        return 1;
    }
    unsigned value=id-REAPER_OPERATOR_ANCHOR_COUNT-1u;
    static const char alphabet[]=":;=+";
    out[5]='\0';
    for(size_t position=5u;position>0u;--position){
        out[position-1u]=alphabet[value%4u];
        value/=4u;
    }
    return 1;
}
