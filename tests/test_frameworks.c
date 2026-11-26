#include "reaper/frameworks.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void catalogue_is_complete_and_well_formed(void) {
    assert(reaper_framework_catalog_count() == 66U);
    assert(reaper_framework_catalog_validate());
    assert(reaper_framework_catalog_at(0U) != NULL);
    assert(reaper_framework_catalog_at(65U) != NULL);
    assert(reaper_framework_catalog_at(66U) == NULL);
}

static void every_framework_has_a_unique_latin_name(void) {
    for (size_t i = 0U; i < reaper_framework_catalog_count(); ++i) {
        const ReaperFrameworkSpec *left = reaper_framework_catalog_at(i);
        assert(left != NULL);
        assert(strlen(left->name) > 1U);
        for (const char *p = left->name; *p != '\0'; ++p) {
            assert((*p >= 'A' && *p <= 'Z') || (*p >= 'a' && *p <= 'z'));
        }
        for (size_t j = i + 1U; j < reaper_framework_catalog_count(); ++j) {
            const ReaperFrameworkSpec *right = reaper_framework_catalog_at(j);
            assert(right != NULL);
            assert(strcmp(left->id, right->id) != 0);
            assert(strcmp(left->name, right->name) != 0);
        }
    }
}

static void lookup_accepts_name_and_identifier_case_insensitively(void) {
    const ReaperFrameworkSpec *by_name = reaper_framework_find("Jevron");
    const ReaperFrameworkSpec *by_id = reaper_framework_find("JEVRON");
    assert(by_name != NULL && by_id != NULL);
    assert(strcmp(by_name->id, "jevron") == 0);
    assert(by_name == by_id);
    assert(reaper_framework_find("not-a-framework") == NULL);
    assert(reaper_framework_find(NULL) == NULL);
    assert(reaper_framework_find("") == NULL);
}

static void missing_evidence_blocks_assessment(void) {
    const ReaperFrameworkSpec *spec = reaper_framework_find("Teljorn");
    assert(spec != NULL);
    ReaperFrameworkAssessment result = reaper_framework_assess("Teljorn", 0U);
    assert(result.found == 1);
    assert(result.state == REAPER_FRAMEWORK_BLOCKED);
    assert(result.missing_evidence == spec->required_evidence);
    assert(result.manual_review_required == 1);
    assert(result.source_mutation_authorized == 0);
    assert(result.merge_authorized == 0);
}

static void complete_evidence_requests_human_review_only(void) {
    const ReaperFrameworkSpec *spec = reaper_framework_find("Seljkorn");
    assert(spec != NULL);
    ReaperFrameworkAssessment result = reaper_framework_assess(
        "Seljkorn", REAPER_FRAMEWORK_EVIDENCE_ALL
    );
    assert(result.found == 1);
    assert(result.state == REAPER_FRAMEWORK_REVIEW_REQUIRED);
    assert(result.missing_evidence == 0U);
    assert(result.manual_review_required == 1);
    assert(result.source_mutation_authorized == 0);
    assert(result.merge_authorized == 0);
}

static void invalid_names_and_evidence_bits_fail_closed(void) {
    ReaperFrameworkAssessment unknown = reaper_framework_assess("unknown", 0U);
    assert(unknown.found == 0);
    assert(unknown.state == REAPER_FRAMEWORK_UNKNOWN);
    ReaperFrameworkAssessment invalid = reaper_framework_assess(
        "Jevron", UINT32_C(1) << 31
    );
    assert(invalid.found == 0);
    assert(invalid.state == REAPER_FRAMEWORK_UNKNOWN);
    assert(strcmp(reaper_framework_assessment_state_name(
        REAPER_FRAMEWORK_BLOCKED), "blocked") == 0);
    assert(strcmp(reaper_framework_evidence_name(
        REAPER_FRAMEWORK_EVIDENCE_SECURITY), "security") == 0);
}

int main(void) {
    catalogue_is_complete_and_well_formed();
    every_framework_has_a_unique_latin_name();
    lookup_accepts_name_and_identifier_case_insensitively();
    missing_evidence_blocks_assessment();
    complete_evidence_requests_human_review_only();
    invalid_names_and_evidence_bits_fail_closed();
    puts("native framework tests: 6 groups passed");
    return 0;
}
