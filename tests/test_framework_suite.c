#include "reaper/framework_suite.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void registry_has_twenty_stable_frameworks(void) {
    static const char *const ids[REAPER_FRAMEWORK_COUNT] = {
        "codex-no", "joint-baby", "correpse", "allocate-purpose", "collillioi", "aspdoi", "asjiop", "alllll", "zabor", "vjinz", "supreme-boy", "chee-now", "humble-bumble", "hub2", "kloz", "co", "cripplebo", "ripplecripple", "secator", "pollatia"
    };
    uint32_t contracts = 0U;
    assert(reaper_framework_abi_version() == REAPER_FRAMEWORK_ABI_VERSION);
    assert(reaper_framework_count() == REAPER_FRAMEWORK_COUNT);
    for (uint32_t i = 0U; i < REAPER_FRAMEWORK_COUNT; ++i) {
        const ReaperFramework *framework = reaper_framework_at(i);
        assert(framework != NULL);
        assert(strcmp(framework->id, ids[i]) == 0);
        assert(framework->maturity != NULL);
        assert(strcmp(framework->maturity, "contract-only") == 0);
        assert(framework->function_count == REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE);
        for (uint32_t j = 0U; j < framework->function_count; ++j) {
            const ReaperFrameworkFunction *function = &framework->functions[j];
            assert(function->key != NULL && function->key[0] != '\0');
            assert(function->name != NULL && function->name[0] != '\0');
            assert(function->min_arity <= function->max_arity);
        }
        contracts += framework->function_count;
    }
    assert(contracts == 120U);
    assert(reaper_framework_at(REAPER_FRAMEWORK_COUNT) == NULL);
}

static void lookup_and_signatures_are_case_insensitive(void) {
    const ReaperFramework *framework = reaper_framework_find("JOINT-BABY");
    const ReaperFrameworkFunction *function = NULL;
    assert(framework != NULL);
    assert(strcmp(framework->name, "Joint Baby") == 0);
    assert(reaper_framework_find("supremeboy") != NULL);
    assert(reaper_framework_find("missing") == NULL);
    assert(reaper_framework_validate_arity(
        framework, "invoke_foreign", 3U, &function) == REAPER_FRAMEWORK_OK);
    assert(function != NULL);
    assert(strcmp(function->key, "RPR-FWK-002-F03") == 0);
    assert(reaper_framework_validate_arity(
        framework, "invoke_foreign", 2U, &function) == REAPER_FRAMEWORK_ARITY_MISMATCH);
    assert(function == NULL);
    assert(reaper_framework_validate_arity(
        framework, "not_registered", 1U, &function) == REAPER_FRAMEWORK_NOT_FOUND);
    assert(reaper_framework_validate_arity(
        NULL, "invoke_foreign", 3U, NULL) == REAPER_FRAMEWORK_INVALID_ARGUMENT);
}

static void public_statistics_report_only_verified_scope(void) {
    ReaperFrameworkRegistryStats stats;
    assert(reaper_framework_registry_stats(&stats) == REAPER_FRAMEWORK_OK);
    assert(stats.registered_frameworks == 20U);
    assert(stats.registered_function_contracts == 120U);
    assert(stats.registry_api_functions == 7U);
    assert(stats.executable_domain_handlers == 0U);
    assert(stats.reaper_source_bindings == 0U);
    assert(reaper_framework_registry_stats(NULL) == REAPER_FRAMEWORK_INVALID_ARGUMENT);
}

int main(void) {
    registry_has_twenty_stable_frameworks();
    lookup_and_signatures_are_case_insensitive();
    public_statistics_report_only_verified_scope();
    puts("native framework registry: 3 groups passed (20 frameworks, 120 contracts)");
    return 0;
}
