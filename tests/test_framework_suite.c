#include "reaper/framework_suite.h"

#include <assert.h>
#include <stdint.h>
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
    assert(stats.registry_api_functions == 8U);
    assert(stats.executable_domain_handlers == 0U);
    assert(stats.reaper_source_bindings == 0U);
    assert(reaper_framework_registry_stats(NULL) == REAPER_FRAMEWORK_INVALID_ARGUMENT);
}


typedef struct {
    unsigned calls;
    int report_oversized;
    int fail;
} DispatchContext;

static ReaperFrameworkStatus echo_dispatch(
    const ReaperFramework *framework,
    const ReaperFrameworkFunction *function,
    const void *request_payload,
    uint32_t request_size,
    void *response_payload,
    uint32_t response_capacity,
    uint32_t *response_size,
    void *host_context
) {
    DispatchContext *context = (DispatchContext *)host_context;
    if (framework == NULL || function == NULL || response_size == NULL ||
        context == NULL)
        return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    context->calls += 1U;
    if (context->fail) return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    if (context->report_oversized) {
        *response_size = response_capacity + 1U;
        return REAPER_FRAMEWORK_OK;
    }
    if (request_size > response_capacity) return REAPER_FRAMEWORK_OUT_OF_RANGE;
    if (request_size > 0U)
        memcpy(response_payload, request_payload, request_size);
    *response_size = request_size;
    return REAPER_FRAMEWORK_OK;
}

static void cross_language_dispatch_is_explicit_and_bounded(void) {
    const char request[] = "rpr";
    char response[8] = { 0 };
    uint32_t response_size = 99U;
    DispatchContext context = { 0U, 0, 0 };
    assert(reaper_framework_invoke(
        "joint-baby", "invoke_foreign", 3U,
        request, 3U, response, sizeof response, &response_size,
        echo_dispatch, &context) == REAPER_FRAMEWORK_OK);
    assert(context.calls == 1U);
    assert(response_size == 3U);
    assert(memcmp(response, request, 3U) == 0);

    response_size = 99U;
    assert(reaper_framework_invoke(
        "joint-baby", "invoke_foreign", 2U,
        request, 3U, response, sizeof response, &response_size,
        echo_dispatch, &context) == REAPER_FRAMEWORK_ARITY_MISMATCH);
    assert(response_size == 0U && context.calls == 1U);

    assert(reaper_framework_invoke(
        "missing", "invoke_foreign", 3U,
        request, 3U, response, sizeof response, &response_size,
        echo_dispatch, &context) == REAPER_FRAMEWORK_NOT_FOUND);
    assert(context.calls == 1U);

    assert(reaper_framework_invoke(
        "joint-baby", "invoke_foreign", 3U,
        request, REAPER_FRAMEWORK_MAX_PAYLOAD_BYTES + 1U,
        response, sizeof response, &response_size,
        echo_dispatch, &context) == REAPER_FRAMEWORK_OUT_OF_RANGE);
    assert(response_size == 0U && context.calls == 1U);

    context.report_oversized = 1;
    assert(reaper_framework_invoke(
        "joint-baby", "invoke_foreign", 3U,
        request, 3U, response, sizeof response, &response_size,
        echo_dispatch, &context) == REAPER_FRAMEWORK_OUT_OF_RANGE);
    assert(response_size == 0U);

    context.report_oversized = 0;
    context.fail = 1;
    assert(reaper_framework_invoke(
        "joint-baby", "invoke_foreign", 3U,
        request, 3U, response, sizeof response, &response_size,
        echo_dispatch, &context) == REAPER_FRAMEWORK_DISPATCH_FAILED);
    assert(response_size == 0U);

    assert(reaper_framework_invoke(
        "joint-baby", "invoke_foreign", 3U,
        request, 3U, response, sizeof response, &response_size,
        NULL, &context) == REAPER_FRAMEWORK_INVALID_ARGUMENT);
}

int main(void) {
    registry_has_twenty_stable_frameworks();
    lookup_and_signatures_are_case_insensitive();
    public_statistics_report_only_verified_scope();
    cross_language_dispatch_is_explicit_and_bounded();
    puts("native framework registry: 4 groups passed (20 frameworks, 120 contracts, bounded host dispatch)");
    return 0;
}
