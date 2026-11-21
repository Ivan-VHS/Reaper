#include "reaper/capability_suite.h"

#include <math.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>

#define FN(name_, min_, max_, description_) { name_, min_, max_, description_ }
#define MODULE(id_, name_, domain_, array_) \
    { id_, name_, domain_, array_, sizeof(array_) / sizeof((array_)[0]) }

static const ReaperCapabilityFunction OPERANDU[] = {
    FN("eval_expression", 2U, 2U, "Evaluate a typed expression in an explicit data context."),
    FN("bind_operands", 3U, 3U, "Bind two operands and validate operator type compatibility."),
    FN("fold_series", 3U, 3U, "Reduce an immutable series with an initial accumulator."),
    FN("map_operands", 2U, 2U, "Transform each operand without mutating the input collection."),
    FN("validate_arity", 2U, 2U, "Validate an operation name and its argument signature."),
    FN("trace_ast", 1U, 1U, "Return an AST traversal trace and evaluation order.")
};
static const ReaperCapabilityFunction DROPAUL[] = {
    FN("accept_drop", 2U, 2U, "Validate a payload before accepting it into a target zone."),
    FN("route_payload", 2U, 2U, "Select a destination channel by deterministic routing rules."),
    FN("drain_queue", 2U, 2U, "Remove a bounded batch from a queue and report processing state."),
    FN("stage_artifact", 2U, 2U, "Place an artifact reference into a staging bucket."),
    FN("quarantine_invalid", 2U, 2U, "Isolate an invalid item without stopping unrelated work."),
    FN("flush_staging", 1U, 1U, "Commit staged entries to the configured destination.")
};
static const ReaperCapabilityFunction ZDORO[] = {
    FN("log_checkin", 2U, 2U, "Record a user-controlled wellness check-in with consent."),
    FN("compute_readiness", 1U, 1U, "Calculate a non-clinical readiness indicator from history."),
    FN("schedule_recovery", 2U, 2U, "Suggest recovery windows from load and scheduling constraints."),
    FN("track_habit_streak", 2U, 2U, "Track completion streaks and missed habit check-ins."),
    FN("alert_overstrain", 2U, 2U, "Compare declared metrics with user-configured thresholds."),
    FN("summarize_wellness", 1U, 1U, "Summarize user-owned wellness records for a time period.")
};
static const ReaperCapabilityFunction PYEMONT[] = {
    FN("build_slice", 3U, 3U, "Build a filtered multidimensional slice from a dataset."),
    FN("calc_delta", 2U, 2U, "Calculate absolute and relative changes against a baseline."),
    FN("detect_anomalies", 2U, 2U, "Flag statistically unusual points in a time series."),
    FN("forecast_trend", 2U, 2U, "Project a trend over a caller-selected horizon."),
    FN("rank_segments", 2U, 2U, "Rank segments by a selected numeric metric."),
    FN("export_report", 2U, 2U, "Serialize a prepared report to a supported format.")
};
static const ReaperCapabilityFunction DILLY[] = {
    FN("defer_task", 2U, 2U, "Persist a task for execution after a relative delay."),
    FN("snooze_reminder", 2U, 2U, "Move a reminder deadline while preserving its context."),
    FN("hold_in_buffer", 2U, 2U, "Hold an item until a TTL expires or an event releases it."),
    FN("release_due", 1U, 1U, "Release due entries using a supplied monotonic or wall-clock timestamp."),
    FN("cancel_deferred", 1U, 1U, "Cancel a deferred entry and release its timer resources."),
    FN("list_pending", 1U, 1U, "List pending tasks under a caller-provided scope filter.")
};
static const ReaperCapabilityFunction BAPLAP[] = {
    FN("start_lap", 2U, 2U, "Start a measured lap within a live timing session."),
    FN("split_lap", 1U, 1U, "Record a split and begin the next lap."),
    FN("iterate_batch", 2U, 2U, "Apply a deterministic step to a bounded batch."),
    FN("retry_loop", 3U, 3U, "Retry a callback with a bounded attempt count and backoff."),
    FN("calc_lap_stats", 1U, 1U, "Calculate mean, minimum and maximum lap durations."),
    FN("close_session", 1U, 1U, "Close a timing session and archive its measured laps.")
};
static const ReaperCapabilityFunction SRETUO[] = {
    FN("reverse_sequence", 1U, 1U, "Reverse sequence order without changing element values."),
    FN("invert_predicate", 1U, 1U, "Create the logical inverse of a predicate."),
    FN("rollback_state", 1U, 1U, "Restore a validated state snapshot."),
    FN("mirror_mapping", 1U, 1U, "Swap mapping keys and values after uniqueness checks."),
    FN("undo_last_op", 1U, 1U, "Undo the last reversible operation in a history stack."),
    FN("flip_axis", 2U, 2U, "Transpose or reflect a matrix along the selected axis.")
};
static const ReaperCapabilityFunction KALI[] = {
    FN("verify_capability", 3U, 3U, "Authorize an actor against a resource and requested action."),
    FN("sandbox_exec", 2U, 2U, "Request isolated execution under an explicit resource policy."),
    FN("scan_payload", 2U, 2U, "Inspect untrusted content against a named security policy."),
    FN("rotate_secret", 1U, 1U, "Rotate a managed secret without exposing its value."),
    FN("audit_event", 2U, 2U, "Append a structured event to the audit stream."),
    FN("revoke_session", 2U, 2U, "Revoke an active session and its associated credentials.")
};
static const ReaperCapabilityFunction ZALAM[] = {
    FN("split_by_delimiter", 2U, 2U, "Split text or a stream at an explicit boundary."),
    FN("clip_range", 3U, 3U, "Clamp a numeric value to an inclusive range."),
    FN("chunk_collection", 2U, 2U, "Partition a collection into bounded fixed-size chunks."),
    FN("splice_segments", 4U, 4U, "Replace or insert a segment at a checked sequence offset."),
    FN("find_breakpoints", 2U, 2U, "Detect abrupt transitions in an ordered numeric series."),
    FN("stitch_fragments", 2U, 2U, "Join validated fragments using an explicit bridge.")
};
static const ReaperCapabilityFunction LIUR[] = {
    FN("link_entities", 3U, 3U, "Create a typed relationship between two entity identifiers."),
    FN("resolve_deps", 1U, 1U, "Resolve a dependency closure in valid processing order."),
    FN("find_path", 3U, 3U, "Find a path between nodes in a supplied graph."),
    FN("detect_cycles", 1U, 1U, "Detect directed cycles in a dependency graph."),
    FN("unlink_entities", 3U, 3U, "Remove a typed relationship and validate graph integrity."),
    FN("neighbors_of", 2U, 2U, "Enumerate graph neighbors up to a bounded traversal depth.")
};
static const ReaperCapabilityFunction KEEL_KOH[] = {
    FN("set_anchor", 2U, 2U, "Store a baseline value for a named configuration parameter."),
    FN("stabilize_config", 2U, 2U, "Reconcile a configuration against an approved anchor set."),
    FN("dampen_fluctuation", 2U, 2U, "Smooth a numeric series with an explicit damping factor."),
    FN("check_drift", 3U, 3U, "Compare a current value against its anchor and tolerance."),
    FN("pin_version", 2U, 2U, "Pin a component to an exact version identifier."),
    FN("restore_baseline", 1U, 1U, "Restore an approved baseline within a named scope.")
};
static const ReaperCapabilityFunction VOROF[] = {
    FN("harvest_source", 1U, 1U, "Collect records from a registered source under a schedule or trigger."),
    FN("merge_feeds", 2U, 2U, "Merge input feeds and deduplicate by a stable key."),
    FN("extract_fields", 2U, 2U, "Normalize selected source fields through a schema map."),
    FN("aggregate_batch", 3U, 3U, "Group records and calculate configured aggregates."),
    FN("pull_incremental", 1U, 1U, "Read records newer than a persisted source cursor."),
    FN("consolidate_store", 1U, 1U, "Consolidate records into a selected target store.")
};
static const ReaperCapabilityFunction VPROF[] = {
    FN("profile_block", 2U, 2U, "Measure elapsed time and resource counters around a callback."),
    FN("sample_cpu_mem", 1U, 1U, "Sample CPU and memory telemetry at a bounded interval."),
    FN("find_bottlenecks", 1U, 1U, "Rank expensive stages from captured execution traces."),
    FN("count_allocations", 1U, 1U, "Read allocation counters for a defined instrumentation scope."),
    FN("compare_profiles", 2U, 2U, "Compare captured profiles and identify regressions."),
    FN("dump_flame_data", 1U, 1U, "Export stack samples in a flame-graph compatible format.")
};
static const ReaperCapabilityFunction PROFE[] = {
    FN("create_profile", 3U, 3U, "Create a profile with a named role and validated attributes."),
    FN("assign_role", 2U, 2U, "Assign a role and its policy-bound capability set."),
    FN("map_competencies", 2U, 2U, "Map a profile to a declared competency matrix."),
    FN("evaluate_readiness", 2U, 2U, "Compare a profile against a task requirement set."),
    FN("update_attrs", 2U, 2U, "Apply a schema-checked attribute patch with history."),
    FN("match_profiles", 2U, 2U, "Rank candidate profiles against explicit selection criteria.")
};
static const ReaperCapabilityFunction PROSSEE[] = {
    FN("start_process", 2U, 2U, "Start a process instance from a registered definition."),
    FN("advance_stage", 2U, 2U, "Advance a process after validating transition guards."),
    FN("pause_process", 2U, 2U, "Pause a process while retaining its execution context."),
    FN("resume_process", 1U, 1U, "Resume a process from a valid paused state."),
    FN("handle_step_error", 3U, 3U, "Apply a configured retry, branch or stop policy to a failed step."),
    FN("get_process_status", 1U, 1U, "Return process state, completed steps and active locks.")
};
static const ReaperCapabilityFunction VPROSSEE[] = {
    FN("build_survey", 2U, 2U, "Build a typed survey with validation and branching rules."),
    FN("next_question", 2U, 2U, "Select the next survey question from the previous answer."),
    FN("validate_answer", 2U, 2U, "Validate a response against its declared question schema."),
    FN("score_responses", 2U, 2U, "Calculate a weighted score from validated session answers."),
    FN("branch_logic", 2U, 2U, "Evaluate a survey branch using validated answers."),
    FN("export_answers", 2U, 2U, "Export survey answers in an explicitly selected format.")
};
static const ReaperCapabilityFunction PROFESSIYA[] = {
    FN("catalog_professions", 1U, 1U, "List profession profiles matching structured filters."),
    FN("get_requirements", 1U, 1U, "Return the required competencies for a profession profile."),
    FN("build_career_track", 3U, 3U, "Build a skill-aware transition path between profession profiles."),
    FN("calc_skill_gap", 2U, 2U, "Measure missing competencies against a target profession."),
    FN("suggest_roles", 1U, 1U, "Suggest roles from a declared skills profile."),
    FN("benchmark_role", 2U, 2U, "Compare role requirements for a selected region or segment.")
};
static const ReaperCapabilityFunction PROFEVO[] = {
    FN("record_milestone", 2U, 2U, "Record a dated, measurable evolution milestone."),
    FN("evolve_level", 3U, 3U, "Update a domain level using an explicit progress delta."),
    FN("snapshot_evolution", 1U, 1U, "Capture a versioned snapshot of current progress state."),
    FN("diff_stages", 3U, 3U, "Compare two evolution snapshots and report changed fields."),
    FN("adapt_plan", 2U, 2U, "Adapt a development plan to updated goals and evidence."),
    FN("project_growth", 2U, 2U, "Project a growth trajectory over a bounded number of periods.")
};

static const ReaperCapabilityModule MODULES[] = {
    MODULE("operandu", "Operandu", "Expressions, operands and transformations", OPERANDU),
    MODULE("dropaul", "Dropaul", "Payload routing, queues and staging", DROPAUL),
    MODULE("zdoro", "Zdoro", "Wellness check-ins and recovery", ZDORO),
    MODULE("pyemont", "Pyemont", "Analytics, reports and forecasts", PYEMONT),
    MODULE("dilly", "Dilly", "Deferred tasks and reminders", DILLY),
    MODULE("baplap", "Baplap", "Iterations, retries and lap timing", BAPLAP),
    MODULE("sretuo", "Sretuo", "Reversal, rollback and mirroring", SRETUO),
    MODULE("kali", "Kali", "Security, isolation and access control", KALI),
    MODULE("zalam", "Zalam", "Segmentation, clipping and stitching", ZALAM),
    MODULE("liur", "Liur", "Entity links and dependency graphs", LIUR),
    MODULE("keel-koh", "Keel Koh", "Anchors, stabilization and drift control", KEEL_KOH),
    MODULE("vorof", "Vorof", "Source collection and consolidation", VOROF),
    MODULE("vprof", "Vprof", "Profiling, telemetry and allocations", VPROF),
    MODULE("profe", "Profe", "Profiles, roles and competencies", PROFE),
    MODULE("prossee", "Prossee", "Process lifecycles and transitions", PROSSEE),
    MODULE("vprossee", "Vprossee", "Surveys, responses and branching", VPROSSEE),
    MODULE("professiya", "Professiya", "Profession and career tracks", PROFESSIYA),
    MODULE("profevo", "Profevo", "Evolution and growth planning", PROFEVO)
};

#undef MODULE
#undef FN

static int ascii_equal_ci(const char *left, const char *right) {
    if (left == NULL || right == NULL) return 0;
    while (*left != '\0' && *right != '\0') {
        if (tolower((unsigned char)*left) != tolower((unsigned char)*right)) return 0;
        ++left;
        ++right;
    }
    return *left == '\0' && *right == '\0';
}

size_t reaper_capability_module_count(void) {
    return sizeof(MODULES) / sizeof(MODULES[0]);
}

const ReaperCapabilityModule *reaper_capability_module_at(size_t index) {
    if (index >= reaper_capability_module_count()) return NULL;
    return &MODULES[index];
}

const ReaperCapabilityModule *reaper_capability_module_find(const char *id_or_name) {
    if (id_or_name == NULL) return NULL;
    for (size_t i = 0U; i < reaper_capability_module_count(); ++i) {
        if (ascii_equal_ci(MODULES[i].id, id_or_name) ||
            ascii_equal_ci(MODULES[i].name, id_or_name)) return &MODULES[i];
    }
    return NULL;
}

const ReaperCapabilityFunction *reaper_capability_function_find(
    const ReaperCapabilityModule *module, const char *function_name
) {
    if (module == NULL || function_name == NULL) return NULL;
    for (size_t i = 0U; i < module->function_count; ++i) {
        if (ascii_equal_ci(module->functions[i].name, function_name))
            return &module->functions[i];
    }
    return NULL;
}

ReaperCapabilityStatus reaper_capability_validate_arity(
    const ReaperCapabilityModule *module, const char *function_name,
    size_t argument_count, const ReaperCapabilityFunction **function_out
) {
    const ReaperCapabilityFunction *function =
        reaper_capability_function_find(module, function_name);
    if (function_out != NULL) *function_out = function;
    if (module == NULL || function_name == NULL)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    if (function == NULL) return REAPER_CAPABILITY_NOT_FOUND;
    if (argument_count < function->min_arity ||
        argument_count > function->max_arity)
        return REAPER_CAPABILITY_ARITY_MISMATCH;
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_fold_i64(
    const int64_t *items, size_t count, ReaperI64Reducer reducer,
    void *context, int64_t initial, int64_t *result
) {
    int64_t aggregate = initial;
    if ((count > 0U && items == NULL) || reducer == NULL || result == NULL)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    for (size_t i = 0U; i < count; ++i)
        aggregate = reducer(aggregate, items[i], i, context);
    *result = aggregate;
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_map_i64(
    const int64_t *items, size_t count, ReaperI64Transform transform,
    void *context, int64_t *output, size_t output_capacity
) {
    if ((count > 0U && (items == NULL || output == NULL || items == output)) ||
        transform == NULL)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    if (output_capacity < count) return REAPER_CAPABILITY_OUT_OF_RANGE;
    for (size_t i = 0U; i < count; ++i)
        output[i] = transform(items[i], i, context);
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_reverse_i64(
    const int64_t *items, size_t count, int64_t *output,
    size_t output_capacity
) {
    if ((count > 0U && (items == NULL || output == NULL)))
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    if (output_capacity < count) return REAPER_CAPABILITY_OUT_OF_RANGE;
    if (items == output) {
        for (size_t i = 0U; i < count / 2U; ++i) {
            const int64_t value = output[i];
            output[i] = output[count - 1U - i];
            output[count - 1U - i] = value;
        }
    } else {
        for (size_t i = 0U; i < count; ++i)
            output[i] = items[count - 1U - i];
    }
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_clip_f64(
    double value, double minimum, double maximum, double *output
) {
    if (output == NULL) return REAPER_CAPABILITY_INVALID_ARGUMENT;
    if (!isfinite(value) || !isfinite(minimum) || !isfinite(maximum))
        return REAPER_CAPABILITY_NUMERIC_ERROR;
    if (minimum > maximum) return REAPER_CAPABILITY_OUT_OF_RANGE;
    *output = value < minimum ? minimum : (value > maximum ? maximum : value);
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_chunk_count(
    size_t item_count, size_t chunk_size, size_t *chunk_count
) {
    if (chunk_count == NULL || chunk_size == 0U)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    *chunk_count = item_count == 0U ? 0U : 1U + (item_count - 1U) / chunk_size;
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_calc_delta_f64(
    double current, double baseline, double *absolute_delta,
    double *relative_delta
) {
    double absolute_value;
    double relative_value;
    if (absolute_delta == NULL || relative_delta == NULL)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    if (!isfinite(current) || !isfinite(baseline))
        return REAPER_CAPABILITY_NUMERIC_ERROR;
    absolute_value = current - baseline;
    if (!isfinite(absolute_value) || baseline == 0.0)
        return REAPER_CAPABILITY_NUMERIC_ERROR;
    relative_value = absolute_value / baseline;
    if (!isfinite(relative_value)) return REAPER_CAPABILITY_NUMERIC_ERROR;
    *absolute_delta = absolute_value;
    *relative_delta = relative_value;
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_detect_anomalies_f64(
    const double *series, size_t count, double sensitivity,
    unsigned char *flags, size_t flags_capacity, size_t *anomaly_count
) {
    long double mean = 0.0L;
    long double variance = 0.0L;
    size_t anomalies = 0U;
    if (series == NULL || flags == NULL || anomaly_count == NULL ||
        count == 0U || !isfinite(sensitivity) || sensitivity <= 0.0)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    if (flags_capacity < count) return REAPER_CAPABILITY_OUT_OF_RANGE;
    for (size_t i = 0U; i < count; ++i) {
        if (!isfinite(series[i])) return REAPER_CAPABILITY_NUMERIC_ERROR;
        mean += (long double)series[i];
    }
    mean /= (long double)count;
    for (size_t i = 0U; i < count; ++i) {
        const long double diff = (long double)series[i] - mean;
        variance += diff * diff;
    }
    variance /= (long double)count;
    if (!isfinite((double)mean) || !isfinite((double)variance))
        return REAPER_CAPABILITY_NUMERIC_ERROR;
    for (size_t i = 0U; i < count; ++i) {
        const long double diff = (long double)series[i] - mean;
        const long double lhs = diff * diff;
        const long double rhs = (long double)sensitivity *
            (long double)sensitivity * variance;
        flags[i] = (unsigned char)(variance > 0.0L && lhs > rhs ? 1U : 0U);
        if (flags[i] != 0U) ++anomalies;
    }
    *anomaly_count = anomalies;
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_forecast_trend_f64(
    const double *series, size_t count, size_t horizon, double *forecast
) {
    long double sum_x = 0.0L, sum_y = 0.0L, sum_xy = 0.0L, sum_x2 = 0.0L;
    long double denominator, slope, intercept, target_x, predicted;
    if (series == NULL || forecast == NULL || count < 2U || horizon == 0U)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    for (size_t i = 0U; i < count; ++i) {
        const long double x = (long double)i;
        const long double y = (long double)series[i];
        if (!isfinite(series[i])) return REAPER_CAPABILITY_NUMERIC_ERROR;
        sum_x += x;
        sum_y += y;
        sum_xy += x * y;
        sum_x2 += x * x;
    }
    denominator = (long double)count * sum_x2 - sum_x * sum_x;
    if (denominator == 0.0L) return REAPER_CAPABILITY_NUMERIC_ERROR;
    slope = ((long double)count * sum_xy - sum_x * sum_y) / denominator;
    intercept = (sum_y - slope * sum_x) / (long double)count;
    target_x = (long double)count + (long double)horizon - 1.0L;
    predicted = intercept + slope * target_x;
    if (predicted > (long double)HUGE_VAL || predicted < -(long double)HUGE_VAL)
        return REAPER_CAPABILITY_NUMERIC_ERROR;
    *forecast = (double)predicted;
    if (!isfinite(*forecast)) return REAPER_CAPABILITY_NUMERIC_ERROR;
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_check_drift_f64(
    double current, double anchor, double tolerance, int *drifted
) {
    const long double difference = (long double)current - (long double)anchor;
    if (drifted == NULL || !isfinite(current) || !isfinite(anchor) ||
        !isfinite(tolerance) || tolerance < 0.0)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    *drifted = (difference < 0.0L ? -difference : difference) >
        (long double)tolerance ? 1 : 0;
    return REAPER_CAPABILITY_OK;
}

ReaperCapabilityStatus reaper_capability_retry_delay_ms(
    unsigned attempt, unsigned base_delay_ms, unsigned max_delay_ms,
    unsigned *delay_ms
) {
    unsigned long long delay = (unsigned long long)base_delay_ms;
    if (delay_ms == NULL || max_delay_ms < base_delay_ms)
        return REAPER_CAPABILITY_INVALID_ARGUMENT;
    for (unsigned i = 0U; i < attempt && delay < (unsigned long long)max_delay_ms; ++i) {
        delay *= 2ULL;
        if (delay > (unsigned long long)max_delay_ms)
            delay = (unsigned long long)max_delay_ms;
    }
    if (delay > (unsigned long long)max_delay_ms)
        delay = (unsigned long long)max_delay_ms;
    *delay_ms = (unsigned)delay;
    return REAPER_CAPABILITY_OK;
}
