#include "reaper/ffi.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int64_t evaluate(const char *source) {
    int64_t result = -999;
    char error[256] = {0};
    int32_t status = reaper_v1_eval_i64(source, (uint64_t)strlen(source),
                                        &result, error, sizeof error);
    if (status != REAPER_ABI_OK) fprintf(stderr, "%s: %s\n", source, error);
    assert(status == REAPER_ABI_OK);
    return result;
}

int main(void) {
    int64_t result = 12345;
    uint64_t count = 0u, ordinal = 0u;
    char error[256] = {0};
    const char embedded_nul[] = {'1', '\0', '2'};

    assert(reaper_abi_version() == REAPER_ABI_VERSION);
    assert(evaluate("1 + 2 * 3") == 7);
    assert(evaluate("(20 - 2) * 3 / 2") == 27);
    assert(evaluate("-7 + 2") == -5);
    assert(evaluate("84 / 2") == 42);

    assert(reaper_v1_eval_i64("7 / 0", 5u, &result, error, sizeof error)
           == REAPER_ABI_OPTIMIZE_ERROR);
    assert(result == 12345 && strstr(error, "zero") != NULL);
    assert(reaper_v1_eval_i64("9223372036854775807 + 1", 23u, &result,
                              error, sizeof error) == REAPER_ABI_OPTIMIZE_ERROR);
    assert(result == 12345);
    assert(reaper_v1_eval_i64(embedded_nul, 3u, &result, error, sizeof error)
           == REAPER_ABI_INVALID_ARGUMENT);
    assert(reaper_v1_eval_i64("1", REAPER_MAX_SOURCE_BYTES + 1u, &result,
                              error, sizeof error) == REAPER_ABI_SOURCE_TOO_LARGE);
    assert(reaper_v1_eval_i64(NULL, 0u, &result, error, sizeof error)
           == REAPER_ABI_INVALID_ARGUMENT);
    assert(reaper_v1_eval_i64("1", 1u, NULL, error, sizeof error)
           == REAPER_ABI_INVALID_ARGUMENT);

    assert(reaper_v1_selfhood_count(&count) == REAPER_ABI_OK && count == 20u);
    assert(reaper_v1_selfhood_lookup("Сам", &ordinal) == REAPER_ABI_OK && ordinal == 2u);
    assert(reaper_v1_selfhood_lookup("неизвестно", &ordinal) == REAPER_ABI_NOT_FOUND);
    assert(reaper_v1_selfhood_count(NULL) == REAPER_ABI_INVALID_ARGUMENT);
    puts("native C ABI tests: expression runtime and selfhood lookup passed");
    return 0;
}
