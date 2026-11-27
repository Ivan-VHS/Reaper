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

int main(void) {
    test_topology_and_affinity();
    test_scheduler_order_and_round_robin();
    test_thread_and_cpu_lifecycle();
    test_ap_startup_context_and_debug();
    test_live_update_and_power();
    puts("Reaper native processor-control tests passed");
    return 0;
}
