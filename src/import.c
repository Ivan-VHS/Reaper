#include "reaper/import.h"

#include "reaper/ast.h"
#include "reaper/lexer.h"
#include "reaper/lower.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint32_t state[8];
    uint64_t bit_count;
    uint8_t block[64];
    size_t used;
} ReaperSha256;

static uint32_t rotate_right(uint32_t value, unsigned bits) {
    return (value >> bits) | (value << (32u - bits));
}

static uint32_t load_be32(const uint8_t *bytes) {
    return ((uint32_t)bytes[0] << 24) | ((uint32_t)bytes[1] << 16) |
           ((uint32_t)bytes[2] << 8) | (uint32_t)bytes[3];
}

static void store_be32(uint8_t *bytes, uint32_t value) {
    bytes[0] = (uint8_t)(value >> 24);
    bytes[1] = (uint8_t)(value >> 16);
    bytes[2] = (uint8_t)(value >> 8);
    bytes[3] = (uint8_t)value;
}

static void sha256_transform(ReaperSha256 *sha, const uint8_t block[64]) {
    static const uint32_t constants[64] = {
        0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,
        0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
        0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,
        0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
        0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,
        0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
        0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,
        0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
        0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,
        0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
        0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,
        0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
        0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,
        0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
        0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,
        0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
    };
    uint32_t words[64];
    uint32_t a, b, c, d, e, f, g, h;
    size_t i;
    for (i = 0u; i < 16u; ++i) words[i] = load_be32(block + i * 4u);
    for (i = 16u; i < 64u; ++i) {
        uint32_t s0 = rotate_right(words[i - 15u], 7u) ^
                      rotate_right(words[i - 15u], 18u) ^
                      (words[i - 15u] >> 3u);
        uint32_t s1 = rotate_right(words[i - 2u], 17u) ^
                      rotate_right(words[i - 2u], 19u) ^
                      (words[i - 2u] >> 10u);
        words[i] = words[i - 16u] + s0 + words[i - 7u] + s1;
    }
    a = sha->state[0]; b = sha->state[1]; c = sha->state[2]; d = sha->state[3];
    e = sha->state[4]; f = sha->state[5]; g = sha->state[6]; h = sha->state[7];
    for (i = 0u; i < 64u; ++i) {
        uint32_t sum1 = rotate_right(e, 6u) ^ rotate_right(e, 11u) ^
                        rotate_right(e, 25u);
        uint32_t choose = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + sum1 + choose + constants[i] + words[i];
        uint32_t sum0 = rotate_right(a, 2u) ^ rotate_right(a, 13u) ^
                        rotate_right(a, 22u);
        uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = sum0 + majority;
        h = g; g = f; f = e; e = d + temp1;
        d = c; c = b; b = a; a = temp1 + temp2;
    }
    sha->state[0] += a; sha->state[1] += b; sha->state[2] += c;
    sha->state[3] += d; sha->state[4] += e; sha->state[5] += f;
    sha->state[6] += g; sha->state[7] += h;
}

static void sha256_init(ReaperSha256 *sha) {
    static const uint32_t initial[8] = {
        0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,
        0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u
    };
    memcpy(sha->state, initial, sizeof(initial));
    sha->bit_count = 0u;
    sha->used = 0u;
}

static void sha256_update(ReaperSha256 *sha, const uint8_t *data, size_t length) {
    size_t offset = 0u;
    while (offset < length) {
        size_t available = sizeof(sha->block) - sha->used;
        size_t chunk = length - offset < available ? length - offset : available;
        memcpy(sha->block + sha->used, data + offset, chunk);
        sha->used += chunk;
        offset += chunk;
        if (sha->used == sizeof(sha->block)) {
            sha256_transform(sha, sha->block);
            sha->bit_count += UINT64_C(512);
            sha->used = 0u;
        }
    }
}

void reaper_source_sha256(const void *data, size_t length,
                          uint8_t digest[REAPER_SOURCE_DIGEST_BYTES]) {
    ReaperSha256 sha;
    uint64_t total_bits;
    size_t i;
    if (digest == NULL || (data == NULL && length != 0u)) return;
    sha256_init(&sha);
    sha256_update(&sha, (const uint8_t *)data, length);
    total_bits = (uint64_t)length * UINT64_C(8);
    sha.block[sha.used++] = UINT8_C(0x80);
    if (sha.used > 56u) {
        while (sha.used < 64u) sha.block[sha.used++] = 0u;
        sha256_transform(&sha, sha.block);
        sha.used = 0u;
    }
    while (sha.used < 56u) sha.block[sha.used++] = 0u;
    for (i = 0u; i < 8u; ++i)
        sha.block[63u - i] = (uint8_t)(total_bits >> (i * 8u));
    sha256_transform(&sha, sha.block);
    for (i = 0u; i < 8u; ++i) store_be32(digest + i * 4u, sha.state[i]);
}

static ReaperImportStatus import_fail(ReaperImportError *error,
                                      ReaperImportStatus status,
                                      size_t index, const char *message) {
    if (error != NULL) {
        error->status = status;
        error->instruction_index = index;
        (void)snprintf(error->message, sizeof(error->message), "%s", message);
    }
    return status;
}

const char *reaper_import_status_name(ReaperImportStatus status) {
    static const char *const names[] = {
        "ok", "invalid_argument", "stale_generation", "digest_mismatch",
        "parse_error", "lowering_error", "verification_error",
        "capacity_exceeded", "unsupported"
    };
    return (unsigned)status < sizeof(names) / sizeof(names[0])
        ? names[(unsigned)status] : "unknown";
}

static uint32_t expected_effect(ReaperIrOpcode opcode) {
    return opcode == REAPER_IR_OP_RETURN
        ? REAPER_EFFECT_CONTROL : REAPER_EFFECT_PURE;
}

static ReaperTypedType typed_type(ReaperIrType type) {
    if (type == REAPER_IR_TYPE_I64) return REAPER_TYPED_I64;
    if (type == REAPER_IR_TYPE_UNIT) return REAPER_TYPED_UNIT;
    return (ReaperTypedType)0;
}

ReaperImportStatus reaper_canonical_typed_module_verify(
    const ReaperCanonicalTypedModule *module, ReaperImportError *error) {
    ReaperIrNode *raw;
    ReaperIrModule ir;
    ReaperIrError ir_error;
    size_t i;
    if (error != NULL) memset(error, 0, sizeof(*error));
    if (module == NULL || module->schema_version != REAPER_IMPORT_ABI_VERSION ||
        module->module_id[0] == '\0' || module->generation == 0u ||
        module->source_bytes == 0u || module->nodes == NULL ||
        module->length == 0u ||
        memchr(module->module_id, '\0', sizeof(module->module_id)) == NULL)
        return import_fail(error, REAPER_IMPORT_INVALID_ARGUMENT, 0u,
                           "canonical typed module header is invalid");
    if (module->length > SIZE_MAX / sizeof(*raw))
        return import_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, 0u,
                           "canonical typed module is too large");
    raw = (ReaperIrNode *)malloc(module->length * sizeof(*raw));
    if (raw == NULL)
        return import_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, 0u,
                           "cannot allocate verifier scratch storage");
    for (i = 0u; i < module->length; ++i) {
        const ReaperTypedInstruction *node = &module->nodes[i];
        if (node->source_start_byte > node->source_end_byte ||
            node->source_end_byte > module->source_bytes ||
            node->source_start_byte != node->instruction.source_start_byte ||
            node->source_end_byte != node->instruction.source_end_byte ||
            node->type != typed_type(node->instruction.type) ||
            node->effects != expected_effect(node->instruction.opcode) ||
            node->ownership != REAPER_OWNERSHIP_NONE) {
            free(raw);
            return import_fail(error, REAPER_IMPORT_VERIFICATION_ERROR, i,
                               "typed IR metadata, effect, ownership, or source span is invalid");
        }
        raw[i] = node->instruction;
    }
    ir.nodes = raw;
    ir.length = module->length;
    if (!reaper_ir_verify(&ir, &ir_error)) {
        free(raw);
        return import_fail(error, REAPER_IMPORT_VERIFICATION_ERROR,
                           ir_error.node_index, ir_error.message);
    }
    free(raw);
    if (error != NULL) error->status = REAPER_IMPORT_OK;
    return REAPER_IMPORT_OK;
}

ReaperImportStatus reaper_import_expression(
    const char *source, size_t source_bytes,
    const ReaperSourceImportManifest *manifest,
    ReaperTypedInstruction *storage, size_t storage_capacity,
    ReaperCanonicalTypedModule *out, ReaperImportError *error) {
    char *source_copy = NULL;
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error;
    ReaperAst ast;
    ReaperParseError parse_error;
    ReaperIrNode *raw = NULL;
    ReaperTypedInstruction *staged = NULL;
    ReaperIrError ir_error;
    ReaperIrModule ir;
    uint8_t digest[REAPER_SOURCE_DIGEST_BYTES];
    size_t length = 0u, i;
    ReaperImportStatus status = REAPER_IMPORT_INVALID_ARGUMENT;
    if (error != NULL) memset(error, 0, sizeof(*error));
    if (out != NULL) memset(out, 0, sizeof(*out));
    if (source == NULL || source_bytes == 0u ||
        source_bytes > REAPER_MAX_SOURCE_BYTES || manifest == NULL ||
        storage == NULL || out == NULL || storage_capacity == 0u ||
        storage_capacity > SIZE_MAX / sizeof(*raw) ||
        memchr(source, '\0', source_bytes) != NULL ||
        manifest->module_id[0] == '\0' ||
        memchr(manifest->module_id, '\0', sizeof(manifest->module_id)) == NULL) {
        return import_fail(error, REAPER_IMPORT_INVALID_ARGUMENT, 0u,
                           "source, manifest, output storage and bounded size are required");
    }
    if (manifest->generation == 0u ||
        manifest->generation != manifest->expected_generation) {
        if (error != NULL) {
            error->expected_generation = manifest->expected_generation;
            error->actual_generation = manifest->generation;
        }
        return import_fail(error, REAPER_IMPORT_STALE_GENERATION, 0u,
                           "source module generation does not match the expected generation");
    }
    reaper_source_sha256(source, source_bytes, digest);
    if (memcmp(digest, manifest->expected_source_digest, sizeof(digest)) != 0)
        return import_fail(error, REAPER_IMPORT_DIGEST_MISMATCH, 0u,
                           "source SHA-256 does not match the import manifest");

    source_copy = (char *)malloc(source_bytes + 1u);
    raw = (ReaperIrNode *)calloc(storage_capacity, sizeof(*raw));
    staged = (ReaperTypedInstruction *)calloc(storage_capacity, sizeof(*staged));
    if (source_copy == NULL || raw == NULL || staged == NULL) {
        status = import_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, 0u,
                             "cannot allocate bounded import scratch storage");
        goto cleanup;
    }
    memcpy(source_copy, source, source_bytes);
    source_copy[source_bytes] = '\0';

    if (!reaper_lex(source_copy, &tokens, &lex_error)) {
        status = import_fail(error, REAPER_IMPORT_PARSE_ERROR, 0u, lex_error.message);
        goto cleanup;
    }
    if (!reaper_parse_expression(&tokens, &ast, &parse_error)) {
        status = import_fail(error, REAPER_IMPORT_PARSE_ERROR, 0u, parse_error.message);
        goto cleanup;
    }
    if (!reaper_lower_ast_to_ir(&ast, raw, storage_capacity,
                                &length, &ir_error)) {
        status = import_fail(error, REAPER_IMPORT_LOWERING_ERROR,
                             ir_error.node_index, ir_error.message);
        reaper_ast_free(&ast);
        goto cleanup;
    }
    reaper_ast_free(&ast);
    reaper_tokens_free(&tokens);
    if (length > storage_capacity) {
        status = import_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, 0u,
                             "typed IR output capacity is too small");
        goto cleanup;
    }
    ir.nodes = raw;
    ir.length = length;
    if (!reaper_ir_verify(&ir, &ir_error)) {
        status = import_fail(error, REAPER_IMPORT_VERIFICATION_ERROR,
                             ir_error.node_index, ir_error.message);
        goto cleanup;
    }
    for (i = 0u; i < length; ++i) {
        if (raw[i].source_start_byte > raw[i].source_end_byte ||
            raw[i].source_end_byte > source_bytes) {
            status = import_fail(error, REAPER_IMPORT_VERIFICATION_ERROR, i,
                                 "IR source byte span escapes the imported source");
            goto cleanup;
        }
        staged[i].instruction = raw[i];
        staged[i].type = typed_type(raw[i].type);
        staged[i].effects = expected_effect(raw[i].opcode);
        staged[i].ownership = REAPER_OWNERSHIP_NONE;
        staged[i].source_start_byte = raw[i].source_start_byte;
        staged[i].source_end_byte = raw[i].source_end_byte;
        if (staged[i].type == (ReaperTypedType)0) {
            status = import_fail(error, REAPER_IMPORT_UNSUPPORTED, i,
                                 "IR type is not represented by the typed adapter");
            goto cleanup;
        }
    }
    memcpy(storage, staged, length * sizeof(*storage));
    out->schema_version = REAPER_IMPORT_ABI_VERSION;
    (void)snprintf(out->module_id, sizeof(out->module_id), "%s", manifest->module_id);
    out->generation = manifest->generation;
    out->source_bytes = source_bytes;
    memcpy(out->source_digest, digest, sizeof(digest));
    out->nodes = storage;
    out->length = length;
    status = reaper_canonical_typed_module_verify(out, error);

cleanup:
    if (tokens.items != NULL) reaper_tokens_free(&tokens);
    free(source_copy);
    free(raw);
    free(staged);
    if (status != REAPER_IMPORT_OK) memset(out, 0, sizeof(*out));
    return status;
}
