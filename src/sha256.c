#include "reaper/sha256.h"

#include <string.h>

static const uint32_t constants[64] = {
    UINT32_C(0x428a2f98), UINT32_C(0x71374491), UINT32_C(0xb5c0fbcf),
    UINT32_C(0xe9b5dba5), UINT32_C(0x3956c25b), UINT32_C(0x59f111f1),
    UINT32_C(0x923f82a4), UINT32_C(0xab1c5ed5), UINT32_C(0xd807aa98),
    UINT32_C(0x12835b01), UINT32_C(0x243185be), UINT32_C(0x550c7dc3),
    UINT32_C(0x72be5d74), UINT32_C(0x80deb1fe), UINT32_C(0x9bdc06a7),
    UINT32_C(0xc19bf174), UINT32_C(0xe49b69c1), UINT32_C(0xefbe4786),
    UINT32_C(0x0fc19dc6), UINT32_C(0x240ca1cc), UINT32_C(0x2de92c6f),
    UINT32_C(0x4a7484aa), UINT32_C(0x5cb0a9dc), UINT32_C(0x76f988da),
    UINT32_C(0x983e5152), UINT32_C(0xa831c66d), UINT32_C(0xb00327c8),
    UINT32_C(0xbf597fc7), UINT32_C(0xc6e00bf3), UINT32_C(0xd5a79147),
    UINT32_C(0x06ca6351), UINT32_C(0x14292967), UINT32_C(0x27b70a85),
    UINT32_C(0x2e1b2138), UINT32_C(0x4d2c6dfc), UINT32_C(0x53380d13),
    UINT32_C(0x650a7354), UINT32_C(0x766a0abb), UINT32_C(0x81c2c92e),
    UINT32_C(0x92722c85), UINT32_C(0xa2bfe8a1), UINT32_C(0xa81a664b),
    UINT32_C(0xc24b8b70), UINT32_C(0xc76c51a3), UINT32_C(0xd192e819),
    UINT32_C(0xd6990624), UINT32_C(0xf40e3585), UINT32_C(0x106aa070),
    UINT32_C(0x19a4c116), UINT32_C(0x1e376c08), UINT32_C(0x2748774c),
    UINT32_C(0x34b0bcb5), UINT32_C(0x391c0cb3), UINT32_C(0x4ed8aa4a),
    UINT32_C(0x5b9cca4f), UINT32_C(0x682e6ff3), UINT32_C(0x748f82ee),
    UINT32_C(0x78a5636f), UINT32_C(0x84c87814), UINT32_C(0x8cc70208),
    UINT32_C(0x90befffa), UINT32_C(0xa4506ceb), UINT32_C(0xbef9a3f7),
    UINT32_C(0xc67178f2)
};

static uint32_t rotate_right(uint32_t value, unsigned count) {
    return (value >> count) | (value << (32u - count));
}

static uint32_t load_be32(const uint8_t *bytes) {
    return ((uint32_t)bytes[0] << 24u) |
           ((uint32_t)bytes[1] << 16u) |
           ((uint32_t)bytes[2] << 8u) |
           (uint32_t)bytes[3];
}

static void store_be32(uint8_t *bytes, uint32_t value) {
    bytes[0] = (uint8_t)(value >> 24u);
    bytes[1] = (uint8_t)(value >> 16u);
    bytes[2] = (uint8_t)(value >> 8u);
    bytes[3] = (uint8_t)value;
}

static void transform(ReaperSha256Context *context, const uint8_t block[64]) {
    uint32_t words[64];
    uint32_t a, b, c, d, e, f, g, h;
    size_t index;
    for (index = 0u; index < 16u; ++index) words[index] = load_be32(block + index * 4u);
    for (index = 16u; index < 64u; ++index) {
        const uint32_t x = words[index - 15u];
        const uint32_t y = words[index - 2u];
        const uint32_t s0 = rotate_right(x, 7u) ^ rotate_right(x, 18u) ^ (x >> 3u);
        const uint32_t s1 = rotate_right(y, 17u) ^ rotate_right(y, 19u) ^ (y >> 10u);
        words[index] = words[index - 16u] + s0 + words[index - 7u] + s1;
    }

    a = context->state[0]; b = context->state[1];
    c = context->state[2]; d = context->state[3];
    e = context->state[4]; f = context->state[5];
    g = context->state[6]; h = context->state[7];

    for (index = 0u; index < 64u; ++index) {
        const uint32_t sum1 = rotate_right(e, 6u) ^ rotate_right(e, 11u) ^ rotate_right(e, 25u);
        const uint32_t choice = (e & f) ^ ((~e) & g);
        const uint32_t temp1 = h + sum1 + choice + constants[index] + words[index];
        const uint32_t sum0 = rotate_right(a, 2u) ^ rotate_right(a, 13u) ^ rotate_right(a, 22u);
        const uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        const uint32_t temp2 = sum0 + majority;
        h = g; g = f; f = e; e = d + temp1;
        d = c; c = b; b = a; a = temp1 + temp2;
    }

    context->state[0] += a; context->state[1] += b;
    context->state[2] += c; context->state[3] += d;
    context->state[4] += e; context->state[5] += f;
    context->state[6] += g; context->state[7] += h;
}

void reaper_sha256_init(ReaperSha256Context *context) {
    if (context == NULL) return;
    context->state[0] = UINT32_C(0x6a09e667);
    context->state[1] = UINT32_C(0xbb67ae85);
    context->state[2] = UINT32_C(0x3c6ef372);
    context->state[3] = UINT32_C(0xa54ff53a);
    context->state[4] = UINT32_C(0x510e527f);
    context->state[5] = UINT32_C(0x9b05688c);
    context->state[6] = UINT32_C(0x1f83d9ab);
    context->state[7] = UINT32_C(0x5be0cd19);
    context->bit_count = 0u;
    context->block_length = 0u;
    memset(context->block, 0, sizeof context->block);
}

int reaper_sha256_update(ReaperSha256Context *context, const void *data, size_t length) {
    const uint8_t *input = (const uint8_t *)data;
    size_t offset = 0u;
    if (context == NULL || (length > 0u && data == NULL) ||
        length > (UINT64_MAX - context->bit_count) / 8u) return 0;
    context->bit_count += (uint64_t)length * UINT64_C(8);
    while (offset < length) {
        size_t amount = sizeof context->block - context->block_length;
        if (amount > length - offset) amount = length - offset;
        memcpy(context->block + context->block_length, input + offset, amount);
        context->block_length += amount;
        offset += amount;
        if (context->block_length == sizeof context->block) {
            transform(context, context->block);
            context->block_length = 0u;
        }
    }
    return 1;
}

void reaper_sha256_final(ReaperSha256Context *context, uint8_t digest[32]) {
    uint64_t bits;
    size_t index;
    if (context == NULL || digest == NULL) return;
    bits = context->bit_count;
    context->block[context->block_length++] = UINT8_C(0x80);
    if (context->block_length > 56u) {
        while (context->block_length < 64u) context->block[context->block_length++] = 0u;
        transform(context, context->block);
        context->block_length = 0u;
    }
    while (context->block_length < 56u) context->block[context->block_length++] = 0u;
    for (index = 0u; index < 8u; ++index)
        context->block[63u - index] = (uint8_t)(bits >> (index * 8u));
    transform(context, context->block);
    for (index = 0u; index < 8u; ++index) store_be32(digest + index * 4u, context->state[index]);
    memset(context, 0, sizeof *context);
}

void reaper_sha256_hex(const uint8_t digest[32], char output[65]) {
    static const char digits[] = "0123456789abcdef";
    size_t index;
    if (digest == NULL || output == NULL) return;
    for (index = 0u; index < 32u; ++index) {
        output[index * 2u] = digits[digest[index] >> 4u];
        output[index * 2u + 1u] = digits[digest[index] & UINT8_C(0x0f)];
    }
    output[64] = '\0';
}

int reaper_sha256_buffer(const void *data, size_t length, char output[65]) {
    ReaperSha256Context context;
    uint8_t digest[32];
    if (output == NULL || (length > 0u && data == NULL)) return 0;
    reaper_sha256_init(&context);
    if (!reaper_sha256_update(&context, data, length)) return 0;
    reaper_sha256_final(&context, digest);
    reaper_sha256_hex(digest, output);
    return 1;
}
