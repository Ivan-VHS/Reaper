#ifdef NDEBUG
#undef NDEBUG
#endif
#include "reaper/dabi64_process.h"

#include <assert.h>
#include <string.h>

static int64_t entry_ok(ReaperDabiRuntime *runtime, uint64_t argc,
                        const char *const *argv, uint64_t envc,
                        const char *const *envp) {
    ReaperDabiValue value = reaper_dabi_unit();
    (void)envc;
    (void)envp;
    if (argc != 1u || strcmp(argv[0], "reaper") != 0) return 2;
    if (reaper_dabi_string_new(runtime, (const uint8_t *)"ok", 2u,
                               &value) != REAPER_DABI_OK) return 3;
    reaper_dabi_value_drop(runtime, &value);
    return 42;
}

static int64_t entry_leaks(ReaperDabiRuntime *runtime, uint64_t argc,
                           const char *const *argv, uint64_t envc,
                           const char *const *envp) {
    ReaperDabiValue value;
    (void)argc; (void)argv; (void)envc; (void)envp;
    if (reaper_dabi_string_new(runtime, (const uint8_t *)"leak", 4u,
                               &value) != REAPER_DABI_OK) return -1;
    return 0;
}

int main(void) {
    ReaperDabiHostV1 host = {
        REAPER_DABI64_VERSION, (uint32_t)sizeof(ReaperDabiHostV1),
        NULL, NULL, NULL, NULL, NULL
    };
    const char *argv[] = {"reaper"};
    ReaperDabiProcessResult result;
    assert(reaper_dabi_process_dispatch(&host, NULL, entry_ok, 1u, argv,
                                        0u, NULL, &result) == REAPER_DABI_OK);
    assert(result.exit_code == 42 && result.live_objects_at_exit == 0u);
    assert(reaper_dabi_process_dispatch(&host, NULL, entry_leaks, 0u, NULL,
                                        0u, NULL, &result) == REAPER_DABI_CLOSED);
    assert(result.exit_code == 0 && result.live_objects_at_exit == 1u);
    return 0;
}
