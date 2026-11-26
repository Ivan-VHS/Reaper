#include "reaper/hw_graph.h"

#include <stdio.h>
#include <string.h>

#define NANOSECONDS_PER_SECOND UINT64_C(1000000000)
#define VALID_BACKENDS (REAPER_HW_BACKEND_CPU | REAPER_HW_BACKEND_GPU)

typedef struct {
    uint32_t queue_index;
    uint64_t start_ns;
    uint64_t finish_ns;
    uint64_t duration_ns;
    int feasible;
} QueueChoice;

static ReaperHwGraphStatus fail(
    ReaperHwGraphError *error,
    ReaperHwGraphStatus status,
    uint32_t node_id,
    uint32_t related_node_id,
    const char *message
) {
    if (error != NULL) {
        error->status = status;
        error->node_id = node_id;
        error->related_node_id = related_node_id;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}

static void clear_error(ReaperHwGraphError *error) {
    if (error != NULL) {
        error->status = REAPER_HW_GRAPH_OK;
        error->node_id = 0U;
        error->related_node_id = 0U;
        error->message[0] = '\0';
    }
}

static int add_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (result == NULL || right > UINT64_MAX - left) return 0;
    *result = left + right;
    return 1;
}

/*
 * Calculate floor(value * multiplier / divisor) and its exact remainder.
 * multiplier is bounded by 1e9 at the call sites. The bitwise recurrence
 * keeps the intermediate remainder below divisor, avoiding a 64-bit product.
 */
static void multiply_divide_small(
    uint64_t value,
    uint64_t multiplier,
    uint64_t divisor,
    uint64_t *quotient,
    uint64_t *remainder
) {
    uint64_t q = 0U;
    uint64_t r = 0U;
    int bit;

    for (bit = 63; bit >= 0; --bit) {
        q *= 2U;
        if (r >= divisor - r) {
            r -= divisor - r;
            q += 1U;
        } else {
            r += r;
        }

        if (((multiplier >> (unsigned)bit) & UINT64_C(1)) != 0U) {
            if (value != 0U && r >= divisor - value) {
                r -= divisor - value;
                q += 1U;
            } else {
                r += value;
            }
        }
    }

    *quotient = q;
    *remainder = r;
}

/* Exact ceil(value * 1e9 / rate), with overflow reported to the caller. */
static int estimate_nanoseconds(
    uint64_t value,
    uint64_t rate,
    uint64_t *duration_ns
) {
    uint64_t whole;
    uint64_t fraction;
    uint64_t fraction_remainder;
    uint64_t base;

    if (duration_ns == NULL || rate == 0U) return 0;
    if (value == 0U) {
        *duration_ns = 0U;
        return 1;
    }

    whole = value / rate;
    if (whole > UINT64_MAX / NANOSECONDS_PER_SECOND) return 0;
    base = whole * NANOSECONDS_PER_SECOND;

    multiply_divide_small(
        value % rate, NANOSECONDS_PER_SECOND, rate,
        &fraction, &fraction_remainder
    );
    if (fraction_remainder != 0U) {
        if (fraction == UINT64_MAX) return 0;
        fraction += 1U;
    }
    return add_u64(base, fraction, duration_ns);
}

static int find_node_index(
    const ReaperHwGraphNode *nodes,
    uint32_t node_count,
    uint32_t id,
    uint32_t *index
) {
    uint32_t i;
    for (i = 0U; i < node_count; ++i) {
        if (nodes[i].id == id) {
            if (index != NULL) *index = i;
            return 1;
        }
    }
    return 0;
}

static int validate_profile(const ReaperHwExecutionProfile *profile) {
    if (profile == NULL || profile->cpu_operations_per_second == 0U ||
        profile->host_memory_bytes == 0U || profile->cpu_queue_count == 0U ||
        profile->cpu_queue_count > REAPER_HW_GRAPH_MAX_QUEUES) {
        return 0;
    }
    if (profile->gpu_available != 0 && profile->gpu_available != 1) return 0;
    if (profile->gpu_available != 0 &&
        (profile->gpu_operations_per_second == 0U ||
         profile->transfer_bytes_per_second == 0U ||
         profile->gpu_memory_bytes == 0U ||
         profile->gpu_queue_count == 0U ||
         profile->gpu_queue_count > REAPER_HW_GRAPH_MAX_QUEUES)) {
        return 0;
    }
    return 1;
}

static QueueChoice choose_queue(
    const uint64_t *queue_available,
    uint32_t queue_count,
    uint64_t ready_ns,
    uint64_t duration_ns
) {
    QueueChoice choice = { 0U, 0U, 0U, duration_ns, 0 };
    uint32_t i;

    for (i = 0U; i < queue_count; ++i) {
        uint64_t start_ns = queue_available[i] > ready_ns
            ? queue_available[i] : ready_ns;
        uint64_t finish_ns = 0U;
        if (!add_u64(start_ns, duration_ns, &finish_ns)) continue;
        if (!choice.feasible || finish_ns < choice.finish_ns ||
            (finish_ns == choice.finish_ns && i < choice.queue_index)) {
            choice.queue_index = i;
            choice.start_ns = start_ns;
            choice.finish_ns = finish_ns;
            choice.duration_ns = duration_ns;
            choice.feasible = 1;
        }
    }
    return choice;
}

ReaperHwGraphStatus reaper_hw_graph_plan(
    const ReaperHwExecutionProfile *profile,
    const ReaperHwGraphNode *nodes,
    uint32_t node_count,
    ReaperHwGraphStep *steps,
    uint32_t step_capacity,
    uint32_t *step_count,
    ReaperHwGraphError *error
) {
    uint32_t indegree[REAPER_HW_GRAPH_MAX_NODES];
    uint32_t topological[REAPER_HW_GRAPH_MAX_NODES];
    uint32_t topological_count = 0U;
    uint8_t emitted[REAPER_HW_GRAPH_MAX_NODES];
    uint64_t finish_by_index[REAPER_HW_GRAPH_MAX_NODES];
    uint32_t backend_by_index[REAPER_HW_GRAPH_MAX_NODES];
    uint64_t cpu_queue_available[REAPER_HW_GRAPH_MAX_QUEUES] = {0};
    uint64_t gpu_queue_available[REAPER_HW_GRAPH_MAX_QUEUES] = {0};
    uint64_t host_memory_reserved = 0U;
    uint64_t gpu_memory_reserved = 0U;
    uint32_t i;

    clear_error(error);
    if (step_count != NULL) *step_count = 0U;
    if (profile == NULL || nodes == NULL || steps == NULL || step_count == NULL)
        return fail(error, REAPER_HW_GRAPH_INVALID_ARGUMENT, 0U, 0U,
                    "profile, nodes, steps, and step_count are required");
    if (node_count == 0U)
        return fail(error, REAPER_HW_GRAPH_INVALID_ARGUMENT, 0U, 0U,
                    "graph must contain at least one node");
    if (node_count > REAPER_HW_GRAPH_MAX_NODES)
        return fail(error, REAPER_HW_GRAPH_TOO_MANY_NODES, 0U, 0U,
                    "graph exceeds the fixed node limit");
    if (step_capacity < node_count)
        return fail(error, REAPER_HW_GRAPH_OUTPUT_TOO_SMALL, 0U, 0U,
                    "step output capacity must cover every graph node");
    if (!validate_profile(profile))
        return fail(error, REAPER_HW_GRAPH_INVALID_PROFILE, 0U, 0U,
                    "execution profile has invalid rates, memory, or queue limits");

    memset(indegree, 0, sizeof indegree);
    memset(emitted, 0, sizeof emitted);
    memset(finish_by_index, 0, sizeof finish_by_index);
    memset(backend_by_index, 0, sizeof backend_by_index);

    /* Validate node identity, backend masks, dependencies, and memory budget. */
    for (i = 0U; i < node_count; ++i) {
        uint32_t j;
        const ReaperHwGraphNode *node = &nodes[i];

        if (find_node_index(nodes, i, node->id, NULL))
            return fail(error, REAPER_HW_GRAPH_DUPLICATE_NODE,
                        node->id, 0U, "node identifiers must be unique");
        if (node->backend_mask == 0U ||
            (node->backend_mask & ~((uint32_t)VALID_BACKENDS)) != 0U)
            return fail(error, REAPER_HW_GRAPH_NO_FEASIBLE_BACKEND,
                        node->id, 0U, "node backend mask is empty or unsupported");
        if (node->dependency_count > node_count - 1U ||
            (node->dependency_count != 0U && node->dependencies == NULL))
            return fail(error, REAPER_HW_GRAPH_INVALID_ARGUMENT,
                        node->id, 0U, "node dependency list is invalid");
        if (!add_u64(host_memory_reserved, node->host_memory_bytes,
                      &host_memory_reserved))
            return fail(error, REAPER_HW_GRAPH_RESOURCE_LIMIT,
                        node->id, 0U, "host memory reservation overflows uint64");

        indegree[i] = node->dependency_count;
        for (j = 0U; j < node->dependency_count; ++j) {
            uint32_t dependency_index;
            uint32_t k;
            uint32_t dependency_id = node->dependencies[j];
            if (dependency_id == node->id)
                return fail(error, REAPER_HW_GRAPH_CYCLE,
                            node->id, dependency_id, "node cannot depend on itself");
            if (!find_node_index(nodes, node_count, dependency_id,
                                 &dependency_index))
                return fail(error, REAPER_HW_GRAPH_UNKNOWN_DEPENDENCY,
                            node->id, dependency_id, "dependency identifier does not exist");
            for (k = 0U; k < j; ++k) {
                if (node->dependencies[k] == dependency_id)
                    return fail(error, REAPER_HW_GRAPH_DUPLICATE_DEPENDENCY,
                                node->id, dependency_id, "dependency is listed more than once");
            }
            (void)dependency_index;
        }
    }

    if (host_memory_reserved > profile->host_memory_bytes)
        return fail(error, REAPER_HW_GRAPH_RESOURCE_LIMIT, 0U, 0U,
                    "conservative graph host-memory reservation exceeds profile budget");

    /* Stable Kahn sort: when multiple nodes are ready, preserve input order. */
    while (topological_count < node_count) {
        uint32_t selected = node_count;
        for (i = 0U; i < node_count; ++i) {
            if (emitted[i] == 0U && indegree[i] == 0U) {
                selected = i;
                break;
            }
        }
        if (selected == node_count)
            return fail(error, REAPER_HW_GRAPH_CYCLE, 0U, 0U,
                        "dependency graph contains a cycle");

        emitted[selected] = 1U;
        topological[topological_count++] = selected;

        for (i = 0U; i < node_count; ++i) {
            uint32_t j;
            if (emitted[i] != 0U) continue;
            for (j = 0U; j < nodes[i].dependency_count; ++j) {
                if (nodes[i].dependencies[j] == nodes[selected].id) {
                    if (indegree[i] > 0U) indegree[i] -= 1U;
                    break;
                }
            }
        }
    }

    /* Assign each node to the earliest-finishing feasible CPU/GPU queue. */
    for (i = 0U; i < topological_count; ++i) {
        uint32_t index = topological[i];
        const ReaperHwGraphNode *node = &nodes[index];
        uint64_t ready_ns = 0U;
        int cross_backend_sync = 0;
        int dependency_from_gpu = 0;
        int cpu_cost_overflow = 0;
        int gpu_cost_overflow = 0;
        uint32_t j;
        QueueChoice cpu_choice = {0};
        QueueChoice gpu_choice = {0};
        uint32_t selected_backend;
        QueueChoice selected_choice;

        for (j = 0U; j < node->dependency_count; ++j) {
            uint32_t dependency_index = 0U;
            (void)find_node_index(nodes, node_count, node->dependencies[j],
                                  &dependency_index);
            if (finish_by_index[dependency_index] > ready_ns)
                ready_ns = finish_by_index[dependency_index];
            if (backend_by_index[dependency_index] == REAPER_HW_BACKEND_GPU)
                dependency_from_gpu = 1;
        }

        if ((node->backend_mask & REAPER_HW_BACKEND_CPU) != 0U &&
            node->host_memory_bytes <= profile->host_memory_bytes) {
            uint64_t cpu_duration = 0U;
            uint64_t return_transfer_ns = 0U;
            if (!estimate_nanoseconds(node->operations,
                                      profile->cpu_operations_per_second,
                                      &cpu_duration) ||
                (dependency_from_gpu &&
                 (!estimate_nanoseconds(node->transfer_bytes,
                                        profile->transfer_bytes_per_second,
                                        &return_transfer_ns) ||
                  !add_u64(cpu_duration, return_transfer_ns, &cpu_duration)))) {
                cpu_cost_overflow = 1;
            } else {
                cpu_choice = choose_queue(cpu_queue_available,
                                          profile->cpu_queue_count,
                                          ready_ns, cpu_duration);
            }
        }

        if ((node->backend_mask & REAPER_HW_BACKEND_GPU) != 0U &&
            profile->gpu_available != 0 &&
            node->gpu_memory_bytes <= profile->gpu_memory_bytes - gpu_memory_reserved) {
            uint64_t compute_ns = 0U;
            uint64_t transfer_ns = 0U;
            uint64_t gpu_duration = 0U;
            if (!estimate_nanoseconds(node->operations,
                                      profile->gpu_operations_per_second,
                                      &compute_ns) ||
                !estimate_nanoseconds(node->transfer_bytes,
                                      profile->transfer_bytes_per_second,
                                      &transfer_ns) ||
                !add_u64(compute_ns, transfer_ns, &gpu_duration)) {
                gpu_cost_overflow = 1;
            } else {
                gpu_choice = choose_queue(gpu_queue_available,
                                          profile->gpu_queue_count,
                                          ready_ns, gpu_duration);
            }
        }

        if (!cpu_choice.feasible && !gpu_choice.feasible) {
            if (cpu_cost_overflow || gpu_cost_overflow)
                return fail(error, REAPER_HW_GRAPH_COST_OVERFLOW,
                            node->id, 0U, "all otherwise eligible backend cost estimates overflow");
            return fail(error, REAPER_HW_GRAPH_NO_FEASIBLE_BACKEND,
                        node->id, 0U, "no backend satisfies node capabilities and resource budgets");
        }

        /* CPU wins exact ties to avoid an unnecessary device transfer. */
        if (cpu_choice.feasible &&
            (!gpu_choice.feasible || cpu_choice.finish_ns <= gpu_choice.finish_ns)) {
            selected_backend = REAPER_HW_BACKEND_CPU;
            selected_choice = cpu_choice;
            cpu_queue_available[selected_choice.queue_index] = selected_choice.finish_ns;
        } else {
            selected_backend = REAPER_HW_BACKEND_GPU;
            selected_choice = gpu_choice;
            gpu_queue_available[selected_choice.queue_index] = selected_choice.finish_ns;
            if (!add_u64(gpu_memory_reserved, node->gpu_memory_bytes,
                         &gpu_memory_reserved))
                return fail(error, REAPER_HW_GRAPH_RESOURCE_LIMIT,
                            node->id, 0U, "GPU memory reservation overflows uint64");
        }

        cross_backend_sync = 0;
        for (j = 0U; j < node->dependency_count; ++j) {
            uint32_t dependency_index = 0U;
            (void)find_node_index(nodes, node_count, node->dependencies[j],
                                  &dependency_index);
            if (backend_by_index[dependency_index] != selected_backend)
                cross_backend_sync = 1;
        }

        backend_by_index[index] = selected_backend;
        finish_by_index[index] = selected_choice.finish_ns;
        steps[i].node_id = node->id;
        steps[i].backend = selected_backend;
        steps[i].queue_index = selected_choice.queue_index;
        steps[i].estimated_start_ns = selected_choice.start_ns;
        steps[i].estimated_duration_ns = selected_choice.duration_ns;
        steps[i].estimated_finish_ns = selected_choice.finish_ns;
        steps[i].requires_cross_backend_sync = cross_backend_sync;
    }

    *step_count = node_count;
    return REAPER_HW_GRAPH_OK;
}

const char *reaper_hw_graph_status_name(ReaperHwGraphStatus status) {
    switch (status) {
    case REAPER_HW_GRAPH_OK: return "ok";
    case REAPER_HW_GRAPH_INVALID_ARGUMENT: return "invalid_argument";
    case REAPER_HW_GRAPH_INVALID_PROFILE: return "invalid_profile";
    case REAPER_HW_GRAPH_TOO_MANY_NODES: return "too_many_nodes";
    case REAPER_HW_GRAPH_OUTPUT_TOO_SMALL: return "output_too_small";
    case REAPER_HW_GRAPH_DUPLICATE_NODE: return "duplicate_node";
    case REAPER_HW_GRAPH_UNKNOWN_DEPENDENCY: return "unknown_dependency";
    case REAPER_HW_GRAPH_DUPLICATE_DEPENDENCY: return "duplicate_dependency";
    case REAPER_HW_GRAPH_CYCLE: return "cycle";
    case REAPER_HW_GRAPH_NO_FEASIBLE_BACKEND: return "no_feasible_backend";
    case REAPER_HW_GRAPH_RESOURCE_LIMIT: return "resource_limit";
    case REAPER_HW_GRAPH_COST_OVERFLOW: return "cost_overflow";
    default: return "unknown";
    }
}
