#ifndef REAPER_SYSTEM_FEATURES_H
#define REAPER_SYSTEM_FEATURES_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_SYSTEM_FEATURES_ABI_VERSION 1U
#define REAPER_SYSTEM_MAX_CONTRACTS 256U
#define REAPER_SYSTEM_MAX_CONTRACT_FIELDS 64U
#define REAPER_SYSTEM_MAX_CONTRACT_EDGES 1024U
#define REAPER_SYSTEM_MAX_IDENTIFIER_BYTES 96U
#define REAPER_SYSTEM_MAX_ARENA_ALIGNMENT 4096U
#define REAPER_SYSTEM_MAX_LEASE_DAYS 120U
#define REAPER_SYSTEM_DIGEST_BYTES 32U
#define REAPER_SYSTEM_MAX_RECONCILE_ITEMS 65536U
#define REAPER_SYSTEM_MAX_PHASES 16U
#define REAPER_SYSTEM_LATENCY_BUCKETS 28U
#define REAPER_SYSTEM_MAX_OVERRIDE_TOKEN_BYTES 256U

typedef enum {
    REAPER_SYSTEM_OK = 0,
    REAPER_SYSTEM_INVALID_ARGUMENT,
    REAPER_SYSTEM_LIMIT_EXCEEDED,
    REAPER_SYSTEM_INVALID_IDENTIFIER,
    REAPER_SYSTEM_DUPLICATE,
    REAPER_SYSTEM_MISSING_DEPENDENCY,
    REAPER_SYSTEM_INCOMPATIBLE_FIELD,
    REAPER_SYSTEM_DEPENDENCY_CYCLE,
    REAPER_SYSTEM_BUFFER_TOO_SMALL,
    REAPER_SYSTEM_INVALID_ORDER,
    REAPER_SYSTEM_EXPIRED,
    REAPER_SYSTEM_LEASE_WARNING,
    REAPER_SYSTEM_BUDGET_EXCEEDED,
    REAPER_SYSTEM_DENIED,
    REAPER_SYSTEM_NOT_ACTIVE,
    REAPER_SYSTEM_INVARIANT_FAILED,
    REAPER_SYSTEM_UNTESTED_ROLLBACK
} ReaperSystemStatus;

typedef struct {
    ReaperSystemStatus status;
    size_t item_index;
    char message[160];
} ReaperSystemError;

const char *reaper_system_status_name(ReaperSystemStatus status);

/* 1. Deterministic contract graph, suitable for a compiler pre-emission pass. */
typedef struct {
    const char *name;
    uint32_t type_id;
    uint32_t flags;
} ReaperContractFieldSpec;

typedef struct {
    const char *contract_id;
    uint32_t minimum_version;
    const ReaperContractFieldSpec *required_fields;
    size_t required_field_count;
} ReaperContractDependency;

typedef struct {
    const char *contract_id;
    uint32_t version;
    const ReaperContractFieldSpec *fields;
    size_t field_count;
    const ReaperContractDependency *dependencies;
    size_t dependency_count;
} ReaperContractSpec;

ReaperSystemStatus reaper_contract_graph_validate(
    const ReaperContractSpec *contracts, size_t contract_count,
    ReaperSystemError *error
);
ReaperSystemStatus reaper_contract_graph_order(
    const ReaperContractSpec *contracts, size_t contract_count,
    size_t *ordered_indices, size_t capacity, size_t *written,
    ReaperSystemError *error
);

/* 2. Caller-owned arena slots. No heap allocation occurs in this API. */
typedef struct {
    uint8_t *storage;
    size_t capacity;
    size_t offset;
    size_t high_water;
    uint64_t frame_id;
    int active;
} ReaperArenaSlot;

/* Initialize arena and ephemeral scope descriptors to {0} before first use. */
ReaperSystemStatus reaper_arena_slot_begin(
    ReaperArenaSlot *slot, void *storage, size_t capacity, uint64_t frame_id
);
void *reaper_arena_slot_alloc(
    ReaperArenaSlot *slot, size_t size, size_t alignment,
    ReaperSystemError *error
);
ReaperSystemStatus reaper_arena_slot_end(
    ReaperArenaSlot *slot, int zeroize_used_memory
);

/* 3. Cooperative budgets. Hard preemption requires a host process/scheduler;
 * checkpoints cannot interrupt a non-cooperative callback. */
typedef struct {
    uint64_t elapsed_ns;
    uint64_t current_memory_bytes;
    uint64_t peak_memory_bytes;
    uint64_t checkpoints;
    int halted;
} ReaperWorkerBudgetDump;

typedef struct {
    uint64_t cpu_limit_ns;
    uint64_t memory_limit_bytes;
    uint64_t started_ns;
    uint64_t last_checkpoint_ns;
    uint64_t peak_memory_bytes;
    uint64_t checkpoints;
    int halted;
} ReaperWorkerBudget;

ReaperSystemStatus reaper_worker_budget_begin(
    ReaperWorkerBudget *budget, uint64_t cpu_limit_ns,
    uint64_t memory_limit_bytes, uint64_t now_ns
);
ReaperSystemStatus reaper_worker_budget_checkpoint(
    ReaperWorkerBudget *budget, uint64_t now_ns,
    uint64_t current_memory_bytes, ReaperWorkerBudgetDump *dump
);
void reaper_worker_budget_dump(
    const ReaperWorkerBudget *budget, uint64_t now_ns,
    uint64_t current_memory_bytes, ReaperWorkerBudgetDump *dump
);

/* 4. Aggregate-only diff/reconcile plan. It never applies mutations. */
typedef struct {
    const char *resource_id;
    uint32_t schema_version;
    uint64_t item_count;
    uint8_t digest[REAPER_SYSTEM_DIGEST_BYTES];
} ReaperAggregateState;

typedef enum {
    REAPER_RECONCILE_NOOP = 0,
    REAPER_RECONCILE_UPSERT,
    REAPER_RECONCILE_DROP
} ReaperReconcileAction;

typedef struct {
    const char *resource_id;
    ReaperReconcileAction action;
    uint32_t before_schema_version;
    uint32_t after_schema_version;
    uint64_t before_item_count;
    uint64_t after_item_count;
} ReaperReconcilePlanItem;

typedef int (*ReaperAggregateInvariant)(
    const ReaperAggregateState *candidate, void *context
);

ReaperSystemStatus reaper_reconcile_plan_build(
    const ReaperAggregateState *before, size_t before_count,
    const ReaperAggregateState *after, size_t after_count,
    ReaperAggregateInvariant invariant, void *invariant_context,
    ReaperReconcilePlanItem *plan, size_t plan_capacity,
    size_t *written, ReaperSystemError *error
);

/* 5. Ephemeral scope. The caller supplies backing bytes; end() wipes them.
 * Initialize the scope to {0} before its first begin(). */
typedef struct {
    uint8_t *bytes;
    size_t length;
    uint64_t generation;
    int active;
} ReaperEphemeralScope;

ReaperSystemStatus reaper_ephemeral_scope_begin(
    ReaperEphemeralScope *scope, void *bytes, size_t length, uint64_t generation
);
ReaperSystemStatus reaper_ephemeral_match(
    const ReaperEphemeralScope *scope, const void *left_digest,
    const void *right_digest, size_t digest_length, int *matches
);
ReaperSystemStatus reaper_ephemeral_scope_end(ReaperEphemeralScope *scope);

/* 6. Mutation authorization gate. Emits revision metadata only; an explicit
 * host adapter must apply an authorized plan and persist its revision event. */
typedef enum {
    REAPER_MUTATION_AUTO = 0,
    REAPER_MUTATION_MANUAL
} ReaperMutationMode;

typedef struct {
    const uint8_t *opaque_bytes;
    size_t length;
    uint64_t expected_revision;
    int host_validated;
} ReaperOverrideGrant;

typedef struct {
    uint64_t previous_revision;
    uint64_t next_revision;
    ReaperMutationMode mode;
    const char *operation_id;
} ReaperRevisionEvent;

ReaperSystemStatus reaper_mutation_authorize(
    ReaperMutationMode mode, int validator_passed,
    uint64_t current_revision, uint64_t expected_revision,
    const char *operation_id, const ReaperOverrideGrant *override_grant,
    ReaperRevisionEvent *event, ReaperSystemError *error
);

/* 7. Typed lease-window value with a compile-time-checked literal helper. */
typedef struct { uint16_t days; } ReaperLeaseWindowDays;
typedef struct {
    uint32_t created_day_utc;
    uint32_t valid_until_day_utc;
} ReaperLeaseWindow;

#define REAPER_LEASE_DAYS(days_) \
    ((ReaperLeaseWindowDays){ \
        (uint16_t)((days_) + 0U * sizeof(char[((days_) >= 1U && \
        (days_) <= REAPER_SYSTEM_MAX_LEASE_DAYS) ? 1 : -1])) \
    })

ReaperSystemStatus reaper_lease_window_open(
    uint32_t created_day_utc, ReaperLeaseWindowDays duration,
    ReaperLeaseWindow *window, ReaperSystemError *error
);
ReaperSystemStatus reaper_lease_window_check(
    const ReaperLeaseWindow *window, uint32_t current_day_utc,
    uint16_t warning_days, uint16_t *days_remaining
);

/* 8. Fixed-size latency histograms. Caller-owned and thread-confined. */
typedef struct {
    uint64_t samples[REAPER_SYSTEM_LATENCY_BUCKETS];
    uint64_t sample_count;
    uint64_t total_ns;
    uint64_t max_ns;
} ReaperLatencyPhase;

typedef struct {
    ReaperLatencyPhase phases[REAPER_SYSTEM_MAX_PHASES];
    size_t phase_count;
} ReaperLatencyProfiler;

typedef struct {
    uint64_t sample_count;
    uint64_t mean_ns;
    uint64_t p95_ns;
    uint64_t p99_ns;
    uint64_t max_ns;
} ReaperLatencySummary;

void reaper_latency_profiler_init(ReaperLatencyProfiler *profiler, size_t phase_count);
ReaperSystemStatus reaper_latency_record(
    ReaperLatencyProfiler *profiler, size_t phase, uint64_t duration_ns
);
ReaperSystemStatus reaper_latency_summary(
    const ReaperLatencyProfiler *profiler, size_t phase,
    ReaperLatencySummary *summary
);

/* 9. Effect boundary for local-only modules. The compiler must aggregate
 * transitive import effects before calling this validator. */
#define REAPER_EFFECT_FILE_READ  (1U << 0)
#define REAPER_EFFECT_FILE_WRITE (1U << 1)
#define REAPER_EFFECT_CLOCK      (1U << 2)
#define REAPER_EFFECT_NETWORK    (1U << 3)
#define REAPER_EFFECT_REMOTE_IO  (1U << 4)
#define REAPER_EFFECT_PROCESS    (1U << 5)
#define REAPER_EFFECT_HARDWARE   (1U << 6)
#define REAPER_EFFECT_LOG        (1U << 7)
#define REAPER_EFFECT_FORBIDDEN_LOCAL \
    (REAPER_EFFECT_NETWORK | REAPER_EFFECT_REMOTE_IO)

ReaperSystemStatus reaper_module_effects_validate(
    int local_only, uint32_t declared_effects,
    uint32_t inferred_effects, uint32_t imported_effects,
    ReaperSystemError *error
);

/* 10. Paired, tested forward/rollback migration contract. */
typedef struct {
    const char *migration_id;
    uint32_t from_version;
    uint32_t to_version;
    const char *forward_step_id;
    const char *rollback_step_id;
    int forward_tested;
    int rollback_tested;
} ReaperRollbackPlan;

ReaperSystemStatus reaper_rollback_plan_validate(
    const ReaperRollbackPlan *plan, ReaperSystemError *error
);

#ifdef __cplusplus
}
#endif

#endif
