#ifndef REAPER_SEADLOW_H
#define REAPER_SEADLOW_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_SEADLOW_TILE_WORDS 256u

typedef enum {
    REAPER_SEADLOW_AND = 1,
    REAPER_SEADLOW_OR,
    REAPER_SEADLOW_XOR,
    REAPER_SEADLOW_NOT
} ReaperSeadlowOp;

typedef struct {
    size_t bits_processed;
    size_t words_processed;
    size_t tail_bytes_processed;
    size_t tail_bits_processed;
    size_t tiles_processed;
} ReaperSeadlowReport;

typedef struct {
    char message[192];
} ReaperSeadlowError;

/* Operate on exactly bit_count bits. Unaligned pointers are supported. Exact
 * in-place operation is allowed; partial output/input overlap is rejected.
 * Unused high bits in the last byte are cleared. NOT ignores rhs. */
int reaper_seadlow_transform(
    ReaperSeadlowOp operation,
    uint8_t *output,
    const uint8_t *lhs,
    const uint8_t *rhs,
    size_t bit_count,
    ReaperSeadlowReport *report,
    ReaperSeadlowError *error
);

/* Count set bits in exactly bit_count bits. */
int reaper_seadlow_popcount(
    const uint8_t *input,
    size_t bit_count,
    size_t *count,
    ReaperSeadlowReport *report,
    ReaperSeadlowError *error
);

#ifdef __cplusplus
}
#endif

#endif
