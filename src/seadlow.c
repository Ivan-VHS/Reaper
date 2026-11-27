#include "reaper/seadlow.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int fail(ReaperSeadlowError *error, const char *message) {
    if (error != NULL) {
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static void clear_report(ReaperSeadlowReport *report) {
    if (report != NULL) memset(report, 0, sizeof *report);
}

static int valid_operation(ReaperSeadlowOp operation) {
    return operation == REAPER_SEADLOW_AND ||
        operation == REAPER_SEADLOW_OR ||
        operation == REAPER_SEADLOW_XOR ||
        operation == REAPER_SEADLOW_NOT;
}

/* Return -1 if either address range cannot be represented without wrapping. */
static int ranges_overlap_sized(
    const void *left,
    size_t left_bytes,
    const void *right,
    size_t right_bytes
) {
    if (left_bytes == 0u || right_bytes == 0u) return 0;
    const uintptr_t left_start = (uintptr_t)left;
    const uintptr_t right_start = (uintptr_t)right;
    if ((uintmax_t)left_bytes > (uintmax_t)(UINTPTR_MAX - left_start) ||
        (uintmax_t)right_bytes > (uintmax_t)(UINTPTR_MAX - right_start)) {
        return -1;
    }
    const uintptr_t left_end = left_start + (uintptr_t)left_bytes;
    const uintptr_t right_end = right_start + (uintptr_t)right_bytes;
    return left_start < right_end && right_start < left_end;
}

/* Exact in-place transforms are allowed; all other intersections are not. */
static int ranges_overlap(const void *left, const void *right, size_t bytes) {
    if (bytes == 0u || left == right) return 0;
    return ranges_overlap_sized(left, bytes, right, bytes);
}

static uint64_t apply_word(
    ReaperSeadlowOp operation,
    uint64_t left,
    uint64_t right
) {
    switch (operation) {
    case REAPER_SEADLOW_AND: return left & right;
    case REAPER_SEADLOW_OR: return left | right;
    case REAPER_SEADLOW_XOR: return left ^ right;
    case REAPER_SEADLOW_NOT: return ~left;
    default: return 0u;
    }
}

static size_t popcount_word(uint64_t value);

static int transform_impl(
    ReaperSeadlowOp operation,
    uint8_t *output,
    const uint8_t *lhs,
    const uint8_t *rhs,
    size_t bit_count,
    size_t *population_count,
    ReaperSeadlowReport *report,
    ReaperSeadlowError *error
) {
    clear_report(report);
    if (error != NULL) error->message[0] = '\0';
    if (!valid_operation(operation)) {
        return fail(error, "unknown Seadlow bitwise operation");
    }
    if (bit_count == 0u) {
        if (population_count != NULL) *population_count = 0u;
        return 1;
    }
    if (output == NULL || lhs == NULL ||
        (operation != REAPER_SEADLOW_NOT && rhs == NULL)) {
        return fail(error, "output and required input buffers are mandatory");
    }

    const size_t byte_count = bit_count / 8u +
        (bit_count % 8u != 0u ? 1u : 0u);
    if (population_count != NULL) {
        const int output_overlap = ranges_overlap_sized(
            population_count, sizeof *population_count, output, byte_count
        );
        const int left_overlap = ranges_overlap_sized(
            population_count, sizeof *population_count, lhs, byte_count
        );
        const int right_overlap = operation == REAPER_SEADLOW_NOT ? 0 :
            ranges_overlap_sized(population_count, sizeof *population_count,
                                 rhs, byte_count);
        if (output_overlap != 0 || left_overlap != 0 || right_overlap != 0) {
            return fail(error,
                "population count storage must not overlap bit buffers");
        }
    }
    if (operation != REAPER_SEADLOW_NOT) {
        const int left_overlap = ranges_overlap(output, lhs, byte_count);
        const int right_overlap = ranges_overlap(output, rhs, byte_count);
        if (left_overlap < 0 || right_overlap < 0) {
            return fail(error, "buffer address range overflow");
        }
        if ((output != lhs && left_overlap != 0) ||
            (output != rhs && right_overlap != 0)) {
            return fail(error, "partial output/input buffer overlap is not supported");
        }
    } else {
        const int overlap = ranges_overlap(output, lhs, byte_count);
        if (overlap < 0) return fail(error, "buffer address range overflow");
        if (output != lhs && overlap != 0) {
            return fail(error, "partial output/input buffer overlap is not supported");
        }
    }

    const size_t word_count = bit_count / 64u;
    size_t population_total = 0u;
    size_t word_index = 0u;
    while (word_index < word_count) {
        size_t tile_end = word_index + REAPER_SEADLOW_TILE_WORDS;
        if (tile_end < word_index || tile_end > word_count) {
            tile_end = word_count;
        }
        for (; word_index < tile_end; ++word_index) {
            const size_t offset = word_index * sizeof(uint64_t);
            uint64_t left = 0u, right = 0u;
            memcpy(&left, lhs + offset, sizeof left);
            if (operation != REAPER_SEADLOW_NOT) {
                memcpy(&right, rhs + offset, sizeof right);
            }
            const uint64_t value = apply_word(operation, left, right);
            memcpy(output + offset, &value, sizeof value);
            if (population_count != NULL) {
                population_total += popcount_word(value);
            }
        }
        if (report != NULL) ++report->tiles_processed;
    }

    const size_t full_bytes = bit_count / 8u;
    const size_t word_bytes = word_count * sizeof(uint64_t);
    for (size_t offset = word_bytes; offset < full_bytes; ++offset) {
        const uint8_t left = lhs[offset];
        uint8_t right = 0u;
        if (operation != REAPER_SEADLOW_NOT) right = rhs[offset];
        const uint8_t value = (uint8_t)apply_word(operation, left, right);
        output[offset] = value;
        if (population_count != NULL) {
            population_total += popcount_word((uint64_t)value);
        }
        if (report != NULL) ++report->tail_bytes_processed;
    }

    const size_t tail_bits = bit_count % 8u;
    if (tail_bits != 0u) {
        const uint8_t mask = (uint8_t)((1u << tail_bits) - 1u);
        const uint8_t left = lhs[full_bytes];
        uint8_t right = 0u;
        if (operation != REAPER_SEADLOW_NOT) right = rhs[full_bytes];
        const uint8_t value =
            (uint8_t)(apply_word(operation, left, right) & mask);
        output[full_bytes] = value;
        if (population_count != NULL) {
            population_total += popcount_word((uint64_t)value);
        }
        if (report != NULL) {
            ++report->tail_bytes_processed;
            report->tail_bits_processed = tail_bits;
        }
    }

    if (population_count != NULL) *population_count = population_total;
    if (report != NULL) {
        report->bits_processed = bit_count;
        report->words_processed = word_count;
    }
    return 1;
}

int reaper_seadlow_transform(
    ReaperSeadlowOp operation,
    uint8_t *output,
    const uint8_t *lhs,
    const uint8_t *rhs,
    size_t bit_count,
    ReaperSeadlowReport *report,
    ReaperSeadlowError *error
) {
    return transform_impl(operation, output, lhs, rhs, bit_count, NULL,
                          report, error);
}

int reaper_seadlow_transform_popcount(
    ReaperSeadlowOp operation,
    uint8_t *output,
    const uint8_t *lhs,
    const uint8_t *rhs,
    size_t bit_count,
    size_t *population_count,
    ReaperSeadlowReport *report,
    ReaperSeadlowError *error
) {
    if (population_count == NULL) {
        clear_report(report);
        if (error != NULL) error->message[0] = '\\0';
        return fail(error, "population count output is mandatory");
    }
    return transform_impl(operation, output, lhs, rhs, bit_count,
                          population_count, report, error);
}

static size_t popcount_word(uint64_t value) {
    value -= (value >> 1u) & UINT64_C(0x5555555555555555);
    value = (value & UINT64_C(0x3333333333333333)) +
        ((value >> 2u) & UINT64_C(0x3333333333333333));
    value = (value + (value >> 4u)) & UINT64_C(0x0F0F0F0F0F0F0F0F);
    value *= UINT64_C(0x0101010101010101);
    return (size_t)(value >> 56u);
}

int reaper_seadlow_popcount(
    const uint8_t *input,
    size_t bit_count,
    size_t *count,
    ReaperSeadlowReport *report,
    ReaperSeadlowError *error
) {
    clear_report(report);
    if (error != NULL) error->message[0] = '\0';
    if (count == NULL) return fail(error, "popcount output is mandatory");
    if (bit_count == 0u) {
        *count = 0u;
        return 1;
    }
    if (input == NULL) return fail(error, "input buffer is mandatory");

    const size_t word_count = bit_count / 64u;
    size_t total = 0u;
    size_t word_index = 0u;
    while (word_index < word_count) {
        size_t tile_end = word_index + REAPER_SEADLOW_TILE_WORDS;
        if (tile_end < word_index || tile_end > word_count) {
            tile_end = word_count;
        }
        for (; word_index < tile_end; ++word_index) {
            uint64_t word = 0u;
            memcpy(&word, input + word_index * sizeof word, sizeof word);
            total += popcount_word(word);
        }
        if (report != NULL) ++report->tiles_processed;
    }

    const size_t full_bytes = bit_count / 8u;
    const size_t word_bytes = word_count * sizeof(uint64_t);
    for (size_t offset = word_bytes; offset < full_bytes; ++offset) {
        total += popcount_word((uint64_t)input[offset]);
        if (report != NULL) ++report->tail_bytes_processed;
    }
    const size_t tail_bits = bit_count % 8u;
    if (tail_bits != 0u) {
        const uint8_t mask = (uint8_t)((1u << tail_bits) - 1u);
        total += popcount_word((uint64_t)(input[full_bytes] & mask));
        if (report != NULL) {
            ++report->tail_bytes_processed;
            report->tail_bits_processed = tail_bits;
        }
    }

    *count = total;
    if (report != NULL) {
        report->bits_processed = bit_count;
        report->words_processed = word_count;
    }
    return 1;
}
