#include "reaper/system_features.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void fill_digest(uint8_t digest[REAPER_SYSTEM_DIGEST_BYTES], uint8_t value) {
    for (size_t i = 0U; i < REAPER_SYSTEM_DIGEST_BYTES; ++i)
        digest[i] = (uint8_t)(value + (uint8_t)i);
}

/* 1. Contract graph */
static void test_contract_graph_and_compatibility(void) {
    const ReaperContractFieldSpec base_fields[] = {{"format", 1U, 0U}, {"revision", 2U, 1U}};
    const ReaperContractFieldSpec required_fields[] = {{"format", 1U, 0U}};
    const ReaperContractDependency codec_deps[] = {{"base", 2U, required_fields, 1U}};
    const ReaperContractDependency app_deps[] = {{"codec", 1U, NULL, 0U}};
    const ReaperContractSpec contracts[] = {
        {"app", 1U, NULL, 0U, app_deps, 1U},
        {"codec", 1U, NULL, 0U, codec_deps, 1U},
        {"base", 2U, base_fields, 2U, NULL, 0U}
    };
    const size_t expected[] = {2U, 1U, 0U};
    size_t ordered[3] = {99U, 99U, 99U};
    size_t written = 0U;
    ReaperSystemError error;
    assert(reaper_contract_graph_validate(contracts, 3U, &error) == REAPER_SYSTEM_OK);
    assert(reaper_contract_graph_order(contracts, 3U, ordered, 3U, &written, &error) == REAPER_SYSTEM_OK);
    assert(written == 3U && memcmp(ordered, expected, sizeof expected) == 0);

    const ReaperContractDependency cycle_a_dep[] = {{"B", 1U, NULL, 0U}};
    const ReaperContractDependency cycle_b_dep[] = {{"A", 1U, NULL, 0U}};
    const ReaperContractSpec cycle[] = {
        {"A", 1U, NULL, 0U, cycle_a_dep, 1U},
        {"B", 1U, NULL, 0U, cycle_b_dep, 1U}
    };
    assert(reaper_contract_graph_validate(cycle, 2U, &error) == REAPER_SYSTEM_DEPENDENCY_CYCLE);

    const ReaperContractFieldSpec wrong_required[] = {{"format", 9U, 0U}};
    const ReaperContractDependency bad_dep[] = {{"base", 1U, wrong_required, 1U}};
    const ReaperContractSpec incompatible[] = {
        {"codec", 1U, NULL, 0U, bad_dep, 1U},
        {"base", 2U, base_fields, 2U, NULL, 0U}
    };
    assert(reaper_contract_graph_validate(incompatible, 2U, &error) == REAPER_SYSTEM_INCOMPATIBLE_FIELD);
}

/* 2. Arena slots */
static void test_arena_slots_are_bounded_and_zeroized(void) {
    uint8_t memory[128];
    memset(memory, 0xA5, sizeof memory);
    ReaperArenaSlot slot = {0};
    ReaperSystemError error;
    assert(reaper_arena_slot_begin(&slot, memory, sizeof memory, 7U) == REAPER_SYSTEM_OK);
    uint8_t *first = (uint8_t *)reaper_arena_slot_alloc(&slot, 13U, 8U, &error);
    assert(first != NULL && ((uintptr_t)first % 8U) == 0U);
    memset(first, 0x3C, 13U);
    assert(reaper_arena_slot_alloc(&slot, 200U, 8U, &error) == NULL);
    assert(error.status == REAPER_SYSTEM_LIMIT_EXCEEDED);
    const size_t used = slot.offset;
    assert(reaper_arena_slot_end(&slot, 1) == REAPER_SYSTEM_OK);
    for (size_t i = 0U; i < used; ++i) assert(memory[i] == 0U);
    assert(reaper_arena_slot_alloc(&slot, 1U, 1U, &error) == NULL);
}

/* 3. Worker budgets */
static void test_worker_budget_halts_and_dumps_state(void) {
    ReaperWorkerBudget budget;
    ReaperWorkerBudgetDump dump;
    assert(reaper_worker_budget_begin(&budget, 1000U, 512U, 100U) == REAPER_SYSTEM_OK);
    assert(reaper_worker_budget_checkpoint(&budget, 200U, 256U, &dump) == REAPER_SYSTEM_OK);
    assert(dump.halted == 0 && dump.peak_memory_bytes == 256U);
    assert(reaper_worker_budget_checkpoint(&budget, 1200U, 256U, &dump) == REAPER_SYSTEM_BUDGET_EXCEEDED);
    assert(dump.halted == 1 && dump.elapsed_ns == 1100U);
    assert(reaper_worker_budget_checkpoint(&budget, 1300U, 256U, &dump) == REAPER_SYSTEM_BUDGET_EXCEEDED);

    assert(reaper_worker_budget_begin(&budget, 1000U, 64U, 10U) == REAPER_SYSTEM_OK);
    assert(reaper_worker_budget_checkpoint(&budget, 20U, 65U, &dump) == REAPER_SYSTEM_BUDGET_EXCEEDED);
    assert(dump.current_memory_bytes == 65U && dump.halted == 1);
    assert(reaper_worker_budget_checkpoint(&budget, 19U, 1U, &dump) == REAPER_SYSTEM_BUDGET_EXCEEDED);
}

/* 4. Aggregate diff/reconcile plan */
static int item_count_bounded(const ReaperAggregateState *state, void *context) {
    const uint64_t maximum = *(const uint64_t *)context;
    return state->item_count <= maximum;
}

static void test_reconcile_plan_is_deterministic_and_atomic(void) {
    ReaperAggregateState before[2] = {
        {"cache.alpha", 1U, 10U, {0}},
        {"cache.beta", 1U, 20U, {0}}
    };
    ReaperAggregateState after[2] = {
        {"cache.alpha", 1U, 10U, {0}},
        {"cache.gamma", 2U, 30U, {0}}
    };
    fill_digest(before[0].digest, 1U);
    fill_digest(before[1].digest, 2U);
    fill_digest(after[0].digest, 1U);
    fill_digest(after[1].digest, 3U);

    ReaperReconcilePlanItem plan[4];
    ReaperSystemError error;
    size_t written = 0U;
    const uint64_t maximum = 100U;
    assert(reaper_reconcile_plan_build(before, 2U, after, 2U,
        item_count_bounded, (void *)&maximum, plan, 4U, &written, &error) == REAPER_SYSTEM_OK);
    assert(written == 3U);
    assert(strcmp(plan[0].resource_id, "cache.alpha") == 0);
    assert(plan[0].action == REAPER_RECONCILE_NOOP);
    assert(strcmp(plan[1].resource_id, "cache.beta") == 0);
    assert(plan[1].action == REAPER_RECONCILE_DROP);
    assert(strcmp(plan[2].resource_id, "cache.gamma") == 0);
    assert(plan[2].action == REAPER_RECONCILE_UPSERT);

    ReaperReconcilePlanItem sentinel = {"sentinel", REAPER_RECONCILE_DROP, 0U, 0U, 0U, 0U};
    written = 77U;
    assert(reaper_reconcile_plan_build(before, 2U, after, 2U,
        item_count_bounded, (void *)&maximum, &sentinel, 1U, &written, &error) ==
        REAPER_SYSTEM_BUFFER_TOO_SMALL);
    assert(written == 0U && strcmp(sentinel.resource_id, "sentinel") == 0);

    const uint64_t too_small = 1U;
    assert(reaper_reconcile_plan_build(before, 2U, after, 2U,
        item_count_bounded, (void *)&too_small, plan, 4U, &written, &error) ==
        REAPER_SYSTEM_INVARIANT_FAILED);
    assert(written == 0U);
}

/* 5. Ephemeral memory */
static void test_ephemeral_scope_matches_then_wipes(void) {
    uint8_t scratch[64];
    memset(scratch, 0xD7, sizeof scratch);
    uint8_t *left = scratch;
    uint8_t *right = scratch + REAPER_SYSTEM_DIGEST_BYTES;
    fill_digest(left, 9U);
    memcpy(right, left, REAPER_SYSTEM_DIGEST_BYTES);
    ReaperEphemeralScope scope = {0};
    int matches = 0;
    assert(reaper_ephemeral_scope_begin(&scope, scratch, sizeof scratch, 3U) == REAPER_SYSTEM_OK);
    assert(reaper_ephemeral_match(&scope, left, right, REAPER_SYSTEM_DIGEST_BYTES, &matches) == REAPER_SYSTEM_OK);
    assert(matches == 1);
    right[7] ^= 1U;
    assert(reaper_ephemeral_match(&scope, left, right, REAPER_SYSTEM_DIGEST_BYTES, &matches) == REAPER_SYSTEM_OK);
    assert(matches == 0);
    const uint8_t external_digest[REAPER_SYSTEM_DIGEST_BYTES] = {0};
    assert(reaper_ephemeral_match(&scope, left, external_digest, REAPER_SYSTEM_DIGEST_BYTES, &matches) == REAPER_SYSTEM_DENIED);
    assert(reaper_ephemeral_scope_end(&scope) == REAPER_SYSTEM_OK);
    for (size_t i = 0U; i < sizeof scratch; ++i) assert(scratch[i] == 0U);
    assert(reaper_ephemeral_match(&scope, left, right, REAPER_SYSTEM_DIGEST_BYTES, &matches) == REAPER_SYSTEM_NOT_ACTIVE);
}

/* 6. Automatic and guarded manual mutation */
static void test_mutation_authorization_requires_revision_and_gate(void) {
    ReaperRevisionEvent event;
    ReaperSystemError error;
    const uint8_t token_bytes[] = {1U, 2U, 3U, 4U};
    const ReaperOverrideGrant grant = {token_bytes, sizeof token_bytes, 8U, 1};
    assert(reaper_mutation_authorize(REAPER_MUTATION_AUTO, 0, 8U, 8U,
        "refresh.index", NULL, &event, &error) == REAPER_SYSTEM_DENIED);
    assert(reaper_mutation_authorize(REAPER_MUTATION_AUTO, 1, 8U, 8U,
        "refresh.index", NULL, &event, &error) == REAPER_SYSTEM_OK);
    assert(event.previous_revision == 8U && event.next_revision == 9U);
    assert(reaper_mutation_authorize(REAPER_MUTATION_MANUAL, 0, 8U, 8U,
        "repair.index", NULL, &event, &error) == REAPER_SYSTEM_DENIED);
    assert(reaper_mutation_authorize(REAPER_MUTATION_MANUAL, 0, 8U, 8U,
        "repair.index", &grant, &event, &error) == REAPER_SYSTEM_OK);
    assert(event.mode == REAPER_MUTATION_MANUAL);
    assert(reaper_mutation_authorize(REAPER_MUTATION_MANUAL, 0, 9U, 8U,
        "repair.index", &grant, &event, &error) == REAPER_SYSTEM_INVALID_ORDER);
}

/* 7. Lease windows */
static void test_lease_window_warns_and_expires(void) {
    ReaperLeaseWindow window;
    ReaperSystemError error;
    uint16_t remaining = 0U;
    assert(reaper_lease_window_open(100U, REAPER_LEASE_DAYS(30U), &window, &error) == REAPER_SYSTEM_OK);
    assert(window.valid_until_day_utc == 130U);
    assert(reaper_lease_window_check(&window, 120U, 3U, &remaining) == REAPER_SYSTEM_OK);
    assert(remaining == 10U);
    assert(reaper_lease_window_check(&window, 128U, 3U, &remaining) == REAPER_SYSTEM_LEASE_WARNING);
    assert(remaining == 2U);
    assert(reaper_lease_window_check(&window, 130U, 3U, &remaining) == REAPER_SYSTEM_EXPIRED);
    assert(remaining == 0U);
}

/* 8. Runtime latency profiler */
static void test_latency_profiler_reports_percentiles(void) {
    ReaperLatencyProfiler profiler;
    ReaperLatencySummary summary;
    reaper_latency_profiler_init(&profiler, 2U);
    for (uint64_t i = 1U; i <= 1000U; ++i)
        assert(reaper_latency_record(&profiler, 0U, i * 1000U) == REAPER_SYSTEM_OK);
    assert(reaper_latency_summary(&profiler, 0U, &summary) == REAPER_SYSTEM_OK);
    assert(summary.sample_count == 1000U);
    assert(summary.mean_ns == 500500U);
    assert(summary.p95_ns >= 950000U);
    assert(summary.p99_ns >= summary.p95_ns);
    assert(summary.max_ns == 1000000U);
    assert(reaper_latency_summary(&profiler, 2U, &summary) == REAPER_SYSTEM_INVALID_ARGUMENT);
}

/* 9. Local-only effect boundary */
static void test_local_only_rejects_transitive_network_effects(void) {
    ReaperSystemError error;
    assert(reaper_module_effects_validate(1, REAPER_EFFECT_FILE_READ,
        REAPER_EFFECT_FILE_READ, 0U, &error) == REAPER_SYSTEM_OK);
    assert(reaper_module_effects_validate(1,
        REAPER_EFFECT_FILE_READ | REAPER_EFFECT_NETWORK,
        REAPER_EFFECT_FILE_READ, REAPER_EFFECT_NETWORK, &error) == REAPER_SYSTEM_DENIED);
    assert(reaper_module_effects_validate(1, REAPER_EFFECT_FILE_READ,
        REAPER_EFFECT_FILE_READ, REAPER_EFFECT_REMOTE_IO, &error) == REAPER_SYSTEM_DENIED);
    assert(reaper_module_effects_validate(0, REAPER_EFFECT_NETWORK,
        REAPER_EFFECT_NETWORK, 0U, &error) == REAPER_SYSTEM_OK);
    assert(reaper_module_effects_validate(0, REAPER_EFFECT_FILE_READ,
        REAPER_EFFECT_NETWORK, 0U, &error) == REAPER_SYSTEM_DENIED);
}

/* 10. Migration and reverse-plan validation */
static void test_migration_requires_tested_forward_and_rollback(void) {
    ReaperSystemError error;
    const ReaperRollbackPlan valid = {"cache.schema.v2", 1U, 2U, "upgrade.v2", "downgrade.v2", 1, 1};
    const ReaperRollbackPlan missing_test = {"cache.schema.v2", 1U, 2U, "upgrade.v2", "downgrade.v2", 1, 0};
    const ReaperRollbackPlan bad_version = {"cache.schema.v2", 2U, 2U, "upgrade.v2", "downgrade.v2", 1, 1};
    assert(reaper_rollback_plan_validate(&valid, &error) == REAPER_SYSTEM_OK);
    assert(reaper_rollback_plan_validate(&missing_test, &error) == REAPER_SYSTEM_UNTESTED_ROLLBACK);
    assert(reaper_rollback_plan_validate(&bad_version, &error) == REAPER_SYSTEM_INVALID_ARGUMENT);
}

int main(void) {
    test_contract_graph_and_compatibility();
    test_arena_slots_are_bounded_and_zeroized();
    test_worker_budget_halts_and_dumps_state();
    test_reconcile_plan_is_deterministic_and_atomic();
    test_ephemeral_scope_matches_then_wipes();
    test_mutation_authorization_requires_revision_and_gate();
    test_lease_window_warns_and_expires();
    test_latency_profiler_reports_percentiles();
    test_local_only_rejects_transitive_network_effects();
    test_migration_requires_tested_forward_and_rollback();
    puts("native system feature tests: 10 groups passed");
    return 0;
}
