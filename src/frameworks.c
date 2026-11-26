#include "reaper/frameworks.h"

#include <ctype.h>
#include <string.h>

#define F(id_, name_, domain_, focus_, deliverable_, evidence_) \
    { id_, name_, domain_, focus_, deliverable_, evidence_ }

static const ReaperFrameworkSpec FRAMEWORKS[] = {
    F("jevron", "Jevron", "architecture", "system topology discovery", "versioned architecture graph and unresolved-boundary report", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS),
    F("jarfen", "Jarfen", "architecture", "module and ownership boundaries", "module ownership map and boundary violations", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("trexjon", "Trexjon", "architecture", "dependency graph and cycle analysis", "deterministic dependency graph and cycle report", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS),
    F("voljmer", "Voljmer", "architecture", "component decomposition and cohesion", "component map with coupling and cohesion findings", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS),
    F("reijen", "Reijen", "architecture", "requirement-to-implementation traceability", "requirement coverage matrix with missing links", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("drajen", "Drajen", "architecture", "architecture decision and constraint analysis", "decision record, assumptions and trade-off ledger", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("spijron", "Spijron", "source-quality", "source inventory and ownership discovery", "source inventory with module and language totals", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("vexjor", "Vexjor", "source-quality", "static source analysis and finding triage", "prioritized static-analysis findings with source locations", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("krejndar", "Krejndar", "source-quality", "complexity and maintainability analysis", "complexity baseline and bounded decomposition proposals", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_PERFORMANCE),
    F("morjen", "Morjen", "source-quality", "behavior-preserving refactor planning", "refactor plan with compatibility checkpoints", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("tarjen", "Tarjen", "source-quality", "public API and extension-point design", "API surface inventory and compatibility contract", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("flixjen", "Flixjen", "source-quality", "coding convention and consistency audit", "actionable consistency findings without automatic rewrites", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("jorjan", "Jorjan", "security", "threat modeling and attack-surface mapping", "threat model with assets, trust boundaries and mitigations", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("brejven", "Brejven", "security", "secret and credential exposure detection", "redacted secret-pattern findings and remediation guidance", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("keldjor", "Keldjor", "security", "privilege and capability-boundary review", "least-privilege matrix and privilege escalation findings", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY | REAPER_FRAMEWORK_EVIDENCE_TESTS),
    F("vajpern", "Vajpern", "security", "dependency and software-supply-chain review", "dependency provenance and supply-chain risk report", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("grejmor", "Grejmor", "security", "vulnerability triage and secure-code review", "severity-ranked security findings with evidence references", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("teljorn", "Teljorn", "security", "trust-boundary and untrusted-input analysis", "input-boundary map with limits and rejection requirements", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("sajfern", "Sajfern", "delivery", "build-system and toolchain integrity", "build graph, toolchain constraints and reproducibility gaps", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("deljen", "Deljen", "delivery", "test pipeline and test ownership design", "test inventory and verification pipeline plan", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS),
    F("roxjon", "Roxjon", "delivery", "continuous-integration workflow review", "CI dependency graph and missing quality-gate report", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("meljorn", "Meljorn", "delivery", "package and artifact construction", "artifact manifest and packaging acceptance checklist", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("kejron", "Kejron", "delivery", "release staging and release readiness", "release gate report with blocking evidence", REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("fenjer", "Fenjer", "delivery", "reproducible build and provenance analysis", "reproducibility checklist and build-input provenance report", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("vorjen", "Vorjen", "contracts-data", "schema definition and data-shape validation", "versioned schema proposal and validation cases", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("trajven", "Trajven", "contracts-data", "data and API migration planning", "ordered migration plan with rollback checkpoints", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("skorjen", "Skorjen", "contracts-data", "serialization and interchange formats", "serialization contract with round-trip and malformed-input cases", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("beljtor", "Beljtor", "contracts-data", "persistence and data-integrity controls", "integrity invariants and recovery verification plan", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("nexjen", "Nexjen", "contracts-data", "contract drift and schema compatibility", "contract drift report and version-alignment actions", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("derjon", "Derjon", "contracts-data", "backward and forward compatibility", "compatibility matrix with explicit unsupported combinations", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("kreijen", "Kreijen", "verification", "test strategy and acceptance-case design", "test strategy covering normal, boundary and failure cases", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS),
    F("veljkor", "Veljkor", "verification", "property, invariant and boundary testing", "invariant catalogue and property-test plan", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("tesjen", "Tesjen", "verification", "regression detection and behavioral parity", "regression matrix tied to changed behavior", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("morjden", "Morjden", "verification", "module and service integration testing", "integration scenarios with contract-level assertions", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("zefirn", "Zefirn", "verification", "cross-repository contract verification", "provider-consumer compatibility matrix and integration cases", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("rexjen", "Rexjen", "verification", "performance baseline and benchmark validity", "reproducible benchmark plan with workload and environment metadata", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_PERFORMANCE),
    F("kajldor", "Kajldor", "operations", "resource budgets and capacity limits", "CPU, memory, storage and concurrency budget ledger", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_PERFORMANCE),
    F("feljin", "Feljin", "operations", "logging, diagnostics and observability quality", "diagnostic coverage map with redaction and cardinality checks", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("vorjten", "Vorjten", "operations", "health, readiness and lifecycle behavior", "health/readiness contract and lifecycle transition tests", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("trexjen", "Trexjen", "operations", "fault containment and resilience testing", "failure-mode matrix with bounded retry and timeout requirements", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("seljven", "Seljven", "operations", "rollback, recovery and safe restoration", "recovery procedure and rollback verification matrix", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("drajgon", "Drajgon", "operations", "backup integrity and restore validation", "backup inventory with integrity and restore test cases", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("kesjin", "Kesjin", "documentation", "documentation information architecture", "documentation map with stale, orphaned and missing sections", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("brejden", "Brejden", "documentation", "README and onboarding completeness", "README audit with verified commands and implementation status", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("neljkor", "Neljkor", "documentation", "localization and terminology consistency", "locale coverage matrix and terminology drift report", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("tevjin", "Tevjin", "documentation", "API and reference documentation", "API reference gaps linked to actual public contracts", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("merjok", "Merjok", "documentation", "examples, tutorials and reproducible walkthroughs", "example verification plan and missing learning paths", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("jorven", "Jorven", "documentation", "knowledge indexing and source traceability", "local knowledge index with source and freshness references", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("rejnhar", "Rejnhar", "experience", "accessibility and inclusive interaction audit", "accessibility findings and keyboard/reduced-motion test plan", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("keljven", "Keljven", "experience", "UI and interaction contract consistency", "UI state, input and error contract matrix", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS),
    F("fendjin", "Fendjin", "experience", "localized interface behavior", "UI locale coverage and fallback behavior report", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("vajden", "Vajden", "experience", "interaction performance and responsiveness", "interaction latency budget and responsive-state test plan", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_PERFORMANCE),
    F("trevjorn", "Trevjorn", "experience", "end-to-end user workflow coherence", "workflow map with state transitions and recovery paths", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("skorjvin", "Skorjvin", "experience", "product journey and end-to-end acceptance", "user-journey acceptance matrix across integrated surfaces", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("deljmor", "Deljmor", "federation", "repository federation and ownership graph", "cross-repository ownership and dependency map", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("krejns", "Krejns", "federation", "ABI, FFI and binary interoperability", "ABI contract matrix with layout, calling-convention and error tests", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("veljin", "Veljin", "federation", "platform and toolchain adaptation", "platform capability matrix and fallback plan", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("tesjendor", "Tesjendor", "federation", "plugin and extension lifecycle boundaries", "extension contract with trust, version and lifecycle gates", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("morvajn", "Morvajn", "federation", "shared-state synchronization and consistency", "cross-repository consistency model and conflict plan", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
    F("zexjen", "Zexjen", "federation", "service and subsystem integration", "integration boundary map with failure and timeout contracts", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("rejnor", "Rejnor", "governance", "evidence-based maturity and completeness", "maturity assessment tied to executable exit criteria", REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("kajlven", "Kajlven", "governance", "auditable evidence ledger and provenance", "evidence ledger with claim, source, owner and verification state", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("fengjin", "Fengjin", "governance", "risk scoring and change control", "risk register with impact, likelihood and mitigation evidence", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY),
    F("vorjden", "Vorjden", "governance", "roadmap prioritization and dependency sequencing", "prioritized roadmap with dependency and capacity assumptions", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION),
    F("trejns", "Trejns", "governance", "change-impact analysis across components", "change-impact graph and required regression scope", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY),
    F("seljkorn", "Seljkorn", "governance", "governed multi-framework orchestration", "ordered execution plan with conflict, approval and rollback gates", REAPER_FRAMEWORK_EVIDENCE_SOURCE | REAPER_FRAMEWORK_EVIDENCE_CONTRACTS | REAPER_FRAMEWORK_EVIDENCE_TESTS | REAPER_FRAMEWORK_EVIDENCE_SECURITY | REAPER_FRAMEWORK_EVIDENCE_ROLLBACK),
};

#undef F

static int ascii_equal_fold(const char *left, const char *right) {
    if (left == NULL || right == NULL) return 0;
    while (*left != '\0' && *right != '\0') {
        const unsigned char a = (unsigned char)*left;
        const unsigned char b = (unsigned char)*right;
        if (tolower(a) != tolower(b)) return 0;
        ++left;
        ++right;
    }
    return *left == '\0' && *right == '\0';
}

static int ascii_word(const char *value, int allow_uppercase) {
    if (value == NULL || *value == '\0') return 0;
    for (const unsigned char *cursor = (const unsigned char *)value;
         *cursor != '\0'; ++cursor) {
        if ((*cursor >= (unsigned char)'a' && *cursor <= (unsigned char)'z') ||
            (allow_uppercase && *cursor >= (unsigned char)'A' &&
             *cursor <= (unsigned char)'Z')) {
            continue;
        }
        return 0;
    }
    return 1;
}

size_t reaper_framework_catalog_count(void) {
    return sizeof(FRAMEWORKS) / sizeof(FRAMEWORKS[0]);
}

const ReaperFrameworkSpec *reaper_framework_catalog_at(size_t index) {
    if (index >= reaper_framework_catalog_count()) return NULL;
    return &FRAMEWORKS[index];
}

const ReaperFrameworkSpec *reaper_framework_find(const char *name_or_id) {
    if (name_or_id == NULL || *name_or_id == '\0') return NULL;
    for (size_t index = 0U; index < reaper_framework_catalog_count(); ++index) {
        const ReaperFrameworkSpec *item = &FRAMEWORKS[index];
        if (ascii_equal_fold(name_or_id, item->id) ||
            ascii_equal_fold(name_or_id, item->name)) {
            return item;
        }
    }
    return NULL;
}

int reaper_framework_catalog_validate(void) {
    const uint32_t allowed = REAPER_FRAMEWORK_EVIDENCE_ALL;
    if (reaper_framework_catalog_count() != 66U) return 0;
    for (size_t i = 0U; i < reaper_framework_catalog_count(); ++i) {
        const ReaperFrameworkSpec *item = &FRAMEWORKS[i];
        if (!ascii_word(item->id, 0) || !ascii_word(item->name, 1) ||
            item->domain == NULL || *item->domain == '\0' ||
            item->specialization == NULL || *item->specialization == '\0' ||
            item->deliverable == NULL || *item->deliverable == '\0' ||
            item->required_evidence == 0U ||
            (item->required_evidence & ~allowed) != 0U) {
            return 0;
        }
        for (size_t j = i + 1U; j < reaper_framework_catalog_count(); ++j) {
            if (ascii_equal_fold(item->id, FRAMEWORKS[j].id) ||
                ascii_equal_fold(item->name, FRAMEWORKS[j].name)) {
                return 0;
            }
        }
    }
    return 1;
}

ReaperFrameworkAssessment reaper_framework_assess(
    const char *name_or_id,
    uint32_t available_evidence
) {
    ReaperFrameworkAssessment assessment = {
        0, REAPER_FRAMEWORK_UNKNOWN, 0U, available_evidence,
        0U, 0, 0, 0
    };
    const ReaperFrameworkSpec *item = reaper_framework_find(name_or_id);
    if (item == NULL || (available_evidence & ~REAPER_FRAMEWORK_EVIDENCE_ALL) != 0U) {
        return assessment;
    }
    assessment.found = 1;
    assessment.required_evidence = item->required_evidence;
    assessment.missing_evidence = item->required_evidence & ~available_evidence;
    assessment.state = assessment.missing_evidence == 0U
        ? REAPER_FRAMEWORK_REVIEW_REQUIRED
        : REAPER_FRAMEWORK_BLOCKED;
    assessment.manual_review_required = 1;
    /* Profiles can prepare evidence and plans, never mutate or merge code. */
    assessment.source_mutation_authorized = 0;
    assessment.merge_authorized = 0;
    return assessment;
}

const char *reaper_framework_assessment_state_name(
    ReaperFrameworkAssessmentState state
) {
    switch (state) {
    case REAPER_FRAMEWORK_UNKNOWN: return "unknown";
    case REAPER_FRAMEWORK_BLOCKED: return "blocked";
    case REAPER_FRAMEWORK_REVIEW_REQUIRED: return "review-required";
    default: return "invalid";
    }
}

const char *reaper_framework_evidence_name(uint32_t single_flag) {
    switch (single_flag) {
    case REAPER_FRAMEWORK_EVIDENCE_SOURCE: return "source";
    case REAPER_FRAMEWORK_EVIDENCE_CONTRACTS: return "contracts";
    case REAPER_FRAMEWORK_EVIDENCE_TESTS: return "tests";
    case REAPER_FRAMEWORK_EVIDENCE_SECURITY: return "security";
    case REAPER_FRAMEWORK_EVIDENCE_PERFORMANCE: return "performance";
    case REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION: return "documentation";
    case REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY: return "compatibility";
    case REAPER_FRAMEWORK_EVIDENCE_ROLLBACK: return "rollback";
    default: return "unknown";
    }
}
