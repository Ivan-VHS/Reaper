#ifndef REAPER_IMPORT_H
#define REAPER_IMPORT_H

#include "reaper/ir.h"

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_IMPORT_ABI_VERSION UINT32_C(0x00010000)
#define REAPER_IMPORT_MODULE_ID_CAPACITY 64u
#define REAPER_SOURCE_DIGEST_BYTES 32u

typedef enum {
    REAPER_IMPORT_OK = 0,
    REAPER_IMPORT_INVALID_ARGUMENT,
    REAPER_IMPORT_STALE_GENERATION,
    REAPER_IMPORT_DIGEST_MISMATCH,
    REAPER_IMPORT_PARSE_ERROR,
    REAPER_IMPORT_LOWERING_ERROR,
    REAPER_IMPORT_VERIFICATION_ERROR,
    REAPER_IMPORT_CAPACITY_EXCEEDED,
    REAPER_IMPORT_UNSUPPORTED
} ReaperImportStatus;

typedef enum {
    REAPER_TYPED_I64 = 1,
    REAPER_TYPED_UNIT = 2
} ReaperTypedType;

typedef enum {
    REAPER_EFFECT_PURE = UINT32_C(1) << 0,
    REAPER_EFFECT_CONTROL = UINT32_C(1) << 1,
    REAPER_EFFECT_MEMORY_READ = UINT32_C(1) << 2,
    REAPER_EFFECT_MEMORY_WRITE = UINT32_C(1) << 3,
    REAPER_EFFECT_MMIO_READ = UINT32_C(1) << 4,
    REAPER_EFFECT_MMIO_WRITE = UINT32_C(1) << 5,
    REAPER_EFFECT_DMA_TRANSFER = UINT32_C(1) << 6,
    REAPER_EFFECT_PRIVILEGED = UINT32_C(1) << 7,
    REAPER_EFFECT_UNSAFE = UINT32_C(1) << 8
} ReaperEffect;

typedef enum {
    REAPER_OWNERSHIP_NONE = 0,
    REAPER_OWNERSHIP_BORROWED,
    REAPER_OWNERSHIP_OWNED,
    REAPER_OWNERSHIP_MOVED,
    REAPER_OWNERSHIP_SHARED
} ReaperOwnership;

typedef struct {
    char module_id[REAPER_IMPORT_MODULE_ID_CAPACITY];
    uint64_t generation;
    uint64_t expected_generation;
    uint8_t expected_source_digest[REAPER_SOURCE_DIGEST_BYTES];
} ReaperSourceImportManifest;

typedef struct {
    ReaperIrNode instruction;
    ReaperTypedType type;
    uint32_t effects;
    ReaperOwnership ownership;
    uint64_t source_start_byte;
    uint64_t source_end_byte;
} ReaperTypedInstruction;

typedef struct {
    uint32_t schema_version;
    char module_id[REAPER_IMPORT_MODULE_ID_CAPACITY];
    uint64_t generation;
    uint64_t source_bytes;
    uint8_t source_digest[REAPER_SOURCE_DIGEST_BYTES];
    ReaperTypedInstruction *nodes;
    size_t length;
} ReaperCanonicalTypedModule;

typedef struct {
    ReaperImportStatus status;
    size_t instruction_index;
    uint64_t expected_generation;
    uint64_t actual_generation;
    char message[192];
} ReaperImportError;

/* SHA-256 over an exact byte sequence; no NUL terminator is included implicitly. */
void reaper_source_sha256(const void *data, size_t length,
                          uint8_t digest[REAPER_SOURCE_DIGEST_BYTES]);
const char *reaper_import_status_name(ReaperImportStatus status);

/*
 * Import the currently supported native scalar-expression subset.
 * Caller owns output storage; the module is published only after digest,
 * generation, source spans, typing, effects, ownership and IR verification pass.
 */
ReaperImportStatus reaper_import_expression(
    const char *source,
    size_t source_bytes,
    const ReaperSourceImportManifest *manifest,
    ReaperTypedInstruction *storage,
    size_t storage_capacity,
    ReaperCanonicalTypedModule *out,
    ReaperImportError *error
);

ReaperImportStatus reaper_canonical_typed_module_verify(
    const ReaperCanonicalTypedModule *module,
    ReaperImportError *error
);

#ifdef __cplusplus
}
#endif
#endif
