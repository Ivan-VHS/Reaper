#include "reaper/hw_graph.h"

#include <assert.h>
#include <stdio.h>

static ReaperHwExecutionProfile make_profile(void) {
    ReaperHwExecutionProfile profile = {
        UINT64_C(100000000), UINT64_C(1000000000),
        UINT64_C(1000000000), UINT64_C(1) << 30,
        UINT64_C(1) << 30, 2U, 2U, 1
    };
    return profile;
}

static void test_large_compute_prefers_gpu(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 1U, UINT64_C(100000000), UINT64_C(1048576), 4096U,
          UINT64_C(16) << 20,
          REAPER_HW_BACKEND_CPU | REAPER_HW_BACKEND_GPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[1];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    assert(reaper_hw_graph_plan(&profile, nodes, 1U, steps, 1U,
        &count, &error) == REAPER_HW_GRAPH_OK);
    assert(count == 1U);
    assert(steps[0].backend == REAPER_HW_BACKEND_GPU);
    assert(steps[0].queue_index < profile.gpu_queue_count);
    assert(steps[0].estimated_finish_ns > 0U);
}

static void test_transfer_cost_can_keep_work_on_cpu(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 2U, 100U, UINT64_C(2000000), 1024U, 4096U,
          REAPER_HW_BACKEND_CPU | REAPER_HW_BACKEND_GPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[1];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    assert(reaper_hw_graph_plan(&profile, nodes, 1U, steps, 1U,
        &count, &error) == REAPER_HW_GRAPH_OK);
    assert(steps[0].backend == REAPER_HW_BACKEND_CPU);
}

static void test_dependency_order_and_cross_backend_barrier(void) {
    ReaperHwExecutionProfile profile = make_profile();
    const uint32_t dependency[] = { 10U };
    ReaperHwGraphNode nodes[] = {
        { 20U, UINT64_C(100000000), 4096U, 4096U, 4096U,
          REAPER_HW_BACKEND_GPU, dependency, 1U },
        { 10U, UINT64_C(1000000), 0U, 4096U, 0U,
          REAPER_HW_BACKEND_CPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[2];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    assert(reaper_hw_graph_plan(&profile, nodes, 2U, steps, 2U,
        &count, &error) == REAPER_HW_GRAPH_OK);
    assert(count == 2U);
    assert(steps[0].node_id == 10U);
    assert(steps[1].node_id == 20U);
    assert(steps[1].estimated_start_ns >= steps[0].estimated_finish_ns);
    assert(steps[1].requires_cross_backend_sync == 1);
}

static void test_cycle_and_unknown_dependency_are_rejected(void) {
    ReaperHwExecutionProfile profile = make_profile();
    const uint32_t dep_a[] = { 2U };
    const uint32_t dep_b[] = { 1U };
    ReaperHwGraphNode cycle[] = {
        { 1U, 1U, 0U, 0U, 0U, REAPER_HW_BACKEND_CPU, dep_a, 1U },
        { 2U, 1U, 0U, 0U, 0U, REAPER_HW_BACKEND_CPU, dep_b, 1U }
    };
    const uint32_t missing[] = { 99U };
    ReaperHwGraphNode unknown[] = {
        { 1U, 1U, 0U, 0U, 0U, REAPER_HW_BACKEND_CPU, missing, 1U },
        { 2U, 1U, 0U, 0U, 0U, REAPER_HW_BACKEND_CPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[2];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    assert(reaper_hw_graph_plan(&profile, cycle, 2U, steps, 2U,
        &count, &error) == REAPER_HW_GRAPH_CYCLE);
    assert(reaper_hw_graph_plan(&profile, unknown, 2U, steps, 2U,
        &count, &error) == REAPER_HW_GRAPH_UNKNOWN_DEPENDENCY);
}

static void test_gpu_memory_budget_falls_back_to_cpu(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 7U, UINT64_C(100000000), 1024U, 4096U,
          (UINT64_C(2) << 30),
          REAPER_HW_BACKEND_CPU | REAPER_HW_BACKEND_GPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[1];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    assert(reaper_hw_graph_plan(&profile, nodes, 1U, steps, 1U,
        &count, &error) == REAPER_HW_GRAPH_OK);
    assert(steps[0].backend == REAPER_HW_BACKEND_CPU);
}

static void test_host_memory_budget_and_output_capacity(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 1U, 100U, 0U, profile.host_memory_bytes, 0U,
          REAPER_HW_BACKEND_CPU, NULL, 0U },
        { 2U, 100U, 0U, 1U, 0U,
          REAPER_HW_BACKEND_CPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[2];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    assert(reaper_hw_graph_plan(&profile, nodes, 2U, steps, 2U,
        &count, &error) == REAPER_HW_GRAPH_RESOURCE_LIMIT);
    assert(reaper_hw_graph_plan(&profile, nodes, 2U, steps, 1U,
        &count, &error) == REAPER_HW_GRAPH_OUTPUT_TOO_SMALL);
}

static void test_gpu_only_without_device_fails_closed(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 5U, 1U, 0U, 0U, 0U, REAPER_HW_BACKEND_GPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[1];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    profile.gpu_available = 0;
    assert(reaper_hw_graph_plan(&profile, nodes, 1U, steps, 1U,
        &count, &error) == REAPER_HW_GRAPH_NO_FEASIBLE_BACKEND);
}

static void test_gpu_to_cpu_edge_accounts_for_return_transfer(void) {
    ReaperHwExecutionProfile profile = make_profile();
    const uint32_t dependency[] = { 30U };
    ReaperHwGraphNode nodes[] = {
        { 31U, UINT64_C(100000000), UINT64_C(1000000000), 4096U, 0U,
          REAPER_HW_BACKEND_CPU, dependency, 1U },
        { 30U, UINT64_C(100000000), 4096U, 4096U, 4096U,
          REAPER_HW_BACKEND_GPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[2];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    assert(reaper_hw_graph_plan(&profile, nodes, 2U, steps, 2U,
        &count, &error) == REAPER_HW_GRAPH_OK);
    assert(steps[0].node_id == 30U);
    assert(steps[1].node_id == 31U);
    assert(steps[1].requires_cross_backend_sync == 1);
    assert(steps[1].estimated_duration_ns == UINT64_C(2000000000));
}

static void test_cpu_queues_overlap_independent_nodes(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 41U, UINT64_C(100000000), 0U, 1024U, 0U,
          REAPER_HW_BACKEND_CPU, NULL, 0U },
        { 42U, UINT64_C(100000000), 0U, 1024U, 0U,
          REAPER_HW_BACKEND_CPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[2];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    assert(reaper_hw_graph_plan(&profile, nodes, 2U, steps, 2U,
        &count, &error) == REAPER_HW_GRAPH_OK);
    assert(steps[0].queue_index != steps[1].queue_index);
    assert(steps[0].estimated_start_ns == 0U);
    assert(steps[1].estimated_start_ns == 0U);
}

static void test_cost_overflow_on_one_backend_allows_other_backend(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 61U, UINT64_MAX, 0U, 0U, 0U,
          REAPER_HW_BACKEND_CPU | REAPER_HW_BACKEND_GPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[1];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    profile.cpu_operations_per_second = 1U;
    profile.gpu_operations_per_second = UINT64_C(1000000000000000000);
    assert(reaper_hw_graph_plan(&profile, nodes, 1U, steps, 1U,
        &count, &error) == REAPER_HW_GRAPH_OK);
    assert(steps[0].backend == REAPER_HW_BACKEND_GPU);
}

static void test_cost_overflow_when_all_eligible_backends_overflow(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 62U, UINT64_MAX, 0U, 0U, 0U,
          REAPER_HW_BACKEND_CPU | REAPER_HW_BACKEND_GPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[1];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    profile.cpu_operations_per_second = 1U;
    profile.gpu_operations_per_second = 1U;
    assert(reaper_hw_graph_plan(&profile, nodes, 1U, steps, 1U,
        &count, &error) == REAPER_HW_GRAPH_COST_OVERFLOW);
    assert(count == 0U);
}

static void test_nanosecond_estimate_rounds_up(void) {
    ReaperHwExecutionProfile profile = make_profile();
    ReaperHwGraphNode nodes[] = {
        { 51U, 1U, 0U, 0U, 0U, REAPER_HW_BACKEND_CPU, NULL, 0U }
    };
    ReaperHwGraphStep steps[1];
    ReaperHwGraphError error = {0};
    uint32_t count = 0U;
    profile.cpu_operations_per_second = 3U;
    assert(reaper_hw_graph_plan(&profile, nodes, 1U, steps, 1U,
        &count, &error) == REAPER_HW_GRAPH_OK);
    assert(steps[0].estimated_duration_ns == UINT64_C(333333334));
}

int main(void) {
    test_large_compute_prefers_gpu();
    test_transfer_cost_can_keep_work_on_cpu();
    test_dependency_order_and_cross_backend_barrier();
    test_cycle_and_unknown_dependency_are_rejected();
    test_gpu_memory_budget_falls_back_to_cpu();
    test_host_memory_budget_and_output_capacity();
    test_gpu_only_without_device_fails_closed();
    test_gpu_to_cpu_edge_accounts_for_return_transfer();
    test_cpu_queues_overlap_independent_nodes();
    test_cost_overflow_on_one_backend_allows_other_backend();
    test_cost_overflow_when_all_eligible_backends_overflow();
    test_nanosecond_estimate_rounds_up();
    puts("hardware graph planner tests: 12 groups passed");
    return 0;
}
