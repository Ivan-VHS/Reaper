#include "reaper/evolution_apply.h"
#include "reaper/sha256.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char current[128];
    size_t current_length;
    int branch_exists;
    char branch_name[128];
    char branch_revision[65];
    int audit_count;
    int checks_fail;
    int commit_fail;
    int publish_fail_after_create;
    int branch_rollback_fail;
    int audit_fail_commit;
    int recovery_saved;
    int workspace_count;
    int workspace_end_count;
} FakeHost;

typedef struct {
    int kind;
    FakeHost *owner;
    char replacement[128];
    size_t replacement_length;
    char original[128];
    size_t original_length;
} FakeStage;

typedef struct {
    int kind;
    FakeHost *owner;
    char branch[128];
    char revision[65];
} FakeBranchRollback;

static int verify_grant(void *context, const void *grant, size_t size,
                        const char *repo, const char *branch, uint64_t now) {
    (void)context;
    return grant != NULL && size == 6u && memcmp(grant, "signed", 6u) == 0 &&
           strcmp(repo, "Ivan-VHS/Reaper") == 0 &&
           strcmp(branch, "feat/test-apply") == 0 && now > 0u;
}

static int verify_path(void *context, const void *grant, size_t size,
                       const char *repo, const char *path, uint64_t now) {
    (void)context; (void)grant; (void)size; (void)repo; (void)now;
    return strcmp(path, "src/main.rpr") == 0;
}

static int verify_revision(void *context, const char *repo, const char *branch,
                           const char *algorithm, const char *revision) {
    (void)context;
    return strcmp(repo, "Ivan-VHS/Reaper") == 0 &&
           strcmp(branch, "main") == 0 && strcmp(algorithm, "sha1") == 0 &&
           strlen(revision) == 40u;
}

static int begin_workspace(void *context, const char *repo, const char *base_branch,
                           const char *algorithm, const char *revision,
                           const char *target_branch, const ReaperApplyLimits *limits,
                           void **workspace) {
    FakeHost *fake = (FakeHost *)context;
    if (strcmp(repo, "Ivan-VHS/Reaper") != 0 ||
        strcmp(base_branch, "main") != 0 ||
        strcmp(algorithm, "sha1") != 0 || strlen(revision) != 40u ||
        strcmp(target_branch, "main") == 0 || fake->branch_exists ||
        limits->timeout_ms == 0u) return 0;
    ++fake->workspace_count;
    *workspace = fake;
    return 1;
}

static int resolve_path(void *context, void *workspace, const char *relative,
                        char *output, size_t capacity) {
    (void)context;
    if (workspace == NULL || strcmp(relative, "src/main.rpr") != 0 || capacity < 32u) return 0;
    (void)snprintf(output, capacity, "/isolated/worktree/src/main.rpr");
    return 1;
}

static int read_file(void *context, void *workspace, const char *path,
                     uint8_t **bytes, size_t *length) {
    FakeHost *fake = (FakeHost *)context;
    (void)path;
    if (workspace != fake) return 0;
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

static int stage_replace(void *context, void *workspace, const char *path,
                         const char *expected, const uint8_t *replacement,
                         size_t length, void **handle) {
    FakeHost *fake = (FakeHost *)context;
    FakeStage *stage;
    char digest[65];
    (void)path;
    if (workspace != fake || length >= sizeof fake->current) return 0;
    stage = (FakeStage *)calloc(1u, sizeof *stage);
    if (stage == NULL) return 0;
    if (!reaper_sha256_buffer(fake->current, fake->current_length, digest) ||
        strcmp(digest, expected) != 0) {
        free(stage);
        return 0;
    }
    stage->kind = 1;
    stage->owner = fake;
    stage->original_length = fake->current_length;
    memcpy(stage->original, fake->current, stage->original_length);
    stage->replacement_length = length;
    if (length > 0u) memcpy(stage->replacement, replacement, length);
    *handle = stage;
    return 1;
}

static int run_checks(void *context, void *workspace, void *const *stages,
                      size_t count, const char *const *ids, size_t check_count,
                      const ReaperApplyLimits *limits, char *report, size_t cap) {
    FakeHost *fake = (FakeHost *)context;
    if (workspace != fake || count != 1u || check_count != 1u ||
        stages[0] == NULL || strcmp(ids[0], "reaper.unit") != 0 ||
        limits->timeout_ms > 120000u || fake->checks_fail) {
        (void)snprintf(report, cap, "declared-check-failed");
        return 0;
    }
    (void)snprintf(report, cap, "one-registered-check-passed");
    return 1;
}

static int commit_staged(void *context, void *workspace,
                         void *handle, void **rollback) {
    FakeHost *fake = (FakeHost *)context;
    FakeStage *stage = (FakeStage *)handle;
    if (workspace != fake || stage == NULL || stage->kind != 1 || fake->commit_fail) return 0;
    memcpy(fake->current, stage->replacement, stage->replacement_length);
    fake->current_length = stage->replacement_length;
    *rollback = stage;
    return 1;
}

static int rollback_committed(void *context, void *workspace, void *handle) {
    FakeHost *fake = (FakeHost *)context;
    FakeStage *stage = (FakeStage *)handle;
    if (workspace != fake || stage == NULL || stage->kind != 1) return 0;
    memcpy(fake->current, stage->original, stage->original_length);
    fake->current_length = stage->original_length;
    return 1;
}

static int discard_staged(void *context, void *workspace, void *handle) {
    FakeStage *stage = (FakeStage *)handle;
    (void)context;
    if (workspace == NULL || stage == NULL || stage->kind != 1) return 0;
    free(stage);
    return 1;
}

static int publish_topic_branch(void *context, void *workspace,
                                const char *target_branch, const char *algorithm,
                                const char *base_revision, char published_revision[65],
                                void **rollback) {
    FakeHost *fake = (FakeHost *)context;
    FakeBranchRollback *snapshot;
    if (workspace != fake || fake->branch_exists ||
        strcmp(target_branch, "feat/test-apply") != 0 ||
        strcmp(algorithm, "sha1") != 0 || strlen(base_revision) != 40u) return 0;
    snapshot = (FakeBranchRollback *)calloc(1u, sizeof *snapshot);
    if (snapshot == NULL) return 0;
    snapshot->kind = 2;
    snapshot->owner = fake;
    (void)snprintf(snapshot->branch, sizeof snapshot->branch, "%s", target_branch);
    memset(snapshot->revision, '1', 40u);
    snapshot->revision[40] = '\0';

    fake->branch_exists = 1;
    (void)snprintf(fake->branch_name, sizeof fake->branch_name, "%s", target_branch);
    (void)snprintf(fake->branch_revision, sizeof fake->branch_revision, "%s", snapshot->revision);
    (void)snprintf(published_revision, 65u, "%s", snapshot->revision);
    *rollback = snapshot;
    return fake->publish_fail_after_create ? 0 : 1;
}

static int rollback_topic_branch(void *context, void *handle) {
    FakeHost *fake = (FakeHost *)context;
    FakeBranchRollback *snapshot = (FakeBranchRollback *)handle;
    if (snapshot == NULL || snapshot->kind != 2 || snapshot->owner != fake ||
        fake->branch_rollback_fail) return 0;
    if (!fake->branch_exists ||
        strcmp(fake->branch_name, snapshot->branch) != 0 ||
        strcmp(fake->branch_revision, snapshot->revision) != 0) return 0;
    fake->branch_exists = 0;
    fake->branch_name[0] = '\0';
    fake->branch_revision[0] = '\0';
    return 1;
}

static void release_rollback(void *context, void *handle) {
    (void)context;
    free(handle);
}

static int preserve_recovery(void *context, void *handle,
                             const char *request_id, const char *branch,
                             const char *path) {
    FakeHost *fake = (FakeHost *)context;
    (void)request_id; (void)branch; (void)path;
    fake->recovery_saved = 1;
    free(handle);
    return 1;
}

static void end_workspace(void *context, void *workspace) {
    FakeHost *fake = (FakeHost *)context;
    assert(workspace == fake);
    ++fake->workspace_end_count;
}

static int audit_append(void *context, const char *event, const char *request,
                        const char *repo, const char *branch, const char *revision,
                        const char *path, const char *digest, const char *details) {
    FakeHost *fake = (FakeHost *)context;
    (void)request; (void)repo; (void)branch; (void)revision;
    (void)path; (void)digest; (void)details;
    if (fake->audit_fail_commit && strcmp(event, "apply.committed") == 0) return 0;
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
    host.begin_workspace = begin_workspace;
    host.resolve_confined_path = resolve_path;
    host.read_file = read_file;
    host.release_buffer = release_buffer;
    host.stage_replace = stage_replace;
    host.run_declared_checks = run_checks;
    host.commit_staged = commit_staged;
    host.rollback_committed = rollback_committed;
    host.discard_staged = discard_staged;
    host.publish_topic_branch = publish_topic_branch;
    host.rollback_topic_branch = rollback_topic_branch;
    host.release_rollback = release_rollback;
    host.preserve_failed_rollback = preserve_recovery;
    host.end_workspace = end_workspace;
    host.audit_append = audit_append;
    return host;
}

static void setup(FakeHost *fake, ReaperEvolutionApplyHost *host,
                  ReaperEvolutionApplyRequest *request,
                  ReaperSourcePatch *patch) {
    const uint8_t original[] = "old source";
    const uint8_t replacement[] = "new source";
    const char *checks[] = {"reaper.unit"};
    char diagnostic[128];

    memset(fake, 0, sizeof *fake);
    memcpy(fake->current, original, sizeof original - 1u);
    fake->current_length = sizeof original - 1u;
    *host = make_host(fake);
    assert(reaper_evolution_patch_generate("src/main.rpr", original,
        sizeof original - 1u, replacement, sizeof replacement - 1u,
        patch, diagnostic, sizeof diagnostic));

    memset(request, 0, sizeof *request);
    request->request_id = "test-apply-001";
    request->repository_id = "Ivan-VHS/Reaper";
    request->default_branch = "main";
    request->base_branch = "main";
    request->target_branch = "feat/test-apply";
    request->revision_algorithm = "sha1";
    request->base_revision = "0123456789012345678901234567890123456789";
    request->signed_grant = "signed";
    request->signed_grant_size = 6u;
    request->now_unix_seconds = 100u;
    request->patches = patch;
    request->patch_count = 1u;
    request->check_ids = checks;
    request->check_count = 1u;
    request->limits = (ReaperApplyLimits){5000u, 64u * 1024u * 1024u,
        1024u * 1024u, 4u, 64u};
}

static void test_success_creates_topic_branch(void) {
    FakeHost fake;
    ReaperEvolutionApplyHost host;
    ReaperEvolutionApplyRequest request;
    ReaperEvolutionApplyResult result;
    ReaperSourcePatch patch;
    setup(&fake, &host, &request, &patch);
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_OK);
    assert(result.applied_files == 1u);
    assert(strcmp(fake.current, "new source") == 0);
    assert(fake.branch_exists == 1);
    assert(strcmp(fake.branch_name, "feat/test-apply") == 0);
    assert(strcmp(result.published_branch, "feat/test-apply") == 0);
    assert(strlen(result.published_revision) == 40u);
    assert(fake.workspace_end_count == 1);
}

static void test_checks_failure_discards_workspace(void) {
    FakeHost fake;
    ReaperEvolutionApplyHost host;
    ReaperEvolutionApplyRequest request;
    ReaperEvolutionApplyResult result;
    ReaperSourcePatch patch;
    setup(&fake, &host, &request, &patch);
    fake.checks_fail = 1;
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_CHECKS_FAILED);
    assert(strcmp(fake.current, "old source") == 0);
    assert(fake.branch_exists == 0);
    assert(fake.workspace_end_count == 1);
}

static void test_audit_failure_rolls_back_files_and_topic_ref(void) {
    FakeHost fake;
    ReaperEvolutionApplyHost host;
    ReaperEvolutionApplyRequest request;
    ReaperEvolutionApplyResult result;
    ReaperSourcePatch patch;
    setup(&fake, &host, &request, &patch);
    fake.audit_fail_commit = 1;
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_AUDIT_FAILED);
    assert(strcmp(fake.current, "old source") == 0);
    assert(fake.branch_exists == 0);
    assert(result.rolled_back_files == 1u);
    assert(fake.workspace_end_count == 1);
}

static void test_partial_publish_failure_rolls_back_ref(void) {
    FakeHost fake;
    ReaperEvolutionApplyHost host;
    ReaperEvolutionApplyRequest request;
    ReaperEvolutionApplyResult result;
    ReaperSourcePatch patch;
    setup(&fake, &host, &request, &patch);
    fake.publish_fail_after_create = 1;
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_PUBLISH_FAILED);
    assert(strcmp(fake.current, "old source") == 0);
    assert(fake.branch_exists == 0);
}

static void test_failed_ref_rollback_is_preserved_for_recovery(void) {
    FakeHost fake;
    ReaperEvolutionApplyHost host;
    ReaperEvolutionApplyRequest request;
    ReaperEvolutionApplyResult result;
    ReaperSourcePatch patch;
    setup(&fake, &host, &request, &patch);
    fake.audit_fail_commit = 1;
    fake.branch_rollback_fail = 1;
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_ROLLBACK_FAILED);
    assert(fake.recovery_saved == 1);
    assert(fake.branch_exists == 1);
    assert(strcmp(fake.current, "old source") == 0);
}

static void test_default_branch_and_path_escape_are_rejected(void) {
    FakeHost fake;
    ReaperEvolutionApplyHost host;
    ReaperEvolutionApplyRequest request;
    ReaperEvolutionApplyResult result;
    ReaperSourcePatch patch;
    ReaperSourcePatch invalid_patch;

    setup(&fake, &host, &request, &patch);
    request.target_branch = "main";
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_INVALID_ARGUMENT);

    setup(&fake, &host, &request, &patch);
    invalid_patch = patch;
    invalid_patch.relative_path = "../outside.rpr";
    request.patches = &invalid_patch;
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_INVALID_ARGUMENT);
}

static void test_untrusted_host_and_stale_source_are_rejected(void) {
    FakeHost fake;
    ReaperEvolutionApplyHost host;
    ReaperEvolutionApplyRequest request;
    ReaperEvolutionApplyResult result;
    ReaperSourcePatch patch;
    ReaperEvolutionApplyHost incomplete;

    setup(&fake, &host, &request, &patch);
    incomplete = host;
    incomplete.capabilities &= ~REAPER_APPLY_HOST_NO_SYMLINKS;
    result = reaper_evolution_apply(&incomplete, &request);
    assert(result.status == REAPER_APPLY_HOST_UNTRUSTED);

    setup(&fake, &host, &request, &patch);
    memcpy(fake.current, "changed", 7u);
    fake.current_length = 7u;
    result = reaper_evolution_apply(&host, &request);
    assert(result.status == REAPER_APPLY_FINGERPRINT_MISMATCH);
    assert(fake.branch_exists == 0);
}

int main(void) {
    test_success_creates_topic_branch();
    test_checks_failure_discards_workspace();
    test_audit_failure_rolls_back_files_and_topic_ref();
    test_partial_publish_failure_rolls_back_ref();
    test_failed_ref_rollback_is_preserved_for_recovery();
    test_default_branch_and_path_escape_are_rejected();
    test_untrusted_host_and_stale_source_are_rejected();
    puts("native evolution apply tests: 7 groups passed");
    return 0;
}
