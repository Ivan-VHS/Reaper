#include "reaper/framework.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    int starts;
    int stops;
    int start_result;
    int stop_result;
    uint64_t received_capabilities;
} Lifecycle;

static int start_callback(void *context, uint64_t capabilities) {
    Lifecycle *state = (Lifecycle *)context;
    ++state->starts;
    state->received_capabilities = capabilities;
    return state->start_result;
}

static int stop_callback(void *context) {
    Lifecycle *state = (Lifecycle *)context;
    ++state->stops;
    return state->stop_result;
}

static const char *const TEST_PROVIDES[] = { "test.storage.v1" };
static const char *const TEST_POINTS[] = { "test.storage.adapter" };
static const ReaperFrameworkDependency TEST_DEPENDENCIES[] = {
    { "codexno", { 1U, 0U, 0U }, { 2U, 0U, 0U } }
};

static ReaperFrameworkManifest make_extension(
    const char *id,
    const ReaperFrameworkDependency *dependencies,
    size_t dependency_count,
    uint64_t capabilities,
    Lifecycle *lifecycle
) {
    ReaperFrameworkManifest manifest = {
        .id = id,
        .name = "Test extension",
        .description = "A deterministic framework lifecycle test extension.",
        .version = { 1U, 2U, 0U },
        .abi_major = REAPER_FRAMEWORK_ABI_MAJOR,
        .abi_minor = REAPER_FRAMEWORK_ABI_MINOR,
        .dependencies = dependencies,
        .dependency_count = dependency_count,
        .provides = TEST_PROVIDES,
        .provides_count = 1U,
        .extension_points = TEST_POINTS,
        .extension_point_count = 1U,
        .required_capabilities = capabilities,
        .start = start_callback,
        .stop = stop_callback,
        .context = lifecycle
    };
    return manifest;
}

static void builtins_are_stable_and_resolve_deterministically(void) {
    ReaperFrameworkRegistry registry;
    ReaperFrameworkError error;
    reaper_framework_registry_init(&registry, 0U);
    assert(reaper_framework_builtin_count() == 5U);
    assert(reaper_framework_builtin_find("CODEXNO") != NULL);
    assert(reaper_framework_builtin_find("Allocate Purpose") != NULL);
    assert(reaper_framework_builtin_at(5U) == NULL);
    assert(reaper_framework_register_builtins(&registry, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_registry_count(&registry) == 5U);
    assert(reaper_framework_resolve(&registry, &error) == REAPER_FRAMEWORK_OK);
    {
        const ReaperFrameworkEntry *allocate =
            reaper_framework_registry_find(&registry, "allocate-purpose");
        const ReaperFrameworkEntry *correpse =
            reaper_framework_registry_find(&registry, "correpse");
        assert(allocate != NULL && correpse != NULL);
        assert(allocate->state == REAPER_FRAMEWORK_STATE_RESOLVED);
        assert(correpse->state == REAPER_FRAMEWORK_STATE_RESOLVED);
        assert(strcmp(reaper_framework_state_name(correpse->state), "resolved") == 0);
        assert(strcmp(reaper_framework_resolved_at(&registry, 0U)->manifest->id,
                      "allocate-purpose") == 0);
        assert(strcmp(reaper_framework_resolved_at(&registry, 4U)->manifest->id,
                      "correpse") == 0);
        assert(reaper_framework_resolved_at(&registry, 5U) == NULL);
    }
    assert(reaper_framework_activate(&registry, &error) == REAPER_FRAMEWORK_OK);
    {
        ReaperFrameworkStats stats;
        reaper_framework_stats_snapshot(&registry, &stats);
        assert(stats.total == 5U);
        assert(stats.registered == 0U);
        assert(stats.resolved == 5U);
        assert(stats.active == 0U);
        assert(stats.activation_runs == 1U);
    }
}

static void executable_extension_obeys_dependencies_and_capabilities(void) {
    ReaperFrameworkRegistry registry;
    ReaperFrameworkError error;
    Lifecycle lifecycle = { 0, 0, 0, 0, 0U };
    ReaperFrameworkManifest extension = make_extension(
        "test-storage", TEST_DEPENDENCIES, 1U,
        REAPER_SYSTEM_CAP_FS_READ, &lifecycle
    );
    reaper_framework_registry_init(&registry, REAPER_SYSTEM_CAP_FS_READ);
    assert(reaper_framework_register(&registry, &extension, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_register_builtins(&registry, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_resolve(&registry, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_activate(&registry, &error) == REAPER_FRAMEWORK_OK);
    assert(lifecycle.starts == 1);
    assert(lifecycle.received_capabilities == REAPER_SYSTEM_CAP_FS_READ);
    {
        const ReaperFrameworkEntry *entry =
            reaper_framework_registry_find(&registry, "test-storage");
        assert(entry != NULL && entry->state == REAPER_FRAMEWORK_STATE_ACTIVE);
    }
    assert(reaper_framework_deactivate(&registry, &error) == REAPER_FRAMEWORK_OK);
    assert(lifecycle.stops == 1);
    {
        ReaperFrameworkStats stats;
        reaper_framework_stats_snapshot(&registry, &stats);
        assert(stats.active == 0U);
        assert(stats.stopped == 1U);
        assert(stats.deactivation_runs == 1U);
    }
}

static void resolver_rejects_missing_versions_cycles_and_conflicts(void) {
    ReaperFrameworkRegistry registry;
    ReaperFrameworkError error;
    Lifecycle first_state = { 0, 0, 0, 0, 0U };
    Lifecycle second_state = { 0, 0, 0, 0, 0U };
    ReaperFrameworkDependency missing[] = {
        { "missing-framework", { 1U, 0U, 0U }, { 0U, 0U, 0U } }
    };
    ReaperFrameworkManifest missing_ext = make_extension(
        "requires-missing", missing, 1U, 0U, &first_state
    );
    reaper_framework_registry_init(&registry, 0U);
    assert(reaper_framework_register(&registry, &missing_ext, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_resolve(&registry, &error) ==
           REAPER_FRAMEWORK_DEPENDENCY_MISSING);
    assert(strcmp(error.related_id, "missing-framework") == 0);

    {
        ReaperFrameworkDependency too_new[] = {
            { "codexno", { 2U, 0U, 0U }, { 3U, 0U, 0U } }
        };
        ReaperFrameworkManifest version_ext = make_extension(
            "requires-newer", too_new, 1U, 0U, &first_state
        );
        reaper_framework_registry_init(&registry, 0U);
        assert(reaper_framework_register_builtins(&registry, &error) == REAPER_FRAMEWORK_OK);
        assert(reaper_framework_register(&registry, &version_ext, &error) == REAPER_FRAMEWORK_OK);
        assert(reaper_framework_resolve(&registry, &error) ==
               REAPER_FRAMEWORK_VERSION_MISMATCH);
    }
    {
        const ReaperFrameworkDependency a_dep[] = {
            { "cycle-b", { 1U, 0U, 0U }, { 0U, 0U, 0U } }
        };
        const ReaperFrameworkDependency b_dep[] = {
            { "cycle-a", { 1U, 0U, 0U }, { 0U, 0U, 0U } }
        };
        ReaperFrameworkManifest a = make_extension("cycle-a", a_dep, 1U, 0U, &first_state);
        ReaperFrameworkManifest b = make_extension("cycle-b", b_dep, 1U, 0U, &second_state);
        reaper_framework_registry_init(&registry, 0U);
        assert(reaper_framework_register(&registry, &a, &error) == REAPER_FRAMEWORK_OK);
        assert(reaper_framework_register(&registry, &b, &error) == REAPER_FRAMEWORK_OK);
        assert(reaper_framework_resolve(&registry, &error) ==
               REAPER_FRAMEWORK_DEPENDENCY_CYCLE);
    }
    {
        static const char *const conflict_ids[] = { "conflict-b" };
        ReaperFrameworkManifest a = make_extension("conflict-a", NULL, 0U, 0U, &first_state);
        ReaperFrameworkManifest b = make_extension("conflict-b", NULL, 0U, 0U, &second_state);
        a.conflicts = conflict_ids;
        a.conflict_count = 1U;
        reaper_framework_registry_init(&registry, 0U);
        assert(reaper_framework_register(&registry, &a, &error) == REAPER_FRAMEWORK_OK);
        assert(reaper_framework_register(&registry, &b, &error) == REAPER_FRAMEWORK_OK);
        assert(reaper_framework_resolve(&registry, &error) == REAPER_FRAMEWORK_CONFLICT);
    }
}

static void permission_and_manifest_errors_are_explicit(void) {
    ReaperFrameworkRegistry registry;
    ReaperFrameworkError error;
    Lifecycle lifecycle = { 0, 0, 0, 0, 0U };
    ReaperFrameworkManifest extension = make_extension(
        "needs-write", NULL, 0U, REAPER_SYSTEM_CAP_FS_WRITE, &lifecycle
    );
    reaper_framework_registry_init(&registry, REAPER_SYSTEM_CAP_FS_READ);
    assert(reaper_framework_register(&registry, &extension, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_resolve(&registry, &error) ==
           REAPER_FRAMEWORK_CAPABILITY_DENIED);

    extension.abi_major = 99U;
    assert(reaper_framework_manifest_validate(&extension, &error) ==
           REAPER_FRAMEWORK_ABI_MISMATCH);
    extension.abi_major = REAPER_FRAMEWORK_ABI_MAJOR;
    extension.start = NULL;
    assert(reaper_framework_manifest_validate(&extension, &error) ==
           REAPER_FRAMEWORK_INVALID_MANIFEST);
    extension.id = "Bad_ID";
    extension.start = start_callback;
    assert(reaper_framework_manifest_validate(&extension, &error) ==
           REAPER_FRAMEWORK_INVALID_MANIFEST);
}

static void activation_failure_rolls_back_prior_extensions(void) {
    ReaperFrameworkRegistry registry;
    ReaperFrameworkError error;
    Lifecycle first_state = { 0, 0, 0, 0, 0U };
    Lifecycle second_state = { 0, 0, -1, 0, 0U };
    ReaperFrameworkManifest first = make_extension(
        "rollback-first", NULL, 0U, 0U, &first_state
    );
    const ReaperFrameworkDependency second_dep[] = {
        { "rollback-first", { 1U, 0U, 0U }, { 2U, 0U, 0U } }
    };
    ReaperFrameworkManifest second = make_extension(
        "rollback-second", second_dep, 1U, 0U, &second_state
    );
    reaper_framework_registry_init(&registry, 0U);
    assert(reaper_framework_register(&registry, &first, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_register(&registry, &second, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_resolve(&registry, &error) == REAPER_FRAMEWORK_OK);
    assert(reaper_framework_activate(&registry, &error) ==
           REAPER_FRAMEWORK_CALLBACK_FAILED);
    assert(first_state.starts == 1 && first_state.stops == 1);
    assert(second_state.starts == 1 && second_state.stops == 0);
    assert(reaper_framework_registry_find(&registry, "rollback-first")->state ==
           REAPER_FRAMEWORK_STATE_STOPPED);
    assert(reaper_framework_registry_find(&registry, "rollback-second")->state ==
           REAPER_FRAMEWORK_STATE_FAILED);
    {
        ReaperFrameworkStats stats;
        reaper_framework_stats_snapshot(&registry, &stats);
        assert(stats.rollback_stops == 1U);
        assert(stats.callback_failures == 1U);
        assert(stats.failed == 1U);
    }
}

int main(void) {
    builtins_are_stable_and_resolve_deterministically();
    executable_extension_obeys_dependencies_and_capabilities();
    resolver_rejects_missing_versions_cycles_and_conflicts();
    permission_and_manifest_errors_are_explicit();
    activation_failure_rolls_back_prior_extensions();
    puts("native framework core tests: 5 groups passed");
    return 0;
}
