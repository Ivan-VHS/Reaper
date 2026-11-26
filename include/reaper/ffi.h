#ifndef REAPER_FFI_H
#define REAPER_FFI_H

#include <stdint.h>
#include "reaper/lexer.h"

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_ABI_VERSION UINT32_C(1)
#define REAPER_V1_MAX_SOURCE_BYTES (1024u * 1024u)

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
int32_t reaper_v1_eval_i64(const char *source, uint64_t source_size,
                           int64_t *result, char *diagnostic,
                           uint64_t diagnostic_capacity);
int32_t reaper_v1_selfhood_lookup(const char *identity, uint64_t *ordinal);

#ifdef __cplusplus
}
#endif
#endif
