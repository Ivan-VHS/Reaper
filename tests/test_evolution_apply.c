#include "reaper/evolution_apply.h"
#include "reaper/sha256.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char current[128];
    size_t current_length;
    char staged[128];
    size_t staged_length;
    char backup[128];
    size_t backup_length;
    int audit_count;
    int checks_fail;
    int commit_fail;
    int rollback_fail;
    int audit_fail_event;
    int stage_active;
    int commit_calls;
} FakeHost;

typedef struct {
    FakeHost *owner;
    char replacement[128];
    size_t replacement_length;
    char original[128];
    size_t original_length;
} FakeStage;

static int verify_grant(void *context, const void *grant, size_t size,
                        const char *repo, const char *branch, uint64_t now) {
    (void)context; (void)repo; (void)branch;
    return grant != NULL && size == 6u && memcmp(grant, "signed", 6u) == 0 && now > 0u;
}
static int verify_path(void *context, const void *grant, size_t size,
                       const char *repo, const char *path, uint64_t now) {
    (void)context; (void)grant; (void)size; (void)repo; (void)now;
    return strcmp(path, "src/main.rpr") == 0;
}
static int verify_revision(void *context, const char *repo, const char *branch,
                           const char *algorithm, const char *revision) {
    (void)context; (void)repo;
    return strcmp(branch, "main") == 0 && strcmp(algorithm, "sha1") == 0 &&
           strlen(revision) == 40u;
}
static int resolve_path(void *context, const char *repo, const char *relative,
                        char *output, size_t capacity) {
    (void)context; (void)repo;
    if (strcmp(relative, "src/main.rpr") != 0 || capacity < 32u) return 0;
    (void)snprintf(output, capacity, "/test/repo/src/main.rpr");
    return 1;
}
static int read_file(void *context, const char *path, uint8_t **bytes, size_t *length) {
    FakeHost *fake = (FakeHost *)context;
    (void)path;
    *bytes = (uint8_t *)malloc(fake->current_length == 0u ? 1u : fake->current_length);
    if (*bytes == NULL) return 0;
    memcpy(*bytes, fake->current, fake->current_length);
    *length = fake->current_length;
    return 1;
}
static void release_buffer(void *context, uint8_t *bytes) {
    (void)context;
    free(bytes);
}
static int stage_replace(void *context, const char *path, const char *expected,
                         const uint8_t *replacement, size_t length, void **handle) {
    FakeHost *fake = (FakeHost *)context;
    FakeStage *stage = (FakeStage *)calloc(1u, sizeof *stage);
    char digest[65];
    (void)path;
    if (stage == NULL || length >= sizeof stage->replacement) { free(stage); return 0; }
    if (!reaper_sha256_buffer(fake->current, fake->current_length, digest) ||
        strcmp(digest, expected) != 0) { free(stage); return 0; }
    stage->owner = fake;
    stage->original_length = fake->current_length;
    memcpy(stage->original, fake->current, stage->original_length);
    stage->replacement_length = length;
    memcpy(stage->replacement, replacement, length);
    fake->stage_active = 1;
    *handle = stage;
    return 1;
}
static int run_checks(void *context, void *const *stages, size_t count,
                      const char *const *ids, size_t check_count,
                      const ReaperApplyLimits *limits, char *report, size_t cap) {
    FakeHost *fake = (FakeHost *)context;
    (void)stages; (void)ids;
    if (count != 1u || check_count != 1u || limits->timeout_ms > 120000u ||
        fake->checks_fail) {
        (void)snprintf(report, cap, "declared-check-failed");
        return 0;
    }
    (void)snprintf(report, cap, "one-registered-check-passed");
    return 1;
}
static int commit_staged(void *context, void *handle, void **rollback) {
    FakeHost *fake = (FakeHost *)context;
    FakeStage *stage = (FakeStage *)handle;
    ++fake->commit_calls;
    if (fake->commit_fail) return 0;
    memcpy(fake->current, stage->replacement, stage->replacement_length);
    fake->current_length = stage->replacement_length;
    *rollback = stage;
    return 1;
}
static int rollback_committed(void *context, void *handle) {
    FakeHost *fake = (FakeHost *)context;
    FakeStage *stage = (FakeStage *)handle;
    if (fake->rollback_fail) return 0;
    memcpy(fake->current, stage->original, stage->original_length);
    fake->current_length = stage->original_length;
    return 1;
}
static int discard_staged(void *context, void *handle) {
    FakeStage *stage = (FakeStage *)handle;
    (void)context;
    free(stage);
    return 1;
}
static void release_rollback(void *context, void *handle) {
    (void)context;
    free(handle);
}
static int audit_append(void *context, const char *event, const char *request,
                        const char *repo, const char *branch, const char *revision,
                        const char *path, const char *digest, const char *details) {
    FakeHost *fake = (FakeHost *)context;
    (void)request; (void)repo; (void)branch; (void)revision;
    (void)path; (void)digest; (void)details;
    if (fake->audit_fail_event && strcmp(event, "apply.committed") == 0) return 0;
    ++fake->audit_count;
    return 1;
}

static ReaperEvolutionApplyHost make_host(FakeHost *fake) {
    ReaperEvolutionApplyHost host;
    memset(&host, 0, sizeof host);
    host.abi_version = REAPER_EVOLUTION_APPLY_ABI_VERSION;
    host.capabilities = REAPER_APPLY_HOST_REQUIRED_CAPABILITIES;
    host.context = fake;
    host.verify_repository_grant = verify_grant;
    host.verify_path_scope = verify_path;
    host.verify_git_revision = verify_revision;
    host.resolve_confined_path = resolve_path;
    host.read_file = read_file;
    host.release_buffer = release_buffer;
    host.stage_replace = stage_replace;
    host.run_declared_checks = run_checks;
    host.commit_staged = commit_staged;
    host.rollback_committed = rollback_committed;
    host.discard_staged = discard_staged;
    host.release_rollback = release_rollback;
    host.audit_append = audit_append;
    return host;
}

static ReaperEvolutionApplyRequest make_request(
    const ReaperSourcePatch *patch, const char *const *checks) {
    ReaperEvolutionApplyRequest request;
    memset(&request, 0, sizeof request);
    request.request_id = "test-apply-001";
    request.repository_id = "Ivan-VHS/Reaper";
    request.default_branch = "main";
    request.base_branch = "main";
    request.target_branch = "feat/test-apply";
    request.revision_algorithm = "sha1";
    request.base_revision = "0123456789012345678901234567890123456789";
    request.signed_grant = "signed";
    request.signed_grant_size = 6u;
    request.now_unix_seconds = 100u;
    request.patches = patch;
    request.patch_count = 1u;
    request.check_ids = checks;
    request.check_count = 1u;
    request.limits = (ReaperApplyLimits){5000u, 64u * 1024u * 1024u,
        1024u * 1024u, 4u, 64u};
    return request;
}

int main(void) {
    FakeHost fake;
    ReaperEvolutionApplyHost host;
    ReaperEvolutionApplyRequest request;
    ReaperEvolutionApplyResult result;
    ReaperSourcePatch patch;
    char diagnostic[128];
    const char *checks[] = {"reaper.unit"};
    const uint8_t original[] = "old source";
    const uint8_t replacement[] = "new source";

    memset(&fake, 0, sizeof fake);
    memcpy(fake.current, original, sizeof original - 1u);
    fake.current_length = sizeof original - 1u;
    host = make_host(&fake);
    assert(reaper_evolution_patch_generate("src/main.rpr", original,
        sizeof original - 1u, replacement, sizeof replacement - 1u,
        &patch, diagnostic, sizeof diagnostic));
    request = make_request(&patch, checks);

    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_OK);
    assert(result.applied_files == 1u);
    assert(strcmp(fake.current, "new source") == 0);

    memcpy(fake.current, original, sizeof original - 1u);
    fake.current_length = sizeof original - 1u;
    fake.checks_fail = 1;
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_CHECKS_FAILED);
    assert(strcmp(fake.current, "old source") == 0);
    fake.checks_fail = 0;

    request.target_branch = "main";
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_INVALID_ARGUMENT);
    request.target_branch = "feat/test-apply";

    {
        ReaperSourcePatch invalid_patch = patch;
        invalid_patch.relative_path = "../outside.rpr";
        request.patches = &invalid_patch;
        result = reaper_evolution_apply(&host, &request);
        assert(result.status == REAPER_APPLY_INVALID_ARGUMENT);
        request.patches = &patch;
    }

    {
        ReaperEvolutionApplyHost incomplete = host;
        incomplete.capabilities &= ~REAPER_APPLY_HOST_NO_SYMLINKS;
        result = reaper_evolution_apply(&incomplete, &request);
        assert(result.status == REAPER_APPLY_HOST_UNTRUSTED);
    }

    memcpy(fake.current, "changed", 7u);
    fake.current_length = 7u;
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_FINGERPRINT_MISMATCH);

    puts("native evolution apply tests: 6 groups passed");
    return 0;
}
