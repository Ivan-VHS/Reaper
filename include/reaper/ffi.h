#ifndef REAPER_FFI_H
#define REAPER_FFI_H

#include <stdint.h>
#include "reaper/lexer.h"

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_ABI_VERSION UINT32_C(1)

/* Stable status codes returned by the versioned native C ABI. */
typedef enum {
    REAPER_ABI_OK = 0,
    REAPER_ABI_INVALID_ARGUMENT = 1,
    REAPER_ABI_LIMIT = 2,
    REAPER_ABI_SYNTAX_ERROR = 3,
    REAPER_ABI_UNSUPPORTED_EXPRESSION = 4,
    REAPER_ABI_ARITHMETIC_ERROR = 5,
    REAPER_ABI_NOT_FOUND = 6
} ReaperAbiStatus;

uint32_t reaper_abi_version(void);

/* Evaluate the pure integer expression subset using Reaper's lexer, parser
 * and verified i64 IR. Source length is explicit; embedded NUL is rejected.
 * The result is written only when the entire expression evaluates. */
int32_t reaper_v1_eval_i64(
    const char *source,
    uint64_t source_size,
    int64_t *result,
    char *diagnostic,
    uint64_t diagnostic_capacity
);

/* Look up one stable, canonical selfhood identifier. The ordinal output is
 * left untouched when the identity is invalid or unknown. */
int32_t reaper_v1_selfhood_lookup(
    const char *identity,
    uint64_t *ordinal
);

#ifdef __cplusplus
}
#endif
#endif
