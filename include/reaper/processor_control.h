#ifndef REAPER_PROCESSOR_CONTROL_H
#define REAPER_PROCESSOR_CONTROL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_PROCESSOR_MAX_LOGICAL_CPUS 64U
#define REAPER_PROCESSOR_DIGEST_BYTES 32U
#define REAPER_PROCESSOR_MAX_PATCH_BYTES (16U * 1024U * 1024U)
#define REAPER_PROCESSOR_MAX_DEBUG_BYTES (64U * 1024U)

enum {
    REAPER_PROCESSOR_CAP_POWER_CONTROL = UINT32_C(1) << 0,
    REAPER_PROCESSOR_CAP_DEBUG_CAPTURE = UINT32_C(1) << 1,
    REAPER_PROCESSOR_CAP_PATCH_STAGE = UINT32_C(1) << 2,
    REAPER_PROCESSOR_CAP_PATCH_ACTIVATE = UINT32_C(1) << 3,
    REAPER_PROCESSOR_CAP_PATCH_ROLLBACK = UINT32_C(1) << 4
};

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
    REAPER_PROCESSOR_UNSUPPORTED,
    REAPER_PROCESSOR_ADAPTER_FAILURE,
    REAPER_PROCESSOR_OUTPUT_TOO_LARGE
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

typedef struct {
    uint64_t token;
    uint64_t generation;
    uint32_t abi_major;
    uint8_t digest[REAPER_PROCESSOR_DIGEST_BYTES];
} ReaperProcessorPatchTicket;

typedef enum {
    REAPER_PROCESSOR_POWER_BALANCED = 0,
    REAPER_PROCESSOR_POWER_PERFORMANCE,
    REAPER_PROCESSOR_POWER_EFFICIENCY,
    REAPER_PROCESSOR_POWER_QUIET,
    REAPER_PROCESSOR_POWER_THERMAL_GUARD
} ReaperProcessorPowerProfile;

typedef struct {
    void *context;
    uint32_t capabilities;
    ReaperProcessorStatus (*set_frequency_cap)(
        void *context, uint32_t cpu_id, uint32_t minimum_khz,
        uint32_t target_khz, uint32_t maximum_khz,
        uint32_t topology_generation
    );
    ReaperProcessorStatus (*set_power_profile)(
        void *context, uint32_t cpu_id, ReaperProcessorPowerProfile profile,
        uint32_t topology_generation
    );
    ReaperProcessorStatus (*debug_capture)(
        void *context, uint32_t cpu_id, uint32_t flags,
        uint32_t timeout_ms, uint8_t *buffer,
        size_t capacity, size_t *written
    );
    ReaperProcessorStatus (*verify_artifact)(
        void *context, const uint8_t *image, size_t image_size,
        const uint8_t digest[REAPER_PROCESSOR_DIGEST_BYTES],
        const uint8_t *signature, size_t signature_size
    );
    ReaperProcessorStatus (*stage_patch)(
        void *context, uint64_t generation,
        const uint8_t digest[REAPER_PROCESSOR_DIGEST_BYTES],
        const uint8_t *image, size_t image_size, uint64_t *ticket
    );
    ReaperProcessorStatus (*activate_patch)(
        void *context, uint64_t ticket, uint64_t generation
    );
    ReaperProcessorStatus (*rollback_patch)(
        void *context, uint64_t ticket, uint64_t known_good_generation
    );
} ReaperProcessorPlatformOps;

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

ReaperProcessorStatus reaper_processor_apply_frequency_cap(
    const ReaperProcessorPlatformOps *ops,
    uint32_t cpu_id, uint32_t minimum_khz, uint32_t target_khz,
    uint32_t maximum_khz, uint32_t topology_generation
);

ReaperProcessorStatus reaper_processor_apply_power_profile(
    const ReaperProcessorPlatformOps *ops, uint32_t cpu_id,
    ReaperProcessorPowerProfile profile, uint32_t topology_generation
);

ReaperProcessorStatus reaper_processor_debug_capture(
    const ReaperProcessorPlatformOps *ops,
    const ReaperProcessorDebugSession *session,
    uint32_t logical_cpu_count, uint8_t *buffer,
    size_t buffer_capacity, size_t *bytes_written
);

ReaperProcessorStatus reaper_processor_stage_patch(
    const ReaperProcessorPlatformOps *ops,
    const ReaperProcessorRevision *active,
    const ReaperProcessorRevision *candidate,
    const ReaperProcessorEvidence *evidence,
    const uint8_t *image, size_t image_size,
    const uint8_t *signature, size_t signature_size,
    int abi_compatible, int safe_point, int quiescent,
    int rollback_ready, ReaperProcessorPatchTicket *ticket
);

ReaperProcessorStatus reaper_processor_activate_patch(
    const ReaperProcessorPlatformOps *ops,
    const ReaperProcessorPatchTicket *ticket,
    int safe_point, int quiescent
);

ReaperProcessorStatus reaper_processor_rollback_patch(
    const ReaperProcessorPlatformOps *ops,
    const ReaperProcessorPatchTicket *ticket,
    uint64_t known_good_generation
);

const char *reaper_processor_status_name(ReaperProcessorStatus status);

#ifdef __cplusplus
}
#endif

#endif
