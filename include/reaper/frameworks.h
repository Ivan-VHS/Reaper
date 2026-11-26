#ifndef REAPER_FRAMEWORKS_H
#define REAPER_FRAMEWORKS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum {
    REAPER_FRAMEWORK_EVIDENCE_SOURCE        = UINT32_C(1) << 0,
    REAPER_FRAMEWORK_EVIDENCE_CONTRACTS     = UINT32_C(1) << 1,
    REAPER_FRAMEWORK_EVIDENCE_TESTS         = UINT32_C(1) << 2,
    REAPER_FRAMEWORK_EVIDENCE_SECURITY      = UINT32_C(1) << 3,
    REAPER_FRAMEWORK_EVIDENCE_PERFORMANCE  = UINT32_C(1) << 4,
    REAPER_FRAMEWORK_EVIDENCE_DOCUMENTATION= UINT32_C(1) << 5,
    REAPER_FRAMEWORK_EVIDENCE_COMPATIBILITY= UINT32_C(1) << 6,
    REAPER_FRAMEWORK_EVIDENCE_ROLLBACK     = UINT32_C(1) << 7
};

#define REAPER_FRAMEWORK_EVIDENCE_ALL (UINT32_C(0xff))

typedef struct {
    const char *id;
    const char *name;
    const char *domain;
    const char *specialization;
    const char *deliverable;
    uint32_t required_evidence;
} ReaperFrameworkSpec;

typedef enum {
    REAPER_FRAMEWORK_UNKNOWN = 0,
    REAPER_FRAMEWORK_BLOCKED = 1,
    REAPER_FRAMEWORK_REVIEW_REQUIRED = 2
} ReaperFrameworkAssessmentState;

typedef struct {
    int found;
    ReaperFrameworkAssessmentState state;
    uint32_t required_evidence;
    uint32_t available_evidence;
    uint32_t missing_evidence;
    int manual_review_required;
    int source_mutation_authorized;
    int merge_authorized;
} ReaperFrameworkAssessment;

/* The catalogue is immutable and contains 66 reviewed framework profiles. */
size_t reaper_framework_catalog_count(void);
const ReaperFrameworkSpec *reaper_framework_catalog_at(size_t index);
const ReaperFrameworkSpec *reaper_framework_find(const char *name_or_id);
int reaper_framework_catalog_validate(void);

/*
 * Assess a framework against evidence already collected by its caller.
 * A complete result is only eligible for human review; this API never grants
 * permission to modify source files or merge a change.
 */
ReaperFrameworkAssessment reaper_framework_assess(
    const char *name_or_id,
    uint32_t available_evidence
);

const char *reaper_framework_assessment_state_name(
    ReaperFrameworkAssessmentState state
);
const char *reaper_framework_evidence_name(uint32_t single_flag);

#ifdef __cplusplus
}
#endif

#endif
