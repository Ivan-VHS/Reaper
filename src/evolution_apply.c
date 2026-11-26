#include "reaper/evolution_apply.h"
#include "reaper/sha256.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    void *staged;
    void *rollback;
    char path[REAPER_EVOLUTION_APPLY_MAX_PATH];
    int committed;
} ApplyEntry;

static ReaperEvolutionApplyResult result_init(void) {
    ReaperEvolutionApplyResult result;
    memset(&result, 0, sizeof result);
    result.status = REAPER_APPLY_INVALID_ARGUMENT;
    return result;
}

static int valid_text(const char *value, size_t maximum) {
    size_t index;
    if (value == NULL || value[0] == '\0') return 0;
    for (index = 0u; index < maximum; ++index) {
        const unsigned char ch = (unsigned char)value[index];
        if (ch == 0u) return 1;
        if (ch < 0x20u || ch == 0x7fu) return 0;
    }
    return 0;
}

static int valid_identifier(const char *value, size_t maximum) {
    size_t index;
    if (!valid_text(value, maximum)) return 0;
    for (index = 0u; value[index] != '\0'; ++index) {
        const unsigned char ch = (unsigned char)value[index];
        if (!(isalnum(ch) || ch == '_' || ch == '-' || ch == '.')) return 0;
    }
    return 1;
}

static int valid_slash_identifier(const char *value, size_t maximum) {
    size_t index, segment_start = 0u;
    if (!valid_text(value, maximum) || value[0] == '/') return 0;
    for (index = 0u; value[index] != '\0'; ++index) {
        const unsigned char ch = (unsigned char)value[index];
        if (ch == '/') {
            const size_t segment_length = index - segment_start;
            if (segment_length == 0u ||
                (segment_length == 1u && value[segment_start] == '.') ||
                (segment_length == 2u && value[segment_start] == '.' &&
                 value[segment_start + 1u] == '.')) return 0;
            segment_start = index + 1u;
        } else if (!(isalnum(ch) || ch == '_' || ch == '-' || ch == '.')) {
            return 0;
        }
    }
    if (segment_start == index) return 0;
    if ((index - segment_start == 1u && value[segment_start] == '.') ||
        (index - segment_start == 2u && value[segment_start] == '.' &&
         value[segment_start + 1u] == '.')) return 0;
    return 1;
}

static int valid_relative_path(const char *path) {
    size_t index = 0u, segment_length = 0u;
    if (!valid_text(path, REAPER_EVOLUTION_APPLY_MAX_PATH) ||
        path[0] == '/' || path[0] == '\\') return 0;
    for (; path[index] != '\0'; ++index) {
        const unsigned char ch = (unsigned char)path[index];
        if (ch == ':' || ch == '\\' || ch < 0x20u || ch == 0x7fu) return 0;
        if (ch == '/') {
            if (segment_length == 0u) return 0;
            if ((segment_length == 1u && path[index - 1u] == '.') ||
                (segment_length == 2u && path[index - 1u] == '.' &&
                 path[index - 2u] == '.')) return 0;
            segment_length = 0u;
        } else {
            ++segment_length;
        }
    }
    if (segment_length == 0u) return 0;
    if ((segment_length == 1u && path[index - 1u] == '.') ||
        (segment_length == 2u && path[index - 1u] == '.' &&
         path[index - 2u] == '.')) return 0;
    return 1;
}

static int valid_hex(const char *value, size_t expected_length) {
    size_t index;
    if (value == NULL) return 0;
    for (index = 0u; index < expected_length; ++index) {
        if (value[index] == 0 || !isxdigit((unsigned char)value[index])) return 0;
    }
    return value[expected_length] == 0;
}

static int valid_revision(const ReaperEvolutionApplyRequest *request) {
    if (request->revision_algorithm == NULL || request->base_revision == NULL) return 0;
    if (strcmp(request->revision_algorithm, "sha1") == 0)
        return valid_hex(request->base_revision, 40u);
    if (strcmp(request->revision_algorithm, "sha256") == 0)
        return valid_hex(request->base_revision, 64u);
    return 0;
}

static int valid_limits(const ReaperApplyLimits *limits) {
    return limits->timeout_ms >= 100u && limits->timeout_ms <= 120000u &&
           limits->memory_limit_bytes >= UINT64_C(1048576) &&
           limits->memory_limit_bytes <= UINT64_C(4294967296) &&
           limits->output_limit_bytes >= UINT64_C(1024) &&
           limits->output_limit_bytes <= UINT64_C(16777216) &&
           limits->process_limit >= 1u && limits->process_limit <= 32u &&
           limits->file_limit >= 1u && limits->file_limit <= 256u;
}

static int valid_check_id(const char *value) {
    return valid_identifier(value, 96u);
}

static int host_complete(const ReaperEvolutionApplyHost *host) {
    return host != NULL &&
        host->abi_version == REAPER_EVOLUTION_APPLY_ABI_VERSION &&
        (host->capabilities & REAPER_APPLY_HOST_REQUIRED_CAPABILITIES) ==
            REAPER_APPLY_HOST_REQUIRED_CAPABILITIES &&
        host->verify_repository_grant != NULL &&
        host->verify_path_scope != NULL &&
        host->verify_git_revision != NULL &&
        host->begin_workspace != NULL &&
        host->resolve_confined_path != NULL &&
        host->read_file != NULL &&
        host->release_buffer != NULL &&
        host->stage_replace != NULL &&
        host->run_declared_checks != NULL &&
        host->commit_staged != NULL &&
        host->rollback_committed != NULL &&
        host->discard_staged != NULL &&
        host->publish_topic_branch != NULL &&
        host->rollback_topic_branch != NULL &&
        host->release_rollback != NULL &&
        host->preserve_failed_rollback != NULL &&
        host->end_workspace != NULL &&
        host->audit_append != NULL;
}

static int hash_u64(ReaperSha256Context *context, uint64_t value) {
    uint8_t encoded[8];
    size_t index;
    for (index = 0u; index < 8u; ++index)
        encoded[7u - index] = (uint8_t)(value >> (index * 8u));
    return reaper_sha256_update(context, encoded, sizeof encoded);
}

static int hash_field(ReaperSha256Context *context, const void *bytes, size_t length) {
    return hash_u64(context, (uint64_t)length) &&
           reaper_sha256_update(context, bytes, length);
}

static int request_digest(const ReaperEvolutionApplyRequest *request, char output[65]) {
    ReaperSha256Context context;
    uint8_t digest[32];
    size_t index;
    reaper_sha256_init(&context);
    if (!hash_field(&context, request->request_id, strlen(request->request_id)) ||
        !hash_field(&context, request->repository_id, strlen(request->repository_id)) ||
        !hash_field(&context, request->default_branch, strlen(request->default_branch)) ||
        !hash_field(&context, request->base_branch, strlen(request->base_branch)) ||
        !hash_field(&context, request->target_branch, strlen(request->target_branch)) ||
        !hash_field(&context, request->revision_algorithm, strlen(request->revision_algorithm)) ||
        !hash_field(&context, request->base_revision, strlen(request->base_revision)) ||
        !hash_u64(&context, (uint64_t)request->patch_count)) return 0;
    for (index = 0u; index < request->patch_count; ++index) {
        const ReaperSourcePatch *patch = &request->patches[index];
        if (!hash_field(&context, patch->relative_path, strlen(patch->relative_path)) ||
            !hash_field(&context, patch->expected_original_sha256, 64u) ||
            !hash_u64(&context, (uint64_t)patch->replacement_size) ||
            !hash_field(&context, patch->replacement, patch->replacement_size)) return 0;
    }
    if (!hash_u64(&context, (uint64_t)request->check_count)) return 0;
    for (index = 0u; index < request->check_count; ++index) {
        if (!hash_field(&context, request->check_ids[index], strlen(request->check_ids[index]))) return 0;
    }
    if (!hash_u64(&context, request->limits.timeout_ms) ||
        !hash_u64(&context, request->limits.memory_limit_bytes) ||
        !hash_u64(&context, request->limits.output_limit_bytes) ||
        !hash_u64(&context, request->limits.process_limit) ||
        !hash_u64(&context, request->limits.file_limit)) return 0;
    reaper_sha256_final(&context, digest);
    reaper_sha256_hex(digest, output);
    return 1;
}

static void cleanup_committed_backups(const ReaperEvolutionApplyHost *host,
                                      ApplyEntry *entries, size_t count) {
    size_t index;
    for (index = 0u; index < count; ++index) {
        if (entries[index].committed && entries[index].rollback != NULL) {
            host->release_rollback(host->context, entries[index].rollback);
            entries[index].rollback = NULL;
        }
        entries[index].staged = NULL;
    }
}

static int rollback_entries(const ReaperEvolutionApplyHost *host,
                            const ReaperEvolutionApplyRequest *request,
                            void *workspace,
                            ApplyEntry *entries, size_t count,
                            ReaperEvolutionApplyResult *result) {
    size_t index;
    int ok = 1;
    for (index = count; index > 0u; --index) {
        ApplyEntry *entry = &entries[index - 1u];
        if (entry->committed && entry->rollback != NULL) {
            if (host->rollback_committed(host->context, workspace, entry->rollback)) {
                ++result->rolled_back_files;
                host->release_rollback(host->context, entry->rollback);
                entry->rollback = NULL;
                entry->staged = NULL;
            } else {
                if (host->preserve_failed_rollback(host->context, entry->rollback,
                        request->request_id, request->target_branch, entry->path)) {
                    /* Ownership moves to the host's durable recovery store. */
                    entry->rollback = NULL;
                    entry->staged = NULL;
                }
                ok = 0;
            }
        } else if (!entry->committed && entry->staged != NULL) {
            if (!host->discard_staged(host->context, workspace, entry->staged)) ok = 0;
            entry->staged = NULL;
        }
    }
    return ok;
}

static int rollback_published_branch(const ReaperEvolutionApplyHost *host,
                                     const ReaperEvolutionApplyRequest *request,
                                     void **published_rollback) {
    if (published_rollback == NULL || *published_rollback == NULL) return 1;
    if (host->rollback_topic_branch(host->context, *published_rollback)) {
        host->release_rollback(host->context, *published_rollback);
        *published_rollback = NULL;
        return 1;
    }
    if (host->preserve_failed_rollback(host->context, *published_rollback,
            request->request_id, request->target_branch, "")) {
        /* Ownership moves to the durable recovery store. */
        *published_rollback = NULL;
    }
    return 0;
}

int reaper_evolution_patch_generate(const char *relative_path,
                                    const uint8_t *original, size_t original_size,
                                    const uint8_t *replacement, size_t replacement_size,
                                    ReaperSourcePatch *patch,
                                    char *diagnostic, size_t diagnostic_capacity) {
    if (diagnostic != NULL && diagnostic_capacity > 0u) diagnostic[0] = '\0';
    if (patch == NULL || !valid_relative_path(relative_path) ||
        (original_size > 0u && original == NULL) ||
        (replacement_size > 0u && replacement == NULL) ||
        original_size > REAPER_EVOLUTION_APPLY_MAX_FILE_BYTES ||
        replacement_size > REAPER_EVOLUTION_APPLY_MAX_FILE_BYTES) {
        if (diagnostic != NULL && diagnostic_capacity > 0u)
            (void)snprintf(diagnostic, diagnostic_capacity, "%s", "invalid patch input or file size limit exceeded");
        return 0;
    }
    memset(patch, 0, sizeof *patch);
    patch->relative_path = relative_path;
    patch->replacement = replacement;
    patch->replacement_size = replacement_size;
    if (!reaper_sha256_buffer(original, original_size, patch->expected_original_sha256)) {
        if (diagnostic != NULL && diagnostic_capacity > 0u)
            (void)snprintf(diagnostic, diagnostic_capacity, "%s", "cannot compute source SHA-256");
        return 0;
    }
    return 1;
}

ReaperEvolutionApplyResult reaper_evolution_apply(
    const ReaperEvolutionApplyHost *host,
    const ReaperEvolutionApplyRequest *request
) {
    ReaperEvolutionApplyResult result = result_init();
    ApplyEntry entries[REAPER_EVOLUTION_APPLY_MAX_FILES];
    size_t index, total_replacement_bytes = 0u;
    void *staged_handles[REAPER_EVOLUTION_APPLY_MAX_FILES] = {0};
    void *workspace = NULL;
    void *published_rollback = NULL;
    char canonical_path[REAPER_EVOLUTION_APPLY_MAX_PATH];
    char actual_digest[65];
    uint8_t *current_bytes = NULL;
    size_t current_size = 0u;
    int checks_passed = 0;
    int branch_published = 0;

    memset(entries, 0, sizeof entries);
    if (!host_complete(host)) {
        result.status = REAPER_APPLY_HOST_UNTRUSTED;
        return result;
    }
    if (request == NULL ||
        !valid_identifier(request->request_id, 96u) ||
        !valid_slash_identifier(request->repository_id, 128u) ||
        !valid_slash_identifier(request->default_branch, 128u) ||
        !valid_slash_identifier(request->base_branch, 128u) ||
        !valid_slash_identifier(request->target_branch, 128u) ||
        strcmp(request->target_branch, request->default_branch) == 0 ||
        !valid_revision(request) ||
        request->signed_grant == NULL || request->signed_grant_size == 0u ||
        request->signed_grant_size > 65536u ||
        request->patches == NULL || request->patch_count == 0u ||
        request->patch_count > REAPER_EVOLUTION_APPLY_MAX_FILES ||
        request->check_ids == NULL || request->check_count == 0u ||
        request->check_count > REAPER_EVOLUTION_APPLY_MAX_CHECKS ||
        !valid_limits(&request->limits)) {
        result.status = REAPER_APPLY_INVALID_ARGUMENT;
        return result;
    }

    for (index = 0u; index < request->check_count; ++index) {
        size_t other;
        if (!valid_check_id(request->check_ids[index])) {
            result.status = REAPER_APPLY_INVALID_ARGUMENT;
            return result;
        }
        for (other = index + 1u; other < request->check_count; ++other) {
            if (request->check_ids[other] != NULL &&
                strcmp(request->check_ids[index], request->check_ids[other]) == 0) {
                result.status = REAPER_APPLY_INVALID_ARGUMENT;
                return result;
            }
        }
    }

    for (index = 0u; index < request->patch_count; ++index) {
        size_t other;
        const ReaperSourcePatch *patch = &request->patches[index];
        if (!valid_relative_path(patch->relative_path) ||
            !valid_hex(patch->expected_original_sha256, 64u) ||
            (patch->replacement_size > 0u && patch->replacement == NULL) ||
            patch->replacement_size > REAPER_EVOLUTION_APPLY_MAX_FILE_BYTES ||
            total_replacement_bytes > REAPER_EVOLUTION_APPLY_MAX_TOTAL_BYTES - patch->replacement_size) {
            result.status = REAPER_APPLY_INVALID_ARGUMENT;
            return result;
        }
        total_replacement_bytes += patch->replacement_size;
        for (other = index + 1u; other < request->patch_count; ++other) {
            if (request->patches[other].relative_path != NULL &&
                strcmp(patch->relative_path, request->patches[other].relative_path) == 0) {
                result.status = REAPER_APPLY_INVALID_ARGUMENT;
                return result;
            }
        }
    }

    if (!host->verify_repository_grant(host->context, request->signed_grant,
            request->signed_grant_size, request->repository_id,
            request->target_branch, request->now_unix_seconds)) {
        result.status = REAPER_APPLY_GRANT_DENIED;
        return result;
    }
    if (!host->verify_git_revision(host->context, request->repository_id,
            request->base_branch, request->revision_algorithm, request->base_revision)) {
        result.status = REAPER_APPLY_REVISION_DENIED;
        return result;
    }

    if (!request_digest(request, result.request_digest)) {
        result.status = REAPER_APPLY_INVALID_ARGUMENT;
        return result;
    }
    (void)snprintf(result.published_branch, sizeof result.published_branch,
                   "%s", request->target_branch);
    if (!host->audit_append(host->context, "apply.started", request->request_id,
            request->repository_id, request->target_branch, request->base_revision,
            "", result.request_digest, "grant and immutable base revision verified")) {
        result.status = REAPER_APPLY_AUDIT_FAILED;
        return result;
    }

    if (!host->begin_workspace(host->context, request->repository_id,
            request->base_branch, request->revision_algorithm, request->base_revision,
            request->target_branch, &request->limits, &workspace) ||
        workspace == NULL) {
        result.status = REAPER_APPLY_WORKSPACE_FAILED;
        goto fail;
    }

    for (index = 0u; index < request->patch_count; ++index) {
        const ReaperSourcePatch *patch = &request->patches[index];
        if (!host->verify_path_scope(host->context, request->signed_grant,
                request->signed_grant_size, request->repository_id,
                patch->relative_path, request->now_unix_seconds)) {
            result.status = REAPER_APPLY_PATH_DENIED;
            (void)snprintf(result.failed_path, sizeof result.failed_path, "%s", patch->relative_path);
            goto fail;
        }
        canonical_path[0] = '\0';
        if (!host->resolve_confined_path(host->context, workspace, patch->relative_path,
                canonical_path, sizeof canonical_path) ||
            !valid_text(canonical_path, sizeof canonical_path)) {
            result.status = REAPER_APPLY_PATH_DENIED;
            (void)snprintf(result.failed_path, sizeof result.failed_path, "%s", patch->relative_path);
            goto fail;
        }
        current_bytes = NULL;
        current_size = 0u;
        if (!host->read_file(host->context, workspace, canonical_path,
                &current_bytes, &current_size) ||
            (current_size > 0u && current_bytes == NULL) ||
            current_size > REAPER_EVOLUTION_APPLY_MAX_FILE_BYTES) {
            if (current_bytes != NULL) host->release_buffer(host->context, current_bytes);
            current_bytes = NULL;
            result.status = REAPER_APPLY_READ_FAILED;
            (void)snprintf(result.failed_path, sizeof result.failed_path, "%s", patch->relative_path);
            goto fail;
        }
        if (!reaper_sha256_buffer(current_bytes, current_size, actual_digest) ||
            strcmp(actual_digest, patch->expected_original_sha256) != 0) {
            host->release_buffer(host->context, current_bytes);
            current_bytes = NULL;
            result.status = REAPER_APPLY_FINGERPRINT_MISMATCH;
            (void)snprintf(result.failed_path, sizeof result.failed_path, "%s", patch->relative_path);
            goto fail;
        }
        host->release_buffer(host->context, current_bytes);
        current_bytes = NULL;

        if (!host->stage_replace(host->context, workspace, canonical_path,
                patch->expected_original_sha256, patch->replacement,
                patch->replacement_size, &entries[index].staged) ||
            entries[index].staged == NULL) {
            if (entries[index].staged != NULL) {
                (void)host->discard_staged(host->context, workspace, entries[index].staged);
                entries[index].staged = NULL;
            }
            result.status = REAPER_APPLY_STAGE_FAILED;
            (void)snprintf(result.failed_path, sizeof result.failed_path, "%s", patch->relative_path);
            goto fail;
        }
        (void)snprintf(entries[index].path, sizeof entries[index].path, "%s", patch->relative_path);
        staged_handles[index] = entries[index].staged;
        if (!host->audit_append(host->context, "patch.staged", request->request_id,
                request->repository_id, request->target_branch, request->base_revision,
                patch->relative_path, patch->expected_original_sha256, "source pinned in isolated workspace")) {
            result.status = REAPER_APPLY_AUDIT_FAILED;
            goto fail;
        }
    }

    if (!host->run_declared_checks(host->context, workspace,
            staged_handles, request->patch_count,
            request->check_ids, request->check_count, &request->limits,
            result.report, sizeof result.report)) {
        result.status = REAPER_APPLY_CHECKS_FAILED;
        goto fail;
    }
    checks_passed = 1;
    if (!host->audit_append(host->context, "checks.passed", request->request_id,
            request->repository_id, request->target_branch, request->base_revision,
            "", result.request_digest, result.report)) {
        result.status = REAPER_APPLY_AUDIT_FAILED;
        goto fail;
    }

    for (index = 0u; index < request->patch_count; ++index) {
        if (!host->commit_staged(host->context, workspace,
                entries[index].staged, &entries[index].rollback)) {
            result.status = REAPER_APPLY_COMMIT_FAILED;
            (void)snprintf(result.failed_path, sizeof result.failed_path, "%s", entries[index].path);
            goto fail;
        }
        entries[index].committed = 1;
        if (entries[index].rollback == NULL) {
            result.status = REAPER_APPLY_ROLLBACK_FAILED;
            (void)snprintf(result.failed_path, sizeof result.failed_path, "%s", entries[index].path);
            goto fail;
        }
        ++result.applied_files;
    }

    if (!host->publish_topic_branch(host->context, workspace,
            request->target_branch, request->revision_algorithm,
            request->base_revision, result.published_revision, &published_rollback)) {
        result.status = REAPER_APPLY_PUBLISH_FAILED;
        if (published_rollback != NULL) branch_published = 1;
        goto fail;
    }
    branch_published = 1;
    if (published_rollback == NULL ||
        !valid_revision(&(ReaperEvolutionApplyRequest){
            .revision_algorithm = request->revision_algorithm,
            .base_revision = result.published_revision
        })) {
        result.status = REAPER_APPLY_PUBLISH_FAILED;
        goto fail;
    }

    if (!host->audit_append(host->context, "apply.committed", request->request_id,
            request->repository_id, request->target_branch, result.published_revision,
            "", result.request_digest, result.report)) {
        result.status = REAPER_APPLY_AUDIT_FAILED;
        goto fail;
    }

    cleanup_committed_backups(host, entries, request->patch_count);
    host->release_rollback(host->context, published_rollback);
    published_rollback = NULL;
    host->end_workspace(host->context, workspace);
    workspace = NULL;
    result.status = REAPER_APPLY_OK;
    return result;

fail:
    if (current_bytes != NULL) host->release_buffer(host->context, current_bytes);
    {
        int rollback_ok = 1;
        if (branch_published &&
            !rollback_published_branch(host, request, &published_rollback))
            rollback_ok = 0;
        if (workspace != NULL &&
            !rollback_entries(host, request, workspace, entries, request->patch_count, &result))
            rollback_ok = 0;
        if (!host->audit_append(host->context, "apply.rolled_back", request->request_id,
                request->repository_id, request->target_branch,
                branch_published ? result.published_revision : request->base_revision,
                result.failed_path, result.request_digest,
                checks_passed ? "branch publication failed or audit did not commit; rollback attempted" :
                                "isolated workspace operation failed; staged changes discarded")) {
            if (rollback_ok) result.status = REAPER_APPLY_AUDIT_FAILED;
        }
        if (!rollback_ok) result.status = REAPER_APPLY_ROLLBACK_FAILED;
    }
    if (workspace != NULL) host->end_workspace(host->context, workspace);
    return result;
}

const char *reaper_evolution_apply_status_name(ReaperApplyStatus status) {
    switch (status) {
    case REAPER_APPLY_OK: return "ok";
    case REAPER_APPLY_INVALID_ARGUMENT: return "invalid-argument";
    case REAPER_APPLY_HOST_UNTRUSTED: return "host-untrusted";
    case REAPER_APPLY_GRANT_DENIED: return "grant-denied";
    case REAPER_APPLY_REVISION_DENIED: return "revision-denied";
    case REAPER_APPLY_PATH_DENIED: return "path-denied";
    case REAPER_APPLY_FINGERPRINT_MISMATCH: return "fingerprint-mismatch";
    case REAPER_APPLY_LIMIT_EXCEEDED: return "limit-exceeded";
    case REAPER_APPLY_WORKSPACE_FAILED: return "workspace-failed";
    case REAPER_APPLY_READ_FAILED: return "read-failed";
    case REAPER_APPLY_STAGE_FAILED: return "stage-failed";
    case REAPER_APPLY_CHECKS_FAILED: return "checks-failed";
    case REAPER_APPLY_COMMIT_FAILED: return "commit-failed";
    case REAPER_APPLY_PUBLISH_FAILED: return "publish-failed";
    case REAPER_APPLY_AUDIT_FAILED: return "audit-failed";
    case REAPER_APPLY_ROLLBACK_FAILED: return "rollback-failed";
    default: return "invalid-status";
    }
}
