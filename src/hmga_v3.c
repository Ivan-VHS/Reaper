#include "reaper/hmga_v3.h"

static const hmga_v3_axiom axioms[HMGA_V3_AXIOM_COUNT] = {
    { "Lock",       "Naturalness",   "Compose functions" },
    { "Fix",        "Organicity",    "Automated tests" },
    { "Establish",  "Ease",          "Review-gated delivery" },
    { "Reserve",    "Naturalness",   "Optional startup" },
    { "Prepare",    "Sincerity",     "Native application" },
    { "Assign",     "Authenticity",  "Desktop application" },
    { "Approve",    "Genuineness",   "White-red-blue design" },
    { "Standardize","Individuality", "Version and dependency updates" },
    { "Expose",     "Vitality",      "New functions" },
    { "Apply",      "Compatibility", "Apply compatible functions to compatible inputs" },
    { "Configure",  "Simplicity",    "Configuration" },
    { "Integrate",  "Directness",    "Merge after review" },
    { "Ensure",     "Wholeness",     "Unify compatible modules" },
    { "Protect",    "Organicity",    "Systematize" },
    { "Set",        "Unobtrusiveness","Consolidate modules" },
    { "Refine",     "Freedom",       "Improve code readability" },
    { "Improve",    "Integrity",     "Improve quality" },
    { "Scale",      "Relevance",     "Expand useful capabilities" },
    { "Strengthen", "Harmony",       "Improve robustness" },
    { "Continue",   "Knowledge",     "Continue evolution" }
};

const hmga_v3_axiom *hmga_v3_get_axioms(size_t *count) {
    if (count != NULL) {
        *count = HMGA_V3_AXIOM_COUNT;
    }
    return axioms;
}

size_t hmga_v3_get_operator_count(void) {
    return HMGA_V3_OPERATOR_COUNT;
}

int hmga_v3_get_operator(size_t index, hmga_v3_operator *out) {
    if (out == NULL || index >= HMGA_V3_OPERATOR_COUNT) {
        return -1;
    }

    out->sequence = (uint16_t)(index + 1u);
    out->left_axiom = (uint8_t)(index / HMGA_V3_AXIOM_COUNT + 1u);
    out->right_axiom = (uint8_t)(index % HMGA_V3_AXIOM_COUNT + 1u);
    return 0;
}

int hmga_v3_budget_for_rounds(uint32_t rounds, hmga_v3_budget *out) {
    if (out == NULL) {
        return -1;
    }

    out->rounds = 0u;
    out->operator_evaluations = 0u;
    if (rounds == 0u || rounds > HMGA_V3_MAX_ROUNDS) {
        return -1;
    }

    out->rounds = rounds;
    out->operator_evaluations =
        (uint64_t)rounds * (uint64_t)HMGA_V3_OPERATOR_COUNT;
    return 0;
}
