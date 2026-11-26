#include "reaper/evolution.h"
#include "reaper/frameworks.h"

#include <stdio.h>

ReaperEvolutionPolicy reaper_evolution_default_policy(void) {
    ReaperEvolutionPolicy policy = { 1U, 1U, 1000U, 100U };
    return policy;
}

ReaperEvolutionDecision reaper_evolution_evaluate(
    const ReaperEvolutionEvidence *evidence,
    const ReaperEvolutionPolicy *policy
) {
    ReaperEvolutionDecision decision = { REAPER_EVOLUTION_BLOCKED, 0U };
    if (evidence == NULL || policy == NULL) {
        decision.blockers = UINT32_MAX;
        return decision;
    }

    if (!evidence->specification_present)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_SPEC;
    if (!evidence->implementation_present)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_IMPLEMENTATION;
    if (evidence->positive_tests < policy->minimum_positive_tests)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_POSITIVE_TESTS;
    if (evidence->negative_tests < policy->minimum_negative_tests)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_NEGATIVE_TESTS;
    if (evidence->fuzz_cases < policy->minimum_fuzz_cases)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_FUZZING;
    if (evidence->differential_cases < policy->minimum_differential_cases)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_DIFFERENTIAL;
    if (!evidence->compatibility_checked)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_COMPATIBILITY;
    if (!evidence->security_reviewed)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_SECURITY;
    if (!evidence->rollback_available)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_ROLLBACK;
    if (evidence->performance_claimed &&
        (evidence->benchmark_before_ns == 0U ||
         evidence->benchmark_after_ns == 0U ||
         evidence->benchmark_after_ns >= evidence->benchmark_before_ns))
        decision.blockers |= REAPER_EVOLUTION_NEEDS_PERF_EVIDENCE;
    if (!evidence->maintainer_approved)
        decision.blockers |= REAPER_EVOLUTION_NEEDS_HUMAN_APPROVAL;

    if (decision.blockers == 0U)
        decision.state = REAPER_EVOLUTION_APPROVED_FOR_MANUAL_MERGE;
    else if (decision.blockers == REAPER_EVOLUTION_NEEDS_HUMAN_APPROVAL)
        decision.state = REAPER_EVOLUTION_REVIEW_REQUIRED;
    else
        decision.state = REAPER_EVOLUTION_BLOCKED;
    return decision;
}

const char *reaper_evolution_state_name(ReaperEvolutionState state) {
    switch (state) {
    case REAPER_EVOLUTION_BLOCKED: return "blocked";
    case REAPER_EVOLUTION_REVIEW_REQUIRED: return "review-required";
    case REAPER_EVOLUTION_APPROVED_FOR_MANUAL_MERGE: return "approved-for-manual-merge";
    default: return "invalid";
    }
}

void reaper_evolution_print_status(void) {
    const ReaperEvolutionPolicy policy = reaper_evolution_default_policy();
    (void)printf("REAPER Autonomous Evolution / C17\n");
    (void)printf("mode: evidence-gated; source mutation: disabled\n");
    (void)printf("minimum evidence: positive=%u negative=%u fuzz=%u differential=%u\n",
        policy.minimum_positive_tests, policy.minimum_negative_tests,
        policy.minimum_fuzz_cases, policy.minimum_differential_cases);
    (void)printf("pipeline: SPEC -> IMPLEMENT -> TEST -> FUZZ -> DIFFERENTIAL -> "
                 "COMPATIBILITY -> SECURITY -> ROLLBACK -> HUMAN REVIEW\n");
    (void)printf("merge policy: maintainer-controlled; never automatic\n");
}
