#ifndef REAPER_SHA256_H
#define REAPER_SHA256_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t state[8];
    uint64_t bit_count;
    uint8_t block[64];
    size_t block_length;
} ReaperSha256Context;

void reaper_sha256_init(ReaperSha256Context *context);
int reaper_sha256_update(ReaperSha256Context *context, const void *data, size_t length);
void reaper_sha256_final(ReaperSha256Context *context, uint8_t digest[32]);
void reaper_sha256_hex(const uint8_t digest[32], char output[65]);
int reaper_sha256_buffer(const void *data, size_t length, char output[65]);

#ifdef __cplusplus
}
#endif
#endif
