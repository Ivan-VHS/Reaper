#include "reaper/command_palette.h"

#include <assert.h>
#include <stdio.h>

int main(void) {
    const ReaperPaletteCommand commands[] = {
        {"open-file", "Open File", "project document load"},
        {"open-settings", "Settings", "preferences configure"},
        {"run-tests", "Run Tests", "quality verify"},
        {"toggle-xray", "X-Ray Mode", "performance telemetry hud"}
    };
    ReaperPaletteMatch matches[4];
    size_t count;

    count = reaper_palette_rank(commands, 4u, "open file", matches, 4u);
    assert(count == 1u && matches[0].command_index == 0u);

    count = reaper_palette_rank(commands, 4u, "pref", matches, 4u);
    assert(count == 1u && matches[0].command_index == 1u);

    count = reaper_palette_rank(commands, 4u, "telemetry", matches, 4u);
    assert(count == 1u && matches[0].command_index == 3u);

    count = reaper_palette_rank(commands, 4u, "open", matches, 2u);
    assert(count == 2u);
    assert(matches[0].command_index == 0u);
    assert(matches[1].command_index == 1u);

    assert(reaper_palette_rank(commands, 4u, "", matches, 4u) == 0u);
    assert(reaper_palette_rank(NULL, 4u, "open", matches, 4u) == 0u);
    puts("Reaper command palette tests passed.");
    return 0;
}
