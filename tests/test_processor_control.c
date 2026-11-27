#include "reaper/processor_control.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void test_topology_and_affinity(void) {
    ReaperLogicalCpu cpus[] = {
        {0U, 0U, 0U, 4U, REAPER_CPU_ONLINE},
        {1U, 0U, 0U, 4U, REAPER_CPU_ONLINE},
        {2U, 1U, 0U, 4U, REAPER_CPU_OFFLINE},
        {3U, 1U, 0U, 4U, REAPER_CPU_ONLINE}
    };
    ReaperProcessorTopology topology = {4U, 3U, 4U};
    assert(reaper_processor_topology_validate(cpus, 4U, &topology) == REAPER_PROCESSOR_OK);
    cpus[3].logical_id = 2U;
    assert(reaper_processor_topology_validate(cpus, 4U, &topology) == REAPER_PROCESSOR_DUPLICATE_CPU);
    cpus[3].logical_id = 3U;
    topology.online_cpu_count = 4U;
    assert(reaper_processor_topology_validate(cpus, 4U, &topology) == REAPER_PROCESSOR_INVALID_TOPOLOGY);
    assert(reaper_processor_affinity_contains(UINT64_C(0x8000000000000001), 63U));
    assert(!reaper_processor_affinity_contains(UINT64_C(1), 64U));
}

static void test_scheduler_order_and_round_robin(void) {
    ReaperProcessorThread threads[] = {
        {11U, 50U, UINT64_C(0x3), 10U, 10, 0U, REAPER_THREAD_READY},
        {12U, 20U, UINT64_C(0x1), 10U, 20, 0U, REAPER_THREAD_READY},
        {13U, 0U, UINT64_C(0x1), 10U, 20, 0U, REAPER_THREAD_READY},
        {14U, 5U, UINT64_C(0x2), 10U, 20, 0U, REAPER_THREAD_READY}
    };
    size_t selected = SIZE_MAX;
    assert(reaper_processor_select_next(threads, 4U, 0U, 0U, &selected) == REAPER_PROCESSOR_OK);
    assert(threads[selected].thread_id == 12U);
    assert(reaper_processor_select_next(threads, 4U, 0U, 12U, &selected) == REAPER_PROCESSOR_OK);
    assert(threads[selected].thread_id == 13U);
    assert(reaper_processor_select_next(threads, 4U, 1U, 0U, &selected) == REAPER_PROCESSOR_OK);
    assert(threads[selected].thread_id == 14U);
    threads[2].state = REAPER_THREAD_BLOCKED;
    threads[0].state = REAPER_THREAD_BLOCKED;
    assert(reaper_processor_select_next(threads, 4U, 0U, 0U, &selected) == REAPER_PROCESSOR_UNSUPPORTED);
}

static void test_thread_and_cpu_lifecycle(void) {
    assert(reaper_processor_thread_transition_valid(REAPER_THREAD_CREATED, REAPER_THREAD_READY));
    assert(reaper_processor_thread_transition_valid(REAPER_THREAD_RUNNING, REAPER_THREAD_SLEEPING));
    assert(!reaper_processor_thread_transition_valid(REAPER_THREAD_ZOMBIE, REAPER_THREAD_READY));
    assert(!reaper_processor_core_offline_allowed(REAPER_CPU_ONLINE, 0U, 0U, 0U, 0U, 0U));
    assert(!reaper_processor_core_offline_allowed(REAPER_CPU_DRAINING, 0U, 1U, 0U, 0U, 0U));
    assert(reaper_processor_core_offline_allowed(REAPER_CPU_DRAINING, 0U, 0U, 0U, 0U, 0U));
}

static void test_ap_startup_context_and_debug(void) {
    assert(reaper_processor_ap_startup_validate(1, 1, 1, 1, 1, 1, 1) == REAPER_PROCESSOR_OK);
    assert(reaper_processor_ap_startup_validate(1, 0, 1, 1, 1, 1, 1) == REAPER_PROCESSOR_NOT_QUIESCENT);
    uint8_t stack[512];
    uintptr_t base = (uintptr_t)stack;
    uintptr_t aligned = (base + 15U) & ~(uintptr_t)15U;
    assert(reaper_processor_context_frame_validate(aligned, sizeof(stack) - (size_t)(aligned - base), aligned) == REAPER_PROCESSOR_OK);
    assert(reaper_processor_context_frame_validate(aligned, sizeof(stack) - (size_t)(aligned - base), aligned + 8U) == REAPER_PROCESSOR_OK);
    assert(reaper_processor_context_frame_validate(aligned, 64U, aligned) == REAPER_PROCESSOR_INVALID_TOPOLOGY);
    assert(reaper_processor_context_frame_validate(aligned, sizeof(stack), aligned + 1U) == REAPER_PROCESSOR_INVALID_TOPOLOGY);

    ReaperProcessorDebugSession session = {1U, 5000U, 4096U, 0U, 1U, 0U};
    assert(reaper_processor_debug_session_validate(&session, 4U) == REAPER_PROCESSOR_ACCESS_DENIED);
    session.capabilities = 1U;
    assert(reaper_processor_debug_session_validate(&session, 4U) == REAPER_PROCESSOR_OK);
    session.cpu_id = 4U;
    assert(reaper_processor_debug_session_validate(&session, 4U) == REAPER_PROCESSOR_INVALID_ARGUMENT);
}

static void test_live_update_and_power(void) {
    ReaperProcessorRevision active = {1U, 8U, REAPER_REVISION_ACTIVE, {1U}};
    ReaperProcessorRevision candidate = {1U, 9U, REAPER_REVISION_STAGED, {2U}};
    ReaperProcessorEvidence evidence = {100U, 100U, 0U, 9500U, {2U}};
    assert(reaper_processor_live_update_validate(&active, &candidate, &evidence,
        1, 1, 1, 1, 1) == REAPER_PROCESSOR_OK);
    assert(reaper_processor_live_update_validate(&active, &candidate, &evidence,
        1, 1, 1, 0, 1) == REAPER_PROCESSOR_ACCESS_DENIED);
    candidate.abi_major = 2U;
    assert(reaper_processor_live_update_validate(&active, &candidate, &evidence,
        1, 1, 1, 1, 1) == REAPER_PROCESSOR_INCOMPATIBLE_ABI);
    assert(reaper_processor_power_request_validate(1, 0, 1) == REAPER_PROCESSOR_ACCESS_DENIED);
    assert(reaper_processor_power_request_validate(1, 1, 0) == REAPER_PROCESSOR_UNSUPPORTED);
    assert(reaper_processor_power_request_validate(1, 1, 1) == REAPER_PROCESSOR_OK);
}

typedef struct {
    uint32_t frequency_calls;
    uint32_t power_calls;
    uint32_t debug_calls;
    uint32_t verify_calls;
    uint32_t stage_calls;
    uint32_t activate_calls;
    uint32_t rollback_calls;
    uint64_t staged_generation;
} FakeProcessorAdapter;

static ReaperProcessorStatus fake_frequency(
    void *context, uint32_t cpu_id, uint32_t minimum_khz,
    uint32_t target_khz, uint32_t maximum_khz, uint32_t generation
) {
    FakeProcessorAdapter *fake = (FakeProcessorAdapter *)context;
    assert(cpu_id == 1U && minimum_khz <= target_khz);
    assert(target_khz <= maximum_khz && generation == 4U);
    ++fake->frequency_calls;
    return REAPER_PROCESSOR_OK;
}

static ReaperProcessorStatus fake_power_profile(
    void *context, uint32_t cpu_id, ReaperProcessorPowerProfile profile,
    uint32_t generation
) {
    FakeProcessorAdapter *fake = (FakeProcessorAdapter *)context;
    assert(cpu_id == 1U && profile == REAPER_PROCESSOR_POWER_BALANCED);
    assert(generation == 4U);
    ++fake->power_calls;
    return REAPER_PROCESSOR_OK;
}

static ReaperProcessorStatus fake_debug(
    void *context, uint32_t cpu_id, uint32_t flags,
    uint32_t timeout_ms, uint8_t *buffer,
    size_t capacity, size_t *written
) {
    FakeProcessorAdapter *fake = (FakeProcessorAdapter *)context;
    assert(cpu_id == 0U && flags == 1U && timeout_ms == 500U);
    ++fake->debug_calls;
    const size_t count = capacity < 8U ? capacity : 8U;
    for (size_t i = 0U; i < count; ++i) buffer[i] = (uint8_t)(i + 1U);
    *written = count;
    return REAPER_PROCESSOR_OK;
}

static ReaperProcessorStatus fake_verify(
    void *context, const uint8_t *image, size_t image_size,
    const uint8_t digest[REAPER_PROCESSOR_DIGEST_BYTES],
    const uint8_t *signature, size_t signature_size
) {
    FakeProcessorAdapter *fake = (FakeProcessorAdapter *)context;
    ++fake->verify_calls;
    if (image == NULL || image_size == 0U || signature == NULL ||
        signature_size != 1U || signature[0] != 0xa5U ||
        image[0] != digest[0])
        return REAPER_PROCESSOR_ACCESS_DENIED;
    return REAPER_PROCESSOR_OK;
}

static ReaperProcessorStatus fake_stage(
    void *context, uint64_t generation,
    const uint8_t digest[REAPER_PROCESSOR_DIGEST_BYTES],
    const uint8_t *image, size_t image_size, uint64_t *ticket
) {
    FakeProcessorAdapter *fake = (FakeProcessorAdapter *)context;
    assert(image != NULL && image_size > 0U && image[0] == digest[0]);
    ++fake->stage_calls;
    fake->staged_generation = generation;
    *ticket = UINT64_C(77);
    return REAPER_PROCESSOR_OK;
}

static ReaperProcessorStatus fake_activate(
    void *context, uint64_t ticket, uint64_t generation
) {
    FakeProcessorAdapter *fake = (FakeProcessorAdapter *)context;
    assert(ticket == UINT64_C(77) && generation == fake->staged_generation);
    ++fake->activate_calls;
    return REAPER_PROCESSOR_OK;
}

static ReaperProcessorStatus fake_rollback(
    void *context, uint64_t ticket, uint64_t known_good_generation
) {
    FakeProcessorAdapter *fake = (FakeProcessorAdapter *)context;
    assert(ticket == UINT64_C(77) && known_good_generation + 1U == fake->staged_generation);
    ++fake->rollback_calls;
    return REAPER_PROCESSOR_OK;
}

static void test_capability_gated_platform_adapters(void) {
    FakeProcessorAdapter fake = {0};
    ReaperProcessorPlatformOps ops = {
        .context = &fake,
        .capabilities = REAPER_PROCESSOR_CAP_POWER_CONTROL |
                        REAPER_PROCESSOR_CAP_DEBUG_CAPTURE |
                        REAPER_PROCESSOR_CAP_PATCH_STAGE |
                        REAPER_PROCESSOR_CAP_PATCH_ACTIVATE |
                        REAPER_PROCESSOR_CAP_PATCH_ROLLBACK,
        .set_frequency_cap = fake_frequency,
        .set_power_profile = fake_power_profile,
        .debug_capture = fake_debug,
        .verify_artifact = fake_verify,
        .stage_patch = fake_stage,
        .activate_patch = fake_activate,
        .rollback_patch = fake_rollback
    };

    assert(reaper_processor_apply_frequency_cap(
        &ops, 1U, 800000U, 3000000U, 5000000U, 4U
    ) == REAPER_PROCESSOR_OK);
    assert(fake.frequency_calls == 1U);
    assert(reaper_processor_apply_power_profile(
        &ops, 1U, REAPER_PROCESSOR_POWER_BALANCED, 4U
    ) == REAPER_PROCESSOR_OK);
    assert(fake.power_calls == 1U);
    assert(reaper_processor_apply_power_profile(
        &ops, 1U, (ReaperProcessorPowerProfile)99, 4U
    ) == REAPER_PROCESSOR_INVALID_ARGUMENT);
    assert(reaper_processor_apply_frequency_cap(
        &ops, 1U, 4000000U, 3000000U, 5000000U, 4U
    ) == REAPER_PROCESSOR_INVALID_ARGUMENT);

    ReaperProcessorDebugSession session = {
        0U, 500U, 16U, UINT32_C(1), 1U, 0U
    };
    uint8_t capture[32] = {0U};
    size_t written = 0U;
    assert(reaper_processor_debug_capture(
        &ops, &session, 2U, capture, sizeof(capture), &written
    ) == REAPER_PROCESSOR_OK);
    assert(written == 8U && capture[0] == 1U && fake.debug_calls == 1U);
    session.capture_limit = 100U;
    assert(reaper_processor_debug_capture(
        &ops, &session, 2U, capture, sizeof(capture), &written
    ) == REAPER_PROCESSOR_OUTPUT_TOO_LARGE);

    const uint8_t active_digest[REAPER_PROCESSOR_DIGEST_BYTES] = {1U};
    const uint8_t candidate_digest[REAPER_PROCESSOR_DIGEST_BYTES] = {2U};
    const uint8_t image[] = {2U, 3U, 4U, 5U};
    const uint8_t signature[] = {0xa5U};
    ReaperProcessorRevision active = {
        1U, 8U, REAPER_REVISION_ACTIVE, {1U}
    };
    ReaperProcessorRevision candidate = {
        1U, 9U, REAPER_REVISION_STAGED, {2U}
    };
    ReaperProcessorEvidence evidence = {
        100U, 100U, 0U, 9500U, {2U}
    };
    ReaperProcessorPatchTicket ticket = {0};

    (void)active_digest;
    (void)candidate_digest;
    assert(reaper_processor_stage_patch(
        &ops, &active, &candidate, &evidence,
        image, sizeof(image), signature, sizeof(signature),
        1, 1, 1, 1, &ticket
    ) == REAPER_PROCESSOR_OK);
    assert(ticket.token == UINT64_C(77));
    assert(fake.verify_calls == 1U && fake.stage_calls == 1U);
    assert(reaper_processor_activate_patch(&ops, &ticket, 1, 0)
           == REAPER_PROCESSOR_NOT_QUIESCENT);
    assert(reaper_processor_activate_patch(&ops, &ticket, 1, 1)
           == REAPER_PROCESSOR_OK);
    assert(reaper_processor_rollback_patch(&ops, &ticket, 8U)
           == REAPER_PROCESSOR_OK);
    assert(fake.activate_calls == 1U && fake.rollback_calls == 1U);

    const uint8_t bad_signature[] = {0U};
    ReaperProcessorPatchTicket rejected = {0};
    assert(reaper_processor_stage_patch(
        &ops, &active, &candidate, &evidence,
        image, sizeof(image), bad_signature, sizeof(bad_signature),
        1, 1, 1, 1, &rejected
    ) == REAPER_PROCESSOR_ACCESS_DENIED);
    assert(fake.stage_calls == 1U);
}

int main(void) {
    test_topology_and_affinity();
    test_scheduler_order_and_round_robin();
    test_thread_and_cpu_lifecycle();
    test_ap_startup_context_and_debug();
    test_live_update_and_power();
    test_capability_gated_platform_adapters();
    puts("Reaper native processor-control tests passed");
    return 0;
}
