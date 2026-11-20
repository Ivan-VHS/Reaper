#include "reaper/operators.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    char glyph[6]; ReaperOperatorInfo info;
    for (unsigned id = 1u; id <= REAPER_OPERATOR_COUNT; ++id) {
        assert(reaper_operator_glyph(id, glyph));
        assert(reaper_operator_lookup(glyph, &info));
        assert(info.id == id && strcmp(info.glyph, glyph) == 0);
    }
    assert(reaper_operator_lookup("::", &info) && info.id == 5u && info.executable);
    assert(reaper_operator_lookup(":::::", &info) && info.id == 49u && !info.executable);
    assert(!reaper_operator_lookup("+++++", &info));
    assert(!reaper_operator_lookup("::::::", &info));
    assert(!reaper_operator_glyph(0u, glyph) && !reaper_operator_glyph(667u, glyph));
    puts("native operator registry: 666 IDs round-trip");
    return 0;
}
