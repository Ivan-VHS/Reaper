#include "reaper/system_features.h"

#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static ReaperSystemStatus fail(
    ReaperSystemError *error, ReaperSystemStatus status,
    size_t item_index, const char *message
) {
    if (error != NULL) {
        error->status = status;
        error->item_index = item_index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}

static int valid_identifier(const char *value) {
    size_t length = 0U;
    if (value == NULL || value[0] == '\0') return 0;
    while (value[length] != '\0') {
        const unsigned char ch = (unsigned char)value[length];
        const int alpha = (ch >= (unsigned char)'A' && ch <= (unsigned char)'Z') ||
                          (ch >= (unsigned char)'a' && ch <= (unsigned char)'z');
        const int digit = ch >= (unsigned char)'0' && ch <= (unsigned char)'9';
        if ((!alpha && !digit && ch != (unsigned char)'_' &&
             ch != (unsigned char)'.' && ch != (unsigned char)'-') ||
            length >= REAPER_SYSTEM_MAX_IDENTIFIER_BYTES) return 0;
        ++length;
    }
    return length != 0U;
}

static int bytes_equal_constant_time(const void *left, const void *right, size_t length) {
    if (length == 0U) return 1;
    if (left == NULL || right == NULL) return 0;
    const uint8_t *a = (const uint8_t *)left;
    const uint8_t *b = (const uint8_t *)right;
    volatile uint8_t difference = 0U;
    for (size_t i = 0U; i < length; ++i)
        difference = (uint8_t)(difference | (uint8_t)(a[i] ^ b[i]));
    return difference == 0U;
}

const char *reaper_system_status_name(ReaperSystemStatus status) {
    switch (status) {
    case REAPER_SYSTEM_OK: return "ok";
    case REAPER_SYSTEM_INVALID_ARGUMENT: return "invalid-argument";
    case REAPER_SYSTEM_LIMIT_EXCEEDED: return "limit-exceeded";
    case REAPER_SYSTEM_INVALID_IDENTIFIER: return "invalid-identifier";
    case REAPER_SYSTEM_DUPLICATE: return "duplicate";
    case REAPER_SYSTEM_MISSING_DEPENDENCY: return "missing-dependency";
    case REAPER_SYSTEM_INCOMPATIBLE_FIELD: return "incompatible-field";
    case REAPER_SYSTEM_DEPENDENCY_CYCLE: return "dependency-cycle";
    case REAPER_SYSTEM_BUFFER_TOO_SMALL: return "buffer-too-small";
    case REAPER_SYSTEM_INVALID_ORDER: return "invalid-order";
    case REAPER_SYSTEM_EXPIRED: return "expired";
    case REAPER_SYSTEM_LEASE_WARNING: return "lease-warning";
    case REAPER_SYSTEM_BUDGET_EXCEEDED: return "budget-exceeded";
    case REAPER_SYSTEM_DENIED: return "denied";
    case REAPER_SYSTEM_NOT_ACTIVE: return "not-active";
    case REAPER_SYSTEM_INVARIANT_FAILED: return "invariant-failed";
    case REAPER_SYSTEM_UNTESTED_ROLLBACK: return "untested-rollback";
    }
    return "unknown";
}

/* 1. Contract graph */
static size_t contract_find(const ReaperContractSpec *contracts,
                            size_t count, const char *contract_id) {
    for (size_t i = 0U; i < count; ++i)
        if (strcmp(contracts[i].contract_id, contract_id) == 0) return i;
    return count;
}

static const ReaperContractFieldSpec *field_find(
    const ReaperContractSpec *contract, const char *name
) {
    for (size_t i = 0U; i < contract->field_count; ++i)
        if (strcmp(contract->fields[i].name, name) == 0) return &contract->fields[i];
    return NULL;
}

ReaperSystemStatus reaper_contract_graph_validate(
    const ReaperContractSpec *contracts, size_t contract_count,
    ReaperSystemError *error
) {
    if (error != NULL) { error->status = REAPER_SYSTEM_OK; error->item_index = 0U; error->message[0] = '\0'; }
    if (contract_count != 0U && contracts == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "contract storage is required");
    if (contract_count > REAPER_SYSTEM_MAX_CONTRACTS)
        return fail(error, REAPER_SYSTEM_LIMIT_EXCEEDED, 0U, "contract graph exceeds 256 nodes");

    size_t edge_count = 0U;
    for (size_t i = 0U; i < contract_count; ++i) {
        const ReaperContractSpec *contract = &contracts[i];
        if (!valid_identifier(contract->contract_id) || contract->version == 0U)
            return fail(error, REAPER_SYSTEM_INVALID_IDENTIFIER, i, "contract ID and positive version are required");
        if (contract->field_count > REAPER_SYSTEM_MAX_CONTRACT_FIELDS ||
            contract->dependency_count > REAPER_SYSTEM_MAX_CONTRACT_EDGES)
            return fail(error, REAPER_SYSTEM_LIMIT_EXCEEDED, i, "contract field or dependency limit exceeded");
        if ((contract->field_count != 0U && contract->fields == NULL) ||
            (contract->dependency_count != 0U && contract->dependencies == NULL))
            return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, i, "contract field and dependency storage is required");
        if (contract->dependency_count > REAPER_SYSTEM_MAX_CONTRACT_EDGES - edge_count)
            return fail(error, REAPER_SYSTEM_LIMIT_EXCEEDED, i, "contract graph exceeds 1024 edges");
        edge_count += contract->dependency_count;

        for (size_t j = 0U; j < i; ++j)
            if (strcmp(contracts[j].contract_id, contract->contract_id) == 0)
                return fail(error, REAPER_SYSTEM_DUPLICATE, i, "duplicate contract ID");

        for (size_t f = 0U; f < contract->field_count; ++f) {
            if (!valid_identifier(contract->fields[f].name) || contract->fields[f].type_id == 0U)
                return fail(error, REAPER_SYSTEM_INVALID_IDENTIFIER, i, "field name and type ID are required");
            for (size_t prior = 0U; prior < f; ++prior)
                if (strcmp(contract->fields[prior].name, contract->fields[f].name) == 0)
                    return fail(error, REAPER_SYSTEM_DUPLICATE, i, "duplicate contract field");
        }
    }

    for (size_t i = 0U; i < contract_count; ++i) {
        const ReaperContractSpec *contract = &contracts[i];
        for (size_t d = 0U; d < contract->dependency_count; ++d) {
            const ReaperContractDependency *dependency = &contract->dependencies[d];
            if (!valid_identifier(dependency->contract_id))
                return fail(error, REAPER_SYSTEM_INVALID_IDENTIFIER, i, "dependency ID is invalid");
            if (dependency->required_field_count > REAPER_SYSTEM_MAX_CONTRACT_FIELDS ||
                (dependency->required_field_count != 0U && dependency->required_fields == NULL))
                return fail(error, REAPER_SYSTEM_LIMIT_EXCEEDED, i, "dependency field contract is invalid");
            for (size_t prior = 0U; prior < d; ++prior)
                if (strcmp(contract->dependencies[prior].contract_id, dependency->contract_id) == 0)
                    return fail(error, REAPER_SYSTEM_DUPLICATE, i, "duplicate contract dependency");

            const size_t target_index = contract_find(contracts, contract_count, dependency->contract_id);
            if (target_index == contract_count)
                return fail(error, REAPER_SYSTEM_MISSING_DEPENDENCY, i, "contract dependency does not exist");
            const ReaperContractSpec *target = &contracts[target_index];
            if (target->version < dependency->minimum_version)
                return fail(error, REAPER_SYSTEM_INCOMPATIBLE_FIELD, i, "dependency contract version is too old");
            for (size_t f = 0U; f < dependency->required_field_count; ++f) {
                const ReaperContractFieldSpec *required = &dependency->required_fields[f];
                if (!valid_identifier(required->name) || required->type_id == 0U)
                    return fail(error, REAPER_SYSTEM_INVALID_IDENTIFIER, i, "required dependency field is invalid");
                const ReaperContractFieldSpec *actual = field_find(target, required->name);
                if (actual == NULL || actual->type_id != required->type_id ||
                    actual->flags != required->flags)
                    return fail(error, REAPER_SYSTEM_INCOMPATIBLE_FIELD, i, "dependency field contract is incompatible");
            }
        }
    }

    uint8_t emitted[REAPER_SYSTEM_MAX_CONTRACTS] = {0U};
    for (size_t step = 0U; step < contract_count; ++step) {
        size_t selected = contract_count;
        for (size_t i = 0U; i < contract_count; ++i) {
            if (emitted[i] != 0U) continue;
            int ready = 1;
            for (size_t d = 0U; d < contracts[i].dependency_count; ++d) {
                const size_t dependency_index = contract_find(
                    contracts, contract_count, contracts[i].dependencies[d].contract_id);
                if (dependency_index == contract_count || emitted[dependency_index] == 0U) {
                    ready = 0; break;
                }
            }
            if (ready && (selected == contract_count ||
                strcmp(contracts[i].contract_id, contracts[selected].contract_id) < 0))
                selected = i;
        }
        if (selected == contract_count)
            return fail(error, REAPER_SYSTEM_DEPENDENCY_CYCLE, step, "contract dependency cycle detected");
        emitted[selected] = 1U;
    }
    if (error != NULL) {
        error->status = REAPER_SYSTEM_OK; error->item_index = 0U;
        (void)snprintf(error->message, sizeof error->message, "%s", "ok");
    }
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_contract_graph_order(
    const ReaperContractSpec *contracts, size_t contract_count,
    size_t *ordered_indices, size_t capacity, size_t *written,
    ReaperSystemError *error
) {
    if (written == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "written output is required");
    *written = 0U;
    ReaperSystemStatus status = reaper_contract_graph_validate(contracts, contract_count, error);
    if (status != REAPER_SYSTEM_OK) return status;
    if (capacity < contract_count || (contract_count != 0U && ordered_indices == NULL))
        return fail(error, REAPER_SYSTEM_BUFFER_TOO_SMALL, 0U, "contract order output is too small");

    uint8_t emitted[REAPER_SYSTEM_MAX_CONTRACTS] = {0U};
    for (size_t step = 0U; step < contract_count; ++step) {
        size_t selected = contract_count;
        for (size_t i = 0U; i < contract_count; ++i) {
            if (emitted[i] != 0U) continue;
            int ready = 1;
            for (size_t d = 0U; d < contracts[i].dependency_count; ++d) {
                const size_t dependency_index = contract_find(
                    contracts, contract_count, contracts[i].dependencies[d].contract_id);
                if (dependency_index == contract_count || emitted[dependency_index] == 0U) {
                    ready = 0; break;
                }
            }
            if (ready && (selected == contract_count ||
                strcmp(contracts[i].contract_id, contracts[selected].contract_id) < 0))
                selected = i;
        }
        if (selected == contract_count)
            return fail(error, REAPER_SYSTEM_DEPENDENCY_CYCLE, step, "contract dependency cycle detected");
        ordered_indices[step] = selected;
        emitted[selected] = 1U;
    }
    *written = contract_count;
    return REAPER_SYSTEM_OK;
}

/* 2. Arena slots */
static int power_of_two(size_t value) {
    return value != 0U && (value & (value - 1U)) == 0U;
}

ReaperSystemStatus reaper_arena_slot_begin(
    ReaperArenaSlot *slot, void *storage, size_t capacity, uint64_t frame_id
) {
    if (slot == NULL || storage == NULL || capacity == 0U || frame_id == 0U)
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    if (slot->active != 0) return REAPER_SYSTEM_DENIED;
    slot->storage = (uint8_t *)storage;
    slot->capacity = capacity;
    slot->offset = 0U;
    slot->high_water = 0U;
    slot->frame_id = frame_id;
    slot->active = 1;
    return REAPER_SYSTEM_OK;
}

void *reaper_arena_slot_alloc(
    ReaperArenaSlot *slot, size_t size, size_t alignment, ReaperSystemError *error
) {
    if (error != NULL) { error->status = REAPER_SYSTEM_OK; error->item_index = 0U; error->message[0] = '\0'; }
    if (slot == NULL || slot->active == 0 || slot->storage == NULL) {
        (void)fail(error, REAPER_SYSTEM_NOT_ACTIVE, 0U, "arena frame is not active"); return NULL;
    }
    if (size == 0U || !power_of_two(alignment) || alignment > REAPER_SYSTEM_MAX_ARENA_ALIGNMENT) {
        (void)fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "allocation size or alignment is invalid"); return NULL;
    }
    const uintptr_t base = (uintptr_t)slot->storage;
    if (slot->offset > slot->capacity || base > UINTPTR_MAX - slot->offset) {
        (void)fail(error, REAPER_SYSTEM_LIMIT_EXCEEDED, 0U, "arena address overflow"); return NULL;
    }
    const uintptr_t current = base + slot->offset;
    const uintptr_t mask = (uintptr_t)(alignment - 1U);
    if (current > UINTPTR_MAX - mask) {
        (void)fail(error, REAPER_SYSTEM_LIMIT_EXCEEDED, 0U, "arena alignment overflow"); return NULL;
    }
    const uintptr_t aligned = (current + mask) & ~mask;
    const uintptr_t padding = aligned - current;
    if (padding > SIZE_MAX || (size_t)padding > slot->capacity - slot->offset ||
        size > slot->capacity - slot->offset - (size_t)padding) {
        (void)fail(error, REAPER_SYSTEM_LIMIT_EXCEEDED, 0U, "arena frame capacity exceeded"); return NULL;
    }
    const size_t start = slot->offset + (size_t)padding;
    slot->offset = start + size;
    if (slot->offset > slot->high_water) slot->high_water = slot->offset;
    return slot->storage + start;
}

ReaperSystemStatus reaper_arena_slot_end(ReaperArenaSlot *slot, int zeroize_used_memory) {
    if (slot == NULL || slot->active == 0 || slot->storage == NULL)
        return REAPER_SYSTEM_NOT_ACTIVE;
    if (zeroize_used_memory != 0) {
        volatile uint8_t *bytes = (volatile uint8_t *)slot->storage;
        for (size_t i = 0U; i < slot->offset; ++i) bytes[i] = 0U;
    }
    slot->offset = 0U;
    slot->active = 0;
    slot->storage = NULL;
    slot->capacity = 0U;
    return REAPER_SYSTEM_OK;
}

/* 3. Cooperative worker budgets */
void reaper_worker_budget_dump(
    const ReaperWorkerBudget *budget, uint64_t now_ns,
    uint64_t current_memory_bytes, ReaperWorkerBudgetDump *dump
) {
    if (budget == NULL || dump == NULL) return;
    dump->elapsed_ns = now_ns >= budget->started_ns ? now_ns - budget->started_ns : 0U;
    dump->current_memory_bytes = current_memory_bytes;
    dump->peak_memory_bytes = budget->peak_memory_bytes > current_memory_bytes ?
                              budget->peak_memory_bytes : current_memory_bytes;
    dump->checkpoints = budget->checkpoints;
    dump->halted = budget->halted;
}

ReaperSystemStatus reaper_worker_budget_begin(
    ReaperWorkerBudget *budget, uint64_t cpu_limit_ns,
    uint64_t memory_limit_bytes, uint64_t now_ns
) {
    if (budget == NULL || cpu_limit_ns == 0U || memory_limit_bytes == 0U)
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    budget->cpu_limit_ns = cpu_limit_ns;
    budget->memory_limit_bytes = memory_limit_bytes;
    budget->started_ns = now_ns;
    budget->last_checkpoint_ns = now_ns;
    budget->peak_memory_bytes = 0U;
    budget->checkpoints = 0U;
    budget->halted = 0;
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_worker_budget_checkpoint(
    ReaperWorkerBudget *budget, uint64_t now_ns,
    uint64_t current_memory_bytes, ReaperWorkerBudgetDump *dump
) {
    if (budget == NULL) return REAPER_SYSTEM_INVALID_ARGUMENT;
    if (budget->halted != 0) {
        if (dump != NULL) reaper_worker_budget_dump(budget, now_ns, current_memory_bytes, dump);
        return REAPER_SYSTEM_BUDGET_EXCEEDED;
    }
    if (now_ns < budget->last_checkpoint_ns || now_ns < budget->started_ns)
        return REAPER_SYSTEM_INVALID_ORDER;
    if (current_memory_bytes > budget->peak_memory_bytes)
        budget->peak_memory_bytes = current_memory_bytes;
    if (budget->checkpoints != UINT64_MAX) ++budget->checkpoints;
    budget->last_checkpoint_ns = now_ns;
    if (now_ns - budget->started_ns > budget->cpu_limit_ns ||
        current_memory_bytes > budget->memory_limit_bytes) {
        budget->halted = 1;
        if (dump != NULL) reaper_worker_budget_dump(budget, now_ns, current_memory_bytes, dump);
        return REAPER_SYSTEM_BUDGET_EXCEEDED;
    }
    if (dump != NULL) reaper_worker_budget_dump(budget, now_ns, current_memory_bytes, dump);
    return REAPER_SYSTEM_OK;
}

/* 4. Aggregate reconciliation */
static int valid_sorted_aggregates(const ReaperAggregateState *items, size_t count) {
    if (count > REAPER_SYSTEM_MAX_RECONCILE_ITEMS || (count != 0U && items == NULL)) return 0;
    for (size_t i = 0U; i < count; ++i) {
        if (!valid_identifier(items[i].resource_id) || items[i].schema_version == 0U) return 0;
        if (i != 0U && strcmp(items[i - 1U].resource_id, items[i].resource_id) >= 0) return 0;
    }
    return 1;
}

static int aggregate_equal(const ReaperAggregateState *left, const ReaperAggregateState *right) {
    return left->schema_version == right->schema_version &&
           left->item_count == right->item_count &&
           bytes_equal_constant_time(left->digest, right->digest, REAPER_SYSTEM_DIGEST_BYTES);
}

static size_t aggregate_union_count(
    const ReaperAggregateState *before, size_t before_count,
    const ReaperAggregateState *after, size_t after_count
) {
    size_t left = 0U, right = 0U, count = 0U;
    while (left < before_count || right < after_count) {
        if (left == before_count) ++right;
        else if (right == after_count) ++left;
        else {
            const int order = strcmp(before[left].resource_id, after[right].resource_id);
            if (order < 0) ++left;
            else if (order > 0) ++right;
            else { ++left; ++right; }
        }
        ++count;
    }
    return count;
}

ReaperSystemStatus reaper_reconcile_plan_build(
    const ReaperAggregateState *before, size_t before_count,
    const ReaperAggregateState *after, size_t after_count,
    ReaperAggregateInvariant invariant, void *invariant_context,
    ReaperReconcilePlanItem *plan, size_t plan_capacity, size_t *written,
    ReaperSystemError *error
) {
    if (written == NULL) return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "written output is required");
    *written = 0U;
    if (!valid_sorted_aggregates(before, before_count) ||
        !valid_sorted_aggregates(after, after_count))
        return fail(error, REAPER_SYSTEM_INVALID_ORDER, 0U, "aggregate snapshots must be valid and strictly sorted");
    if (invariant != NULL) {
        for (size_t i = 0U; i < after_count; ++i)
            if (!invariant(&after[i], invariant_context))
                return fail(error, REAPER_SYSTEM_INVARIANT_FAILED, i, "candidate aggregate violates an invariant");
    }
    const size_t required = aggregate_union_count(before, before_count, after, after_count);
    if (required > plan_capacity || (required != 0U && plan == NULL))
        return fail(error, REAPER_SYSTEM_BUFFER_TOO_SMALL, 0U, "reconcile plan capacity is insufficient");

    size_t left = 0U, right = 0U, output = 0U;
    while (left < before_count || right < after_count) {
        if (left == before_count) {
            const ReaperAggregateState *item = &after[right++];
            plan[output++] = (ReaperReconcilePlanItem){
                item->resource_id, REAPER_RECONCILE_UPSERT, 0U,
                item->schema_version, 0U, item->item_count
            };
        } else if (right == after_count) {
            const ReaperAggregateState *item = &before[left++];
            plan[output++] = (ReaperReconcilePlanItem){
                item->resource_id, REAPER_RECONCILE_DROP, item->schema_version,
                0U, item->item_count, 0U
            };
        } else {
            const ReaperAggregateState *old_item = &before[left];
            const ReaperAggregateState *new_item = &after[right];
            const int order = strcmp(old_item->resource_id, new_item->resource_id);
            if (order < 0) {
                ++left;
                plan[output++] = (ReaperReconcilePlanItem){
                    old_item->resource_id, REAPER_RECONCILE_DROP,
                    old_item->schema_version, 0U, old_item->item_count, 0U
                };
            } else if (order > 0) {
                ++right;
                plan[output++] = (ReaperReconcilePlanItem){
                    new_item->resource_id, REAPER_RECONCILE_UPSERT,
                    0U, new_item->schema_version, 0U, new_item->item_count
                };
            } else {
                ++left; ++right;
                const int same = aggregate_equal(old_item, new_item);
                plan[output++] = (ReaperReconcilePlanItem){
                    old_item->resource_id,
                    same ? REAPER_RECONCILE_NOOP : REAPER_RECONCILE_UPSERT,
                    old_item->schema_version, new_item->schema_version,
                    old_item->item_count, new_item->item_count
                };
            }
        }
    }
    *written = output;
    return REAPER_SYSTEM_OK;
}

/* 5. Ephemeral scope */
ReaperSystemStatus reaper_ephemeral_scope_begin(
    ReaperEphemeralScope *scope, void *bytes, size_t length, uint64_t generation
) {
    if (scope == NULL || bytes == NULL || length == 0U || generation == 0U)
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    if (scope->active != 0) return REAPER_SYSTEM_DENIED;
    scope->bytes = (uint8_t *)bytes;
    scope->length = length;
    scope->generation = generation;
    scope->active = 1;
    return REAPER_SYSTEM_OK;
}

static int ephemeral_contains(
    const ReaperEphemeralScope *scope, const void *value, size_t length
) {
    if (scope == NULL || scope->bytes == NULL || value == NULL) return 0;
    const uintptr_t begin = (uintptr_t)scope->bytes;
    const uintptr_t address = (uintptr_t)value;
    if (begin > UINTPTR_MAX - scope->length || address < begin) return 0;
    const uintptr_t end = begin + scope->length;
    if (address > end || length > (size_t)(end - address)) return 0;
    return 1;
}

ReaperSystemStatus reaper_ephemeral_match(
    const ReaperEphemeralScope *scope, const void *left_digest,
    const void *right_digest, size_t digest_length, int *matches
) {
    if (scope == NULL || matches == NULL || left_digest == NULL ||
        right_digest == NULL || digest_length != REAPER_SYSTEM_DIGEST_BYTES)
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    if (scope->active == 0 || scope->bytes == NULL)
        return REAPER_SYSTEM_NOT_ACTIVE;
    if (!ephemeral_contains(scope, left_digest, digest_length) ||
        !ephemeral_contains(scope, right_digest, digest_length))
        return REAPER_SYSTEM_DENIED;
    *matches = bytes_equal_constant_time(left_digest, right_digest, digest_length);
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_ephemeral_scope_end(ReaperEphemeralScope *scope) {
    if (scope == NULL || scope->active == 0 || scope->bytes == NULL)
        return REAPER_SYSTEM_NOT_ACTIVE;
    volatile uint8_t *bytes = (volatile uint8_t *)scope->bytes;
    for (size_t i = 0U; i < scope->length; ++i) bytes[i] = 0U;
    scope->bytes = NULL;
    scope->length = 0U;
    scope->generation = 0U;
    scope->active = 0;
    return REAPER_SYSTEM_OK;
}

/* 6. Mutation gate */
ReaperSystemStatus reaper_mutation_authorize(
    ReaperMutationMode mode, int validator_passed,
    uint64_t current_revision, uint64_t expected_revision,
    const char *operation_id, const ReaperOverrideGrant *override_grant,
    ReaperRevisionEvent *event, ReaperSystemError *error
) {
    if (event == NULL || !valid_identifier(operation_id))
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "revision event and operation ID are required");
    if (expected_revision != current_revision || current_revision == UINT64_MAX)
        return fail(error, REAPER_SYSTEM_INVALID_ORDER, 0U, "revision changed or revision counter is exhausted");
    if (mode == REAPER_MUTATION_AUTO) {
        if (!validator_passed)
            return fail(error, REAPER_SYSTEM_DENIED, 0U, "automatic mutation requires a passing validator");
    } else if (mode == REAPER_MUTATION_MANUAL) {
        if (override_grant == NULL || override_grant->opaque_bytes == NULL ||
            override_grant->length == 0U ||
            override_grant->length > REAPER_SYSTEM_MAX_OVERRIDE_TOKEN_BYTES ||
            override_grant->host_validated == 0 ||
            override_grant->expected_revision != current_revision)
            return fail(error, REAPER_SYSTEM_DENIED, 0U, "manual override requires a host-validated revision-bound grant");
    } else {
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "unknown mutation mode");
    }
    event->previous_revision = current_revision;
    event->next_revision = current_revision + 1U;
    event->mode = mode;
    event->operation_id = operation_id;
    return REAPER_SYSTEM_OK;
}

/* 7. Lease windows */
ReaperSystemStatus reaper_lease_window_open(
    uint32_t created_day_utc, ReaperLeaseWindowDays duration,
    ReaperLeaseWindow *window, ReaperSystemError *error
) {
    if (window == NULL || duration.days == 0U ||
        duration.days > REAPER_SYSTEM_MAX_LEASE_DAYS)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "lease duration must be 1..120 days");
    if (created_day_utc > UINT32_MAX - duration.days)
        return fail(error, REAPER_SYSTEM_LIMIT_EXCEEDED, 0U, "lease end day overflows UTC day counter");
    window->created_day_utc = created_day_utc;
    window->valid_until_day_utc = created_day_utc + duration.days;
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_lease_window_check(
    const ReaperLeaseWindow *window, uint32_t current_day_utc,
    uint16_t warning_days, uint16_t *days_remaining
) {
    if (window == NULL || window->valid_until_day_utc <= window->created_day_utc)
        return REAPER_SYSTEM_INVALID_ARGUMENT;
    if (current_day_utc < window->created_day_utc) return REAPER_SYSTEM_INVALID_ORDER;
    if (current_day_utc >= window->valid_until_day_utc) {
        if (days_remaining != NULL) *days_remaining = 0U;
        return REAPER_SYSTEM_EXPIRED;
    }
    const uint32_t remaining = window->valid_until_day_utc - current_day_utc;
    if (days_remaining != NULL) *days_remaining = (uint16_t)remaining;
    return remaining <= warning_days ? REAPER_SYSTEM_LEASE_WARNING : REAPER_SYSTEM_OK;
}

/* 8. Latency profiling */
static const uint64_t latency_upper_bounds[REAPER_SYSTEM_LATENCY_BUCKETS - 1U] = {
    1000ULL, 2000ULL, 4000ULL, 8000ULL, 16000ULL, 32000ULL, 64000ULL,
    128000ULL, 256000ULL, 512000ULL, 1000000ULL, 2000000ULL,
    4000000ULL, 8000000ULL, 16000000ULL, 32000000ULL, 64000000ULL,
    128000000ULL, 256000000ULL, 512000000ULL, 1000000000ULL,
    2000000000ULL, 4000000000ULL, 8000000000ULL, 16000000000ULL,
    32000000000ULL, 64000000000ULL
};

void reaper_latency_profiler_init(ReaperLatencyProfiler *profiler, size_t phase_count) {
    if (profiler == NULL) return;
    memset(profiler, 0, sizeof *profiler);
    profiler->phase_count = phase_count <= REAPER_SYSTEM_MAX_PHASES ?
                            phase_count : REAPER_SYSTEM_MAX_PHASES;
}

ReaperSystemStatus reaper_latency_record(
    ReaperLatencyProfiler *profiler, size_t phase, uint64_t duration_ns
) {
    if (profiler == NULL || profiler->phase_count > REAPER_SYSTEM_MAX_PHASES ||
        phase >= profiler->phase_count) return REAPER_SYSTEM_INVALID_ARGUMENT;
    ReaperLatencyPhase *target = &profiler->phases[phase];
    if (target->sample_count == UINT64_MAX ||
        UINT64_MAX - target->total_ns < duration_ns)
        return REAPER_SYSTEM_LIMIT_EXCEEDED;
    size_t bucket = REAPER_SYSTEM_LATENCY_BUCKETS - 1U;
    for (size_t i = 0U; i < REAPER_SYSTEM_LATENCY_BUCKETS - 1U; ++i) {
        if (duration_ns <= latency_upper_bounds[i]) { bucket = i; break; }
    }
    if (target->samples[bucket] == UINT64_MAX) return REAPER_SYSTEM_LIMIT_EXCEEDED;
    ++target->samples[bucket];
    ++target->sample_count;
    target->total_ns += duration_ns;
    if (duration_ns > target->max_ns) target->max_ns = duration_ns;
    return REAPER_SYSTEM_OK;
}

static uint64_t latency_quantile(const ReaperLatencyPhase *phase, uint64_t numerator) {
    if (phase->sample_count == 0U) return 0U;
    const uint64_t quotient = phase->sample_count / 100U;
    const uint64_t remainder = phase->sample_count % 100U;
    const uint64_t rank = quotient * numerator + (remainder * numerator + 99U) / 100U;
    uint64_t cumulative = 0U;
    for (size_t i = 0U; i < REAPER_SYSTEM_LATENCY_BUCKETS; ++i) {
        cumulative += phase->samples[i];
        if (cumulative >= rank)
            return i < REAPER_SYSTEM_LATENCY_BUCKETS - 1U ?
                   latency_upper_bounds[i] : phase->max_ns;
    }
    return phase->max_ns;
}

ReaperSystemStatus reaper_latency_summary(
    const ReaperLatencyProfiler *profiler, size_t phase,
    ReaperLatencySummary *summary
) {
    if (profiler == NULL || summary == NULL ||
        profiler->phase_count > REAPER_SYSTEM_MAX_PHASES ||
        phase >= profiler->phase_count) return REAPER_SYSTEM_INVALID_ARGUMENT;
    const ReaperLatencyPhase *source_phase = &profiler->phases[phase];
    summary->sample_count = source_phase->sample_count;
    summary->mean_ns = source_phase->sample_count == 0U ? 0U :
                       source_phase->total_ns / source_phase->sample_count;
    summary->p95_ns = latency_quantile(source_phase, 95U);
    summary->p99_ns = latency_quantile(source_phase, 99U);
    summary->max_ns = source_phase->max_ns;
    return REAPER_SYSTEM_OK;
}

/* 9. Local-only effect boundary */
ReaperSystemStatus reaper_module_effects_validate(
    int local_only, uint32_t declared_effects,
    uint32_t inferred_effects, uint32_t imported_effects,
    ReaperSystemError *error
) {
    const uint32_t actual_effects = inferred_effects | imported_effects;
    if ((actual_effects & ~declared_effects) != 0U)
        return fail(error, REAPER_SYSTEM_DENIED, 0U, "module uses an effect absent from its declaration");
    if (local_only != 0 &&
        ((declared_effects | actual_effects) & REAPER_EFFECT_FORBIDDEN_LOCAL) != 0U)
        return fail(error, REAPER_SYSTEM_DENIED, 0U, "local-only module cannot depend on network or remote I/O effects");
    return REAPER_SYSTEM_OK;
}

/* 10. Paired migrations */
ReaperSystemStatus reaper_rollback_plan_validate(
    const ReaperRollbackPlan *plan, ReaperSystemError *error
) {
    if (plan == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "rollback plan is required");
    if (!valid_identifier(plan->migration_id) ||
        !valid_identifier(plan->forward_step_id) ||
        !valid_identifier(plan->rollback_step_id) ||
        plan->from_version == 0U || plan->to_version <= plan->from_version ||
        strcmp(plan->forward_step_id, plan->rollback_step_id) == 0)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, 0U, "migration IDs and increasing source/target versions are required");
    if (plan->forward_tested == 0 || plan->rollback_tested == 0)
        return fail(error, REAPER_SYSTEM_UNTESTED_ROLLBACK, 0U, "forward and rollback steps must both have passing tests");
    return REAPER_SYSTEM_OK;
}
