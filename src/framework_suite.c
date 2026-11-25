#include "reaper/framework_suite.h"

#include <ctype.h>
#include <stddef.h>

static const ReaperFrameworkFunction FUNCTIONS_001[] = {
    { "RPR-FWK-001-F01", "lookup_symbol", 1U, 2U, "Resolve a stable symbol key in the public registry." },
    { "RPR-FWK-001-F02", "inspect_feature", 1U, 1U, "Return the maturity record for one language feature." },
    { "RPR-FWK-001-F03", "list_contracts", 1U, 1U, "Enumerate registered operation contracts for a framework." },
    { "RPR-FWK-001-F04", "describe_framework", 1U, 1U, "Read one framework descriptor without executing its operations." },
    { "RPR-FWK-001-F05", "compare_versions", 2U, 2U, "Compare two semantic version identifiers." },
    { "RPR-FWK-001-F06", "export_catalog", 1U, 1U, "Serialize a caller-selected catalog view." }
};

static const ReaperFrameworkFunction FUNCTIONS_002[] = {
    { "RPR-FWK-002-F01", "bind_language", 2U, 3U, "Describe an explicit source-to-host language binding." },
    { "RPR-FWK-002-F02", "validate_abi", 2U, 2U, "Validate an ABI identifier and version pair." },
    { "RPR-FWK-002-F03", "invoke_foreign", 3U, 3U, "Validate a foreign-call request before host dispatch." },
    { "RPR-FWK-002-F04", "marshal_value", 2U, 2U, "Validate a typed value for ABI marshalling." },
    { "RPR-FWK-002-F05", "unmarshal_value", 2U, 2U, "Validate a typed ABI result for decoding." },
    { "RPR-FWK-002-F06", "release_foreign", 1U, 1U, "Validate release of a host-owned foreign handle." }
};

static const ReaperFrameworkFunction FUNCTIONS_003[] = {
    { "RPR-FWK-003-F01", "check_invariant", 2U, 2U, "Evaluate a named invariant against supplied evidence." },
    { "RPR-FWK-003-F02", "reconcile_state", 2U, 2U, "Produce a deterministic reconciliation plan." },
    { "RPR-FWK-003-F03", "compare_contracts", 2U, 2U, "Compare two versioned interface contracts." },
    { "RPR-FWK-003-F04", "validate_schema", 2U, 2U, "Validate a payload against a named schema." },
    { "RPR-FWK-003-F05", "detect_conflict", 2U, 2U, "Identify conflicting values in a merge candidate." },
    { "RPR-FWK-003-F06", "prove_precondition", 2U, 2U, "Check a declared precondition against explicit inputs." }
};

static const ReaperFrameworkFunction FUNCTIONS_004[] = {
    { "RPR-FWK-004-F01", "arena_create", 2U, 2U, "Describe a bounded arena allocation request." },
    { "RPR-FWK-004-F02", "arena_reserve", 2U, 2U, "Validate a reservation against an arena capacity." },
    { "RPR-FWK-004-F03", "arena_release", 1U, 1U, "Validate release of an owned allocation region." },
    { "RPR-FWK-004-F04", "budget_split", 3U, 3U, "Split a resource budget while preserving its total." },
    { "RPR-FWK-004-F05", "quota_check", 2U, 2U, "Compare requested resources with an explicit quota." },
    { "RPR-FWK-004-F06", "allocation_trace", 1U, 1U, "Inspect allocation events for a declared scope." }
};

static const ReaperFrameworkFunction FUNCTIONS_005[] = {
    { "RPR-FWK-005-F01", "map_sequence", 2U, 2U, "Describe a pure sequence transformation." },
    { "RPR-FWK-005-F02", "filter_sequence", 2U, 2U, "Describe a predicate-based sequence filter." },
    { "RPR-FWK-005-F03", "fold_sequence", 3U, 3U, "Describe a left fold with an explicit initial value." },
    { "RPR-FWK-005-F04", "zip_sequences", 2U, 2U, "Describe a bounded pairwise sequence composition." },
    { "RPR-FWK-005-F05", "stable_sort", 2U, 2U, "Describe a deterministic stable ordering." },
    { "RPR-FWK-005-F06", "partition_sequence", 2U, 2U, "Partition a sequence using an explicit size or predicate." }
};

static const ReaperFrameworkFunction FUNCTIONS_006[] = {
    { "RPR-FWK-006-F01", "task_spawn", 2U, 2U, "Validate task creation under a caller-owned task scope." },
    { "RPR-FWK-006-F02", "task_cancel", 2U, 2U, "Validate cancellation of a task handle." },
    { "RPR-FWK-006-F03", "await_result", 2U, 2U, "Describe a bounded wait for a task result." },
    { "RPR-FWK-006-F04", "deadline_after", 2U, 2U, "Calculate a deadline from a supplied monotonic timestamp." },
    { "RPR-FWK-006-F05", "schedule_task", 3U, 3U, "Validate a task scheduling request and its policy." },
    { "RPR-FWK-006-F06", "join_scope", 1U, 1U, "Describe joining all child tasks in a scope." }
};

static const ReaperFrameworkFunction FUNCTIONS_007[] = {
    { "RPR-FWK-007-F01", "abi_negotiate", 2U, 2U, "Negotiate a supported ABI version and feature set." },
    { "RPR-FWK-007-F02", "encode_frame", 2U, 2U, "Validate fields for a versioned binary frame." },
    { "RPR-FWK-007-F03", "decode_frame", 2U, 2U, "Validate a binary frame before decoding." },
    { "RPR-FWK-007-F04", "type_fingerprint", 1U, 1U, "Compute or resolve a stable type fingerprint." },
    { "RPR-FWK-007-F05", "call_descriptor", 2U, 2U, "Resolve a function signature and calling convention." },
    { "RPR-FWK-007-F06", "validate_layout", 2U, 2U, "Check a declared layout against ABI constraints." }
};

static const ReaperFrameworkFunction FUNCTIONS_008[] = {
    { "RPR-FWK-008-F01", "feature_lookup", 1U, 1U, "Resolve a stable language feature key." },
    { "RPR-FWK-008-F02", "feature_enablement", 2U, 2U, "Check feature availability for a target profile." },
    { "RPR-FWK-008-F03", "enumerate_features", 1U, 1U, "Enumerate features in a named capability area." },
    { "RPR-FWK-008-F04", "dependency_order", 1U, 1U, "Return a dependency-safe feature implementation order." },
    { "RPR-FWK-008-F05", "compatibility_check", 2U, 2U, "Check compatibility between two feature profiles." },
    { "RPR-FWK-008-F06", "capability_diff", 2U, 2U, "Describe differences between capability sets." }
};

static const ReaperFrameworkFunction FUNCTIONS_009[] = {
    { "RPR-FWK-009-F01", "grant_create", 3U, 3U, "Describe a scoped capability grant." },
    { "RPR-FWK-009-F02", "grant_check", 3U, 3U, "Check a principal, resource and requested capability." },
    { "RPR-FWK-009-F03", "grant_revoke", 2U, 2U, "Validate revocation of a scoped grant." },
    { "RPR-FWK-009-F04", "scope_intersect", 2U, 2U, "Calculate the least-authority intersection of two scopes." },
    { "RPR-FWK-009-F05", "policy_match", 2U, 2U, "Evaluate a named policy against explicit facts." },
    { "RPR-FWK-009-F06", "audit_decision", 2U, 2U, "Format a decision record without exposing secrets." }
};

static const ReaperFrameworkFunction FUNCTIONS_010[] = {
    { "RPR-FWK-010-F01", "source_map_lookup", 2U, 2U, "Resolve an IR location to its original source span." },
    { "RPR-FWK-010-F02", "span_translate", 2U, 2U, "Translate a span between declared coordinate systems." },
    { "RPR-FWK-010-F03", "diagnostic_emit", 2U, 2U, "Create a structured diagnostic from a code and span." },
    { "RPR-FWK-010-F04", "trace_register", 2U, 2U, "Register a named trace scope and its metadata." },
    { "RPR-FWK-010-F05", "symbol_resolve", 2U, 2U, "Resolve a symbol in a versioned namespace." },
    { "RPR-FWK-010-F06", "origin_chain", 1U, 1U, "Return provenance links for an artifact." }
};

static const ReaperFrameworkFunction FUNCTIONS_011[] = {
    { "RPR-FWK-011-F01", "quality_gate", 2U, 2U, "Evaluate a release gate against its evidence set." },
    { "RPR-FWK-011-F02", "build_matrix", 2U, 2U, "Describe a target and configuration build matrix." },
    { "RPR-FWK-011-F03", "test_evidence", 2U, 2U, "Validate a test result as release evidence." },
    { "RPR-FWK-011-F04", "regression_compare", 2U, 2U, "Compare two metric snapshots for regressions." },
    { "RPR-FWK-011-F05", "artifact_attest", 2U, 2U, "Describe an artifact provenance attestation." },
    { "RPR-FWK-011-F06", "release_check", 1U, 1U, "Summarize readiness of a declared release candidate." }
};

static const ReaperFrameworkFunction FUNCTIONS_012[] = {
    { "RPR-FWK-012-F01", "channel_open", 2U, 2U, "Describe creation of a bounded message channel." },
    { "RPR-FWK-012-F02", "channel_send", 2U, 2U, "Validate sending a typed message to a channel." },
    { "RPR-FWK-012-F03", "channel_receive", 2U, 2U, "Describe receiving one message under a wait policy." },
    { "RPR-FWK-012-F04", "channel_close", 1U, 1U, "Validate closure of a channel owned by the caller." },
    { "RPR-FWK-012-F05", "backpressure_check", 2U, 2U, "Evaluate a queue against an explicit back-pressure limit." },
    { "RPR-FWK-012-F06", "fanout_dispatch", 2U, 2U, "Describe deterministic delivery to a recipient set." }
};

static const ReaperFrameworkFunction FUNCTIONS_013[] = {
    { "RPR-FWK-013-F01", "result_ok", 1U, 1U, "Describe a successful typed result." },
    { "RPR-FWK-013-F02", "result_err", 2U, 2U, "Describe a typed failure result." },
    { "RPR-FWK-013-F03", "map_ok", 2U, 2U, "Describe a transformation applied only to successful results." },
    { "RPR-FWK-013-F04", "map_err", 2U, 2U, "Describe a transformation applied only to error values." },
    { "RPR-FWK-013-F05", "recover_error", 2U, 2U, "Describe recovery under an explicit error policy." },
    { "RPR-FWK-013-F06", "classify_failure", 1U, 1U, "Classify a failure using stable diagnostic categories." }
};

static const ReaperFrameworkFunction FUNCTIONS_014[] = {
    { "RPR-FWK-014-F01", "service_register", 2U, 2U, "Register a service descriptor in a host-owned registry." },
    { "RPR-FWK-014-F02", "service_resolve", 2U, 2U, "Resolve a service by name and version constraints." },
    { "RPR-FWK-014-F03", "endpoint_health", 2U, 2U, "Evaluate a service health response." },
    { "RPR-FWK-014-F04", "event_publish", 2U, 2U, "Validate publication to a named event topic." },
    { "RPR-FWK-014-F05", "event_subscribe", 2U, 2U, "Describe a scoped event subscription." },
    { "RPR-FWK-014-F06", "event_ack", 2U, 2U, "Validate acknowledgement of a delivered event." }
};

static const ReaperFrameworkFunction FUNCTIONS_015[] = {
    { "RPR-FWK-015-F01", "module_load", 2U, 2U, "Describe loading a versioned Reaper module." },
    { "RPR-FWK-015-F02", "module_export", 2U, 2U, "Resolve a public export from a module." },
    { "RPR-FWK-015-F03", "module_import", 2U, 2U, "Validate an explicit module import request." },
    { "RPR-FWK-015-F04", "dependency_resolve", 1U, 1U, "Resolve a dependency closure without executing it." },
    { "RPR-FWK-015-F05", "module_version", 1U, 1U, "Read a module's declared semantic version." },
    { "RPR-FWK-015-F06", "module_unload", 2U, 2U, "Validate unloading after owned references are released." }
};

static const ReaperFrameworkFunction FUNCTIONS_016[] = {
    { "RPR-FWK-016-F01", "core_hash", 1U, 1U, "Compute a stable hash over canonical bytes." },
    { "RPR-FWK-016-F02", "checksum", 1U, 1U, "Calculate a corruption-detection checksum." },
    { "RPR-FWK-016-F03", "stable_id", 2U, 2U, "Derive a stable identifier from a namespace and input." },
    { "RPR-FWK-016-F04", "text_normalize", 2U, 2U, "Normalize text under an explicit normalization policy." },
    { "RPR-FWK-016-F05", "compare_bytes", 2U, 2U, "Compare byte sequences without implicit conversion." },
    { "RPR-FWK-016-F06", "version_parse", 1U, 1U, "Parse a strict semantic version identifier." }
};

static const ReaperFrameworkFunction FUNCTIONS_017[] = {
    { "RPR-FWK-017-F01", "fault_record", 2U, 2U, "Create a structured fault record from supplied evidence." },
    { "RPR-FWK-017-F02", "retry_plan", 3U, 3U, "Calculate a bounded retry plan." },
    { "RPR-FWK-017-F03", "circuit_check", 2U, 2U, "Evaluate a circuit-breaker state transition." },
    { "RPR-FWK-017-F04", "fallback_select", 2U, 2U, "Select a declared fallback for a failed component." },
    { "RPR-FWK-017-F05", "isolate_component", 2U, 2U, "Describe isolation within a host-authorized boundary." },
    { "RPR-FWK-017-F06", "recovery_report", 1U, 1U, "Summarize a recovery attempt and its evidence." }
};

static const ReaperFrameworkFunction FUNCTIONS_018[] = {
    { "RPR-FWK-018-F01", "stream_open", 2U, 2U, "Describe opening a typed stream under a bounded policy." },
    { "RPR-FWK-018-F02", "stream_push", 2U, 2U, "Validate a stream item before enqueueing." },
    { "RPR-FWK-018-F03", "stream_merge", 2U, 2U, "Describe a deterministic merge of compatible streams." },
    { "RPR-FWK-018-F04", "stream_throttle", 2U, 2U, "Apply a declared rate or demand limit." },
    { "RPR-FWK-018-F05", "stream_checkpoint", 1U, 1U, "Describe a checkpoint for replayable stream state." },
    { "RPR-FWK-018-F06", "stream_close", 1U, 1U, "Validate stream closure and resource release." }
};

static const ReaperFrameworkFunction FUNCTIONS_019[] = {
    { "RPR-FWK-019-F01", "access_decide", 3U, 3U, "Make an explicit allow-or-deny decision from policy inputs." },
    { "RPR-FWK-019-F02", "principal_resolve", 1U, 1U, "Resolve a principal from a trusted host identity." },
    { "RPR-FWK-019-F03", "secret_ref", 2U, 2U, "Create a non-secret reference to a host-managed secret." },
    { "RPR-FWK-019-F04", "token_validate", 2U, 2U, "Validate token metadata without logging token material." },
    { "RPR-FWK-019-F05", "policy_compile", 2U, 2U, "Validate a policy before host enforcement." },
    { "RPR-FWK-019-F06", "security_audit", 2U, 2U, "Create a redacted security audit event." }
};

static const ReaperFrameworkFunction FUNCTIONS_020[] = {
    { "RPR-FWK-020-F01", "stats_snapshot", 1U, 1U, "Create a snapshot from published, non-sensitive counters." },
    { "RPR-FWK-020-F02", "counter_add", 2U, 2U, "Describe a monotonic counter update." },
    { "RPR-FWK-020-F03", "gauge_set", 2U, 2U, "Describe an absolute gauge update." },
    { "RPR-FWK-020-F04", "histogram_observe", 2U, 2U, "Record an observation in a declared histogram." },
    { "RPR-FWK-020-F05", "metrics_export", 2U, 2U, "Export selected aggregate metrics in a versioned format." },
    { "RPR-FWK-020-F06", "privacy_filter", 2U, 2U, "Remove or aggregate fields outside a public metrics policy." }
};

static const ReaperFramework FRAMEWORKS[] = {
    { "codex-no", "CodexNo", "Compiler and language feature catalog", "RPR-FWK-001", "contract-only", FUNCTIONS_001, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "joint-baby", "Joint Baby", "Cross-language composition and ABI binding", "RPR-FWK-002", "contract-only", FUNCTIONS_002, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "correpse", "Correpse", "Contracts, consistency and reconciliation", "RPR-FWK-003", "contract-only", FUNCTIONS_003, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "allocate-purpose", "Allocate Purpose", "Memory, allocation and resource budgets", "RPR-FWK-004", "contract-only", FUNCTIONS_004, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "collillioi", "Collillioi", "Collections and deterministic algorithms", "RPR-FWK-005", "contract-only", FUNCTIONS_005, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "aspdoi", "Aspdoi", "Asynchronous tasks and structured scheduling", "RPR-FWK-006", "contract-only", FUNCTIONS_006, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "asjiop", "ASJIOP", "ABI, serialization and binary layouts", "RPR-FWK-007", "contract-only", FUNCTIONS_007, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "alllll", "ALLLLL", "Language feature registry and compatibility", "RPR-FWK-008", "contract-only", FUNCTIONS_008, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "zabor", "Zabor", "Capability grants and policy scopes", "RPR-FWK-009", "contract-only", FUNCTIONS_009, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "vjinz", "Vjinz", "Source maps, diagnostics and tracing", "RPR-FWK-010", "contract-only", FUNCTIONS_010, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "supreme-boy", "SupremeBoy", "Quality gates and release evidence", "RPR-FWK-011", "contract-only", FUNCTIONS_011, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "chee-now", "CheeNow", "Channels, concurrency and back-pressure", "RPR-FWK-012", "contract-only", FUNCTIONS_012, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "humble-bumble", "HumbleBumble", "Result values, error taxonomy and recovery", "RPR-FWK-013", "contract-only", FUNCTIONS_013, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "hub2", "Hub2", "Service discovery and event distribution", "RPR-FWK-014", "contract-only", FUNCTIONS_014, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "kloz", "Kloz", "Modules, packages and dependency lifecycle", "RPR-FWK-015", "contract-only", FUNCTIONS_015, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "co", "CO", "Core primitives and deterministic identity", "RPR-FWK-016", "contract-only", FUNCTIONS_016, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "cripplebo", "CrippleBO", "Fault records and resilience policies", "RPR-FWK-017", "contract-only", FUNCTIONS_017, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "ripplecripple", "RippleCripple", "Reactive streams and flow control", "RPR-FWK-018", "contract-only", FUNCTIONS_018, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "secator", "Secator", "Security policy and secret references", "RPR-FWK-019", "contract-only", FUNCTIONS_019, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE },
    { "pollatia", "PollATIA", "Public statistics and privacy-aware metrics", "RPR-FWK-020", "contract-only", FUNCTIONS_020, REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE }
};

static int ascii_equal_ci(const char *left, const char *right) {
    if (left == NULL || right == NULL) return 0;
    while (*left != '\0' && *right != '\0') {
        if (tolower((unsigned char)*left) != tolower((unsigned char)*right)) return 0;
        ++left;
        ++right;
    }
    return *left == '\0' && *right == '\0';
}

uint32_t reaper_framework_abi_version(void) {
    return REAPER_FRAMEWORK_ABI_VERSION;
}

uint32_t reaper_framework_count(void) {
    return (uint32_t)(sizeof(FRAMEWORKS) / sizeof(FRAMEWORKS[0]));
}

const ReaperFramework *reaper_framework_at(uint32_t index) {
    if (index >= reaper_framework_count()) return NULL;
    return &FRAMEWORKS[index];
}

const ReaperFramework *reaper_framework_find(const char *id_or_name) {
    if (id_or_name == NULL) return NULL;
    for (uint32_t i = 0U; i < reaper_framework_count(); ++i) {
        if (ascii_equal_ci(FRAMEWORKS[i].id, id_or_name) ||
            ascii_equal_ci(FRAMEWORKS[i].name, id_or_name)) return &FRAMEWORKS[i];
    }
    return NULL;
}

const ReaperFrameworkFunction *reaper_framework_function_find(
    const ReaperFramework *framework, const char *function_name
) {
    if (framework == NULL || function_name == NULL) return NULL;
    for (uint32_t i = 0U; i < framework->function_count; ++i) {
        if (ascii_equal_ci(framework->functions[i].name, function_name))
            return &framework->functions[i];
    }
    return NULL;
}

ReaperFrameworkStatus reaper_framework_validate_arity(
    const ReaperFramework *framework, const char *function_name,
    uint32_t argument_count, const ReaperFrameworkFunction **function_out
) {
    const ReaperFrameworkFunction *function;
    if (function_out != NULL) *function_out = NULL;
    if (framework == NULL || function_name == NULL)
        return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    function = reaper_framework_function_find(framework, function_name);
    if (function == NULL) return REAPER_FRAMEWORK_NOT_FOUND;
    if (argument_count < function->min_arity ||
        argument_count > function->max_arity)
        return REAPER_FRAMEWORK_ARITY_MISMATCH;
    if (function_out != NULL) *function_out = function;
    return REAPER_FRAMEWORK_OK;
}

ReaperFrameworkStatus reaper_framework_registry_stats(
    ReaperFrameworkRegistryStats *stats
) {
    uint32_t contracts = 0U;
    if (stats == NULL) return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    for (uint32_t i = 0U; i < reaper_framework_count(); ++i)
        contracts += FRAMEWORKS[i].function_count;
    stats->registered_frameworks = reaper_framework_count();
    stats->registered_function_contracts = contracts;
    stats->registry_api_functions = REAPER_FRAMEWORK_REGISTRY_API_FUNCTIONS;
    stats->executable_domain_handlers = 0U;
    stats->reaper_source_bindings = 0U;
    return REAPER_FRAMEWORK_OK;
}
