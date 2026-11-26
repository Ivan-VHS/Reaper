#ifndef REAPER_EVOLUTION_APPLY_H
#define REAPER_EVOLUTION_APPLY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_EVOLUTION_APPLY_ABI_VERSION UINT32_C(2)
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
    REAPER_APPLY_WORKSPACE_FAILED,
    REAPER_APPLY_READ_FAILED,
    REAPER_APPLY_STAGE_FAILED,
    REAPER_APPLY_CHECKS_FAILED,
    REAPER_APPLY_COMMIT_FAILED,
    REAPER_APPLY_PUBLISH_FAILED,
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
    REAPER_APPLY_HOST_ROLLBACK            = UINT32_C(1) << 9,
    REAPER_APPLY_HOST_RECOVERY_STORE      = UINT32_C(1) << 10,
    REAPER_APPLY_HOST_ISOLATED_WORKSPACE  = UINT32_C(1) << 11,
    REAPER_APPLY_HOST_TOPIC_BRANCH_PUBLISH= UINT32_C(1) << 12,
    REAPER_APPLY_HOST_CONDITIONAL_REF_CAS = UINT32_C(1) << 13
};

#define REAPER_APPLY_HOST_REQUIRED_CAPABILITIES ( \
    REAPER_APPLY_HOST_PATH_CONFINED | REAPER_APPLY_HOST_NO_SYMLINKS | \
    REAPER_APPLY_HOST_ATOMIC_REPLACE | REAPER_APPLY_HOST_REVISION_VERIFIED | \
    REAPER_APPLY_HOST_GRANT_CRYPTOGRAPHIC | REAPER_APPLY_HOST_SANDBOXED_CHECKS | \
    REAPER_APPLY_HOST_NO_NETWORK | REAPER_APPLY_HOST_RESOURCE_LIMITED | \
    REAPER_APPLY_HOST_DURABLE_AUDIT | REAPER_APPLY_HOST_ROLLBACK | \
    REAPER_APPLY_HOST_RECOVERY_STORE | REAPER_APPLY_HOST_ISOLATED_WORKSPACE | \
    REAPER_APPLY_HOST_TOPIC_BRANCH_PUBLISH | REAPER_APPLY_HOST_CONDITIONAL_REF_CAS)

typedef struct {
    uint32_t timeout_ms;
    uint64_t memory_limit_bytes;
    uint64_t output_limit_bytes;
    uint32_t process_limit;
    uint32_t file_limit;
} ReaperApplyLimits;

/* Exact whole-file patch. expected_original_sha256 pins original source bytes.
 * Replacement storage remains caller-owned for the duration of apply(). */
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
    const void *signed_grant;       /* Opaque, host-issued token; never parsed by this engine. */
    size_t signed_grant_size;
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

    /* Returns trusted host wall-clock time. Guest-supplied timestamps are
     * never accepted for not-before, expiry or revocation decisions. */
    int (*trusted_time_unix_seconds)(void *context, uint64_t *now_unix_seconds);
    /* Verifies signature, issuer, subject, repository, target branch, expiry,
     * revocation and repository.apply scope using a host-held trust key and
     * the trusted timestamp above. */
    int (*verify_repository_grant)(
        void *context, const void *grant, size_t grant_size,
        const char *repository_id, const char *target_branch,
        const char *request_digest,
        uint64_t now_unix_seconds
    );
    /* Checks per-path source.write scope against the same signed grant. */
    int (*verify_path_scope)(
        void *context, const void *grant, size_t grant_size,
        const char *repository_id, const char *relative_path,
        uint64_t now_unix_seconds
    );
    /* Confirms base_branch resolves to the exact Git object named by revision. */
    int (*verify_git_revision)(
        void *context, const char *repository_id, const char *base_branch,
        const char *algorithm, const char *revision
    );
    /* Creates a fresh isolated workspace rooted at that immutable Git object.
     * Must reject existing target refs, default-branch aliases, shared mutable
     * checkouts and any path outside the repository sandbox. */
    int (*begin_workspace)(
        void *context, const char *repository_id,
        const char *base_branch, const char *algorithm, const char *revision,
        const char *target_branch, const ReaperApplyLimits *limits,
        void **workspace
    );
    /* Resolves a repository-relative path inside this exact workspace.
     * Rejects traversal, symlink/reparse-point escapes and non-regular files.
     * The returned canonical form must be stable for the underlying file
     * identity (including case-folding on case-insensitive filesystems). */
    int (*resolve_confined_path)(
        void *context, void *workspace, const char *relative_path,
        char *canonical_path, size_t canonical_path_capacity
    );
    int (*read_file)(
        void *context, void *workspace, const char *canonical_path,
        uint8_t **bytes, size_t *length
    );
    void (*release_buffer)(void *context, uint8_t *bytes);
    /* Stages a replacement in the isolated workspace and re-checks the
     * original digest under the same file-identity lock used for replacement.
     * On successful commit, the stage handle is consumed. On failed commit,
     * it remains valid for discard_staged. */
    int (*stage_replace)(
        void *context, void *workspace, const char *canonical_path,
        const char *expected_original_sha256,
        const uint8_t *replacement, size_t replacement_size,
        void **staged_handle
    );
    /* Runs only registered checks against the fully materialized isolated
     * workspace. The callback must enforce no-network and the declared
     * CPU/memory/output/process/file limits. */
    int (*run_declared_checks)(
        void *context, void *workspace,
        const char *const *check_ids, size_t check_count,
        const ReaperApplyLimits *limits,
        char *report, size_t report_capacity
    );
    /* Commits a staged replacement only within the isolated workspace and
     * returns a rollback snapshot independent from the stage handle. A
     * successful commit consumes staged_handle. A failed commit leaves
     * staged_handle valid for discard_staged and may return a snapshot if
     * partial materialization occurred. This must not update Git refs. */
    int (*commit_staged)(
        void *context, void *workspace,
        void *staged_handle, void **rollback_handle
    );
    int (*rollback_committed)(void *context, void *workspace, void *rollback_handle);
    int (*discard_staged)(void *context, void *workspace, void *staged_handle);

    /* Creates a Git tree/commit from the verified workspace, with base_revision
     * as the sole parent, then creates target_branch using an atomic
     * create-if-absent ref update. Must never force-update a branch. Returns
     * a 40- or 64-hex commit ID and a conditional ref rollback handle. */
    int (*publish_topic_branch)(
        void *context, void *workspace, const char *target_branch,
        const char *algorithm, const char *base_revision,
        char published_revision[65], void **published_rollback
    );
    /* Removes only the target ref created by this request and only while it
     * still points to the published_revision recorded by the host handle. */
    int (*rollback_topic_branch)(void *context, void *published_rollback);
    void (*release_rollback)(void *context, void *rollback_handle);
    /* Transfers a failed rollback handle to a durable recovery queue. */
    int (*preserve_failed_rollback)(
        void *context, void *rollback_handle, const char *request_id,
        const char *target_branch, const char *relative_path
    );
    /* Releases the ephemeral workspace. It must not delete a published branch. */
    void (*end_workspace)(void *context, void *workspace);
    /* Appends to a durable, tamper-evident, hash-chained journal. */
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
    char published_branch[REAPER_EVOLUTION_APPLY_MAX_PATH];
    char published_revision[65];
    char failed_path[REAPER_EVOLUTION_APPLY_MAX_PATH];
    char report[REAPER_EVOLUTION_APPLY_MAX_REPORT];
} ReaperEvolutionApplyResult;

/* Generates a deterministic exact-replacement patch and pins the original
 * bytes with SHA-256. Output patch references caller-owned buffers. */
int reaper_evolution_patch_generate(
    const char *relative_path,
    const uint8_t *original, size_t original_size,
    const uint8_t *replacement, size_t replacement_size,
    ReaperSourcePatch *patch,
    char *diagnostic, size_t diagnostic_capacity
);

/*
 * Transaction:
 * grant + immutable revision -> isolated workspace -> path grants -> hash checks
 * -> stage -> sandboxed checks -> workspace commits -> atomic topic-branch publish
 * -> durable audit. Failures roll back file snapshots and the conditional Git ref.
 * This engine performs no ambient filesystem/process/network I/O.
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
