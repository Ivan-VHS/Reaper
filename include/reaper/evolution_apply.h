#ifndef REAPER_EVOLUTION_APPLY_H
#define REAPER_EVOLUTION_APPLY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_EVOLUTION_APPLY_ABI_VERSION UINT32_C(1)
#define REAPER_EVOLUTION_APPLY_MAX_FILES 64u
#define REAPER_EVOLUTION_APPLY_MAX_CHECKS 32u
#define REAPER_EVOLUTION_APPLY_MAX_PATH 512u
#define REAPER_EVOLUTION_APPLY_MAX_REPORT 4096u
#define REAPER_EVOLUTION_APPLY_MAX_FILE_BYTES (4u * 1024u * 1024u)
#define REAPER_EVOLUTION_APPLY_MAX_TOTAL_BYTES (16u * 1024u * 1024u)

typedef enum {
    REAPER_APPLY_OK = 0,
    REAPER_APPLY_INVALID_ARGUMENT,
    REAPER_APPLY_HOST_UNTRUSTED,
    REAPER_APPLY_GRANT_DENIED,
    REAPER_APPLY_REVISION_DENIED,
    REAPER_APPLY_PATH_DENIED,
    REAPER_APPLY_FINGERPRINT_MISMATCH,
    REAPER_APPLY_LIMIT_EXCEEDED,
    REAPER_APPLY_READ_FAILED,
    REAPER_APPLY_STAGE_FAILED,
    REAPER_APPLY_CHECKS_FAILED,
    REAPER_APPLY_COMMIT_FAILED,
    REAPER_APPLY_AUDIT_FAILED,
    REAPER_APPLY_ROLLBACK_FAILED
} ReaperApplyStatus;

enum {
    REAPER_APPLY_HOST_PATH_CONFINED       = UINT32_C(1) << 0,
    REAPER_APPLY_HOST_NO_SYMLINKS         = UINT32_C(1) << 1,
    REAPER_APPLY_HOST_ATOMIC_REPLACE      = UINT32_C(1) << 2,
    REAPER_APPLY_HOST_REVISION_VERIFIED   = UINT32_C(1) << 3,
    REAPER_APPLY_HOST_GRANT_CRYPTOGRAPHIC = UINT32_C(1) << 4,
    REAPER_APPLY_HOST_SANDBOXED_CHECKS    = UINT32_C(1) << 5,
    REAPER_APPLY_HOST_NO_NETWORK          = UINT32_C(1) << 6,
    REAPER_APPLY_HOST_RESOURCE_LIMITED    = UINT32_C(1) << 7,
    REAPER_APPLY_HOST_DURABLE_AUDIT       = UINT32_C(1) << 8,
    REAPER_APPLY_HOST_ROLLBACK            = UINT32_C(1) << 9
};

#define REAPER_APPLY_HOST_REQUIRED_CAPABILITIES ( \
    REAPER_APPLY_HOST_PATH_CONFINED | REAPER_APPLY_HOST_NO_SYMLINKS | \
    REAPER_APPLY_HOST_ATOMIC_REPLACE | REAPER_APPLY_HOST_REVISION_VERIFIED | \
    REAPER_APPLY_HOST_GRANT_CRYPTOGRAPHIC | REAPER_APPLY_HOST_SANDBOXED_CHECKS | \
    REAPER_APPLY_HOST_NO_NETWORK | REAPER_APPLY_HOST_RESOURCE_LIMITED | \
    REAPER_APPLY_HOST_DURABLE_AUDIT | REAPER_APPLY_HOST_ROLLBACK)

typedef struct {
    uint32_t timeout_ms;
    uint64_t memory_limit_bytes;
    uint64_t output_limit_bytes;
    uint32_t process_limit;
    uint32_t file_limit;
} ReaperApplyLimits;

/*
 * Exact whole-file patch. expected_original_sha256 pins the source bytes.
 * replacement storage remains caller-owned for the duration of apply().
 */
typedef struct {
    const char *relative_path;
    char expected_original_sha256[65];
    const uint8_t *replacement;
    size_t replacement_size;
} ReaperSourcePatch;

typedef struct {
    const char *request_id;
    const char *repository_id;
    const char *default_branch;
    const char *base_branch;
    const char *target_branch;
    const char *revision_algorithm; /* "sha1" (40 hex) or "sha256" (64 hex). */
    const char *base_revision;
    const void *signed_grant;       /* Opaque, host-issued token; never interpreted here. */
    size_t signed_grant_size;
    uint64_t now_unix_seconds;
    const ReaperSourcePatch *patches;
    size_t patch_count;
    const char *const *check_ids;   /* Registered check IDs, never shell commands. */
    size_t check_count;
    ReaperApplyLimits limits;
} ReaperEvolutionApplyRequest;

typedef struct {
    uint32_t abi_version;
    uint32_t capabilities;
    void *context;

    /* Verifies signature, issuer, subject, repository, target branch, expiry,
     * revocation and repository.apply scope using a host-held trust key. */
    int (*verify_repository_grant)(
        void *context, const void *grant, size_t grant_size,
        const char *repository_id, const char *target_branch,
        uint64_t now_unix_seconds
    );
    /* Checks per-path source.write scope against the same signed grant. */
    int (*verify_path_scope)(
        void *context, const void *grant, size_t grant_size,
        const char *repository_id, const char *relative_path,
        uint64_t now_unix_seconds
    );
    /* Confirms the exact Git object and that base_branch resolves to it. */
    int (*verify_git_revision)(
        void *context, const char *repository_id, const char *base_branch,
        const char *algorithm, const char *revision
    );
    /* Resolves a repository-relative path under the granted root. The host
     * must reject traversal, symlink/reparse-point escapes and non-regular files. */
    int (*resolve_confined_path)(
        void *context, const char *repository_id, const char *relative_path,
        char *canonical_path, size_t canonical_path_capacity
    );
    /* Returns an owned byte buffer; release_buffer must free it. */
    int (*read_file)(
        void *context, const char *canonical_path,
        uint8_t **bytes, size_t *length
    );
    void (*release_buffer)(void *context, uint8_t *bytes);
    /* Creates a staged replacement and a rollback snapshot. It must re-check
     * expected_original_sha256 under the same OS-level file identity lock used
     * for replacement, preventing a read/stage TOCTOU race. */
    int (*stage_replace)(
        void *context, const char *canonical_path,
        const char *expected_original_sha256,
        const uint8_t *replacement, size_t replacement_size,
        void **staged_handle
    );
    /* Runs only registered check IDs over the staged workspace. The callback
     * must enforce sandbox, no-network and resource-limit capabilities. */
    int (*run_declared_checks)(
        void *context, void *const *staged_handles, size_t staged_count,
        const char *const *check_ids, size_t check_count,
        const ReaperApplyLimits *limits,
        char *report, size_t report_capacity
    );
    /* Commits one staged file atomically and retains a rollback snapshot. */
    int (*commit_staged)(
        void *context, void *staged_handle, void **rollback_handle
    );
    int (*rollback_committed)(void *context, void *rollback_handle);
    int (*discard_staged)(void *context, void *staged_handle);
    void (*release_rollback)(void *context, void *rollback_handle);
    /* Must append to a durable, tamper-evident, hash-chained journal. */
    int (*audit_append)(
        void *context, const char *event, const char *request_id,
        const char *repository_id, const char *branch,
        const char *revision, const char *path,
        const char *digest, const char *details
    );
} ReaperEvolutionApplyHost;

typedef struct {
    ReaperApplyStatus status;
    size_t applied_files;
    size_t rolled_back_files;
    char request_digest[65];
    char failed_path[REAPER_EVOLUTION_APPLY_MAX_PATH];
    char report[REAPER_EVOLUTION_APPLY_MAX_REPORT];
} ReaperEvolutionApplyResult;

/* Generates a deterministic exact-replacement patch and pins the original
 * file contents with SHA-256. Output patch references caller-owned buffers. */
int reaper_evolution_patch_generate(
    const char *relative_path,
    const uint8_t *original, size_t original_size,
    const uint8_t *replacement, size_t replacement_size,
    ReaperSourcePatch *patch,
    char *diagnostic, size_t diagnostic_capacity
);

/*
 * Apply transaction:
 * grant + revision + path checks -> fingerprint -> stage -> sandboxed checks
 * -> atomic commits -> durable audit. Any failed commit/audit rolls back in
 * reverse order. The engine performs no ambient filesystem/process/network I/O.
 */
ReaperEvolutionApplyResult reaper_evolution_apply(
    const ReaperEvolutionApplyHost *host,
    const ReaperEvolutionApplyRequest *request
);

const char *reaper_evolution_apply_status_name(ReaperApplyStatus status);

#ifdef __cplusplus
}
#endif
#endif
