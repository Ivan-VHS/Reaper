#ifndef REAPER_BACKEND_H
#define REAPER_BACKEND_H

#include "reaper/import.h"

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_HOST_C17_BACKEND_ID "reaper.host-c17.source.v1"
#define REAPER_HOST_C17_ABI_ID "host-c17-compiler-delegated"

typedef enum {
    REAPER_BACKEND_QUALIFICATION_NONE = 0,
    REAPER_BACKEND_QUALIFICATION_STRUCTURAL = 1,
    REAPER_BACKEND_QUALIFICATION_SEMANTIC = 2,
    REAPER_BACKEND_QUALIFICATION_HOST_ABI = 3,
    REAPER_BACKEND_QUALIFICATION_QUALIFIED = 4
} ReaperBackendQualificationLevel;

enum {
    REAPER_BACKEND_EVIDENCE_SOURCE_GOLDEN = UINT32_C(1) << 0,
    REAPER_BACKEND_EVIDENCE_COMPILED_FIXTURE = UINT32_C(1) << 1,
    REAPER_BACKEND_EVIDENCE_EXECUTED_FIXTURE = UINT32_C(1) << 2,
    REAPER_BACKEND_EVIDENCE_IR_PARITY = UINT32_C(1) << 3,
    REAPER_BACKEND_EVIDENCE_SPAN_VERIFIED = UINT32_C(1) << 4
};

typedef struct {
    const char *backend_id;
    const char *abi_id;
    uint32_t schema_version;
    uint32_t supported_opcodes;
    uint32_t supported_effects;
    uint32_t source_emission_only;
} ReaperBackendManifest;

typedef struct {
    char backend_id[48];
    char abi_id[48];
    uint32_t evidence;
    ReaperBackendQualificationLevel level;
    uint32_t native_machine_code;
    uint32_t abi_delegated_to_host_compiler;
    char message[160];
} ReaperBackendQualification;

const ReaperBackendManifest *reaper_backend_host_c17_manifest(void);
ReaperImportStatus reaper_backend_host_c17_emit(
    const ReaperCanonicalTypedModule *module,
    char *output,
    size_t output_capacity,
    size_t *output_bytes,
    ReaperImportError *error
);

/* Evidence is supplied by a test/qualification harness, never inferred here. */
void reaper_backend_qualification_evaluate(
    uint32_t evidence,
    ReaperBackendQualification *out
);

#ifdef __cplusplus
}
#endif
#endif
