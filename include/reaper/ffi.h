#ifndef REAPER_FFI_H
#define REAPER_FFI_H

#include <stdint.h>

#if defined(_WIN32)
#  if defined(REAPER_FFI_BUILD)
#    define REAPER_FFI_API __declspec(dllexport)
#  elif defined(REAPER_FFI_USE)
#    define REAPER_FFI_API __declspec(dllimport)
#  else
#    define REAPER_FFI_API
#  endif
#else
#  define REAPER_FFI_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_ABI_VERSION 1u
#define REAPER_MAX_SOURCE_BYTES UINT64_C(1048576)

enum {
    REAPER_ABI_OK = 0,
    REAPER_ABI_INVALID_ARGUMENT = -1,
    REAPER_ABI_UNSUPPORTED_ABI = -2,
    REAPER_ABI_SOURCE_TOO_LARGE = -3,
    REAPER_ABI_LEX_ERROR = -4,
    REAPER_ABI_PARSE_ERROR = -5,
    REAPER_ABI_LOWER_ERROR = -6,
    REAPER_ABI_OPTIMIZE_ERROR = -7,
    REAPER_ABI_EXECUTION_ERROR = -8,
    REAPER_ABI_BUFFER_TOO_SMALL = -9,
    REAPER_ABI_NOT_FOUND = -10
};

/* Evaluate one bounded integer expression using Reaper's native C17 pipeline.
 * The source is UTF-8 text with an explicit byte length and may not contain NUL.
 * output is written only when the complete pipeline succeeds. Error text is optional.
 */
REAPER_FFI_API uint32_t reaper_abi_version(void);
REAPER_FFI_API int32_t reaper_v1_eval_i64(
    const char *source, uint64_t source_length, int64_t *output,
    char *error, uint64_t error_capacity
);

/* Exact UTF-8 lookup into Reaper's immutable selfhood/autonomy vocabulary. */
REAPER_FFI_API int32_t reaper_v1_selfhood_count(uint64_t *count);
REAPER_FFI_API int32_t reaper_v1_selfhood_lookup(
    const char *identity, uint64_t *ordinal
);

#ifdef __cplusplus
}
#endif

#endif
