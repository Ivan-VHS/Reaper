#include "reaper/hmga_v3.h"

#include <stdio.h>

#define CHECK(condition) do { \
    if (!(condition)) { \
        (void)fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__, #condition); \
        return 1; \
    } \
} while (0)

int main(void) {
    size_t axiom_count = 0u;
    const hmga_v3_axiom *catalogue = hmga_v3_get_axioms(&axiom_count);
    unsigned char seen[HMGA_V3_AXIOM_COUNT + 1u][HMGA_V3_AXIOM_COUNT + 1u] = {{0}};
    hmga_v3_budget budget = {0u, 0u};
    hmga_v3_operator op;
    size_t index;

    CHECK(catalogue != NULL);
    CHECK(axiom_count == HMGA_V3_AXIOM_COUNT);
    for (index = 0u; index < axiom_count; ++index) {
        CHECK(catalogue[index].imperative != NULL && catalogue[index].imperative[0] != '\0');
        CHECK(catalogue[index].quality != NULL && catalogue[index].quality[0] != '\0');
        CHECK(catalogue[index].engineering_vector != NULL &&
              catalogue[index].engineering_vector[0] != '\0');
    }

    CHECK(hmga_v3_get_operator_count() == HMGA_V3_OPERATOR_COUNT);
    for (index = 0u; index < HMGA_V3_OPERATOR_COUNT; ++index) {
        CHECK(hmga_v3_get_operator(index, &op) == 0);
        CHECK(op.sequence == index + 1u);
        CHECK(op.left_axiom == index / HMGA_V3_AXIOM_COUNT + 1u);
        CHECK(op.right_axiom == index % HMGA_V3_AXIOM_COUNT + 1u);
        CHECK(seen[op.left_axiom][op.right_axiom] == 0u);
        seen[op.left_axiom][op.right_axiom] = 1u;
    }
    for (index = 1u; index <= HMGA_V3_AXIOM_COUNT; ++index) {
        size_t column;
        for (column = 1u; column <= HMGA_V3_AXIOM_COUNT; ++column) {
            CHECK(seen[index][column] == 1u);
        }
    }
    CHECK(hmga_v3_get_operator(HMGA_V3_OPERATOR_COUNT, &op) != 0);
    CHECK(hmga_v3_get_operator(0u, NULL) != 0);

    CHECK(hmga_v3_budget_for_rounds(1u, &budget) == 0);
    CHECK(budget.rounds == 1u && budget.operator_evaluations == 400u);
    CHECK(hmga_v3_budget_for_rounds(HMGA_V3_MAX_ROUNDS, &budget) == 0);
    CHECK(budget.operator_evaluations == 25600u);
    CHECK(hmga_v3_budget_for_rounds(0u, &budget) != 0);
    CHECK(hmga_v3_budget_for_rounds(HMGA_V3_MAX_ROUNDS + 1u, &budget) != 0);
    CHECK(hmga_v3_budget_for_rounds(1u, NULL) != 0);

    (void)puts("HMGA v3: 20 axioms, 400 unique ordered operators, bounded budgets OK");
    return 0;
}
