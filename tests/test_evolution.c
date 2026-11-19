#include "reaper/evolution.h"

#include <assert.h>
#include <stdio.h>

static ReaperEvolutionEvidence complete_evidence(void) {
    ReaperEvolutionEvidence evidence = {
        8U, 12U, 5000U, 400U, 1000000U, 850000U,
        1, 1, 1, 1, 1, 1, 1
    };
    return evidence;
}

static void default_policy_has_real_thresholds(void) {
    ReaperEvolutionPolicy policy = reaper_evolution_default_policy();
    assert(policy.minimum_positive_tests == 1U);
    assert(policy.minimum_negative_tests == 1U);
    assert(policy.minimum_fuzz_cases == 1000U);
    assert(policy.minimum_differential_cases == 100U);
}

static void complete_evidence_is_eligible_only_after_approval(void) {
    ReaperEvolutionEvidence evidence = complete_evidence();
    ReaperEvolutionPolicy policy = reaper_evolution_default_policy();
    ReaperEvolutionDecision decision = reaper_evolution_evaluate(&evidence, &policy);
    assert(decision.state == REAPER_EVOLUTION_APPROVED_FOR_MANUAL_MERGE);
    assert(decision.blockers == 0U);
    evidence.maintainer_approved = 0;
    decision = reaper_evolution_evaluate(&evidence, &policy);
    assert(decision.state == REAPER_EVOLUTION_REVIEW_REQUIRED);
    assert(decision.blockers == REAPER_EVOLUTION_NEEDS_HUMAN_APPROVAL);
}

static void missing_evidence_fails_closed(void) {
    ReaperEvolutionEvidence evidence = complete_evidence();
    ReaperEvolutionPolicy policy = reaper_evolution_default_policy();
    evidence.security_reviewed = 0;
    evidence.rollback_available = 0;
    evidence.fuzz_cases = 0U;
    ReaperEvolutionDecision decision = reaper_evolution_evaluate(&evidence, &policy);
    assert(decision.state == REAPER_EVOLUTION_BLOCKED);
    assert((decision.blockers & REAPER_EVOLUTION_NEEDS_SECURITY) != 0U);
    assert((decision.blockers & REAPER_EVOLUTION_NEEDS_ROLLBACK) != 0U);
    assert((decision.blockers & REAPER_EVOLUTION_NEEDS_FUZZING) != 0U);
}

static void performance_claim_requires_measured_improvement(void) {
    ReaperEvolutionEvidence evidence = complete_evidence();
    ReaperEvolutionPolicy policy = reaper_evolution_default_policy();
    evidence.benchmark_after_ns = evidence.benchmark_before_ns;
    ReaperEvolutionDecision decision = reaper_evolution_evaluate(&evidence, &policy);
    assert((decision.blockers & REAPER_EVOLUTION_NEEDS_PERF_EVIDENCE) != 0U);
    evidence.performance_claimed = 0;
    decision = reaper_evolution_evaluate(&evidence, &policy);
    assert((decision.blockers & REAPER_EVOLUTION_NEEDS_PERF_EVIDENCE) == 0U);
}

static void null_inputs_fail_closed(void) {
    ReaperEvolutionDecision decision = reaper_evolution_evaluate(NULL, NULL);
    assert(decision.state == REAPER_EVOLUTION_BLOCKED);
    assert(decision.blockers == UINT32_MAX);
    assert(reaper_evolution_state_name(REAPER_EVOLUTION_BLOCKED)[0] == 'b');
}

int main(void) {
    default_policy_has_real_thresholds();
    complete_evidence_is_eligible_only_after_approval();
    missing_evidence_fails_closed();
    performance_claim_requires_measured_improvement();
    null_inputs_fail_closed();
    puts("native evolution tests: 5 groups passed");
    return 0;
}
