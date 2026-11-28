#include "reaper/ffi.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    char diagnostic[256];
    int64_t result = 987;
    uint64_t ordinal = 99u;

    assert(reaper_abi_version() == REAPER_ABI_VERSION);
    assert(reaper_v1_eval_i64("(6 * 7) - 1", 11u, &result,
                              diagnostic, sizeof diagnostic) == REAPER_ABI_OK);
    assert(result == 41);
    assert(reaper_v1_eval_i64("84 / 2", 6u, &result,
                              diagnostic, sizeof diagnostic) == REAPER_ABI_OK);
    assert(result == 42);
    {
        const char minimum[] = "-9223372036854775808";
        assert(reaper_v1_eval_i64(minimum, sizeof(minimum) - 1u, &result,
                                  diagnostic, sizeof diagnostic) == REAPER_ABI_OK);
        assert(result == INT64_MIN);
    }
    {
        const char below_minimum[] = "-9223372036854775809";
        assert(reaper_v1_eval_i64(below_minimum, sizeof(below_minimum) - 1u, &result,
                                  diagnostic, sizeof diagnostic) == REAPER_ABI_UNSUPPORTED_EXPRESSION);
    }
    {
        const char negate_minimum[] = "--9223372036854775808";
        result = 987;
        assert(reaper_v1_eval_i64(negate_minimum, sizeof(negate_minimum) - 1u, &result,
                                  diagnostic, sizeof diagnostic) == REAPER_ABI_ARITHMETIC_ERROR);
        assert(result == 987);
    }

    result = 987;
    assert(reaper_v1_eval_i64("9223372036854775807 + 1", 23u, &result,
                              diagnostic, sizeof diagnostic) == REAPER_ABI_ARITHMETIC_ERROR);
    assert(result == 987);
    assert(strstr(diagnostic, "overflow") != NULL);

    assert(reaper_v1_eval_i64("1 / 0", 5u, &result,
                              diagnostic, sizeof diagnostic) == REAPER_ABI_ARITHMETIC_ERROR);
    assert(result == 987);
    assert(strstr(diagnostic, "zero") != NULL);

    assert(reaper_v1_eval_i64("1 +", 3u, &result,
                              diagnostic, sizeof diagnostic) == REAPER_ABI_SYNTAX_ERROR);
    assert(reaper_v1_eval_i64("1 + 2.5", 7u, &result,
                              diagnostic, sizeof diagnostic) == REAPER_ABI_UNSUPPORTED_EXPRESSION);
    assert(reaper_v1_eval_i64("1\0+2", 4u, &result,
                              diagnostic, sizeof diagnostic) == REAPER_ABI_INVALID_ARGUMENT);
    assert(reaper_v1_eval_i64("", 0u, &result,
                              diagnostic, sizeof diagnostic) == REAPER_ABI_LIMIT);

    assert(reaper_v1_selfhood_lookup("Сам", &ordinal) == REAPER_ABI_OK);
    assert(ordinal == 2u);
    ordinal = 99u;
    assert(reaper_v1_selfhood_lookup("unknown", &ordinal) == REAPER_ABI_NOT_FOUND);
    assert(ordinal == 99u);
    assert(reaper_v1_selfhood_lookup(NULL, &ordinal) == REAPER_ABI_INVALID_ARGUMENT);

    puts("Reaper ABI v1 tests passed.");
    return 0;
}
