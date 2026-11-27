#ifndef REAPER_PROCESSOR_CONTROL_H
#define REAPER_PROCESSOR_CONTROL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_PROCESSOR_MAX_LOGICAL_CPUS 64U
#define REAPER_PROCESSOR_DIGEST_BYTES 32U

typedef enum {
    REAPER_PROCESSOR_OK = 0,
    REAPER_PROCESSOR_INVALID_ARGUMENT,
    REAPER_PROCESSOR_INVALID_TOPOLOGY,
    REAPER_PROCESSOR_DUPLICATE_CPU,
    REAPER_PROCESSOR_STALE_GENERATION,
    REAPER_PROCESSOR_INVALID_STATE,
    REAPER_PROCESSOR_NOT_QUIESCENT,
    REAPER_PROCESSOR_ACCESS_DENIED,
    REAPER_PROCESSOR_INCOMPATIBLE_ABI,
    REAPER_PROCESSOR_INVALID_EVIDENCE,
    REAPER_PROCESSOR_UNSUPPORTED
} ReaperProcessorStatus;

typedef enum {
    REAPER_CPU_OFFLINE = 0,
    REAPER_CPU_STARTING,
    REAPER_CPU_ONLINE,
    REAPER_CPU_DRAINING,
    REAPER_CPU_QUARANTINED,
    REAPER_CPU_FAILED
} ReaperCpuState;

typedef enum {
    REAPER_THREAD_CREATED = 0,
    REAPER_THREAD_READY,
    REAPER_THREAD_RUNNING,
    REAPER_THREAD_BLOCKED,
    REAPER_THREAD_SLEEPING,
    REAPER_THREAD_ZOMBIE
} ReaperThreadState;

typedef enum {
    REAPER_REVISION_DRAFT = 0,
    REAPER_REVISION_VERIFIED,
    REAPER_REVISION_STAGED,
    REAPER_REVISION_ACTIVE,
    REAPER_REVISION_RETIRED,
    REAPER_REVISION_REJECTED
} ReaperRevisionState;

typedef struct {
    uint32_t logical_id;
    uint32_t core_id;
    uint32_t package_id;
    uint32_t generation;
    ReaperCpuState state;
} ReaperLogicalCpu;

typedef struct {
    uint64_t thread_id;
    uint64_t deadline_ns;
    uint64_t affinity_mask;
    uint64_t quantum_remaining;
    int32_t priority;
    uint32_t last_cpu;
    ReaperThreadState state;
} ReaperProcessorThread;

typedef struct {
    uint32_t logical_cpu_count;
    uint32_t online_cpu_count;
    uint32_t generation;
} ReaperProcessorTopology;

typedef struct {
    uint32_t abi_major;
    uint64_t generation;
    ReaperRevisionState state;
    uint8_t source_digest[REAPER_PROCESSOR_DIGEST_BYTES];
} ReaperProcessorRevision;

typedef struct {
    uint32_t tests_total;
    uint32_t tests_passed;
    uint32_t tests_failed;
    uint32_t coverage_basis_points;
    uint8_t artifact_digest[REAPER_PROCESSOR_DIGEST_BYTES];
} ReaperProcessorEvidence;

typedef struct {
    uint32_t cpu_id;
    uint32_t timeout_ms;
    uint32_t capture_limit;
    uint32_t capabilities;
    uint8_t trace_enabled;
    uint8_t single_step_enabled;
} ReaperProcessorDebugSession;

ReaperProcessorStatus reaper_processor_topology_validate(
    const ReaperLogicalCpu *cpus, size_t cpu_count,
    const ReaperProcessorTopology *topology
);

int reaper_processor_affinity_contains(uint64_t affinity_mask, uint32_t cpu_id);
ReaperProcessorStatus reaper_processor_select_next(
    const ReaperProcessorThread *threads, size_t thread_count,
    uint32_t cpu_id, uint64_t after_thread_id, size_t *selected_index
);

int reaper_processor_thread_transition_valid(
    ReaperThreadState current, ReaperThreadState next
);

int reaper_processor_core_offline_allowed(
    ReaperCpuState state, uint32_t runnable_threads,
    uint32_t active_interrupts, uint32_t held_locks,
    uint32_t dma_leases, uint32_t preempt_depth
);

ReaperProcessorStatus reaper_processor_ap_startup_validate(
    int bootstrap_ready, int local_controller_ready,
    int stack_ready, int gdt_ready, int idt_ready,
    int per_cpu_ready, int trampoline_ready
);

ReaperProcessorStatus reaper_processor_context_frame_validate(
    uintptr_t stack_base, size_t stack_size, uintptr_t saved_stack_pointer
);

ReaperProcessorStatus reaper_processor_live_update_validate(
    const ReaperProcessorRevision *active,
    const ReaperProcessorRevision *candidate,
    const ReaperProcessorEvidence *evidence,
    int signature_valid, int abi_compatible,
    int safe_point, int quiescent, int rollback_ready
);

ReaperProcessorStatus reaper_processor_power_request_validate(
    int request_in_range, int capability_granted, int native_adapter_ready
);

ReaperProcessorStatus reaper_processor_debug_session_validate(
    const ReaperProcessorDebugSession *session,
    uint32_t logical_cpu_count
);

const char *reaper_processor_status_name(ReaperProcessorStatus status);

#ifdef __cplusplus
}
#endif

#endif
