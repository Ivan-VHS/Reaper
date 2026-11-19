#ifndef REAPER_EVOLUTION_H
#define REAPER_EVOLUTION_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Evidence gate for a proposed language/compiler change.
 *
 * This module never edits source files and never merges branches. It turns
 * explicit, reviewable evidence into a deterministic readiness decision.
 * Counts are minimums, not proof of correctness or a security sandbox.
 */
typedef enum {
    REAPER_EVOLUTION_BLOCKED = 0,
    REAPER_EVOLUTION_REVIEW_REQUIRED = 1,
    REAPER_EVOLUTION_APPROVED_FOR_MANUAL_MERGE = 2
} ReaperEvolutionState;

enum {
    REAPER_EVOLUTION_NEEDS_SPEC          = UINT32_C(1) << 0,
    REAPER_EVOLUTION_NEEDS_IMPLEMENTATION= UINT32_C(1) << 1,
    REAPER_EVOLUTION_NEEDS_POSITIVE_TESTS= UINT32_C(1) << 2,
    REAPER_EVOLUTION_NEEDS_NEGATIVE_TESTS= UINT32_C(1) << 3,
    REAPER_EVOLUTION_NEEDS_FUZZING       = UINT32_C(1) << 4,
    REAPER_EVOLUTION_NEEDS_DIFFERENTIAL  = UINT32_C(1) << 5,
    REAPER_EVOLUTION_NEEDS_COMPATIBILITY = UINT32_C(1) << 6,
    REAPER_EVOLUTION_NEEDS_SECURITY      = UINT32_C(1) << 7,
    REAPER_EVOLUTION_NEEDS_ROLLBACK      = UINT32_C(1) << 8,
    REAPER_EVOLUTION_NEEDS_PERF_EVIDENCE = UINT32_C(1) << 9,
    REAPER_EVOLUTION_NEEDS_HUMAN_APPROVAL= UINT32_C(1) << 10
};

typedef struct {
    uint32_t positive_tests;
    uint32_t negative_tests;
    uint32_t fuzz_cases;
    uint32_t differential_cases;
    uint64_t benchmark_before_ns;
    uint64_t benchmark_after_ns;
    int specification_present;
    int implementation_present;
    int compatibility_checked;
    int security_reviewed;
    int rollback_available;
    int performance_claimed;
    int maintainer_approved;
} ReaperEvolutionEvidence;

typedef struct {
    uint32_t minimum_positive_tests;
    uint32_t minimum_negative_tests;
    uint32_t minimum_fuzz_cases;
    uint32_t minimum_differential_cases;
} ReaperEvolutionPolicy;

typedef struct {
    ReaperEvolutionState state;
    uint32_t blockers;
} ReaperEvolutionDecision;

ReaperEvolutionPolicy reaper_evolution_default_policy(void);
ReaperEvolutionDecision reaper_evolution_evaluate(
    const ReaperEvolutionEvidence *evidence,
    const ReaperEvolutionPolicy *policy
);
const char *reaper_evolution_state_name(ReaperEvolutionState state);
void reaper_evolution_print_status(void);

#ifdef __cplusplus
}
#endif

#endif
