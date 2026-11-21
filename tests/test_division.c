#include "reaper/division.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

static void check_condition(
    int condition, const char *expression, const char *file, int line
) {
    if (!condition) {
        fprintf(stderr, "CHECK failed at %s:%d: %s\n",
                file, line, expression);
        exit(EXIT_FAILURE);
    }
}

#define CHECK(expression) \
    check_condition((expression), #expression, __FILE__, __LINE__)

static void expect_division(
    int64_t dividend, int64_t divisor, int64_t quotient, int64_t remainder
) {
    ReaperEuclideanResult result;
    CHECK(reaper_euclidean_divmod_i64(dividend, divisor, &result) == 0);
    CHECK(result.quotient == quotient);
    CHECK(result.remainder == remainder);
}

int main(void) {
    int exact = 0;
    ReaperPartitionPlan plan;
    size_t offset = 0U, count = 0U, cursor = 0U, total = 0U;
    size_t recommended = 0U;

    expect_division(17, 5, 3, 2);
    expect_division(-17, 5, -4, 3);
    expect_division(17, -5, -3, 2);
    expect_division(-17, -5, 4, 3);
    expect_division(INT64_MIN, 3, INT64_MIN / 3 - 1, 1);
    CHECK(reaper_euclidean_divmod_i64(1, 0, &(ReaperEuclideanResult){0}) != 0);
    CHECK(reaper_euclidean_divmod_i64(INT64_MIN, -1, &(ReaperEuclideanResult){0}) != 0);
    CHECK(reaper_is_divisible_i64(42, 7, &exact) == 0 && exact == 1);
    CHECK(reaper_is_divisible_i64(43, 7, &exact) == 0 && exact == 0);
    CHECK(reaper_is_divisible_i64(1, 0, &exact) != 0);

    CHECK(reaper_partition_plan_init(10U, 3U, &plan) == 0);
    for (size_t i = 0U; i < plan.partition_count; ++i) {
        CHECK(reaper_partition_plan_range(&plan, i, &offset, &count) == 0);
        CHECK(offset == cursor);
        cursor += count;
        total += count;
    }
    CHECK(total == 10U && cursor == 10U);
    CHECK(reaper_partition_plan_init(2U, 5U, &plan) == 0);
    CHECK(reaper_partition_plan_range(&plan, 4U, &offset, &count) == 0);
    CHECK(offset == 2U && count == 0U);
    CHECK(reaper_partition_plan_init(1U, 0U, &plan) != 0);
    CHECK(reaper_partition_plan_range(&plan, 5U, &offset, &count) != 0);

    CHECK(reaper_recommend_partition_count(10000U, 16U, 256U, &recommended) == 0);
    CHECK(recommended == 16U);
    CHECK(reaper_recommend_partition_count(100U, 16U, 256U, &recommended) == 0);
    CHECK(recommended == 1U);
    CHECK(reaper_recommend_partition_count(0U, 16U, 256U, &recommended) == 0);
    CHECK(recommended == 0U);
    CHECK(reaper_recommend_partition_count(10U, 0U, 1U, &recommended) != 0);

    puts("Reaper division and partition tests passed.");
    return 0;
}
