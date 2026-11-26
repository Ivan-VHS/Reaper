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

/* HMAC-SHA-256 helpers. Hex digests are 64 lowercase hexadecimal characters.
 * Verification compares digest bytes in constant time after format validation. */
int reaper_hmac_sha256_buffer(
    const void *key, size_t key_length,
    const void *data, size_t data_length,
    char output[65]
);
int reaper_hmac_sha256_verify(
    const void *key, size_t key_length,
    const void *data, size_t data_length,
    const char expected_digest[65]
);

/* Build the next deterministic audit hash-chain digest from a previous
 * 64-character SHA-256 digest and length-prefixed event fields. The host still
 * owns durable append, ordering, locking, access control and storage. */
int reaper_audit_chain_next(
    const char previous_digest[65],
    const char *event,
    const char *request_id,
    const char *repository_id,
    const char *branch,
    const char *revision,
    const char *path,
    const char *content_digest,
    const char *details,
    char output_digest[65]
);

#ifdef __cplusplus
}
#endif
#endif
