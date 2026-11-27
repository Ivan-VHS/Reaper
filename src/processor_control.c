#include "reaper/processor_control.h"

#include <limits.h>
#include <string.h>

static int digest_present(const uint8_t digest[REAPER_PROCESSOR_DIGEST_BYTES]) {
    uint8_t aggregate = 0U;
    for (size_t i = 0U; i < REAPER_PROCESSOR_DIGEST_BYTES; ++i)
        aggregate = (uint8_t)(aggregate | digest[i]);
    return aggregate != 0U;
}

ReaperProcessorStatus reaper_processor_topology_validate(
    const ReaperLogicalCpu *cpus, size_t cpu_count,
    const ReaperProcessorTopology *topology
) {
    if (topology == NULL || (cpu_count != 0U && cpus == NULL))
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if (topology->logical_cpu_count == 0U ||
        topology->logical_cpu_count > REAPER_PROCESSOR_MAX_LOGICAL_CPUS ||
        cpu_count != (size_t)topology->logical_cpu_count ||
        topology->generation == 0U)
        return REAPER_PROCESSOR_INVALID_TOPOLOGY;

    uint64_t seen = 0U;
    uint32_t online = 0U;
    for (size_t i = 0U; i < cpu_count; ++i) {
        const ReaperLogicalCpu *cpu = &cpus[i];
        if (cpu->logical_id >= topology->logical_cpu_count ||
            cpu->generation != topology->generation ||
            cpu->state < REAPER_CPU_OFFLINE ||
            cpu->state > REAPER_CPU_FAILED)
            return REAPER_PROCESSOR_STALE_GENERATION;
        const uint64_t bit = UINT64_C(1) << cpu->logical_id;
        if ((seen & bit) != 0U) return REAPER_PROCESSOR_DUPLICATE_CPU;
        seen |= bit;
        if (cpu->state == REAPER_CPU_ONLINE) ++online;
    }

    const uint64_t expected =
        topology->logical_cpu_count == 64U
            ? UINT64_MAX
            : ((UINT64_C(1) << topology->logical_cpu_count) - UINT64_C(1));
    if (seen != expected || online != topology->online_cpu_count)
        return REAPER_PROCESSOR_INVALID_TOPOLOGY;
    return REAPER_PROCESSOR_OK;
}

int reaper_processor_affinity_contains(uint64_t affinity_mask, uint32_t cpu_id) {
    if (cpu_id >= REAPER_PROCESSOR_MAX_LOGICAL_CPUS) return 0;
    return (affinity_mask & (UINT64_C(1) << cpu_id)) != 0U;
}

static uint64_t effective_deadline(uint64_t deadline_ns) {
    return deadline_ns == 0U ? UINT64_MAX : deadline_ns;
}

ReaperProcessorStatus reaper_processor_select_next(
    const ReaperProcessorThread *threads, size_t thread_count,
    uint32_t cpu_id, uint64_t after_thread_id, size_t *selected_index
) {
    if (selected_index == NULL || (thread_count != 0U && threads == NULL) ||
        cpu_id >= REAPER_PROCESSOR_MAX_LOGICAL_CPUS)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    *selected_index = SIZE_MAX;

    size_t selected = SIZE_MAX;
    int32_t best_priority = INT32_MIN;
    uint64_t best_deadline = UINT64_MAX;
    uint64_t best_id_after = UINT64_MAX;
    uint64_t best_id_wrap = UINT64_MAX;

    for (size_t i = 0U; i < thread_count; ++i) {
        const ReaperProcessorThread *thread = &threads[i];
        if (thread->thread_id == 0U || thread->state != REAPER_THREAD_READY ||
            !reaper_processor_affinity_contains(thread->affinity_mask, cpu_id))
            continue;

        const uint64_t deadline = effective_deadline(thread->deadline_ns);
        if (thread->priority > best_priority ||
            (thread->priority == best_priority && deadline < best_deadline)) {
            selected = SIZE_MAX;
            best_priority = thread->priority;
            best_deadline = deadline;
            best_id_after = UINT64_MAX;
            best_id_wrap = UINT64_MAX;
        }
        if (thread->priority != best_priority || deadline != best_deadline) continue;

        if (thread->thread_id > after_thread_id) {
            if (thread->thread_id < best_id_after) {
                best_id_after = thread->thread_id;
                selected = i;
            }
        } else if (thread->thread_id < best_id_wrap) {
            best_id_wrap = thread->thread_id;
        }
    }

    if (selected == SIZE_MAX && best_id_wrap != UINT64_MAX) {
        for (size_t i = 0U; i < thread_count; ++i) {
            const ReaperProcessorThread *thread = &threads[i];
            if (thread->thread_id == best_id_wrap &&
                thread->state == REAPER_THREAD_READY &&
                reaper_processor_affinity_contains(thread->affinity_mask, cpu_id)) {
                selected = i;
                break;
            }
        }
    }
    if (selected == SIZE_MAX) return REAPER_PROCESSOR_UNSUPPORTED;
    *selected_index = selected;
    return REAPER_PROCESSOR_OK;
}

int reaper_processor_thread_transition_valid(
    ReaperThreadState current, ReaperThreadState next
) {
    switch (current) {
    case REAPER_THREAD_CREATED:
        return next == REAPER_THREAD_READY;
    case REAPER_THREAD_READY:
        return next == REAPER_THREAD_RUNNING || next == REAPER_THREAD_ZOMBIE;
    case REAPER_THREAD_RUNNING:
        return next == REAPER_THREAD_READY || next == REAPER_THREAD_BLOCKED ||
               next == REAPER_THREAD_SLEEPING || next == REAPER_THREAD_ZOMBIE;
    case REAPER_THREAD_BLOCKED:
    case REAPER_THREAD_SLEEPING:
        return next == REAPER_THREAD_READY || next == REAPER_THREAD_ZOMBIE;
    case REAPER_THREAD_ZOMBIE:
    default:
        return 0;
    }
}

int reaper_processor_core_offline_allowed(
    ReaperCpuState state, uint32_t runnable_threads,
    uint32_t active_interrupts, uint32_t held_locks,
    uint32_t dma_leases, uint32_t preempt_depth
) {
    return state == REAPER_CPU_DRAINING && runnable_threads == 0U &&
           active_interrupts == 0U && held_locks == 0U &&
           dma_leases == 0U && preempt_depth == 0U;
}

ReaperProcessorStatus reaper_processor_ap_startup_validate(
    int bootstrap_ready, int local_controller_ready,
    int stack_ready, int gdt_ready, int idt_ready,
    int per_cpu_ready, int trampoline_ready
) {
    if (!bootstrap_ready || !local_controller_ready || !stack_ready ||
        !gdt_ready || !idt_ready || !per_cpu_ready || !trampoline_ready)
        return REAPER_PROCESSOR_NOT_QUIESCENT;
    return REAPER_PROCESSOR_OK;
}

ReaperProcessorStatus reaper_processor_context_frame_validate(
    uintptr_t stack_base, size_t stack_size, uintptr_t saved_stack_pointer
) {
    if (stack_base == 0U || stack_size < 128U || saved_stack_pointer == 0U)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if (stack_base > UINTPTR_MAX - stack_size)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    const uintptr_t stack_end = stack_base + stack_size;
    if ((saved_stack_pointer & (uintptr_t)0x07U) != 0U ||
        saved_stack_pointer < stack_base ||
        saved_stack_pointer > stack_end - 128U)
        return REAPER_PROCESSOR_INVALID_TOPOLOGY;
    return REAPER_PROCESSOR_OK;
}

ReaperProcessorStatus reaper_processor_live_update_validate(
    const ReaperProcessorRevision *active,
    const ReaperProcessorRevision *candidate,
    const ReaperProcessorEvidence *evidence,
    int signature_valid, int abi_compatible,
    int safe_point, int quiescent, int rollback_ready
) {
    if (active == NULL || candidate == NULL || evidence == NULL)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if (active->state != REAPER_REVISION_ACTIVE ||
        candidate->state != REAPER_REVISION_STAGED ||
        candidate->generation != active->generation + UINT64_C(1) ||
        !digest_present(active->source_digest) ||
        !digest_present(candidate->source_digest))
        return REAPER_PROCESSOR_INVALID_STATE;
    if (!abi_compatible || candidate->abi_major != active->abi_major)
        return REAPER_PROCESSOR_INCOMPATIBLE_ABI;
    if (!signature_valid || !safe_point || !quiescent || !rollback_ready)
        return REAPER_PROCESSOR_ACCESS_DENIED;
    if (evidence->tests_total == 0U ||
        evidence->tests_passed != evidence->tests_total ||
        evidence->tests_failed != 0U ||
        evidence->coverage_basis_points > 10000U ||
        !digest_present(evidence->artifact_digest))
        return REAPER_PROCESSOR_INVALID_EVIDENCE;
    if (memcmp(candidate->source_digest, evidence->artifact_digest,
               REAPER_PROCESSOR_DIGEST_BYTES) != 0)
        return REAPER_PROCESSOR_INVALID_EVIDENCE;
    return REAPER_PROCESSOR_OK;
}

ReaperProcessorStatus reaper_processor_power_request_validate(
    int request_in_range, int capability_granted, int native_adapter_ready
) {
    if (!request_in_range) return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if (!capability_granted) return REAPER_PROCESSOR_ACCESS_DENIED;
    if (!native_adapter_ready) return REAPER_PROCESSOR_UNSUPPORTED;
    return REAPER_PROCESSOR_OK;
}

ReaperProcessorStatus reaper_processor_debug_session_validate(
    const ReaperProcessorDebugSession *session,
    uint32_t logical_cpu_count
) {
    if (session == NULL || logical_cpu_count == 0U ||
        logical_cpu_count > REAPER_PROCESSOR_MAX_LOGICAL_CPUS)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if (session->cpu_id >= logical_cpu_count || session->timeout_ms == 0U ||
        session->timeout_ms > 60000U || session->capture_limit == 0U ||
        session->capture_limit > 100000U)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if ((session->trace_enabled != 0U || session->single_step_enabled != 0U) &&
        (session->capabilities & UINT32_C(1)) == 0U)
        return REAPER_PROCESSOR_ACCESS_DENIED;
    return REAPER_PROCESSOR_OK;
}

ReaperProcessorStatus reaper_processor_apply_frequency_cap(
    const ReaperProcessorPlatformOps *ops,
    uint32_t cpu_id, uint32_t minimum_khz, uint32_t target_khz,
    uint32_t maximum_khz, uint32_t topology_generation
) {
    if (ops == NULL || cpu_id >= REAPER_PROCESSOR_MAX_LOGICAL_CPUS ||
        topology_generation == 0U || minimum_khz == 0U ||
        minimum_khz > target_khz || target_khz > maximum_khz)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if ((ops->capabilities & REAPER_PROCESSOR_CAP_POWER_CONTROL) == 0U ||
        ops->set_frequency_cap == NULL)
        return REAPER_PROCESSOR_ACCESS_DENIED;
    return ops->set_frequency_cap(ops->context, cpu_id, minimum_khz,
                                  target_khz, maximum_khz,
                                  topology_generation);
}

ReaperProcessorStatus reaper_processor_debug_capture(
    const ReaperProcessorPlatformOps *ops,
    const ReaperProcessorDebugSession *session,
    uint32_t logical_cpu_count, uint8_t *buffer,
    size_t buffer_capacity, size_t *bytes_written
) {
    if (bytes_written == NULL || buffer == NULL || buffer_capacity == 0U)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    *bytes_written = 0U;
    ReaperProcessorStatus status =
        reaper_processor_debug_session_validate(session, logical_cpu_count);
    if (status != REAPER_PROCESSOR_OK) return status;
    if (buffer_capacity > REAPER_PROCESSOR_MAX_DEBUG_BYTES ||
        session->capture_limit > buffer_capacity)
        return REAPER_PROCESSOR_OUTPUT_TOO_LARGE;
    if (ops == NULL ||
        (ops->capabilities & REAPER_PROCESSOR_CAP_DEBUG_CAPTURE) == 0U ||
        ops->debug_capture == NULL)
        return REAPER_PROCESSOR_ACCESS_DENIED;

    uint32_t flags = 0U;
    if (session->trace_enabled != 0U) flags |= UINT32_C(1);
    if (session->single_step_enabled != 0U) flags |= UINT32_C(2);
    size_t produced = 0U;
    status = ops->debug_capture(
        ops->context, session->cpu_id, flags, session->timeout_ms,
        buffer, session->capture_limit, &produced
    );
    if (status != REAPER_PROCESSOR_OK) return status;
    if (produced > session->capture_limit || produced > buffer_capacity)
        return REAPER_PROCESSOR_ADAPTER_FAILURE;
    *bytes_written = produced;
    return REAPER_PROCESSOR_OK;
}

ReaperProcessorStatus reaper_processor_stage_patch(
    const ReaperProcessorPlatformOps *ops,
    const ReaperProcessorRevision *active,
    const ReaperProcessorRevision *candidate,
    const ReaperProcessorEvidence *evidence,
    const uint8_t *image, size_t image_size,
    const uint8_t *signature, size_t signature_size,
    int abi_compatible, int safe_point, int quiescent,
    int rollback_ready, ReaperProcessorPatchTicket *ticket
) {
    if (ticket == NULL || image == NULL || image_size == 0U ||
        image_size > REAPER_PROCESSOR_MAX_PATCH_BYTES ||
        signature == NULL || signature_size == 0U ||
        signature_size > 4096U || candidate == NULL)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    ticket->token = 0U;
    ticket->generation = 0U;
    ticket->abi_major = 0U;
    memset(ticket->digest, 0, sizeof(ticket->digest));

    ReaperProcessorStatus status = reaper_processor_live_update_validate(
        active, candidate, evidence, 0, abi_compatible,
        safe_point, quiescent, rollback_ready
    );
    if (status != REAPER_PROCESSOR_ACCESS_DENIED) return status;

    if (ops == NULL ||
        (ops->capabilities & REAPER_PROCESSOR_CAP_PATCH_STAGE) == 0U ||
        ops->verify_artifact == NULL || ops->stage_patch == NULL)
        return REAPER_PROCESSOR_ACCESS_DENIED;

    status = ops->verify_artifact(
        ops->context, candidate->source_digest, signature, signature_size
    );
    if (status != REAPER_PROCESSOR_OK) return status;

    uint64_t adapter_ticket = 0U;
    status = ops->stage_patch(
        ops->context, candidate->generation, candidate->source_digest,
        image, image_size, &adapter_ticket
    );
    if (status != REAPER_PROCESSOR_OK) return status;
    if (adapter_ticket == 0U) return REAPER_PROCESSOR_ADAPTER_FAILURE;

    ticket->token = adapter_ticket;
    ticket->generation = candidate->generation;
    ticket->abi_major = candidate->abi_major;
    memcpy(ticket->digest, candidate->source_digest, sizeof(ticket->digest));
    return REAPER_PROCESSOR_OK;
}

ReaperProcessorStatus reaper_processor_activate_patch(
    const ReaperProcessorPlatformOps *ops,
    const ReaperProcessorPatchTicket *ticket,
    int safe_point, int quiescent
) {
    if (ticket == NULL || ticket->token == 0U || ticket->generation == 0U)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if (!safe_point || !quiescent) return REAPER_PROCESSOR_NOT_QUIESCENT;
    if (ops == NULL ||
        (ops->capabilities & REAPER_PROCESSOR_CAP_PATCH_ACTIVATE) == 0U ||
        ops->activate_patch == NULL)
        return REAPER_PROCESSOR_ACCESS_DENIED;
    return ops->activate_patch(ops->context, ticket->token,
                               ticket->generation);
}

ReaperProcessorStatus reaper_processor_rollback_patch(
    const ReaperProcessorPlatformOps *ops,
    const ReaperProcessorPatchTicket *ticket,
    uint64_t known_good_generation
) {
    if (ticket == NULL || ticket->token == 0U ||
        ticket->generation == 0U || known_good_generation == 0U ||
        known_good_generation >= ticket->generation)
        return REAPER_PROCESSOR_INVALID_ARGUMENT;
    if (ops == NULL ||
        (ops->capabilities & REAPER_PROCESSOR_CAP_PATCH_ROLLBACK) == 0U ||
        ops->rollback_patch == NULL)
        return REAPER_PROCESSOR_ACCESS_DENIED;
    return ops->rollback_patch(ops->context, ticket->token,
                               known_good_generation);
}

const char *reaper_processor_status_name(ReaperProcessorStatus status) {
    switch (status) {
    case REAPER_PROCESSOR_OK: return "ok";
    case REAPER_PROCESSOR_INVALID_ARGUMENT: return "invalid-argument";
    case REAPER_PROCESSOR_INVALID_TOPOLOGY: return "invalid-topology";
    case REAPER_PROCESSOR_DUPLICATE_CPU: return "duplicate-cpu";
    case REAPER_PROCESSOR_STALE_GENERATION: return "stale-generation";
    case REAPER_PROCESSOR_INVALID_STATE: return "invalid-state";
    case REAPER_PROCESSOR_NOT_QUIESCENT: return "not-quiescent";
    case REAPER_PROCESSOR_ACCESS_DENIED: return "access-denied";
    case REAPER_PROCESSOR_INCOMPATIBLE_ABI: return "incompatible-abi";
    case REAPER_PROCESSOR_INVALID_EVIDENCE: return "invalid-evidence";
    case REAPER_PROCESSOR_UNSUPPORTED: return "unsupported";
    case REAPER_PROCESSOR_ADAPTER_FAILURE: return "adapter-failure";
    case REAPER_PROCESSOR_OUTPUT_TOO_LARGE: return "output-too-large";
    }
    return "unknown";
}
