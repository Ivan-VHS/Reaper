#ifndef REAPER_HW_GRAPH_H
#define REAPER_HW_GRAPH_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Bounded, deterministic planner for CPU/GPU work graphs.
 *
 * The planner validates dependencies and produces an execution proposal. It
 * does not allocate device memory, submit commands, map MMIO, or access a GPU.
 * A trusted platform adapter remains responsible for execution.
 */
#define REAPER_HW_GRAPH_MAX_NODES 256U
#define REAPER_HW_GRAPH_MAX_QUEUES 32U

enum {
    REAPER_HW_BACKEND_CPU = UINT32_C(1) << 0,
    REAPER_HW_BACKEND_GPU = UINT32_C(1) << 1
};

typedef enum {
    REAPER_HW_GRAPH_OK = 0,
    REAPER_HW_GRAPH_INVALID_ARGUMENT,
    REAPER_HW_GRAPH_INVALID_PROFILE,
    REAPER_HW_GRAPH_TOO_MANY_NODES,
    REAPER_HW_GRAPH_OUTPUT_TOO_SMALL,
    REAPER_HW_GRAPH_DUPLICATE_NODE,
    REAPER_HW_GRAPH_UNKNOWN_DEPENDENCY,
    REAPER_HW_GRAPH_DUPLICATE_DEPENDENCY,
    REAPER_HW_GRAPH_CYCLE,
    REAPER_HW_GRAPH_NO_FEASIBLE_BACKEND,
    REAPER_HW_GRAPH_RESOURCE_LIMIT,
    REAPER_HW_GRAPH_COST_OVERFLOW
} ReaperHwGraphStatus;

/*
 * Rates are caller-supplied measurements for one named target/profile. The
 * planner never probes hardware or validates the provenance of these rates.
 * Memory values are byte budgets and queue counts are bounded by MAX_QUEUES.
 */
typedef struct {
    uint64_t cpu_operations_per_second;
    uint64_t gpu_operations_per_second;
    uint64_t transfer_bytes_per_second;
    uint64_t host_memory_bytes;
    uint64_t gpu_memory_bytes;
    uint32_t cpu_queue_count;
    uint32_t gpu_queue_count;
    int gpu_available;
} ReaperHwExecutionProfile;

/*
 * transfer_bytes is the aggregate transfer volume associated with this node's
 * GPU execution. If this node is placed on CPU and consumes any GPU-produced
 * dependency, the same volume is charged as a conservative device-to-host
 * return transfer. All memory reservations are summed across the full graph;
 * this version does not reuse allocations after a node finishes.
 *
 * The node array and every dependency array are caller-owned and must remain
 * valid for the duration of reaper_hw_graph_plan().
 */
typedef struct {
    uint32_t id;
    uint64_t operations;
    uint64_t transfer_bytes;
    uint64_t host_memory_bytes;
    uint64_t gpu_memory_bytes;
    uint32_t backend_mask;
    const uint32_t *dependencies;
    uint32_t dependency_count;
} ReaperHwGraphNode;

typedef struct {
    uint32_t node_id;
    uint32_t backend;
    uint32_t queue_index;
    uint64_t estimated_start_ns;
    uint64_t estimated_duration_ns;
    uint64_t estimated_finish_ns;
    int requires_cross_backend_sync;
} ReaperHwGraphStep;

typedef struct {
    ReaperHwGraphStatus status;
    uint32_t node_id;
    uint32_t related_node_id;
    char message[160];
} ReaperHwGraphError;

/*
 * Produces a stable topological plan. Output storage must hold node_count
 * steps and must not overlap the input node/dependency storage.
 */
ReaperHwGraphStatus reaper_hw_graph_plan(
    const ReaperHwExecutionProfile *profile,
    const ReaperHwGraphNode *nodes,
    uint32_t node_count,
    ReaperHwGraphStep *steps,
    uint32_t step_capacity,
    uint32_t *step_count,
    ReaperHwGraphError *error
);

const char *reaper_hw_graph_status_name(ReaperHwGraphStatus status);

#ifdef __cplusplus
}
#endif

#endif
